import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models import User, MemberActivity, FundDue
from app.permissions import approved_required
from app.services.access import can_view_member, can_view_all_members
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
    )


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
