# CB3_Gcal_sync
Scrapes the [Manhattan CB3 meeting calendar](https://www.nyc.gov/site/manhattancb3/calendar/calendar.page) and keeps a public Google Calendar ("Manhattan CB3") in sync: new meetings are created, changed ones updated, cancelled ones removed. Past events are never touched.

## Setup
1. In [Google Cloud Console](https://console.cloud.google.com/) create a project, enable the **Google Calendar API**, configure the OAuth consent screen (add yourself as a test user), and create an **OAuth client ID** of type *Desktop app*. Download it as `credentials.json` into this folder.
2. `pip install -r requirements.txt`
3. `python sync_cb3.py --dry-run` (first run opens a browser for login; caches `token.json`)
4. `python sync_cb3.py` — creates the calendar, syncs, makes it public, and prints the share links.

Flags: `--dry-run` shows planned changes only; `--private` keeps/makes the calendar private.

## Sharing
The script prints three links: `ical_feed` (subscribe in Google/Apple/Outlook), `web_view` (embeddable page) and `add_to_google` (one-click add). The calendar only updates when the script runs, so schedule it daily, e.g. Windows Task Scheduler running `python C:\Ari\SmallInvests\CB3_Gcal_sync\sync_cb3.py`.

## Tests
`python -m pytest`
