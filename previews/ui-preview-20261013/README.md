# FIA Workspace — UI/UX preview

Brand update: primary colors are now FIA green, black and white. The landing footer follows the supplied `Footer Style #3.png` layout with FIA introduction, three link groups, a bottom information row and a back-to-top control. Social destinations remain unconfigured demo buttons rather than guessed external links. The pre-change design is kept at `D:/PWD301/ui-preview-before-green-footer-20261013`.

This is a standalone design preview, not a production Flask replacement.

This version adapts the supplied `Product Landing Page.fig` reference: midnight navy surfaces, hot-pink accents, large editorial serif headings, product-style mockups and a dedicated FIA landing screen. The embedded thumbnail and a decorative sphere asset were inspected/extracted locally; this is a visual adaptation, not a pixel-exact reconstruction of every Figma layer.

Run `python preview_server.py --port 5082` from this directory and open `http://127.0.0.1:5082`. The server binds only to localhost, serves this preview and exposes one read-only CTFtime calendar adapter. Opening `index.html` directly still shows the local design, but cannot load live CTFtime data. The original light preview remains unchanged at `D:/PWD301/ui-preview-20261012`.

FIA members, money, FIA events, tasks, messages and notifications are synthetic demo data. Forms and actions only change in-memory preview state; reloading resets it. No real AI call, email, authentication, export or club-data mutation occurs. Production permissions and backend integration are not tested by this preview. The CTFtime tab is the exception to sample data: it reads the real public calendar described below.

## CTFtime calendar

Events has two source tabs for both member and board design modes. FIA retains its existing sample event controls; CTFtime shows ongoing/upcoming competitions in a 90-day window with source links and the actual retrieval timestamp. CTFtime times display in Asia/Bangkok (UTC+7). Board design mode has a one-click “Tạo sự kiện FIA” shortcut: it copies the contest title, start/end and source link into a demo “FIA tham gia CTF” participation event, switches to the FIA tab and prevents duplicates by CTFtime ID. Members can view that demo event and try registration, but cannot import contests. Unknown capacity/location remain unspecified. These imports exist only in memory and reset on reload: no real club database mutation or CTFtime/team registration occurs. Frontend role checks are demo controls, not production security.

`GET /api/ctftime/events` uses a fixed public Google ICS feed belonging to `ctftime@gmail.com`, the calendar embedded on `https://ctftime.org/calendar/`. It does **not** use the CTFtime JSON API, whose documentation limits usage to data analysis/mobile applications and prohibits clones. Neither a reachable public calendar nor this prototype establishes permission for public website redistribution: confirm CTFtime/calendar reuse terms before production publishing.

The adapter has a 15-second upstream timeout, a 3 MB response bound, a 10-minute server cache and a short error cooldown. It excludes cancelled entries and entries without supported UTC timestamps or an official CTFtime event URL. Display is bounded to 100 events. It does not invent rating/weight or online/offline metadata absent from the calendar. If refresh fails, at most a 24-hour-old successful cache is labeled stale; without a cache the UI shows an error, not fabricated competition data. The browser loads only when CTFtime is selected and has a five-minute cache. The external source may change schedules: always verify on the linked CTFtime event page.

Workspace routes now require a UI-only demo login. The default role is member; board-design mode must be chosen explicitly in the demo login selector. Member screens show only personal sample tasks/dues and no administration controls. Guest direct links redirect to login; member administration links redirect to the member dashboard. Demo identity (not passwords) is kept in sessionStorage for the current tab and removed on logout. This frontend routing is **not real authentication or authorization** and can be altered with developer tools; the actual Flask app must continue using server-side session and permission checks when these designs are integrated.

Start at the FIA landing screen, choose “Vào workspace” for the dashboard. Use the sidebar for primary pages. Use “Xem các màn hình” or Ctrl+K for login, registration, pending approval, profile and check-in layouts. Narrow screens have a collapsible menu. Dialogs support keyboard navigation and Escape.

The current Flask app remains untouched during this design work. A private complete backup was created before preview implementation at `/home/phanquang/backups/club-management-before-ui-20261012-105648`; it includes configuration and a consistent SQLite snapshot. Do not upload that backup.

After design approval, integrate these visual patterns into existing Jinja templates while retaining real routes, CSRF, role checks, AI proposal approvals and business validation. This preview must not be deployed as the actual club app.
