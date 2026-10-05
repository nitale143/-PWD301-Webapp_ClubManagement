"""Explicit, backed-up SQLite upgrades for databases created by older releases."""

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


def migrate_legacy_money(database_path):
    path = Path(database_path).resolve()
    if not path.is_file():
        raise ValueError(f"Không tìm thấy SQLite database: {path}")

    with closing(sqlite3.connect(path, timeout=30)) as connection:
        columns = connection.execute("PRAGMA table_info(fund_transaction)").fetchall()
        amount_column = next((row for row in columns if row[1] == "so_tien"), None)
        if amount_column is None:
            raise ValueError("Không tìm thấy cột fund_transaction.so_tien.")
        if amount_column[2].upper().startswith("NUMERIC"):
            return None
        if amount_column[2].upper() != "FLOAT":
            raise ValueError(f"Kiểu cột không được hỗ trợ: {amount_column[2]}")
        amounts = connection.execute("SELECT so_tien FROM fund_transaction").fetchall()
        if any(Decimal(str(row[0])).as_tuple().exponent < -2 for row in amounts):
            raise ValueError("Có giao dịch cũ nhiều hơn 2 chữ số thập phân; cần đối soát trước khi chuyển.")
        backup = path.with_name(path.name + ".bak-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f"))
        with closing(sqlite3.connect(backup)) as backup_connection:
            connection.backup(backup_connection)

        connection.execute("PRAGMA foreign_keys=OFF")
        try:
            connection.execute("BEGIN IMMEDIATE")
            before = connection.execute("SELECT COUNT(*) FROM fund_transaction").fetchone()[0]
            connection.execute("""
                CREATE TABLE fund_transaction_new (
                    id INTEGER NOT NULL PRIMARY KEY,
                    period_id INTEGER NOT NULL REFERENCES fund_period (id),
                    danh_muc VARCHAR(100) NOT NULL,
                    noi_dung VARCHAR(255),
                    ngay DATE NOT NULL,
                    so_tien NUMERIC(14, 2) NOT NULL,
                    tao_boi_id INTEGER REFERENCES user (id)
                )
            """)
            connection.execute("""
                INSERT INTO fund_transaction_new
                    (id, period_id, danh_muc, noi_dung, ngay, so_tien, tao_boi_id)
                SELECT id, period_id, danh_muc, noi_dung, ngay, so_tien, tao_boi_id
                FROM fund_transaction
            """)
            after = connection.execute("SELECT COUNT(*) FROM fund_transaction_new").fetchone()[0]
            if before != after:
                raise RuntimeError("Số giao dịch thay đổi trong quá trình chuyển.")
            connection.execute("DROP TABLE fund_transaction")
            connection.execute("ALTER TABLE fund_transaction_new RENAME TO fund_transaction")
            if connection.execute("PRAGMA foreign_key_check").fetchone():
                raise RuntimeError("Lỗi ràng buộc khóa ngoại sau khi chuyển.")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.execute("PRAGMA foreign_keys=ON")
        return backup


def migrate_email_recipients(database_path):
    """Allow external email drafts while preserving existing member drafts."""
    path = Path(database_path).resolve()
    if not path.is_file():
        raise ValueError(f"Không tìm thấy SQLite database: {path}")

    with closing(sqlite3.connect(path, timeout=30)) as connection:
        columns = connection.execute("PRAGMA table_info(email_proposal)").fetchall()
        if not columns:
            return None  # Fresh databases get the new schema from db.create_all().
        recipient = next((row for row in columns if row[1] == "recipient_id"), None)
        if recipient is None:
            raise ValueError("Không tìm thấy cột email_proposal.recipient_id.")
        if recipient[3] == 0:
            return None
        if recipient[3] != 1:
            raise ValueError("Kiểu cột email_proposal.recipient_id không được hỗ trợ.")

        backup = path.with_name(path.name + ".bak-email-" +
                                datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f"))
        with closing(sqlite3.connect(backup)) as backup_connection:
            connection.backup(backup_connection)
        backup.chmod(0o600)

        connection.execute("PRAGMA foreign_keys=OFF")
        try:
            connection.execute("BEGIN IMMEDIATE")
            before = connection.execute("SELECT COUNT(*) FROM email_proposal").fetchone()[0]
            connection.execute("""
                CREATE TABLE email_proposal_new (
                    id INTEGER NOT NULL PRIMARY KEY,
                    recipient_id INTEGER REFERENCES user (id),
                    recipient_email VARCHAR(120) NOT NULL,
                    request_text TEXT NOT NULL,
                    subject VARCHAR(180) NOT NULL,
                    body TEXT NOT NULL,
                    status VARCHAR(12) NOT NULL,
                    created_by_id INTEGER NOT NULL REFERENCES user (id),
                    reviewed_by_id INTEGER REFERENCES user (id),
                    created_at DATETIME NOT NULL,
                    reviewed_at DATETIME,
                    sent_at DATETIME,
                    CONSTRAINT ck_email_proposal_status
                        CHECK (status IN ('pending','sending','sent','failed','rejected'))
                )
            """)
            connection.execute("""
                INSERT INTO email_proposal_new
                    (id, recipient_id, recipient_email, request_text, subject, body,
                     status, created_by_id, reviewed_by_id, created_at, reviewed_at, sent_at)
                SELECT id, recipient_id, recipient_email, request_text, subject, body,
                       status, created_by_id, reviewed_by_id, created_at, reviewed_at, sent_at
                FROM email_proposal
            """)
            after = connection.execute("SELECT COUNT(*) FROM email_proposal_new").fetchone()[0]
            if before != after:
                raise RuntimeError("Số bản nháp email thay đổi trong quá trình chuyển.")
            connection.execute("DROP TABLE email_proposal")
            connection.execute("ALTER TABLE email_proposal_new RENAME TO email_proposal")
            connection.execute("CREATE INDEX ix_email_proposal_status ON email_proposal (status)")
            connection.execute("CREATE INDEX ix_email_proposal_creator_status ON email_proposal (created_by_id, status)")
            if connection.execute("PRAGMA foreign_key_check").fetchone():
                raise RuntimeError("Lỗi ràng buộc khóa ngoại sau khi chuyển nháp email.")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.execute("PRAGMA foreign_keys=ON")
        return backup
