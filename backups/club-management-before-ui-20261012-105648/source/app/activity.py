"""
Tinh tinh trang hoat dong cua thanh vien, theo tung (thanh vien, ban, ky).

Rule (theo yeu cau):
  - Chi tinh tren cac Task thuoc mot Ban cu the (Task.ban_id).
  - Task trang thai 'huy' KHONG tinh vao mau so.
  - % = so task hoan_thanh / tong so task (khong tinh huy), trong pham vi
    1 ky (FundPeriod) - ky cua 1 task duoc xac dinh boi ngay ket thuc cua
    Event chua task do.
  - Thanh vien moi duoc duyet trong ky nao thi KHONG tinh % trong chinh ky
    do; tu ky KE TIEP tro di moi bat dau tinh (User.ky_tham_gia_id).
  - Duoc cap nhat lai moi khi mot Event chuyen sang trang thai 'da_ket_thuc'.
"""
from datetime import datetime

from app import db
from app.config import Config
from app.models import Task, FundPeriod, MemberActivity


def _tim_ky_cua_ngay(ngay):
    """Tim FundPeriod ma khoang [ngay_bat_dau, ngay_ket_thuc] chua 'ngay'."""
    return FundPeriod.query.filter(
        FundPeriod.ngay_bat_dau <= ngay,
        db.or_(FundPeriod.ngay_ket_thuc.is_(None), FundPeriod.ngay_ket_thuc >= ngay),
    ).first()


def _xep_loai(phan_tram):
    for nguong, nhan in Config.ACTIVITY_THRESHOLDS:
        if phan_tram >= nguong and nguong > 0:
            return nhan
    return "khong_hoat_dong"


def _tinh_lai_mot_cap(user_id, ban_id, period_id):
    """Tinh lai % hoat dong cho 1 (thanh vien, ban, ky) va luu vao DB."""
    from app.models import User

    user = User.query.get(user_id)
    # Thanh vien moi duyet trong chinh ky nay -> chua tinh %, bo qua.
    if user and user.ky_tham_gia_id == period_id:
        return

    period = FundPeriod.query.get(period_id)
    if not period:
        return

    # Lay tat ca task cua (user, ban) ma Event cua no ket thuc trong ky nay
    tasks = (
        Task.query.join(Task.event)
        .filter(
            Task.assignee_id == user_id,
            Task.ban_id == ban_id,
        )
        .all()
    )
    tasks_trong_ky = [
        t for t in tasks
        if t.event and period.ngay_bat_dau <= t.event.thoi_gian_ket_thuc.date() <= (
            period.ngay_ket_thuc or t.event.thoi_gian_ket_thuc.date()
        )
    ]

    tinh_duoc = [t for t in tasks_trong_ky if t.trang_thai != "huy"]
    tong = len(tinh_duoc)
    hoan_thanh = len([t for t in tinh_duoc if t.trang_thai == "hoan_thanh"])
    phan_tram = round((hoan_thanh / tong) * 100, 1) if tong > 0 else 0.0

    activity = MemberActivity.query.filter_by(
        user_id=user_id, ban_id=ban_id, period_id=period_id
    ).first()
    if not activity:
        activity = MemberActivity(user_id=user_id, ban_id=ban_id, period_id=period_id)
        db.session.add(activity)

    activity.tong_task = tong
    activity.task_hoan_thanh = hoan_thanh
    activity.phan_tram = phan_tram
    activity.trang_thai = _xep_loai(phan_tram)
    activity.cap_nhat_luc = datetime.utcnow()


def cap_nhat_hoat_dong_khi_event_ket_thuc(event):
    """
    Goi ham nay ngay sau khi mot Event duoc danh dau 'da_ket_thuc'.
    Tinh lai % cho tat ca (thanh vien, ban) xuat hien trong cac task cua
    su kien nay.
    """
    period = _tim_ky_cua_ngay(event.thoi_gian_ket_thuc.date())
    if not period:
        return  # khong khop ky nao (vd chua khai bao ky) -> bo qua, khong loi

    cap_da_xu_ly = set()
    for task in event.tasks:
        if task.ban_id is None:
            continue
        key = (task.assignee_id, task.ban_id)
        if key in cap_da_xu_ly:
            continue
        cap_da_xu_ly.add(key)
        _tinh_lai_mot_cap(task.assignee_id, task.ban_id, period.id)

    db.session.commit()
