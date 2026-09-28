from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from flask import current_app

from app import db
from app.models import AuditLog, MemberRecord


class DomainError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def club_now():
    """Event/task wall-clock values in the database are club-local naive datetimes."""
    return datetime.now(ZoneInfo(current_app.config["APP_TIMEZONE"])).replace(tzinfo=None)


def parse_date(value, label):
    try:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        raise DomainError(f"{label} không hợp lệ (YYYY-MM-DD).") from None


def parse_datetime(value, label):
    try:
        parsed = datetime.fromisoformat(str(value))
        return parsed.astimezone(ZoneInfo(current_app.config["APP_TIMEZONE"])).replace(tzinfo=None) if parsed.tzinfo else parsed
    except (TypeError, ValueError):
        raise DomainError(f"{label} không hợp lệ (ISO 8601).") from None


def parse_money(value, label="Số tiền", allow_zero=False):
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number.as_tuple().exponent < -2:
            raise InvalidOperation
        number = number.quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        raise DomainError(f"{label} phải là số tiền hợp lệ, tối đa 2 chữ số thập phân.") from None
    if number < 0 or (number == 0 and not allow_zero):
        raise DomainError(f"{label} phải {'lớn hơn hoặc bằng' if allow_zero else 'lớn hơn'} 0.")
    if number >= Decimal("1000000000000"):
        raise DomainError(f"{label} vượt giới hạn cho phép.")
    return number


def audit(actor, action, obj, details=None):
    entry = AuditLog(
        actor_id=getattr(actor, "id", None), action=action,
        object_type=obj.__class__.__name__, object_id=str(getattr(obj, "id", None) or getattr(obj, "user_id", "")),
        details=details or {},
    )
    db.session.add(entry)
    return entry


def member_record(user):
    record = db.session.get(MemberRecord, user.id)
    if record is None:
        record = MemberRecord(user_id=user.id, ngay_gia_nhap=user.ngay_tao.date() if user.ngay_tao else date.today())
        db.session.add(record)
    return record
