"""Isolated tests for the authenticated CTFtime calendar and FIA import."""

from datetime import date, datetime, timedelta, timezone
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import g

from tests.support import sign_csrf
from app import create_app, db
from app.models import Event, EventDetail, MemberRecord, User
from app.services import ctftime


NOW = datetime(2030, 1, 1, 0, 0, tzinfo=timezone.utc)


def make_ical_event(event_id, *, title="Event", start=None, finish=None, extras=()):
    start = start or NOW + timedelta(days=5)
    finish = finish or start + timedelta(hours=2)
    return "\r\n".join((
        "BEGIN:VEVENT",
        f"SUMMARY:{title}",
        f"DTSTART:{start.strftime('%Y%m%dT%H%M%SZ')}",
        f"DTEND:{finish.strftime('%Y%m%dT%H%M%SZ')}",
        f"URL:https://ctftime.org/event/{event_id}/",
        *extras,
        "END:VEVENT",
    ))


def make_calendar(*events):
    return "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n" + "\r\n".join(events) + "\r\nEND:VCALENDAR\r\n"


def source_event(event_id=71, *, title="Trusted title", start=None, finish=None, location=None):
    start = start or "2030-01-06T00:00:00+00:00"
    finish = finish or "2030-01-06T02:00:00+00:00"
    return {
        "id": event_id,
        "title": title,
        "start": start,
        "finish": finish,
        "ctftime_url": f"https://ctftime.org/event/{event_id}/",
        "location": location,
        "format": None,
        "onsite": None,
        "weight": None,
    }


class CTFtimeParserTests(unittest.TestCase):
    def test_parser_uses_official_source_ids_and_preserves_unknown_location(self):
        event = make_ical_event(
            71,
            title="Pwn Con\\, Summer",
            extras=("DESCRIPTION:Format: Jeopardy\\nOfficial event",),
        )
        result = ctftime.parse_calendar(make_calendar(event), NOW)

        self.assertEqual(len(result["events"]), 1)
        parsed = result["events"][0]
        self.assertEqual(parsed["id"], 71)
        self.assertEqual(parsed["title"], "Pwn Con, Summer")
        self.assertEqual(parsed["format"], "Jeopardy")
        self.assertIsNone(parsed["location"])
        self.assertIsNone(parsed["onsite"])
        self.assertEqual(parsed["ctftime_url"], "https://ctftime.org/event/71/")

    def test_parser_rejects_invalid_source_urls_and_unknown_timezones(self):
        invalid = make_ical_event(72, extras=("URL:https://ctftime.org.attacker.test/event/72/",))
        unknown_tz = "\r\n".join((
            "BEGIN:VEVENT", "SUMMARY:Unknown timezone",
            "DTSTART;TZID=America/Los_Angeles:20300106T000000",
            "DTEND;TZID=America/Los_Angeles:20300106T020000",
            "URL:https://ctftime.org/event/73/", "END:VEVENT",
        ))
        self.assertEqual(ctftime.parse_calendar(make_calendar(invalid, unknown_tz), NOW)["events"], [])

    def test_first_fetch_failure_is_sanitized_and_stale_cache_is_marked(self):
        ctftime._cache = None
        ctftime._cached_at = 0.0
        ctftime._last_attempt = 0.0
        ctftime._last_error = None
        with patch.object(ctftime, "urlopen", side_effect=OSError("secret /private/feed headers")):
            with patch.object(ctftime.time, "monotonic", return_value=100.0):
                with self.assertRaises(ctftime.CalendarUnavailable) as failure:
                    ctftime.calendar_data()
        self.assertNotIn("secret", str(failure.exception))
        self.assertNotIn("/private", str(failure.exception))

        ctftime._cache = {"events": [{"id": 99, "title": "Cached"}], "source": "CTFtime"}
        ctftime._cached_at = 100.0
        ctftime._last_attempt = 0.0
        ctftime._last_error = None
        with patch.object(ctftime, "urlopen", side_effect=OSError("secret upstream response")):
            with patch.object(ctftime.time, "monotonic", return_value=700.0):
                result = ctftime.calendar_data()
        self.assertTrue(result["cached"])
        self.assertTrue(result["stale"])
        self.assertIn("Cached", result["events"][0]["title"])
        self.assertNotIn("secret", result["error"])


class CTFtimeRouteTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        database_path = Path(self.directory.name) / "ctftime-test.db"
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}",
            "SECRET_KEY": "test-only-key",
            "APP_TIMEZONE": "Asia/Bangkok",
        })
        self.client = self.app.test_client()
        self.context = self.app.app_context()
        self.context.push()
        for user_id, role, status in (
            (1, "CN", "approved"),
            (2, "THANH_VIEN", "approved"),
            (3, "CN", "pending"),
        ):
            user = User(
                id=user_id, mssv=f"SV{user_id}", ho_ten=f"Member {user_id}",
                ngay_sinh=date(2000, 1, 1), sdt="0900000000",
                email=f"member{user_id}@example.test", status=status, chuc_vu=role,
            )
            user.set_password("test-password")
            db.session.add(user)
            db.session.add(MemberRecord(user_id=user_id, ngay_gia_nhap=date(2024, 1, 1)))
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        self.context.pop()
        self.directory.cleanup()

    def login(self, user_id, *, csrf="test-csrf"):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(user_id)
            session["_fresh"] = True
            session["csrf_token"] = csrf   # token gốc; form gửi bản đã ký
        g.pop("_login_user", None)

    def import_data(self, event_id="71", csrf="test-csrf", **extra):
        return {"csrf_token": sign_csrf(self.app, csrf), "event_id": event_id, **extra}

    def test_calendar_is_lazy_and_available_to_approved_members(self):
        self.login(2)
        with patch("app.routes.event.calendar_data", return_value={"events": [], "source": "CTFtime"}) as feed:
            page = self.client.get("/event")
            feed.assert_not_called()
            self.assertIn(b"S\xe1\xbb\xb1 ki\xe1\xbb\x87n FIA", page.data)
            self.assertIn(b"CTFtime", page.data)
            response = self.client.get("/api/ctftime/events")
            feed.assert_called_once()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "private, no-store")

    def test_routes_require_login_and_approval_and_import_is_board_only(self):
        self.assertEqual(self.client.get("/api/ctftime/events").status_code, 302)
        self.login(3)
        self.assertEqual(self.client.get("/api/ctftime/events").status_code, 403)
        self.login(2)
        with patch("app.routes.event.event_by_id") as lookup:
            response = self.client.post("/event/import/ctftime", data=self.import_data())
        self.assertEqual(response.status_code, 403)
        lookup.assert_not_called()

    def test_import_requires_csrf_before_looking_up_the_submitted_id(self):
        self.login(1)
        with patch("app.routes.event.event_by_id") as lookup:
            response = self.client.post("/event/import/ctftime", data={"event_id": "71"})
        self.assertEqual(response.status_code, 400)
        lookup.assert_not_called()

    def test_import_uses_server_record_converts_utc_and_allows_ongoing_event(self):
        self.login(1)
        ongoing = source_event(
            title="Trusted <script>alert(1)</script>",
            start="2030-01-01T03:00:00+00:00",
            finish="2030-01-01T05:00:00+00:00",
        )
        feed = {"events": [ongoing], "stale": False}
        with patch("app.routes.event.event_by_id", return_value=(ongoing, feed)) as lookup:
            with patch("app.routes.event.club_now", return_value=datetime(2030, 1, 1, 10, 30)):
                response = self.client.post("/event/import/ctftime", data=self.import_data(
                    title="Attacker title", start="1999-01-01T00:00", finish="1999-01-01T00:01",
                ), follow_redirects=True)
        lookup.assert_called_once_with("71")
        event = Event.query.one()
        detail = db.session.get(EventDetail, event.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request.path, "/event")
        self.assertIn("Đã tạo sự kiện FIA từ CTFtime.".encode(), response.data)
        self.assertEqual(event.ten_su_kien, "FIA tham gia Trusted <script>alert(1)</script>")
        self.assertEqual(event.ma_su_kien, "CTF-71")
        self.assertEqual(event.thoi_gian_bat_dau, datetime(2030, 1, 1, 10, 0))
        self.assertEqual(event.thoi_gian_ket_thuc, datetime(2030, 1, 1, 12, 0))
        self.assertEqual(event.trang_thai, "dang_dien_ra")
        self.assertEqual(detail.dia_diem, "")
        self.assertEqual(
            detail.noi_dung,
            "FIA tham gia cuộc thi này, không phải đơn vị tổ chức.\nNguồn: https://ctftime.org/event/71/",
        )

        detail_page = self.client.get(f"/event/{event.id}")
        self.assertIn("FIA tham gia cuộc thi này, không phải đơn vị tổ chức.".encode(), detail_page.data)
        self.assertIn(b"Ngu\xe1\xbb\x93n: https://ctftime.org/event/71/", detail_page.data)
        self.assertNotIn(b"<script>alert(1)</script>", detail_page.data)

    def test_duplicate_import_is_idempotent_without_another_feed_lookup(self):
        self.login(1)
        existing = Event(
            ten_su_kien="Previously imported", ma_su_kien="CTF-71",
            thoi_gian_bat_dau=datetime(2030, 1, 6, 7),
            thoi_gian_ket_thuc=datetime(2030, 1, 6, 9),
            tao_boi_id=1,
        )
        db.session.add(existing)
        db.session.commit()

        with patch("app.routes.event.event_by_id") as lookup:
            response = self.client.post("/event/import/ctftime", data=self.import_data())

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/event")
        self.assertEqual(Event.query.filter_by(ma_su_kien="CTF-71").count(), 1)
        lookup.assert_not_called()

    def test_first_feed_failure_returns_safe_get_error_and_safe_import_flash(self):
        self.login(1)
        ctftime._cache = None
        ctftime._cached_at = 0.0
        ctftime._last_attempt = 0.0
        ctftime._last_error = None
        with patch.object(ctftime, "urlopen", side_effect=OSError("secret upstream /private/feed")):
            with patch.object(ctftime.time, "monotonic", return_value=100.0):
                response = self.client.get("/api/ctftime/events")
            self.assertEqual(response.status_code, 503)
            self.assertNotIn(b"secret", response.data)
            self.assertNotIn(b"/private", response.data)

            failed_import = self.client.post("/event/import/ctftime", data=self.import_data(), follow_redirects=True)
        self.assertEqual(failed_import.status_code, 200)
        self.assertIn("Chưa thể xác minh sự kiện với lịch CTFtime".encode(), failed_import.data)
        self.assertNotIn(b"secret", failed_import.data)
        self.assertEqual(Event.query.count(), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
