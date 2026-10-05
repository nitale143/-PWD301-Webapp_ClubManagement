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
    so_tien = db.Column(db.Numeric(14, 2), nullable=False)  # thu: +, chi: -
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


# Nghiệp vụ mở rộng. Các bảng riêng giữ nguyên dữ liệu của webapp nhóm hiện có.
class MemberRecord(db.Model):
    __tablename__ = "member_record"
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    ngay_gia_nhap = db.Column(db.Date, nullable=False, default=lambda: datetime.utcnow().date())
    tinh_trang = db.Column(db.String(20), nullable=False, default="active")
    ghi_chu = db.Column(db.Text, nullable=False, default="")
    luu_tru_luc = db.Column(db.DateTime)
    user = db.relationship("User", backref=db.backref("member_record", uselist=False))
    __table_args__ = (
        db.CheckConstraint("tinh_trang IN ('active','paused','left')", name="ck_member_status"),
    )


class FundCollection(db.Model):
    __tablename__ = "fund_collection"
    id = db.Column(db.Integer, primary_key=True)
    ten_khoan_thu = db.Column(db.String(180), nullable=False)
    loai = db.Column(db.String(20), nullable=False)
    so_tien = db.Column(db.Numeric(14, 2), nullable=False)
    ngay_bat_dau = db.Column(db.Date, nullable=False)
    han_dong = db.Column(db.Date, nullable=False, index=True)
    tat_ca_thanh_vien = db.Column(db.Boolean, nullable=False, default=True)
    mo_ta = db.Column(db.Text, nullable=False, default="")
    trang_thai = db.Column(db.String(12), nullable=False, default="draft", index=True)
    tao_boi_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    tao_luc = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (
        db.CheckConstraint("so_tien >= 0", name="ck_fund_collection_amount"),
        db.CheckConstraint("han_dong >= ngay_bat_dau", name="ck_fund_collection_dates"),
        db.CheckConstraint("loai IN ('monthly','semester','yearly','event','voluntary','other')", name="ck_fund_collection_type"),
        db.CheckConstraint("trang_thai IN ('draft','open','closed','cancelled')", name="ck_fund_collection_status"),
        db.Index("ix_fund_collection_status_due", "trang_thai", "han_dong"),
    )


class FundTargetBan(db.Model):
    __tablename__ = "fund_target_ban"
    fund_id = db.Column(db.Integer, db.ForeignKey("fund_collection.id"), primary_key=True)
    ban_id = db.Column(db.Integer, db.ForeignKey("ban.id"), primary_key=True)


class FundAdjustment(db.Model):
    __tablename__ = "fund_adjustment"
    id = db.Column(db.Integer, primary_key=True)
    fund_id = db.Column(db.Integer, db.ForeignKey("fund_collection.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    loai = db.Column(db.String(10), nullable=False)
    so_tien = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    ly_do = db.Column(db.Text, nullable=False)
    tao_boi_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    tao_luc = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (
        db.UniqueConstraint("fund_id", "user_id", name="uq_fund_adjustment_member"),
        db.CheckConstraint("loai IN ('exempt','reduce')", name="ck_fund_adjustment_type"),
        db.CheckConstraint("so_tien >= 0", name="ck_fund_adjustment_amount"),
        db.CheckConstraint("length(trim(ly_do)) > 0", name="ck_fund_adjustment_reason"),
    )


class FundPayment(db.Model):
    __tablename__ = "fund_payment"
    id = db.Column(db.Integer, primary_key=True)
    fund_id = db.Column(db.Integer, db.ForeignKey("fund_collection.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    so_tien = db.Column(db.Numeric(14, 2), nullable=False)
    ngay_dong = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    phuong_thuc = db.Column(db.String(20), nullable=False)
    ma_giao_dich = db.Column(db.String(100), nullable=False, default="")
    trang_thai = db.Column(db.String(12), nullable=False, default="pending", index=True)
    xac_nhan_boi_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    xac_nhan_luc = db.Column(db.DateTime)
    ghi_chu = db.Column(db.Text, nullable=False, default="")
    __table_args__ = (
        db.CheckConstraint("so_tien > 0", name="ck_fund_payment_amount"),
        db.CheckConstraint("trang_thai IN ('pending','confirmed','rejected')", name="ck_fund_payment_status"),
        db.CheckConstraint("trang_thai != 'confirmed' OR xac_nhan_boi_id IS NOT NULL", name="ck_fund_payment_reviewer"),
        db.Index("ix_fund_payment_fund_member_status", "fund_id", "user_id", "trang_thai"),
    )


class PaymentEvidence(db.Model):
    __tablename__ = "payment_evidence"
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey("fund_payment.id"), nullable=False)
    duong_dan = db.Column(db.String(255), nullable=False)
    tai_len_luc = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class EventDetail(db.Model):
    __tablename__ = "event_detail"
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), primary_key=True)
    loai = db.Column(db.String(100), nullable=False, default="other")
    noi_dung = db.Column(db.Text, nullable=False, default="")
    dia_diem = db.Column(db.String(300), nullable=False, default="")
    anh_dai_dien = db.Column(db.String(255), nullable=False, default="")
    han_dang_ky = db.Column(db.DateTime)
    so_nguoi_toi_da = db.Column(db.Integer)
    phu_trach_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    fund_id = db.Column(db.Integer, db.ForeignKey("fund_collection.id"))
    tat_ca_thanh_vien = db.Column(db.Boolean, nullable=False, default=True)
    event = db.relationship("Event", backref=db.backref("detail", uselist=False))
    __table_args__ = (
        db.CheckConstraint("so_nguoi_toi_da IS NULL OR so_nguoi_toi_da > 0", name="ck_event_capacity"),
    )


class EventTargetBan(db.Model):
    __tablename__ = "event_target_ban"
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), primary_key=True)
    ban_id = db.Column(db.Integer, db.ForeignKey("ban.id"), primary_key=True)


class EventRegistration(db.Model):
    __tablename__ = "event_registration"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    trang_thai = db.Column(db.String(12), nullable=False, default="registered")
    dang_ky_luc = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    huy_luc = db.Column(db.DateTime)
    user = db.relationship("User")
    event = db.relationship("Event", backref="registrations")
    __table_args__ = (
        db.UniqueConstraint("event_id", "user_id", name="uq_event_registration_member"),
        db.CheckConstraint("trang_thai IN ('registered','waitlist','cancelled')", name="ck_event_registration_status"),
        db.Index("ix_event_registration_event_status", "event_id", "trang_thai"),
    )


class Attendance(db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    registration_id = db.Column(db.Integer, db.ForeignKey("event_registration.id"), nullable=False, unique=True)
    trang_thai = db.Column(db.String(12), nullable=False, default="pending")
    checkin_luc = db.Column(db.DateTime)
    checkin_boi_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    ghi_chu = db.Column(db.Text, nullable=False, default="")
    registration = db.relationship("EventRegistration", backref=db.backref("attendance", uselist=False))
    __table_args__ = (
        db.CheckConstraint("trang_thai IN ('on_time','late','excused','absent','pending')", name="ck_attendance_status"),
    )


class QRCheckinLog(db.Model):
    __tablename__ = "qr_checkin_log"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    checkin_luc = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class EventFeedback(db.Model):
    __tablename__ = "event_feedback"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    danh_gia = db.Column(db.Integer, nullable=False)
    binh_luan = db.Column(db.Text, nullable=False, default="")
    tao_luc = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (
        db.UniqueConstraint("event_id", "user_id", name="uq_event_feedback_member"),
        db.CheckConstraint("danh_gia BETWEEN 1 AND 5", name="ck_event_feedback_rating"),
    )


class ActivityPoint(db.Model):
    __tablename__ = "activity_point"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"))
    so_diem = db.Column(db.Integer, nullable=False)
    loai = db.Column(db.String(12), nullable=False)
    ly_do = db.Column(db.Text, nullable=False)
    tao_boi_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    tao_luc = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (
        db.CheckConstraint("length(trim(ly_do)) > 0", name="ck_activity_point_reason"),
        db.Index("ix_activity_point_member_time", "user_id", "tao_luc"),
    )


class ClubSetting(db.Model):
    __tablename__ = "club_setting"
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.JSON, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(db.Model):
    __tablename__ = "audit_log"
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    action = db.Column(db.String(100), nullable=False, index=True)
    object_type = db.Column(db.String(100), nullable=False)
    object_id = db.Column(db.String(100), nullable=False)
    details = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class AIProposal(db.Model):
    """An AI suggestion is inert until a board member explicitly approves it."""

    __tablename__ = "ai_proposal"
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(10), nullable=False)
    request_text = db.Column(db.Text, nullable=False)
    payload = db.Column(db.JSON, nullable=False)
    provider = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(12), nullable=False, default="pending", index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    result_ids = db.Column(db.JSON, nullable=False, default=list)
    __table_args__ = (
        db.CheckConstraint("kind IN ('event','task')", name="ck_ai_proposal_kind"),
        db.CheckConstraint("status IN ('pending','approved','rejected')", name="ck_ai_proposal_status"),
        db.Index("ix_ai_proposal_creator_status", "created_by_id", "status"),
    )


class EmailProposal(db.Model):
    """Email draft: chat creation never sends; a separate BDH action does."""

    __tablename__ = "email_proposal"
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    recipient_email = db.Column(db.String(120), nullable=False)
    request_text = db.Column(db.Text, nullable=False)
    subject = db.Column(db.String(180), nullable=False)
    body = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(12), nullable=False, default="pending", index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    sent_at = db.Column(db.DateTime)
    __table_args__ = (
        db.CheckConstraint("status IN ('pending','sending','sent','failed','rejected')",
                           name="ck_email_proposal_status"),
        db.Index("ix_email_proposal_creator_status", "created_by_id", "status"),
    )


class EmailTemplate(db.Model):
    """Shared, reviewable mail content managed by the club leadership."""

    __tablename__ = "email_template"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_key = db.Column(db.String(100), unique=True, nullable=False)
    subject = db.Column(db.String(180), nullable=False)
    body = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                           onupdate=datetime.utcnow)


class AssistantPending(db.Model):
    """The incomplete natural-language proposal currently being clarified."""

    __tablename__ = "assistant_pending"
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    kind = db.Column(db.String(10), nullable=False)
    text = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                           onupdate=datetime.utcnow)


class AIReportSnapshot(db.Model):
    """Immutable reviewed numbers and source rows for export/email."""

    __tablename__ = "ai_report_snapshot"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    period = db.Column(db.String(10), nullable=False)
    payload = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class MemberPlanningProfile(db.Model):
    """Member-provided task preferences; absent rows use conservative defaults."""

    __tablename__ = "member_planning_profile"
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    skills = db.Column(db.JSON, nullable=False, default=list)
    max_active_tasks = db.Column(db.Integer, nullable=False, default=3)
    unavailable_until = db.Column(db.Date)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                           onupdate=datetime.utcnow)
    __table_args__ = (
        db.CheckConstraint("max_active_tasks BETWEEN 1 AND 10",
                           name="ck_member_planning_capacity"),
    )


class AIUsageLog(db.Model):
    """Successful model calls, without prompts, replies, secrets or price guesses."""

    __tablename__ = "ai_usage_log"
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    provider = db.Column(db.String(20), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    purpose = db.Column(db.String(20), nullable=False)
    input_tokens = db.Column(db.Integer, nullable=False, default=0)
    output_tokens = db.Column(db.Integer, nullable=False, default=0)
    total_tokens = db.Column(db.Integer, nullable=False, default=0)
    elapsed_ms = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
