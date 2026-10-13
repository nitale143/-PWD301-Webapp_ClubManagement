"""Real-route checks for the public landing page and workspace entry points."""

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from flask import g

from app import create_app, db
from app.models import MemberRecord, User


class RealLandingAndWorkspaceTests(unittest.TestCase):
    """Exercise rendered UI and the actual AI stream route on isolated SQLite."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        database_path = Path(self.directory.name) / "real-ui-test.db"
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}",
            "SECRET_KEY": "test-only-key",
            "AI_PROVIDER": "rules",
            "AI_AGENT_ENABLED": False,
            "AI_CHAT_MESSAGES_PER_MINUTE": 100,
            "MAIL_ENABLED": False,
            "SCHEDULER_ENABLED": False,
        })
        self.client = self.app.test_client()
        self.context = self.app.app_context()
        self.context.push()

        for user_id, code, name, role in (
            (1, "SV001", "Morgan Member", "THANH_VIEN"),
            (2, "SV002", "Casey Board", "CN"),
        ):
            user = User(
                id=user_id,
                mssv=code,
                ho_ten=name,
                ngay_sinh=date(2003, 1, 1),
                sdt=f"09000000{user_id:02d}",
                email=f"member{user_id}@example.test",
                status="approved",
                chuc_vu=role,
            )
            user.set_password("test-password")
            db.session.add(user)
            db.session.add(MemberRecord(
                user_id=user_id,
                ngay_gia_nhap=date(2024, 1, 1),
            ))
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        self.context.pop()
        self.directory.cleanup()

    def _login(self, user_id):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(user_id)
            session["_fresh"] = True
        g.pop("_login_user", None)

    def test_guest_root_renders_fia_landing_with_real_routes_and_logo(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("FIA CLUB", html)
        self.assertIn("Cùng công nghệ", html)
        self.assertIn("href=\"/login\"", html)
        self.assertIn("href=\"/register\"", html)
        self.assertIn("href=\"/home\"", html)
        self.assertIn("/static/assets/fia-club-logo.png", html)
        self.assertNotIn("/admin/approve", html)
        self.assertNotIn(">BDH<", html)
        logo = self.client.get("/static/assets/fia-club-logo.png")
        self.assertEqual(logo.status_code, 200)
        self.assertEqual(logo.mimetype, "image/png")
        logo.close()

    def test_authenticated_root_continues_to_protected_workspace(self):
        self._login(1)

        response = self.client.get("/")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/home"))

    def test_guest_cannot_open_protected_member_home(self):
        response = self.client.get("/home")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_member_and_board_workspace_navigation_is_role_sensitive(self):
        self._login(1)
        member_response = self.client.get("/home")
        self.assertEqual(member_response.status_code, 200)
        member_html = member_response.get_data(as_text=True)
        self.assertIn("href=\"/ai\"", member_html)
        self.assertNotIn("href=\"/admin/approve\"", member_html)

        self._login(2)
        board_response = self.client.get("/home")
        self.assertEqual(board_response.status_code, 200)
        board_html = board_response.get_data(as_text=True)
        self.assertIn("href=\"/admin/approve\"", board_html)

    def test_ai_page_posts_to_real_sse_endpoint_and_returns_a_result_frame(self):
        self._login(1)
        page = self.client.get("/ai")

        self.assertEqual(page.status_code, 200)
        self.assertIn('data-stream-url="/ai/stream"', page.get_data(as_text=True))
        with self.client.session_transaction() as session:
            csrf_token = session["_csrf_token"]

        response = self.client.post("/ai/stream", data={
            "csrf_token": csrf_token,
            "new_conversation": "1",
            "message": "Hello",
        })

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.assertTrue(response.mimetype == "text/event-stream")
        frames = [
            json.loads(line.removeprefix("data: "))
            for line in response.get_data(as_text=True).splitlines()
            if line.startswith("data: ")
        ]
        frame_types = [frame["type"] for frame in frames]
        self.assertIn("start", frame_types)
        self.assertIn("result", frame_types)
        result = next(frame["result"] for frame in frames if frame["type"] == "result")
        self.assertTrue(result["answer"])
