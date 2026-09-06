# SkyStation Operations Intelligence Portal Rebuild Plan

> **Status:** planning baseline; implementation begins after review of the first vertical slice.

**Goal:** Rebuild the portal as one trustworthy operations system with a source-backed Deep Dive, a full-screen Central Dashboard projection, and a separate protected Billing Deep Dive.

**Architecture:** Server-side normalized data remains the single business truth. Deep Dive modules consume protected normalized APIs and expose filters, records, evidence, and source states. Central Dashboard reads the same aggregates and provides a read-only 16:9 presentation playlist. The frontend is rebuilt around a clear route registry and shared scope/evidence primitives instead of extending the rejected card-grid composition.

**Product authorities:**

- `SkyStation_Operations_Intelligence_Dashboard_PRD_v1.0.pdf` governs Operations Intelligence, Activity, Inventory, Crew, Analytics, MIS, Patang, and Central Dashboard.
- `docs/billing-deep-dive-prd.md` governs Billing Deep Dive only.
- `docs/data-contract.md` governs source IDs, relations, freshness, validation, and customer-safe projection.
- `docs/frontend-visual-direction.md` governs the visual and motion direction.

---

## Non-negotiable product rules

- Central Dashboard is a projection layer, never an independent data-entry or KPI store.
- Deep Dive owns operational truth and source evidence.
- Central Dashboard display views fit within the target 16:9 viewport with no vertical page scroll; Deep Dive may use controlled scrolling for dense operational tables.
- Every material metric, exception, and Patang insight has a source path, time window, and sync state.
- `current`, `stale`, `unavailable`, and `needs_review` are explicit states.
- No production fixtures supply people, customers, assets, statuses, dates, assignments, KPIs, billing states, or MIS values once their connector is enabled.
- Joins use Monday board/item/group/People/relation IDs or explicit Google source IDs, never names, mirror text, or location strings.
- Crew performance is shown as data discipline, delivery performance, and workload/capacity; no opaque overall score.
- Billing amounts and commercial records remain protected inside Billing Deep Dive.
- Customer-safe projections are filtered before browser delivery.
- The new UI uses SkyStation terminology; “Dock” remains only in legacy source/file references.

## Target information architecture

```text
SkyStation Operations Intelligence
├── Central Dashboard
│   └── Full-screen playlist: Operating Pulse, Today, Weekly Delivery,
│       Customer/Site, Fleet, Crew Load, Billing Readiness, Exceptions, Analytics
└── Deep Dive
    ├── Activity Tracking
    ├── Inventory
    ├── Crew Management
    │   └── Person detail + one-on-one evidence
    ├── Analytics
    ├── Billing
    │   └── Month × Drone Asset Matrix + commercial lifecycle
    └── MIS
        └── Customer → Site → Week → Template → Preview → PDF
```

## Phase 0 — Preserve and reset the frontend

**Outcome:** rejected frontend composition is isolated; secure backend and normalized source work remain reusable.

- Work on `rebuild/frontend-reset`, preserving the known-good `main` baseline.
- Keep `scripts/portal_server.py`, adapters, validators, source contracts, tests, and runtime snapshot protections.
- Replace the monolithic route markup with a page registry, shared shell, typed view state, and isolated module containers.
- Remove legacy dashboard fragments rather than hiding them with runtime CSS.
- Define shared primitives: `AppShell`, `ScopeBar`, `SourceState`, `EvidenceDrawer`, `StatusBadge`, `EmptyState`, `DataTable`, `MetricStatement`, and `DisplayFrame`.
- Use CSS grid with explicit viewport budgets; Central Dashboard frames must be tested at 1920×1080 and laptop sizes.

**Gate:** one empty-but-correct shell renders every target route, each route has one owner container, and no route has accidental overflow or console errors.

## Phase 1 — Establish the normalized intelligence layer

**Outcome:** every module can consume the same entities and lineage metadata.

- Complete contracts for Customer, Site, Asset, Deployment, Activity, Team, Person, Deliverable, Billing Period, MIS Template, Source Reference, and Incident/Exception.
- Keep planning records separate from execution evidence.
- Add canonical derived metrics with formulas, filters, exact numerator/denominator, and source references.
- Add sync registry for Monday, Google Sheets, inventory, reporting, and future connectors.
- Add validation issue types for missing relations, duplicate IDs, stale source, missing artifacts, contradictory states, and unconfigured mappings.
- Extend protected APIs with explicit aggregate/detail responses and no fallback fixtures.

**Gate:** API tests prove unauthorized access, unavailable data, stale data, needs-review data, ID-preserving joins, and no source request when credentials are absent.

## Phase 2 — Activity Tracking vertical slice

**Outcome:** first complete operational workflow from plan through delivery evidence.

- Build Daily, Weekly, Monthly, Overall, Customer, and Team perspectives.
- Model the handoff chain:

  `Plan → Flight/Site Activity → Processing & QA → Report Submission → Client-ready`

- Show planned, in progress, completed, delayed, blocked, unplanned, missing-row, unlinked-row, and awaiting-evidence states.
- Add filters for period, customer, site, team, owner, activity type, status, priority, and delay reason.
- Make aggregate clicks open filtered underlying records.
- Add source/evidence drawer with IDs, timestamps, relations, status history where available, and validation flags.

**Gate:** one activity can be traced from plan to downstream evidence, and every missing/ambiguous handoff is distinguishable without inference.

## Phase 3 — Inventory and deployment model

**Outcome:** asset governance is visual, relational, and history-aware.

- Model SkyStations, drones, vehicle-mounted assemblies, and configurable other inventory.
- Add asset identity, serial, model/version, compatibility, condition, maintenance, and state.
- Add time-bound deployment history so movement between sites is represented correctly.
- Detect conflicting simultaneous assignments and unexpected relation targets.
- Use approved asset imagery when supplied; mark temporary assets clearly until then.
- Add asset detail with assignment history, compatibility, incident links, and source timestamps.

**Gate:** an asset can be followed across sites and periods without rewriting historical assignment or billing context.

## Phase 4 — Crew Management and individual deep dive

**Outcome:** management can inspect each person’s evidence without reducing performance to one score.

- Build team overview for supported teams and additional teams through configuration.
- Show current work, completed/pending/overdue assignments, active sites/customers, stale updates, and workload distribution.
- Calculate separate dimensions:
  - data discipline;
  - delivery performance;
  - workload/capacity.
- Add person-level history and source-linked activity drill-down.
- Define and connect the one-on-one Google Sheets source after confirming sheet IDs, tabs, person key, review period, ownership, and field semantics.
- Preserve one-on-one themes/notes with source timestamp and visibility rules; distinguish self-reported, manager-entered, and derived evidence.
- Show missing or conflicting sheet data as `Not synced`, `Needs confirmation`, or `No data`.

**Gate:** selecting a person shows source-backed operational evidence and one-on-one context, with no fabricated score or inferred employment metadata.

## Phase 5 — Analytics and Patang insights

**Outcome:** analytics explains operational decisions and drills into records.

- Add execution, delay, crew/capacity, SkyStation operations, reporting, and customer/site analytics.
- Use time-windowed trends, heatmaps, handoff funnels, aging bands, workload distributions, and recurring-issue views.
- Show exact counts beside percentages and make every chart segment actionable.
- Generate Patang insights only when contributing records support the claim; label data-limited conclusions as provisional.
- Keep comparison periods explicit.

**Gate:** every chart answers a named management question and opens a corresponding filtered evidence state.

## Phase 6 — Billing Deep Dive

**Outcome:** the separate commercial workflow is usable without contaminating the operations dashboard.

- Implement the protected Month × Drone Asset Matrix.
- Model Customer → Contract/PO → Site → Asset → Month → Billability → Service Sheet → Invoice → Payment.
- Add configurable billing periods, cutoff dates, approval steps, rates, partial billing, non-billable reasons, and overrides.
- Add cell drill-down, Billing Queue, monthly closing dashboard, invoice-to-asset-month allocation, deployment history, rate history, exports, and audit events.
- Keep detailed amounts, invoice values, payment records, and commercial evidence inside Billing Deep Dive.
- Central Dashboard receives only approved readiness/exception summaries.

**Gate:** one asset-month progresses independently through service completion, billability, service sheet, invoice, and payment, with audit history and no implied invoice from a billable tick.

## Phase 7 — MIS and PDF export

**Outcome:** customer/site/week reporting is configurable and safe.

- Implement Customer → Site → Week selection.
- Add customer/site template configuration for sections, KPIs, charts, wording, and visibility.
- Build preview from Deep Dive normalized data.
- Export Excel where required and PDF for customer-facing reports.
- Enforce customer-safe fields at the projection layer.
- Render and inspect PDFs for clipping, unreadable tables, broken page breaks, and internal-field leakage.

**Gate:** a selected customer/site/week produces a traceable preview and a verified export containing only approved fields.

## Phase 8 — Central Dashboard projection

**Outcome:** a calm full-screen management display composed from completed Deep Dive views.

- Build the nine PRD playlist views: Operating Pulse, Today, Weekly Delivery, Customer/Site Status, Fleet/Inventory, Crew Load, Billing Readiness, Exceptions, and Key Analytics.
- Each view communicates one management story with one dominant statement and a few supporting visuals.
- Keep dense record tables out of auto-cycle views; use evidence drawers or manual Deep Dive navigation.
- Add configurable playlist order, enabled views, duration, pause/resume, previous/next, refresh, period context, and sync state.
- Use summary billing readiness only; do not expose detailed commercial amounts on the Central Dashboard.
- Verify every displayed value comes from Deep Dive aggregates.

**Gate:** all enabled views fit 1920×1080 with `scrollHeight <= clientHeight`, display controls work, and changing a source state changes the projection honestly.

## Phase 9 — Authentication, roles, and production wiring

**Outcome:** production access and data delivery are secure and operational.

- Deploy the backend separately from GitHub Pages.
- Add Google Workspace identity with `openid`, `email`, and `profile` only.
- Enforce manager/role authorization server-side before protected data is sent to the browser.
- Configure runtime secrets through the deployment secret manager.
- Keep Monday read-only and schedule server-side synchronization.
- Add role rules for Management, Operations, Team Leads, Contract/Account Owners, Finance, and Super Admin.
- Keep the public static preview synthetic-only and separate from production data.

**Gate:** unauthenticated requests return `401`, unauthorized roles cannot access protected modules, missing/stale sources fail closed, and no internal snapshot is public.

## Phase 10 — Visual refinement and release QA

**Outcome:** the product is polished after its workflows are trustworthy.

- Apply the approved visual direction: asymmetric composition, strong hierarchy, dark graphite shell, signal orange, restrained technical detail, and calm motion.
- Remove perpetual shimmer, novelty effects, and decorative chart animation.
- Add reduced-motion behavior and keyboard focus states.
- Verify every route, tab, filter, drawer, matrix cell, chart drilldown, display control, export action, and source-state transition.
- Run browser checks at 1920×1080, 1440×900, laptop, narrow, and reduced-motion settings.
- Check console errors, horizontal overflow, Central Dashboard vertical overflow, asset loading, and protected API behavior.
- Verify the exact deployed artifact after GitHub Pages/backend propagation.

**Release gate:** no unresolved critical data, security, navigation, overflow, console, export, or source-traceability failures.

## Delivery discipline

Each phase is a vertical slice and must produce:

1. normalized contract or UI behavior;
2. tests for the behavior and fail-closed states;
3. a browser-verifiable route or workflow;
4. source/evidence documentation;
5. a small commit on `rebuild/frontend-reset`.

Do not expand to the next phase because a screen looks complete. Advance only when the current workflow is source-backed, traceable, and verified in the browser.
