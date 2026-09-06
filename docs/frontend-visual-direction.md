# SkyStation Frontend Visual Direction

Status: direction captured from stakeholder references, 2026-09-06.

## Product boundary

This direction applies to the SkyStation Operations Intelligence portal. The supplied Contract Billing & Drone Asset Tracking PRD applies only to the protected Billing Deep Dive; its detailed commercial matrix and amounts must not define the whole portal.

## Visual thesis

Build a composed operational interface rather than a repeated card wall. Every screen should establish one dominant operational statement, then support it with a small number of structured evidence regions. The interface should feel like a calm command surface: precise, legible, and useful during daily review.

## Reference-derived principles

- Use a strong horizontal context/header bar with product identity, active section, reporting period, source state, and primary navigation.
- Use asymmetric composition: one dominant visual or decision area beside smaller supporting regions, instead of equal-weight four-card grids.
- Keep the first viewport visually complete. Central Dashboard display views target 16:9 and must be checked for `scrollHeight <= clientHeight`; details open in a drawer or focused working state.
- Establish hierarchy through scale, whitespace, grouping, and alignment. Large numbers or statements should be rare and meaningful.
- Use dark graphite/carbon surfaces for the operating shell, with quiet panels, fine borders, low-intensity grids, and minimal glow.
- Use signal orange for attention and selection, teal/green for current or healthy states, amber for review, red for exception, and slate for unknown. Status must always include text or an icon.
- Treat charts as instruments for decisions: show units, period, legend, exact counts, and a visible route to the underlying records.
- Prefer timelines, progress bands, gauges, heatmaps, compact trend lines, matrices, and evidence lists. Avoid decorative chart wallpaper.
- Use dense tables inside Deep Dive where record scanning requires them, while keeping Central Dashboard display mode editorial and uncluttered.
- Use image-led fleet presentation when approved SkyStation, drone, and vehicle assets are supplied; temporary assets must be explicitly labelled.

## Motion rules

- Animate only when motion explains a transition, refresh, handoff, or drill-down context.
- Use short opacity/position transitions for view changes and restrained chart drawing for newly selected data.
- Display Mode cycling must communicate current view, pause state, and remaining interval without demanding attention.
- Avoid looping neon effects, bouncing elements, perpetual dashboard shimmer, and animation that competes with exceptions.
- Respect `prefers-reduced-motion` by disabling non-essential transitions and chart animation.

## Additional billing and overall-portal reference

The stakeholder-supplied contract billing reference establishes a useful enterprise operating pattern for the whole portal: a persistent left rail for module navigation, a compact global scope/search bar, a concise signal band, a dominant work surface, and a right-side action rail. Its strongest transferable idea is the relationship between a dense operational matrix, a bounded queue of next actions, a progress summary, and a selected-record detail panel.

Apply the pattern selectively:

- **Overall portal:** use persistent context, a clear module rail, a bounded attention queue, and selected-record evidence without turning every route into the same template.
- **Central Dashboard:** retain the rail only when it does not compromise the full-screen display composition; display mode may collapse chrome into a presentation header.
- **Billing Deep Dive:** use the Month × Drone Asset Matrix as the dominant surface, with Billing Queue and month-closing progress beside it, and a cell detail panel below or as a drawer.
- **Deep Dive modules:** use dense tables and detail panels where work requires them; do not force ornamental dashboard cards into operational routes.
- **Interaction:** selecting a matrix cell, queue item, chart segment, or table row must update the detail context visibly, preserve scope, and expose evidence.

Do not copy the reference brand, sample names, sample figures, drone imagery, or exact color choices. Keep SkyStation terminology, approved brand assets, source-state semantics, and protected-data boundaries.

## Screen model

### Central Dashboard

A full-screen read-only projection from Deep Dive. Each playlist view communicates one story: operating pulse, today, weekly delivery, customer/site status, fleet, crew load, billing readiness, exceptions, or key analytics. It includes context and freshness, but no dense record table or data entry.

### Deep Dive

A working environment with global scope controls, filters, dense evidence tables, source-state labels, and an evidence drawer. The six modules remain Activity Tracking, Inventory, Crew Management, Analytics, Billing, and MIS.

### Billing Deep Dive

Use the separate billing specification: protected Month × Drone Asset Matrix, cell drill-down, billability confirmation, billing queue, service-sheet/invoice/payment lifecycle, asset-month invoice allocation, configuration, and audit history. Detailed commercial values stay here.

## Quality gate

Before a visual pass is called complete:

- verify the actual rendered page at 1920×1080 and common laptop dimensions;
- assert no Central Dashboard vertical overflow;
- inspect a screenshot for hierarchy, clipping, weak contrast, and repeated-card composition;
- exercise navigation, period changes, drill-downs, pause/resume, and reduced-motion behavior;
- check console errors and source-state behavior;
- confirm every visible value has a normalized source or an explicit synthetic/unavailable label.
