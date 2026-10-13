"""Deterministic tests for the local CTFtime public-calendar adapter."""
import json
from datetime import datetime, timedelta, timezone
from functools import partial
from http.server import ThreadingHTTPServer
from threading import Thread
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import urlopen as http_urlopen

import preview_server


NOW = datetime(2026, 10, 13, 0, 0, tzinfo=timezone.utc)


def make_event(event_id, *properties):
    return "\r\n".join((
        "BEGIN:VEVENT",
        f"UID:ctftime-{event_id}",
        f"SUMMARY:Event {event_id}",
        f"DTSTART:{(NOW + timedelta(days=10)).strftime('%Y%m%dT%H%M%SZ')}",
        f"DTEND:{(NOW + timedelta(days=10, hours=2)).strftime('%Y%m%dT%H%M%SZ')}",
        f"URL:https://ctftime.org/event/{event_id}/",
        *properties,
        "END:VEVENT",
    ))


def calendar(*events):
    return "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n" + "\r\n".join(events) + "\r\nEND:VCALENDAR\r\n"


class CalendarParserTests(unittest.TestCase):
    def test_utc_window_boundaries_and_sort_order(self):
        at_now = make_event(
            2,
            f"DTSTART:{NOW.strftime('%Y%m%dT%H%M%SZ')}",
            f"DTEND:{(NOW + timedelta(hours=1)).strftime('%Y%m%dT%H%M%SZ')}",
        )
        at_finish = make_event(
            3,
            f"DTSTART:{(NOW + timedelta(days=90)).strftime('%Y%m%dT%H%M%SZ')}",
            f"DTEND:{(NOW + timedelta(days=90, hours=1)).strftime('%Y%m%dT%H%M%SZ')}",
        )
        after_finish = make_event(
            4,
            f"DTSTART:{(NOW + timedelta(days=90, seconds=1)).strftime('%Y%m%dT%H%M%SZ')}",
        )
        before_now = make_event(
            5,
            f"DTSTART:{(NOW - timedelta(hours=3)).strftime('%Y%m%dT%H%M%SZ')}",
            f"DTEND:{(NOW - timedelta(hours=1)).strftime('%Y%m%dT%H%M%SZ')}",
        )
        result = preview_server.parse_calendar(calendar(at_finish, after_finish, before_now, at_now), NOW)

        self.assertEqual([event['id'] for event in result['events']], [2, 3])
        self.assertEqual(result['events'][0]['start'], NOW.isoformat())
        self.assertEqual(result['events'][1]['start'], (NOW + timedelta(days=90)).isoformat())
        self.assertEqual(result['window']['finish'], (NOW + timedelta(days=90)).isoformat())
        self.assertEqual(result['limited'], False)

    def test_unfolded_lines_and_escaped_ics_text(self):
        raw_event = "\r\n".join((
            "BEGIN:VEVENT",
            "SUMMARY:Pwn ",
            " Con Cup\\, Summer\\; Edition",
            f"DTSTART:{(NOW + timedelta(days=2)).strftime('%Y%m%dT%H%M%SZ')}",
            f"DTEND:{(NOW + timedelta(days=2, hours=2)).strftime('%Y%m%dT%H%M%SZ')}",
            "DESCRIPTION:Format: Jeopardy\\nOfficial\\, friendly\\; team\\\\ event",
            "URL:https://ctftime.org/event/77/",
            "LOCATION:Room\\, B\\; floor 2",
            "END:VEVENT",
        ))
        event = preview_server.parse_calendar(calendar(raw_event), NOW)['events'][0]

        self.assertEqual(event['title'], 'Pwn Con Cup, Summer; Edition')
        self.assertEqual(event['format'], 'Jeopardy')
        self.assertEqual(event['location'], 'Room, B; floor 2')

    def test_cancelled_missing_datetime_and_unknown_tzid_are_skipped(self):
        cancelled = make_event(10, "STATUS:CANCELLED")
        missing_start = "\r\n".join((
            "BEGIN:VEVENT", "SUMMARY:No start", "DTEND:20261014T000000Z",
            "URL:https://ctftime.org/event/11/", "END:VEVENT",
        ))
        missing_end = "\r\n".join((
            "BEGIN:VEVENT", "SUMMARY:No finish", "DTSTART:20261014T000000Z",
            "URL:https://ctftime.org/event/12/", "END:VEVENT",
        ))
        unknown_tzid = "\r\n".join((
            "BEGIN:VEVENT", "SUMMARY:Unknown timezone",
            "DTSTART;TZID=America/Los_Angeles:20261014T000000",
            "DTEND;TZID=America/Los_Angeles:20261014T020000",
            "URL:https://ctftime.org/event/13/", "END:VEVENT",
        ))
        result = preview_server.parse_calendar(calendar(cancelled, missing_start, missing_end, unknown_tzid), NOW)

        self.assertEqual(result['events'], [])

    def test_rejects_malformed_calendar_and_nonofficial_source_urls(self):
        with self.assertRaises(preview_server.CalendarUnavailable):
            preview_server.parse_calendar("BEGIN:VEVENT\nEND:VEVENT", NOW)

        lookalike_host = make_event(21, "URL:https://ctftime.org.attacker.test/event/21/")
        wrong_path = make_event(22, "URL:https://ctftime.org/events/22/")
        description_suffix = make_event(
            23,
            "DESCRIPTION:Details https://ctftime.org/event/23.evil.test",
            "URL:https://attacker.test/event/23/",
        )
        credentials = make_event(24, "URL:https://attacker.test@ctftime.org/event/24/")
        valid = make_event(25, "URL:https://ctftime.org/event/25/")
        result = preview_server.parse_calendar(
            calendar(lookalike_host, wrong_path, description_suffix, credentials, valid), NOW)

        self.assertEqual([event['id'] for event in result['events']], [25])
        self.assertEqual(result['events'][0]['ctftime_url'], 'https://ctftime.org/event/25/')

    def test_deduplicates_by_ctftime_id_and_keeps_earliest_feed_entry(self):
        first = make_event(31, "SUMMARY:First copy")
        second = make_event(31, "SUMMARY:Second copy")
        result = preview_server.parse_calendar(calendar(first, second), NOW)

        self.assertEqual(len(result['events']), 1)
        self.assertEqual(result['events'][0]['title'], 'First copy')

    def test_caps_response_at_100_and_marks_it_limited(self):
        entries = [make_event(event_id) for event_id in range(1, 102)]
        result = preview_server.parse_calendar(calendar(*entries), NOW)

        self.assertEqual(len(result['events']), 100)
        self.assertEqual(result['events'][0]['id'], 1)
        self.assertEqual(result['events'][-1]['id'], 100)
        self.assertTrue(result['limited'])


class CalendarAdapterTests(unittest.TestCase):
    def setUp(self):
        preview_server._cache = None
        preview_server._cached_at = 0.0
        preview_server._last_attempt = 0.0
        preview_server._last_error = None

    def tearDown(self):
        preview_server._cache = None
        preview_server._cached_at = 0.0
        preview_server._last_attempt = 0.0
        preview_server._last_error = None

    def test_network_failure_is_sanitized_and_stale_cache_is_served(self):
        with patch.object(preview_server, 'urlopen', side_effect=OSError('secret token /private/feed.ics')):
            with self.assertRaises(preview_server.CalendarUnavailable) as failure:
                with patch.object(preview_server.time, 'monotonic', return_value=200.0):
                    preview_server.calendar_data()
            self.assertNotIn('secret', str(failure.exception))
            self.assertNotIn('/private', str(failure.exception))

        cached = {'events': [{'id': 99, 'title': 'Cached'}], 'source': 'CTFtime'}
        preview_server._cache = cached
        preview_server._cached_at = 200.0
        preview_server._last_attempt = 0.0
        preview_server._last_error = None
        with patch.object(preview_server, 'urlopen', side_effect=OSError('private headers')) as opener:
            with patch.object(preview_server.time, 'monotonic', return_value=820.0):
                result = preview_server.calendar_data()

        opener.assert_called_once()
        self.assertEqual(result['events'], cached['events'])
        self.assertTrue(result['cached'])
        self.assertTrue(result['stale'])
        self.assertNotIn('private', result['error'])

    def test_recent_failure_suppresses_repeat_network_attempts(self):
        preview_server._last_attempt = 300.0
        preview_server._last_error = 'safe cached error'
        with patch.object(preview_server, 'urlopen') as opener:
            with patch.object(preview_server.time, 'monotonic', return_value=310.0):
                with self.assertRaises(preview_server.CalendarUnavailable):
                    preview_server.calendar_data()

        opener.assert_not_called()

    def test_local_http_endpoint_returns_sanitized_503_when_feed_fails(self):
        server = ThreadingHTTPServer(
            ('127.0.0.1', 0), partial(preview_server.PreviewHandler, directory='.'))
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch.object(preview_server, 'urlopen', side_effect=OSError('secret upstream body')):
                with patch.object(preview_server.time, 'monotonic', return_value=400.0):
                    try:
                        response = http_urlopen(f'http://127.0.0.1:{server.server_port}/api/ctftime/events')
                    except HTTPError as error:
                        response = error
                    with response:
                        payload = json.loads(response.read())
                        self.assertEqual(response.status, 503)
                        self.assertEqual(response.headers['Cache-Control'], 'no-store')
            self.assertEqual(payload['source_url'], preview_server.SOURCE_URL)
            self.assertNotIn('secret upstream body', json.dumps(payload))
            self.assertNotIn('private', json.dumps(payload))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
