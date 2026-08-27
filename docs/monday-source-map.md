# Live Monday source map

Captured from authenticated Monday read-only board metadata on 2026-08-27. IDs below are verified board IDs; column IDs are verified from each board schema and must be re-read before mutations.

| Purpose | Board | Board ID | Current items | Key relation / identity |
|---|---|---:|---:|---|
| People master | SkyStation Crew Repository | `5030902067` | 15 | item group + People Manager |
| Planning master | SkyStation Activity Repository | `5027240228` | 72 | `board_relation_mm2qwdd3` → Customer Repository |
| Flight execution | 1_Flight Operations | `5027240883` | 21 | `board_relation_mm1gwp2a` → Activity Repository |
| Processing and QA | 2_Processing and QA | `5027256991` | 14 | `board_relation_mm1gwp2a` → Activity Repository |
| Report delivery | 3_Report Submission | `5027265596` | 154 | `board_relation_mm1gwp2a` → Activity Repository; service intake relation |
| Site execution | 4_Site Activities | `5028018276` | 44 | `board_relation_mm1gwp2a` → Activity/Customer Repository |
| Internal work | 6_Work Tracker | `5029561760` | not captured in this pass | requires schema read before adapter |
| Fleet source | SkyStation Inventory | `5028042389` | not captured in this pass | requires schema read before adapter |
| Incidents | 7_Incident Logs | `5030309792` | not captured in this pass | requires schema read before adapter |

## First connector slice

Build and validate adapters in this order:

1. Crew Repository: complete and source-backed.
2. Activity Repository: planning records only; no execution claims.
3. Flight Operations: scheduled execution and owner/status evidence.
4. Processing & QA: downstream handoff and processing evidence.
5. Report Submission: delivery evidence and report links.
6. Site Activities: separate execution path; inspect relation target before joining.

## Known schema facts

- Crew team is the Monday group, not a redundant Team column.
- Crew `Manager` is a People column: `multiple_person_mm6msyq2`.
- Crew `Availability` is a Status column: `color_mm6mamdg`.
- Activity Repository has `Owner`, `Co Owner`, `Activity Type`, `Active`, `Weekly Frequency`, `Assignment Date`, and Customer Repository relation fields.
- Flight Operations uses `Conducted By`, `Flight Status`, `Scheduled Date`, `Processing Assign`, `Blocker`, and `Completion Date (Automated)`.
- Processing & QA uses `Assigned To`, `DA Start Date`, `Transfer Date`, `Processing Status`, `Files`, and blocker fields.
- Report Submission uses `Submission Status`, report dates, `Report Link`, `Processed By`, and relations to Activity Repository and Service Request Intake.
- Site Activities uses `Planned Date`, `Activity Date`, `Visit By`, and a relation that can target both Activity Repository and Customer Repository.

## Processing & QA readback (2026-08-27)

The authenticated read-only fetch returned 14 items from `2_Processing and QA`. The current board includes explicit Activity Repository relations for most work, CAD assignees, DA/transfer/processing dates, Processing Status, blocker values, and separate QA checks for ortho, shapefiles, CSV, and IDT.

Two completed array-layout records currently have no Activity Repository relation. The adapter keeps them as `needs_review`; it does not attach them to a similarly named planning row. Several other rows have processing dates but remain `Working on it`, which is valid workflow evidence and must not be converted into completion merely because a date exists.

## Activity Repository readback (2026-08-27)

The authenticated read-only fetch completed across three pages: 25 + 25 + 22 = 72 items. The current data contains:

- recurring work marked `Yes` and `No`, plus `On Demand` rows;
- activity types including Worksite Monitoring, AC Monitoring, DC Monitoring, O&M Inspection, One Time Activity, Security and Surveillance, Site Activity/ Visit, and hardware support/installation work;
- 22 items without a customer relation, including internal/support work, so those records must remain visible as `needs_review` rather than being assigned to a customer by name;
- multi-customer relation rows for shared hardware/support activities;
- missing cadence and assignment dates on some records;
- owner values that include names or email-like text in the current board representation, which the server adapter must resolve to Monday People IDs when the GraphQL response exposes them and otherwise preserve as unresolved owner data.

The adapter acceptance target is a normalized snapshot with 72 unique source item IDs, no inferred customer joins, explicit `needs_review` flags for missing activity type/state/customer relation, and no claim that a planned row represents completed work.

## Report Submission readback (2026-08-27)

The authenticated read-only fetch completed across four pages: 50 + 50 + 50 + 4 = 154 items. Report Submission carries an explicit Activity Repository relation and, for selected customer requests, a separate Adani Service Request Intake relation. Delivery state, blocker, report link, processing/report dates, and assignee evidence are preserved independently.

Completed rows can have a missing report link, while some report links point to Spectra inspection or layer views rather than a report URL. The adapter therefore preserves the exact link and marks `Done` without a link as `needs_review`; it does not infer delivery from a date or from the item name. Stuck and Not Done rows retain the board's blocker text, including customer, network, wind, power, battery, sensor, and array-layout reasons.

## Site Activities readback (2026-08-27)

The authenticated read-only fetch returned 44 items in one page. The `SkyStation Activity Repository` relation is configured to allow targets on Activity Repository (`5027240228`) and a second board (`5028043141`); the fetched rows in this pass point to Activity Repository. The adapter preserves target board IDs and keeps any second-board relation separate instead of treating it as an Activity Repository join.

Site Activities has explicit Planned Date, Activity Date, Visit By, and blocker fields, but no usable status column in the verified schema. Activity Date is therefore retained as execution evidence, while missing Activity Date is `needs_review`; a blocker without a status is also surfaced as a source-schema inconsistency. Historical Tarun MJ assignments remain source evidence and are not converted into current capacity claims.

## Work Tracker readback (2026-08-27)

The authenticated read-only fetch returned 43 items in one page from `6_Work Tracker`. This is an internal solution-development and process-work board with Work ID, start/end dates, Task Status, Priority, People owners, Notes, Category, and file/text evidence. It has no customer or execution-board relation, so its records remain `internal_work` and are excluded from customer delivery, flight, and report-completion metrics unless a future explicit relation is added.

Observed statuses include In Progress, Done, Stuck, Not Started, and Partially Completed. The adapter preserves source status and ownership, marks active work without an owner for review, and flags Done items without an end date; it does not infer customer, project, or delivery meaning from task names, categories, notes, or file links.

## Inventory readback (2026-08-27)

The authenticated read-only fetch returned 121 items from `SkyStation Inventory` (`5028042389`) across SkyStations, Drones, Batteries, Relay stations, Hardware, Memory Cards, Routers, CCTV Cameras, Remote Controls, and Installation Kits. Stable source identity is the Monday item ID plus the source serial/unit field; group ID/title is retained as inventory category context.

The board has separate relations to the SkyStation Customer Repository (`5028043141`), Customer Repository subitems (`5028043142`), and Incident Logs (`5030309792`). The adapter preserves each relation type and target ID independently, along with condition, location, maintenance, and battery cycle fields. It leaves stock or incomplete rows unlinked and marks missing type/serial identifiers or unexpected relation targets as `needs_review`; location text alone is never used to infer customer ownership.

## Incident Logs readback (2026-08-27)

The authenticated read-only fetch returned 10 items from `7_Incident Logs` (`5030309792`). The board contains explicit fields for incident reference/date/time, site and asset context, error description/resolution, owner, source/evidence links, severity, incident status, RCA confirmation, repeat state, report quality, target/actual closure dates, closure blocker, escalation, and missing-to-close checklist.

The adapter preserves separate relations to Inventory (`5028042389`), Customer Repository (`5028043141`), and Activity Repository (`5027240228`), plus distinct reported-by and actual-operator people fields. It flags missing references/statuses, closed rows without closure dates or final evidence, and unexpected relation targets; it does not infer RCA, CAPA/prevention, verification, or closure from neighboring fields.

## Source map rules

- Treat board metadata as live configuration; do not hardcode column positions.
- Re-read schemas before each adapter rollout because users can edit columns/views.
- Use board relation IDs and People IDs for joins. Mirror text is not authoritative.
- Preserve missing values as null and surface them as data-quality states.
- Do not mutate any board during source-map discovery.
