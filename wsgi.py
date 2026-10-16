"""Điểm vào WSGI cho server production (Gunicorn): `gunicorn -c gunicorn.conf.py wsgi:app`."""
from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402

app = create_app()
