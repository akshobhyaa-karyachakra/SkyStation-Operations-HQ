# ADR-0002: Protected Server Adapters Are the Source Boundary

Status: Accepted  
Date: 2026-09-17

## Context

Monday and other source systems contain internal identifiers, credentials, personal data, and operational detail that must not reach public browser code.

## Decision

The browser consumes protected server-side normalized snapshots and public-safe projections. It never calls Monday directly.

## Consequences

- Adapters own source schema mapping and validation.
- Public filtering happens before data reaches the browser.
- Missing, stale, invalid, and unavailable states remain explicit.
- Production deployment requires runtime secret management and a scheduler.
