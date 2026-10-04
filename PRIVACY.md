# Privacy Policy

_Last updated: October 4, 2026_

CB3_Gcal_sync ("the app") is a small open-source script that copies the public meeting schedule of Manhattan Community Board 3 from nyc.gov into a Google Calendar named "Manhattan CB3". It is run by its owner on their own computer.

## What the app accesses
- **Google Calendar:** After the owner signs in with Google, the app uses the Google Calendar API to create and manage one calendar ("Manhattan CB3"), add, update and delete events on it, and set its sharing to public (read-only). It only changes that calendar and the events it created.
- **Public web page:** The app reads the public CB3 calendar page at nyc.gov. No personal data is involved.

## What the app stores
- A Google sign-in token (`token.json`) and the OAuth client file (`credentials.json`) are stored only on the owner's computer. They are not uploaded anywhere.
- The ID of the "Manhattan CB3" calendar is saved in a local file (`config.json`).
- A local log file (`sync.log`) records what the script did.

## What the app does not do
- It does not collect, sell, share, or transmit personal data to any third party or to the developer.
- It does not read or use any data from your other calendars or your Google account beyond what is described above.
- It has no servers, analytics, or advertising.

## Public calendar
The "Manhattan CB3" calendar is public by design. It contains only meeting information (committee names, dates, times, locations, agendas, and Zoom links) that CB3 already publishes on nyc.gov. People who subscribe to it do not interact with this app and no data about them is collected.

## Revoking access
You can revoke the app's access at any time at https://myaccount.google.com/permissions and delete the local files listed above.

## Contact
Questions: open an issue at https://github.com/AriRubinsztejn/CB3_Gcal_sync/issues
