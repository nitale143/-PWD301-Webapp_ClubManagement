"""Local static preview plus a bounded, read-only public calendar adapter.

Not a Flask replacement or an authentication server. No club database access.
The upstream calendar is the public Google calendar embedded at ctftime.org/calendar/.
Confirm reuse terms before publishing this feature beyond the local preview.
"""
import argparse
from datetime import datetime, timedelta, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import re
from pathlib import Path
import threading
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

SOURCE_URL = 'https://ctftime.org/calendar/'
FEED_URL = 'https://calendar.google.com/calendar/ical/ctftime%40gmail.com/public/basic.ics'
MAX_BYTES = 3_000_000
CACHE_SECONDS = 600
_lock = threading.Lock()
_cache = None
_cached_at = 0.0
_last_attempt = 0.0
_last_error = None


class CalendarUnavailable(Exception):
    pass


def _text(value):
    return re.sub(r'\\([nN,;\\])', lambda m: '\n' if m[1].lower() == 'n' else m[1], value)


def _timestamp(value):
    # Only UTC timestamps from this known source are supported; do not guess TZIDs.
    try:
        return datetime.strptime(value, '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def parse_calendar(raw, now):
    if not raw.startswith('BEGIN:VCALENDAR') or 'END:VCALENDAR' not in raw:
        raise CalendarUnavailable('Invalid calendar')
    finish_window = now + timedelta(days=90)
    lines = re.sub(r'\r?\n[ \t]', '', raw).splitlines()
    rows, current = [], None
    for line in lines:
        if line == 'BEGIN:VEVENT':
            current = {}
        elif line == 'END:VEVENT':
            if current is not None:
                rows.append(current)
            current = None
        elif current is not None and ':' in line:
            name, value = line.split(':', 1)
            current[name] = value
    events, seen = [], set()
    for row in rows:
        if row.get('STATUS', '').upper() == 'CANCELLED':
            continue
        start, end = _timestamp(row.get('DTSTART')), _timestamp(row.get('DTEND'))
        if not start or not end or end <= start or end < now or start > finish_window:
            continue
        description = _text(row.get('DESCRIPTION', ''))
        source = re.search(r'https://ctftime\.org/event/([1-9]\d{0,11})/?(?:\s|$)', description)
        if source is None:
            source = re.fullmatch(r'https://ctftime\.org/event/([1-9]\d{0,11})/?', row.get('URL', ''))
        if not source:
            continue
        event_id = int(source[1])
        if event_id in seen:
            continue
        seen.add(event_id)
        title = _text(row.get('SUMMARY', '')).strip()[:240]
        if not title:
            continue
        fmt = re.search(r'^Format:\s*(.+)$', description, re.M)
        events.append({
            'id': event_id, 'title': title,
            'start': start.isoformat(), 'finish': end.isoformat(),
            'ctftime_url': f'https://ctftime.org/event/{event_id}/',
            'url': None, 'format': fmt[1].strip()[:100] if fmt else None,
            'onsite': None, 'weight': None,
            'location': _text(row.get('LOCATION', '')).strip()[:200] or None,
        })
    events.sort(key=lambda row: (row['start'], row['id']))
    return {'events': events[:100], 'source': 'CTFtime', 'source_url': SOURCE_URL,
            'fetched_at': now.isoformat(),
            'window': {'start': now.isoformat(), 'finish': finish_window.isoformat()},
            'limited': len(events) > 100}


def calendar_data():
    global _cache, _cached_at, _last_attempt, _last_error
    with _lock:
        clock = time.monotonic()
        if _cache is not None and clock - _cached_at < CACHE_SECONDS:
            return {**_cache, 'cached': True, 'stale': False}
        # Avoid hammering the public source when it is unavailable.
        if _last_attempt and clock - _last_attempt < 30 and _last_error:
            if _cache is not None and clock - _cached_at <= 86400:
                return {**_cache, 'cached': True, 'stale': True, 'error': _last_error}
            raise CalendarUnavailable(_last_error)
        _last_attempt = clock
        try:
            request = Request(FEED_URL, headers={
                'User-Agent': 'FIA-LocalCalendarPreview/1.0', 'Accept': 'text/calendar'})
            with urlopen(request, timeout=15) as response:
                raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise CalendarUnavailable('Feed too large')
            now = datetime.now(timezone.utc)
            _cache = parse_calendar(raw.decode('utf-8-sig'), now)
            _cached_at = time.monotonic()
            _last_error = None
            return {**_cache, 'cached': False, 'stale': False}
        except Exception:
            # Never expose upstream exception bodies, local paths, or request headers.
            _last_error = 'Không cập nhật được lịch CTFtime. Hãy thử lại sau.'
            if _cache is not None and clock - _cached_at <= 86400:
                return {**_cache, 'cached': True, 'stale': True, 'error': _last_error}
            raise CalendarUnavailable(_last_error) from None


class PreviewHandler(SimpleHTTPRequestHandler):
    def _json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/ctftime/events':
            try:
                self._json(200, calendar_data())
            except CalendarUnavailable as exc:
                self._json(503, {'error': str(exc), 'source_url': SOURCE_URL})
            return
        if path.startswith('/api/'):
            self._json(404, {'error': 'Không có endpoint này trong preview.'})
            return
        super().do_GET()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5082)
    args = parser.parse_args()
    root = str(Path(__file__).resolve().parent)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(PreviewHandler, directory=root))
    print(f'FIA preview: http://127.0.0.1:{args.port}/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
