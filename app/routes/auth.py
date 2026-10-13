from collections import deque
from datetime import datetime
import hashlib
import hmac
import re
import secrets
import threading
import time
from urllib.parse import urlsplit

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.models import Ban, User, UserBan
from app.security import csrf_token
from app.validators import validate_registration
from app.services.access import approved


auth_bp = Blueprint("auth", __name__)
_MSSV_RE = re.compile(r"^[A-Za-z0-9_-]{1,20}$")
_DUMMY_PASSWORD_HASH = generate_password_hash(secrets.token_urlsafe(32))
_GENERIC_LOGIN_ERROR = "MSSV hoặc mật khẩu không đúng."


class _LoginRateLimiter:
    """Per-app in-memory login throttling keyed by IP and a keyed account digest."""

    def __init__(self):
        self._lock = threading.Lock()
        self._attempts = {}

    def is_locked(self, key, now):
        with self._lock:
            entry = self._attempts.get(key)
            if not entry:
                return False
            if entry["locked_until"] > now:
                return True
            if entry["locked_until"]:
                self._attempts.pop(key, None)
                return False
            return False

    def failed(self, key, now, *, max_attempts, window_seconds, lockout_seconds):
        cutoff = now - window_seconds
        with self._lock:
            entry = self._attempts.setdefault(key, {"timestamps": deque(), "locked_until": 0})
            timestamps = entry["timestamps"]
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()
            timestamps.append(now)
            if len(timestamps) >= max_attempts:
                entry["locked_until"] = now + lockout_seconds

            if len(self._attempts) > 4096:
                for stale_key, stale in list(self._attempts.items()):
                    if stale["locked_until"] <= now and not stale["timestamps"]:
                        self._attempts.pop(stale_key, None)
                while len(self._attempts) > 4096:
                    self._attempts.pop(next(iter(self._attempts)))

    def succeeded(self, key):
        with self._lock:
            self._attempts.pop(key, None)


def _safe_next(value):
    """Allow only a same-site root-relative redirect target."""
    if not isinstance(value, str) or not value or len(value) > 2048:
        return None
    if "\\" in value or any(ord(char) < 32 for char in value):
        return None
    lowered = value.lower()
    if "%2f" in lowered or "%5c" in lowered:
        return None
    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    if parsed.scheme or parsed.netloc or not parsed.path.startswith("/") or parsed.path.startswith("//"):
        return None
    return value


def _limiter_settings():
    cfg = current_app.config
    return (
        max(1, int(cfg.get("LOGIN_MAX_ATTEMPTS", 5))),
        max(1, int(cfg.get("LOGIN_WINDOW_SECONDS", 300))),
        max(1, int(cfg.get("LOGIN_LOCKOUT_SECONDS", 300))),
    )


def _login_limiter():
    limiter = current_app.extensions.get("login_rate_limiter")
    if limiter is None:
        limiter = _LoginRateLimiter()
        current_app.extensions["login_rate_limiter"] = limiter
    return limiter


def _login_key(mssv):
    address = request.remote_addr or "unknown"
    secret = str(current_app.config.get("SECRET_KEY") or "development-key")
    material = f"{address}\0{mssv.casefold()}".encode("utf-8", "replace")
    return hmac.new(secret.encode("utf-8"), material, hashlib.sha256).hexdigest()


def _login_failed():
    current_app.logger.warning("Login rejected")
    flash(_GENERIC_LOGIN_ERROR, "error")
    return render_template("login.html", next_target=_safe_next(request.form.get("next")))


def _existing_session_redirect():
    if current_user.status == "pending":
        return redirect(url_for("auth.pending"))
    if current_user.status == "approved" and approved(current_user):
        return redirect(url_for("main.home"))
    logout_user()
    session.clear()
    return None


@auth_bp.route("/", methods=["GET"])
def index():
    """Public FIA landing page; signed-in users continue to the member workspace."""
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    return render_template("landing.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        response = _existing_session_redirect()
        if response:
            return response

    if request.method == "POST":
        mssv = request.form.get("mssv", "").strip()
        password = request.form.get("password", "")
        key = _login_key(mssv[:256])
        limiter_enabled = current_app.config.get("LOGIN_LIMIT_ENABLED", True)
        limiter = _login_limiter() if limiter_enabled else None
        max_attempts, window_seconds, lockout_seconds = _limiter_settings()

        if limiter and limiter.is_locked(key, time.monotonic()):
            current_app.logger.warning("Login rate limit exceeded")
            return _login_failed()

        valid_mssv = bool(_MSSV_RE.fullmatch(mssv))
        user = User.query.filter_by(mssv=mssv).first() if valid_mssv else None
        bounded_password = password[:128]
        password_matches = (
            user.check_password(bounded_password)
            if user is not None
            else check_password_hash(_DUMMY_PASSWORD_HASH, bounded_password)
        )

        if (not valid_mssv or len(password) > 128 or user is None or not password_matches
                or user.status not in {"approved", "pending"}
                or (user.status == "approved" and not approved(user))):
            if limiter:
                limiter.failed(
                    key,
                    time.monotonic(),
                    max_attempts=max_attempts,
                    window_seconds=window_seconds,
                    lockout_seconds=lockout_seconds,
                )
            return _login_failed()

        if limiter:
            limiter.succeeded(key)
        session.clear()
        login_user(user)
        session.permanent = True
        csrf_token()
        if user.status == "pending":
            return redirect(url_for("auth.pending"))
        return redirect(_safe_next(request.form.get("next")) or url_for("main.home"))

    return render_template("login.html", next_target=_safe_next(request.args.get("next")))


@auth_bp.route("/pending")
@login_required
def pending():
    if current_user.status != "pending":
        return redirect(url_for("main.home"))
    return render_template("pending.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        response = _existing_session_redirect()
        if response:
            return response

    bans = Ban.query.all()

    if request.method == "POST":
        errors = validate_registration(request.form)
        mssv = request.form.get("mssv", "").strip()
        if not errors and User.query.filter_by(mssv=mssv).first():
            errors["mssv"] = "MSSV này đã được đăng ký."

        if errors:
            return render_template("register.html", bans=bans, errors=errors, form=request.form)

        selected_ban_ids = list(dict.fromkeys(
            int(ban_id) for ban_id in request.form.getlist("ban_hoat_dong")
        ))
        user = User(
            mssv=mssv,
            ho_ten=request.form.get("ho_ten", "").strip(),
            ngay_sinh=datetime.strptime(request.form.get("ngay_sinh"), "%Y-%m-%d").date(),
            sdt=request.form.get("sdt", "").strip(),
            email=request.form.get("email", "").strip(),
            facebook_link=request.form.get("facebook_link", "").strip(),
            status="pending",
            chuc_vu="THANH_VIEN",
        )
        user.set_password(request.form.get("password"))
        try:
            db.session.add(user)
            db.session.flush()
            for ban_id in selected_ban_ids:
                db.session.add(UserBan(user_id=user.id, ban_id=ban_id))
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            if User.query.filter_by(mssv=mssv).first():
                errors["mssv"] = "MSSV này đã được đăng ký."
            else:
                current_app.logger.warning("Registration rejected by a database constraint")
                flash("Không thể hoàn tất đăng ký lúc này. Vui lòng kiểm tra thông tin và thử lại.", "error")
            return render_template("register.html", bans=bans, errors=errors, form=request.form)

        flash("Đăng ký thành công! Vui lòng chờ BĐH xét duyệt.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", bans=bans, errors={}, form={})


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("auth.login"))
