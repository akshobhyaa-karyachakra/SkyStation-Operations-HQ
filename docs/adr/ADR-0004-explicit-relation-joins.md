# ADR-0004: Use Explicit Stable Relations for Joins

Status: Accepted  
Date: 2026-09-19

## Context

Display names and text labels can collide, change, or represent different records across boards.

## Decision

Use explicit Monday relation/item IDs as join keys. Display names are presentation values only. Missing or ambiguous relations produce `needs_review` rather than a guessed match.

## Consequences

- Handoff and role assignments are traceable.
- Sync validation must preserve relation IDs.
- UI and public projections must not reveal those internal IDs.
