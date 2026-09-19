# Operations Runbook

Status: Draft baseline  
Last reviewed: 2026-09-19

## Local checks

```bash
uv run --with pytest pytest -q
python3 -m py_compile scripts/portal_server.py scripts/portal_metrics.py
node --check /tmp/extracted-script.js
```

Use a real extracted JavaScript file for `node --check`; do not pipe downloaded content directly to an interpreter.

## Static publication

- Branch: `main`.
- GitHub Pages source: repository root.
- Portal entry: `rebuild-preview.html`.
- Wallboard entry: `public-wallboard.html`.
- Verify the workflow run reaches `success` before checking the hosted URL.
- Add a cache-busting `?build=<commit>` query when checking a new static artifact.

## Runtime configuration

Required production configuration is external and must never be committed:

- `PORTAL_API_TOKEN`.
- `MONDAY_API_TOKEN`.
- Snapshot storage/retention.
- Freshness window.
- Google OAuth client and redirect URI.
- Approved manager email/group.
- Sync scheduler.

## Failure handling

- `unavailable`: investigate missing snapshot or failed sync; do not substitute fixtures.
- `needs_review`: inspect contract validation output and source schema changes.
- `stale`: report snapshot age and verify scheduler/runtime health.
- Unauthorized: confirm auth boundary and do not weaken it for convenience.

## Rollback

1. Identify the last verified commit and hosted artifact.
2. Revert or redeploy only the affected change.
3. Re-run tests and public scans.
4. Verify hosted output and record the rollback in `docs/decision-log.md`.

## Secret handling

Never store credentials, API keys, OAuth secrets, passwords, tokens, or connection strings in this repository, HTML, logs, artifacts, or Discord. Replace any captured value with `[REDACTED]`.
