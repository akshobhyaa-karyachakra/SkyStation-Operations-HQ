# Crew Availability backend vertical slice

Status: implemented locally; Monday sync input is server-side only.

```text
Monday Crew Daily Availability (5031561606)
  -> saved board payload
  -> backend/crew_availability.py
  -> SQLite development store / PostgreSQL migration target
  -> /api/public/crew-availability?month=YYYY-MM
  -> aggregate-safe wallboard projection
```

The sync validates weekday rows at exactly 15 records per date, stores raw payloads and source IDs internally, and publishes only date-level counts on the public endpoint. Employee names and Monday identifiers are excluded from the public projection. The protected employee-level route remains to be implemented before the right-side roster is connected to live data.

Run locally:

```bash
PYTHONPATH=. python3 scripts/sync_crew_availability.py --input data/runtime/crew-monday.raw.json
PORTAL_DEV_ALLOW_LOCAL=1 python3 scripts/portal_server.py
curl 'http://127.0.0.1:8767/api/public/crew-availability?month=2026-06'
```

`backend/schema.sql` is the PostgreSQL migration target. The current runtime uses SQLite because PostgreSQL is not installed in this environment. The public wallboard still uses its fixture renderer; switching it to this endpoint is the next integration step, after adding the protected employee-level projection for authorized roster views.
