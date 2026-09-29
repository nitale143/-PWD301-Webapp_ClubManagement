import tempfile
import unittest
import json
import sqlite3
from datetime import date, datetime, timedelta
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from flask import g
from PIL import Image

from app import create_app, db
from app.models import AIProposal, Attendance, Ban, Event, EventRegistration, FundCollection, FundPayment, MemberRecord, Task, User, UserBan
from app.migrations import migrate_legacy_money
from app.services.common import club_now, parse_datetime


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        path = Path(self.directory.name) / "club-test.db"
        self.app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}",
                               "SECRET_KEY": "test-only-key",
                               "PAYMENT_EVIDENCE_DIR": str(Path(self.directory.name) / "evidence")})
        self.client = self.app.test_client()
        self.context = self.app.app_context()
        self.context.push()
        db.session.add(Ban(id=1, ten_ban="Ky thuat"))
        for user_id, role in ((1, "CN"), (2, "THUKY_THUQUY"), (3, "THANH_VIEN"), (4, "THANH_VIEN")):
            user = User(id=user_id, mssv=f"SV{user_id}", ho_ten=f"Member {user_id}",
                        ngay_sinh=date(2003, 1, 1), sdt="0123456789",
                        email=f"member{user_id}@example.test", status="approved", chuc_vu=role)
            user.set_password("test-password")
            db.session.add(user)
            db.session.add(MemberRecord(user_id=user_id, ngay_gia_nhap=date(2024, 1, 1)))
            db.session.add(UserBan(user_id=user_id, ban_id=1))
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        self.context.pop()
        self.directory.cleanup()

    def login(self, user_id):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(user_id)
            session["_fresh"] = True
        g.pop("_login_user", None)

    def csrf(self):
        self.client.get("/admin/roles")
        with self.client.session_transaction() as session:
            return session["_csrf_token"]

    def create_fund(self, amount="100.00", due=None):
        self.login(2)
        today = date.today()
        response = self.client.post("/api/v1/funds", json={
            "name": "Quy thang", "type": "monthly", "amount": amount,
            "start_date": (today - timedelta(days=30)).isoformat(),
            "due_date": (due or today + timedelta(days=2)).isoformat(),
            "applies_to_all": True, "status": "open"})
        self.assertEqual(response.status_code, 201, response.json)
        return response.json["id"]

    def create_event(self, capacity=1):
        self.login(1)
        start = datetime.utcnow() + timedelta(days=1)
        response = self.client.post("/api/v1/events", json={
            "name": "Workshop", "code": f"WS{Event.query.count() + 1}",
            "start_at": start.isoformat(), "end_at": (start + timedelta(hours=2)).isoformat(),
            "registration_deadline": (start - timedelta(hours=1)).isoformat(),
            "capacity": capacity})
        self.assertEqual(response.status_code, 201, response.json)
        return response.json["id"]

    def test_payment_balance_overdue_and_permissions(self):
        self.assertEqual(self.client.get("/api/v1/dashboard").status_code, 401)
        fund_id = self.create_fund(due=date.today() - timedelta(days=1))
        self.login(3)
        forbidden = self.client.post("/api/v1/funds", json={})
        self.assertEqual(forbidden.status_code, 403)
        first = self.client.post(f"/api/v1/funds/{fund_id}/payments",
                                 json={"amount": "40.00", "method": "transfer"})
        self.assertEqual(first.status_code, 201, first.json)
        image = BytesIO()
        Image.new("RGB", (2, 2), "white").save(image, format="PNG")
        image.seek(0)
        evidence = self.client.post(f"/api/v1/payments/{first.json['id']}/evidence",
                                    data={"file": (image, "receipt.png")})
        self.assertEqual(evidence.status_code, 201, evidence.json)
        self.assertTrue(self.client.get(f"/api/v1/payments/evidence/{evidence.json['id']}").data.startswith(b"\x89PNG"))
        duplicate_pending = self.client.post(f"/api/v1/funds/{fund_id}/payments",
                                             json={"amount": "70.00", "method": "transfer"})
        self.assertEqual(duplicate_pending.status_code, 400)
        self.login(2)
        confirmed = self.client.post(f"/api/v1/payments/{first.json['id']}/review",
                                     json={"decision": "confirmed"})
        self.assertEqual(confirmed.status_code, 200, confirmed.json)
        self.assertEqual(self.client.post(f"/api/v1/payments/{first.json['id']}/review",
                                          json={"decision": "confirmed"}).status_code, 400)
        row = self.client.get(f"/api/v1/funds/{fund_id}/balances").json["items"]
        member = next(item for item in row if item["member"]["id"] == 3)
        self.assertEqual(member["balance"]["paid"], "40.00")
        self.assertEqual(member["balance"]["remaining"], "60.00")
        self.assertEqual(member["balance"]["status"], "overdue")
        adjusted = self.client.put(f"/api/v1/funds/{fund_id}/adjustments/3",
                                   json={"type": "reduce", "amount": "20.00", "reason": "Ho tro"})
        self.assertEqual(adjusted.status_code, 200, adjusted.json)
        member = next(item for item in self.client.get(f"/api/v1/funds/{fund_id}/balances").json["items"]
                      if item["member"]["id"] == 3)
        self.assertEqual(member["balance"]["remaining"], "40.00")
        report = self.client.get("/api/v1/reports/funds.xlsx")
        self.assertEqual(report.status_code, 200)
        self.assertTrue(report.data.startswith(b"PK"))

    def test_event_waitlist_promotion_qr_and_activity(self):
        event_id = self.create_event()
        self.login(3)
        first = self.client.post(f"/api/v1/events/{event_id}/registrations", json={})
        self.assertEqual(first.json["status"], "registered")
        self.login(4)
        second = self.client.post(f"/api/v1/events/{event_id}/registrations", json={})
        self.assertEqual(second.json["status"], "waitlist")
        self.login(3)
        cancelled = self.client.post(f"/api/v1/registrations/{first.json['id']}/cancel")
        self.assertEqual(cancelled.json["promoted_id"], second.json["id"])
        event = db.session.get(Event, event_id)
        event.thoi_gian_bat_dau = club_now() - timedelta(minutes=10)
        event.thoi_gian_ket_thuc = club_now() + timedelta(hours=1)
        db.session.commit()
        self.login(1)
        token = self.client.get(f"/api/v1/events/{event_id}/qr").json["token"]
        png = self.client.get(f"/api/v1/events/{event_id}/qr.png")
        self.assertEqual(png.status_code, 200)
        self.assertTrue(png.data.startswith(b"\x89PNG"))
        self.login(4)
        checkin = self.client.post("/api/v1/attendance/checkin", json={"token": token})
        self.assertEqual(checkin.status_code, 200, checkin.json)
        duplicate = self.client.post("/api/v1/attendance/checkin", json={"token": token})
        self.assertEqual(duplicate.status_code, 400, duplicate.json)
        self.assertEqual(self.client.get("/api/v1/members/4/activity").json["points"], 6)

    def test_assistant_scope_and_member_archive(self):
        fund_id = self.create_fund()
        self.login(3)
        answer = self.client.post("/api/v1/assistant", json={"question": "Ai chưa đóng quỹ tháng này?"})
        self.assertEqual(answer.status_code, 200, answer.json)
        self.assertNotIn("Member 4", answer.json["answer"])
        self.assertEqual(self.client.post("/api/v1/assistant", json={"question": "Soạn thông báo nhắc đóng quỹ"}).status_code, 403)
        self.assertEqual(self.client.get("/api/v1/members/4").status_code, 403)
        self.login(2)
        preview = self.client.post("/api/v1/assistant", json={"question": "Soạn thông báo nhắc đóng quỹ"})
        self.assertEqual(preview.status_code, 200)
        self.assertTrue(preview.json["preview"])
        self.login(1)
        archived = self.client.post("/api/v1/members/4/archive")
        self.assertEqual(archived.status_code, 200, archived.json)
        self.login(4)
        self.assertEqual(self.client.get("/api/v1/dashboard").status_code, 403)

    def test_event_edit_copy_cancel_and_activity_setting(self):
        event_id = self.create_event(capacity=2)
        updated = self.client.patch(f"/api/v1/events/{event_id}", json={"location": "Phong A", "capacity": 3})
        self.assertEqual(updated.status_code, 200, updated.json)
        self.assertEqual(updated.json["location"], "Phong A")
        start = datetime.utcnow() + timedelta(days=3)
        copied = self.client.post(f"/api/v1/events/{event_id}/copy", json={
            "code": "COPY1", "start_at": start.isoformat(),
            "end_at": (start + timedelta(hours=1)).isoformat()})
        self.assertEqual(copied.status_code, 201, copied.json)
        self.assertEqual(copied.json["location"], "Phong A")
        cancelled = self.client.post(f"/api/v1/events/{event_id}/cancel")
        self.assertEqual(cancelled.json["status"], "cancelled")
        self.login(3)
        denied = self.client.put("/api/v1/settings/activity", json={"points": {}})
        self.assertEqual(denied.status_code, 403)

    def test_existing_pages_still_render(self):
        self.login(3)
        for path in ("/member", "/event", "/funds", "/ai", "/profile"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)

    def test_member_import_is_atomic(self):
        self.login(1)
        header = "code,name,birth_date,email,phone,department_ids,password\n"
        good = "CSV001,New Member,2003-01-01,new1@example.test,0123456789,1,secret123\n"
        invalid = "bad!,Bad Member,2003-01-01,new2@example.test,0123456789,1,secret123\n"
        rejected = self.client.post("/api/v1/members/import", data={
            "file": (BytesIO((header + good + invalid).encode()), "members.csv")})
        self.assertEqual(rejected.status_code, 400, rejected.json)
        self.assertIsNone(User.query.filter_by(mssv="CSV001").first())
        accepted = self.client.post("/api/v1/members/import", data={
            "file": (BytesIO((header + good).encode()), "members.csv")})
        self.assertEqual(accepted.status_code, 201, accepted.json)
        self.assertEqual(accepted.json["imported"], 1)

    def test_ai_provider_uses_shared_key_and_scoped_context(self):
        self.app.config.update(AI_PROVIDER="anthropic", AI_API_KEY="test-shared-key")
        self.login(3)
        mock_response = BytesIO(json.dumps({"content": [
            {"type": "text", "text": "Đây là câu trả lời từ mô hình."}
        ]}).encode())
        with patch("app.services.assistant.urlopen", return_value=mock_response) as mocked:
            response = self.client.post("/api/v1/assistant", json={"question": "Tóm tắt dữ liệu của tôi"})
        self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(response.json["provider"], "anthropic")
        req = mocked.call_args.args[0]
        self.assertEqual(req.get_header("X-api-key"), "test-shared-key")
        sent = json.loads(req.data)
        self.assertIn("Member 3", sent["messages"][0]["content"])
        self.assertNotIn("Member 4", sent["messages"][0]["content"])

    def test_ai_proposal_requires_approval_then_creates_event_and_tasks(self):
        self.login(1)
        token = self.csrf()
        start = datetime.utcnow() + timedelta(days=3)
        created = self.client.post("/api/v1/assistant/proposals", json={
            "kind": "event", "brief": "Workshop an toàn thông tin",
            "start_at": start.isoformat(),
            "end_at": (start + timedelta(hours=2)).isoformat(), "ban_id": 1},
            headers={"X-CSRF-Token": token})
        self.assertEqual(created.status_code, 201, created.json)
        proposal_id = created.json["id"]
        self.assertEqual(created.json["status"], "pending")
        self.assertEqual(Event.query.count(), 0)
        self.login(3)
        self.assertEqual(self.client.post(f"/api/v1/assistant/proposals/{proposal_id}/review",
                                          json={"decision": "approved"}, headers={"X-CSRF-Token": token}).status_code, 403)
        self.login(1)
        approved = self.client.post(f"/api/v1/assistant/proposals/{proposal_id}/review",
                                    json={"decision": "approved"}, headers={"X-CSRF-Token": token})
        self.assertEqual(approved.status_code, 200, approved.json)
        event_id = approved.json["result_ids"][0]
        self.assertEqual(Event.query.count(), 1)
        self.assertEqual(self.client.post(f"/api/v1/assistant/proposals/{proposal_id}/review",
                                          json={"decision": "approved"}, headers={"X-CSRF-Token": token}).status_code, 400)
        task_proposal = self.client.post("/api/v1/assistant/proposals", json={
            "kind": "task", "brief": "Chuẩn bị tài liệu; Kiểm tra thiết bị",
            "event_id": event_id, "ban_id": 1,
            "deadline": (start + timedelta(hours=1)).isoformat()}, headers={"X-CSRF-Token": token})
        self.assertEqual(task_proposal.status_code, 201, task_proposal.json)
        self.assertEqual(Task.query.count(), 0)
        task_approved = self.client.post(
            f"/api/v1/assistant/proposals/{task_proposal.json['id']}/review",
            json={"decision": "approved"}, headers={"X-CSRF-Token": token})
        self.assertEqual(task_approved.status_code, 200, task_approved.json)
        self.assertEqual(Task.query.count(), 2)

    def test_ai_proposal_web_preview_reject_and_model_output(self):
        self.app.config.update(AI_PROVIDER="anthropic", AI_API_KEY="test-shared-key")
        self.login(1)
        token = self.csrf()
        start = datetime.utcnow() + timedelta(days=4)
        model_json = json.dumps({"name": "Workshop Claude", "content": "Nội dung học tập",
                                 "type": "workshop", "location": "Phòng A", "capacity": 25})
        fake = BytesIO(json.dumps({"content": [{"type": "text", "text": model_json}]}).encode())
        with patch("app.services.assistant.urlopen", return_value=fake):
            created = self.client.post("/ai/proposals/new", data={
                "kind": "event", "brief": "Tổ chức workshop cho CLB",
                "start_at": start.strftime("%Y-%m-%dT%H:%M"),
                "end_at": (start + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M"),
                "csrf_token": token})
        self.assertEqual(created.status_code, 302)
        self.assertEqual(Event.query.count(), 0)
        proposal = AIProposal.query.one()
        self.assertEqual(proposal.payload["name"], "Workshop Claude")
        page = self.client.get("/ai")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"Workshop Claude", page.data)
        rejected = self.client.post(f"/ai/proposals/{proposal.id}/rejected", data={"csrf_token": token})
        self.assertEqual(rejected.status_code, 302)
        self.assertEqual(Event.query.count(), 0)
        self.assertEqual(db.session.get(AIProposal, proposal.id).status, "rejected")

    def test_role_transfer_uses_form_target(self):
        self.login(1)
        role_page = self.client.get("/admin/roles")
        self.assertEqual(role_page.status_code, 200)
        self.assertNotIn(b"onclick=", role_page.data)
        response = self.client.post("/admin/roles/nhuong-quyen", data={"target_id": "3", "csrf_token": self.csrf()})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get(response.location).status_code, 200)
        self.assertEqual(db.session.get(User, 1).chuc_vu, "THANH_VIEN")
        self.assertEqual(db.session.get(User, 3).chuc_vu, "CN")

    def test_treasurer_can_transfer_own_role(self):
        self.login(2)
        self.assertEqual(self.client.get("/admin/roles").status_code, 200)
        response = self.client.post("/admin/roles/nhuong-quyen", data={"target_id": "4", "csrf_token": self.csrf()})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get(response.location).status_code, 200)
        self.assertEqual(db.session.get(User, 2).chuc_vu, "THANH_VIEN")
        self.assertEqual(db.session.get(User, 4).chuc_vu, "THUKY_THUQUY")

    def test_local_time_and_sensitive_form_csrf(self):
        self.assertEqual(parse_datetime("2026-09-28T16:00:00Z", "Giờ"),
                         datetime(2026, 9, 28, 23, 0))
        self.assertEqual(parse_datetime("2026-09-28T23:00:00", "Giờ"),
                         datetime(2026, 9, 28, 23, 0))
        self.login(1)
        self.assertEqual(self.client.post("/admin/roles/nhuong-quyen", data={"target_id": "3"}).status_code, 400)
        self.assertEqual(self.client.post("/api/v1/assistant/proposals", json={}).status_code, 400)
        self.assertEqual(db.session.get(User, 1).chuc_vu, "CN")

    def test_fund_page_uses_collection_payment_flow(self):
        self.login(2)
        token = self.csrf()
        today = club_now().date()
        response = self.client.post("/funds/collections/new", data={
            "csrf_token": token, "name": "Quỹ tháng", "type": "monthly", "amount": "100.00",
            "start_date": today.isoformat(), "due_date": (today + timedelta(days=10)).isoformat(),
        })
        self.assertEqual(response.status_code, 302)
        fund = FundCollection.query.one()
        self.login(3)
        page = self.client.get("/funds")
        self.assertIn("Quỹ tháng".encode(), page.data)
        self.assertEqual(self.client.post(f"/funds/collections/{fund.id}/payments", data={
            "amount": "100.00", "method": "transfer"}).status_code, 400)
        paid = self.client.post(f"/funds/collections/{fund.id}/payments", data={
            "csrf_token": token, "amount": "100.00", "method": "transfer", "transaction_code": "TX123"})
        self.assertEqual(paid.status_code, 302)
        payment = FundPayment.query.one()
        self.assertEqual(payment.trang_thai, "pending")
        self.login(2)
        self.assertIn(b"TX123", self.client.get("/funds").data)
        reviewed = self.client.post(f"/funds/payments/{payment.id}/review", data={
            "csrf_token": token, "decision": "confirmed"})
        self.assertEqual(reviewed.status_code, 302)
        self.assertEqual(db.session.get(FundPayment, payment.id).trang_thai, "confirmed")
        self.login(3)
        self.assertIn(b"paid", self.client.get("/funds").data)

    def test_event_page_registration_qr_and_feedback(self):
        self.login(1)
        token = self.csrf()
        start = club_now() + timedelta(days=1)
        created = self.client.post("/event/new", data={
            "csrf_token": token, "ten_su_kien": "Ngày hội", "ma_su_kien": "NH01",
            "thoi_gian_bat_dau": start.strftime("%Y-%m-%dT%H:%M"),
            "thoi_gian_ket_thuc": (start + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M"),
            "so_nguoi_toi_da": "1", "dia_diem": "Phòng A"})
        self.assertEqual(created.status_code, 302)
        event = Event.query.one()
        self.login(3)
        self.assertIn("Đăng ký tham gia".encode(), self.client.get(f"/event/{event.id}").data)
        registered = self.client.post(f"/event/{event.id}/register", data={"csrf_token": token})
        self.assertEqual(registered.status_code, 302)
        self.assertEqual(EventRegistration.query.one().trang_thai, "registered")
        event.thoi_gian_bat_dau = club_now() - timedelta(minutes=5)
        event.thoi_gian_ket_thuc = club_now() + timedelta(hours=1)
        db.session.commit()
        self.login(1)
        qr = self.client.get(f"/api/v1/events/{event.id}/qr")
        self.assertEqual(qr.status_code, 200)
        self.login(3)
        path = f"/event/{event.id}/checkin/{qr.json['token']}"
        self.assertEqual(self.client.get(path).status_code, 200)
        self.assertEqual(self.client.post(path, data={"csrf_token": token}).status_code, 302)
        self.assertEqual(Attendance.query.one().trang_thai, "late")
        self.login(1)
        self.assertEqual(self.client.post(f"/event/{event.id}/ket-thuc").status_code, 302)
        self.login(3)
        self.assertEqual(self.client.post(f"/event/{event.id}/feedback", data={
            "csrf_token": token, "rating": "5", "comment": "Tốt"}).status_code, 302)
        self.assertIn("Tốt".encode(), self.client.get(f"/event/{event.id}").data)

    def test_event_form_reports_specific_error_and_preserves_input(self):
        self.login(1)
        token = self.csrf()
        start = (club_now() + timedelta(days=1)).replace(second=0, microsecond=0)
        base = {
            "csrf_token": token, "ten_su_kien": "Test1", "ma_su_kien": "T1",
            "thoi_gian_bat_dau": start.strftime("%Y-%m-%dT%H:%M"),
            "thoi_gian_ket_thuc": (start + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M"),
            "dia_diem": "FPT University", "noi_dung": "Test1", "so_nguoi_toi_da": "20",
        }
        cases = [
            ({"thoi_gian_bat_dau": (start - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")},
             "Thời gian bắt đầu phải sau thời điểm hiện tại"),
            ({"thoi_gian_ket_thuc": (start - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M")},
             "Thời gian kết thúc phải sau thời gian bắt đầu"),
            ({"han_dang_ky": (start + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M")},
             "Hạn đăng ký không được sau thời gian bắt đầu"),
            ({"so_nguoi_toi_da": "0"}, "Số người tối đa phải lớn hơn 0"),
        ]
        for change, message in cases:
            with self.subTest(message=message):
                form = {**base, **change}
                response = self.client.post("/event/new", data=form)
                self.assertEqual(response.status_code, 200)
                self.assertIn(message.encode(), response.data)
                for field in ("thoi_gian_bat_dau", "thoi_gian_ket_thuc", "so_nguoi_toi_da"):
                    self.assertIn(f'value="{form[field]}"'.encode(), response.data)
                self.assertIn(b"FPT University", response.data)
        self.assertEqual(Event.query.count(), 0)

    def test_legacy_money_migration_keeps_rows_and_backup(self):
        path = Path(self.directory.name) / "legacy-money.db"
        with sqlite3.connect(path) as connection:
            connection.execute("CREATE TABLE fund_period (id INTEGER PRIMARY KEY)")
            connection.execute('CREATE TABLE "user" (id INTEGER PRIMARY KEY)')
            connection.execute("INSERT INTO fund_period VALUES (1)")
            connection.execute('INSERT INTO "user" VALUES (1)')
            connection.execute("CREATE TABLE fund_transaction (id INTEGER PRIMARY KEY, period_id INTEGER NOT NULL REFERENCES fund_period(id), danh_muc VARCHAR(100) NOT NULL, noi_dung VARCHAR(255), ngay DATE NOT NULL, so_tien FLOAT NOT NULL, tao_boi_id INTEGER REFERENCES user(id))")
            connection.execute("INSERT INTO fund_transaction VALUES (1, 1, 'thu', '', '2026-09-28', 12.50, 1)")
        backup = migrate_legacy_money(path)
        self.assertTrue(backup.is_file())
        with sqlite3.connect(path) as connection:
            column = next(row for row in connection.execute("PRAGMA table_info(fund_transaction)") if row[1] == "so_tien")
            self.assertEqual(column[2], "NUMERIC(14, 2)")
            self.assertEqual(connection.execute("SELECT id, so_tien FROM fund_transaction").fetchone(), (1, 12.5))
        self.assertIsNone(migrate_legacy_money(path))


if __name__ == "__main__":
    unittest.main()
