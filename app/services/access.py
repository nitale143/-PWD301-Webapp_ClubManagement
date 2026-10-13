from app import db
from app.models import MemberRecord, User, UserBan
from .common import DomainError


def approved(user):
    if not user or user.status != "approved":
        return False
    record = db.session.get(MemberRecord, user.id)
    return record is None or (record.luu_tru_luc is None and record.tinh_trang != "left")


ADMIN_ROLES = frozenset({"CN", "PCN", "TB", "THUKY_THUQUY"})
MEMBER_ROLE = "THANH_VIEN"


def is_admin(user):
    return approved(user) and user.chuc_vu in ADMIN_ROLES


def is_board(user):
    return is_admin(user)


def is_treasurer(user):
    return is_admin(user)


def can_view_all_members(user):
    return is_admin(user)


def can_manage_member(actor, target):
    return bool(is_admin(actor) and target and actor.id != target.id)


def _active_admin_count():
    return (db.session.query(db.func.count(User.id))
            .outerjoin(MemberRecord, User.id == MemberRecord.user_id)
            .filter(User.status == "approved", User.chuc_vu.in_(ADMIN_ROLES),
                    db.or_(MemberRecord.user_id.is_(None), db.and_(
                        MemberRecord.luu_tru_luc.is_(None),
                        MemberRecord.tinh_trang != "left")))
            .scalar_subquery())


def _active_member_row(user_id):
    active = (db.session.query(MemberRecord.user_id)
              .filter(MemberRecord.user_id == user_id,
                      MemberRecord.luu_tru_luc.is_(None),
                      MemberRecord.tinh_trang != "left").exists())
    missing = ~db.session.query(MemberRecord.user_id).filter(
        MemberRecord.user_id == user_id).exists()
    return db.or_(active, missing)


def set_member_role_safely(target, new_role):
    """Atomically update a role without removing the last active admin."""
    old_role = target.chuc_vu
    conditions = [User.id == target.id, User.status == "approved",
                  User.chuc_vu == old_role, _active_member_row(User.id)]
    if old_role in ADMIN_ROLES and new_role not in ADMIN_ROLES:
        conditions.append(_active_admin_count() > 1)
    result = db.session.execute(
        db.update(User).where(*conditions).values(chuc_vu=new_role)
    )
    if result.rowcount != 1:
        return False
    db.session.expire(target, ["chuc_vu"])
    return True


def set_member_left_safely(target, record, archived_at=None):
    """Mark a member left while atomically preserving one active admin."""
    values = {"tinh_trang": "left"}
    if archived_at is not None:
        values["luu_tru_luc"] = archived_at
    conditions = [MemberRecord.user_id == target.id]
    active_admin_in_database = db.session.query(User.id).filter(
        User.id == target.id, User.status == "approved", User.chuc_vu.in_(ADMIN_ROLES),
        _active_member_row(User.id)).exists()
    conditions.append(db.or_(~active_admin_in_database, _active_admin_count() > 1))
    result = db.session.execute(
        db.update(MemberRecord).where(*conditions).values(**values)
    )
    if result.rowcount != 1:
        return False
    record.tinh_trang = "left"
    if archived_at is not None:
        record.luu_tru_luc = archived_at
    return True


def can_view_member(actor, target):
    return bool(actor and target and (actor.id == target.id or can_view_all_members(actor) or can_manage_member(actor, target)))


def require(condition, message="Bạn không có quyền thực hiện thao tác này."):
    if not condition:
        raise DomainError(message, 403)


def require_current_approval(actor):
    """Re-read account and membership after a potentially slow external call."""
    db.session.refresh(actor)
    record = db.session.get(MemberRecord, actor.id, populate_existing=True)
    require(actor.status == "approved" and (record is None or (
        record.luu_tru_luc is None and record.tinh_trang != "left")),
        "Tài khoản không còn quyền sử dụng AI.")
    # Refresh relationship rows too: refreshing User alone can retain cached ban roles.
    UserBan.query.filter_by(user_id=actor.id).populate_existing().all()
    db.session.expire(actor, ["ban_links"])


def actor_scope_stamp(actor):
    return actor.chuc_vu


def require_unchanged_scope(actor, stamp):
    require(stamp == actor_scope_stamp(actor),
            "Quyền hoặc ban phụ trách đã thay đổi trong lúc xử lý. Hãy gửi yêu cầu mới.")


def visible_members(actor):
    query = User.query.filter_by(status="approved").outerjoin(MemberRecord, User.id == MemberRecord.user_id).filter(MemberRecord.luu_tru_luc.is_(None))
    if can_view_all_members(actor):
        return query
    return query.filter(User.id == getattr(actor, "id", -1))
