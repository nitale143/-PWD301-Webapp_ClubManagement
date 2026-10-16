"""Tiện ích dùng chung cho test.

Flask-WTF lưu token CSRF gốc trong session["csrf_token"] và form/header phải gửi
bản *đã ký* của token đó. `csrf_for(client)` tạo (nếu chưa có) token gốc trong
session của test client rồi trả về bản đã ký để gửi kèm request.
"""
import hashlib
import os

from itsdangerous import URLSafeTimedSerializer

WTF_SALT = "wtf-csrf-token"


def sign_csrf(app, raw):
    return URLSafeTimedSerializer(app.secret_key, salt=WTF_SALT).dumps(raw)


def csrf_for(client, raw=None):
    """Token CSRF hợp lệ cho session hiện tại của `client`."""
    with client.session_transaction() as session:
        current = session.get("csrf_token")
        if raw is not None:
            session["csrf_token"] = current = raw
        elif not current:
            current = hashlib.sha1(os.urandom(64)).hexdigest()
            session["csrf_token"] = current
    return sign_csrf(client.application, current)
