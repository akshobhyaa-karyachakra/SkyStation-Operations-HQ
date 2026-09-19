# Canonical Logic Contract Reconciliation

Status: Awaiting item-level approval  
Scope: Documentation-only reconciliation; no adapter, server, test, or HTML changes applied.  
Canonical source: [SkyStation Operations Intelligence - Backend, Database, MIS, Analytics and Portal Implementation Guide](https://docs.google.com/document/d/1D9oBi6ytBPEfwH171Iup8_Cj2XE7uWfvGOAkPBMBhB8/edit)  
Export used for comparison: https://docs.google.com/document/d/1D9oBi6ytBPEfwH171Iup8_Cj2XE7uWfvGOAkPBMBhB8/export?format=txt  
Compared: 2026-09-19

## Precedence and evidence rule

The canonical Doc wins for rules, schemas, board IDs, column IDs, relation IDs, status semantics, and validation logic. It does not provide current operational values. Current counts and source values must come from live authenticated Monday reads. The Doc states that its observed counts are time-bound evidence; they must not be hard-coded into adapters, tests, or contracts as permanent totals.

This file lists proposed changes only. No proposal below has been applied to the affected contract, adapter, server, test, or HTML file.

## Summary

| ID | Severity | Area | Proposed action | Applied? |
|---|---|---|---|---|
| C-001 | Blocker | Crew role fields | Align the repository contract with deleted legacy fields and relation/mirror schema; inspect any stale implementation references before applying. | No |
| C-002 | High | Crew invariants | Remove fixed roster counts and brittle named-record invariants; require recalculated-on-sync counts and privacy-safe validation. | No |
| C-003 | High | Work Tracker topology | Separate Work Tracker from the report-producing `work_item` stage chain. | No |
| C-004 | High | Missing board contracts | Add contracts for Overview Mapping, Night Security, Service Request Intake, and Role Framework. | No |
| C-005 | High | Normalized model coverage | Add raw ingestion layer, 18 canonical entities, and snapshot manifest to the data contract. | No |
| C-006 | High | Billing entity | Add a billing entity and explicit unsupported-measure exclusions. | No |
| C-007 | Medium | Incident topology | Reject Activity Repository → Incident Logs as a semantic edge despite the source relation. | No |
| C-008 | Medium | Known source defects | Record duplicate labels, legacy formula behavior, blanks, missing native status, and multi-target relations as source-quality issues. | No |
| C-009 | High | Source map freshness | Reconcile stale counts, missing boards, and stale “not captured” statements in `docs/monday-source-map.md`. | No |
| C-010 | Medium | Analytics contract | Add raw/manifest/quality layers, Night Security, exact incident topology, and canonical count/quality semantics where missing. | No |
| C-011 | Medium | Architecture contract | Add raw ingestion, schema discovery, atomic snapshot publication, manifest, quality issues, and current Doc precedence. | No |
| C-012 | Medium | API contract | Add canonical response envelope and the required protected/public endpoint semantics from Doc §10.1. | No |
| C-013 | Medium | Security contract | Add missing-credential zero-request behavior, direct `/data` 404, and source-quality/public-projection rules. | No |

## C-001 — Blocker — Crew role fields

**Canonical Doc:** §8.1, lines 226–230 of the exported text.  
**Repository:** `docs/data-contract.md:30-36,47-49`; `docs/monday-source-map.md:30-35`.

**What the canonical Doc says:**

- Official Role and text Band columns are deleted and invalid.
- Role is the explicit single-value relation `board_relation_mm79kcd6` to Role Framework `5031376976`.
- Team is mirror `lookup_mm792kmk`.
- Band is mirror `lookup_mm79sxzf`.
- Missing Role relation is `needs_review`.
- Multiple Role links violate the live single-value contract.
- Role joins must never use names, role text, team text, or band text.

**What the repository says:**

- `docs/data-contract.md:30-36` already maps `role_relation`, `team`, and `band` to the explicit relation and mirrors.
- `docs/data-contract.md:49` already says `official_role` and the former text Band field are invalid.
- `docs/monday-source-map.md:30-35` records the same deleted fields and live IDs.
- `scripts/sync_crew_repository.py:31-34,50-57` queries only the live IDs and maps them to `role_relation`, `team`, and `band`; it does not query the deleted fields.
- `scripts/validate_crew_snapshot.py:31-32` rejects a stale `official_role` field in a snapshot.

**Finding:** The adapter and validator are aligned with the canonical Doc. The contract wording is directionally aligned, but the Doc adds explicit single-value cardinality and stronger rejection of all text/name-based role resolution. The repository contract should make those requirements unambiguous.

**Proposed change:** Update `docs/data-contract.md` only after approval to state the exact single-value cardinality rule, reject multiple links, and name all prohibited fallback joins. Do not change the adapter in this documentation slice.

## C-002 — High — Crew invariants and privacy

**Canonical Doc:** §1.2, §8.1, §13, lines 24, 227–230, 353–356.  
**Repository:** `docs/data-contract.md:43-50`; `docs/monday-source-map.md:50-59` and any current crew validation assertions in the working tree.

**What the canonical Doc says:**

- Live Crew Repository readback at audit time was 17 records.
- Counts are time-bound and must be recalculated on every sync.
- Stable source IDs and relation IDs are the identity keys.
- Names are display values and must not become fixed named-record invariants.

**What the repository says:**

- The current tracked `docs/data-contract.md` shown in the working tree has already moved away from the older fixed-count wording, but this reconciliation must verify the working-tree version before any documentation merge.
- `docs/monday-source-map.md:50-59` still records an older 72-item Activity Repository readback and acceptance target as historical evidence, which is valid only if clearly labelled as time-bound.
- The prompt identifies a prior contract state that hard-coded 15 total/14 active and a named employee/group-ID invariant; those exact lines are not present in the current committed `data-contract.md`, so the stale assertion may already be in the uncommitted version or a test/adapter branch.
- `scripts/validate_crew_snapshot.py:14-20` checks duplicate names. Names are display values; duplicate-name detection can be a quality warning, but it must not become a relational identity or privacy-leaking error message in public output.

**Finding:** The canonical rule is recalculated-on-sync. Any fixed count or named employee/group-ID assertion is a contract defect and a privacy concern. Current working-tree files must be reviewed before applying a change because they are intentionally outside this slice.

**Proposed change:** Replace fixed totals with live `record_count`, `active_count`, and status aggregates computed from each snapshot. Convert named-record/group-ID checks into source-ID/relation/schema checks; keep duplicate display names as protected quality metadata, never public output. Review uncommitted tests/scripts separately before altering them.

## C-003 — High — Work Tracker mis-classified

**Canonical Doc:** §2.1, §5.2, lines 58, 137–145.  
**Repository:** `docs/data-contract.md:83-107`; `docs/analytics-monday-workflow-contract.md:47-56`.

**What the canonical Doc says:**

- Work Tracker has no customer or execution-board relation.
- It is internal solution-development/process work.
- It is not a stage in the report-producing chain.
- It must not enter customer delivery, flight execution, or report-completion counts.

**What the repository says:**

- `docs/data-contract.md:83-93` currently lists `work_tracker` inside the common `work_item` stage table alongside flight, site activity, processing, and report submission.
- `docs/analytics-monday-workflow-contract.md:47-56` correctly describes Work Tracker as a distinct supporting workflow and excludes it from the main report-producing handoff.

**Finding:** The data contract’s entity table implies a stage relationship that the analytics contract rejects. This is a cross-document contradiction with metric risk.

**Proposed change:** Separate `work_tracker` into an `internal_work` entity/context source. Explicitly prohibit its participation in handoff, delivery, flight, and report-completion aggregates. Preserve its own statuses and quality states.

## C-004 — High — Missing board contracts

**Canonical Doc:** §2.1, lines 40, 55, 73, 76.  
**Repository:** `docs/data-contract.md` has no dedicated sections for these boards; `docs/monday-source-map.md:5-15` omits them.

**Missing contract 1: `0_Overview Mapping` — board `5028881118`**

- Identity: Activity ID prefix `SS_OM`.
- Fields/rules: Assigned To, Assigned Date, two-day Activity Deadline formula, Activity Repository relation `board_relation_mm1gwp2a`, Activity/Pilot/Planned Quantity/Client mirrors, Mapping Flight Status, blocker, FH2 Setup, Georeferencing, NFZs and Safety, New Org Creation, Stakeholder Permissions, Spectra Setup, Org Link, Completion Date.
- Rule: setup/mapping workflow; completion must not be inferred from a name or date alone.

**Missing contract 2: `5_Night Security and Surveillance` — board `5028800878`**

- 355 items; parent week rows with prefix `SS_NSS`.
- Parent fields: Activity Date, Activity Repository relation, Activity/Client mirrors, Report file, Report Submitted? status.
- Subitem fields: Flight Start, Flight Type (Automated/Manual), Pilot, Status (Completed/Terminated/Incomplete), blocker, Incidents, Validation (Needs More Evidence/Valid Finding/False Alarm/Duplicate), Validation Remarks.
- Rule: independent recurring security workflow, not a stage in the flight-to-report chain.

**Missing contract 3: `Adani - Service Request Intake` — board `5028091149`**

- 73 items.
- Fields: Status, Priority, Track, Category, Description, Affected Solution, Feasibility, Assigned To, Request Date, Affected Sites, Completion Date, Requester, conditional software-request context.
- Rule: intake workflow related from selected Report Submission records; never a substitute for report delivery evidence.

**Missing contract 4: `SkyStation Team Role Bands & Weightage Framework` — parent `5031376976`, competency subitems `5031377037`**

- Parent: 19 records comprising 10 roles, 5 band definitions, and 4 framework rules.
- Parent fields: Team, Band, Role Purpose, Primary Accountability, Core Expectation, Level Differentiation, Promotion Gate, Framework State, Subitems, reverse Crew Repository relation.
- Subitems: Name and authoritative `Weightage %` `numeric_mm79pyxm`; 92 competencies observed.
- Rule: only role parents with valid competency subitems are active roles; weights must be numeric, complete, unique, and sum exactly 100%; do not normalize invalid totals.

**Proposed change:** Add dedicated source/entity sections to `docs/data-contract.md` and rows to `docs/monday-source-map.md`, preserving board IDs, relation targets, status labels, and quality rules exactly. Do not add adapters in this slice.

## C-005 — High — Missing normalized entities, raw layer, and manifest

**Canonical Doc:** §3.1–§3.3, lines 82–94.  
**Repository:** `docs/data-contract.md:20-159`.

**What the canonical Doc requires:**

Raw ingestion tables/layer:

- `raw_board_snapshot`
- `raw_item`
- `raw_column_value`
- `raw_relation`
- `raw_person_value`
- `raw_file_link`
- `sync_run`

Normalized entities:

1. `crew_member`
2. `role_framework_parent`
3. `role_competency`
4. `planned_activity`
5. `flight_execution`
6. `processing_qa`
7. `report_submission`
8. `site_activity`
9. `night_security_week`
10. `night_security_flight`
11. `work_item`
12. `inventory_asset`
13. `customer`
14. `service_request`
15. `incident`
16. `workflow_edge`
17. `quality_issue`
18. `snapshot_manifest`

Every entity carries source identity, source/sync timestamps, schema/data state, validation errors, review flags, source URL, and relation target IDs. Snapshot manifest publication is atomic only after required boards are paginated and validated.

**What the repository says:**

- `docs/data-contract.md` has sections for crew, role framework, planned activity, work item, handoff, inventory, and incident, but no raw ingestion layer, `customer`, `service_request`, `night_security_week`, `night_security_flight`, `flight_execution` naming, `workflow_edge`, `quality_issue`, or `snapshot_manifest` contract.
- Existing contracts use a broader `work_item` abstraction and a derived `handoff`, which need mapping to the canonical 18-entity model.

**Proposed change:** Expand the data contract with raw ingestion, the exact 18 entities, quality_issue semantics, snapshot manifest schema, and atomic publication requirements. Preserve existing fields only where they map cleanly; mark mappings needing approval.

## C-006 — High — Missing billing entity

**Canonical Doc:** §7.1–§7.4, lines 207–220.  
**Repository:** `docs/data-contract.md` has no billing entity section; `docs/api-contract.md` lists `/api/billing`; `scripts/sync_customer_repository_billing.py` and `scripts/portal_server.py` already expose billing-related runtime behavior.

**Canonical billing rules:**

- Source: Customer Repository `5028043141` and billing columns.
- Supported statuses: Ready to bill, Billed, Stuck.
- Evidence: SAP Number, PO Number, Invoice Number, Invoice Date, Basic Billing Value, GST Rate, Gross Billing Value, Latest Bill Month, Inventory relation.
- Key: customer item ID plus explicit customer/site/asset or billing subitem relation where present.
- `Billed` without Invoice Number → `needs_review`.
- Ready to bill/Billed without Basic Billing Value → `needs_review`.
- Unexpected Inventory relation → `needs_review`.
- Do not create collections, ageing, margin, profitability, or payment-received measures.

**Proposed change:** Add a protected `billing_record` entity and validation/presentation rules to `docs/data-contract.md`. Update API/security docs to state unsupported commercial measures must not exist in the normalized/public model.

## C-007 — Medium — Incident edge topology

**Canonical Doc:** §5.2, §3.2, lines 145 and 168–169.  
**Repository:** `docs/data-contract.md:116-136`; `docs/analytics-monday-workflow-contract.md:105-114`; `docs/monday-source-map.md:85-89`.

**Canonical rule:** Incident Logs is an outward branch from Flight Operations. The valid edge is Flight Operations → Incident Logs. Activity Repository → Incident Logs is explicitly rejected even though an Activity Repository relation exists on the source board.

**Repository state:** The analytics workflow contract already documents Flight Operations → Incident Logs and rejects Activity Repository → Incident Logs. The general data contract defines a generic handoff model but does not carry the explicit incident-edge rejection into its handoff/edge rule. The source map describes the relation but does not state the semantic rejection.

**Proposed change:** Add an explicit edge allowlist/rejection rule to `docs/data-contract.md`, `docs/monday-source-map.md`, and any workflow-edge contract. Never build semantic edges from source relations alone.

## C-008 — Medium — Known source defects absent or incomplete in contracts

**Canonical Doc:** §2.1, §6.4, §13, lines 46, 52, 356.  
**Repository:** `docs/data-contract.md`, `docs/monday-source-map.md`, `docs/analytics-monday-workflow-contract.md`.

Record these as source-quality issues, not silent repairs:

- Processing and QA has duplicate `Request for Review` labels.
- A legacy Processing and QA formula can emit `Overdue`, while the backend rule is missing dates → `Deadline unknown`.
- Blank and duplicate status/blocker labels exist in source boards.
- Site Activities has no native status column.
- Site Activities and hardware boards have multi-target relation configuration.
- Current rows may have incomplete relation, evidence, or date fields.
- Incident records include review states and must not be converted into clean success/failure metrics.

**Proposed change:** Add a source-quality defect register or section to the source map and data contract. Define the handling for duplicate/unknown labels, formula disagreement, blank labels, no-native-status boards, and multi-target relations.

## C-009 — High — Source map freshness and missing boards

**Canonical Doc:** §2.1 and §13, lines 34–76, 353–356.  
**Repository:** `docs/monday-source-map.md:3,8-15,42-89`.

**Discrepancies:**

- Source map is labelled captured 2026-08-27 while canonical Doc records a 2026-09-17 verification pass.
- Source map counts are older/time-bound: Activity Repository 72 vs canonical 95; Flight Operations 21 vs 4; Processing and QA 14 vs 21; Report Submission 154 vs 281; Inventory 121 vs 136. The source map must not present these as current counts.
- Source map omits Overview Mapping, Night Security, Service Request Intake, and Role Framework.
- Source map says Work Tracker, Inventory, and Incidents were “not captured in this pass” even though the canonical Doc contains their schemas and the repository has adapters/contracts.
- Source map describes Work Tracker as internal work but its top inventory table lacks a clear excluded-from-handoff rule.

**Proposed change:** Add canonical board inventory and a `last_schema_read`/`counts_are_time_bound` marker. Add missing boards and rules. Preserve old readbacks as dated historical evidence, not current counts.

## C-010 — Medium — Analytics workflow contract gaps

**Canonical Doc:** §3, §5, §6, §9, §13.  
**Repository:** `docs/analytics-monday-workflow-contract.md:47-114`.

**Aligned:** Work Tracker is distinct; Site Activities/Night Security/Incident Logs are not universal stages; incident edge direction is documented; quantity exclusion and Deadline unknown semantics are present.

**Gaps to reconcile:**

- Raw ingestion layer and snapshot manifest are not represented in the workflow contract.
- Quality issue records and partial-results semantics are not specified with the canonical fields.
- Night Security is not included in the normalized workflow model even though it is a documented independent workflow.
- The canonical Doc requires `source_count`, `confirmed_handoff_count`, `exception_count`, `missing_evidence_count`, and `data_state` for every stage/workflow summary; the contract must state this for all supported workflows.
- The canonical Doc explicitly says customer delivery is not proof of a Customer Repository relation; this should be carried into all delivery language.

**Proposed change:** Add workflow quality-envelope, Night Security, manifest, partial-results, and delivery-evidence rules to the analytics contract.

## C-011 — Medium — Architecture contract gaps

**Canonical Doc:** §1, §3, §4, §10, §11.  
**Repository:** `docs/architecture.md:1-59`.

**Gaps:**

- Architecture diagram starts at source boards but omits raw immutable ingestion, schema discovery, sync runs, quality issues, snapshot manifest, and atomic publication.
- Architecture does not state that every adapter must re-read board metadata before rollout.
- Architecture does not state that a failed run retains the last valid snapshot with stale/error metadata or returns unavailable when none exists.
- Architecture does not state direct `/data` snapshot access must return 404.
- Architecture does not state missing Monday credentials must produce zero Monday requests.
- Architecture does not carry the canonical rule that source quality is preserved rather than silently repaired.

**Proposed change:** Expand the architecture diagram and failure/publish contract. Add raw layer, schema discovery, manifest, atomic publication, direct-data blocking, and no-credential behavior.

## C-012 — Medium — API contract gaps

**Canonical Doc:** §10.1, lines 261–266.  
**Repository:** `docs/api-contract.md:1-65`.

**Aligned:** The repository API contract lists the runtime endpoint inventory and documents 401/503/state behavior.

**Gaps:**

- The canonical response envelope requires `schema_version`, `data_state`, `generated_at`/`synced_at`, source summary, validation summary, records or aggregate projection, and explicit error/review fields. The repository API contract does not require the full envelope for every protected endpoint.
- The canonical Doc explicitly requires 401/403 for unauthorized requests, 404 for direct snapshot paths, 503 unavailable, 503 needs_review, and stale metadata. The repository contract documents 401/503 but not the complete 403/direct-snapshot 404 requirement.
- The public status/API contract does not explain per-board source summary and validation-summary shape.

**Proposed change:** Add a response-envelope schema and status-code matrix to `docs/api-contract.md`; document direct `/data` 404 and 403 handling without changing server code in this slice.

## C-013 — Medium — Security contract gaps

**Canonical Doc:** §1.3, §4, §10, lines 27–28, 100–127, 258–272.  
**Repository:** `docs/security-and-privacy.md:1-52`.

**Aligned:** The security document covers runtime secrets, public/protected fields, stable relation IDs, projection-first filtering, and stale/unavailable/review states.

**Gaps:**

- It does not explicitly require the Monday adapter to check for `MONDAY_API_TOKEN` before the first request and make zero requests when absent.
- It does not explicitly require direct `/data` snapshot paths to return 404.
- It does not explicitly require raw snapshots to remain audit/replay-only and never enter public projection.
- It does not mention the canonical source-quality rule that duplicate/unknown/contradictory values are retained and surfaced, not repaired.
- It does not carry the incident edge allowlist or the unsupported billing-measure prohibition.

**Proposed change:** Add these controls and evidence requirements to the security/privacy document.

## Approval gate

Do not apply any proposed change above until the owner approves items individually. After approval:

1. Apply documentation-only changes one conflict at a time.
2. Use one commit per approved conflict item with a clear message.
3. Add an ADR when architecture or public exposure changes.
4. Reconcile adapters/tests only in a separately approved implementation slice.
5. Re-run only the verification commands that were actually executed and report their real output.
