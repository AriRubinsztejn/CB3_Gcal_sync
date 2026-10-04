"""Sync Manhattan CB3 meetings from the NYC.gov calendar page to a Google Calendar."""
import argparse
import logging
import sys

import cb3_scraper
import gcal_sync


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="show planned changes without writing")
    ap.add_argument("--private", action="store_true", help="keep (or make) the calendar private instead of public")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    meetings = cb3_scraper.fetch_meetings()
    if not meetings:
        logging.error("No meetings parsed; page layout may have changed. Aborting without changes.")
        return 1
    logging.info("Parsed %d meetings", len(meetings))
    for m in meetings:
        logging.info("  %s  %s @ %s", m.start.strftime("%a %b %d %I:%M%p"), m.title, m.location)

    service = gcal_sync.get_service()
    cal_id = gcal_sync.get_calendar_id(service, create=not args.dry_run)
    counts = gcal_sync.sync(service, cal_id, meetings, dry_run=args.dry_run)
    logging.info("%s%s", "[dry-run] " if args.dry_run else "", counts)

    if cal_id and not args.dry_run:
        gcal_sync.set_public(service, cal_id, public=not args.private)
        if not args.private:
            for name, url in gcal_sync.share_links(cal_id).items():
                print(f"{name}: {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
