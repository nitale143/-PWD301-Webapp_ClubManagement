"""
Cac decorator kiem tra quyen han, dung chung cho moi blueprint.

Quy tac quyen han (theo yeu cau):
  CN > PCN > TB, ThuKy/ThuQuy > Thanh vien
  - TB chi duoc quan ly/quyen han voi thanh vien trong ban minh quan ly.
  - Nguoi quyen cao hon moi duoc chi dinh chuc vu cho nguoi thap hon
    (khong duoc chi nguoc lai).
"""
from functools import wraps
from flask import abort
from flask_login import current_user
from app.services.access import approved, is_board, can_manage_member


def approved_required(view_func):
    """Chi cho phep thanh vien da duoc BDH duyet (status == approved) truy cap."""

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if not approved(current_user):
            abort(403)
        return view_func(*args, **kwargs)

    return wrapped


def bdh_required(view_func):
    """Chỉ Ban chủ nhiệm (CN, PCN, TB) được truy cập."""

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not is_board(current_user):
            abort(403)
        return view_func(*args, **kwargs)

    return wrapped


def role_required(*roles):
    """Chi cac chuc vu duoc liet ke moi duoc truy cap. Vi du: @role_required('CN', 'PCN')"""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or not approved(current_user) or current_user.chuc_vu not in roles:
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator


def can_assign_role(assigner, target, new_role, current_counts):
    """
    Kiem tra assigner co duoc phep chi dinh new_role cho target khong.
    Tra ve (True, "") hoac (False, "ly do").
    """
    from app.config import Config

    order = Config.ROLE_ORDER
    if new_role not in order:
        return False, "Chuc vu khong hop le."
    if not approved(assigner) or not approved(target) or assigner.id == target.id:
        return False, "Chi duoc chi dinh cho thanh vien khac da duoc duyet."
    if assigner.chuc_vu not in {"CN", "PCN"} or not can_manage_member(assigner, target):
        return False, "Ban khong co quyen phan vai tro nay."
    if not assigner.outranks(target):
        return False, "Ban chi duoc thay doi chuc vu cua nguoi co quyen thap hon."

    # Nguoi chi dinh phai co quyen cao hon chuc vu moi (khong duoc ngang hoac thap hon)
    if order.index(assigner.chuc_vu) >= order.index(new_role):
        return False, "Ban khong co quyen chi dinh chuc vu nay (chi nguoi quyen cao hon moi duoc chi dinh xuong)."

    limit = Config.ROLE_LIMITS.get(new_role)
    if limit is not None and current_counts.get(new_role, 0) >= limit:
        return False, f"Da du so luong toi da cho chuc vu nay ({limit} nguoi)."

    return True, ""
