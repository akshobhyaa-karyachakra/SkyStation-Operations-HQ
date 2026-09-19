# ADR-0003: Crew Availability Is the Public Presence Source

Status: Accepted  
Date: 2026-09-17

## Context

The public wallboard needs a daily crew-presence view, but the source does not establish workload, utilization, or capacity.

## Decision

Use the Crew Repository `Availability` status as the sole public daily-presence source. Blank values map to `Awaiting confirmation`; Terminated and Resigned records are excluded from active totals.

## Consequences

- Public output is limited to team/status aggregates.
- Names and inferred allocation remain protected.
- Unsupported capacity metrics cannot be shown until an authoritative source exists.
