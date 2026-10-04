import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from cb3_scraper import parse_meetings  # noqa: E402

HTML = (pathlib.Path(__file__).parent / "fixtures" / "calendar.html").read_text(encoding="utf8", errors="replace")


def test_parses_all_meetings():
    ms = parse_meetings(HTML)
    assert len(ms) == 7
    first = ms[0]
    assert first.start.isoformat() == "2026-10-08T18:30:00"
    assert first.location.startswith("Community Board 3 Office - 59 East 4th Street")
    assert "zoomgov.com/j/1606458293" in first.description


def test_second_date_format():
    full = parse_meetings(HTML)[-1]
    assert full.title.startswith("Community Board 3, Full Board")
    assert full.start.isoformat() == "2026-10-27T18:30:00"
    assert full.location.startswith("PS 20")


def test_malformed_block_skipped():
    bad = "<h2>Calendar of Meetings - October 2026</h2><h3>X</h3><p>TBD</p>"
    assert parse_meetings(bad) == []
