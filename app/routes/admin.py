from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app import db
from app.models import User, Ban, UserBan, FundPeriod
from app.permissions import bdh_required, can_assign_role
from app.mail import send_email

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/approve")
@login_required
@bdh_required
def approve_list():
    pending_users = User.query.filter_by(status="pending").all()
    return render_template("admin_approve.html", pending_users=pending_users)


@admin_bp.route("/approve/<int:user_id>", methods=["POST"])
@login_required
@bdh_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    action = request.form.get("action")  # 'accept' | 'reject'
    if action == "accept":
        user.status = "approved"
        ky_hien_tai = FundPeriod.query.filter_by(is_current=True).first()
        user.ky_tham_gia_id = ky_hien_tai.id if ky_hien_tai else None
        db.session.commit()
        send_email(
            user.email,
            "[CLB] Ban da tro thanh thanh vien chinh thuc",
            f"Chao {user.ho_ten},\n\nBDH da duyet ho so cua ban (MSSV: {user.mssv}). "
            "Ban co the dang nhap va xem noi dung cua CLB.\n\n-- AI Agent CLB",
        )
        flash(f"Da duyet {user.ho_ten} thanh thanh vien CLB.", "success")
    elif action == "reject":
        user.status = "rejected"
        db.session.commit()
        send_email(
            user.email,
            "[CLB] Ho so dang ky chua duoc chap nhan",
            f"Chao {user.ho_ten},\n\nRat tiec, BDH chua the xac nhan thong tin dang ky "
            f"cua ban (MSSV: {user.mssv}). Vui long lien he BDH de biet them chi tiet.\n\n"
            "-- AI Agent CLB",
        )
        flash(f"Da tu choi {user.ho_ten}.", "success")
    else:
        abort(400)
    return redirect(url_for("admin.approve_list"))


@admin_bp.route("/roles")
@login_required
@bdh_required
def role_list():
    members = User.query.filter_by(status="approved").order_by(User.ho_ten).all()
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

    target.chuc_vu = new_role
    target.chi_dinh_boi_id = current_user.id

    if new_role == "TB":
        if not ban_id:
            flash("Vui long chon ban ma Truong ban nay se quan ly.", "error")
            return redirect(url_for("admin.role_list"))
        # xoa cac quyen truong-ban cu (neu co) roi gan quyen moi
        UserBan.query.filter_by(user_id=target.id, is_truong_ban=True).update(
            {"is_truong_ban": False}
        )
        link = UserBan.query.filter_by(user_id=target.id, ban_id=ban_id).first()
        if not link:
            link = UserBan(user_id=target.id, ban_id=ban_id)
            db.session.add(link)
        link.is_truong_ban = True

    db.session.commit()
    flash(f"Da chi dinh {target.ho_ten} lam {new_role}.", "success")
    return redirect(url_for("admin.role_list"))


@admin_bp.route("/roles/<int:user_id>/nhuong-quyen", methods=["POST"])
@login_required
@bdh_required
def nhuong_quyen(user_id):
    """
    Co che nhuong quyen: BDH cu (current_user) roi vi tri, chi dinh chuc vu
    cua minh cho thanh vien khac (target), ban than current_user thanh
    THANH_VIEN.
    """
    target = User.query.get_or_404(user_id)
    old_role = current_user.chuc_vu
    if old_role == "THANH_VIEN":
        abort(400)

    ban_id = request.form.get("ban_id", type=int)
    if old_role == "TB" and not ban_id:
        flash("Vui long chon ban de nhuong quyen Truong ban.", "error")
        return redirect(url_for("admin.role_list"))

    target.chuc_vu = old_role
    target.chi_dinh_boi_id = current_user.id

    if old_role == "TB":
        UserBan.query.filter_by(user_id=target.id, is_truong_ban=True).update(
            {"is_truong_ban": False}
        )
        link = UserBan.query.filter_by(user_id=target.id, ban_id=ban_id).first()
        if not link:
            link = UserBan(user_id=target.id, ban_id=ban_id)
            db.session.add(link)
        link.is_truong_ban = True

    current_user.chuc_vu = "THANH_VIEN"

    db.session.commit()
    flash(f"Ban da nhuong quyen {old_role} lai cho {target.ho_ten} va tro thanh thanh vien.", "success")
    return redirect(url_for("admin.role_list"))
