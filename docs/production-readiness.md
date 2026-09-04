# Production readiness

The portal is ready for deployment wiring, but production access remains intentionally incomplete until company-owned configuration is supplied.

## Completed in the repository

- Read-only normalized adapters exist for the approved operational boards.
- Protected API routes require `PORTAL_API_TOKEN` unless the loopback-only development bypass is explicitly enabled.
- Direct `/data` snapshot access returns `404`.
- Missing snapshots return `503` with `data_state: unavailable`.
- Invalid snapshots return `503` with `data_state: needs_review`.
- Valid snapshots older than `PORTAL_SNAPSHOT_MAX_AGE_SECONDS` are labelled `stale` and carry their update timestamp.
- `/api/public-status` exposes only source state, schema version, and update timestamp; it does not expose records or credentials.
- Customer-safe dashboard projections exclude billing amounts and protected detail.
- The frontend has no fallback operational fixtures when protected sources are unavailable.

## Required external configuration

1. Deploy `scripts/portal_server.py` behind a production HTTPS reverse proxy or managed application host.
2. Set `PORTAL_API_TOKEN` in server-side runtime configuration. Never put it in Git, HTML, browser JavaScript, logs, or Discord.
3. Set `MONDAY_API_TOKEN` in the server-side secret manager for the read-only sync worker.
4. Set `PORTAL_SNAPSHOT_MAX_AGE_SECONDS` to the agreed freshness window; the default is 86400 seconds.
5. Configure Google OAuth for the production HTTPS origin and redirect URI.
6. Provide the approved manager email allowlist or Google Group to the authorization layer.
7. Configure a scheduler for the sync worker and a protected runtime location for snapshots.
8. Confirm snapshot retention, timezone, sync cadence, and stale-read policy.

## Release checks

Run the repository checks with:

```bash
uv run --with pytest pytest -q
python3 -m py_compile scripts/portal_server.py scripts/portal_metrics.py
```

Before release, exercise unauthorized, authorized, missing, invalid, stale, and direct-snapshot requests against the deployed HTTPS host, then verify the browser receives only the authorized projection.
