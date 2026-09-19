# Business Logic Index

Status: In review  
Canonical logic source: existing Google Doc — URL pending confirmation from the owner.  
Last reviewed: 2026-09-19

This file indexes the existing business-logic Google Doc. It is not a duplicate rulebook. When the Google Doc changes, update this index and the affected repository contracts in the same work slice.

## Rule areas

- Delivery commitment: weekly frequency defines the flight plan; report submission is due Flight Date +1 day; Planned Quantity is scope metadata and is excluded from calculations.
- Crew presence: Crew Repository `Availability` is the sole public daily-presence source; blank maps to `Awaiting confirmation`; Terminated and Resigned are excluded from active totals.
- Evidence and handoff: planning records do not prove execution, and stages join only through explicit stable relations.
- Freshness: `current`, `stale`, `unavailable`, and `needs_review` remain distinct states.
- Public boundary: aggregate team/region information may be public; names, IDs, financial values, internal notes, and unresolved root-cause detail remain protected.
- Role framework: explicit relation IDs are authoritative; display-name matching is not a valid join.

## Implementation map

- Business rules → `docs/data-contract.md` and `docs/monday-source-map.md`.
- Analytics rules → `docs/analytics-monday-workflow-contract.md`.
- Crew adapter → `scripts/sync_crew_repository.py`.
- Role adapter → `scripts/sync_role_framework.py`.
- Public/protected runtime behavior → `scripts/portal_server.py` and `docs/architecture.md`.
- Public wallboard interpretation → `public-wallboard.html` and `docs/product-requirements.md`.

## Open confirmations

- Add the canonical Google Doc URL, owner, and review cadence.
- Confirm the approved public metrics for the next wallboard revision.
- Confirm production snapshot freshness window and timezone.

## Change protocol

1. Update the Google Doc first when the rule is a product/operations decision.
2. Record the changed rule and owner here.
3. Update data contracts, adapters, UI copy, and tests.
4. Add an ADR when the rule changes architecture or public exposure.
5. Verify the deployed projection before release.
