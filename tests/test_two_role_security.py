import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from flask import g

from app import create_app, db
from app.models import Ban, Event, MemberRecord, Task, User, UserBan
from app.services.access import (
    can_manage_member,
    can_view_all_members,
    is_admin,
    is_board,
    is_treasurer,
    set_member_left_safely,
    set_member_role_safely,
    visible_members,
)
from app.permissions import can_assign_role


class TwoRoleSecurityTests(unittest.TestCase):
    ADMIN_ROLES = ((1, "CN"), (2, "PCN"), (3, "TB"), (4, "THUKY_THUQUY"))

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        database_path = Path(self.directory.name) / "two-role-test.db"
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}",
            "SECRET_KEY": "test-only-key",
            "AI_PROVIDER": "rules",
        })
        self.client = self.app.test_client()
        self.context = self.app.app_context()
        self.context.push()
        db.session.add_all([
            Ban(id=1, ten_ban="Engineering"),
            Ban(id=2, ten_ban="Communications"),
        ])
        for user_id, role in (*self.ADMIN_ROLES, (5, "THANH_VIEN"), (6, "THANH_VIEN")):
            user = User(
                id=user_id,
                mssv=f"SV{user_id:03d}",
                ho_ten=f"Member {user_id}",
                ngay_sinh=date(2003, 1, 1),
                sdt=f"09000000{user_id:02d}",
                email=f"member{user_id}@example.test",
                status="approved",
                chuc_vu=role,
            )
            user.set_password("test-password")
            db.session.add(user)
            db.session.add(MemberRecord(user_id=user_id, ngay_gia_nhap=date(2024, 1, 1)))
            db.session.add(UserBan(user_id=user_id, ban_id=1 if user_id % 2 else 2,
                                   is_truong_ban=(role == "TB")))
        db.session.commit()
        self.csrf_token = "two-role-test-csrf"

    def tearDown(self):
        db.session.remove()
        db.engine.dispose()
        self.context.pop()
        self.directory.cleanup()

    def login(self, user_id):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(user_id)
            session["_fresh"] = True
            session["_csrf_token"] = self.csrf_token
        g.pop("_login_user", None)

    @property
    def csrf_headers(self):
        return {"X-CSRF-Token": self.csrf_token}

    def test_all_four_designations_share_global_admin_access(self):
        for user_id, _role in self.ADMIN_ROLES:
            actor = db.session.get(User, user_id)
            self.assertTrue(is_admin(actor))
            self.assertTrue(is_board(actor))
            self.assertTrue(is_treasurer(actor))
            self.assertTrue(can_view_all_members(actor))
            self.assertTrue(can_manage_member(actor, db.session.get(User, 5)))
            self.assertEqual({row.id for row in visible_members(actor)}, set(range(1, 7)))
            self.assertTrue(can_assign_role(actor, db.session.get(User, 5), "PCN", {})[0])

            self.login(user_id)
            self.assertEqual(self.client.get("/admin/roles").status_code, 200)
            response = self.client.get("/api/v1/members")
            self.assertEqual(response.status_code, 200)
            self.assertEqual({row["id"] for row in response.json["items"]}, set(range(1, 7)))

        self.assertFalse(can_assign_role(db.session.get(User, 1), db.session.get(User, 5), "CN", {})[0])

    def test_member_listing_and_member_ids_stay_in_own_scope(self):
        self.login(5)
        response = self.client.get("/api/v1/members")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.json["items"]], [5])
        self.assertEqual(self.client.get("/api/v1/members/6").status_code, 403)
        self.assertEqual(self.client.patch("/api/v1/members/6", json={"name": "Changed"},
                                           headers=self.csrf_headers).status_code, 403)
        self.assertEqual(self.client.post("/api/v1/members/6/archive",
                                          headers=self.csrf_headers).status_code, 403)
        self.assertEqual(self.client.patch("/api/v1/members/5", json={"status": "left"},
                                           headers=self.csrf_headers).status_code, 403)

    def test_role_assignment_has_no_rank_gate_and_cn_uses_the_transfer_workflow(self):
        self.login(4)
        assigned = self.client.post("/admin/roles/5/assign",
                                    data={"chuc_vu": "PCN"},
                                    headers=self.csrf_headers)
        self.assertEqual(assigned.status_code, 302)
        self.assertEqual(db.session.get(User, 5).chuc_vu, "PCN")

        direct_cn = self.client.post("/admin/roles/5/assign",
                                     data={"chuc_vu": "CN"},
                                     headers=self.csrf_headers)
        self.assertEqual(direct_cn.status_code, 302)
        self.assertEqual(db.session.get(User, 5).chuc_vu, "PCN")

        self.login(1)
        handoff = self.client.post("/admin/roles/nhuong-quyen",
                                   data={"target_id": "6"},
                                   headers=self.csrf_headers)
        self.assertEqual(handoff.status_code, 302)
        self.assertEqual(db.session.get(User, 1).chuc_vu, "THANH_VIEN")
        self.assertEqual(db.session.get(User, 6).chuc_vu, "CN")
        self.assertEqual(User.query.filter_by(status="approved", chuc_vu="CN").count(), 1)

    def test_last_active_admin_cannot_be_archived_left_or_downgraded(self):
        for user_id in (2, 3, 4):
            db.session.get(User, user_id).chuc_vu = "THANH_VIEN"
        db.session.commit()
        last_admin = db.session.get(User, 1)
        record = db.session.get(MemberRecord, 1)

        self.assertFalse(set_member_role_safely(last_admin, "THANH_VIEN"))
        db.session.rollback()
        last_admin = db.session.get(User, 1)
        record = db.session.get(MemberRecord, 1)
        self.assertFalse(set_member_left_safely(last_admin, record))
        db.session.rollback()
        self.assertFalse(set_member_left_safely(last_admin, record, datetime.utcnow()))
        db.session.rollback()
        self.assertEqual(db.session.get(User, 1).chuc_vu, "CN")
        self.assertEqual(db.session.get(MemberRecord, 1).tinh_trang, "active")

        self.login(1)
        self.assertEqual(self.client.patch("/api/v1/members/1", json={"status": "left"},
                                           headers=self.csrf_headers).status_code, 403)
        self.assertEqual(self.client.post("/api/v1/members/1/archive",
                                          headers=self.csrf_headers).status_code, 403)

    def test_cancelled_and_ended_events_reject_every_task_mutation(self):
        for index, status in enumerate(("cancelled", "da_ket_thuc"), start=1):
            event_id = 20 + index
            task_id = 30 + index
            start = datetime.utcnow() - timedelta(days=1)
            event = Event(
                id=event_id, ten_su_kien=f"Terminal {status}", ma_su_kien=f"TERM{index}",
                thoi_gian_bat_dau=start, thoi_gian_ket_thuc=start + timedelta(hours=2),
                trang_thai=status, tao_boi_id=1,
            )
            db.session.add(event)
            db.session.add(Task(
                id=task_id, event_id=event_id, ten_task="Terminal task", deadline=start,
                assignee_id=5, ban_id=1, trang_thai="dang_lam",
            ))
        db.session.commit()

        for event_id, task_id in ((21, 31), (22, 32)):
            self.login(3)
            self.assertEqual(self.client.post(f"/event/{event_id}/task/new", headers=self.csrf_headers).status_code, 400)
            self.assertEqual(self.client.post(f"/task/{task_id}/chi-dinh-lai", headers=self.csrf_headers).status_code, 400)
            self.assertEqual(self.client.post(f"/task/{task_id}/cap-nhat-trang-thai",
                                              data={"trang_thai": "huy"},
                                              headers=self.csrf_headers).status_code, 400)
            self.login(5)
            self.assertEqual(self.client.post(f"/task/{task_id}/nop-san-pham",
                                              data={"noi_dung_nop": "submission"},
                                              headers=self.csrf_headers).status_code, 400)

    def test_html_api_and_ctftime_event_creation_are_available_to_all_admin_roles(self):
        starts = datetime.utcnow() + timedelta(days=2)
        ends = starts + timedelta(hours=3)
        for user_id, _role in self.ADMIN_ROLES:
            self.login(user_id)
            html_response = self.client.post("/event/new", data={
                "ma_su_kien": f"HTML{user_id}",
                "ten_su_kien": f"HTML event {user_id}",
                "thoi_gian_bat_dau": starts.strftime("%Y-%m-%dT%H:%M"),
                "thoi_gian_ket_thuc": ends.strftime("%Y-%m-%dT%H:%M"),
            }, headers=self.csrf_headers)
            self.assertEqual(html_response.status_code, 302)
            self.assertIsNotNone(Event.query.filter_by(ma_su_kien=f"HTML{user_id}").first())

            api_response = self.client.post("/api/v1/events", json={
                "name": f"API event {user_id}", "code": f"API{user_id}",
                "start_at": starts.isoformat(), "end_at": ends.isoformat(),
            }, headers=self.csrf_headers)
            self.assertEqual(api_response.status_code, 201, api_response.json)

            source_id = str(1000 + user_id)
            source_event = {
                "start": starts.isoformat(), "finish": ends.isoformat(),
                "title": f"CTF event {user_id}", "location": "Online",
            }
            with patch("app.routes.event.event_by_id",
                       return_value=(source_event, {"stale": False})):
                ctf_response = self.client.post("/event/import/ctftime",
                                                data={"event_id": source_id},
                                                headers=self.csrf_headers)
            self.assertEqual(ctf_response.status_code, 302)
            self.assertIsNotNone(Event.query.filter_by(ma_su_kien=f"CTF-{source_id}").first())


if __name__ == "__main__":
    unittest.main()
