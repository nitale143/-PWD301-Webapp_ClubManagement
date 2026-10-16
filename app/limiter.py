"""Giới hạn tần suất request bằng Flask-Limiter (Ch9 – slide 34).

- Khóa theo IP thật của client (cần ProxyFix khi chạy sau Nginx, xem hardening.py).
- Mặc định đếm trong RAM (`memory://`) – chỉ đúng khi chạy 1 process.
  Production nhiều worker: đặt `RATELIMIT_STORAGE_URI=redis://redis:6379/0`.
- Test tắt limiter (`RATELIMIT_ENABLED=False`) trừ khi test bật lại.
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
