from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app import db
from app.models import Event, Task, User, Ban
from app.permissions import approved_required, bdh_required
from app.mail import send_email
from app.activity import cap_nhat_hoat_dong_khi_event_ket_thuc

event_bp = Blueprint("event", __name__)


@event_bp.route("/event")
@login_required
@approved_required
def event_list():
    events = Event.query.order_by(Event.thoi_gian_bat_dau.desc()).all()
    return render_template("event.html", events=events)


@event_bp.route("/event/new", methods=["GET", "POST"])
@login_required
@bdh_required
def event_new():
    if request.method == "POST":
        ma = request.form.get("ma_su_kien", "").strip()
        if Event.query.filter_by(ma_su_kien=ma).first():
            flash("Ma su kien da ton tai, vui long chon ma khac.", "error")
            return render_template("event_form.html", form=request.form)

        ev = Event(
            ten_su_kien=request.form.get("ten_su_kien", "").strip(),
            ma_su_kien=ma,
            thoi_gian_bat_dau=datetime.strptime(
                request.form.get("thoi_gian_bat_dau"), "%Y-%m-%dT%H:%M"
            ),
            thoi_gian_ket_thuc=datetime.strptime(
                request.form.get("thoi_gian_ket_thuc"), "%Y-%m-%dT%H:%M"
            ),
            trang_thai="sap_dien_ra",
            tao_boi_id=current_user.id,
        )
        db.session.add(ev)
        db.session.commit()
        flash("Da tao su kien. Tiep tuc them task con.", "success")
        return redirect(url_for("event.event_detail", event_id=ev.id))

    return render_template("event_form.html", form={})


@event_bp.route("/event/<int:event_id>")
@login_required
@approved_required
def event_detail(event_id):
    ev = Event.query.get_or_404(event_id)
    bans = Ban.query.all()
    return render_template(
        "event_detail.html", event=ev, bans=bans, is_bdh=current_user.is_bdh()
    )


@event_bp.route("/event/<int:event_id>/task/new", methods=["POST"])
@login_required
@bdh_required
def task_new(event_id):
    """
    Tao task con. Nguoi phu trach BAT BUOC phai duoc chi dinh ngay tu dau
    (khong con co che mo cho thanh vien xung phong).
    """
    ev = Event.query.get_or_404(event_id)

    assignee_mssv = request.form.get("assignee_mssv", "").strip()
    assignee = User.query.filter_by(mssv=assignee_mssv, status="approved").first()
    if not assignee:
        flash("Khong tim thay thanh vien voi MSSV nay. Task phai co nguoi phu trach ngay tu dau.", "error")
        return redirect(url_for("event.event_detail", event_id=ev.id))

    ban_id = request.form.get("ban_id", type=int)

    task = Task(
        event_id=ev.id,
        ten_task=request.form.get("ten_task", "").strip(),
        mo_ta=request.form.get("mo_ta", "").strip(),
        deadline=datetime.strptime(request.form.get("deadline"), "%Y-%m-%dT%H:%M"),
        assignee_id=assignee.id,
        ban_id=ban_id,
        trang_thai="dang_lam",
    )
    db.session.add(task)
    db.session.commit()

    send_email(
        task.assignee.email,
        f"[CLB] Ban duoc giao task moi: {task.ten_task}",
        f"Chao {task.assignee.ho_ten},\n\nBan duoc giao task \"{task.ten_task}\" "
        f"thuoc su kien \"{ev.ten_su_kien}\", han hoan thanh: "
        f"{task.deadline.strftime('%d/%m/%Y %H:%M')}.\n\n-- AI Agent CLB",
    )

    flash("Da them task moi.", "success")
    return redirect(url_for("event.event_detail", event_id=ev.id))


@event_bp.route("/task/<int:task_id>/chi-dinh-lai", methods=["POST"])
@login_required
@bdh_required
def task_reassign(task_id):
    """BDH doi lai nguoi phu trach mot task da ton tai (van la chi dinh, khong phai xung phong)."""
    task = Task.query.get_or_404(task_id)
    mssv = request.form.get("assignee_mssv", "").strip()
    assignee = User.query.filter_by(mssv=mssv, status="approved").first()
    if not assignee:
        flash("Khong tim thay thanh vien voi MSSV nay.", "error")
        return redirect(url_for("event.event_detail", event_id=task.event_id))

    task.assignee_id = assignee.id
    db.session.commit()

    send_email(
        assignee.email,
        f"[CLB] Ban duoc chi dinh task: {task.ten_task}",
        f"Chao {assignee.ho_ten},\n\nBan da duoc chi dinh phu trach task "
        f"\"{task.ten_task}\", han hoan thanh: "
        f"{task.deadline.strftime('%d/%m/%Y %H:%M')}.\n\n-- AI Agent CLB",
    )

    flash("Da chi dinh lai nguoi phu trach task.", "success")
    return redirect(url_for("event.event_detail", event_id=task.event_id))


@event_bp.route("/task/<int:task_id>/nop-san-pham", methods=["POST"])
@login_required
@approved_required
def task_submit(task_id):
    """Chi nguoi duoc giao task moi duoc nop va tu doi trang thai -> cho_duyet."""
    task = Task.query.get_or_404(task_id)
    if task.assignee_id != current_user.id:
        abort(403)

    noi_dung_moi = request.form.get("noi_dung_nop", "").strip()
    # "Neu chua co thay doi trong o nop san pham thi trang thai khong duoc doi."
    if noi_dung_moi and noi_dung_moi != (task.noi_dung_nop or ""):
        task.noi_dung_nop = noi_dung_moi
        task.lan_nop_gan_nhat = datetime.utcnow()
        task.trang_thai = "cho_duyet"
        db.session.commit()

        nguoi_tao = User.query.get(task.event.tao_boi_id)
        if nguoi_tao:
            send_email(
                nguoi_tao.email,
                f"[CLB] Co san pham cho task \"{task.ten_task}\" cho duyet",
                f"Chao {nguoi_tao.ho_ten},\n\n{current_user.ho_ten} vua nop san pham "
                f"cho task \"{task.ten_task}\" (su kien \"{task.event.ten_su_kien}\"), "
                "dang cho BDH duyet.\n\n-- AI Agent CLB",
            )

        flash("Da nop san pham, cho BDH duyet.", "success")
    else:
        flash("Chua co thay doi noi dung nop, trang thai giu nguyen.", "error")
    return redirect(url_for("event.event_detail", event_id=task.event_id))


@event_bp.route("/task/<int:task_id>/cap-nhat-trang-thai", methods=["POST"])
@login_required
@bdh_required
def task_update_status(task_id):
    """BDH doi trang thai: lam_lai (can nhan xet) / hoan_thanh / huy. Khong duoc tu dat 'dang_lam' hay 'cho_duyet'."""
    task = Task.query.get_or_404(task_id)
    new_status = request.form.get("trang_thai")
    nhan_xet = request.form.get("nhan_xet_bdh", "").strip()

    if new_status not in ("lam_lai", "hoan_thanh", "huy"):
        abort(400)
    if new_status == "lam_lai" and not nhan_xet:
        flash("Phai nhap nhan xet khi yeu cau lam lai.", "error")
        return redirect(url_for("event.event_detail", event_id=task.event_id))

    task.trang_thai = new_status
    task.nhan_xet_bdh = nhan_xet or task.nhan_xet_bdh
    db.session.commit()

    status_label = {"lam_lai": "Lam lai", "hoan_thanh": "Hoan thanh", "huy": "Huy"}[new_status]
    body = (
        f"Chao {task.assignee.ho_ten},\n\nTask \"{task.ten_task}\" "
        f"(su kien \"{task.event.ten_su_kien}\") vua duoc BDH cap nhat trang thai: "
        f"{status_label}."
    )
    if nhan_xet:
        body += f"\n\nNhan xet cua BDH: {nhan_xet}"
    body += "\n\n-- AI Agent CLB"
    send_email(task.assignee.email, f"[CLB] Cap nhat task: {task.ten_task}", body)

    flash("Da cap nhat trang thai task.", "success")
    return redirect(url_for("event.event_detail", event_id=task.event_id))


@event_bp.route("/event/<int:event_id>/ket-thuc", methods=["POST"])
@login_required
@bdh_required
def event_end(event_id):
    """
    BDH danh dau su kien da ket thuc. Day la thoi diem duy nhat tinh
    trang hoat dong cua cac thanh vien lien quan (theo ban) duoc cap nhat lai.
    """
    ev = Event.query.get_or_404(event_id)
    ev.trang_thai = "da_ket_thuc"
    db.session.commit()

    cap_nhat_hoat_dong_khi_event_ket_thuc(ev)

    flash("Da danh dau su kien ket thuc va cap nhat lai tinh trang hoat dong lien quan.", "success")
    return redirect(url_for("event.event_detail", event_id=ev.id))
