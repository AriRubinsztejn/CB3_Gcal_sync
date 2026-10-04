# CB3_Gcal_sync

> **Just want the calendar?** Add the public Manhattan CB3 meeting calendar to your own calendar app:
> - [Add to Google Calendar](https://calendar.google.com/calendar/r?cid=9e003cdd8d31e520ef1b697deef2a64ac454d2c22d744a7a152638683504fe06%40group.calendar.google.com)
> - [View in browser](https://calendar.google.com/calendar/embed?src=9e003cdd8d31e520ef1b697deef2a64ac454d2c22d744a7a152638683504fe06%40group.calendar.google.com)
> - iCal feed (Apple Calendar, Outlook, etc. — subscribe by URL): `https://calendar.google.com/calendar/ical/9e003cdd8d31e520ef1b697deef2a64ac454d2c22d744a7a152638683504fe06%40group.calendar.google.com/public/basic.ics`
>
> This is an unofficial calendar. Meetings are copied from the CB3 website, so confirm details there.

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
