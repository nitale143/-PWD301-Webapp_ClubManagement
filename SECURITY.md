# FIA security baseline — OWASP Top 10:2025

This project uses [OWASP Top 10:2025](https://top10.owasp.org/2025/) as a risk checklist, not a certification or guarantee that every vulnerability is eliminated.

## Authorization policy

Approved CN, PCN, TB and THUKY_THUQUY accounts form one global **Admin/BOD** group. THANH_VIEN accounts form the **Member** group. Department/designation labels still support task assignment and office handoff; they do not restrict an admin to a department. Members retain self-only private member/task/fund access and cannot approve actions. Private chat conversations remain owned by their author, including for admin accounts.

Sensitive writes require a session CSRF token. Logout is POST-only. Last-active-admin removal/demotion is conditional in SQL and rechecks current database role, not stale objects. CN is assigned through the explicit designation-handoff flow rather than generic assignment. Ended/cancelled events reject task mutations. AI and mail continue to use explicit approval workflows; a model response alone never authorizes execution.

## Control mapping

| Category | Implemented controls | Remaining deployment responsibility |
| --- | --- | --- |
| A01 Broken Access Control | Shared two-role checks, ownership, global CSRF, private upload path normalization, last-admin safeguards | Restrict direct file serving; do not expose private uploads through a proxy alias |
| A02 Security Misconfiguration | Host allowlist, secure production cookies, debug prohibition, CSP, nosniff, anti-framing, safe cache rules | Set production environment, trusted hosts and trusted HTTPS reverse proxy correctly |
| A03 Software Supply Chain Failures | Tested dependency upgrades, full hash-pinned lock, dependency audit | Repeat audits in CI; review updates and lock changes |
| A04 Cryptographic Failures | Werkzeug password hashing, unpredictable session keys, production HTTPS, encrypted SMTP | Encrypt disks/database backups; rotate disclosed secrets; restrict backup/key permissions |
| A05 Injection | ORM parameters, Jinja escaping, nonce-protected inline scripts, text-only Excel cells, validated email headers | Keep raw SQL/unsafe rendering and arbitrary command execution out of new features |
| A06 Insecure Design | Server-side member/admin policy, terminal-state checks, explicit review gates, bounded model/tool execution | Threat-model each new action and validate concurrent workflows under real load |
| A07 Authentication Failures | Generic failures, bounded login/password inputs, login throttling, session/token rotation, protected logout | Limiter is per-process; use a shared rate limit at the reverse proxy or shared store for multiple workers |
| A08 Software/Data Integrity Failures | Conditional admin mutations, payment/proposal claims, server-verified CTF imports, lock hashes | Test concurrency and recovery with the actual production database backend |
| A09 Security Logging/Alerting Failures | Request IDs, auth/denial/mutation events, rotated private logs without credentials/mail bodies | Monitor logs and configure alerts; private log rotation is not a full alerting service |
| A10 Mishandling Exceptional Conditions | Rollback on failures, safe browser/API errors, bounded upload/provider/feed inputs, no raw exception disclosure | Monitor outages and test backup/restore and external-service recovery |

## Production setup

Use `APP_ENV=production`, a random `SECRET_KEY` of at least 32 characters, and `TRUSTED_HOSTS` containing the real hostnames. Serve through HTTPS. Debug must be off. Sessions are HttpOnly/SameSite=Lax and Secure in production, with an eight-hour lifetime. The app does not blindly trust forwarded HTTPS/IP headers: configure your trusted reverse proxy boundary before exposing it. Local HTTP development remains supported and is not a production security profile.

Install the tested Python 3.14 lock with `python -m pip install --require-hashes -r requirements-lock.txt`, then `python -m pip check`. Regenerate and re-audit the lock if the target Python/platform changes. `pip-audit -r requirements-lock.txt` requires a separately installed audit tool. Tooling itself should be kept updated. Never install dependencies directly from an unreviewed generated answer or user-supplied URL.

When no development SECRET_KEY is configured, a private local key is created in `instance/session-secret.key`. Production refuses a missing/short/example key. Never publish `.env`, that key, `instance/`, uploaded member images, security logs, or raw private backups. Previously disclosed API keys and app passwords should be revoked and replaced by the owner.

MAIL_ENABLED=false no longer prints recipient addresses, subjects or message bodies. SMTP uses TLS or SSL and rejects newline injection in headers. Mail delivery and security alerts must be verified with authorized recipients, not by sending unsolicited test messages.

The old source snapshots under `backups/` and standalone `previews/` are historical/design artifacts, **not** hardened deployment targets. Deploy only the current root application.

## Verification

Run `python -m unittest discover -s tests -q`. Tests use temporary databases and mocked mail/model requests, including CSRF, ownership, all four admin designations, stale-object last-admin protection, cancelled tasks, auth throttling, headers, upload validation/path aliases, and formula-safe exports. Browser scripts verify current UI and real backend SSE/history on the isolated fixture; they must never target the real club database. Passing tests is evidence for these cases, not proof of complete OWASP compliance.
