# Full portal backend map

Status: inventory completed  
Reviewed: 2026-09-27

## Shared target flow

```text
Monday / approved source
  -> server-side adapter
  -> raw snapshot
  -> domain normalization
  -> validation and quality state
  -> shared snapshot manifest
  -> public/protected projection
  -> portal route or wallboard card
```

The browser must never call Monday. Frontend fixtures are preview-only and must not silently replace an unavailable source snapshot.

## Domain inventory

| Portal area | Primary source | Existing adapter | Current runtime state | Next implementation |
|---|---|---|---|---|
| Activity Tracking | SkyStation Activity Repository `5027240228`; Flight Operations; Processing/QA; Report Submission; Site Activities | `sync_activity_repository.py`, `sync_flight_operations.py`, `sync_processing_qa.py`, `sync_report_submission.py`, `sync_site_activities.py` | Adapters and snapshot-oriented server routes exist; cross-domain chain projection needs one manifest and verified joins | Build chain-level normalized tables and one activity projection with explicit lineage/quality states |
| Flight Operations | `1_Flight Operations` `5027240883` plus Activity Repository relation | `sync_flight_operations.py` | Adapter exists; production API/database promotion is incomplete | Normalize scheduled/executed dates, status, owner, relation, blocker, and execution quality |
| Processing and QA | `2_Processing and QA` `5027256991` plus Activity Repository relation | `sync_processing_qa.py` | Adapter exists; QA stage projection needs cross-board validation | Normalize processing dates, QA checks, blocker, relation, and needs-review cases |
| Report Submission | `3_Report Submission` `5027265596` plus Activity/Service Intake relations | `sync_report_submission.py` | Adapter exists; completion and T+1 metrics need published projection | Normalize submission status, evidence/link quality, planned-vs-submitted, and deadline state |
| Site Activities | `4_Site Activities` `5028018276` | `sync_site_activities.py` | Adapter exists; source has execution evidence but no reliable status column | Preserve planned/activity/visit dates and expose missing activity date as review |
| Inventory | SkyStation Inventory `5028042389`; customer, subitem, incident relations | `sync_inventory.py` | Adapter exists; schema/source readback must be reverified before production use | Normalize asset identity, condition, maintenance, relations, and readiness projection |
| Incidents | `7_Incident Logs` `5030309792` plus inventory/customer/activity relations | `sync_incident_logs.py` | Adapter exists; protected evidence projection needs validation | Normalize severity, status, RCA, closure, escalation, and evidence completeness |
| Crew Repository | SkyStation Crew Repository `5030902067` | `sync_crew_repository.py` | Snapshot adapter exists; current public crew directory is source-backed separately | Promote active roster and role/team projection to shared store |
| Crew Daily Availability | Crew Daily Availability `5031561606` | `sync_crew_availability.py` plus `backend/crew_availability.py` | First end-to-end database/API slice verified; wallboard still uses preview fixture | Add scheduled Monday adapter, protected person route, and switch Crew UI to API |
| Daily work/resource allocation | `6_Daily Work Tracker` `5031430709`, Work Repository `5029561760`, Crew Repository | `sync_daily_work_tracker.py`, `sync_work_tracker.py` | Metrics helpers and protected server routes exist; shared snapshot publication incomplete | Build resource calendar and person heatmap projections from dated records |
| Billing | Customer Repository `5028043141` and related billing data | `sync_customer_repository_billing.py` | Adapter exists; customer-safe billing projection needs end-to-end validation | Normalize billing readiness, evidence, policy cases, and protected drawer fields |
| MIS and Analytics | Derived from Flight, Processing, Reports, Site Activities, Daily Work Tracker, Inventory, Incidents | `portal_metrics.py`, `sync_workflow_network.py` | Calculation helpers and preview cards exist; live normalized source contract is incomplete | Build versioned metric projections with numerator, denominator, source state, and quality state |
| Crew Management / Manager Vault | Crew Repository plus protected portal records | `portal_server.py`, `provision_portal_user.py` | Local protected runtime and auth store exist; production hosting/secrets remain external | Harden deployment, authorization, audit, and confidential employee access |
| Public Wallboard | Approved aggregate projections from all domains | `public-wallboard.html`, `data/public-wallboard-card-contract.json` | Static presentation preview; no live API adapter in browser | Add runtime public projection endpoint and replace fixture-only card data |

## Shared database layers

The database should separate:

1. **Raw snapshots** — exact source responses, source IDs, timestamps, and sync run.
2. **Normalized domain tables** — source-specific fields mapped into stable entities.
3. **Relations and lineage** — explicit Monday relation IDs and validated upstream/downstream links.
4. **Quality issues** — missing fields, unexpected labels, duplicate records, invalid relations, and stale data.
5. **Published projections** — versioned public and protected responses used by portal routes.

Every normalized record needs source provenance and a quality state. A failed sync must leave the last valid published snapshot available with an explicit stale/error state.

## Shared API groups

### Public

- `/api/public-status`
- `/api/public/crew-availability?month=YYYY-MM`
- `/api/public/operations-pulse`
- `/api/public/inventory-summary`
- `/api/public/delivery-summary`
- `/api/public/reports-summary`

Public responses contain only approved aggregates, dates, counts, rates, freshness, and quality states. They do not contain employee names, People IDs, Monday IDs, board names, source links, internal notes, customer financial values, or credentials.

### Protected

- `/api/crew-availability/{date}/people`
- `/api/resource-calendar`
- `/api/person-work-heatmap`
- `/api/crew-portal`
- `/api/metrics`
- protected evidence/detail drawers for each domain

Protected responses still require authorization and should return only the minimum source evidence needed for the requested role and route.

## Implementation order

1. Shared sync-run, raw-snapshot, quality-issue, and published-snapshot tables.
2. Crew Daily Availability as the first verified adapter/projection, including protected employee route.
3. Flight Operations → Processing/QA → Report Submission chain, because it powers Activity Tracking, Delivery, Analytics, and Reports.
4. Inventory and Incidents, because readiness and operational attention depend on their relations.
5. Site Activities, Daily Work Tracker, Billing, MIS, and Analytics projections.
6. Public Wallboard API replacement and protected Manager Vault deployment hardening.

## Current qualification

“Adapter exists” means a repository script can normalize or write a snapshot. It does not mean production scheduling, database publication, API authorization, live browser integration, or deployed visual QA is complete. Each domain must pass source readback, validation, projection, endpoint, and browser checks before being marked complete.
