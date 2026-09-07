# Analytics Module Implementation Plan

> **For Hermes:** Use the subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build a high-signal Analytics module in the synthetic SkyStation Operations HQ preview that explains delivery performance, recurring coverage, delay causes, workload, asset readiness, and exception ageing, with every visual leading to an evidence queue.

**Architecture:** Add Analytics as a dedicated route in `rebuild-preview.html`, using one canonical synthetic analytics fixture and one view controller for Daily, Weekly, and Monthly states. Keep the module visually distinct from Activity, Inventory, and Crew: Analytics is an investigation surface built around a dominant performance narrative, diagnostic visual layers, and a right-side action queue. Keep `index.html` untouched and preserve the explicit `SYNTHETIC DEMO` / `NO AUTHENTICATION` boundary.

**Tech Stack:** Self-contained HTML/CSS/JavaScript, existing Skylark Mission Control tokens, inline SVG/CSS visual primitives, Playwright/Chromium browser QA, GitHub Pages hosted verification.

---

## Product contract

Analytics must answer four questions in order:

1. **What changed?** Planned versus completed performance for the selected period.
2. **Where is the pattern?** Heatmap by team/customer-site/day, recurring coverage, workload, and asset readiness.
3. **Why did it happen?** Delay causes, handoff timing, source-quality gaps, and ageing.
4. **What should I inspect next?** A ranked exception queue with period, scope, count, status, and drill-down action.

The module must show:

- Selected period: Daily, Weekly, or Monthly.
- Scope context: current synthetic dataset, selected customer/site/team if filtered.
- Last sync/source state: synthetic preview state, never live-looking.
- Exact counts beside percentages.
- Distinct `No data`, `Not synced`, `Needs confirmation`, and `Needs review` states.
- A visible path from every chart interaction to a filtered evidence queue.

Do not build:

- A leaderboard.
- A decorative dashboard made of equal-weight cards.
- A score implying individual human value.
- A second data-entry system.
- Unsupported production claims from synthetic data.

## Visual direction

Use a **Flight Path Investigation** composition:

- Dark command surface with one dominant orange planned-versus-completed trajectory.
- Quiet survey-grid and route-line cues inside charts only.
- Teal for healthy/current, amber for review/follow-up, red for exception/decline, slate for unknown/future, and orange for primary focus.
- Raleway for display headings; Avenir/Avenir Next for UI and evidence text; monospace only for period/source readouts.
- First viewport: one management statement, dominant trend, and a compact ranked queue. Supporting analyses sit below in an intentional diagnostic sequence.
- No nested card wall. Use a wide hero analysis, compact diagnostic strips, one heatmap, and one evidence table/queue.

---

## Implementation tasks

### Task 1: Inspect and freeze the current rebuild boundary

**Objective:** Confirm the exact insertion points and protect the existing Activity, Inventory, Crew, and production entrypoints.

**Files:**
- Read: `rebuild-preview.html`
- Read: `index.html`
- Read: `docs/frontend-design-plan.md`
- Read: `docs/frontend-redesign-execution-plan.md`

**Steps:**

1. Confirm `index.html` remains unchanged and `rebuild-preview.html` is the active synthetic preview.
2. Locate the nav registry, route-switching logic, content sections, responsive CSS, and reduced-motion rules.
3. Record the existing CSS tokens and avoid introducing a second global palette.
4. Confirm the current branch is clean before implementation.

**Verification:** Existing Activity, Inventory, Hardware Inventory, Crew Overview, and Crew Deep Dive routes still load with zero browser errors before Analytics work begins.

### Task 2: Create the canonical Analytics fixture

**Objective:** Define one internally consistent synthetic data model for all Analytics states.

**Files:**
- Modify: `rebuild-preview.html` JavaScript data section.
- Optional create: `tests/analytics-fixture-check.mjs` if the existing test layout supports it.

**Data shape:**

```js
const analyticsFixture = {
  periods: {
    daily: { label: 'Today · 07 Sep 2026', planned: 18, completed: 11, inProgress: 3, attention: 4 },
    weekly: { label: '31 Aug–06 Sep 2026', planned: 67, completed: 52, inProgress: 8, attention: 7 },
    monthly: { label: 'September 2026 · month to date', planned: 246, completed: 202, inProgress: 31, attention: 13 }
  },
  trend: { planned: [], completed: [], evidence: [] },
  heatmap: { rows: [], columns: [], values: [] },
  delays: [],
  handoff: [],
  recurring: [],
  workload: [],
  readiness: [],
  exceptions: []
};
```

1. Use the same period totals in the hero, trend, funnel, and evidence queue.
2. Ensure all arrays have named customer/site/team/status/source fields.
3. Include deliberate states: one `Needs review`, one `Not synced`, one `Needs confirmation`, and one `No data` example behind a filter or detail state.
4. Keep the fixture fictional and visibly labelled.

**Verification:** A fixture invariant script or browser evaluation confirms that totals and chart series agree for all three periods and no row has an impossible negative or mismatched count.

### Task 3: Add the Analytics route and route metadata

**Objective:** Make Analytics a real route rather than an inert navigation label.

**Files:**
- Modify: `rebuild-preview.html` nav markup.
- Modify: `rebuild-preview.html` route controller.
- Modify: `rebuild-preview.html` topbar/breadcrumb metadata.

**Steps:**

1. Add `data-route="analytics"` to the Analytics navigation button.
2. Add a dedicated `analyticsView` section and register it in the route map.
3. Ensure route switching hides every other content section and activates exactly one nav item.
4. Set the crumb to `Deep Dive / Analytics` and show the period context in the top selector or module context line.
5. Preserve direct route entry if the rebuild uses hash/query route state.

**Verification:** Clicking Analytics changes visible content, active navigation, breadcrumb, and page state; direct refresh on the Analytics route works; no legacy content remains visible.

### Task 4: Build the first viewport hero analysis

**Objective:** Give managers an immediate answer to what changed.

**Files:**
- Modify: `rebuild-preview.html` Analytics markup.
- Modify: `rebuild-preview.html` Analytics CSS.

**Composition:**

- Header: `Analytics` / management statement / `SYNTHETIC DEMO`.
- Period tabs: Daily, Weekly, Monthly.
- Dominant planned-versus-completed SVG trend with exact values and a clear delta callout.
- Small status rail: completion rate, on-time rate, handoff completion, attention count.
- Ranked `What needs inspection` queue on the right.

**Steps:**

1. Render the selected period from the canonical fixture.
2. Draw planned and completed series from the Y-axis baseline, with a static final state under reduced motion.
3. Add a selected point/callout that displays date, planned, completed, gap, and evidence state.
4. Keep the queue visible without forcing a scroll on a 16:9 desktop viewport.
5. Add a context line explaining that values are synthetic preview data.

**Verification:** Changing period changes the chart series, totals, callout, and queue; it does not only change the active tab styling.

### Task 5: Add the diagnostic layer

**Objective:** Explain where and why the performance changed.

**Files:**
- Modify: `rebuild-preview.html` Analytics markup, CSS, and controller.

**Visuals:**

1. **Execution heatmap:** team/customer-site by weekday or period bucket; cells show count and state.
2. **Delay causes:** horizontal bars with count and share, not share alone.
3. **Handoff funnel:** Activity Repository → Flight Operations → Processing/QA → Report Submission → client-ready, with drop-off counts.
4. **Recurring coverage:** expected cadence versus found records, with missing/extra evidence states.
5. **Owner workload:** assigned, active, overdue, and unassigned work; no performance ranking.
6. **Asset readiness:** upcoming activity matched against ready/maintenance/relation-review assets.

**Steps:**

1. Give each visual a one-sentence interpretation generated from fixture values.
2. Add legends with exact counts and state labels.
3. Use a consistent chart-click target model: clicking a mark sets the evidence queue filter.
4. Keep `Needs review` and `No data` visually distinct from zero.
5. Use compact source labels such as `Synthetic activity register`, `Synthetic handoff register`, and `Synthetic fleet snapshot`.

**Verification:** Each visual can be interacted with or focused by keyboard, changes the queue context, and preserves the selected period.

### Task 6: Build the evidence queue and drill-down behavior

**Objective:** Turn Analytics into an investigation workflow rather than a read-only report.

**Files:**
- Modify: `rebuild-preview.html` Analytics markup/controller/CSS.

**Queue contract:**

Each row includes:

- Exception or pattern name.
- Period and customer/site/team scope.
- Exact count and denominator where relevant.
- State badge.
- Cause/source label.
- Next action.
- `Open evidence` control.

**Steps:**

1. Add queue filters for `All`, `Delivery gap`, `Delay`, `Coverage`, `Handoff`, `Asset readiness`, and `Source quality`.
2. Add selected chart mark state and a visible context line such as `Filtered to Weekly · QA backlog · 9 items`.
3. Open an evidence drawer or detail panel with source fields, synthetic IDs, and validation caveats.
4. Make Escape close the drawer and restore focus.
5. Ensure no chart click only changes a highlight; it must change queue content or open evidence.

**Verification:** At least one interaction from every major visual changes the queue or opens evidence, and the selected filter is reflected in the URL/state context if the existing route architecture supports it.

### Task 7: Add responsive, motion, and unavailable states

**Objective:** Make Analytics credible on desktop, 16:9, and mobile without motion-dependent meaning.

**Files:**
- Modify: `rebuild-preview.html` Analytics CSS/controller.

**Steps:**

1. At 1920×1080, keep the hero and queue visible without accidental horizontal overflow.
2. At desktop laptop width, stack or compress diagnostics without collapsing labels.
3. At 390px, horizontally scroll only dense heatmaps/tables; keep period tabs and primary numbers readable.
4. Animate the chart sweep, bars, funnel, and heatmap entrance in a restrained sequence.
5. With `prefers-reduced-motion: reduce`, render final values immediately and disable active animations.
6. Add explicit empty-state renderers for `No data`, `Not synced`, `Needs confirmation`, and `Needs review`.

**Verification:** Browser evaluation confirms no horizontal overflow, final-state parity under reduced motion, and zero console/page errors.

### Task 8: Run interaction and visual QA locally

**Objective:** Verify the exact Analytics experience before publishing.

**Files:**
- Modify only if QA finds a defect: `rebuild-preview.html`.
- Optional create: `tests/analytics-browser-check.mjs`.

**Checks:**

1. Load Analytics directly and through navigation.
2. Exercise Daily, Weekly, Monthly.
3. Click a trend point, heatmap cell, delay cause, funnel stage, recurring-coverage row, workload bar, readiness state, and exception queue row.
4. Verify each changes queue/detail state.
5. Check drawer close, Escape, keyboard focus, and route switching.
6. Capture 1920×1080, desktop, and 390px screenshots for visual review.
7. Confirm synthetic labels, no sensitive production values, no overflow, and zero errors.

### Task 9: Commit, publish, and hosted verification

**Objective:** Verify the exact deployed Analytics artifact rather than only the local file.

**Files:**
- Modify: none after QA passes.
- Commit: `rebuild-preview.html` and any dedicated test/plan files.

**Steps:**

1. Commit the verified Analytics slice with a focused message.
2. Push `main` and confirm the remote commit.
3. Poll the GitHub Pages URL with a cache-busting query until a distinctive Analytics marker is served.
4. Run the same Chromium route, tab, drill-down, responsive, and reduced-motion checks against the hosted URL.
5. Inspect hosted screenshots before reporting completion.

**Acceptance:** The hosted URL serves the new marker, all Analytics views are interactive, the exact chart/queue state is visible, no protected data appears, and browser/page errors remain zero.

---

## Definition of done

Analytics is ready for stakeholder review only when:

- Analytics is a real route in `rebuild-preview.html`.
- Daily, Weekly, and Monthly change actual data and evidence queues.
- The first viewport has one dominant planned-versus-completed narrative and a visible action queue.
- Heatmap, delay causes, handoff funnel, recurring coverage, workload, and readiness each support an investigation path.
- Every visualization has a period, unit, legend, exact count, and source-state context.
- Filled/empty/review states are explicit and not conflated with zero.
- No leaderboard or unsupported person-level productivity judgement is present.
- Synthetic data is clearly labelled and isolated from production.
- Desktop, 16:9, and 390px layouts pass without unintended overflow.
- Reduced-motion users see the final state immediately.
- Local and hosted Chromium checks report zero errors.
- The exact hosted artifact is visually inspected before completion is reported.
