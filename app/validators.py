import re
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

    ho_ten = form.get("ho_ten", "").strip()
    if len(ho_ten) < 2:
        errors["ho_ten"] = "Ho va ten khong hop le."

    mssv = form.get("mssv", "").strip()
    if not MSSV_RE.match(mssv):
        errors["mssv"] = "MSSV phai gom 6-15 ky tu chu/so."

    ngay_sinh = form.get("ngay_sinh", "").strip()
    try:
        dob = datetime.strptime(ngay_sinh, "%Y-%m-%d").date()
        if dob.year < 1980 or dob >= datetime.utcnow().date():
            errors["ngay_sinh"] = "Ngay sinh khong hop le."
    except ValueError:
        errors["ngay_sinh"] = "Dinh dang ngay sinh khong hop le (YYYY-MM-DD)."

    ban_ids = form.getlist("ban_hoat_dong") if hasattr(form, "getlist") else form.get("ban_hoat_dong")
    if not ban_ids:
        errors["ban_hoat_dong"] = "Vui long chon it nhat 1 ban hoat dong."

    sdt = form.get("sdt", "").strip()
    if not PHONE_RE.match(sdt):
        errors["sdt"] = "So dien thoai khong hop le (vd: 0912345678)."

    email = form.get("email", "").strip()
    if not EMAIL_RE.match(email):
        errors["email"] = "Email khong hop le."

    facebook_link = form.get("facebook_link", "").strip()
    if not FACEBOOK_RE.match(facebook_link):
        errors["facebook_link"] = "Link Facebook khong hop le (vd: https://facebook.com/ten.ban)."

    password = form.get("password", "")
    if len(password) < 6:
        errors["password"] = "Mat khau phai co it nhat 6 ky tu."

    return errors
