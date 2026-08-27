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

The current values are representative frontend data. Crew Repository is represented as a read-only normalized projection in this prototype; source connectors, authentication, normalized production storage, contract-backed billing configuration, and production PDF generation remain to be connected.
