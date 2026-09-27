from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models import User, Ban, UserBan
from app.validators import validate_registration

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/", methods=["GET"])
def index():
    """Link goc dua thang vao trang dang nhap (webapp noi bo, khong co landing page)."""
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        mssv = request.form.get("mssv", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(mssv=mssv).first()

        if user is None or not user.check_password(password):
            flash("MSSV hoac mat khau khong dung.", "error")
            return render_template("login.html")

        if user.status == "pending":
            login_user(user)  # dang nhap tam de xem trang cho duyet
            return redirect(url_for("auth.pending"))
        if user.status == "rejected":
            flash("Tai khoan cua ban da bi tu choi. Vui long lien he BDH.", "error")
            return render_template("login.html")

        login_user(user)
        return redirect(url_for("main.home"))

    return render_template("login.html")


@auth_bp.route("/pending")
@login_required
def pending():
    if current_user.status != "pending":
        return redirect(url_for("main.home"))
    return render_template("pending.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    bans = Ban.query.all()

    if request.method == "POST":
        errors = validate_registration(request.form)

        mssv = request.form.get("mssv", "").strip()
        if not errors and User.query.filter_by(mssv=mssv).first():
            errors["mssv"] = "MSSV nay da duoc dang ky."

        if errors:
            return render_template(
                "register.html", bans=bans, errors=errors, form=request.form
            )

        user = User(
            mssv=mssv,
            ho_ten=request.form.get("ho_ten", "").strip(),
            ngay_sinh=datetime.strptime(request.form.get("ngay_sinh"), "%Y-%m-%d").date(),
            sdt=request.form.get("sdt", "").strip(),
            email=request.form.get("email", "").strip(),
            facebook_link=request.form.get("facebook_link", "").strip(),
            status="pending",
            chuc_vu="THANH_VIEN",
        )
        user.set_password(request.form.get("password"))
        db.session.add(user)
        db.session.flush()  # de lay user.id truoc khi tao UserBan

        selected_ban_ids = request.form.getlist("ban_hoat_dong")
        for ban_id in selected_ban_ids:
            db.session.add(UserBan(user_id=user.id, ban_id=int(ban_id)))

        db.session.commit()
        flash("Dang ky thanh cong! Vui long cho BDH xet duyet.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", bans=bans, errors={}, form={})


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
