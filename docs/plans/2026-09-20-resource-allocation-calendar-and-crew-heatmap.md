# Resource Allocation Calendar and Crew Work Heatmap Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Add a source-grounded resource allocation calendar to the Central Dashboard overview and a person-level work heatmap to the protected Crew Deep Dive without inventing utilization or performance metrics.

**Architecture:** The Central Dashboard will show a compact, read-only allocation calendar for the selected reporting window, summarizing dated work by person, team, customer/site, and operational state. The Crew Deep Dive will reuse the same normalized work records to show one selected person’s activity density by date and work type, with click-through to the underlying worklist. Monday remains the source; the portal normalizes records behind the protected API and renders explicit stale, unavailable, needs-review, and synthetic-preview states.

**Tech Stack:** Existing `rebuild-preview.html` preview shell, protected `scripts/portal_server.py`, normalized JSON snapshots under `data/`, pure aggregation in `scripts/portal_metrics.py`, and pytest coverage in `tests/`.

---

## Product decisions

### Central Dashboard: Resource Allocation Calendar

Place this in the Central Dashboard overview, alongside the operating pulse and before secondary detail panels. Its question is: **who is committed to what, on which dates, and where are collisions or uncovered dates?**

- Default window: current week, with Today / This week / This month controls.
- Rows: crew members or operational teams, depending on the access context.
- Columns: dates in the selected window.
- Cell content: count of scheduled work items, with compact state markers for planned, in progress, blocked, completed, and needs review.
- Cell click: opens a filtered allocation worklist showing item name, work date, customer/site, owner(s), status, source board, and evidence link where available.
- Collision signal: multiple concurrent assignments on a person/date are flagged as a review state, not labelled as overload unless a capacity rule exists.
- Empty cell: means no matching source record in the selected window; it must not be described as leave, availability, or idle time.
- Public/client-safe mode: show aggregate resource coverage only; person names, owners, and internal work rows remain protected.

### Crew Deep Dive: Person Work Heatmap

Add this to the selected person’s deep-dive overview, below the person summary and before confidential performance/1:1 panels.

- Default view: last 30 days, with 7 / 30 / 90 day controls.
- X-axis: calendar dates.
- Y-axis: work categories or activity types, with an optional second mode grouped by customer/site.
- Cell intensity: count of source-backed work records, not a productivity score.
- Cell detail: date, work items, status distribution, source links, and whether the record is planned, executed, handed off, or needs review.
- Multi-owner work appears for every named contributor and carries a `shared` marker so counts are not misread as sole ownership.
- Missing or ambiguous owners remain visible as `Unassigned / needs review` in manager views.
- Click-through opens the selected person’s filtered worklist and preserves the selected date/category context.

## Data contract

Add a normalized work-allocation record derived from the Daily Work Tracker and linked Work Repository:

```json
{
  "source_item_id": "2863409765",
  "source_board_id": "5031430709",
  "work_repository_item_id": "2820847344",
  "name": "EV vehicle purchase",
  "work_date": "2026-09-20",
  "owner_ids": ["77996752"],
  "owner_names": ["Sai Akshobhyaa Vrinda"],
  "team": null,
  "customer": null,
  "site": null,
  "work_type": "One-time",
  "status": "Done",
  "shared_assignment": false,
  "evidence_url": null,
  "data_state": "current"
}
```

Rules:

- Join by Monday item IDs and People IDs, never display names alone.
- Preserve multiple owner IDs; do not collapse them to one owner.
- Keep Work Repository ownership as the baseline and retain Discord-derived contributors when the reconciliation has explicitly added them.
- Preserve nulls and emit `needs_review` for missing date, owner, relation, or status.
- Do not calculate utilization, capacity percentage, productivity, ranking, or performance from work counts.
- Source freshness must be shown beside both visuals.

---

## Implementation sequence

### Task 1: Freeze the interaction and access contract

**Files:** `docs/information-architecture.md`, this plan, `docs/data-contract.md`.

- Add the Resource Allocation Calendar to the Central Dashboard overview contract.
- Add Person Work Heatmap to the selected-person Crew Deep Dive contract.
- Record internal-only fields and public-safe aggregate behavior.
- Acceptance: route/access matrix states which users can see names, owners, work rows, and drilldowns.

### Task 2: Extend the work-tracker snapshot contract

**Files:** `scripts/sync_work_tracker.py` or the existing work-tracker adapter, `docs/data-contract.md`, `tests/`.

- Confirm the adapter requests Work Date, Owner, Status, Work Type, Details, Evidence link, and Work Repository relation.
- Normalize People values into stable Monday user IDs plus display names.
- Preserve all owner IDs for multi-owner rows.
- Add validation for missing dates, missing owners, duplicate source IDs, and broken repository relations.
- Acceptance: fixture tests cover Sai’s EV Vehicle Purchase row, a multi-owner row, and an unassigned/needs-review row.

### Task 3: Add pure allocation aggregations

**Files:** `scripts/portal_metrics.py`, `tests/test_portal_metrics.py`.

- Add `build_resource_calendar(records, start_date, end_date, scope)`.
- Add `build_person_work_heatmap(records, person_id, start_date, end_date, grouping)`.
- Return stable date columns, row identities, counts, status breakdowns, shared-assignment markers, and drilldown source IDs.
- Return explicit `unavailable` or `needs_review` states when the source snapshot is missing or invalid.
- Acceptance: aggregation tests prove multi-owner work appears for each contributor, null owners go to review, and counts never become utilization/performance scores.

### Task 4: Add protected API payloads

**Files:** `scripts/portal_server.py`, `tests/test_portal_server.py`.

- Add authenticated read-only endpoints for the normalized allocation payload or extend the existing work-tracker endpoint with named derived fields.
- Keep direct snapshot paths blocked and require the existing portal authorization boundary.
- Add bounded date-range and person filters; reject unbounded or malformed ranges.
- Return `source_state`, `last_synced_at`, and `data_state` alongside records.
- Acceptance: unauthenticated requests return 401, missing snapshots return an explicit unavailable state, and authorized responses contain no secrets.

### Task 5: Build the Central Dashboard calendar

**Files:** `rebuild-preview.html` or the current Central Dashboard entry artifact, shared styles within that file if it remains self-contained.

- Add the calendar panel to the overview composition, using the existing Skylark carbon/graphite surfaces and orange state accent.
- Add Today / This week / This month controls and a clear source/freshness label.
- Render row labels, date headers, compact state dots, collision/review states, and an empty-state legend.
- Wire cell clicks to the existing evidence drawer or a filtered worklist state.
- Keep synthetic preview data clearly labelled until the API is connected.
- Acceptance: date control changes the rendered window, cell click changes the detail context, and no person-level data appears in public-safe mode.

### Task 6: Build the Crew Deep Dive heatmap

**Files:** `rebuild-preview.html`, selected-person Crew Deep Dive markup and controller logic.

- Add 7 / 30 / 90 day controls and category/customer-site grouping.
- Render accessible cell labels with date, category, count, state, and shared-assignment status.
- Add a selected-cell detail panel and worklist drilldown.
- Preserve the existing role-lens, responsibility, review-history, and confidential 1:1 boundaries; the heatmap is operational evidence, not performance scoring.
- Acceptance: switching people updates the heatmap, filters preserve selection context, and confidential panels remain protected.

### Task 7: Add visual and browser regression coverage

**Files:** `tests/`, QA scripts or browser checks under the repository’s existing test workflow, `docs/plans/` evidence notes.

- Verify route navigation, calendar controls, heatmap controls, click-through states, protected/unavailable states, and console cleanliness.
- Verify 1920×1080, 1366×768, and narrow layouts; prevent calendar overflow from hiding dates.
- Verify reduced-motion mode preserves final chart states and removes decorative animation.
- Verify source labels distinguish current, stale, unavailable, needs review, and synthetic preview.
- Acceptance: browser checks prove the visual changed after each control action, not merely that the control exists.

### Task 8: Connect live source and publish separately

**Files:** sync adapter/runtime configuration, deployment entrypoint, release notes.

- Run live Monday readback through the server-side adapter only.
- Validate counts, People IDs, dates, owner propagation, multi-owner rows, and source freshness before rendering.
- Keep repository/push success separate from hosted Pages propagation.
- If the live source is unavailable, render an explicit unavailable state instead of fixture-looking live metrics.
- Acceptance: authorized runtime response, browser rendering, public/client-safe boundary, and hosted deployment are each verified independently.

---

## Acceptance checklist

- The Central Dashboard answers who is allocated to what and when within five seconds.
- The selected person’s Deep Dive answers when and what kind of work they handled without implying productivity.
- Every chart cell has a source-backed drilldown or explicit unavailable/needs-review state.
- Multi-owner work is shown for every named owner and marked shared.
- The calendar never turns an empty day into an availability claim.
- The heatmap never turns work count into utilization, ranking, or performance.
- Public views contain aggregate resource coverage only; protected views enforce authorization server-side.
- Source freshness, exact counts, and time window are visible on both surfaces.
- Existing route, tab, drawer, Manager Vault, public wallboard, and reduced-motion behavior continue to pass regression checks.
