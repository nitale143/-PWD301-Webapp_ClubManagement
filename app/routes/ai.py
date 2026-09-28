from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models import AIProposal, Ban, ChatMessage, Event
from app.permissions import approved_required, bdh_required
from app.security import require_csrf
from app.services.assistant import get_provider
from app.services.access import is_board
from app.services.common import audit, DomainError
from app.services.proposals import can_review, create_proposal, proposal_preview, review_proposal

ai_bp = Blueprint("ai", __name__)


def generate_ai_reply(user_message: str) -> dict:
    return get_provider().answer(current_user, user_message)


@ai_bp.route("/ai", methods=["GET", "POST"])
@login_required
@approved_required
def ai_chat():
    if request.method == "POST":
        content = request.form.get("message", "").strip()
        if content and len(content) <= 2000:
            db.session.add(ChatMessage(user_id=current_user.id, role="user", content=content))
            try:
                result = generate_ai_reply(content)
                reply = result["answer"]
                intent = result["intent"]
                provider = result.get("provider", "rules")
            except DomainError as exc:
                reply = str(exc)
                intent = "denied"
                provider = "error"
            db.session.add(ChatMessage(user_id=current_user.id, role="ai", content=reply))
            audit(current_user, "assistant_query", current_user, {"intent": intent, "provider": provider})
            db.session.commit()
        return redirect(url_for("ai.ai_chat"))

    history = (
        ChatMessage.query.filter_by(user_id=current_user.id)
        .order_by(ChatMessage.thoi_gian.asc())
        .all()
    )
    proposals = []
    if is_board(current_user):
        query = AIProposal.query.filter_by(status="pending").order_by(AIProposal.created_at.desc())
        if current_user.chuc_vu == "TB":
            query = query.filter_by(created_by_id=current_user.id)
        proposals = [proposal for proposal in query.limit(30) if can_review(current_user, proposal)]
    return render_template("ai.html", history=history, proposals=proposals,
                           proposal_preview=proposal_preview,
                           bans=Ban.query.all() if is_board(current_user) else [],
                           events=Event.query.filter(Event.trang_thai.notin_(["da_ket_thuc", "cancelled"])).all()
                           if is_board(current_user) else [])


@ai_bp.route("/ai/proposals/new", methods=["POST"])
@login_required
@bdh_required
def proposal_new():
    require_csrf()
    try:
        create_proposal(current_user, request.form)
        flash("Đã tạo bản xem trước. Cần BDH duyệt trước khi áp dụng.", "success")
    except DomainError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("ai.ai_chat"))


@ai_bp.route("/ai/proposals/<int:proposal_id>/<decision>", methods=["POST"])
@login_required
@bdh_required
def proposal_review(proposal_id, decision):
    require_csrf()
    proposal = AIProposal.query.get_or_404(proposal_id)
    try:
        review_proposal(current_user, proposal, decision)
        flash("Đã duyệt và áp dụng đề xuất." if decision == "approved" else "Đã từ chối đề xuất.", "success")
    except DomainError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("ai.ai_chat"))
