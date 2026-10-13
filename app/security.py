"""Session-backed CSRF guard for every unsafe browser request."""

import hmac
import secrets

from flask import abort, request, session

UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
CSRF_ERROR = "Phiên biểu mẫu không hợp lệ. Hãy tải lại trang."


def csrf_token():
    """Return a stable, unpredictable token for the current (including anonymous) session."""
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def _csrf_token_is_valid():
    supplied = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token", "")
    expected = session.get("_csrf_token", "")
    return bool(
        isinstance(supplied, str)
        and isinstance(expected, str)
        and supplied
        and expected
        and supplied.isascii()
        and expected.isascii()
        and len(supplied) <= 256
        and hmac.compare_digest(supplied, expected)
    )


def require_csrf():
    """Explicit guard for callers that also use this helper outside the global hook."""
    if not _csrf_token_is_valid():
        abort(400, description=CSRF_ERROR)


def install_csrf(app):
    """Require a session token on every unsafe method, including anonymous routes.

    Tokens are accepted in regular form fields or the X-CSRF-Token header. Origin
    headers are deliberately not used as an alternate authorization mechanism.
    """
    if app.extensions.get("session_csrf_guard"):
        return

    @app.before_request
    def _protect_unsafe_requests():
        if request.method in UNSAFE_METHODS and not _csrf_token_is_valid():
            abort(400, description=CSRF_ERROR)

    app.extensions["session_csrf_guard"] = True
