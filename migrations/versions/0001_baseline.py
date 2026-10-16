"""Schema gốc của dự án (trước khi có Flask-Migrate).

Database SQLite cũ (tạo bằng db.create_all) đã có đúng schema này: chạy các lệnh
`flask migrate-chats`, `flask migrate-money`, `flask migrate-email-recipients`
rồi `flask db stamp 0001` và `flask db upgrade` (xem docs/DEVELOPER_GUIDE.md).

Revision ID: 0001
Revises: 
Create Date: 2026-10-14 18:59:35.057487

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('ban',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ten_ban', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('ten_ban')
    )
    op.create_table('club_setting',
    sa.Column('key', sa.String(length=100), nullable=False),
    sa.Column('value', sa.JSON(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('key')
    )
    op.create_table('fund_period',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ten_ky', sa.String(length=50), nullable=False),
    sa.Column('ngay_bat_dau', sa.Date(), nullable=False),
    sa.Column('ngay_ket_thuc', sa.Date(), nullable=True),
    sa.Column('is_current', sa.Boolean(), nullable=True),
    sa.Column('da_nhac_ky_moi', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('mssv', sa.String(length=20), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('ho_ten', sa.String(length=100), nullable=False),
    sa.Column('ngay_sinh', sa.Date(), nullable=False),
    sa.Column('sdt', sa.String(length=15), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('facebook_link', sa.String(length=255), nullable=True),
    sa.Column('avatar_url', sa.String(length=255), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('chuc_vu', sa.String(length=20), nullable=False),
    sa.Column('chi_dinh_boi_id', sa.Integer(), nullable=True),
    sa.Column('hoat_dong_status', sa.String(length=20), nullable=True),
    sa.Column('ngay_tao', sa.DateTime(), nullable=True),
    sa.Column('ky_tham_gia_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['chi_dinh_boi_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['ky_tham_gia_id'], ['fund_period.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_mssv'), ['mssv'], unique=True)

    op.create_table('ai_proposal',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('kind', sa.String(length=10), nullable=False),
    sa.Column('request_text', sa.Text(), nullable=False),
    sa.Column('payload', sa.JSON(), nullable=False),
    sa.Column('provider', sa.String(length=20), nullable=False),
    sa.Column('status', sa.String(length=12), nullable=False),
    sa.Column('created_by_id', sa.Integer(), nullable=False),
    sa.Column('reviewed_by_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('reviewed_at', sa.DateTime(), nullable=True),
    sa.Column('result_ids', sa.JSON(), nullable=False),
    sa.CheckConstraint("kind IN ('event','task')", name='ck_ai_proposal_kind'),
    sa.CheckConstraint("status IN ('pending','approved','rejected')", name='ck_ai_proposal_status'),
    sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['reviewed_by_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('ai_proposal', schema=None) as batch_op:
        batch_op.create_index('ix_ai_proposal_creator_status', ['created_by_id', 'status'], unique=False)
        batch_op.create_index(batch_op.f('ix_ai_proposal_status'), ['status'], unique=False)

    op.create_table('ai_report_snapshot',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('period', sa.String(length=10), nullable=False),
    sa.Column('payload', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('ai_report_snapshot', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_ai_report_snapshot_user_id'), ['user_id'], unique=False)

    op.create_table('ai_usage_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('actor_id', sa.Integer(), nullable=True),
    sa.Column('provider', sa.String(length=20), nullable=False),
    sa.Column('model', sa.String(length=100), nullable=False),
    sa.Column('purpose', sa.String(length=20), nullable=False),
    sa.Column('input_tokens', sa.Integer(), nullable=False),
    sa.Column('output_tokens', sa.Integer(), nullable=False),
    sa.Column('total_tokens', sa.Integer(), nullable=False),
    sa.Column('elapsed_ms', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['actor_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('ai_usage_log', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_ai_usage_log_actor_id'), ['actor_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_ai_usage_log_created_at'), ['created_at'], unique=False)

    op.create_table('assistant_pending',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('kind', sa.String(length=10), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_table('audit_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('actor_id', sa.Integer(), nullable=True),
    sa.Column('action', sa.String(length=100), nullable=False),
    sa.Column('object_type', sa.String(length=100), nullable=False),
    sa.Column('object_id', sa.String(length=100), nullable=False),
    sa.Column('details', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['actor_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('audit_log', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_audit_log_action'), ['action'], unique=False)

    op.create_table('chat_conversation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=100), server_default='Cuộc trò chuyện mới', nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('archived', sa.Boolean(), server_default=sa.false(), nullable=False),
    sa.Column('legacy_marker', sa.String(length=16), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'legacy_marker', name='uq_chat_conversation_legacy')
    )
    with op.batch_alter_table('chat_conversation', schema=None) as batch_op:
        batch_op.create_index('ix_chat_conversation_owner_archived_updated', ['user_id', 'archived', 'updated_at', 'id'], unique=False)

    op.create_table('email_proposal',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('recipient_id', sa.Integer(), nullable=True),
    sa.Column('recipient_email', sa.String(length=120), nullable=False),
    sa.Column('request_text', sa.Text(), nullable=False),
    sa.Column('subject', sa.String(length=180), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=12), nullable=False),
    sa.Column('created_by_id', sa.Integer(), nullable=False),
    sa.Column('reviewed_by_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('reviewed_at', sa.DateTime(), nullable=True),
    sa.Column('sent_at', sa.DateTime(), nullable=True),
    sa.CheckConstraint("status IN ('pending','sending','sent','failed','rejected')", name='ck_email_proposal_status'),
    sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['recipient_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['reviewed_by_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('email_proposal', schema=None) as batch_op:
        batch_op.create_index('ix_email_proposal_creator_status', ['created_by_id', 'status'], unique=False)
        batch_op.create_index(batch_op.f('ix_email_proposal_status'), ['status'], unique=False)

    op.create_table('email_template',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('name_key', sa.String(length=100), nullable=False),
    sa.Column('subject', sa.String(length=180), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('created_by_id', sa.Integer(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name_key')
    )
    op.create_table('event',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ten_su_kien', sa.String(length=150), nullable=False),
    sa.Column('ma_su_kien', sa.String(length=30), nullable=False),
    sa.Column('thoi_gian_bat_dau', sa.DateTime(), nullable=False),
    sa.Column('thoi_gian_ket_thuc', sa.DateTime(), nullable=False),
    sa.Column('trang_thai', sa.String(length=20), nullable=True),
    sa.Column('tao_boi_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['tao_boi_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('ma_su_kien')
    )
    op.create_table('fund_collection',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ten_khoan_thu', sa.String(length=180), nullable=False),
    sa.Column('loai', sa.String(length=20), nullable=False),
    sa.Column('so_tien', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('ngay_bat_dau', sa.Date(), nullable=False),
    sa.Column('han_dong', sa.Date(), nullable=False),
    sa.Column('tat_ca_thanh_vien', sa.Boolean(), nullable=False),
    sa.Column('mo_ta', sa.Text(), nullable=False),
    sa.Column('trang_thai', sa.String(length=12), nullable=False),
    sa.Column('tao_boi_id', sa.Integer(), nullable=False),
    sa.Column('tao_luc', sa.DateTime(), nullable=False),
    sa.CheckConstraint("loai IN ('monthly','semester','yearly','event','voluntary','other')", name='ck_fund_collection_type'),
    sa.CheckConstraint("trang_thai IN ('draft','open','closed','cancelled')", name='ck_fund_collection_status'),
    sa.CheckConstraint('han_dong >= ngay_bat_dau', name='ck_fund_collection_dates'),
    sa.CheckConstraint('so_tien >= 0', name='ck_fund_collection_amount'),
    sa.ForeignKeyConstraint(['tao_boi_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('fund_collection', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_fund_collection_han_dong'), ['han_dong'], unique=False)
        batch_op.create_index('ix_fund_collection_status_due', ['trang_thai', 'han_dong'], unique=False)
        batch_op.create_index(batch_op.f('ix_fund_collection_trang_thai'), ['trang_thai'], unique=False)

    op.create_table('fund_due',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('period_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('da_dong', sa.Boolean(), nullable=True),
    sa.Column('ngay_dong', sa.Date(), nullable=True),
    sa.ForeignKeyConstraint(['period_id'], ['fund_period.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('fund_transaction',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('period_id', sa.Integer(), nullable=False),
    sa.Column('danh_muc', sa.String(length=100), nullable=False),
    sa.Column('noi_dung', sa.String(length=255), nullable=True),
    sa.Column('ngay', sa.Date(), nullable=False),
    sa.Column('so_tien', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('tao_boi_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['period_id'], ['fund_period.id'], ),
    sa.ForeignKeyConstraint(['tao_boi_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('member_activity',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('ban_id', sa.Integer(), nullable=False),
    sa.Column('period_id', sa.Integer(), nullable=False),
    sa.Column('tong_task', sa.Integer(), nullable=True),
    sa.Column('task_hoan_thanh', sa.Integer(), nullable=True),
    sa.Column('phan_tram', sa.Float(), nullable=True),
    sa.Column('trang_thai', sa.String(length=20), nullable=True),
    sa.Column('cap_nhat_luc', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['ban_id'], ['ban.id'], ),
    sa.ForeignKeyConstraint(['period_id'], ['fund_period.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'ban_id', 'period_id', name='uq_activity_user_ban_period')
    )
    op.create_table('member_planning_profile',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('skills', sa.JSON(), nullable=False),
    sa.Column('max_active_tasks', sa.Integer(), nullable=False),
    sa.Column('unavailable_until', sa.Date(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.CheckConstraint('max_active_tasks BETWEEN 1 AND 10', name='ck_member_planning_capacity'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_table('member_record',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('ngay_gia_nhap', sa.Date(), nullable=False),
    sa.Column('tinh_trang', sa.String(length=20), nullable=False),
    sa.Column('ghi_chu', sa.Text(), nullable=False),
    sa.Column('luu_tru_luc', sa.DateTime(), nullable=True),
    sa.CheckConstraint("tinh_trang IN ('active','paused','left')", name='ck_member_status'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_table('notification',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('noi_dung', sa.String(length=255), nullable=False),
    sa.Column('da_doc', sa.Boolean(), nullable=True),
    sa.Column('thoi_gian', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_ban',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('ban_id', sa.Integer(), nullable=False),
    sa.Column('is_truong_ban', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['ban_id'], ['ban.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('activity_point',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=True),
    sa.Column('so_diem', sa.Integer(), nullable=False),
    sa.Column('loai', sa.String(length=12), nullable=False),
    sa.Column('ly_do', sa.Text(), nullable=False),
    sa.Column('tao_boi_id', sa.Integer(), nullable=False),
    sa.Column('tao_luc', sa.DateTime(), nullable=False),
    sa.CheckConstraint('length(trim(ly_do)) > 0', name='ck_activity_point_reason'),
    sa.ForeignKeyConstraint(['event_id'], ['event.id'], ),
    sa.ForeignKeyConstraint(['tao_boi_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('activity_point', schema=None) as batch_op:
        batch_op.create_index('ix_activity_point_member_time', ['user_id', 'tao_luc'], unique=False)

    op.create_table('chat_message',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.String(length=10), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('thoi_gian', sa.DateTime(), nullable=True),
    sa.Column('conversation_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['conversation_id'], ['chat_conversation.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('chat_message', schema=None) as batch_op:
        batch_op.create_index('ix_chat_message_conversation_id_id', ['conversation_id', 'id'], unique=False)

    op.create_table('conversation_pending',
    sa.Column('conversation_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('kind', sa.String(length=10), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['conversation_id'], ['chat_conversation.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('conversation_id')
    )
    op.create_table('event_detail',
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('loai', sa.String(length=100), nullable=False),
    sa.Column('noi_dung', sa.Text(), nullable=False),
    sa.Column('dia_diem', sa.String(length=300), nullable=False),
    sa.Column('anh_dai_dien', sa.String(length=255), nullable=False),
    sa.Column('han_dang_ky', sa.DateTime(), nullable=True),
    sa.Column('so_nguoi_toi_da', sa.Integer(), nullable=True),
    sa.Column('phu_trach_id', sa.Integer(), nullable=True),
    sa.Column('fund_id', sa.Integer(), nullable=True),
    sa.Column('tat_ca_thanh_vien', sa.Boolean(), nullable=False),
    sa.CheckConstraint('so_nguoi_toi_da IS NULL OR so_nguoi_toi_da > 0', name='ck_event_capacity'),
    sa.ForeignKeyConstraint(['event_id'], ['event.id'], ),
    sa.ForeignKeyConstraint(['fund_id'], ['fund_collection.id'], ),
    sa.ForeignKeyConstraint(['phu_trach_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('event_id')
    )
    op.create_table('event_feedback',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('danh_gia', sa.Integer(), nullable=False),
    sa.Column('binh_luan', sa.Text(), nullable=False),
    sa.Column('tao_luc', sa.DateTime(), nullable=False),
    sa.CheckConstraint('danh_gia BETWEEN 1 AND 5', name='ck_event_feedback_rating'),
    sa.ForeignKeyConstraint(['event_id'], ['event.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('event_id', 'user_id', name='uq_event_feedback_member')
    )
    op.create_table('event_registration',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('trang_thai', sa.String(length=12), nullable=False),
    sa.Column('dang_ky_luc', sa.DateTime(), nullable=False),
    sa.Column('huy_luc', sa.DateTime(), nullable=True),
    sa.CheckConstraint("trang_thai IN ('registered','waitlist','cancelled')", name='ck_event_registration_status'),
    sa.ForeignKeyConstraint(['event_id'], ['event.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('event_id', 'user_id', name='uq_event_registration_member')
    )
    with op.batch_alter_table('event_registration', schema=None) as batch_op:
        batch_op.create_index('ix_event_registration_event_status', ['event_id', 'trang_thai'], unique=False)

    op.create_table('event_target_ban',
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('ban_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['ban_id'], ['ban.id'], ),
    sa.ForeignKeyConstraint(['event_id'], ['event.id'], ),
    sa.PrimaryKeyConstraint('event_id', 'ban_id')
    )
    op.create_table('fund_adjustment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('fund_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('loai', sa.String(length=10), nullable=False),
    sa.Column('so_tien', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('ly_do', sa.Text(), nullable=False),
    sa.Column('tao_boi_id', sa.Integer(), nullable=False),
    sa.Column('tao_luc', sa.DateTime(), nullable=False),
    sa.CheckConstraint("loai IN ('exempt','reduce')", name='ck_fund_adjustment_type'),
    sa.CheckConstraint('length(trim(ly_do)) > 0', name='ck_fund_adjustment_reason'),
    sa.CheckConstraint('so_tien >= 0', name='ck_fund_adjustment_amount'),
    sa.ForeignKeyConstraint(['fund_id'], ['fund_collection.id'], ),
    sa.ForeignKeyConstraint(['tao_boi_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('fund_id', 'user_id', name='uq_fund_adjustment_member')
    )
    op.create_table('fund_payment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('fund_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('so_tien', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('ngay_dong', sa.DateTime(), nullable=False),
    sa.Column('phuong_thuc', sa.String(length=20), nullable=False),
    sa.Column('ma_giao_dich', sa.String(length=100), nullable=False),
    sa.Column('trang_thai', sa.String(length=12), nullable=False),
    sa.Column('xac_nhan_boi_id', sa.Integer(), nullable=True),
    sa.Column('xac_nhan_luc', sa.DateTime(), nullable=True),
    sa.Column('ghi_chu', sa.Text(), nullable=False),
    sa.CheckConstraint("trang_thai != 'confirmed' OR xac_nhan_boi_id IS NOT NULL", name='ck_fund_payment_reviewer'),
    sa.CheckConstraint("trang_thai IN ('pending','confirmed','rejected')", name='ck_fund_payment_status'),
    sa.CheckConstraint('so_tien > 0', name='ck_fund_payment_amount'),
    sa.ForeignKeyConstraint(['fund_id'], ['fund_collection.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['xac_nhan_boi_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('fund_payment', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_fund_payment_fund_id'), ['fund_id'], unique=False)
        batch_op.create_index('ix_fund_payment_fund_member_status', ['fund_id', 'user_id', 'trang_thai'], unique=False)
        batch_op.create_index(batch_op.f('ix_fund_payment_trang_thai'), ['trang_thai'], unique=False)
        batch_op.create_index(batch_op.f('ix_fund_payment_user_id'), ['user_id'], unique=False)

    op.create_table('fund_target_ban',
    sa.Column('fund_id', sa.Integer(), nullable=False),
    sa.Column('ban_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['ban_id'], ['ban.id'], ),
    sa.ForeignKeyConstraint(['fund_id'], ['fund_collection.id'], ),
    sa.PrimaryKeyConstraint('fund_id', 'ban_id')
    )
    op.create_table('qr_checkin_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('account_id', sa.Integer(), nullable=False),
    sa.Column('checkin_luc', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['event_id'], ['event.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('task',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('ten_task', sa.String(length=150), nullable=False),
    sa.Column('mo_ta', sa.Text(), nullable=True),
    sa.Column('deadline', sa.DateTime(), nullable=False),
    sa.Column('trang_thai', sa.String(length=20), nullable=True),
    sa.Column('ban_id', sa.Integer(), nullable=True),
    sa.Column('assignee_id', sa.Integer(), nullable=False),
    sa.Column('noi_dung_nop', sa.Text(), nullable=True),
    sa.Column('lan_nop_gan_nhat', sa.DateTime(), nullable=True),
    sa.Column('nhan_xet_bdh', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['assignee_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['ban_id'], ['ban.id'], ),
    sa.ForeignKeyConstraint(['event_id'], ['event.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('attendance',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('registration_id', sa.Integer(), nullable=False),
    sa.Column('trang_thai', sa.String(length=12), nullable=False),
    sa.Column('checkin_luc', sa.DateTime(), nullable=True),
    sa.Column('checkin_boi_id', sa.Integer(), nullable=True),
    sa.Column('ghi_chu', sa.Text(), nullable=False),
    sa.CheckConstraint("trang_thai IN ('on_time','late','excused','absent','pending')", name='ck_attendance_status'),
    sa.ForeignKeyConstraint(['checkin_boi_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['registration_id'], ['event_registration.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('registration_id')
    )
    op.create_table('payment_evidence',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('payment_id', sa.Integer(), nullable=False),
    sa.Column('duong_dan', sa.String(length=255), nullable=False),
    sa.Column('tai_len_luc', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['payment_id'], ['fund_payment.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('payment_evidence')
    op.drop_table('attendance')
    op.drop_table('task')
    op.drop_table('qr_checkin_log')
    op.drop_table('fund_target_ban')
    with op.batch_alter_table('fund_payment', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_fund_payment_user_id'))
        batch_op.drop_index(batch_op.f('ix_fund_payment_trang_thai'))
        batch_op.drop_index('ix_fund_payment_fund_member_status')
        batch_op.drop_index(batch_op.f('ix_fund_payment_fund_id'))

    op.drop_table('fund_payment')
    op.drop_table('fund_adjustment')
    op.drop_table('event_target_ban')
    with op.batch_alter_table('event_registration', schema=None) as batch_op:
        batch_op.drop_index('ix_event_registration_event_status')

    op.drop_table('event_registration')
    op.drop_table('event_feedback')
    op.drop_table('event_detail')
    op.drop_table('conversation_pending')
    with op.batch_alter_table('chat_message', schema=None) as batch_op:
        batch_op.drop_index('ix_chat_message_conversation_id_id')

    op.drop_table('chat_message')
    with op.batch_alter_table('activity_point', schema=None) as batch_op:
        batch_op.drop_index('ix_activity_point_member_time')

    op.drop_table('activity_point')
    op.drop_table('user_ban')
    op.drop_table('notification')
    op.drop_table('member_record')
    op.drop_table('member_planning_profile')
    op.drop_table('member_activity')
    op.drop_table('fund_transaction')
    op.drop_table('fund_due')
    with op.batch_alter_table('fund_collection', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_fund_collection_trang_thai'))
        batch_op.drop_index('ix_fund_collection_status_due')
        batch_op.drop_index(batch_op.f('ix_fund_collection_han_dong'))

    op.drop_table('fund_collection')
    op.drop_table('event')
    op.drop_table('email_template')
    with op.batch_alter_table('email_proposal', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_email_proposal_status'))
        batch_op.drop_index('ix_email_proposal_creator_status')

    op.drop_table('email_proposal')
    with op.batch_alter_table('chat_conversation', schema=None) as batch_op:
        batch_op.drop_index('ix_chat_conversation_owner_archived_updated')

    op.drop_table('chat_conversation')
    with op.batch_alter_table('audit_log', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_audit_log_action'))

    op.drop_table('audit_log')
    op.drop_table('assistant_pending')
    with op.batch_alter_table('ai_usage_log', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_ai_usage_log_created_at'))
        batch_op.drop_index(batch_op.f('ix_ai_usage_log_actor_id'))

    op.drop_table('ai_usage_log')
    with op.batch_alter_table('ai_report_snapshot', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_ai_report_snapshot_user_id'))

    op.drop_table('ai_report_snapshot')
    with op.batch_alter_table('ai_proposal', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_ai_proposal_status'))
        batch_op.drop_index('ix_ai_proposal_creator_status')

    op.drop_table('ai_proposal')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_mssv'))

    op.drop_table('user')
    op.drop_table('fund_period')
    op.drop_table('club_setting')
    op.drop_table('ban')
