"""
Cac decorator kiem tra quyen han, dung chung cho moi blueprint.

Quyền quản trị dùng chung cho các chức vụ CN, PCN, TB và THUKY_THUQUY.
THANH_VIEN chỉ có quyền trong phạm vi dữ liệu của chính mình.
"""
from functools import wraps
from flask import abort
from flask_login import current_user
from app.services.access import ADMIN_ROLES, approved, is_admin, is_board, can_manage_member


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
    """Chỉ tài khoản quản trị đã được duyệt mới được truy cập."""

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not is_board(current_user):
            abort(403)
        return view_func(*args, **kwargs)

    return wrapped


def role_required(*roles):
    """Chi cac chuc vu duoc liet ke moi duoc truy cap. Vi du: @role_required('CN', 'PCN')"""
    admin_only = bool(roles) and set(roles).issubset(ADMIN_ROLES)

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or not (
                    is_admin(current_user) if admin_only else
                    approved(current_user) and current_user.chuc_vu in roles):
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
    if not is_admin(assigner) or not can_manage_member(assigner, target):
        return False, "Ban khong co quyen phan vai tro nay."
    if new_role == "CN":
        return False, "Vui lòng dùng quy trình nhường quyền để chỉ định Chủ nhiệm."

    limit = Config.ROLE_LIMITS.get(new_role)
    if limit is not None and current_counts.get(new_role, 0) >= limit:
        return False, f"Da du so luong toi da cho chuc vu nay ({limit} nguoi)."

    return True, ""
