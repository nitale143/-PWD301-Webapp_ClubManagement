"""Shared plain-text mail templates; rendering never executes template code."""

import re

from app import db
from app.models import EmailTemplate
from .access import require
from .assistant import _normalize
from .common import DomainError, audit


PLACEHOLDERS = {"ten", "mssv", "email"}


def _validate_text(subject, body):
    subject = str(subject or "").strip()
    body = str(body or "").strip()
    if not 1 <= len(subject) <= 180 or "\n" in subject or "\r" in subject:
        raise DomainError("Tiêu đề mẫu phải là một dòng, tối đa 180 ký tự.")
    if not 1 <= len(body) <= 3000:
        raise DomainError("Nội dung mẫu phải từ 1 đến 3000 ký tự.")
    for value in (subject, body):
        found = re.findall(r"\{\{([^{}]*)\}\}", value)
        if any(item not in PLACEHOLDERS for item in found):
            raise DomainError("Chỉ dùng biến {{ten}}, {{mssv}} hoặc {{email}} trong mail mẫu.")
        if re.search(r"\{\{|\}\}", re.sub(r"\{\{(?:ten|mssv|email)\}\}", "", value)):
            raise DomainError("Biến trong mail mẫu không hợp lệ.")
    return subject, body


def save_template(actor, name, subject, body, template=None):
    require(actor.chuc_vu in {"CN", "PCN"},
            "Chỉ Chủ nhiệm hoặc Phó chủ nhiệm được quản lý mail mẫu.")
    name = str(name or "").strip()
    if not 2 <= len(name) <= 100 or "\n" in name or "\r" in name:
        raise DomainError("Tên mẫu phải từ 2 đến 100 ký tự, trên một dòng.")
    name_key = " ".join(_normalize(name).split())
    if not name_key:
        raise DomainError("Tên mẫu không hợp lệ.")
    subject, body = _validate_text(subject, body)
    existing = EmailTemplate.query.filter_by(name_key=name_key).first()
    if existing and (template is None or existing.id != template.id):
        raise DomainError("Tên mail mẫu đã tồn tại.")
    if template is None:
        template = EmailTemplate(created_by_id=actor.id)
        template.active = True
        db.session.add(template)
    template.name = name
    template.name_key = name_key
    template.subject = subject
    template.body = body
    db.session.flush()
    audit(actor, "email_template_saved", template)
    db.session.commit()
    return template


def set_template_active(actor, template, active):
    require(actor.chuc_vu in {"CN", "PCN"},
            "Chỉ Chủ nhiệm hoặc Phó chủ nhiệm được quản lý mail mẫu.")
    template.active = bool(active)
    audit(actor, "email_template_activated" if active else "email_template_disabled", template)
    db.session.commit()


def render_template(template, display_name, code, email):
    if not template.active:
        raise DomainError("Mail mẫu này đã ngừng sử dụng.")
    if not code and any("{{mssv}}" in value for value in (template.subject, template.body)):
        raise DomainError("Mail mẫu có biến MSSV nên chỉ dùng được cho thành viên CLB.")
    substitutions = {"{{ten}}": display_name, "{{mssv}}": code or "", "{{email}}": email}
    subject, body = template.subject, template.body
    for marker, value in substitutions.items():
        subject = subject.replace(marker, value)
        body = body.replace(marker, value)
    return _validate_text(subject, body)
