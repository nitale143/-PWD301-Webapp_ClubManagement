from datetime import datetime
import re
from flask import Blueprint, current_app, jsonify, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Event, EventDetail, EventRegistration, EventFeedback, Task, User, Ban
from app.permissions import approved_required, bdh_required
from app.security import require_csrf
from app.mail import send_email
from app.activity import cap_nhat_hoat_dong_khi_event_ket_thuc
from app.services.common import DomainError, club_now, parse_datetime
from app.services.access import is_admin, is_board
from app.services.events import (
    cancel_registration, eligible, event_is_terminal, feedback, manual_attendance,
    qr_checkin, register, registration_open,
)
from app.services.ctftime import CalendarUnavailable, SOURCE_URL, calendar_data, event_by_id

event_bp = Blueprint("event", __name__)


def _can_manage_task(task):
    return is_admin(current_user)


@event_bp.route("/event")
@login_required
@approved_required
def event_list():
    events = Event.query.order_by(Event.thoi_gian_bat_dau.desc()).all()
    return render_template("event.html", events=events)


@event_bp.get("/api/ctftime/events")
@login_required
@approved_required
def ctftime_events():
    """Fetch the public feed only when an approved member opens its tab."""
    try:
        payload = calendar_data()
    except CalendarUnavailable as exc:
        response = jsonify(error=str(exc), source_url=SOURCE_URL)
        response.status_code = 503
    else:
        response = jsonify(payload)
    response.headers["Cache-Control"] = "private, no-store"
    return response


@event_bp.post("/event/import/ctftime")
@login_required
@approved_required
@bdh_required
def ctftime_import():
    """Create an FIA event from a server-verified public CTFtime calendar row."""
    require_csrf()
    source_id = request.form.get("event_id", "").strip()
    if not re.fullmatch(r"[1-9]\d{0,11}", source_id):
        flash("Mã sự kiện CTFtime không hợp lệ.", "error")
        return redirect(url_for("event.event_list"))

    code = f"CTF-{source_id}"
    existing = Event.query.filter_by(ma_su_kien=code).first()
    if existing:
        flash("Sự kiện FIA này đã được tạo trước đó.", "success")
        return redirect(url_for("event.event_list"))

    try:
        source_event, feed = event_by_id(source_id)
    except CalendarUnavailable:
        flash("Chưa thể xác minh sự kiện với lịch CTFtime. Hãy thử lại sau.", "error")
        return redirect(url_for("event.event_list"))
    if not source_event or not feed:
        flash("Không tìm thấy sự kiện này trong lịch công khai CTFtime.", "error")
        return redirect(url_for("event.event_list"))

    try:
        starts = parse_datetime(source_event["start"], "Thời gian bắt đầu")
        ends = parse_datetime(source_event["finish"], "Thời gian kết thúc")
    except DomainError:
        flash("Thời gian từ lịch CTFtime không hợp lệ.", "error")
        return redirect(url_for("event.event_list"))

    now = club_now()
    if ends <= starts or ends <= now:
        flash("Sự kiện CTFtime đã kết thúc hoặc có thời gian không hợp lệ.", "error")
        return redirect(url_for("event.event_list"))

    event = Event(
        ten_su_kien=("FIA tham gia " + str(source_event["title"]).strip())[:150],
        ma_su_kien=code,
        thoi_gian_bat_dau=starts,
        thoi_gian_ket_thuc=ends,
        trang_thai="dang_dien_ra" if starts <= now else "sap_dien_ra",
        tao_boi_id=current_user.id,
    )
    source_url = f"https://ctftime.org/event/{source_id}/"
    detail = EventDetail(
        loai="ctftime",
        noi_dung=f"FIA tham gia cuộc thi này, không phải đơn vị tổ chức.\nNguồn: {source_url}",
        dia_diem=(source_event.get("location") or "")[:300],
        phu_trach_id=current_user.id,
        tat_ca_thanh_vien=True,
    )
    try:
        db.session.add(event)
        db.session.flush()
        detail.event_id = event.id
        db.session.add(detail)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        duplicate = Event.query.filter_by(ma_su_kien=code).first()
        if duplicate:
            flash("Sự kiện FIA này đã được tạo trước đó.", "success")
            return redirect(url_for("event.event_list"))
        current_app.logger.exception("CTFtime event import failed while saving")
        flash("Chưa thể tạo sự kiện FIA. Hãy thử lại sau.", "error")
        return redirect(url_for("event.event_list"))

    if feed.get("stale"):
        flash("Đã tạo sự kiện FIA từ dữ liệu CTFtime đã lưu; lịch có thể chưa mới nhất.", "success")
    else:
        flash("Đã tạo sự kiện FIA từ CTFtime.", "success")
    return redirect(url_for("event.event_list"))


@event_bp.route("/event/new", methods=["GET", "POST"])
@login_required
@bdh_required
def event_new():
    if request.method == "POST":
        require_csrf()
        ma = request.form.get("ma_su_kien", "").strip()
        name = request.form.get("ten_su_kien", "").strip()
        try:
            starts = datetime.strptime(request.form.get("thoi_gian_bat_dau", ""), "%Y-%m-%dT%H:%M")
            ends = datetime.strptime(request.form.get("thoi_gian_ket_thuc", ""), "%Y-%m-%dT%H:%M")
            deadline_raw = request.form.get("han_dang_ky", "").strip()
            deadline = datetime.strptime(deadline_raw, "%Y-%m-%dT%H:%M") if deadline_raw else None
            capacity_raw = request.form.get("so_nguoi_toi_da", "").strip()
            capacity = int(capacity_raw) if capacity_raw else None
        except ValueError:
            flash("Thời gian hoặc số người tối đa không hợp lệ.", "error")
            return render_template("event_form.html", form=request.form)
        if not name or not ma:
            flash("Vui lòng nhập tên và mã sự kiện.", "error")
            return render_template("event_form.html", form=request.form)
        if starts <= club_now():
            flash("Thời gian bắt đầu phải sau thời điểm hiện tại (giờ CLB).", "error")
            return render_template("event_form.html", form=request.form)
        if ends <= starts:
            flash("Thời gian kết thúc phải sau thời gian bắt đầu.", "error")
            return render_template("event_form.html", form=request.form)
        if deadline and deadline > starts:
            flash("Hạn đăng ký không được sau thời gian bắt đầu.", "error")
            return render_template("event_form.html", form=request.form)
        if capacity is not None and capacity <= 0:
            flash("Số người tối đa phải lớn hơn 0.", "error")
            return render_template("event_form.html", form=request.form)
        if Event.query.filter_by(ma_su_kien=ma).first():
            flash("Ma su kien da ton tai, vui long chon ma khac.", "error")
            return render_template("event_form.html", form=request.form)

        ev = Event(
            ten_su_kien=name,
            ma_su_kien=ma,
            thoi_gian_bat_dau=starts,
            thoi_gian_ket_thuc=ends,
            trang_thai="sap_dien_ra",
            tao_boi_id=current_user.id,
        )
        db.session.add(ev)
        db.session.flush()
        db.session.add(EventDetail(event_id=ev.id, loai="other",
                                   noi_dung=request.form.get("noi_dung", "").strip(),
                                   dia_diem=request.form.get("dia_diem", "").strip(),
                                   han_dang_ky=deadline, so_nguoi_toi_da=capacity,
                                   phu_trach_id=current_user.id, tat_ca_thanh_vien=True))
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
    registration = EventRegistration.query.filter_by(event_id=event_id, user_id=current_user.id).first()
    registrations = EventRegistration.query.filter_by(event_id=event_id).order_by(EventRegistration.dang_ky_luc).all()
    detail = db.session.get(EventDetail, event_id)
    prior_feedback = EventFeedback.query.filter_by(event_id=event_id, user_id=current_user.id).first()
    return render_template(
        "event_detail.html", event=ev, bans=bans,
        is_bdh=is_board(current_user),
        is_board=is_board(current_user),
        registration=registration, registrations=registrations, detail=detail,
        can_register=registration_open(ev, detail) and eligible(ev, current_user),
        prior_feedback=prior_feedback,
    )


@event_bp.post("/event/<int:event_id>/register")
@login_required
@approved_required
def event_register(event_id):
    require_csrf()
    event = db.get_or_404(Event, event_id)
    try:
        registration, _created = register(current_user, event)
        flash("Đã đăng ký sự kiện." if registration.trang_thai == "registered" else "Đã vào danh sách chờ.", "success")
    except DomainError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("event.event_detail", event_id=event_id))


@event_bp.post("/event/<int:event_id>/cancel-registration")
@login_required
@approved_required
def event_cancel_registration(event_id):
    require_csrf()
    registration = EventRegistration.query.filter_by(event_id=event_id, user_id=current_user.id).first_or_404()
    try:
        cancel_registration(current_user, registration)
        flash("Đã hủy đăng ký.", "success")
    except DomainError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("event.event_detail", event_id=event_id))


@event_bp.route("/event/<int:event_id>/checkin/<token>", methods=["GET", "POST"])
@login_required
@approved_required
def event_qr_checkin(event_id, token):
    event = db.get_or_404(Event, event_id)
    if request.method == "POST":
        require_csrf()
        try:
            qr_checkin(current_user, token, expected_event_id=event_id)
            flash("Đã điểm danh thành công.", "success")
        except DomainError as exc:
            db.session.rollback()
            flash(str(exc), "error")
        return redirect(url_for("event.event_detail", event_id=event_id))
    return render_template("checkin_confirm.html", event=event, token=token)


@event_bp.post("/event/<int:event_id>/attendance/<int:registration_id>")
@login_required
@bdh_required
def event_manual_attendance(event_id, registration_id):
    require_csrf()
    registration = EventRegistration.query.filter_by(id=registration_id, event_id=event_id).first_or_404()
    try:
        manual_attendance(current_user, registration, request.form.get("status"), request.form.get("note", ""))
        flash("Đã cập nhật điểm danh.", "success")
    except DomainError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("event.event_detail", event_id=event_id))


@event_bp.post("/event/<int:event_id>/feedback")
@login_required
@approved_required
def event_feedback(event_id):
    require_csrf()
    event = db.get_or_404(Event, event_id)
    try:
        feedback(current_user, event, request.form.get("rating"), request.form.get("comment", ""))
        flash("Đã lưu đánh giá.", "success")
    except DomainError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("event.event_detail", event_id=event_id))


@event_bp.route("/event/<int:event_id>/task/new", methods=["POST"])
@login_required
@bdh_required
def task_new(event_id):
    """
    Tao task con. Nguoi phu trach BAT BUOC phai duoc chi dinh ngay tu dau
    (khong con co che mo cho thanh vien xung phong).
    """
    ev = Event.query.get_or_404(event_id)
    if event_is_terminal(ev):
        abort(400)

    assignee_mssv = request.form.get("assignee_mssv", "").strip()
    assignee = User.query.filter_by(mssv=assignee_mssv, status="approved").first()
    if not assignee:
        flash("Khong tim thay thanh vien voi MSSV nay. Task phai co nguoi phu trach ngay tu dau.", "error")
        return redirect(url_for("event.event_detail", event_id=ev.id))

    ban_id = request.form.get("ban_id", type=int)
    if not ban_id or not Ban.query.get(ban_id):
        flash("Ban hoat dong khong hop le.", "error")
        return redirect(url_for("event.event_detail", event_id=ev.id))
    if not any(link.ban_id == ban_id for link in assignee.ban_links):
        flash("Nguoi phu trach khong thuoc ban cua task.", "error")
        return redirect(url_for("event.event_detail", event_id=ev.id))
    try:
        deadline = datetime.strptime(request.form.get("deadline", ""), "%Y-%m-%dT%H:%M")
    except ValueError:
        flash("Han task khong hop le.", "error")
        return redirect(url_for("event.event_detail", event_id=ev.id))
    if not request.form.get("ten_task", "").strip() or deadline > ev.thoi_gian_ket_thuc:
        flash("Ten task hoac han task khong hop le.", "error")
        return redirect(url_for("event.event_detail", event_id=ev.id))

    task = Task(
        event_id=ev.id,
        ten_task=request.form.get("ten_task", "").strip(),
        mo_ta=request.form.get("mo_ta", "").strip(),
        deadline=deadline,
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
    if not _can_manage_task(task):
        abort(403)
    if event_is_terminal(task.event) or task.trang_thai in {"hoan_thanh", "huy"}:
        abort(400)
    mssv = request.form.get("assignee_mssv", "").strip()
    assignee = User.query.filter_by(mssv=mssv, status="approved").first()
    if not assignee:
        flash("Khong tim thay thanh vien voi MSSV nay.", "error")
        return redirect(url_for("event.event_detail", event_id=task.event_id))
    if task.ban_id and not any(link.ban_id == task.ban_id for link in assignee.ban_links):
        flash("Nguoi phu trach moi khong thuoc ban cua task.", "error")
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
    if task.trang_thai not in {"dang_lam", "lam_lai"} or event_is_terminal(task.event):
        abort(400)

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
    if not _can_manage_task(task):
        abort(403)
    if event_is_terminal(task.event) or task.trang_thai in {"hoan_thanh", "huy"}:
        abort(400)
    new_status = request.form.get("trang_thai")
    nhan_xet = request.form.get("nhan_xet_bdh", "").strip()

    if new_status not in ("lam_lai", "hoan_thanh", "huy"):
        abort(400)
    if new_status in {"lam_lai", "hoan_thanh"} and task.trang_thai != "cho_duyet":
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
    if event_is_terminal(ev):
        abort(400)
    ev.trang_thai = "da_ket_thuc"
    db.session.commit()

    cap_nhat_hoat_dong_khi_event_ket_thuc(ev)

    flash("Da danh dau su kien ket thuc va cap nhat lai tinh trang hoat dong lien quan.", "success")
    return redirect(url_for("event.event_detail", event_id=ev.id))
