from app import db
from app.models import MemberRecord, User, UserBan
from .common import DomainError


def approved(user):
    if not user or user.status != "approved":
        return False
    record = db.session.get(MemberRecord, user.id)
    return record is None or (record.luu_tru_luc is None and record.tinh_trang != "left")


def is_admin(user):
    return approved(user) and user.chuc_vu == "CN"


def is_board(user):
    return approved(user) and user.chuc_vu in {"CN", "PCN", "TB"}


def is_treasurer(user):
    return approved(user) and user.chuc_vu in {"CN", "THUKY_THUQUY"}


def can_view_all_members(user):
    return approved(user) and user.chuc_vu in {"CN", "PCN", "THUKY_THUQUY"}


def can_manage_member(actor, target):
    if not approved(actor) or not target or actor.id == target.id:
        return False
    if actor.chuc_vu in {"CN", "PCN"}:
        return True
    if actor.chuc_vu == "TB":
        managed = set(actor.quan_ly_ban_ids())
        return bool(managed.intersection(link.ban_id for link in target.ban_links))
    return False


def can_view_member(actor, target):
    return bool(actor and target and (actor.id == target.id or can_view_all_members(actor) or can_manage_member(actor, target)))


def require(condition, message="Bạn không có quyền thực hiện thao tác này."):
    if not condition:
        raise DomainError(message, 403)


def visible_members(actor):
    query = User.query.filter_by(status="approved").outerjoin(MemberRecord, User.id == MemberRecord.user_id).filter(MemberRecord.luu_tru_luc.is_(None))
    if can_view_all_members(actor):
        return query
    if approved(actor) and actor.chuc_vu == "TB":
        ban_ids = actor.quan_ly_ban_ids()
        return query.filter(db.or_(User.id == actor.id, User.id.in_(db.session.query(UserBan.user_id).filter(UserBan.ban_id.in_(ban_ids)))))
    return query.filter(User.id == getattr(actor, "id", -1))
