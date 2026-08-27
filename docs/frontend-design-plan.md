# SkyStation Operations HQ: Frontend Design Plan

## 1. Design direction

The portal will use a **Skylark Mission Control** direction: a polished operations product with a dark command surface for management monitoring and lighter evidence surfaces for operational inspection and MIS work.

The design keeps Skylark Orange (`#f05b28`), Dark Skylark Orange (`#d94800`), and the Skylark grey ramp as the identity anchors. Orange marks focus, action, and important change. Teal marks healthy/current data, amber marks review or follow-up, red marks exceptions, and neutral grey marks unknown or unavailable data. Status always includes text or an icon, so colour is never the only signal.

Typography uses Raleway for display headings, Avenir/Avenir Next for interface and report text, and a restrained monospace face for UINs, IDs, timestamps, and technical readouts. Spacing follows a 4px rhythm, with 8, 12, 16, 24, 32, and 48px as the main layout steps. Cards remain compact and purposeful; the design avoids identical card grids, excessive rounding, decorative gradients, and nested card stacks.

The visual language draws from flight paths, survey grids, telemetry, and map layers. These cues appear as quiet chart guides, route lines, grid intersections, and metadata marks. They support orientation and do not compete with operational content.

## 2. Experience principles

Every screen follows this sequence where the data supports it:

1. **Overview:** what is the current operating position?
2. **Signal:** what changed or needs attention?
3. **Evidence:** which source records explain the signal?
4. **Action:** what should the manager inspect, assign, or follow up?

The Central Dashboard is a projection, not a second data-entry system. Deep Dive is the protected operational workspace. The browser receives only data the current authorization boundary permits.

## 3. Global shell

### Central Dashboard and Display Mode

- Use a spacious dark graphite canvas with a restrained navigation rail.
- Lead each sheet with one management statement, one dominant analysis, and a ranked attention queue.
- Keep supporting metrics compact and subordinate to the main question.
- Show reporting period, scope, source state, and last-sync context without exposing connector/debug vocabulary on the management surface.
- Display Mode hides nonessential chrome, fills the horizontal TV canvas, and cycles only through the six Central Dashboard sheets.

### Deep Dive

- Keep the same brand tokens but use lighter evidence surfaces where long tables, filters, links, and report content need sustained reading.
- Preserve a clear route title, module-specific filters, source state, and last-sync context.
- Keep individual crew, owner, blocker, asset, incident, and operational details behind manager authentication.
- Show `No data`, `Not synced`, `Needs confirmation`, `Stale`, and `Unavailable` as distinct states.

## 4. Central Dashboard sheets

### Executive Overview

A management statement at the top, followed by a planned-versus-executed visual, a ranked management-attention queue, and compact customer/site health context. Avoid a first screen made entirely from KPI tiles.

### Activity & Delivery

Use a horizontal planned-versus-completed trend, an execution-gap view, and a customer/site comparison. Clicking a day or exception opens the relevant evidence queue.

### Fleet & Operations

Use visual SkyStation and drone family panels, a vehicle-mounted system relationship view, availability states, and an operational exceptions list. Asset identity and relation provenance must remain separate from descriptive location text.

### Reporting & MIS

Use a left-to-right handoff funnel: flight completion → processing → QA → report readiness → submission. Show ageing bands and missing-link evidence beside the funnel.

### Crew & Capacity

Make this the signature people-oriented sheet, adapting the hotel dashboard’s vertical staff rhythm to a horizontal TV composition.

- Left side: Crew Pulse statement and aggregate availability/workload signal.
- Right side: a tall, scroll-free **Crew On Duty** list.
- Each row shows avatar/initials, Monday-linked name, team, availability, open assignments, completion/evidence state, and blocker or follow-up signal.
- Use workload and evidence bars, never employee performance scores or rankings.
- Public view shows only approved aggregate crew counts. Individual rows remain manager-only.
- On narrower screens, the two columns stack naturally; on portrait screens, the people list becomes the primary vertical composition.

### Customer & Commercial

Use customer/site health, billing readiness, and explicit review states. Keep customer-safe projection rules separate from internal owner/blocker details.

## 5. Deep Dive modules

### Activity Tracking

Use module-owned Today, This Week, and This Month tabs. The tab must change records and derived values, not just the highlight. Use an execution timeline, filters, exception queue, source relation, and drill-down evidence.

### Inventory

Use a visual fleet catalogue with SkyStation version cards, drone-family cards, vehicle-mounted system relationships, support inventory, customer/site allocation, and individual asset detail boundaries. Readiness must show its components: asset state, maintenance, assignment, blocker, and next activity.

### Crew Management

Use Crew Pulse plus a full evidence table. Active employees appear by default; historical employees require an explicit view. Do not infer current role, team, employment, skills, or certifications from historical activity.

### Analytics

Use Daily, Weekly, and Monthly tabs. Each view must change the underlying visual and evidence queue. Prioritize heatmaps, planned-versus-actual trends, handoff timing, recurring coverage, delay causes, asset readiness, owner workload, and exception ageing.

### Billing

Use billing-unit-level rows and a `Why this decision?` interaction. Show rule, evidence, assets, period, and source records. Preserve the distinct Adani, ACME, and ReNew policy cases without reducing them to a generic site status.

### MIS

Use a structured customer report preview with summary, activity status, availability/blockers, uploads, reports, and publication state. Export remains explicitly preview-only until real PDF generation and customer-safe API filtering are implemented.

## 6. Animation and motion plan

Motion should explain change, hierarchy, or cause-and-effect. It must never hide data or make a busy dashboard harder to read.

### Global motion rules

- Use short ease-out transitions for navigation and state changes, generally 160–280ms.
- Use slightly longer transitions for chart drawing and sheet changes, generally 400–700ms.
- Animate transforms, opacity, clip-path, and controlled scale rather than layout dimensions.
- Keep one clear motion event at a time on the management surface; avoid simultaneous movement of every card.
- Respect `prefers-reduced-motion: reduce` by removing chart draw effects, auto-cycle motion, and decorative movement while preserving the final state and all controls.
- Never use bounce, elastic motion, infinite decorative loops, or animation as a substitute for a visible status label.

### Dashboard motion

- On sheet entry, the management statement appears immediately; the primary chart draws from zero to its final values over 500–650ms.
- Ranked attention rows reveal in a restrained stagger of 40–60ms, capped so the queue remains readable.
- Metric changes use a brief value transition and a small directional indicator, not a large count-up that implies false precision.
- Display Mode uses a visible progress track and a calm crossfade between sheets. Pause freezes the progress track and all cycling. Manual navigation immediately cancels the current transition.
- The Crew On Duty panel reveals rows in a short sequential entrance on first load only. Refreshing data updates changed rows with a subtle background/state transition rather than replaying the entire list.

### Chart motion

- Bars grow from their baseline, lines draw along their path, funnel stages fill left to right, and heatmap cells fade to their final intensity.
- On hover or keyboard focus, the selected mark receives a clear outline and the associated evidence label appears. The chart must remain understandable without motion or hover.
- When a filter changes, preserve the chart frame and transition the data marks to their new positions where practical. If the data state changes to unavailable, replace the visual with an explicit empty state instead of animating to zero.
- Chart-click interactions open or update a detail queue with a short transition, retaining the selected period/site/status in the context line.

### Operational feedback

- Buttons show a small pressed/focus state and return to rest quickly.
- Filter changes update the result surface and show the selected value in the context line.
- Save/export boundaries show a clear success, unavailable, or preview-only message. A toast is supplementary and never the only confirmation.
- Locked Deep Dive states appear immediately, with no flash of internal fixture content before the protected request resolves.

## 7. Responsive compositions

### Horizontal TV / 16:9

- Use a wide two-column composition with a dominant analysis on the left and a readable evidence/action column on the right.
- Keep text large enough for viewing distance and avoid vertical scrolling in Display Mode.
- Use the Crew On Duty list as a fixed-height, carefully sized panel with only the intended visible rows.
- Keep sheet navigation and progress visible but quiet.

### Desktop manager workspace

- Use the full shell with navigation rail, contextual filters, evidence tables, and expandable detail surfaces.
- Dense tables use controlled horizontal scrolling inside their own containers.
- Individual source evidence, owner fields, blockers, and audit context are available only after authorization.

### Narrow screens

- Stack primary and secondary panels.
- Convert wide matrices and registers into controlled horizontal scroll regions.
- Preserve tab usability with wrapping or horizontal tab scrolling.
- Keep headings balanced and prevent long labels from overflowing.

## 8. Data and permission behavior

- Central Dashboard public responses contain only approved summary metrics and public source-state information.
- Deep Dive data is fetched through protected server-side APIs and requires manager authorization in production.
- Missing snapshots never become zeros presented as real operational totals.
- `needs_review` records remain visible as review states; they are not silently repaired or excluded from evidence queues.
- Crew identity and operational assignments join through stable Monday IDs and explicit relations, never display-name inference.
- Work Tracker remains internal and cannot prove customer delivery or flight execution.
- Planning records remain separate from execution, handoff, report delivery, inventory ownership, and incident closure evidence.

## 9. Implementation order

1. Build reusable design tokens, shell, state components, chart primitives, and Crew Pulse.
2. Rebuild Crew & Capacity as the first visually complete sheet, including horizontal TV and desktop compositions.
3. Rebuild Activity Tracking with period tabs, filters, execution timeline, and evidence queue.
4. Rebuild Inventory with visual catalogue and relation-aware detail states.
5. Rebuild Analytics with Daily/Weekly/Monthly visual state transitions and drill-down queues.
6. Rebuild Billing with billing-unit evidence and decision explanation.
7. Rebuild MIS with structured customer-safe sections and export boundary.
8. Replace Central Dashboard fixture metrics with canonical normalized metrics and drill-downs.
9. Add Google manager authentication and production deployment.
10. Run the final visual and functional gate at 16:9 TV, desktop, and narrow widths.

## 10. Acceptance criteria

Every slice is complete only when:

- the intended API-backed data or explicit unavailable/review state is rendered;
- all relevant tabs and subtabs change both content and active state;
- filters, toggles, drill-downs, export/display controls, and keyboard behavior work;
- public dashboards contain no protected operational details;
- protected routes fail closed without authorization;
- charts animate purposefully and still work with reduced motion;
- the browser console has no errors;
- images and assets load from the delivered path;
- the 16:9 composition has no clipping, excessive density, or accidental scrolling;
- the exact committed and delivered artifact is verified before release.
