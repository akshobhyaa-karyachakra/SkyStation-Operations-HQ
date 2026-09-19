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

## Known endpoint families

- `/api/public-status` — public source state, schema version, and update timestamp only.
- Crew Repository projection — protected source-backed crew records and aggregate inputs.
- Role Framework projection — protected role/competency snapshot.
- Workflow/analytics projection — protected normalized workflow data.
- Inventory, incident, activity, billing, and report projections — protected unless explicitly reduced to approved public aggregates.

The exact endpoint names and response schemas are implementation-owned and must be read from `scripts/portal_server.py` before production integration.

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
