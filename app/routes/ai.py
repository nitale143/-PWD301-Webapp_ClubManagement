from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user

from app import db
from app.models import ChatMessage
from app.permissions import approved_required

ai_bp = Blueprint("ai", __name__)


def generate_ai_reply(user_message: str) -> str:
    """
    O day la noi ket noi voi mot LLM that (vi du Anthropic API) de:
      - tom tat/loc/sap xep danh sach thanh vien theo yeu cau BDH
      - tong hop su kien, tinh hoat dong theo ban
      - de xuat chia task con (chi thuc thi sau khi BDH duyet)
      - soan mail thong bao khi doi trang thai / canh bao deadline 7 ngay

    Quyet dinh thiet ke: dung 1 API key CHUNG do CLB quan ly (cau hinh o
    app/config.py: AI_PROVIDER, AI_API_KEY, AI_MODEL - lay tu bien moi
    truong), KHONG cho tung thanh vien tu nhap API key rieng. Ly do: tranh
    phai luu tru/ma hoa key ca nhan cua tung nguoi, de kiem soat chi phi
    chung, va da so thanh vien khong ranh ky thuat de tu lay API key.

    Hien tai la ham stub (chua goi API that vi chua co AI_API_KEY) de
    webapp chay duoc ngay. De ket noi that: doc current_app.config["AI_API_KEY"],
    goi API model, truyen kem du lieu member/event/fund lien quan (query
    tu DB) lam ngu canh (context) cho model.
    """
    return (
        "(AI Agent demo) Da nhan yeu cau: \""
        + user_message
        + "\". Ket noi mot LLM that (vi du qua Anthropic API, dung chung "
        "1 API key cau hinh o AI_API_KEY) trong app/routes/ai.py -> "
        "generate_ai_reply() de tra loi thuc te dua tren du lieu thanh vien "
        "/ su kien / quy hien co."
    )


@ai_bp.route("/ai", methods=["GET", "POST"])
@login_required
@approved_required
def ai_chat():
    if request.method == "POST":
        content = request.form.get("message", "").strip()
        if content:
            db.session.add(ChatMessage(user_id=current_user.id, role="user", content=content))
            reply = generate_ai_reply(content)
            db.session.add(ChatMessage(user_id=current_user.id, role="ai", content=reply))
            db.session.commit()
        return redirect(url_for("ai.ai_chat"))

    history = (
        ChatMessage.query.filter_by(user_id=current_user.id)
        .order_by(ChatMessage.thoi_gian.asc())
        .all()
    )
    return render_template("ai.html", history=history)
