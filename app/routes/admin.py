from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app import db
from app.models import User, Ban, UserBan, FundPeriod, FundDue
from app.permissions import bdh_required, can_assign_role, role_required
from app.mail import send_email
from app.security import require_csrf
from app.services.common import member_record
from app.services.access import can_manage_member, approved
from app.services.common import audit

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/approve")
@login_required
@bdh_required
def approve_list():
    pending_users = User.query.filter_by(status="pending").all()
    if current_user.chuc_vu == "TB":
        managed = set(current_user.quan_ly_ban_ids())
        pending_users = [user for user in pending_users if managed.intersection(link.ban_id for link in user.ban_links)]
    return render_template("admin_approve.html", pending_users=pending_users)


@admin_bp.route("/approve/<int:user_id>", methods=["POST"])
@login_required
@bdh_required
def approve_user(user_id):
    require_csrf()
    user = User.query.get_or_404(user_id)
    if user.status != "pending":
        abort(400)
    if current_user.chuc_vu == "TB" and not set(current_user.quan_ly_ban_ids()).intersection(link.ban_id for link in user.ban_links):
        abort(403)
    action = request.form.get("action")  # 'accept' | 'reject'
    if action == "accept":
        user.status = "approved"
        ky_hien_tai = FundPeriod.query.filter_by(is_current=True).first()
        user.ky_tham_gia_id = ky_hien_tai.id if ky_hien_tai else None
        member_record(user)
        if ky_hien_tai and not FundDue.query.filter_by(period_id=ky_hien_tai.id, user_id=user.id).first():
            db.session.add(FundDue(period_id=ky_hien_tai.id, user_id=user.id, da_dong=False))
        audit(current_user, "member_approve", user)
        db.session.commit()
        mailed = send_email(
            user.email,
            "[CLB] Ban da tro thanh thanh vien chinh thuc",
            f"Chao {user.ho_ten},\n\nBDH da duyet ho so cua ban (MSSV: {user.mssv}). "
            "Ban co the dang nhap va xem noi dung cua CLB.\n\n-- AI Agent CLB",
        )
        flash(f"Da duyet {user.ho_ten} thanh thanh vien CLB.", "success")
        if not mailed:
            flash("Email thong bao chua gui duoc. Kiem tra cau hinh SMTP va thong bao truc tiep cho thanh vien.", "error")
    elif action == "reject":
        user.status = "rejected"
        audit(current_user, "member_reject", user)
        db.session.commit()
        mailed = send_email(
            user.email,
            "[CLB] Ho so dang ky chua duoc chap nhan",
            f"Chao {user.ho_ten},\n\nRat tiec, BDH chua the xac nhan thong tin dang ky "
            f"cua ban (MSSV: {user.mssv}). Vui long lien he BDH de biet them chi tiet.\n\n"
            "-- AI Agent CLB",
        )
        flash(f"Da tu choi {user.ho_ten}.", "success")
        if not mailed:
            flash("Email thong bao chua gui duoc. Kiem tra cau hinh SMTP va thong bao truc tiep cho thanh vien.", "error")
    else:
        abort(400)
    return redirect(url_for("admin.approve_list"))


@admin_bp.route("/roles")
@login_required
@role_required("CN", "PCN", "TB", "THUKY_THUQUY")
def role_list():
    members = User.query.filter_by(status="approved").order_by(User.ho_ten).all()
    if current_user.chuc_vu == "TB":
        members = [member for member in members if can_manage_member(current_user, member) or member.id == current_user.id]
    bans = Ban.query.all()

    counts = {}
    for m in members:
        counts[m.chuc_vu] = counts.get(m.chuc_vu, 0) + 1

    return render_template(
        "admin_roles.html", members=members, bans=bans, counts=counts, current_user=current_user
    )


@admin_bp.route("/roles/<int:user_id>/assign", methods=["POST"])
@login_required
@bdh_required
def assign_role(user_id):
    require_csrf()
    target = User.query.get_or_404(user_id)
    new_role = request.form.get("chuc_vu")
    ban_id = request.form.get("ban_id", type=int)  # bat buoc khi new_role == 'TB'

    counts = {}
    for m in User.query.filter_by(status="approved").all():
        counts[m.chuc_vu] = counts.get(m.chuc_vu, 0) + 1
    # tru di 1 neu target dang giu dung chuc vu do (khong tinh trung lap khi giu nguyen)
    if target.chuc_vu == new_role:
        counts[new_role] = max(0, counts.get(new_role, 0) - 1)

    ok, message = can_assign_role(current_user, target, new_role, counts)
    if not ok:
        flash(message, "error")
        return redirect(url_for("admin.role_list"))

    if new_role == "TB":
        if not ban_id or not Ban.query.get(ban_id):
            flash("Vui long chon ban ma Truong ban nay se quan ly.", "error")
            return redirect(url_for("admin.role_list"))
    # Xoa quyen truong ban khi chuyen sang chuc vu khac.
    UserBan.query.filter_by(user_id=target.id, is_truong_ban=True).update(
        {"is_truong_ban": False}
    )
    target.chuc_vu = new_role
    target.chi_dinh_boi_id = current_user.id

    if new_role == "TB":
        # xoa cac quyen truong-ban cu (neu co) roi gan quyen moi
        link = UserBan.query.filter_by(user_id=target.id, ban_id=ban_id).first()
        if not link:
            link = UserBan(user_id=target.id, ban_id=ban_id)
            db.session.add(link)
        link.is_truong_ban = True

    audit(current_user, "role_assign", target, {"role": new_role, "ban_id": ban_id})
    db.session.commit()
    flash(f"Da chi dinh {target.ho_ten} lam {new_role}.", "success")
    return redirect(url_for("admin.role_list"))


@admin_bp.route("/roles/nhuong-quyen", methods=["POST"])
@login_required
@role_required("CN", "PCN", "TB", "THUKY_THUQUY")
def nhuong_quyen():
    """
    Co che nhuong quyen: BDH cu (current_user) roi vi tri, chi dinh chuc vu
    cua minh cho thanh vien khac (target), ban than current_user thanh
    THANH_VIEN.
    """
    require_csrf()
    user_id = request.form.get("target_id", type=int)
    if user_id is None:
        abort(400)
    target = User.query.get_or_404(user_id)
    old_role = current_user.chuc_vu
    can_transfer = (can_manage_member(current_user, target) or
                    (old_role == "THUKY_THUQUY" and target.chuc_vu == "THANH_VIEN"))
    if target.id == current_user.id or not approved(target) or not current_user.outranks(target) or not can_transfer:
        abort(400)

    ban_id = request.form.get("ban_id", type=int)
    if old_role == "TB" and (not ban_id or ban_id not in current_user.quan_ly_ban_ids()):
        flash("Vui long chon ban de nhuong quyen Truong ban.", "error")
        return redirect(url_for("admin.role_list"))

    UserBan.query.filter_by(user_id=target.id, is_truong_ban=True).update(
        {"is_truong_ban": False}
    )

    target.chuc_vu = old_role
    target.chi_dinh_boi_id = current_user.id

    if old_role == "TB":
        link = UserBan.query.filter_by(user_id=target.id, ban_id=ban_id).first()
        if not link:
            link = UserBan(user_id=target.id, ban_id=ban_id)
            db.session.add(link)
        link.is_truong_ban = True

    current_user.chuc_vu = "THANH_VIEN"
    UserBan.query.filter_by(user_id=current_user.id, is_truong_ban=True).update(
        {"is_truong_ban": False}
    )

    audit(current_user, "role_transfer", target, {"role": old_role})
    db.session.commit()
    flash(f"Ban da nhuong quyen {old_role} lai cho {target.ho_ten} va tro thanh thanh vien.", "success")
    return redirect(url_for("main.home"))
