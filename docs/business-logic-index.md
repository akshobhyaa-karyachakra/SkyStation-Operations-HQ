# Business Logic Index

Status: In review  
Canonical logic source: [SkyStation Operations Intelligence - Backend, Database, MIS, Analytics and Portal Implementation Guide](https://docs.google.com/document/d/1D9oBi6ytBPEfwH171Iup8_Cj2XE7uWfvGOAkPBMBhB8/edit)
Plain-text export: https://docs.google.com/document/d/1D9oBi6ytBPEfwH171Iup8_Cj2XE7uWfvGOAkPBMBhB8/export?format=txt
Owner: Skylark product/operations owner — exact named owner to be confirmed
Review cadence: before each adapter rollout and whenever live Monday schema/rules change
Last reconciled: 2026-09-19

## Rule of precedence

For rules, schemas, column IDs, board IDs, relation IDs, status semantics, and validation logic, the canonical Google Doc takes precedence over repository documents when they disagree. The Doc is documentation only and is never an operational data source. Live authenticated Monday readback is the source of operational values and current counts.

This distinction is mandatory: use the Doc to decide how to interpret and validate data; use live Monday reads to obtain the data itself. Do not copy observed counts from the Doc into code or treat them as permanent roster/board totals.

## Rule areas

- Delivery commitment: weekly frequency defines the flight plan; report submission is due Flight Date +1 day; Planned Quantity is scope metadata and is excluded from calculations.
- Crew presence: Crew Repository `Availability` is the sole public daily-presence source; blank maps to `Awaiting confirmation`; Terminated and Resigned are excluded from active totals.
- Crew role fields: the old Official Role/text Band columns are deleted and invalid; Role is the explicit single-value relation `board_relation_mm79kcd6` to Role Framework; Team and Band are live mirrors.
- Evidence and handoff: planning records do not prove execution, and stages join only through explicit stable relations.
- Work Tracker: internal work only; it is not a stage in the report-producing chain and must not enter delivery, flight, or report-completion counts.
- Incident topology: the valid semantic branch is Flight Operations → Incident Logs; Activity Repository → Incident Logs is rejected even if the source relation exists.
- Freshness and quality: `current`, `stale`, `unavailable`, `needs_review`, `no_data`, and `partial_results` remain distinct states where applicable.
- Public boundary: aggregate team/region information may be public; names, IDs, financial values, internal notes, and unresolved root-cause detail remain protected.

## Implementation map

- Business rules → `docs/data-contract.md` and `docs/monday-source-map.md`.
- Canonical conflict register → `docs/CONFLICTS.md`.
- Analytics rules → `docs/analytics-monday-workflow-contract.md`.
- Crew adapter → `scripts/sync_crew_repository.py`.
- Role adapter → `scripts/sync_role_framework.py`.
- Public/protected runtime behavior → `scripts/portal_server.py` and `docs/architecture.md`.
- Public wallboard interpretation → `public-wallboard.html` and `docs/product-requirements.md`.
- Source-quality and release behavior → `docs/qa-and-release.md` and `docs/operations-runbook.md`.

## Open confirmations

- Confirm the named owner of the canonical Google Doc; the URL and precedence rule are now registered.
- Confirm whether the canonical Doc should be mirrored into a versioned export artifact in the repository. Do not copy it automatically without an explicit policy.
- Approve or reject each item in `docs/CONFLICTS.md` before applying repository contract changes.

## Change protocol

1. Update the canonical Google Doc first when the rule is a product/operations decision.
2. Re-read live Monday schema and values separately; never use Doc counts as operational truth.
3. Add or update a conflict entry when repository text diverges.
4. Obtain item-level approval before changing contracts or code.
5. Apply approved documentation changes one conflict item per commit; update affected adapters/tests only in a separately approved slice.
6. Add an ADR when the change alters architecture or public exposure.
7. Re-run contract tests, public-safety checks, and deployed verification.
