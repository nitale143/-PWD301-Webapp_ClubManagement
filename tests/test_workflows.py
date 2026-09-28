import tempfile
import unittest
import json
from datetime import date, datetime, timedelta
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from flask import g
from PIL import Image

from app import create_app, db
from app.models import AIProposal, Ban, Event, MemberRecord, Task, User, UserBan


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
        event.thoi_gian_bat_dau = datetime.utcnow() - timedelta(minutes=10)
        event.thoi_gian_ket_thuc = datetime.utcnow() + timedelta(hours=1)
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
        start = datetime.utcnow() + timedelta(days=3)
        created = self.client.post("/api/v1/assistant/proposals", json={
            "kind": "event", "brief": "Workshop an toàn thông tin",
            "start_at": start.isoformat(),
            "end_at": (start + timedelta(hours=2)).isoformat(), "ban_id": 1})
        self.assertEqual(created.status_code, 201, created.json)
        proposal_id = created.json["id"]
        self.assertEqual(created.json["status"], "pending")
        self.assertEqual(Event.query.count(), 0)
        self.login(3)
        self.assertEqual(self.client.post(f"/api/v1/assistant/proposals/{proposal_id}/review",
                                          json={"decision": "approved"}).status_code, 403)
        self.login(1)
        approved = self.client.post(f"/api/v1/assistant/proposals/{proposal_id}/review",
                                    json={"decision": "approved"})
        self.assertEqual(approved.status_code, 200, approved.json)
        event_id = approved.json["result_ids"][0]
        self.assertEqual(Event.query.count(), 1)
        self.assertEqual(self.client.post(f"/api/v1/assistant/proposals/{proposal_id}/review",
                                          json={"decision": "approved"}).status_code, 400)
        task_proposal = self.client.post("/api/v1/assistant/proposals", json={
            "kind": "task", "brief": "Chuẩn bị tài liệu; Kiểm tra thiết bị",
            "event_id": event_id, "ban_id": 1,
            "deadline": (start + timedelta(hours=1)).isoformat()})
        self.assertEqual(task_proposal.status_code, 201, task_proposal.json)
        self.assertEqual(Task.query.count(), 0)
        task_approved = self.client.post(
            f"/api/v1/assistant/proposals/{task_proposal.json['id']}/review",
            json={"decision": "approved"})
        self.assertEqual(task_approved.status_code, 200, task_approved.json)
        self.assertEqual(Task.query.count(), 2)

    def test_ai_proposal_web_preview_reject_and_model_output(self):
        self.app.config.update(AI_PROVIDER="anthropic", AI_API_KEY="test-shared-key")
        self.login(1)
        start = datetime.utcnow() + timedelta(days=4)
        model_json = json.dumps({"name": "Workshop Claude", "content": "Nội dung học tập",
                                 "type": "workshop", "location": "Phòng A", "capacity": 25})
        fake = BytesIO(json.dumps({"content": [{"type": "text", "text": model_json}]}).encode())
        with patch("app.services.assistant.urlopen", return_value=fake):
            created = self.client.post("/ai/proposals/new", data={
                "kind": "event", "brief": "Tổ chức workshop cho CLB",
                "start_at": start.strftime("%Y-%m-%dT%H:%M"),
                "end_at": (start + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M")})
        self.assertEqual(created.status_code, 302)
        self.assertEqual(Event.query.count(), 0)
        proposal = AIProposal.query.one()
        self.assertEqual(proposal.payload["name"], "Workshop Claude")
        page = self.client.get("/ai")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"Workshop Claude", page.data)
        rejected = self.client.post(f"/ai/proposals/{proposal.id}/rejected")
        self.assertEqual(rejected.status_code, 302)
        self.assertEqual(Event.query.count(), 0)
        self.assertEqual(db.session.get(AIProposal, proposal.id).status, "rejected")

    def test_role_transfer_uses_form_target(self):
        self.login(1)
        role_page = self.client.get("/admin/roles")
        self.assertEqual(role_page.status_code, 200)
        self.assertNotIn(b"onclick=", role_page.data)
        response = self.client.post("/admin/roles/nhuong-quyen", data={"target_id": "3"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get(response.location).status_code, 200)
        self.assertEqual(db.session.get(User, 1).chuc_vu, "THANH_VIEN")
        self.assertEqual(db.session.get(User, 3).chuc_vu, "CN")

    def test_treasurer_can_transfer_own_role(self):
        self.login(2)
        self.assertEqual(self.client.get("/admin/roles").status_code, 200)
        response = self.client.post("/admin/roles/nhuong-quyen", data={"target_id": "4"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get(response.location).status_code, 200)
        self.assertEqual(db.session.get(User, 2).chuc_vu, "THANH_VIEN")
        self.assertEqual(db.session.get(User, 4).chuc_vu, "THUKY_THUQUY")


if __name__ == "__main__":
    unittest.main()
