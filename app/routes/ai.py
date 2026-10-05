from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, abort
from flask_login import login_required, current_user

from app import db
from app.models import AIProposal, AIReportSnapshot, AIUsageLog, Ban, ChatMessage, EmailProposal, EmailTemplate, Event
from app.permissions import approved_required, bdh_required, role_required
from app.security import require_csrf
from app.services.agent import check_chat_rate, respond
from app.services.access import is_board
from app.services.common import audit, DomainError
from app.services.proposals import can_review, create_proposal, proposal_preview, review_proposal
from app.services.email_proposals import (can_review_email, edit_email_draft,
                                          reconcile_email_draft, review_email_draft)
from app.services.email_templates import save_template, set_template_active
from app.services.briefings import (can_access_report, daily_digest, report_data,
                                    report_email_draft, report_text, report_workbook,
                                    save_report)

ai_bp = Blueprint("ai", __name__)


@ai_bp.route("/ai", methods=["GET", "POST"])
@login_required
@approved_required
def ai_chat():
    if request.method == "POST":
        require_csrf()
        content = request.form.get("message", "").strip()
        if content and len(content) <= 2000:
            try:
                check_chat_rate(current_user)
                result = respond(current_user, content)
                reply = result["answer"]
                intent = result["intent"]
                provider = result.get("provider", "rules")
            except DomainError as exc:
                reply = str(exc)
                intent = "denied"
                provider = "error"
            db.session.add(ChatMessage(user_id=current_user.id, role="user", content=content))
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
    email_proposals = []
    usage_summary = None
    digest = None
    reports = []
    report_previews = {}
    if is_board(current_user):
        digest = daily_digest(current_user)
        reports = [row for row in (AIReportSnapshot.query.filter_by(user_id=current_user.id)
                   .order_by(AIReportSnapshot.id.desc()).limit(30).all())
                   if can_access_report(current_user, row)][:10]
        report_previews = {period: report_text(report_data(current_user, period))
                           for period in ("week", "month")}
        query = AIProposal.query.filter_by(status="pending").order_by(AIProposal.created_at.desc())
        if current_user.chuc_vu == "TB":
            query = query.filter_by(created_by_id=current_user.id)
        proposals = [proposal for proposal in query.limit(30) if can_review(current_user, proposal)]
        email_query = EmailProposal.query.filter(
            EmailProposal.status.in_(["pending", "failed", "sending"])
        ).order_by(EmailProposal.created_at.desc())
        if current_user.chuc_vu == "TB":
            email_query = email_query.filter_by(created_by_id=current_user.id)
        email_proposals = [draft for draft in email_query.limit(30) if can_review_email(current_user, draft)]
        usage_query = AIUsageLog.query.filter(
            AIUsageLog.created_at >= datetime.utcnow() - timedelta(days=1))
        if current_user.chuc_vu == "TB":
            usage_query = usage_query.filter_by(actor_id=current_user.id)
        usage = usage_query.all()
        usage_summary = {"calls": len(usage),
                         "tokens": sum(row.total_tokens for row in usage),
                         "average_ms": round(sum(row.elapsed_ms for row in usage) / len(usage))
                         if usage else 0}
    return render_template("ai.html", history=history, proposals=proposals,
                           email_proposals=email_proposals, usage_summary=usage_summary,
                           email_templates=(EmailTemplate.query.order_by(EmailTemplate.name).all()
                                            if current_user.chuc_vu in {"CN", "PCN"} else
                                            EmailTemplate.query.filter_by(active=True)
                                            .order_by(EmailTemplate.name).all()
                                            if is_board(current_user) else []),
                           digest=digest, reports=reports, report_previews=report_previews,
                           report_text=report_text,
                           proposal_preview=proposal_preview,
                           bans=Ban.query.all() if is_board(current_user) else [],
                           events=Event.query.filter(Event.trang_thai.notin_(["da_ket_thuc", "cancelled"])).all()
                           if is_board(current_user) else [])


@ai_bp.post("/ai/reports/<period>/save")
@login_required
@bdh_required
def report_save(period):
    require_csrf()
    try:
        saved = save_report(current_user, period)
        flash(f"Đã lưu báo cáo #{saved.id}. Có thể tải đúng bản này hoặc tạo nháp email.", "success")
    except DomainError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("ai.ai_chat"))


@ai_bp.get("/ai/reports/<int:report_id>.xlsx")
@login_required
@bdh_required
def report_export(report_id):
    snapshot = db.get_or_404(AIReportSnapshot, report_id)
    if not can_access_report(current_user, snapshot):
        abort(403)
    return send_file(report_workbook(snapshot),
                     download_name=f"bao-cao-clb-{snapshot.period}-{snapshot.id}.xlsx",
                     as_attachment=True,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@ai_bp.post("/ai/reports/<int:report_id>/email-draft")
@login_required
@bdh_required
def report_draft_email(report_id):
    require_csrf()
    snapshot = db.get_or_404(AIReportSnapshot, report_id)
    if not can_access_report(current_user, snapshot):
        abort(403)
    try:
        draft = report_email_draft(current_user, snapshot)
        flash(f"Đã tạo nháp email #{draft.id} gửi tới email hồ sơ của bạn; chưa gửi.", "success")
    except DomainError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("ai.ai_chat"))


@ai_bp.post("/ai/email-templates")
@login_required
@role_required("CN", "PCN")
def email_template_create():
    require_csrf()
    try:
        save_template(current_user, request.form.get("name"), request.form.get("subject"),
                      request.form.get("body"))
        flash("Đã lưu mail mẫu dùng chung; chưa gửi email nào.", "success")
    except DomainError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("ai.ai_chat"))


@ai_bp.post("/ai/email-templates/<int:template_id>/update")
@login_required
@role_required("CN", "PCN")
def email_template_update(template_id):
    require_csrf()
    template = db.get_or_404(EmailTemplate, template_id)
    try:
        save_template(current_user, request.form.get("name"), request.form.get("subject"),
                      request.form.get("body"), template)
        flash("Đã cập nhật mail mẫu. Nháp cũ vẫn giữ nội dung đã xem trước.", "success")
    except DomainError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("ai.ai_chat"))


@ai_bp.post("/ai/email-templates/<int:template_id>/active")
@login_required
@role_required("CN", "PCN")
def email_template_active(template_id):
    require_csrf()
    template = db.get_or_404(EmailTemplate, template_id)
    set_template_active(current_user, template, request.form.get("active") == "yes")
    flash("Đã cập nhật trạng thái mail mẫu.", "success")
    return redirect(url_for("ai.ai_chat"))


@ai_bp.route("/ai/email-proposals/<int:draft_id>/<decision>", methods=["POST"])
@login_required
@bdh_required
def email_proposal_review(draft_id, decision):
    require_csrf()
    draft = db.get_or_404(EmailProposal, draft_id)
    try:
        sent = review_email_draft(current_user, draft, decision,
                                  confirm_retry=request.form.get("confirm_retry") == "yes")
        if decision == "rejected":
            flash("Đã từ chối bản nháp email; chưa gửi thư.", "success")
        elif sent:
            flash("Máy chủ SMTP đã nhận email để gửi.", "success")
        else:
            flash("Email chưa gửi được. Kiểm tra SMTP rồi bấm Thử gửi lại.", "error")
    except DomainError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("ai.ai_chat"))


@ai_bp.route("/ai/email-proposals/<int:draft_id>/edit", methods=["POST"])
@login_required
@bdh_required
def email_proposal_edit(draft_id):
    require_csrf()
    draft = db.get_or_404(EmailProposal, draft_id)
    try:
        edit_email_draft(current_user, draft, request.form.get("subject"),
                         request.form.get("body"))
        flash("Đã lưu bản nháp; vẫn chưa gửi email.", "success")
    except DomainError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("ai.ai_chat"))


@ai_bp.route("/ai/email-proposals/<int:draft_id>/reconcile/<outcome>", methods=["POST"])
@login_required
@bdh_required
def email_proposal_reconcile(draft_id, outcome):
    require_csrf()
    draft = db.get_or_404(EmailProposal, draft_id)
    try:
        reconcile_email_draft(current_user, draft, outcome)
        flash("Đã ghi nhận kết quả sau khi đối soát hộp thư.", "success")
    except DomainError as exc:
        db.session.rollback()
        flash(str(exc), "error")
    return redirect(url_for("ai.ai_chat"))


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
