import io
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, abort
from flask_login import login_required, current_user

from app import db
from app.models import FundPeriod, FundTransaction, FundDue, User
from app.permissions import approved_required
from app.mail import send_email

funds_bp = Blueprint("funds", __name__)


def _is_thu_quy():
    return current_user.chuc_vu == "THUKY_THUQUY"


@funds_bp.route("/funds/period/new", methods=["POST"])
@login_required
@approved_required
def period_new():
    """
    Thu quy tao ky moi (Spring/Summer/Fall...). Ky cu (neu co) tu dong bi
    dong lai (is_current=False) - tai 1 thoi diem chi co dung 1 ky dang mo.
    """
    if not _is_thu_quy():
        abort(403)

    ten_ky = request.form.get("ten_ky", "").strip()
    try:
        ngay_bat_dau = datetime.strptime(request.form.get("ngay_bat_dau"), "%Y-%m-%d").date()
        ngay_ket_thuc_raw = request.form.get("ngay_ket_thuc", "").strip()
        ngay_ket_thuc = (
            datetime.strptime(ngay_ket_thuc_raw, "%Y-%m-%d").date() if ngay_ket_thuc_raw else None
        )
    except ValueError:
        flash("Ngay khong hop le.", "error")
        return redirect(url_for("funds.funds_home"))

    if not ten_ky:
        flash("Vui long nhap ten ky (vd: Spring 2027).", "error")
        return redirect(url_for("funds.funds_home"))

    # Dong ky dang mo (neu co) truoc khi mo ky moi
    FundPeriod.query.filter_by(is_current=True).update({"is_current": False})

    period = FundPeriod(
        ten_ky=ten_ky,
        ngay_bat_dau=ngay_bat_dau,
        ngay_ket_thuc=ngay_ket_thuc,
        is_current=True,
        da_nhac_ky_moi=False,
    )
    db.session.add(period)
    db.session.flush()

    # Tao san ban ghi FundDue (chua dong) cho tat ca thanh vien dang hoat dong
    for member in User.query.filter_by(status="approved").all():
        db.session.add(FundDue(period_id=period.id, user_id=member.id, da_dong=False))

    db.session.commit()
    flash(f"Da mo ky moi: {ten_ky}.", "success")
    return redirect(url_for("funds.funds_home"))


@funds_bp.route("/funds")
@login_required
@approved_required
def funds_home():
    period = FundPeriod.query.filter_by(is_current=True).first()
    transactions, dues, so_du, tong_thu, tong_chi = [], [], 0, 0, 0

    if period:
        transactions = (
            FundTransaction.query.filter_by(period_id=period.id)
            .order_by(FundTransaction.ngay.desc())
            .all()
        )
        tong_thu = sum(t.so_tien for t in transactions if t.so_tien > 0)
        tong_chi = sum(t.so_tien for t in transactions if t.so_tien < 0)
        so_du = tong_thu + tong_chi
        dues = FundDue.query.filter_by(period_id=period.id).all()

    return render_template(
        "funds.html",
        period=period,
        transactions=transactions,
        dues=dues,
        so_du=so_du,
        tong_thu=tong_thu,
        tong_chi=tong_chi,
        is_thu_quy=_is_thu_quy(),
    )


@funds_bp.route("/funds/transaction/new", methods=["POST"])
@login_required
@approved_required
def transaction_new():
    if not _is_thu_quy():
        abort(403)
    period = FundPeriod.query.filter_by(is_current=True).first()
    if not period:
        flash("Chua co ky quy nao dang mo.", "error")
        return redirect(url_for("funds.funds_home"))

    so_tien = float(request.form.get("so_tien", 0))
    tx = FundTransaction(
        period_id=period.id,
        danh_muc=request.form.get("danh_muc", "").strip(),
        noi_dung=request.form.get("noi_dung", "").strip(),
        ngay=datetime.strptime(request.form.get("ngay"), "%Y-%m-%d").date(),
        so_tien=so_tien,
        tao_boi_id=current_user.id,
    )
    db.session.add(tx)
    db.session.commit()
    flash("Da ghi nhan giao dich.", "success")
    return redirect(url_for("funds.funds_home"))


@funds_bp.route("/funds/due/<int:user_id>/toggle", methods=["POST"])
@login_required
@approved_required
def toggle_due(user_id):
    if not _is_thu_quy():
        abort(403)
    period = FundPeriod.query.filter_by(is_current=True).first()
    if not period:
        abort(400)

    due = FundDue.query.filter_by(period_id=period.id, user_id=user_id).first()
    if not due:
        due = FundDue(period_id=period.id, user_id=user_id, da_dong=False)
        db.session.add(due)

    due.da_dong = not due.da_dong
    due.ngay_dong = datetime.utcnow().date() if due.da_dong else None
    db.session.commit()
    return redirect(url_for("funds.funds_home"))


@funds_bp.route("/funds/nhac-dong-quy", methods=["POST"])
@login_required
@approved_required
def remind_unpaid():
    """Thu quy yeu cau gui mail nhac cac thanh vien chua dong quy trong ky hien tai."""
    if not _is_thu_quy():
        abort(403)
    period = FundPeriod.query.filter_by(is_current=True).first()
    if not period:
        flash("Chua co ky quy nao dang mo.", "error")
        return redirect(url_for("funds.funds_home"))

    unpaid_dues = FundDue.query.filter_by(period_id=period.id, da_dong=False).all()
    for due in unpaid_dues:
        send_email(
            due.user.email,
            f"[CLB] Nhac dong quy ky {period.ten_ky}",
            f"Chao {due.user.ho_ten},\n\nBan chua dong quy CLB cho ky \"{period.ten_ky}\". "
            "Vui long lien he thu quy de hoan tat.\n\n-- AI Agent CLB",
        )

    flash(f"Da gui nhac nho toi {len(unpaid_dues)} thanh vien chua dong quy.", "success")
    return redirect(url_for("funds.funds_home"))


@funds_bp.route("/funds/export")
@login_required
@approved_required
def export_funds_excel():
    from openpyxl import Workbook

    period = FundPeriod.query.filter_by(is_current=True).first()
    wb = Workbook()
    ws = wb.active
    ws.title = "Thu chi"
    ws.append(["Ngay", "Danh muc", "Noi dung", "So tien"])
    if period:
        for tx in FundTransaction.query.filter_by(period_id=period.id):
            ws.append([tx.ngay.isoformat(), tx.danh_muc, tx.noi_dung, tx.so_tien])

    ws2 = wb.create_sheet("Dong quy")
    ws2.append(["Ho ten", "MSSV", "Da dong"])
    if period:
        for due in FundDue.query.filter_by(period_id=period.id):
            ws2.append([due.user.ho_ten, due.user.mssv, "Co" if due.da_dong else "Chua"])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name="quy_clb.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
