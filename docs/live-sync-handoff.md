# Live Monday sync handoff

Updated: 2026-09-27

## Current objective
Connect the full portal backend to live Monday data without exposing credentials or publishing unvalidated numbers.

## Completed

- Full portal backend map: `docs/portal-backend-map.md`.
- Shared PostgreSQL target schema: `backend/platform_schema.sql`.
- Crew Availability SQLite development slice and public API:
  - `backend/crew_availability.py`
  - `scripts/sync_crew_availability.py`
  - `GET /api/public/crew-availability?month=YYYY-MM`
- Cross-board delivery projection:
  - `backend/delivery.py`
  - `GET /api/public/delivery-summary?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
- Atomic batch publisher:
  - `scripts/sync_delivery_sources.py`
  - Runs Flight Operations, Processing/QA, and Report Submission adapters in a temporary directory.
  - Publishes all three only if every adapter succeeds.
  - A failure leaves prior snapshots untouched.
- Snapshot validator:
  - `scripts/validate_delivery_snapshots.py`
  - Prints only aggregate totals, quality counts, and missing-snapshot state.
- Delivery tests:
  - `tests/test_delivery_projection.py`
  - Covers complete chains, missing stages, invalid Done reports, and duplicate stages.
- Stale fixed record-count checks were removed from the three delivery adapters. Structural validation is used instead.
- Completed-stage totals exclude records marked `needs_review`.

## Live source facts already read

- Flight Operations board: 6 current records in the last read.
- Processing and QA board: 7 current records in the last read; several records had missing dates or relations.
- Report Submission board: 329 current records in the last read.
- Board relations use Activity Repository IDs, not display names.

## Current blocker

`MONDAY_API_TOKEN` is not available in the backend runtime. The batch command was tested and correctly stopped before making any request:

```text
MONDAY_API_TOKEN is required; no request was made
```

No token is stored in this repository, Discord, Google Docs, source code, or logs.

## Resume procedure

1. Place the token in a private server-only file, for example `/opt/data/secrets/skystation.env`, with mode `600`:

   ```text
   MONDAY_API_TOKEN=<private value>
   ```

2. Load it only in the backend shell:

   ```bash
   set -a
   source /opt/data/secrets/skystation.env
   set +a
   ```

3. Run from the repository root:

   ```bash
   python3 scripts/sync_delivery_sources.py
   ```

4. Share only the non-secret command output. Never share the token.

5. Inspect `data/snapshot-manifest.json` and the three ignored snapshots. Check counts, source IDs, relation targets, dates, statuses, blockers, evidence, and `needs_review` records.

6. Run the delivery projection against the published snapshots and verify the public response contains aggregate fields only.

7. Only after that connect Reports, Activity Tracking, Analytics, MIS, and the public wallboard to the delivery API.

## Safety rules

- Never mutate Monday during source discovery or sync validation.
- Never use names as cross-board join keys.
- Never replace unavailable data with fixtures in a source-backed view.
- Never count a `needs_review` stage as completed.
- Never publish partial batch results.
- Never expose Monday IDs, Discord IDs, private links, internal notes, credentials, or tokens in public responses.
