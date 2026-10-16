"""Ranh giới bảo mật và xử lý lỗi an toàn cho mọi route (Ch10 – Middleware & Error handling).

- `configure_security`: kiểm tra cấu hình lúc khởi động (SECRET_KEY, debug, HTTPS),
  gắn ProxyFix khi chạy sau Nginx, bật log file.
- `install_hardening`: hook before/after_request (host allowlist, HTTPS, header
  bảo mật, CSP nonce, log thao tác) và error handler trả lỗi an toàn.
"""
import ipaddress
import logging
import os
import posixpath
import secrets
from datetime import timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path
from urllib.parse import urlsplit

from flask import abort, g, jsonify, request
from flask_login import current_user
from markupsafe import escape
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix


def configure_security(app):
    """Kiểm tra cấu hình lúc khởi động: APP_ENV hợp lệ, SECRET_KEY đủ mạnh ở production (dev tự tạo
    khóa trong instance/), cấm debug ở production, bật cookie Secure, gắn ProxyFix theo
    TRUST_PROXY_HOPS và mở file log instance/security.log.
    """
    if app.config.get("APP_ENV") not in {"development", "production"}:
        raise RuntimeError("APP_ENV must be development or production.")
    production = app.config.get("APP_ENV") == "production"
    key = app.config.get("SECRET_KEY")
    weak = not key or len(str(key)) < 32 or str(key).startswith(("replace-", "change-")) or str(key) in {
        "doi-key-nay-truoc-khi-deploy", "change-this-secret-key", "change-me"}
    if production and not app.config.get("TESTING") and weak:
        raise RuntimeError("Production requires an unpredictable SECRET_KEY of at least 32 characters.")
    if not key or (weak and not production and not app.config.get("TESTING")):
        if app.config.get("TESTING"):
            key = secrets.token_urlsafe(48)
        else:
            path = Path(app.instance_path) / "session-secret.key"
            try:
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError:
                key = path.read_text(encoding="ascii").strip()
                if len(key) < 32:
                    raise RuntimeError("Local session key is invalid; restore it before starting.")
            else:
                key = secrets.token_urlsafe(48)
                with os.fdopen(descriptor, "w", encoding="ascii") as handle:
                    handle.write(key)
            os.chmod(path, 0o600)
        app.config["SECRET_KEY"] = key
    if production:
        if app.config.get("DEBUG"):
            raise RuntimeError("Debug mode must be disabled in production.")
        if not app.config.get("SECURITY_TRUSTED_HOSTS"):
            raise RuntimeError("Production requires configured TRUSTED_HOSTS.")
        if app.config.get("MAIL_ENABLED") and not app.config.get("MAIL_USE_TLS") and not app.config.get("MAIL_USE_SSL"):
            raise RuntimeError("Production SMTP must use TLS or SSL.")
        app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_HTTPONLY=True)
    app.config.setdefault("PERMANENT_SESSION_LIFETIME", timedelta(hours=8))
    if production:
        app.config.update(REMEMBER_COOKIE_SECURE=True)
    # WSGI middleware: chỉ tin header X-Forwarded-* từ đúng số proxy đã khai báo.
    # Khi đứng sau Nginx (TRUST_PROXY_HOPS=1) Flask mới thấy đúng IP client và
    # scheme https; nếu không, kiểm tra HTTPS bên dưới sẽ chặn mọi request.
    hops = int(app.config.get("TRUST_PROXY_HOPS") or 0)
    if hops > 0:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=hops, x_proto=hops, x_host=hops, x_port=hops)
    if not app.config.get("TESTING"):
        log_path = Path(app.instance_path) / "security.log"
        handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
        os.chmod(log_path, 0o600)


def install_hardening(app):
    """Gắn hook before_request (host allowlist, bắt buộc HTTPS ở production, kiểm tra quyền xem ảnh
    upload), after_request (CSP có nonce, header bảo mật, Cache-Control, log thao tác) và error
    handler trả lỗi an toàn dạng HTML/JSON.
    """
    @app.before_request
    def request_boundary():
        g.request_id = secrets.token_hex(12)
        g.csp_nonce = secrets.token_urlsafe(24)
        try:
            host = urlsplit("http://" + request.host).hostname
        except ValueError:
            host = None
        trusted = set(app.config.get("SECURITY_TRUSTED_HOSTS", ()))
        allowed = bool(host and host.lower() in trusted)
        if not allowed and host and app.config.get("APP_ENV") != "production":
            try:
                allowed = ipaddress.ip_address(host).is_private
            except ValueError:
                pass
        if not allowed:
            abort(400, description="Tên máy chủ không hợp lệ.")
        if app.config.get("APP_ENV") == "production" and not app.config.get("TESTING") and not request.is_secure:
            abort(400, description="Hệ thống yêu cầu kết nối HTTPS.")
        static_name = (request.view_args or {}).get("filename", "") if request.endpoint == "static" else ""
        normalized_name = posixpath.normpath("/" + static_name.replace("\\", "/")).lstrip("/") if static_name else ""
        if normalized_name.startswith("uploads/"):
            from app.models import User
            from app.services.access import approved, can_view_member
            if not current_user.is_authenticated or not approved(current_user):
                abort(403)
            owner = User.query.filter_by(avatar_url="/static/" + normalized_name).first()
            if owner is None or not can_view_member(current_user, owner):
                abort(403)

    @app.context_processor
    def security_template_context():
        return {"csp_nonce": getattr(g, "csp_nonce", "")}

    @app.after_request
    def security_response(response):
        nonce = getattr(g, "csp_nonce", "")
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'nonce-" + nonce + "'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; "
            "connect-src 'self'; object-src 'none'; base-uri 'none'; "
            "frame-ancestors 'none'; form-action 'self'")
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["X-Request-ID"] = getattr(g, "request_id", "")
        try:
            authenticated = current_user.is_authenticated
            actor_id = current_user.id if authenticated else "anonymous"
        except Exception:
            authenticated, actor_id = False, "unavailable"
        if authenticated or request.path.startswith(("/login", "/register", "/ai", "/api/", "/password", "/confirm", "/reauth")):
            response.headers["Cache-Control"] = "private, no-store"
        if app.config.get("APP_ENV") == "production" and request.is_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        if response.status_code in {400, 401, 403, 429} or (request.method not in {"GET", "HEAD", "OPTIONS"}):
            app.logger.log(logging.WARNING if response.status_code >= 400 else logging.INFO,
                           "security_request endpoint=%s method=%s status=%s actor_id=%s request_id=%s",
                           request.endpoint or "unmatched", request.method, response.status_code,
                           actor_id,
                           getattr(g, "request_id", ""))
        return response

    def error_response(code):
        message = {400: "Yêu cầu không hợp lệ. Hãy tải lại trang và kiểm tra biểu mẫu.",
                   401: "Vui lòng đăng nhập.", 403: "Bạn không có quyền thực hiện thao tác này.",
                   404: "Không tìm thấy nội dung.", 409: "Dữ liệu đã thay đổi. Hãy tải lại rồi thử lại.",
                   413: "Dữ liệu tải lên vượt giới hạn.", 429: "Quá nhiều yêu cầu. Vui lòng thử lại sau.",
                   500: "Chưa thể xử lý yêu cầu. Vui lòng thử lại hoặc báo quản trị viên."}.get(code, "Không thể xử lý yêu cầu.")
        reference = getattr(g, "request_id", "")
        if request.path.startswith("/api/") or request.path == "/ai/stream" or request.is_json:
            return jsonify(error=message, request_id=reference), code
        return ("<!doctype html><html lang='vi'><meta charset='utf-8'><title>FIA</title>"
                "<h1>" + str(escape(message)) + "</h1><p>Mã hỗ trợ: " + str(escape(reference)) +
                "</p><a href='/'>Về trang FIA</a></html>"), code

    @app.errorhandler(HTTPException)
    def http_failure(error):
        response = app.make_response(error_response(error.code or 500))
        if error.code == 405 and getattr(error, "valid_methods", None):
            response.headers["Allow"] = ", ".join(error.valid_methods)
        if error.code == 429:
            response.headers["Retry-After"] = str(app.config.get("LOGIN_LOCKOUT_SECONDS", 300))
        return response

    @app.errorhandler(Exception)
    def unexpected_failure(error):
        from app import db
        db.session.rollback()
        # Ghi đủ stack trace vào log server (Ch10 – slide 32, 34); người dùng chỉ
        # thấy thông báo chung kèm mã hỗ trợ request_id để đối chiếu log.
        app.logger.exception("unhandled_exception type=%s path=%s request_id=%s",
                             type(error).__name__, request.path, getattr(g, "request_id", ""))
        if app.config.get("TESTING"):
            raise error
        return error_response(500)
