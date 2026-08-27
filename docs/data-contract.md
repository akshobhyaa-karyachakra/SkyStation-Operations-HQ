# SkyStation portal data contract v1

Status: design baseline, read-only integration phase.

## Core rule

Monday is the source of truth for operational records. The portal consumes normalized records produced by a server-side sync. Frontend fixtures must not supply roster, ownership, status, dates, or KPI values for a source-backed view.

Every normalized record carries:

- `source_provider`: `monday`
- `source_board_id`
- `source_item_id`
- `source_updated_at`
- `synced_at`
- `data_state`: `current`, `stale`, `unavailable`, or `needs_review`

Monday item IDs, group IDs, People IDs, and board-relation IDs are join keys. Display names are never join keys.

## Entity: crew_member

Canonical source: `SkyStation Crew Repository` (`5030902067`).

| Normalized field | Monday source | Rule |
|---|---|---|
| `monday_item_id` | item ID | Required stable identity |
| `name` | Name | Display value only |
| `team_group_id` | item group ID | Canonical team key |
| `team_group` | item group title | Current group label |
| `official_role` | `text_mm6mk51e` | Preserve source text |
| `band` | `text_mm6mg4v2` | Preserve source text; no inferred band |
| `manager[]` | `multiple_person_mm6msyq2` | Monday People IDs and names |
| `team_lead` | `boolean_mm6m50k9` | Boolean |
| `region_location` | `text_mm6mx08z` | Preserve source text |
| `availability` | `color_mm6mamdg` | Status label from live schema |
| `historical` | derived from Terminated/Resigned | Exclude from active capacity by default |
| `daily_tracking_required` | `boolean_mm6mvm85` | Boolean |
| `start_date` | `date_mm6mm5pf` | Null when source is blank |
| `email` | `email_mm6mx3gz` | Null until confirmed |
| `notes` | `long_text_mm6mswwm` | Preserve source note |

Required invariants:

- 15 total records and 14 active records in the current snapshot.
- No duplicate Monday item IDs or names.
- Aarya Vira and Ammar Dali resolve to `group_mm6m3fvh` / `SkyStation Operations` in the current source.
- Historical records do not enter active-team metrics.

## Entity: planned_activity

Canonical source: `SkyStation Activity Repository` (`5027240228`). This is a static planning/reference board; it does not prove execution.

| Normalized field | Monday source | Rule |
|---|---|---|
| `monday_item_id` | item ID | Required identity |
| `name` | Name | Display value only |
| `customer_group_id` | item group ID | Customer grouping key |
| `customer` | group title | Preserve exact group label |
| `owner_user_ids` | `multiple_person_mm1g7qjb` | Monday People IDs |
| `co_owner_user_ids` | `multiple_person_mm1gvaap` | Secondary owner only |
| `activity_type` | `color_mm1gsat9` | Live status label |
| `active_state` | `color_mm1g3h74` | Yes / No / On Demand |
| `weekly_frequency` | `dropdown_mm3rv0jk` | Cadence source |
| `assignment_date` | `date_mm3t9qdk` | Planning/assignment date |
| `planned_quantity` | `text_mm1rrn73` | Preserve source text |
| `customer_relation_ids` | `board_relation_mm2qwdd3` | Relation-backed customer context |

`planned_activity` may be used to calculate expected work, but not completed work, actual execution, or report delivery.

## Entity: work_item

Execution sources are separate boards and are unified by stage, not by item name:

| Stage | Board | ID |
|---|---|---|
| `flight` | `1_Flight Operations` | `5027240883` |
| `site_activity` | `4_Site Activities` | `5028018276` |
| `processing_qa` | `2_Processing and QA` | `5027256991` |
| `report_submission` | `3_Report Submission` | `5027265596` |
| `work_tracker` | `6_Work Tracker` | `5029561760` |

Common fields:

- `source_board_id`, `source_item_id`, `name`
- `stage`
- `activity_repository_item_ids` from the board relation `board_relation_mm1gwp2a` where present
- `owner_user_ids` from the native People field or linked source owner, with the fallback documented per board
- `status`
- `planned_date`, `execution_date`, `completion_date`
- `blocker`
- `evidence_links`
- `source_updated_at`

A work item is considered linked only when the Monday relation returns the linked item ID. Mirror text is presentation-only and cannot establish a join.

### Board-specific fields

- Flight Operations: `date4` Scheduled Date, `color_mm1g9w3q` Flight Status, `multiple_person_mm1ra8c2` Conducted By, `multiple_person_mm1h1fts` Processing Assign, `date_mm1h9es2` Completion Date, `dropdown_mm1s419z` Blocker.
- Processing & QA: `date_mm1h5gsw` DA Start Date, `date4` Transfer Date, `date_mm1h7a47` Processing Start Date, `color_mm1g9w3q` Processing Status, `multiple_person_mm22hxev` Assigned To, `file_mm65zqx` Files, `dropdown_mm1skymk` Blocker.
- Report Submission: `date_mm1h5gsw` DA Start Date, `date4` DA End Date, `date_mm1h7a47` Processing Start Date, `date_mm1h35kq` Processing End Date, `date_mm1ha6yw` Report Submission Date, `color_mm1g9w3q` Submission Status, `link_mm1htkk8` Report Link, `multiple_person_mm22yh1f` Processed By.
- Site Activities: `date_mm3stezz` Planned Date, `date4` Activity Date, `multiple_person_mm1ra8c2` Visit By, `dropdown_mm1s419z` Blocker. Its relation may target both Activity Repository (`5027240228`) and Customer Repository (`5028043141`), so relation target IDs must be inspected before normalization.

## Entity: handoff

A handoff is derived only from explicit relations and date/status evidence:

```text
planned_activity
  → flight or site_activity
  → processing_qa
  → report_submission
  → client_ready
```

The portal must distinguish:

- missing execution row;
- execution row exists but is not linked to the plan;
- upstream stage complete but downstream row absent;
- downstream row exists but is awaiting evidence;
- source data unavailable.

No handoff is created from matching names, site text, or display labels alone.

## Freshness and failure states

- `current`: latest valid snapshot is within the configured freshness window.
- `stale`: last valid snapshot exists but is older than the window.
- `unavailable`: no valid snapshot is available.
- `needs_review`: snapshot exists but a contract invariant failed.

## Entity: inventory_asset

Canonical source: `SkyStation Inventory` (`5028042389`). The asset model preserves physical inventory identity and source-backed relations without inferring customer ownership from location or names.

Every record uses schema `inventory_asset.v1` and carries the source item/group IDs, asset type, serial or explicit unit identifier, condition, location, maintenance dates, battery cycle count where present, and separate relations to SkyStation Customer Repository (`5028043141`), Customer Repository subitems (`5028043142`), and Incident Logs (`5030309792`). Missing type/serial identifiers and unexpected relation targets are `needs_review`; unmatched stock remains unlinked.

## Entity: incident

Canonical source: `7_Incident Logs` (`5030309792`). Every record uses schema `incident.v1` and preserves the incident reference, incident/site/asset context, source and evidence links, owner/reporters/operators, status/severity, RCA and report-quality states, closure dates, closure blocker, escalation, and next-action fields. Inventory, customer, and Activity Repository relations are separate ID-backed arrays. “Closed”, “Final”, or “Resolved - Verify” are source states; the adapter does not infer RCA, prevention, verification, or closure evidence.

When a sync fails, serve the last valid protected snapshot with its age and error state. Never silently use hardcoded frontend values.

## Customer-safe projection

Customer endpoints receive only approved customer fields and source-derived operational summaries. Internal owner identities, board IDs, workflow shorthand, internal notes, unresolved discussions, and raw asset details are excluded at normalization/API projection time, not merely hidden in the UI.
