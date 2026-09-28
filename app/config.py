import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "doi-key-nay-truoc-khi-deploy")
    APP_TIMEZONE = os.environ.get("APP_TIMEZONE", "Asia/Bangkok")
    SESSION_COOKIE_SAMESITE = "Lax"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "instance", "clb.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Danh sach chuc vu (thu tu quyen han giam dan)
    ROLE_ORDER = ["CN", "PCN", "TB", "THUKY_THUQUY", "THANH_VIEN"]
    ROLE_LABELS = {
        "CN": "Chu nhiem",
        "PCN": "Pho chu nhiem",
        "TB": "Truong ban",
        "THUKY_THUQUY": "Thu ky / Thu quy",
        "THANH_VIEN": "Thanh vien",
    }
    # Gioi han so luong theo chuc vu (BDH)
    ROLE_LIMITS = {"CN": 1, "PCN": 2, "TB": 3, "THUKY_THUQUY": 1}

    MEMBER_STATUS = ["pending", "approved", "rejected"]
    ACTIVITY_STATUS = [
        "tich_cuc",       # > 80%
        "hoat_dong",      # > 50%
        "it_hoat_dong",   # < 49%
        "khong_hoat_dong",# 0%
        "ngung_hoat_dong",# BDH chi dinh
    ]
    # Nguong % de xep loai tinh trang hoat dong (tinh theo tung ban/ky)
    ACTIVITY_THRESHOLDS = [
        (80, "tich_cuc"),
        (50, "hoat_dong"),
        (0.01, "it_hoat_dong"),
        (0, "khong_hoat_dong"),
    ]
    TASK_STATUS = ["dang_lam", "cho_duyet", "lam_lai", "hoan_thanh", "huy"]
    EVENT_STATUS = ["sap_dien_ra", "dang_dien_ra", "da_ket_thuc"]

    # --- Cau hinh gui mail (SMTP) ---
    # Mac dinh MAIL_ENABLED=False: webapp van chay binh thuong, email se
    # duoc in ra console thay vi gui that. Set bien moi truong de bat that.
    MAIL_ENABLED = os.environ.get("MAIL_ENABLED", "false").lower() == "true"
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", MAIL_USERNAME)

    # --- Scheduler ---
    DEADLINE_WARNING_DAYS = 7
    # So ngay truoc khi ky hien tai ket thuc thi bat dau nhac BDH nhap ky moi
    PERIOD_REMINDER_DAYS = 30

    # --- AI Agent ---
    # Dung 1 API key CHUNG do CLB quan ly (khong cho tung user tu nhap key
    # rieng, de tranh phai luu/ma hoa key ca nhan va de kiem soat chi phi).
    AI_PROVIDER = os.environ.get("AI_PROVIDER", "anthropic")
    AI_API_KEY = os.environ.get("AI_API_KEY", "")
    AI_MODEL = os.environ.get("AI_MODEL", "claude-sonnet-4-6")
    AI_WORKSPACE_ID = os.environ.get("AI_WORKSPACE_ID", "")
    AI_TIMEOUT_SECONDS = 20

    # --- Upload avatar (luu truc tiep tren server, phuc vu demo) ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads", "avatars")
    ALLOWED_AVATAR_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    MAX_CONTENT_LENGTH = 3 * 1024 * 1024  # 3MB moi request
