# Analytics Monday workflow contract

**Status:** DRAFT — source-grounded, pending Sai review  
**Readback date:** 2026-09-12  
**Workspace:** SkyStation Management (`1681624`)

## Purpose

Analytics must render the operational workflow from Monday records and stable relations. The 3D chart is a view of this contract; it must never maintain a second, independent workflow fixture once the protected adapter is connected.

## Source boards

| Logical role | Board | ID | Live item count | What it proves |
|---|---|---:|---:|---|
| Planning/reference anchor | SkyStation Activity Repository | `5027240228` | 93 | A configured site + activity combination, owner, cadence, active state, and source relation. It has no execution status or execution date. |
| Field execution | 1_Flight Operations | `5027240883` | 5 | Scheduled flight activity, flight status, conducted-by, blocker, processing assignment, completion date, and relation to Activity Repository. |
| Processing and QA | 2_Processing and QA | `5027256991` | 12 | DA start, transfer, processing start, processing status, QA checks, files, blockers, and relation to Activity Repository. |
| Delivery | 3_Report Submission | `5027265596` | 267 | Submission status, blockers, report link, QA/progress checks, DA and processing dates, report submission date, and relation to Activity Repository. |

## Canonical topology

```text
ORDER LIFECYCLE
New SkyStation order
        │
        ▼
-1_SkyStation Hardware Installation / Disassembly
        │
        ▼
0_Overview Mapping
        │
        ▼
SkyStation Activity Repository
        │
        ├── Recurring Activities and/or Service Requests
        │       │
        │       ├── 1_Flight Operations
        │       │       ├── 2_Processing and QA
        │       │       └── 3_Report Submission → customer delivery
        │       │
        │       └── 4_Site Activities
        │               └── recurring maintenance and cleaning
        │
        ├── 5_Night Security and Surveillance
        │       └── independent night-team workflow
        │
        ├── 6_Work Tracker
        │       └── one-time, solution-development, and process-improvement work
        │
        └── 7_Incident Logs
                └── incident repository, including emergencies and landings
```

Supporting context boards such as SkyStation Inventory and SkyStation Customer Repository connect to the relevant operational records; they are not universal sequential stages.

The main report-producing handoff is `1_Flight Operations → 2_Processing and QA → 3_Report Submission`. Site Activities, Night Security, Work Tracker, and Incident Logs remain distinct workflows with their own state semantics.

## Node definitions

1. **Reference / planned** — Activity Repository item with `Active = Yes`, `On Demand`, or an explicitly selected source scope. `Active = No` and historical `Completed` rows remain visible only when the selected view requires them. Weekly Frequency and Assignment Date define planning context; Planned Quantity is scope metadata and is excluded from activity counts.
2. **Field execution** — Flight Operations item identified by its own `Activity ID`, `Scheduled Date`, and `Flight Status`. `Done` is execution completion; `Working on it`, `Stuck`, `Not Done`, and `Partial Completion` are distinct states. Missing scheduled dates are `Deadline unknown`.
3. **Processing / QA** — Processing and QA item identified by its own `Activity ID`, DA Start Date, Transfer Date, Processing Start Date, Processing Status, individual QA checks, Files, Blocker, and Activity Repository relation. `Done`, `Partially Completed`, `Request for Review`, `Working on it`, and `Stuck` remain separate states.
4. **Delivery** — Report Submission item identified by its own `Activity ID`, Submission Status, report link, progress-report check, dates, blocker, and Activity Repository relation. `Done`, `Working on it`, `Stuck`, `Not Done`, and `Partial Completion` remain separate states.

## Exception branches

- **Held / blocked:** `Stuck` or a non-empty blocker column; show the exact blocker category when available.
- **Returned for review:** `Request for Review`, `Partial Completion`, or failed QA check; show the owning board and field.
- **Missing lineage:** no Activity Repository relation or an unexpected relation target; mark `Needs review` and do not count as a confirmed handoff.
- **Missing evidence:** no file on Processing and QA or no report link on Report Submission where the workflow requires it; show `Unavailable`/`Needs review`, never infer completion.
- **Missing date:** absent or invalid stage dates; show `Deadline unknown`, never `Overdue`.
- **Carry-forward:** a later-stage item exists without a matching upstream stage for the selected period; show it as an unresolved lineage branch rather than a successful conversion.

## Period semantics

The protected adapter filters by stage-appropriate dates before aggregation:

- **Today:** intraday buckets for the selected calendar date.
- **This week:** Monday through Sunday using the relevant stage date.
- **This month:** week-of-month buckets `01–07`, `08–14`, `15–21`, `22–28`, `29–30`.

Each stage reports `source_count`, `confirmed_handoff_count`, `exception_count`, `missing_evidence_count`, and `data_state`. A stage conversion is calculated only from deterministic shared-relation matches and valid dates. Zero denominators, duplicates, conflicting statuses, future records, and unsupported fields resolve to `Needs review` or `Unavailable`.

## Current readback snapshot

The 2026-09-12 read-only audit found:

- Activity Repository: 93 rows; 29 `Yes`, 39 `On Demand`, 13 `No`, 12 `Completed`.
- Flight Operations: 5 rows; all 5 `Done`; 3 missing Scheduled Date; 5 missing Processing Assign.
- Processing and QA: 12 rows; 8 `Done`, 3 `Request for Review`, and 1 additional non-final review-state record; several records have no Activity Repository relation, dates, or files.
- Report Submission: 267 rows; 159 `Done`, 102 `Stuck`, 4 `Not Done`, 2 `Working on it`; 14 missing Activity Repository relation; 50 missing DA Start Date; 116 missing Report Submission Date.

These figures are an audit snapshot, not the portal's permanent fixture. The future adapter must recalculate them from live readback on every sync.

## Implementation boundary

The public/static preview must not call Monday directly or contain credentials. The production path is a protected server-side read-only adapter that returns a versioned normalized model with `source_board_id`, `source_item_id`, relation IDs, `source_updated_at`, `synced_at`, and explicit data-quality states. Until that adapter exists, the preview may show synthetic/demo values only when clearly labelled as demo data; the topology and field names must follow this contract.

## Monday integration contract

The implemented adapter is `scripts/sync_workflow_network.py`. It composes the existing read-only board adapters and writes `data/workflow_network.snapshot.json`; the protected runtime exposes that snapshot at `/api/workflow-network`. It must never be called from public browser JavaScript with a Monday token.

The adapter fetches every page from each source board before aggregation. A first page is never treated as the complete board. It preserves Monday board and item IDs, People IDs, and Board Relation target IDs; names and mirror text are display values only and cannot establish a join.

The normalized model is `workflow-network.v1` and contains:

- stage summaries for Activity Repository, Flight Operations, Processing & QA, Report Submission, Incident Logs, and derived Customer Delivery;
- per-stage source item IDs, record counts, status counts, review counts, and source board IDs;
- semantic edges for `Activity Repository → Flight Operations`, `Flight Operations → Processing & QA`, `Processing & QA → Report Submission`, `Report Submission → Customer Delivery`, and `Flight Operations → Incident Logs`;
- relation evidence showing which source item and Activity Repository item support a handoff;
- node attention/red state and aggregate quality counts;
- explicit `data_state` and validation failures.

Customer Delivery is derived only from Report Submission records with `status = Done`. It is not evidence of a confirmed Customer Repository relation. Incident Logs is an outward branch from Flight Operations; the adapter must reject any Activity Repository → Incident Logs edge.

## Failure and data-quality semantics

The workflow must distinguish operational failure from incomplete evidence:

```text
confirmed blocked or failed handoff → red and flashing
needs review or incomplete evidence → amber / review state
working or in progress → workflow-family color
completed with required evidence → completed state
unrecognized or unavailable source state → needs_review / unavailable
```

`Stuck`, `Not Done`, `Blocked`, an unresolved blocker, failed QA, or an open incident can create an attention/red state only in the stage where the evidence exists. Missing dates, owners, relations, files, report links, or unfamiliar status labels are `Needs review`, not automatic failure. Missing dates render as `Deadline unknown`; they must never be rendered as `Overdue`.

A stage conversion is confirmed only when the source relation, stage identity, and relevant date/evidence fields support it. Carry-forward records, unexpected relation targets, duplicate source IDs, conflicting statuses, and zero-denominator calculations remain unresolved rather than being inferred from names or neighboring rows.

## Renderer and route safeguards

The existing WebGL topology, camera choreography, labels, and animation remain the presentation layer for this model. Live data may change node state, counts, attention, and connector emphasis, but it must not create unsupported topology or replace the shared node/edge model.

The renderer safeguards are:

- one canvas and one WebGL renderer per workflow surface;
- an idempotent `workflowRendererReady` guard that prevents duplicate animation loops on refresh or route changes;
- a visible-state retry after Analytics route activation so a hidden canvas cannot permanently miss initialization;
- one shared projection transform for spheres, links, particles, labels, and camera fitting;
- endpoint-based wide framing with projected-bounds centering and label clamping;
- dedicated Activity Repository framing that includes all inbound sources and their labels;
- explicit Incident Logs playback before Customer Delivery, using only the Flight Operations → Incident Logs branch;
- red flashing reserved for confirmed broken/incident paths, with the affected node, connector, and packet state driven from the same normalized state;
- pause/replay/loop behavior that does not spawn a second renderer or reset unrelated camera state.

## Runtime and security safeguards

The Monday credential is read only from runtime configuration. If it is absent, the adapter exits before making a request and reports that synchronization is pending. Credentials, API keys, OAuth secrets, passwords, tokens, and connection strings must never be written to snapshots, source files, logs, public HTML, or Discord.

The protected API must fail closed when the snapshot is absent, malformed, stale, or unauthorized. The public static preview must show an explicit unavailable/demo state rather than silently falling back to live-looking fixture values. Generated snapshots containing internal people or operational records are runtime-only and must not be committed to the public repository.

Every future sync must verify schema version, complete pagination, duplicate IDs, expected relation targets, stage-specific status rules, source counts, and snapshot freshness before the workflow view is allowed to consume the result. Monday mutations are outside this contract; this path is read-only.

## Verification record

The current implementation has been verified with:

- live authenticated Monday MCP schema and sample-record reads for the source boards;
- normalized-model contract tests for source IDs, relation preservation, status-derived red states, Customer Delivery derivation, unsupported edges, and missing-secret behavior;
- Python compilation and inline JavaScript syntax checks;
- protected endpoint registration at `/api/workflow-network`;
- lifecycle checks for visible-state retry and duplicate-renderer prevention.

Browser screenshot QA remains a separate requirement. Hosted source propagation and implementation markers do not constitute visual approval; a real browser pass must still confirm settled rendering, label readability, red flashing, narrow-screen behavior, and the complete playback cycle.
