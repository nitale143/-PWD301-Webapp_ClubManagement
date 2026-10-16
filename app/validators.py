"""Quy tắc kiểm tra dữ liệu dùng chung cho form (WTForms) và REST API.

Nguyên tắc "Zero Trust" (Ch4 – slide 28-29): mọi dữ liệu người dùng gửi lên
đều được kiểm tra lại ở server, kể cả khi trình duyệt đã kiểm tra.
"""
import re
import unicodedata

from wtforms.validators import ValidationError

MSSV_RE = re.compile(r"^[A-Za-z0-9]{6,15}$")
PHONE_RE = re.compile(r"^0\d{9,10}$")
FACEBOOK_RE = re.compile(r"^https?://(www\.)?facebook\.com/.+$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

PASSWORD_MIN = 8
PASSWORD_MAX = 128
COMMON_PASSWORDS = frozenset({
    "12345678", "123456789", "1234567890", "password", "password1", "password123",
    "qwerty123", "11111111", "abc12345", "matkhau123", "iloveyou1", "admin123",
})


def contains_control(value):
    """True nếu chuỗi có ký tự điều khiển (xuống dòng, tab, ký tự ẩn…)."""
    return any(unicodedata.category(char).startswith("C") for char in value or "")


def password_problems(password, mssv=None):
    """Trả về danh sách lý do mật khẩu chưa đủ mạnh (rỗng = hợp lệ).

    Chính sách (Ch6 – slide 79-80): 8–128 ký tự, có ít nhất một chữ cái và một
    chữ số, không chứa MSSV, không nằm trong danh sách mật khẩu phổ biến.
    """
    problems = []
    if not isinstance(password, str) or not PASSWORD_MIN <= len(password) <= PASSWORD_MAX:
        return [f"Mật khẩu phải có từ {PASSWORD_MIN} đến {PASSWORD_MAX} ký tự."]
    if not re.search(r"[^\W\d_]", password):
        problems.append("Mật khẩu phải có ít nhất một chữ cái.")
    if not re.search(r"\d", password):
        problems.append("Mật khẩu phải có ít nhất một chữ số.")
    if mssv and len(mssv) >= 4 and mssv.casefold() in password.casefold():
        problems.append("Mật khẩu không được chứa MSSV.")
    if password.casefold() in COMMON_PASSWORDS:
        problems.append("Mật khẩu quá phổ biến, hãy chọn mật khẩu khác.")
    return problems


class StrongPassword:
    """Validator WTForms tùy biến dùng `password_problems` (Ch6 – slide 80, Ch4 – slide 35).

    `mssv_field`: tên field MSSV trong cùng form (nếu có) để chặn mật khẩu chứa MSSV.
    """

    def __init__(self, mssv_field=None):
        """`mssv_field`: tên field MSSV trong form để chặn mật khẩu chứa MSSV."""
        self.mssv_field = mssv_field

    def __call__(self, form, field):
        """Chạy password_problems; có vấn đề thì báo ValidationError."""
        mssv = None
        if self.mssv_field and self.mssv_field in form:
            mssv = (form[self.mssv_field].data or "").strip()
        elif getattr(form, "mssv_value", None):
            mssv = form.mssv_value
        problems = password_problems(field.data or "", mssv)
        if problems:
            raise ValidationError(" ".join(problems))


class NoControlChars:
    """Chặn ký tự điều khiển trong các ô văn bản một dòng."""

    def __init__(self, message="Dữ liệu chứa ký tự không hợp lệ."):
        """Thông báo lỗi tùy chỉnh."""
        self.message = message

    def __call__(self, form, field):
        """Báo lỗi nếu chuỗi có ký tự điều khiển."""
        if isinstance(field.data, str) and contains_control(field.data):
            raise ValidationError(self.message)
