from datetime import datetime, timedelta

from app import db
from app.models import ActivityPoint, Attendance, ClubSetting, Event, EventDetail, EventRegistration, EventTargetBan, UserBan
from .access import is_board, require
from .common import DomainError, audit


DEFAULT_POINTS = {"on_time": 10, "late": 6, "excused": 0, "absent": -5, "pending": 0}
DEFAULT_THRESHOLDS = {"active": 75, "normal": 40, "inactive_days": 60}


def setting(key, defaults):
    row = db.session.get(ClubSetting, key)
    return {**defaults, **(row.value if row and isinstance(row.value, dict) else {})}


def sync_attendance_point(attendance, actor):
    registration = db.session.get(EventRegistration, attendance.registration_id)
    rules = setting("activity_point_rules", DEFAULT_POINTS)
    points = int(rules.get(attendance.trang_thai, 0))
    point = ActivityPoint.query.filter_by(
        user_id=registration.user_id, event_id=registration.event_id, loai="attendance"
    ).first()
    if point is None:
        point = ActivityPoint(user_id=registration.user_id, event_id=registration.event_id, loai="attendance")
        db.session.add(point)
    point.so_diem = points
    point.ly_do = f"Điểm danh: {attendance.trang_thai}"
    point.tao_boi_id = actor.id
    point.tao_luc = datetime.utcnow()
    return point


def manual_point(actor, member, points, reason, event=None, kind="manual"):
    require(is_board(actor))
    if kind not in {"manual", "special"}:
        raise DomainError("Loại điểm không hợp lệ.")
    reason = str(reason or "").strip()
    if not reason:
        raise DomainError("Điều chỉnh điểm phải có lý do.")
    try:
        points = int(points)
    except (TypeError, ValueError):
        raise DomainError("Điểm phải là số nguyên.") from None
    if abs(points) > 1000:
        raise DomainError("Điểm điều chỉnh vượt giới hạn cho phép.")
    point = ActivityPoint(
        user_id=member.id, event_id=event.id if event else None,
        so_diem=points, loai=kind, ly_do=reason, tao_boi_id=actor.id,
    )
    db.session.add(point)
    db.session.flush()
    audit(actor, "activity_point_manual", point, {"points": points, "reason": reason})
    db.session.commit()
    return point


def activity_stats(member, now=None):
    from .common import club_now
    event_now = now or club_now()
    audit_now = datetime.utcnow()
    member_bans = {link.ban_id for link in member.ban_links}
    eligible_count = 0
    events = Event.query.filter(
        Event.thoi_gian_bat_dau <= event_now,
        Event.trang_thai.notin_(["draft", "cancelled"]),
    ).all()
    for event in events:
        detail = db.session.get(EventDetail, event.id)
        if detail and not detail.tat_ca_thanh_vien:
            targets = {row.ban_id for row in EventTargetBan.query.filter_by(event_id=event.id)}
            if not targets.intersection(member_bans):
                continue
        eligible_count += 1
    registrations = EventRegistration.query.filter(
        EventRegistration.user_id == member.id,
        EventRegistration.trang_thai != "cancelled",
    ).all()
    attendance_rows = (
        Attendance.query.join(EventRegistration)
        .filter(EventRegistration.user_id == member.id)
        .all()
    )
    statuses = {name: sum(row.trang_thai == name for row in attendance_rows) for name in DEFAULT_POINTS}
    present = statuses["on_time"] + statuses["late"]
    rate = round(present * 100 / eligible_count, 1) if eligible_count else 0.0
    latest = max((row.checkin_luc for row in attendance_rows if row.checkin_luc), default=None)
    total_points = db.session.query(db.func.coalesce(db.func.sum(ActivityPoint.so_diem), 0)).filter(ActivityPoint.user_id == member.id).scalar()
    thresholds = setting("activity_thresholds", DEFAULT_THRESHOLDS)
    if not latest or latest < audit_now - timedelta(days=int(thresholds["inactive_days"])):
        classification = "Không hoạt động"
    elif rate >= int(thresholds["active"]):
        classification = "Tích cực"
    elif rate >= int(thresholds["normal"]):
        classification = "Bình thường"
    else:
        classification = "Ít hoạt động"
    return {
        "eligible": eligible_count, "registered": len(registrations), "present": present,
        "late": statuses["late"], "excused": statuses["excused"],
        "absent": statuses["absent"], "rate": rate, "points": int(total_points or 0),
        "latest": latest, "classification": classification,
    }
