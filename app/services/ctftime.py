"""Bounded, read-only access to CTFtime's public calendar feed."""

from datetime import datetime, timedelta, timezone
from threading import Lock
import re
import time
from urllib.request import Request, urlopen


SOURCE_URL = "https://ctftime.org/calendar/"
FEED_URL = "https://calendar.google.com/calendar/ical/ctftime%40gmail.com/public/basic.ics"
MAX_BYTES = 3_000_000
CACHE_SECONDS = 600
STALE_SECONDS = 86_400
RETRY_SECONDS = 30
FETCH_TIMEOUT_SECONDS = 15

_lock = Lock()
_cache = None
_cached_at = 0.0
_last_attempt = 0.0
_last_error = None


class CalendarUnavailable(Exception):
    """Raised when no usable public calendar data is available."""


def _text(value):
    """Giải mã ký tự escape trong iCalendar (\\n, \\, \\; …)."""
    return re.sub(r"\\([nN,;\\])", lambda match: "\n" if match[1].lower() == "n" else match[1], value)


def _timestamp(value):
    """Parse only UTC iCalendar timestamps; do not guess source timezones."""
    try:
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def parse_calendar(raw, now=None):
    """Parse the public iCalendar feed using the preview's bounded rules."""
    if not isinstance(raw, str) or not raw.startswith("BEGIN:VCALENDAR") or "END:VCALENDAR" not in raw:
        raise CalendarUnavailable("Invalid calendar")

    now = now or datetime.now(timezone.utc)
    finish_window = now + timedelta(days=90)
    lines = re.sub(r"\r?\n[ \t]", "", raw).splitlines()
    rows, current = [], None
    for line in lines:
        if line == "BEGIN:VEVENT":
            current = {}
        elif line == "END:VEVENT":
            if current is not None:
                rows.append(current)
            current = None
        elif current is not None and ":" in line:
            name, value = line.split(":", 1)
            current[name] = value

    events, seen = [], set()
    for row in rows:
        if row.get("STATUS", "").upper() == "CANCELLED":
            continue
        start, end = _timestamp(row.get("DTSTART")), _timestamp(row.get("DTEND"))
        if not start or not end or end <= start or end < now or start > finish_window:
            continue

        description = _text(row.get("DESCRIPTION", ""))
        source = re.search(r"https://ctftime\.org/event/([1-9]\d{0,11})/?(?:\s|$)", description)
        if source is None:
            source = re.fullmatch(r"https://ctftime\.org/event/([1-9]\d{0,11})/?", row.get("URL", ""))
        if source is None:
            continue

        event_id = int(source[1])
        if event_id in seen:
            continue
        title = _text(row.get("SUMMARY", "")).strip()[:240]
        if not title:
            continue
        seen.add(event_id)
        fmt = re.search(r"^Format:\s*(.+)$", description, re.M)
        events.append({
            "id": event_id,
            "title": title,
            "start": start.isoformat(),
            "finish": end.isoformat(),
            "ctftime_url": f"https://ctftime.org/event/{event_id}/",
            "url": None,
            "format": fmt[1].strip()[:100] if fmt else None,
            # The public calendar does not provide these fields reliably.
            "onsite": None,
            "weight": None,
            "location": _text(row.get("LOCATION", "")).strip()[:200] or None,
        })

    events.sort(key=lambda event: (event["start"], event["id"]))
    return {
        "events": events[:100],
        "source": "CTFtime",
        "source_url": SOURCE_URL,
        "fetched_at": now.isoformat(),
        "window": {"start": now.isoformat(), "finish": finish_window.isoformat()},
        "limited": len(events) > 100,
    }


def calendar_data():
    """Return fresh or honest stale cache data, with a bounded public fetch."""
    global _cache, _cached_at, _last_attempt, _last_error
    with _lock:
        clock = time.monotonic()
        if _cache is not None and clock - _cached_at < CACHE_SECONDS:
            return {**_cache, "cached": True, "stale": False}

        if _last_attempt and clock - _last_attempt < RETRY_SECONDS and _last_error:
            if _cache is not None and clock - _cached_at <= STALE_SECONDS:
                return {**_cache, "cached": True, "stale": True, "error": _last_error}
            raise CalendarUnavailable(_last_error)

        _last_attempt = clock
        try:
            request = Request(FEED_URL, headers={
                "User-Agent": "FIA-PublicCalendar/1.0",
                "Accept": "text/calendar",
            })
            with urlopen(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
                raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise CalendarUnavailable("Feed too large")

            fetched_at = datetime.now(timezone.utc)
            _cache = parse_calendar(raw.decode("utf-8-sig"), fetched_at)
            _cached_at = time.monotonic()
            _last_error = None
            return {**_cache, "cached": False, "stale": False}
        except Exception:
            # Do not expose upstream response bodies, local paths, or headers.
            _last_error = "Không cập nhật được lịch CTFtime. Hãy thử lại sau."
            if _cache is not None and clock - _cached_at <= STALE_SECONDS:
                return {**_cache, "cached": True, "stale": True, "error": _last_error}
            raise CalendarUnavailable(_last_error) from None


def event_by_id(event_id):
    """Look up an importable event from parsed server-side calendar data."""
    if not re.fullmatch(r"[1-9]\d{0,11}", str(event_id or "")):
        return None, None
    data = calendar_data()
    event_id = int(event_id)
    event = next((item for item in data["events"] if item["id"] == event_id), None)
    return event, data
