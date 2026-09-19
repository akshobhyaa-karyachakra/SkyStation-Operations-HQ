# API and Runtime Contract

Status: Draft baseline  
Last reviewed: 2026-09-19

This document records the contract boundary visible from the current repository. Endpoint details must be verified against `scripts/portal_server.py` whenever a route changes.

## Authentication

- Protected endpoints require `PORTAL_API_TOKEN` in the server-side request boundary.
- Tokens must never appear in HTML, browser JavaScript, Git, logs, Discord, or documentation.
- Public status must expose only approved source metadata.

## Contract states

Every source-backed response must preserve one of:

- `current`
- `stale`
- `unavailable`
- `needs_review`

## Implemented endpoint inventory

The current runtime defines these snapshot endpoints in `scripts/portal_server.py`:

- `/api/crew` — protected Crew Repository snapshot.
- `/api/activity` — protected Activity Repository snapshot.
- `/api/flight` — protected Flight Operations snapshot.
- `/api/site-activities` — protected Site Activities snapshot.
- `/api/processing-qa` — protected Processing and QA snapshot.
- `/api/report-submission` — protected Report Submission snapshot.
- `/api/work-tracker` — protected Work Tracker snapshot.
- `/api/inventory` — protected Inventory snapshot.
- `/api/incidents` — protected Incident Logs snapshot.
- `/api/workflow-network` — protected workflow network snapshot.
- `/api/billing` — protected Customer Repository billing snapshot.
- `/api/role-framework` — protected Role Framework snapshot.
- `/api/metrics` — protected derived metrics built from available snapshots.
- `/api/crew-portal` — protected Manager Vault store projection.
- `/api/crew-portal/role-lenses` — protected role-lens projection.
- `/api/crew-portal/performance` — protected performance projection.
- `/api/crew-portal/responsibilities` — protected responsibility projection.
- `/api/crew-portal/requests` — protected edit-request projection.
- `/api/crew-portal/one-to-ones` — protected one-to-one projection.
- `/api/public-status` — public source state, schema version, and update timestamp only.

Snapshot endpoints return `401` when unauthorized, `503` with `data_state: unavailable` when no snapshot exists, `503` with `data_state: needs_review` when the snapshot is invalid, and `200` with the body plus `data_state` and `snapshot_updated_at` when valid/current or stale. The exact field schemas remain implementation-owned by each adapter and must be updated here when a schema is promoted for production use.

## Public projection rules

Allowed only when approved:

- Team/region aggregates.
- Source state and freshness.
- Counts and derived rates whose source and calculation are documented.
- Customer-safe delivery/readiness outcomes.

Excluded:

- Names, People IDs, Monday IDs, source board names, raw notes, financial values, serial numbers, credentials, internal blockers, and unresolved root-cause detail.

## Contract testing

Each endpoint requires tests for authorized, unauthorized, missing snapshot, invalid snapshot, stale snapshot, and public-field filtering behavior. A successful HTTP status alone is insufficient; read back the response and assert the projection fields.
