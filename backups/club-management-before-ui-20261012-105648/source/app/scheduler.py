"""
Scheduler chay ngam trong tien trinh Flask (dung APScheduler) de kiem tra
moi ngay xem task nao con dung DEADLINE_WARNING_DAYS (mac dinh 7 ngay)
nua la den han, va gui mail canh bao cho nguoi phu trach.

Vi day la scheduler chay "trong" tien trinh web (khong phai tien trinh
rieng), luu y 2 diem khi trien khai that:
  1. Flask debug reloader khoi dong app 2 lan -> code duoi da chan bang
     bien moi truong WERKZEUG_RUN_MAIN de scheduler chi chay 1 lan.
  2. Neu chay nhieu worker (vd gunicorn -w 4), scheduler se chay lap lai
     trong tung worker -> gui mail trung nhieu lan. Khi do nen tach
     scheduler ra thanh 1 tien trinh/cron job rieng, hoac dung
     Celery beat, thay vi chay chung trong web process.
"""
import os
from datetime import timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from app import db
from app.mail import send_email
from app.services.common import club_now

_scheduler = None


def init_scheduler(app):
    global _scheduler
    if _scheduler is not None:
        return  # da khoi tao roi, tranh tao 2 scheduler

    # Chi chay o tien trinh chinh khi dang debug (tranh Flask reloader chay 2 lan)
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return

    _scheduler = BackgroundScheduler(daemon=True, timezone=app.config["APP_TIMEZONE"])
    _scheduler.add_job(
        func=lambda: check_deadlines(app),
        trigger="cron",
        hour=7,
        minute=0,
        id="check_deadlines",
        replace_existing=True,
    )
    _scheduler.add_job(
        func=lambda: check_period_reminder(app),
        trigger="cron",
        hour=7,
        minute=5,
        id="check_period_reminder",
        replace_existing=True,
    )
    _scheduler.start()
    print("[SCHEDULER] Da khoi dong: kiem tra deadline + nhac ky moi moi ngay luc 07:00.")


def check_deadlines(app):
    """Job chay moi ngay: tim task sap den han va gui mail canh bao."""
    from app.models import Task  # import tre de tranh circular import

    with app.app_context():
        warn_days = app.config["DEADLINE_WARNING_DAYS"]
        target_date = (club_now() + timedelta(days=warn_days)).date()

        tasks = Task.query.filter(Task.trang_thai.in_(["dang_lam", "lam_lai"])).all()
        for task in tasks:
            if task.assignee and task.deadline.date() == target_date:
                send_email(
                    task.assignee.email,
                    f"[CLB] Con {warn_days} ngay nua den han: {task.ten_task}",
                    (
                        f"Chao {task.assignee.ho_ten},\n\n"
                        f"Task \"{task.ten_task}\" thuoc su kien "
                        f"\"{task.event.ten_su_kien}\" se den han vao luc "
                        f"{task.deadline.strftime('%d/%m/%Y %H:%M')} "
                        f"(con {warn_days} ngay nua).\n\n"
                        "Vui long hoan thanh va nop san pham dung han.\n\n"
                        "-- AI Agent CLB"
                    ),
                )


def check_period_reminder(app):
    """
    Job chay moi ngay: neu ky quy hien tai sap ket thuc (trong vong
    PERIOD_REMINDER_DAYS ngay) ma chua nhac, tao Notification cho tat ca
    BDH de ho kip nhap thoi gian cho ky ke tiep (Spring/Summer/Fall).
    Danh dau da_nhac_ky_moi=True de khong nhac lap lai moi ngay.
    """
    from app.models import FundPeriod, User, Notification

    with app.app_context():
        period = FundPeriod.query.filter_by(is_current=True).first()
        if not period or not period.ngay_ket_thuc or period.da_nhac_ky_moi:
            return

        so_ngay_con_lai = (period.ngay_ket_thuc - club_now().date()).days
        if so_ngay_con_lai > app.config["PERIOD_REMINDER_DAYS"]:
            return

        bdh_members = User.query.filter(
            User.status == "approved", User.chuc_vu != "THANH_VIEN"
        ).all()
        noi_dung = (
            f"Ky \"{period.ten_ky}\" se ket thuc vao {period.ngay_ket_thuc.strftime('%d/%m/%Y')} "
            f"(con {so_ngay_con_lai} ngay). Vui long chuan bi nhap thong tin cho ky ke tiep."
        )
        for member in bdh_members:
            db.session.add(Notification(user_id=member.id, noi_dung=noi_dung))
            send_email(member.email, "[CLB] Nhac chuan bi ky moi", noi_dung + "\n\n-- AI Agent CLB")

        period.da_nhac_ky_moi = True
        db.session.commit()
