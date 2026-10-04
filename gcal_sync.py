"""Google Calendar side of the CB3 sync: auth, calendar lookup, upsert/delete, public sharing."""
import hashlib
import json
import logging
import pathlib
from datetime import datetime, timezone
from urllib.parse import quote

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_NAME = "Manhattan CB3"
TZ = "America/New_York"
ROOT = pathlib.Path(__file__).parent
CONFIG = ROOT / "config.json"

log = logging.getLogger(__name__)


def get_service():
    token, creds_file = ROOT / "token.json", ROOT / "credentials.json"
    creds = Credentials.from_authorized_user_file(token, SCOPES) if token.exists() else None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES).run_local_server(port=0)
        token.write_text(creds.to_json())
    return build("calendar", "v3", credentials=creds)


def get_calendar_id(service, create=True):
    cfg = json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
    cal_id = cfg.get("calendar_id")
    if cal_id:
        try:
            service.calendars().get(calendarId=cal_id).execute()
            return cal_id
        except Exception:
            log.warning("Saved calendar %s not found; looking up by name", cal_id)
    for item in service.calendarList().list().execute().get("items", []):
        if item.get("summary") == CALENDAR_NAME and item.get("accessRole") == "owner":
            cal_id = item["id"]
            break
    else:
        if not create:
            return None
        cal_id = service.calendars().insert(body={"summary": CALENDAR_NAME, "timeZone": TZ}).execute()["id"]
        log.info("Created calendar %r", CALENDAR_NAME)
    CONFIG.write_text(json.dumps({"calendar_id": cal_id}))
    return cal_id


def set_public(service, cal_id, public):
    rules = service.acl().list(calendarId=cal_id).execute().get("items", [])
    existing = next((r for r in rules if r["scope"]["type"] == "default"), None)
    if public and not existing:
        service.acl().insert(calendarId=cal_id, body={"role": "reader", "scope": {"type": "default"}}).execute()
        log.info("Calendar is now public (read-only)")
    elif not public and existing:
        service.acl().delete(calendarId=cal_id, ruleId=existing["id"]).execute()
        log.info("Calendar is now private")


def share_links(cal_id):
    q = quote(cal_id)
    return {
        "ical_feed": f"https://calendar.google.com/calendar/ical/{q}/public/basic.ics",
        "web_view": f"https://calendar.google.com/calendar/embed?src={q}",
        "add_to_google": f"https://calendar.google.com/calendar/r?cid={q}",
    }


def _key(m):
    return hashlib.sha1(f"{m.title}|{m.start.date()}".encode()).hexdigest()


def _hash(m):
    return hashlib.sha1(
        f"{m.title}|{m.start.isoformat()}|{m.end.isoformat()}|{m.location}|{m.description}".encode()
    ).hexdigest()


def _body(m):
    return {
        "summary": m.title,
        "location": m.location,
        "description": m.description,
        "start": {"dateTime": m.start.isoformat(), "timeZone": TZ},
        "end": {"dateTime": m.end.isoformat(), "timeZone": TZ},
        "extendedProperties": {"private": {"cb3_key": _key(m), "cb3_hash": _hash(m)}},
    }


def _existing_events(service, cal_id):
    """Future events previously created by this script, keyed by cb3_key."""
    now = datetime.now(timezone.utc).isoformat()
    found, token = {}, None
    while cal_id:
        resp = service.events().list(
            calendarId=cal_id, timeMin=now, singleEvents=True, maxResults=250, pageToken=token
        ).execute()
        for ev in resp.get("items", []):
            k = ev.get("extendedProperties", {}).get("private", {}).get("cb3_key")
            if k:
                found[k] = ev
        token = resp.get("nextPageToken")
        if not token:
            break
    return found


def sync(service, cal_id, meetings, dry_run=False):
    """Create/update/delete future events so the calendar mirrors `meetings`. Returns counts."""
    existing = _existing_events(service, cal_id)
    counts = {"created": 0, "updated": 0, "deleted": 0, "unchanged": 0}
    wanted = {_key(m): m for m in meetings}
    for k, m in wanted.items():
        ev = existing.get(k)
        if ev is None:
            log.info("CREATE %s  %s", m.start, m.title)
            if not dry_run:
                service.events().insert(calendarId=cal_id, body=_body(m)).execute()
            counts["created"] += 1
        elif ev["extendedProperties"]["private"].get("cb3_hash") != _hash(m):
            log.info("UPDATE %s  %s", m.start, m.title)
            if not dry_run:
                service.events().update(calendarId=cal_id, eventId=ev["id"], body=_body(m)).execute()
            counts["updated"] += 1
        else:
            counts["unchanged"] += 1
    for k, ev in existing.items():
        if k not in wanted:
            log.info("DELETE %s  %s", ev["start"].get("dateTime"), ev.get("summary"))
            if not dry_run:
                service.events().delete(calendarId=cal_id, eventId=ev["id"]).execute()
            counts["deleted"] += 1
    return counts
