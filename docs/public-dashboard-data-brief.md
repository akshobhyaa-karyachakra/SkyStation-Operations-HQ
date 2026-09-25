# Skylark Public Dashboard
## Data, source, projection, and page-direction brief

**Status:** Direction-setting document for the next public-dashboard rebuild  
**Audience:** Sai, product/design, data engineering, portal engineering, QA  
**Boundary:** Public display only; aggregate operational signals; no internal records  
**Source of truth:** Monday-backed normalized server projections, never browser-side Monday calls

---

## 1. What the public dashboard is for

The Public Dashboard is a public-safe operational display. It should let a viewer understand the operating state of Skylark in seconds, then understand the few signals that explain that state without exposing internal people, customer, asset, billing, or evidence records.

It is not a manager workspace, task register, source browser, billing console, or replacement for the protected Manager Vault. It is a projection layer with a deliberately smaller vocabulary than the internal portal.

### Public viewer questions

1. Is work moving?
2. Where is work in the operating chain?
3. Is the field and crew system available for current demand?
4. Where is work happening at a safe regional level?
5. Are customer-ready reports being delivered on cadence?
6. Is the fleet ready for planned demand?

### Non-goals

- Showing public names, employee-level presence, customer names, site names, serial numbers, board/item IDs, internal notes, billing amounts, credentials, or raw Monday links.
- Showing a number when its source is stale, unavailable, contradictory, or unresolved.
- Inferring joins from names, titles, location text, dates, or visual similarity.
- Turning activity volume into a person-performance score.
- Presenting planned scope as completed work.
- Presenting a static synthetic fixture as live operational truth.

---

## 2. Canonical technical flow

```text
Monday boards
  → server-side read-only adapters
  → board-specific normalization
  → relation/date/status validation
  → source snapshot + quality state
  → approved public projection
  → public dashboard API/display
```

The browser must never call Monday directly and must never contain a Monday token. The public projection must be generated server-side from approved normalized data. The hosted static preview may use clearly labelled synthetic values, but it must not silently become a source-backed surface.

Every public response should carry:

- `schema_version`
- `data_state`: `current`, `stale`, `unavailable`, `partial`, `needs_review`, or `no_data`
- `source_updated_at`
- `snapshot_updated_at`
- `validation_issues[]`
- `period` and operating timezone
- projection version
- aggregate-only/public-safe classification

When a source is unavailable, the UI must show an unavailable or stale state. It must not replace the state with a plausible number.

---

## 3. Verified source inventory

The following source map is the starting contract. Board metadata and column IDs must be re-read before production adapters or mutations because Monday configuration can change.

| Source | Board ID | Role | Public use |
|---|---:|---|---|
| SkyStation Crew Repository | `5030902067` | People, team, role, availability context | Aggregate crew availability only |
| SkyStation Activity Repository | `5027240228` | Planning/reference activity master | Planned scope and cadence only; never proof of execution |
| 1_Flight Operations | `5027240883` | Scheduled and conducted flight execution | Planned, executed, blocked, completion aggregates |
| 2_Processing and QA | `5027256991` | Processing and QA evidence | Processing/QA queue and completion aggregates |
| 3_Report Submission | `5027265596` | Report delivery evidence | Submitted, delivered, late, and queue aggregates |
| 4_Site Activities | `5028018276` | Site-level execution evidence | Region/site execution aggregation only; no public site detail |
| SkyStation Inventory | `5028042389` | Fleet and asset state | Readiness, maintenance, and asset-family aggregates |
| 7_Incident Logs | `5030309792` | Asset/site incident state | Aggregate incident/open-attention counts only |
| 6_Daily Work Tracker | `5031430709` | Internal dated work occurrences | Excluded from public delivery metrics unless a future approved projection explicitly includes it |
| Work Repository | `5029561760` | Durable work definitions | Protected operational context; not a public delivery source |

Customer Repository, Customer Repository subitems, service intake, billing, and raw relations may support protected projections, but customer identity and financial detail are excluded from the public surface.

---

## 4. Join and lineage rules

### Authoritative join keys

- Monday board ID
- Monday item ID
- Monday group ID where category context is needed
- Monday People ID
- Monday board-relation target board ID and target item ID
- Explicit source relation column

### Forbidden joins

The public projection must not join records using:

- Similar item names
- Customer-name text
- Site-name text
- Location text
- Same owner name
- Same date
- Nearby group position
- Mirror text without the underlying relation ID

If the explicit relation is missing or points to an unexpected board, the record becomes `needs_review` and is excluded from a confident public metric.

### Lineage retained internally

Every aggregate should be traceable to its contributing source IDs in the protected backend. The public response can expose only a safe freshness/provenance label such as `Source snapshot · updated 09:35 UTC`, not raw IDs or internal links.

---

## 5. Required public state model

Every page and every prominent metric needs a visible state treatment.

| State | Meaning | Public treatment |
|---|---|---|
| Current | Source is fresh and validation passed | Show aggregate |
| Stale | Source exists but is outside freshness threshold | Show value only with stale label, or suppress if misleading |
| Partial | Some approved source inputs are missing | Show partial label and bounded aggregate |
| Needs review | Contradictory relation, date, status, or required field | Show review count/queue, not confident completion |
| Unavailable | Adapter/API/source failed | Show unavailable state; no fixture fallback |
| No data | Valid source returned no applicable rows | Show no-data explanation, not zero by implication |
| Awaiting confirmation | Record exists but required source state is blank/ambiguous | Keep separate from available, ready, done, or complete |

Colour never carries meaning alone. Every status has text and, where useful, a count.

---

# 6. Page-by-page dashboard brief

The page names below are the current six-screen information architecture. The next design pass should follow Sai's page-specific direction before implementation. This section defines what each page must be able to show and where it comes from.

## Page 01 — Operations Pulse

### Viewer question
Is the operation moving, and what deserves attention now?

### Primary signal
A single composite or explicitly named operational-health signal. The formula must be documented before use. It must not be a hand-waved blend of unrelated percentages.

### Required visible elements

- Reporting period and operating timezone.
- Source freshness/state.
- Planned activity count.
- Executed flight count and execution rate.
- Processing/QA-ready count where the stage contract is valid.
- Report-submitted and customer-ready output count.
- Attention count split into evidence, review, source, blocker, or stale categories.
- One plain-language interpretation sentence.
- Public boundary label: aggregates only; internal records protected.

### Source inputs

- Activity Repository: planned/reference rows, cadence, explicit customer relation where needed.
- Flight Operations: Scheduled Date, Flight Status, Conducted By, Activity Repository relation, Blocker, Completion Date.
- Processing and QA: Processing Status, relation, blocker, QA checks, evidence/file state.
- Report Submission: Submission Status, report dates, report link state, blocker, relation, processed-by state.
- Snapshot/validation service: freshness, source state, unresolved lineage, duplicate checks.

### Calculation rules

- Planned means planning-source rows in the selected period; it does not mean flown.
- Executed means a valid Flight Operations row with authoritative execution/completion evidence according to the approved status contract.
- Reported means a valid Report Submission state; a date alone does not prove delivery.
- A completed report without a required link becomes `needs_review` where the contract requires a link.
- Do not double-count the same operational chain across stage boards; use explicit relation lineage and unique source IDs.

### Do not show

Names, customers, sites, raw blockers, board IDs, links, internal notes, billing values, or a person ranking.

---

## Page 02 — Delivery Flow

### Viewer question
Where are items accumulating between plan and customer-ready delivery?

### Required visible elements

- A six-stage flow: mapped/planned → scheduled → flown → processed/QA → reported → delivered.
- Stage counts and conversion rates.
- Current gate/constraint count.
- Unresolved-lineage count separate from operational backlog.
- Evidence/review queue count.
- A short interpretation of the largest visible gap.

### Source inputs

- Activity Repository: plan/reference stage.
- Flight Operations: scheduled/flown stage.
- Processing and QA: processing and QA stage.
- Report Submission: report submitted/delivered stage.
- Site Activities only where the approved workflow explicitly includes site execution.
- Incident Logs as a separate branch, never silently folded into delivery completion.

### Calculation rules

- A stage transition requires a valid source state and, where applicable, an explicit relation to the upstream activity.
- Missing relation = unresolved lineage, not a successful transition.
- A blocker is evidence of an attention state, not proof that the whole chain failed.
- Counts must use unique source-chain identity and preserve stage-specific IDs internally.

### Do not show

Raw item names, internal blocker text, owner names, source links, or customer-specific chain rows.

---

## Page 03 — Crew Presence

### Viewer question
Are teams present and available for current operating demand?

### Required visible elements

- Active-record denominator.
- Available, deployed, WFH, leave, and awaiting-confirmation aggregates where source states exist.
- Team-level aggregate breakdown.
- Snapshot date and source freshness.
- Classification coverage: classified active records / active records.
- Clear distinction between presence and performance.

### Source inputs

- SkyStation Crew Repository: active/historical treatment, team/group, availability status, role, region context.
- People IDs and group IDs for protected joins.
- Daily Work Tracker only for protected work-occurrence views; activity records must not infer availability.

### Calculation rules

- Terminated/Resigned historical records are excluded from active denominator by source-backed state.
- Blank or malformed availability remains awaiting confirmation.
- Work activity does not prove presence, utilization, capacity, or performance.
- Public output is aggregate by team or safe group; no public person names.

### Do not show

Employee names, individual schedules, person-level workload, performance scores, manager notes, or monthly 1:1 history.

---

## Page 04 — Geographic Operations

### Viewer question
Where is work happening, and where is operating pressure concentrated?

### Required visible elements

- Region-level coverage, not a customer/site directory.
- Active regions and completed/in-progress counts.
- Region status: on track, attention, constrained, or review.
- Weather/field-constraint aggregate where supported by source evidence.
- Public-safe geographic interpretation.
- Source/freshness state.

### Source inputs

- Site Activities: execution dates and explicit activity relations.
- Activity Repository: region/customer context only where relation-backed and approved for public aggregation.
- Crew Repository: region context only for aggregate crew views.
- Incident Logs: region-safe incident counts where approved.

### Calculation rules

- Region is derived from an approved source field or relation, not guessed from customer/site text.
- Exact customer/site names are suppressed.
- A missing region becomes unclassified/review, not a guessed region.
- Weather and field constraints must retain source evidence and category definitions.

### Do not show

Maps with precise site coordinates, customer names, site names, asset serials, internal incident narratives, or security-sensitive locations.

---

## Page 05 — Reporting Outcomes

### Viewer question
Are reports reaching customer-ready state on the expected cadence?

### Required visible elements

- Planned versus submitted output trend.
- Submission count and timeliness rate.
- Open queue split by evidence, review, source, and blocker where available.
- Period selector with authoritative dates documented.
- T+1 or equivalent timeliness label only if the contract is approved.
- A clear distinction between submitted, delivered, and customer-ready.

### Source inputs

- Report Submission: Submission Status, report/submission dates, DA and processing dates, Report Link, blocker, Activity relation, processed-by state.
- Processing and QA: QA/evidence readiness.
- Activity Repository: plan/cadence reference where used.
- Snapshot validation: missing link, late date, relation, and freshness checks.

### Calculation rules

- A report is submitted only when the approved Submission Status says so.
- A report is customer-ready only when the approved evidence and status contract passes.
- A link is evidence, not a replacement for status; a status is not a replacement for required evidence.
- Missing report link on a completed row becomes review if the contract requires it.
- Do not call a submission late without an approved deadline and authoritative dates.

### Do not show

Report URLs, customer names, internal report notes, employee names, raw blockers, or confidential file metadata.

---

## Page 06 — Fleet & Readiness

### Viewer question
Is the fleet ready for planned demand, and what maintenance attention exists?

### Required visible elements

- Ready, maintenance, out-of-service, review/unclassified counts.
- Readiness percentage with denominator.
- Asset-family aggregate breakdown.
- Open incident aggregate.
- Maintenance attention aggregate.
- Planned-demand coverage interpretation.
- Explicit “no serials / public aggregate” boundary.

### Source inputs

- SkyStation Inventory: item/group, explicit type/model, condition, location, maintenance fields, battery cycles where approved, customer/site relations, asset identity.
- Incident Logs: incident state, severity, closure/verification state, asset relation.
- Customer/SkyStation relations only for protected joins; public output is aggregate.

### Calculation rules

- Blank condition is review/unclassified, not Ready.
- Location text cannot create customer ownership.
- V2/V3 or model slices require an explicit source model/version field; do not infer from partial names.
- Asset readiness and deployment are separate dimensions.
- Incidents are not automatically maintenance and maintenance is not automatically an incident.
- Readiness percentage must state the denominator and exclude invalid/unclassified records from confident ready totals.

### Do not show

Serial numbers, exact asset locations, customer assignment, internal condition notes, incident RCA, owner names, or protected links.

---

## 7. Data requirements by layer

### Ingestion layer

- Read board metadata and schema before adapter execution.
- Capture board ID, item ID, group ID, column ID, raw value, source updated timestamp, relation targets, People IDs, files, and URLs.
- Preserve blank values and raw status labels.
- Never mutate Monday during discovery or ingestion.

### Normalization layer

Every normalized record must include:

- `schema_version`
- `source_provider`
- `source_board_id`
- `source_item_id`
- `source_group_id`
- `source_updated_at`
- `source_url` in protected storage
- board-specific normalized fields
- `validation_issues[]`
- `needs_review`
- explicit relation arrays
- authoritative dates by field name

### Validation layer

Validate:

- duplicate source IDs
- expected relation target board IDs
- missing required statuses
- date parse and timezone
- impossible date ordering
- evidence requirements
- contradictory states
- unexpected asset/customer relations
- stale source thresholds
- incomplete active crew availability
- report completion without required link/evidence

### Projection layer

Projection code must:

- aggregate only approved fields
- redact protected dimensions before API delivery
- retain calculation explanations
- return source state and freshness
- include period and timezone
- avoid fixture fallback when source is unavailable
- expose a safe `quality_summary` rather than raw internal diagnostics

### Presentation layer

Every page must show:

- page purpose
- period
- source/freshness state
- denominator for percentages
- status text alongside colour
- a plain-language interpretation
- public boundary label

---

## 8. API/projection contract proposal

```json
{
  "schema_version": "public_dashboard.v1",
  "projection": "operations_pulse",
  "period": {"key": "month_to_date", "timezone": "Asia/Kolkata"},
  "data_state": "current",
  "source_updated_at": "2026-09-17T09:35:00Z",
  "snapshot_updated_at": "2026-09-17T09:36:12Z",
  "quality_summary": {
    "records_considered": 0,
    "records_excluded": 0,
    "needs_review": 0,
    "stale_sources": 0
  },
  "public_boundary": "aggregate_only",
  "metrics": {},
  "interpretation": "",
  "validation_issues": []
}
```

The public API should never return raw Monday board IDs, raw item IDs, People IDs, credentials, internal notes, customer names, serial numbers, or protected links. Those remain in the protected evidence layer.

---

## 9. Freshness and period rules

- Pick one operating timezone and use it on every page.
- `Today` means the selected local calendar date in that timezone.
- `This week` means Monday through Sunday unless product direction changes it explicitly.
- `This month` means the first through last local calendar day of the month.
- Each metric declares its authoritative date field: Scheduled Date, Activity Date, DA Start Date, Transfer Date, Report Submission Date, Completion Date, or another approved field.
- Never mix dates silently inside one rate.
- Never label a snapshot live if it is synthetic, stale, partial, or source-unavailable.

---

## 10. QA and acceptance checklist

### Content

- All six screens answer one clear public question.
- Every number has a label, period, denominator, and source role.
- Planned, executed, processed, reported, delivered, and ready are distinct.
- No protected person, customer, asset, billing, or evidence detail leaks.

### Source integrity

- Browser makes no Monday requests.
- API returns source state and freshness.
- Explicit relation IDs are used for joins.
- Missing/contradictory fields become review states.
- No fixture fallback masks unavailable data.

### Display behavior

- Each screen fits one viewport at the intended display aspect.
- Screen rail, previous/next, pause, auto-cycle, hidden-tab pause, restart, and reduced-motion behavior work.
- Mobile/narrow layout has no horizontal overflow.
- A screen transition never leaves a blank final state.
- Public Dashboard is reachable from the welcome page.
- Internal portal does not expose a redundant Public Dashboard or Manager Vault tab.

### Release evidence

- Hosted URL checked after propagation.
- All six screen headings checked after transition completion.
- Console errors captured and resolved.
- Screenshot captured for each screen at desktop and mobile sizes.
- Projection contract and source map versioned with the implementation.

---

## 11. Decisions needed from Sai before the next build

For each page, specify:

1. The visual metaphor or layout direction.
2. The one primary question the first viewport must answer.
3. The exact metrics and denominator.
4. The source-backed fields allowed in the public projection.
5. The interpretation sentence or rule.
6. The states that should show as current, stale, review, unavailable, or no data.
7. Any animation, cycling, or interaction behavior.
8. Any public-safe redactions beyond the baseline above.

Until those directions arrive, the current public wallboard should be treated as a disposable placeholder for replacement, not as the final product design.

---

## Source references

- `docs/product-requirements.md`
- `docs/data-contract.md`
- `docs/monday-source-map.md`
- `docs/production-readiness.md`
- `/opt/data/tmp/portal-card-logic.md`
- `/opt/data/tmp/portal-audit-addendum.md`
