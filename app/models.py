from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager


# ---------------------------------------------------------------------------
# Bang trung gian: thanh vien <-> ban hoat dong (nhieu-nhieu)
# ---------------------------------------------------------------------------
class UserBan(db.Model):
    __tablename__ = "user_ban"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    ban_id = db.Column(db.Integer, db.ForeignKey("ban.id"), nullable=False)
    # True neu nguoi nay la Truong ban cua ban nay
    is_truong_ban = db.Column(db.Boolean, default=False)

    user = db.relationship("User", back_populates="ban_links")
    ban = db.relationship("Ban", back_populates="user_links")


class Ban(db.Model):
    """Ban hoat dong: Ky thuat, Nhan su, Truyen thong."""
    __tablename__ = "ban"
    id = db.Column(db.Integer, primary_key=True)
    ten_ban = db.Column(db.String(50), unique=True, nullable=False)

    user_links = db.relationship("UserBan", back_populates="ban")


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    mssv = db.Column(db.String(20), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    ho_ten = db.Column(db.String(100), nullable=False)
    ngay_sinh = db.Column(db.Date, nullable=False)
    sdt = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    facebook_link = db.Column(db.String(255))
    avatar_url = db.Column(db.String(255), default="/static/img/default_avatar.svg")

    # pending | approved | rejected
    status = db.Column(db.String(20), default="pending", nullable=False)
    # CN | PCN | TB | THUKY_THUQUY | THANH_VIEN
    chuc_vu = db.Column(db.String(20), default="THANH_VIEN", nullable=False)
    # nguoi da chi dinh chuc vu nay (de phuc vu co che nhuong quyen)
    chi_dinh_boi_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    hoat_dong_status = db.Column(db.String(20), default="hoat_dong")
    ngay_tao = db.Column(db.DateTime, default=datetime.utcnow)

    # Ky (FundPeriod) ma thanh vien nay duoc BDH duyet vao. Dung de tinh
    # tinh trang hoat dong: ky nay khong tinh %, tu ky KE TIEP moi tinh.
    ky_tham_gia_id = db.Column(db.Integer, db.ForeignKey("fund_period.id"), nullable=True)

    ban_links = db.relationship(
        "UserBan", back_populates="user", foreign_keys=[UserBan.user_id]
    )

    # ---- password helpers ----
    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    # ---- quyen han helpers ----
    ROLE_RANK = {"CN": 0, "PCN": 1, "TB": 2, "THUKY_THUQUY": 2, "THANH_VIEN": 3}

    def outranks(self, other_user):
        """True neu self co quyen cao hon other_user (duoc phep chi dinh/quan ly)."""
        return self.ROLE_RANK.get(self.chuc_vu, 99) < self.ROLE_RANK.get(
            other_user.chuc_vu, 99
        )

    def is_bdh(self):
        return self.chuc_vu != "THANH_VIEN"

    def quan_ly_ban_ids(self):
        """Cac ban_id ma Truong ban nay quan ly (rong neu khong phai TB)."""
        if self.chuc_vu != "TB":
            return []
        return [link.ban_id for link in self.ban_links if link.is_truong_ban]

    def __repr__(self):
        return f"<User {self.mssv} - {self.ho_ten}>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------------------------------------------------------------------
# Su kien / Task
# ---------------------------------------------------------------------------
class Event(db.Model):
    __tablename__ = "event"
    id = db.Column(db.Integer, primary_key=True)
    ten_su_kien = db.Column(db.String(150), nullable=False)
    ma_su_kien = db.Column(db.String(30), unique=True, nullable=False)
    thoi_gian_bat_dau = db.Column(db.DateTime, nullable=False)
    thoi_gian_ket_thuc = db.Column(db.DateTime, nullable=False)
    # sap_dien_ra | dang_dien_ra | da_ket_thuc
    trang_thai = db.Column(db.String(20), default="sap_dien_ra")
    tao_boi_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    tasks = db.relationship("Task", backref="event", cascade="all, delete-orphan")


class Task(db.Model):
    __tablename__ = "task"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    ten_task = db.Column(db.String(150), nullable=False)
    mo_ta = db.Column(db.Text)
    deadline = db.Column(db.DateTime, nullable=False)

    # dang_lam | cho_duyet | lam_lai | hoan_thanh | huy
    trang_thai = db.Column(db.String(20), default="dang_lam")

    # Ban ma task nay thuoc ve (de tinh tinh trang hoat dong theo ban).
    ban_id = db.Column(db.Integer, db.ForeignKey("ban.id"), nullable=True)

    # Chi dinh nguoi phu trach NGAY TU DAU khi tao task (khong con co che
    # xung phong / mo cho dang ky).
    assignee_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    noi_dung_nop = db.Column(db.Text)          # san pham user nop
    lan_nop_gan_nhat = db.Column(db.DateTime)  # de kiem tra "chua co thay doi thi khong doi trang thai"
    nhan_xet_bdh = db.Column(db.Text)          # nhan xet khi "lam lai"

    assignee = db.relationship("User", foreign_keys=[assignee_id])
    ban = db.relationship("Ban")


# ---------------------------------------------------------------------------
# Quy CLB (ky quan ly theo lich hoc: Spring / Summer / Fall)
# ---------------------------------------------------------------------------
class FundPeriod(db.Model):
    __tablename__ = "fund_period"
    id = db.Column(db.Integer, primary_key=True)
    ten_ky = db.Column(db.String(50), nullable=False)  # vd: "Spring 2027"
    ngay_bat_dau = db.Column(db.Date, nullable=False)
    ngay_ket_thuc = db.Column(db.Date, nullable=True)
    is_current = db.Column(db.Boolean, default=False)
    # Da gui thong bao nhac BDH nhap ky ke tiep chua (tranh nhac lap lai moi ngay)
    da_nhac_ky_moi = db.Column(db.Boolean, default=False)

    transactions = db.relationship(
        "FundTransaction", backref="period", cascade="all, delete-orphan"
    )
    dues = db.relationship("FundDue", backref="period", cascade="all, delete-orphan")


class FundTransaction(db.Model):
    __tablename__ = "fund_transaction"
    id = db.Column(db.Integer, primary_key=True)
    period_id = db.Column(db.Integer, db.ForeignKey("fund_period.id"), nullable=False)
    danh_muc = db.Column(db.String(100), nullable=False)
    noi_dung = db.Column(db.String(255))
    ngay = db.Column(db.Date, nullable=False)
    so_tien = db.Column(db.Float, nullable=False)  # thu: +, chi: -
    tao_boi_id = db.Column(db.Integer, db.ForeignKey("user.id"))


class FundDue(db.Model):
    """Trang thai dong quy cua tung thanh vien trong 1 ky."""
    __tablename__ = "fund_due"
    id = db.Column(db.Integer, primary_key=True)
    period_id = db.Column(db.Integer, db.ForeignKey("fund_period.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    da_dong = db.Column(db.Boolean, default=False)
    ngay_dong = db.Column(db.Date, nullable=True)

    user = db.relationship("User")


# ---------------------------------------------------------------------------
# Tinh trang hoat dong: tinh theo (thanh vien, ban, ky), cap nhat moi khi
# mot su kien ket thuc.
# ---------------------------------------------------------------------------
class MemberActivity(db.Model):
    __tablename__ = "member_activity"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    ban_id = db.Column(db.Integer, db.ForeignKey("ban.id"), nullable=False)
    period_id = db.Column(db.Integer, db.ForeignKey("fund_period.id"), nullable=False)

    tong_task = db.Column(db.Integer, default=0)       # khong tinh task 'huy'
    task_hoan_thanh = db.Column(db.Integer, default=0)
    phan_tram = db.Column(db.Float, default=0.0)
    trang_thai = db.Column(db.String(20), default="khong_hoat_dong")
    cap_nhat_luc = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")
    ban = db.relationship("Ban")
    period = db.relationship("FundPeriod")

    __table_args__ = (
        db.UniqueConstraint("user_id", "ban_id", "period_id", name="uq_activity_user_ban_period"),
    )


# ---------------------------------------------------------------------------
# AI chat history
# ---------------------------------------------------------------------------
class ChatMessage(db.Model):
    __tablename__ = "chat_message"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'user' | 'ai'
    content = db.Column(db.Text, nullable=False)
    thoi_gian = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    """Thong bao hien o trang Home (canh bao task, nhac deadline, nhac tao ky moi,...)."""
    __tablename__ = "notification"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    noi_dung = db.Column(db.String(255), nullable=False)
    da_doc = db.Column(db.Boolean, default=False)
    thoi_gian = db.Column(db.DateTime, default=datetime.utcnow)
