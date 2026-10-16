"""Lệnh quản trị chạy bằng `flask --app run.py <lệnh>` (Ch11 – vận hành).

Lệnh có sẵn:
    flask --app run.py db upgrade           # (Flask-Migrate) cập nhật schema mới nhất
    flask --app run.py init-db              # upgrade + tạo 3 ban mặc định + bảng role
    flask --app run.py create-cn            # tạo tài khoản Chủ nhiệm đầu tiên
    flask --app run.py sync-roles           # ghi đè quyền của các role theo DEFAULT_ROLES
    flask --app run.py run-scheduler        # chạy job định kỳ ở tiến trình riêng
    flask --app run.py migrate-chats | migrate-money | migrate-email-recipients
                                            # nâng cấp database SQLite cũ (trước khi có migrations/)
"""
from datetime import date
import time

import click
from flask_migrate import upgrade

from app import db


def register_cli(app):
    """Đăng ký các lệnh `flask --app run.py ...` (init-db, sync-roles, create-cn, run-scheduler,
    migrate-*) vào app.
    """
    from app.legacy_sqlite import (
        migrate_chat_conversations, migrate_email_recipients, migrate_legacy_money,
    )
    from app.models import Ban, Role, User
    from app.validators import MSSV_RE, password_problems

    def _require_sqlite_file():
        if db.engine.url.get_backend_name() != "sqlite" or not db.engine.url.database:
            raise click.ClickException("Lệnh này chỉ hỗ trợ SQLite database trên đĩa.")

    @app.cli.command("init-db")
    def init_db():
        """Cập nhật schema bằng migration rồi tạo dữ liệu nền (ban, role)."""
        upgrade()
        Role.insert_roles()
        if not Ban.query.first():
            for ten in ["Kỹ thuật", "Nhân sự", "Truyền thông"]:
                db.session.add(Ban(ten_ban=ten))
            db.session.commit()
            click.echo("Đã tạo 3 ban hoạt động mặc định.")
        click.echo("Database đã sẵn sàng.")

    @app.cli.command("sync-roles")
    def sync_roles():
        """Ghi đè quyền trong bảng role theo app.models.DEFAULT_ROLES."""
        Role.insert_roles(overwrite=True)
        for role in Role.query.order_by(Role.rank, Role.name):
            click.echo(f"{role.name:<14} rank={role.rank} permissions={role.permissions}")

    @app.cli.command("create-cn")
    def create_cn():
        """Tạo tài khoản Chủ nhiệm đầu tiên (đã duyệt) để khởi động hệ thống."""
        Role.insert_roles()
        mssv = click.prompt("MSSV").strip()
        if not MSSV_RE.fullmatch(mssv):
            raise click.ClickException("MSSV phải gồm 6-15 ký tự chữ/số.")
        if User.query.filter_by(mssv=mssv).first():
            raise click.ClickException("MSSV này đã tồn tại.")
        ho_ten = click.prompt("Họ tên").strip()
        email = click.prompt("Email").strip().lower()
        if User.query.filter_by(email=email).first():
            raise click.ClickException("Email này đã được dùng.")
        password = click.prompt("Mật khẩu", hide_input=True, confirmation_prompt=True)
        problems = password_problems(password, mssv)
        if problems:
            raise click.ClickException(" ".join(problems))

        user = User(
            mssv=mssv, ho_ten=ho_ten, ngay_sinh=date(2000, 1, 1), sdt="0000000000",
            email=email, facebook_link="https://facebook.com/placeholder",
            status="approved", chuc_vu="CN",
        )
        user.password = password
        db.session.add(user)
        db.session.commit()
        click.echo(f"Đã tạo Chủ nhiệm {ho_ten} ({mssv}). Hãy đăng nhập và cập nhật thông tin cá nhân.")

    @app.cli.command("run-scheduler")
    def run_scheduler():
        """Chạy APScheduler ở tiến trình riêng (dùng khi web chạy nhiều worker Gunicorn)."""
        from app.scheduler import init_scheduler
        init_scheduler(app, force=True)
        click.echo("Scheduler đang chạy. Nhấn Ctrl+C để dừng.")
        try:
            while True:
                time.sleep(3600)
        except (KeyboardInterrupt, SystemExit):
            pass

    # ---- nâng cấp database SQLite tạo trước khi có thư mục migrations/ ----
    @app.cli.command("migrate-chats")
    def migrate_chats():
        """Kiểm tra/nâng cấp bảng hội thoại AI trên SQLite cũ (an toàn khi chạy lại)."""
        if db.engine.url.get_backend_name() != "sqlite":
            raise click.ClickException("Lệnh này chỉ hỗ trợ SQLite.")
        backup = migrate_chat_conversations(db.engine.url.database or ":memory:")
        click.echo(f"Đã cập nhật hội thoại AI. Bản sao lưu: {backup}" if backup else
                   "Cấu trúc hội thoại AI đã đúng; không cần cập nhật.")

    @app.cli.command("migrate-money")
    def migrate_money():
        """Sao lưu rồi đổi cột tiền FLOAT cũ sang NUMERIC."""
        _require_sqlite_file()
        backup = migrate_legacy_money(db.engine.url.database)
        click.echo(f"Đã cập nhật cột tiền. Bản sao lưu: {backup}" if backup else
                   "Cột tiền đã đúng kiểu; không cần cập nhật.")

    @app.cli.command("migrate-email-recipients")
    def migrate_email_drafts():
        """Sao lưu rồi cho phép nháp email gửi tới địa chỉ ngoài CLB."""
        _require_sqlite_file()
        backup = migrate_email_recipients(db.engine.url.database)
        click.echo(f"Đã cập nhật nháp email. Bản sao lưu: {backup}" if backup else
                   "Cấu trúc nháp email đã đúng; không cần cập nhật.")
