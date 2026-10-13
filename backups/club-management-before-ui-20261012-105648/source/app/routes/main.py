from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models import Notification, Event, Task
from app.permissions import approved_required
from app.services.common import club_now
from app.services.access import is_board
from app.services.briefings import daily_digest

main_bp = Blueprint("main", __name__)


@main_bp.route("/home")
@login_required
@approved_required
def home():
    # Cot trai: thong bao (task chua hoan thanh, su kien/task cua CLB,...)
    notifications = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.thoi_gian.desc())
        .limit(20)
        .all()
    )

    # Cot phai: su kien sap dien ra + nguoi tham gia/duoc giao task
    upcoming_events = (
        Event.query.filter(Event.trang_thai.in_(["sap_dien_ra", "dang_dien_ra"]),
                           Event.thoi_gian_ket_thuc >= club_now())
        .order_by(Event.thoi_gian_bat_dau.asc())
        .limit(5)
        .all()
    )
    event_participants = {}
    for ev in upcoming_events:
        assignees = {t.assignee for t in ev.tasks if t.assignee is not None}
        event_participants[ev.id] = list(assignees)

    return render_template(
        "home.html",
        notifications=notifications,
        upcoming_events=upcoming_events,
        event_participants=event_participants,
        daily_digest=daily_digest(current_user) if is_board(current_user) else None,
    )
