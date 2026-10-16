"""Bảo vệ CSRF (Flask-WTF) và các chốt chặn tài khoản dùng chung.

CSRF (Ch4 – slide 20-22, 42): `CSRFProtect` được bật cho toàn app trong
`create_app()`; mọi request POST/PUT/PATCH/DELETE phải gửi token qua field
`csrf_token` của form hoặc header `X-CSRFToken` / `X-CSRF-Token` (AJAX).
Template lấy token bằng `{{ csrf_token() }}` hoặc `{{ form.hidden_tag() }}`.
"""
from flask import jsonify, redirect, request, url_for
from flask_login import current_user
from flask_wtf.csrf import generate_csrf

from app import csrf

# Các endpoint vẫn dùng được khi tài khoản đang bị buộc đổi mật khẩu
_PASSWORD_CHANGE_ALLOWED = frozenset({
    "auth.change_password", "auth.logout", "auth.reauthenticate", "auth.pending", "static",
})


def csrf_token():
    """Token CSRF cho session hiện tại (giữ tên cũ cho code/test đang gọi)."""
    return generate_csrf()


def require_csrf():
    """Kiểm tra CSRF tường minh trong view.

    CSRFProtect đã kiểm tra trước mọi view; hàm này giữ lại để các view nhạy
    cảm thể hiện rõ yêu cầu và vẫn an toàn nếu sau này view được `csrf.exempt`.
    """
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        csrf.protect()


def install_account_guards(app):
    """Hook trước mỗi request:

    - CSRFProtect bỏ qua URL không khớp route nào; hook này vẫn đòi token cho
      mọi request ghi dữ liệu để hành vi đồng nhất (trả 400 thay vì 404).
    - Tài khoản bị đánh dấu `must_change_password` (mật khẩu tạm / tài khoản
      import) chỉ được vào trang đổi mật khẩu.
    """

    @app.before_request
    def _csrf_for_unmatched_routes():
        if (request.endpoint is None and request.method in {"POST", "PUT", "PATCH", "DELETE"}
                and app.config.get("WTF_CSRF_ENABLED", True)):
            csrf.protect()

    @app.before_request
    def _force_password_change():
        if not current_user.is_authenticated or not getattr(current_user, "must_change_password", False):
            return None
        if request.endpoint in _PASSWORD_CHANGE_ALLOWED:
            return None
        if request.path.startswith("/api/"):
            return jsonify(error="Bạn cần đổi mật khẩu trước khi tiếp tục."), 403
        return redirect(url_for("auth.change_password"))
