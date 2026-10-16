"""Cấu hình Gunicorn (Ch11 – Production WSGI server).

Chạy: gunicorn -c gunicorn.conf.py wsgi:app
Biến môi trường có thể ghi đè: GUNICORN_BIND, GUNICORN_WORKERS, GUNICORN_THREADS, GUNICORN_TIMEOUT.
Lưu ý: chạy nhiều worker thì đặt SCHEDULER_IN_WEB=false và chạy
`flask --app run.py run-scheduler` ở tiến trình riêng; đặt RATELIMIT_STORAGE_URI
trỏ tới Redis để giới hạn tần suất dùng chung giữa các worker.
"""
import multiprocessing
import os

bind = os.environ.get("GUNICORN_BIND", "127.0.0.1:8000")
workers = int(os.environ.get("GUNICORN_WORKERS", min(4, multiprocessing.cpu_count() * 2 + 1)))
threads = int(os.environ.get("GUNICORN_THREADS", 2))
# Trợ lý AI dùng SSE (stream) có thể kéo dài tới AI_AGENT_MAX_SECONDS (mặc định 90s)
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 120))
graceful_timeout = 30
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOGLEVEL", "info")
# Chỉ tin header X-Forwarded-* từ Nginx chạy cùng máy/mạng nội bộ
forwarded_allow_ips = os.environ.get("FORWARDED_ALLOW_IPS", "127.0.0.1")
