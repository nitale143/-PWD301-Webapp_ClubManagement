"""Manual browser verification server. Never uses the club database or credentials."""
import tempfile
from datetime import date
from pathlib import Path

from app import create_app, db
from app.models import Ban, MemberRecord, User, UserBan


def main():
    with tempfile.TemporaryDirectory(prefix="fia-ui-test-") as directory:
        app = create_app({
            "TESTING": True, "TEMPLATES_AUTO_RELOAD": True, "SECRET_KEY": "browser-test-only",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(Path(directory) / "ui.db"),
            "AI_PROVIDER": "rules", "AI_API_KEY": "", "GEMINI_API_KEY": "",
            "AI_CHAT_MESSAGES_PER_MINUTE": 200, "MAIL_ENABLED": False,
        })
        with app.app_context():
            db.session.add(Ban(id=1, ten_ban="Kỹ thuật"))
            for user_id, role in ((1, "CN"), (2, "THANH_VIEN")):
                user = User(id=user_id, mssv=f"QA00{user_id}", ho_ten=f"QA User {user_id}",
                            ngay_sinh=date(2003, 1, 1), sdt=f"090000000{user_id}",
                            email=f"qa{user_id}@example.test", status="approved", chuc_vu=role)
                user.set_password("ui-test-password")
                db.session.add(user)
                db.session.add(MemberRecord(user_id=user_id, ngay_gia_nhap=date(2026, 1, 1)))
                db.session.add(UserBan(user_id=user_id, ban_id=1))
            db.session.commit()
        app.run(host="0.0.0.0", port=5090, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
