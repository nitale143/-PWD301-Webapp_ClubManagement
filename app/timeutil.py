"""Tiện ích thời gian dùng chung.

Python 3.12+ đánh dấu `datetime.utcnow()` là deprecated. Database của dự án
lưu thời gian UTC dạng *naive* (không kèm múi giờ), nên `utcnow()` trả về đúng
kiểu đó để tương thích dữ liệu cũ.
"""
from datetime import datetime, timezone


def utcnow():
    """Thời điểm hiện tại theo UTC, dạng naive datetime (giống utcnow() cũ)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
