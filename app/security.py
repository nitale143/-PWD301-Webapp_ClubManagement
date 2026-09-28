"""Small session-backed CSRF guard for sensitive browser forms."""

import hmac
import secrets

from flask import abort, request, session


def csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def require_csrf():
    supplied = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token", "")
    expected = session.get("_csrf_token", "")
    if not supplied or not expected or not hmac.compare_digest(supplied, expected):
        abort(400, description="Phiên biểu mẫu không hợp lệ. Hãy tải lại trang.")
