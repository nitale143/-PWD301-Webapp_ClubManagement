"""
Ham gui email dung chung cho toan bo app, dua tren smtplib (SMTP) thuan,
khong can Flask-Mail.

Vi du cau hinh voi Gmail (dat trong bien moi truong hoac file .env):
    MAIL_ENABLED=true
    MAIL_SERVER=smtp.gmail.com
    MAIL_PORT=587
    MAIL_USE_TLS=true
    MAIL_USERNAME=clb.example@gmail.com
    MAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx   # App Password, KHONG dung mat khau Gmail thuong
    MAIL_DEFAULT_SENDER=clb.example@gmail.com

Neu dung mail server cua truong/to chuc, doi MAIL_SERVER/MAIL_PORT tuong ung.
"""
import smtplib
from email.message import EmailMessage
from flask import current_app


def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Gui mot email don gian (plain text). Tra ve True neu gui thanh cong.

    Khi MAIL_ENABLED=False (mac dinh), ham chi in noi dung ra console -
    tien loi de phat trien/test ma khong can tai khoan SMTP that, va
    webapp khong bao gio bi crash chi vi thieu cau hinh mail.
    """
    cfg = current_app.config

    if not to_email:
        return False

    if not cfg.get("MAIL_ENABLED"):
        print(f"[MAIL-STUB] To: {to_email}\nSubject: {subject}\n{body}\n{'-'*40}")
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg["MAIL_DEFAULT_SENDER"]
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(cfg["MAIL_SERVER"], cfg["MAIL_PORT"], timeout=10) as server:
            if cfg.get("MAIL_USE_TLS"):
                server.starttls()
            if cfg.get("MAIL_USERNAME"):
                server.login(cfg["MAIL_USERNAME"], cfg["MAIL_PASSWORD"])
            server.send_message(msg)
        return True
    except Exception as exc:
        # Khong de loi gui mail lam sap ca request nguoi dung dang cho.
        print(f"[MAIL-ERROR] Gui mail toi {to_email} that bai: {exc}")
        return False
