import re
import unicodedata
from datetime import datetime

MSSV_RE = re.compile(r"^[A-Za-z0-9]{6,15}$")
PHONE_RE = re.compile(r"^0\d{9,10}$")
FACEBOOK_RE = re.compile(r"^https?://(www\.)?facebook\.com/.+$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_registration(form):
    """
    Nhan vao request.form, tra ve dict {field: error_message}.
    Dict rong nghia la hop le.
    """
    errors = {}

    ho_ten = _text(form, "ho_ten")
    if not 2 <= len(ho_ten) <= 100 or _contains_control(ho_ten):
        errors["ho_ten"] = "Ho va ten khong hop le."

    mssv = _text(form, "mssv")
    if not MSSV_RE.fullmatch(mssv):
        errors["mssv"] = "MSSV phai gom 6-15 ky tu chu/so."

    ngay_sinh = _text(form, "ngay_sinh")
    try:
        dob = datetime.strptime(ngay_sinh, "%Y-%m-%d").date()
        if dob.year < 1980 or dob >= datetime.utcnow().date():
            errors["ngay_sinh"] = "Ngay sinh khong hop le."
    except (TypeError, ValueError, OverflowError):
        errors["ngay_sinh"] = "Dinh dang ngay sinh khong hop le (YYYY-MM-DD)."

    ban_ids = form.getlist("ban_hoat_dong") if hasattr(form, "getlist") else form.get("ban_hoat_dong")
    if not ban_ids:
        errors["ban_hoat_dong"] = "Vui long chon it nhat 1 ban hoat dong."
    else:
        from app.models import Ban
        ids = ban_ids if isinstance(ban_ids, (list, tuple)) else [ban_ids]
        if len(ids) > 20:
            errors["ban_hoat_dong"] = "Ban hoat dong khong hop le."
            ids = []
        try:
            parsed_ids = [
                int(value) for value in ids
                if str(value).isdigit() and len(str(value)) <= 10
            ]
            unique_ids = set(parsed_ids) if len(parsed_ids) == len(ids) else set()
        except (TypeError, ValueError, OverflowError):
            unique_ids = set()
        if not unique_ids or Ban.query.filter(Ban.id.in_(unique_ids)).count() != len(unique_ids):
            errors["ban_hoat_dong"] = "Ban hoat dong khong hop le."

    sdt = _text(form, "sdt")
    if len(sdt) > 15 or not PHONE_RE.fullmatch(sdt):
        errors["sdt"] = "So dien thoai khong hop le (vd: 0912345678)."

    email = _text(form, "email")
    if len(email) > 120 or not EMAIL_RE.fullmatch(email):
        errors["email"] = "Email khong hop le."

    facebook_link = _text(form, "facebook_link")
    if (len(facebook_link) > 255 or _contains_control(facebook_link)
            or not FACEBOOK_RE.fullmatch(facebook_link)):
        errors["facebook_link"] = "Link Facebook khong hop le (vd: https://facebook.com/ten.ban)."

    password = form.get("password", "")
    if not isinstance(password, str) or not 8 <= len(password) <= 128:
        errors["password"] = "Mat khau phai co tu 8 den 128 ky tu."

    return errors


def _text(form, field):
    value = form.get(field, "")
    return value.strip() if isinstance(value, str) else ""


def _contains_control(value):
    return any(unicodedata.category(char).startswith("C") for char in value)
