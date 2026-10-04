"""Scrape the Manhattan CB3 meeting calendar page into Meeting objects."""
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

URL = "https://www.nyc.gov/site/manhattancb3/calendar/calendar.page"
DEFAULT_DURATION = timedelta(hours=2)  # page gives no end time

log = logging.getLogger(__name__)

# "Thursday, October 8 at 6:30pm -- ..." and "Tuesday, October 27, 2026 - 6:30pm"
DATE_RE = re.compile(
    r"(?P<weekday>Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s*"
    r"(?P<month>[A-Z][a-z]+)\s+(?P<day>\d{1,2})(?:,\s*(?P<year>\d{4}))?"
    r"\s*(?:at|-|–)\s*(?P<time>\d{1,2}(?::\d{2})?\s*[ap]m)",
    re.I,
)
HEADER_YEAR_RE = re.compile(r"\b(20\d{2})\b")


@dataclass
class Meeting:
    title: str
    start: datetime
    end: datetime
    location: str
    description: str


def _parse_start(m, default_year):
    year = int(m.group("year") or default_year)
    time = m.group("time").replace(" ", "").upper()
    fmt = "%I:%M%p" if ":" in time else "%I%p"
    text = f"{m.group('month')} {m.group('day')} {year} {time}"
    return datetime.strptime(text, "%B %d %Y " + fmt)


def parse_meetings(html, today=None):
    today = today or datetime.now()
    soup = BeautifulSoup(html, "html.parser")
    h2 = soup.find("h2", string=re.compile("Calendar of Meetings"))
    ym = HEADER_YEAR_RE.search(h2.get_text()) if h2 else None
    default_year = int(ym.group(1)) if ym else today.year

    meetings = []
    for h3 in soup.find_all("h3"):
        title = h3.get_text(" ", strip=True)
        # Collect siblings up to the next h3.
        block = []
        for sib in h3.find_next_siblings():
            if sib.name == "h3":
                break
            block.append(sib)
        first_p = next((p for p in block if p.name == "p"), None)
        if not first_p:
            continue
        lines = [l.strip() for l in first_p.get_text("\n").replace("\xa0", " ").split("\n") if l.strip()]
        first = lines[0] if lines else ""
        m = DATE_RE.search(first)
        if not m:
            log.warning("Skipping %r: no parseable date in %r", title, first)
            continue
        try:
            start = _parse_start(m, default_year)
        except ValueError:
            log.warning("Skipping %r: bad date %r", title, first)
            continue

        rest = first[m.end():].strip()
        rest = re.sub(r"^(--|-|–)\s*", "", rest)
        if rest:
            location, details = rest, lines[1:]
        else:  # location on the next line
            location, details = (lines[1] if len(lines) > 1 else ""), lines[2:]

        desc = [title, ""] + details
        for p in block:
            if p is not first_p and p.name == "p":
                desc.append(p.get_text(" ", strip=True))
        for ol in (b for b in block if b.name == "ol"):
            desc.extend(f"- {li.get_text(' ', strip=True)}" for li in ol.find_all("li"))
        desc += ["", f"Source: {URL}"]
        meetings.append(Meeting(title, start, start + DEFAULT_DURATION, location, "\n".join(desc)))
    return meetings


def fetch_meetings():
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0 (CB3 calendar sync)"}, timeout=30)
    resp.raise_for_status()
    return parse_meetings(resp.text)
