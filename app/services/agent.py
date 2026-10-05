"""One policy path for the browser chat and JSON assistant API."""

from datetime import datetime, timedelta

from flask import current_app

from app.models import ChatMessage
from .assistant import get_provider
from .briefings import maybe_answer_briefing
from .common import DomainError
from .email_proposals import maybe_create_email_draft
from .natural_proposals import maybe_create_natural_proposal
from .proposals import maybe_create_chat_proposal
from .verified_queries import maybe_answer_member_query


def check_chat_rate(actor):
    count = ChatMessage.query.filter(
        ChatMessage.user_id == actor.id, ChatMessage.role == "user",
        ChatMessage.thoi_gian >= datetime.utcnow() - timedelta(minutes=1),
    ).count()
    if count >= current_app.config["AI_CHAT_MESSAGES_PER_MINUTE"]:
        raise DomainError("Bạn gửi câu hỏi quá nhanh. Vui lòng đợi một phút.", 429)


def respond(actor, message):
    return (maybe_create_email_draft(actor, message)
            or maybe_answer_briefing(actor, message)
            or maybe_create_chat_proposal(actor, message)
            or maybe_answer_member_query(actor, message)
            or maybe_create_natural_proposal(actor, message)
            or get_provider().answer(actor, message))
