# FIA UI/UX previews

- `ui-preview-20261013/`: current green/black/white design, demo sessions, member/BDH views, FIA and live CTFtime tabs, and the BDH shortcut to create an in-memory FIA participation event.
- `ui-preview-20261012/`: original light-design source backup.
- `ui-preview-before-green-footer-20261013/`: source backup before the green branding/footer update.

Run the current preview separately from the real Flask app:

```sh
cd previews/ui-preview-20261013
python3 preview_server.py --port 5082
```

Open http://127.0.0.1:5082. Choose the explicit BDH demo role to try CTFtime imports. Sample club actions reset on reload and do not write to the real database, send mail or register teams at CTFtime. Preview role selection is not real authorization. Read the current preview README for calendar sourcing and production reuse limitations.

Generated screenshots and runtime caches are excluded from these source backups. The old real Flask source snapshot is in `../backups/club-management-before-ui-20261012-105648/source/`.
