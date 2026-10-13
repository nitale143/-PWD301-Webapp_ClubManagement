import os
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models import User, MemberActivity, FundDue, MemberPlanningProfile
from app.permissions import approved_required
from app.services.access import can_view_member, can_view_all_members
from app.security import require_csrf
from flask import abort

profile_bp = Blueprint("profile", __name__)


def _allowed_avatar(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_AVATAR_EXTENSIONS"]


@profile_bp.route("/profile")
@profile_bp.route("/profile/<int:user_id>")
@login_required
@approved_required
def view_profile(user_id=None):
    """
    Xem thong tin ca nhan. Neu khong truyen user_id -> xem chinh minh.
    Xem nguoi khac chi hien thong tin cong khai (giong rule trang Member).
    """
    user = User.query.get_or_404(user_id) if user_id else current_user
    if not can_view_member(current_user, user):
        abort(403)
    is_self = user.id == current_user.id
    can_see_full = is_self or can_view_all_members(current_user)

    activities = (
        MemberActivity.query.filter_by(user_id=user.id)
        .order_by(MemberActivity.period_id.desc())
        .all()
    )
    dues = FundDue.query.filter_by(user_id=user.id).all() if can_see_full else []

    return render_template(
        "profile.html",
        member=user,
        is_self=is_self,
        can_see_full=can_see_full,
        activities=activities,
        dues=dues,
        planning_profile=db.session.get(MemberPlanningProfile, user.id) if is_self else None,
    )


@profile_bp.route("/profile/task-preferences", methods=["POST"])
@login_required
@approved_required
def task_preferences():
    """Members control the information used by AI task suggestions."""
    require_csrf()
    skills = list(dict.fromkeys(
        skill.strip().casefold() for skill in request.form.get("skills", "").split(",")
        if skill.strip()
    ))
    try:
        capacity = int(request.form.get("max_active_tasks", "3"))
        until_raw = request.form.get("unavailable_until", "").strip()
        unavailable_until = date.fromisoformat(until_raw) if until_raw else None
    except ValueError:
        flash("Thông tin nhận task không hợp lệ.", "error")
        return redirect(url_for("profile.view_profile"))
    if (len(skills) > 10 or any(not 2 <= len(skill) <= 30 for skill in skills)
            or not 1 <= capacity <= 10):
        flash("Tối đa 10 kỹ năng và 1–10 task đang làm.", "error")
        return redirect(url_for("profile.view_profile"))
    profile = db.session.get(MemberPlanningProfile, current_user.id)
    if profile is None:
        profile = MemberPlanningProfile(user_id=current_user.id)
        db.session.add(profile)
    profile.skills = skills
    profile.max_active_tasks = capacity
    profile.unavailable_until = unavailable_until
    db.session.commit()
    flash("Đã cập nhật khả năng nhận task.", "success")
    return redirect(url_for("profile.view_profile"))


@profile_bp.route("/profile/avatar", methods=["POST"])
@login_required
@approved_required
def upload_avatar():
    """Upload anh dai dien, luu truc tiep vao server (phuc vu demo)."""
    file = request.files.get("avatar")
    if not file or file.filename == "":
        flash("Vui long chon mot file anh.", "error")
        return redirect(url_for("profile.view_profile"))

    if not _allowed_avatar(file.filename):
        flash("Chi chap nhan file anh (png, jpg, jpeg, gif, webp).", "error")
        return redirect(url_for("profile.view_profile"))

    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    ext = file.filename.rsplit(".", 1)[-1].lower()
    filename = secure_filename(f"user_{current_user.id}.{ext}")
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    current_user.avatar_url = f"/static/uploads/avatars/{filename}"
    db.session.commit()

    flash("Da cap nhat anh dai dien.", "success")
    return redirect(url_for("profile.view_profile"))
