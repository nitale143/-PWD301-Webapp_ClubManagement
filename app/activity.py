"""Tính tình trạng hoạt động của thành viên theo từng (thành viên, ban, kỳ).

Quy tắc:
  - Chỉ tính trên các Task thuộc một Ban cụ thể (Task.ban_id).
  - Task trạng thái 'huy' KHÔNG tính vào mẫu số.
  - % = số task hoan_thanh / tổng số task (không tính hủy), trong phạm vi
    1 kỳ (FundPeriod); kỳ của task xác định bởi ngày kết thúc của Event chứa task.
  - Thành viên được duyệt trong kỳ nào thì KHÔNG tính % trong chính kỳ đó;
    từ kỳ KẾ TIẾP mới bắt đầu tính (User.ky_tham_gia_id).
  - Được tính lại mỗi khi một Event chuyển sang trạng thái 'da_ket_thuc'.
"""

from app import db
from app.config import Config
from app.models import Task, FundPeriod, MemberActivity
from app.timeutil import utcnow


def _tim_ky_cua_ngay(ngay):
    """Tìm FundPeriod có khoảng [ngay_bat_dau, ngay_ket_thuc] chứa `ngay`."""
    return FundPeriod.query.filter(
        FundPeriod.ngay_bat_dau <= ngay,
        db.or_(FundPeriod.ngay_ket_thuc.is_(None), FundPeriod.ngay_ket_thuc >= ngay),
    ).first()


def _xep_loai(phan_tram):
    """Đổi % hoàn thành task thành nhãn tình trạng (tich_cuc / hoat_dong / it_hoat_dong /
    khong_hoat_dong) theo Config.ACTIVITY_THRESHOLDS.
    """
    for nguong, nhan in Config.ACTIVITY_THRESHOLDS:
        if phan_tram >= nguong and nguong > 0:
            return nhan
    return "khong_hoat_dong"


def _tinh_lai_mot_cap(user_id, ban_id, period_id):
    """Tính lại % hoạt động cho 1 bộ (thành viên, ban, kỳ) và lưu vào MemberActivity."""
    from app.models import User

    user = db.session.get(User, user_id)
    # Thành viên mới duyệt trong chính kỳ này → chưa tính %
    if user and user.ky_tham_gia_id == period_id:
        return

    period = db.session.get(FundPeriod, period_id)
    if not period:
        return

    # Lấy các task của (user, ban) có Event kết thúc trong kỳ này
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
    activity.cap_nhat_luc = utcnow()


def cap_nhat_hoat_dong_khi_event_ket_thuc(event):
    """Gọi ngay sau khi một Event được đánh dấu 'da_ket_thuc': tính lại % cho
    mọi cặp (thành viên, ban) xuất hiện trong các task của sự kiện."""
    period = _tim_ky_cua_ngay(event.thoi_gian_ket_thuc.date())
    if not period:
        return  # chưa khai báo kỳ phù hợp → bỏ qua, không báo lỗi

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
