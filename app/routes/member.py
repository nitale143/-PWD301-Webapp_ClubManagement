import io
from flask import Blueprint, render_template, request, send_file
from flask_login import login_required, current_user

from app.models import User, Ban
from app.permissions import approved_required

member_bp = Blueprint("member", __name__)


def _parse_filters():
    q = request.args.get("q", "").strip()
    ban_id = request.args.get("ban_id", type=int)
    sort_by = request.args.get("sort", "ho_ten")  # ho_ten | mssv
    return q, ban_id, sort_by


def _filtered_members():
    q, ban_id, sort_by = _parse_filters()

    members = User.query.filter_by(status="approved")

    if q:
        like = f"%{q}%"
        members = members.filter(
            (User.ho_ten.ilike(like)) | (User.mssv.ilike(like))
        )
    if ban_id:
        members = members.join(User.ban_links).filter_by(ban_id=ban_id)

    if sort_by == "mssv":
        members = members.order_by(User.mssv.asc())
    else:
        members = members.order_by(User.ho_ten.asc())

    return members.all()


@member_bp.route("/member")
@login_required
@approved_required
def member_list():
    members = _filtered_members()
    bans = Ban.query.all()
    q, ban_id, sort_by = _parse_filters()
    # BDH xem day du thong tin; thanh vien thuong chi xem ho ten/mssv/chuc vu/ban
    return render_template(
        "member.html",
        members=members,
        bans=bans,
        is_bdh=current_user.is_bdh(),
        selected_q=q,
        selected_ban_id=ban_id,
        selected_sort=sort_by,
    )


@member_bp.route("/member/export")
@login_required
@approved_required
def export_excel():
    """Xuat danh sach thanh vien (theo bo loc hien tai) ra file Excel."""
    from openpyxl import Workbook

    members = _filtered_members()
    wb = Workbook()
    ws = wb.active
    ws.title = "Danh sach thanh vien"

    if current_user.is_bdh():
        headers = ["Ho ten", "MSSV", "Chuc vu", "Ban hoat dong", "SDT", "Email", "Tinh trang HD"]
    else:
        headers = ["Ho ten", "MSSV", "Chuc vu", "Ban hoat dong"]
    ws.append(headers)

    for m in members:
        ban_names = ", ".join(link.ban.ten_ban for link in m.ban_links)
        row = [m.ho_ten, m.mssv, m.chuc_vu, ban_names]
        if current_user.is_bdh():
            row += [m.sdt, m.email, m.hoat_dong_status]
        ws.append(row)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name="danh_sach_thanh_vien.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
