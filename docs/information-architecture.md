# Information Architecture and Route Map

Status: In review  
Last reviewed: 2026-09-19

## Entry points

- `index.html` → redirect-only entry point.
- `rebuild-preview.html` → main portal preview.
- `public-wallboard.html` → public TV display.

## Main portal routes

The current preview uses client-side route buttons inside `rebuild-preview.html`:

- Activity Tracking — default route; execution and attention review.
- Public Wallboard — full-page navigation to `public-wallboard.html`.
- Inventory — fleet and hardware preview.
- Crew Management — aggregate/personal preview boundary; public wallboard only receives aggregates.
- Analytics — daily/weekly/monthly analytics and workflow network.
- Billing — preview route with source-state handling.
- MIS — customer-safe export preview.
- Manager Vault — future protected workspace.
- Crew Overview resource allocation — protected internal calendar of dated work assignments.
- Crew Deep Dive person heatmap — protected individual work-density view with source drilldowns.

## Public Wallboard

The wallboard is a separate static route with six fixed screens:

1. Operations Pulse
2. Delivery Flow
3. Crew and Resource Pulse
4. Geographic Operations
5. Reporting Outcomes
6. Fleet and Readiness

Navigation back to the main portal is an explicit `Main portal` link. The display does not require a mouse, hover, drawers, or scrolling.

## State model

All surfaces must distinguish:

- Current/live source.
- Stale source.
- Unavailable source.
- Needs review.
- Synthetic preview.
- Awaiting confirmation.
- Excluded historical records.

## Future protected route model

- Public projection: aggregate, customer-safe, no authentication for approved display data.
- Manager Vault: authenticated manager route for names, owners, blockers, source records, role detail, crew history, billing evidence, and operational controls.

## Navigation rules

- Route labels describe the user task, not the source board.
- Public Wallboard must always provide a return path.
- A route is incomplete if its button only opens a notice without a documented next implementation slice.
- Any route that exposes protected data must fail closed before rendering internal fixture content.
