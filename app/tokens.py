"""Token có chữ ký và thời hạn (Ch6 – slide 91-92, itsdangerous).

Mỗi mục đích (purpose) dùng một `salt` riêng, nên token xác minh email không
thể dùng làm token đặt lại mật khẩu và ngược lại. Token chỉ được *ký*, không
mã hóa: không bỏ dữ liệu nhạy cảm vào payload.
"""
from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

PURPOSES = {"confirm": "email-confirm", "reset": "password-reset"}


def _serializer(purpose):
    """Bộ ký URLSafeTimedSerializer theo mục đích (mỗi mục đích một salt)."""
    if purpose not in PURPOSES:
        raise ValueError("Mục đích token không hợp lệ.")
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=PURPOSES[purpose])


def dumps(payload, purpose):
    """Ký payload thành token theo mục đích."""
    return _serializer(purpose).dumps(payload)


def loads(token, purpose, max_age):
    """Giải mã token; trả về None nếu sai chữ ký, sai mục đích hoặc hết hạn."""
    if not isinstance(token, str) or not token or len(token) > 1024:
        return None
    try:
        return _serializer(purpose).loads(token, max_age=max_age)
    except (SignatureExpired, BadSignature):
        return None
