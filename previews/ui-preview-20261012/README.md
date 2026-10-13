# FIA Workspace — UI/UX preview

This is a standalone design preview, not a production Flask replacement.

Open `index.html` in a browser, or serve this directory with `python -m http.server 5080 --bind 127.0.0.1` and open `http://127.0.0.1:5080`.

All members, money, events, tasks, messages and notifications are synthetic demo data. Forms and actions only change in-memory preview state; reloading resets it. No real AI call, email, authentication, export or club-data mutation occurs. Production permissions and backend integration are not tested by this preview.

Use the sidebar for primary pages. Use “Xem các màn hình” or Ctrl+K for login, registration, pending approval, profile and check-in layouts. Narrow screens have a collapsible menu. Dialogs support keyboard navigation and Escape.

The current Flask app remains untouched during this design work. A private complete backup was created before preview implementation at `/home/phanquang/backups/club-management-before-ui-20261012-105648`; it includes configuration and a consistent SQLite snapshot. Do not upload that backup.

After design approval, integrate these visual patterns into existing Jinja templates while retaining real routes, CSRF, role checks, AI proposal approvals and business validation. This preview must not be deployed as the actual club app.
