# Old web application — source backup

`source/` contains the Flask source snapshot taken before the UI redesign on 12 October 2026. This is a source-only backup for comparison and recovery of code, not a complete deployment backup.

For safe Git publication, this copy excludes `.env`, API and SMTP credentials, the SQLite database and its backups, uploaded member files, Git internals, compiled Python caches, virtual environments and private defense notes. Configure new local environment variables and initialize a fresh database if running it separately.

The original complete private backup remains on the owner's computer. It was not uploaded. Never commit its `project.tar.gz` or database files.

The current application remains at the repository root. Design previews are under `previews/`; they are not production applications.
