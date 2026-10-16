# Image chạy webapp CLB bằng Gunicorn (Ch11 – Docker).
# Build:  docker build -t club-webapp .
# Chạy:   docker compose up -d   (xem docker-compose.yml)
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Cài thư viện trước để tận dụng cache của Docker khi chỉ sửa code
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Chạy bằng user thường, không dùng root
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/instance /app/app/static/uploads \
    && chown -R appuser:appuser /app/instance /app/app/static/uploads
USER appuser

EXPOSE 8000
ENV GUNICORN_BIND=0.0.0.0:8000 FLASK_APP=run.py

# Cập nhật schema rồi khởi động Gunicorn
CMD ["sh", "-c", "flask --app run.py init-db && gunicorn -c gunicorn.conf.py wsgi:app"]
