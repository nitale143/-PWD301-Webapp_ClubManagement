"""Phân quyền Role/Permission, cột xác thực email/mật khẩu, email duy nhất.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-15

- Tạo bảng `role` và nạp quyền mặc định (CN, PCN, TB, THUKY_THUQUY, THANH_VIEN).
- Thêm vào `user`: email_confirmed, email_confirmed_at, must_change_password,
  password_changed_at.
- Chuẩn hóa email về chữ thường và thêm unique index `ix_user_email`.
  Nếu database đang có 2 tài khoản trùng email, migration dừng lại và liệt kê
  để BĐH xử lý trước (sửa email một trong hai tài khoản).
"""
from alembic import op
import sqlalchemy as sa


revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

# Bit quyền – phải khớp app.models.Permission tại thời điểm viết migration
APPROVE_MEMBERS, MANAGE_MEMBERS, MANAGE_EVENTS, MANAGE_FUNDS = 1, 2, 4, 8
ASSIGN_ROLES, HANDOFF_ROLE, BOARD, MANAGE_TEMPLATES = 16, 32, 64, 128
ALL = (APPROVE_MEMBERS | MANAGE_MEMBERS | MANAGE_EVENTS | MANAGE_FUNDS
       | ASSIGN_ROLES | HANDOFF_ROLE | BOARD | MANAGE_TEMPLATES)

ROLES = [
    {"name": "CN", "label": "Chủ nhiệm", "rank": 0, "default": False, "permissions": ALL},
    {"name": "PCN", "label": "Phó chủ nhiệm", "rank": 1, "default": False, "permissions": ALL},
    {"name": "TB", "label": "Trưởng ban", "rank": 2, "default": False,
     "permissions": MANAGE_MEMBERS | MANAGE_EVENTS | HANDOFF_ROLE | BOARD},
    {"name": "THUKY_THUQUY", "label": "Thư ký / Thủ quỹ", "rank": 2, "default": False,
     "permissions": MANAGE_EVENTS | MANAGE_FUNDS | HANDOFF_ROLE | BOARD},
    {"name": "THANH_VIEN", "label": "Thành viên", "rank": 9, "default": True, "permissions": 0},
]


def upgrade():
    role = op.create_table(
        'role',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=20), nullable=False),
        sa.Column('label', sa.String(length=64), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('default', sa.Boolean(), nullable=False),
        sa.Column('permissions', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    with op.batch_alter_table('role', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_role_default'), ['default'], unique=False)
    op.bulk_insert(role, ROLES)

    # Email: chuẩn hóa chữ thường rồi kiểm tra trùng trước khi thêm unique index
    bind = op.get_bind()
    bind.execute(sa.text('UPDATE "user" SET email = lower(trim(email))'))
    duplicates = bind.execute(sa.text(
        'SELECT email, COUNT(*) FROM "user" GROUP BY email HAVING COUNT(*) > 1')).fetchall()
    if duplicates:
        listing = ", ".join(f"{row[0]} ({row[1]} tài khoản)" for row in duplicates)
        raise RuntimeError("Không thể thêm ràng buộc email duy nhất vì có email trùng: "
                           f"{listing}. Hãy sửa email trùng rồi chạy lại `flask db upgrade`.")

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('email_confirmed', sa.Boolean(), server_default=sa.false(), nullable=False))
        batch_op.add_column(sa.Column('email_confirmed_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('must_change_password', sa.Boolean(), server_default=sa.false(), nullable=False))
        batch_op.add_column(sa.Column('password_changed_at', sa.DateTime(), nullable=True))
        batch_op.create_index(batch_op.f('ix_user_email'), ['email'], unique=True)


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_email'))
        batch_op.drop_column('password_changed_at')
        batch_op.drop_column('must_change_password')
        batch_op.drop_column('email_confirmed_at')
        batch_op.drop_column('email_confirmed')

    with op.batch_alter_table('role', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_role_default'))
    op.drop_table('role')
