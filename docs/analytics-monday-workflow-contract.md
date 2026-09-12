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
Activity Repository (reference / planned)
                 │ explicit board relation
                 ▼
Flight Operations (field execution)
                 │ shared Activity Repository relation; no direct Flight → QA relation
                 ▼
Processing & QA (processing, checks, files)
                 │ shared Activity Repository relation; no direct QA → Report relation
                 ▼
Report Submission (delivery evidence)
                 │
                 ├── follow-up / carry-forward
                 ├── blocker / stuck branch
                 ├── missing relation branch
                 ├── missing date branch
                 └── missing evidence branch
```

The shared Activity Repository relation is the join key currently available across the execution boards. The adapter must preserve board-specific item IDs and report lineage confidence. It must not infer direct handoffs from item names, mirror text, or nearby dates.

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
