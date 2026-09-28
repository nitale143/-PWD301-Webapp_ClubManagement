import secrets
from datetime import datetime, timedelta

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app import db
from app.models import (
    Attendance, Event, EventDetail, EventFeedback, EventRegistration,
    EventTargetBan, QRCheckinLog, User,
)
from .access import approved, is_board, require
from .activities import sync_attendance_point
from .common import DomainError, audit, parse_datetime


QR_TTL_SECONDS = 15 * 60
REGISTRATION_STATES = {"registered", "waitlist", "cancelled"}
ATTENDANCE_STATES = {"on_time", "late", "excused", "absent", "pending"}


def _serializer():
    return URLSafeTimedSerializer(current_app.secret_key, salt="event-checkin")


def registration_open(event, detail, now=None):
    now = now or datetime.utcnow()
    return event.trang_thai in {"sap_dien_ra", "open"} and (not detail or not detail.han_dang_ky or now <= detail.han_dang_ky)


def eligible(event, member):
    detail = db.session.get(EventDetail, event.id)
    if not detail or detail.tat_ca_thanh_vien:
        return True
    target_ids = {row.ban_id for row in EventTargetBan.query.filter_by(event_id=event.id)}
    return bool(target_ids.intersection(link.ban_id for link in member.ban_links))


def register(actor, event, member=None):
    member = member or actor
    require(approved(actor) and (actor.id == member.id or is_board(actor)))
    if not approved(member):
        raise DomainError("Thành viên chưa được duyệt.")
    detail = db.session.get(EventDetail, event.id)
    if not registration_open(event, detail):
        raise DomainError("Sự kiện hiện không mở đăng ký.")
    if not eligible(event, member):
        raise DomainError("Thành viên không thuộc đối tượng được tham gia.", 403)
    registration = EventRegistration.query.filter_by(event_id=event.id, user_id=member.id).first()
    if registration and registration.trang_thai != "cancelled":
        return registration, False
    count = EventRegistration.query.filter_by(event_id=event.id, trang_thai="registered").count()
    capacity = detail.so_nguoi_toi_da if detail else None
    state = "waitlist" if capacity and count >= capacity else "registered"
    if registration is None:
        registration = EventRegistration(event_id=event.id, user_id=member.id)
        db.session.add(registration)
    registration.trang_thai = state
    registration.dang_ky_luc = datetime.utcnow()
    registration.huy_luc = None
    db.session.flush()
    audit(actor, "event_registration", registration, {"event_id": event.id, "member_id": member.id, "state": state})
    db.session.commit()
    return registration, True


def cancel_registration(actor, registration):
    require(approved(actor) and (actor.id == registration.user_id or is_board(actor)))
    if registration.trang_thai == "cancelled":
        return None
    if registration.attendance and registration.attendance.trang_thai != "pending":
        raise DomainError("Không thể hủy đăng ký sau khi đã điểm danh.")
    freed_slot = registration.trang_thai == "registered"
    registration.trang_thai = "cancelled"
    registration.huy_luc = datetime.utcnow()
    promoted = None
    if freed_slot:
        promoted = EventRegistration.query.filter_by(
            event_id=registration.event_id, trang_thai="waitlist"
        ).order_by(EventRegistration.dang_ky_luc, EventRegistration.id).first()
        if promoted:
            promoted.trang_thai = "registered"
    audit(actor, "event_registration_cancel", registration, {"promoted_id": promoted.id if promoted else None})
    db.session.commit()
    return promoted


def qr_token(actor, event):
    require(is_board(actor))
    return _serializer().dumps({"event_id": event.id, "nonce": secrets.token_urlsafe(12)})


def qr_checkin(actor, token, now=None):
    require(approved(actor))
    try:
        payload = _serializer().loads(str(token or ""), max_age=QR_TTL_SECONDS)
    except SignatureExpired:
        raise DomainError("Mã QR đã hết hạn.") from None
    except BadSignature:
        raise DomainError("Mã QR không hợp lệ.") from None
    event = db.session.get(Event, payload.get("event_id"))
    if not event:
        raise DomainError("Không tìm thấy sự kiện của mã QR.", 404)
    now = now or datetime.utcnow()
    if event.trang_thai in {"cancelled", "da_ket_thuc"} or not (event.thoi_gian_bat_dau - timedelta(minutes=30) <= now <= event.thoi_gian_ket_thuc):
        raise DomainError("Chỉ được điểm danh trong thời gian diễn ra sự kiện.")
    registration = EventRegistration.query.filter_by(event_id=event.id, user_id=actor.id, trang_thai="registered").first()
    if not registration:
        raise DomainError("Bạn chưa đăng ký sự kiện này.")
    attendance = Attendance.query.filter_by(registration_id=registration.id).first()
    if (attendance and attendance.checkin_luc) or QRCheckinLog.query.filter_by(event_id=event.id, user_id=actor.id).first():
        raise DomainError("Bạn đã điểm danh sự kiện này rồi.")
    if attendance is None:
        attendance = Attendance(registration_id=registration.id)
        db.session.add(attendance)
    attendance.trang_thai = "late" if now > event.thoi_gian_bat_dau else "on_time"
    attendance.checkin_luc = now
    attendance.checkin_boi_id = actor.id
    db.session.add(QRCheckinLog(event_id=event.id, user_id=actor.id, account_id=actor.id, checkin_luc=now))
    sync_attendance_point(attendance, actor)
    db.session.flush()
    audit(actor, "qr_checkin", attendance, {"event_id": event.id})
    db.session.commit()
    return attendance


def manual_attendance(actor, registration, state, note=""):
    require(is_board(actor))
    if state not in ATTENDANCE_STATES:
        raise DomainError("Trạng thái điểm danh không hợp lệ.")
    if registration.trang_thai != "registered":
        raise DomainError("Chỉ điểm danh thành viên đã đăng ký chính thức.")
    attendance = Attendance.query.filter_by(registration_id=registration.id).first()
    if attendance is None:
        attendance = Attendance(registration_id=registration.id)
        db.session.add(attendance)
    attendance.trang_thai = state
    attendance.checkin_boi_id = actor.id
    attendance.checkin_luc = datetime.utcnow() if state in {"on_time", "late"} else None
    attendance.ghi_chu = str(note or "").strip()
    sync_attendance_point(attendance, actor)
    db.session.flush()
    audit(actor, "attendance_manual", attendance, {"state": state})
    db.session.commit()
    return attendance


def feedback(actor, event, rating, comment=""):
    require(approved(actor))
    if event.trang_thai not in {"da_ket_thuc", "completed"}:
        raise DomainError("Chỉ phản hồi sau khi sự kiện kết thúc.")
    registration = EventRegistration.query.filter_by(event_id=event.id, user_id=actor.id, trang_thai="registered").first()
    if not registration:
        raise DomainError("Bạn chưa tham gia sự kiện này.", 403)
    try:
        rating = int(rating)
    except (TypeError, ValueError):
        raise DomainError("Đánh giá phải từ 1 đến 5.") from None
    if not 1 <= rating <= 5:
        raise DomainError("Đánh giá phải từ 1 đến 5.")
    row = EventFeedback.query.filter_by(event_id=event.id, user_id=actor.id).first()
    if row is None:
        row = EventFeedback(event_id=event.id, user_id=actor.id)
        db.session.add(row)
    row.danh_gia = rating
    row.binh_luan = str(comment or "").strip()
    db.session.flush()
    audit(actor, "event_feedback", row, {"event_id": event.id})
    db.session.commit()
    return row
