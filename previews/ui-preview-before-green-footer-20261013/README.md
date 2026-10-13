# FIA Workspace — UI/UX preview

This is a standalone design preview, not a production Flask replacement.

This version adapts the supplied `Product Landing Page.fig` reference: midnight navy surfaces, hot-pink accents, large editorial serif headings, product-style mockups and a dedicated FIA landing screen. The embedded thumbnail and a decorative sphere asset were inspected/extracted locally; this is a visual adaptation, not a pixel-exact reconstruction of every Figma layer.

Open `index.html` in a browser, or serve this directory with `python -m http.server 5082 --bind 127.0.0.1` and open `http://127.0.0.1:5082`. The original light preview remains unchanged at `D:/PWD301/ui-preview-20261012`.

All members, money, events, tasks, messages and notifications are synthetic demo data. Forms and actions only change in-memory preview state; reloading resets it. No real AI call, email, authentication, export or club-data mutation occurs. Production permissions and backend integration are not tested by this preview.

Start at the FIA landing screen, choose “Vào workspace” for the dashboard. Use the sidebar for primary pages. Use “Xem các màn hình” or Ctrl+K for login, registration, pending approval, profile and check-in layouts. Narrow screens have a collapsible menu. Dialogs support keyboard navigation and Escape.

The current Flask app remains untouched during this design work. A private complete backup was created before preview implementation at `/home/phanquang/backups/club-management-before-ui-20261012-105648`; it includes configuration and a consistent SQLite snapshot. Do not upload that backup.

After design approval, integrate these visual patterns into existing Jinja templates while retaining real routes, CSRF, role checks, AI proposal approvals and business validation. This preview must not be deployed as the actual club app.
