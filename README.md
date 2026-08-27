# SkyStation Operations HQ

V5 frontend prototype for the SkyStation Operations Intelligence Portal.

## Run locally

Open `index.html` directly in a browser, or serve the repository directory:

```bash
python3 -m http.server 8767
```

The portal includes:

- six Central Dashboard management sheets;
- Display Mode with Previous, Next, Pause, Resume, progress, and Escape controls;
- Activity Tracking with Today / This Week / This Month states, owner/status filters, and an execution register;
- Inventory catalogue with fleet, drone-model, vehicle-system, and customer-allocation views;
- Crew Management with a Crew Repository-backed 14-active / 1-historical directory and historical-record toggle;
- Daily / Weekly / Monthly Analytics;
- handoff and reporting pipeline views;
- billing-unit decision views;
- structured, customer-safe MIS preview with customer/site/week selectors.

Crew Repository now has an explicit read-only data boundary:

- `scripts/sync_crew_repository.py` calls Monday server-side using `MONDAY_API_TOKEN`, requests only the approved Crew Repository fields, normalizes records by Monday item/user IDs, validates counts and team assignments, and writes `data/crew_repository.snapshot.json`.
- `scripts/validate_crew_snapshot.py` validates a snapshot without contacting Monday.
- The Crew Management view loads the normalized snapshot over HTTP and fails closed with `no fallback data loaded` if it cannot load; it does not silently use a second roster fixture.

Run the connector only in a trusted server/runtime:

```bash
MONDAY_API_TOKEN='[REDACTED]' python3 scripts/sync_crew_repository.py
python3 scripts/validate_crew_snapshot.py
```

The generated snapshot is intentionally local/runtime-only and is ignored by Git because this repository is published through GitHub Pages. Do not deploy internal Monday data through the public static bundle. Authentication, protected production storage, scheduled synchronization, the remaining operational-board connectors, contract-backed billing configuration, and production PDF generation remain to be connected.
