import pathlib
import sys
from datetime import datetime, timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import gcal_sync  # noqa: E402
from cb3_scraper import Meeting  # noqa: E402


def meeting(title, start):
    return Meeting(title, start, start + timedelta(hours=2), "Somewhere", f"{title}\nSource")


class FakeService:
    """Minimal stand-in for the Calendar API client, backed by a list of events."""

    def __init__(self, events=()):
        self.events_ = list(events)
        self.inserted, self.deleted, self.updated = [], [], []

    def events(self):
        return self

    def list(self, calendarId, timeMin, **kw):
        self.time_min = timeMin
        return _Call({"items": list(self.events_)})

    def insert(self, calendarId, body):
        ev = dict(body, id=f"new{len(self.inserted)}", created=f"2026-10-25T00:00:0{len(self.inserted)}Z")
        ev["end"] = body["end"]
        self.inserted.append(ev)
        self.events_.append(ev)
        return _Call(ev)

    def update(self, calendarId, eventId, body):
        self.updated.append(eventId)
        return _Call({})

    def delete(self, calendarId, eventId):
        self.deleted.append(eventId)
        self.events_ = [e for e in self.events_ if e["id"] != eventId]
        return _Call({})


class _Call:
    def __init__(self, result):
        self.result = result

    def execute(self):
        return self.result


def stored(m, event_id, created="2026-10-01T00:00:00Z"):
    """An event as the API would return it after we inserted `m`."""
    body = gcal_sync._body(m)
    return dict(body, id=event_id, created=created)


PAST = meeting("SLA Committee", datetime(2020, 1, 1, 18, 30))  # long over
FUTURE = meeting("Full Board", datetime(2099, 1, 1, 18, 30))


def run(svc, meetings, **kw):
    return gcal_sync.sync(svc, "cal", meetings, **kw)


def test_past_meeting_already_on_calendar_is_not_recreated():
    svc = FakeService([stored(PAST, "a")])
    counts = run(svc, [PAST])
    assert counts["created"] == 0 and counts["unchanged"] == 1
    assert svc.inserted == []


def test_lookup_window_starts_at_earliest_meeting_not_now():
    svc = FakeService()
    run(svc, [PAST, FUTURE])
    assert svc.time_min.startswith("2019-12-31")


def test_second_run_after_creating_is_idempotent():
    svc = FakeService()
    assert run(svc, [PAST, FUTURE])["created"] == 2
    again = run(svc, [PAST, FUTURE])
    assert again["created"] == 0 and again["unchanged"] == 2


def test_existing_duplicates_are_removed_keeping_oldest():
    svc = FakeService([
        stored(PAST, "newer", created="2026-10-03T00:00:00Z"),
        stored(PAST, "oldest", created="2026-10-01T00:00:00Z"),
        stored(PAST, "middle", created="2026-10-02T00:00:00Z"),
    ])
    counts = run(svc, [PAST])
    assert counts["deduped"] == 2 and counts["created"] == 0
    assert sorted(svc.deleted) == ["middle", "newer"]
    assert [e["id"] for e in svc.events_] == ["oldest"]


def test_dry_run_changes_nothing():
    svc = FakeService([stored(PAST, "a"), stored(PAST, "b", created="2026-10-02T00:00:00Z")])
    counts = run(svc, [PAST, FUTURE], dry_run=True)
    assert counts["deduped"] == 1 and counts["created"] == 1
    assert svc.deleted == [] and svc.inserted == []


def test_removed_upcoming_meeting_is_deleted_but_past_one_is_kept():
    gone_future = meeting("Cancelled", datetime(2099, 2, 1, 18, 30))
    gone_past = meeting("Old", datetime(2020, 2, 1, 18, 30))
    svc = FakeService([stored(gone_future, "f"), stored(gone_past, "p"), stored(FUTURE, "x")])
    counts = run(svc, [PAST, FUTURE])
    assert svc.deleted == ["f"]
    assert counts["deleted"] == 1


def test_changed_meeting_is_updated():
    svc = FakeService([stored(meeting("Full Board", FUTURE.start), "x")])
    changed = Meeting(FUTURE.title, FUTURE.start, FUTURE.end, "New place", "different")
    assert run(svc, [changed])["updated"] == 1 and svc.updated == ["x"]


def test_no_meetings_does_nothing():
    svc = FakeService([stored(PAST, "a")])
    assert run(svc, [])["deleted"] == 0 and svc.deleted == []
