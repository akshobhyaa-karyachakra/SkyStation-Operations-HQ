# UI Consistency and Motion Audit

**Project:** SkyStation Operations HQ internal portal  
**Branch:** `polish/ui-consistency`  
**Mode:** Preserve-mode refinement  
**Source:** `rebuild-preview.html` at `d9c65ae`  
**Date:** 2026-09-19

## Design read

Reading this as: a source-safe internal operations console for operational users, with a dark carbon/graphite language, orange Skylark accent, compact data hierarchy, and restrained motion that explains state changes without competing with work.

## Scope guardrails

This pass preserves:

- Existing routes and navigation labels.
- Existing information architecture and tab order.
- Existing synthetic preview data and data flow.
- Existing public/protected boundary and `SYNTHETIC DEMO` / `NO AUTHENTICATION` messaging.
- Existing chart, workflow, crew, inventory, billing, MIS, and Manager Vault behavior.
- Public Wallboard redesign as a separate track.

No Monday integration, source contract, adapter, server, test, or business-logic change belongs in this pass.

## Source inventory

`rebuild-preview.html` is a 390,431-byte single-file preview with 171 lines, 39 style blocks, 5 script blocks, 99 buttons, 10 route controls, and 697 references to Analytics surfaces. The source contains 35 keyframe declarations, 46 CSS transitions, 87 animation declarations, 31 reduced-motion references, and 45 focus-related rules.

The current surface already includes:

- Activity Tracking.
- Public Wallboard navigation.
- Inventory with fleet/hardware tabs.
- Crew Management with overview, band management, and deep-dive modes.
- Analytics with period controls, filters, workflow constellation, charts, and drill-down behavior.
- Billing.
- MIS.
- Manager Vault preview states.
- Synthetic-data and no-authentication labels.
- Workflow renderer guards and visible-state initialization.
- Focus-visible styling and reduced-motion overrides.

## What is working well

1. **The visual language is established.** Carbon, graphite, orange, teal, amber, red, blue, and violet state semantics appear as a coherent operations-console system.
2. **The portal has real interaction coverage.** Route controls, inventory tabs, activity filters, analytics filters, crew modes, drill-downs, drawer states, and animated numeric transitions are wired in the source.
3. **Motion already communicates some state.** Workflow reveal, crew chart drawing, view entry, metric count-up, drill focus, and status transitions have identifiable operational purposes.
4. **Accessibility foundations exist.** The source includes reduced-motion media rules, focus-visible outlines, semantic labels on several controls, and non-motion fallback behavior in key animation paths.
5. **The preview boundary is visible.** Synthetic data and no-authentication messaging are present, which prevents the static preview from being mistaken for a live operational surface.

## Refinement opportunities

### 1. Consolidate the style system

The file contains many late-appended style blocks, including repeated overrides for inventory, crew, analytics, billing, MIS, workflow, and branding. The refinement should preserve computed behavior while consolidating duplicate tokens and repeated component rules into a clearer layer order.

**Risk:** low if selectors and values are preserved; medium if specificity changes.  
**Acceptance:** no route or computed-state regression; one documented token layer; no duplicate override needed for the same component state.

### 2. Tighten typography and hierarchy

The portal uses a compact Inter/system stack with several local font declarations and many small labels. Refine heading, eyebrow, supporting text, table text, and numeric emphasis so the first viewport has a clearer primary signal and secondary evidence hierarchy without changing copy.

**Risk:** low.  
**Acceptance:** existing copy unchanged; key metrics remain legible; tables do not wrap unexpectedly at desktop or narrow fallback widths.

### 3. Normalize spacing and panel rhythm

The portal has many dense modules assembled through feature-specific overrides. Establish consistent spacing steps, panel padding, heading gaps, tab gaps, and chart insets while preserving each route’s composition.

**Risk:** medium because the single-file layout has route-specific height assumptions.  
**Acceptance:** no clipping or overflow introduced; no panel loses visible evidence; narrow layouts remain usable.

### 4. Refine control states

Buttons, tabs, filters, selects, drawer triggers, and drill-down controls already work, but their hover, active, focus, pressed, disabled, and selected states should share one operational interaction language.

**Risk:** low.  
**Acceptance:** every interactive control has a visible non-color-only state; focus-visible remains clear; active state does not depend on motion.

### 5. Reduce motion duplication and competition

The source has 87 animation declarations and multiple successive crew/chart/workflow animation overrides. The goal is not more motion. It is to give each surface one entry rhythm, one data-reveal rhythm, and one interaction-feedback rhythm.

Recommended motion model:

- **Route entry:** short opacity/translate reveal, 240-360ms.
- **Metric change:** count-up only when the value changes or the view first opens; no repeated looping.
- **Workflow:** one staged reveal for topology and one subtle state emphasis for attention nodes.
- **Crew charts:** draw-once reveal with reduced-motion static fallback.
- **Controls:** 120-180ms transform/border feedback, no bounce.
- **Drill focus:** brief outline/halo acknowledgement, never a persistent glow.

**Risk:** medium because existing animation classes are distributed across many blocks.  
**Acceptance:** reduced-motion mode removes decorative motion; keyboard interactions remain immediate; animation does not restart excessively on unrelated state changes.

### 6. Improve loading, empty, unavailable, and review states

The preview already labels synthetic data, but each major route should make state hierarchy visually consistent: normal, attention, review, unavailable, and no-data. These states should be represented with text and structure, not color or animation alone.

**Risk:** low if copy and synthetic semantics are preserved.  
**Acceptance:** every state has a visible label, explanation, and stable layout; no fixture number appears to substitute for unavailable data.

### 7. Responsive and overflow hardening

The portal uses a fixed-height application shell and several dense grids. The audit should verify route-level behavior at 1920×1080, 1366×768, and narrow fallback widths, with special attention to analytics workflow, billing matrices, crew deep dive, inventory hardware, and MIS panels.

**Risk:** medium.  
**Acceptance:** no accidental page-level horizontal scroll; essential controls remain reachable; dense tables have an intentional narrow-screen treatment.

### 8. Accessibility and motion safety

Keep and strengthen the existing reduced-motion behavior. Avoid introducing scroll listeners, continuous React-state animation loops, full-screen parallax, or unpausable ambient motion. Animate only transform and opacity where possible.

**Acceptance:** `prefers-reduced-motion: reduce` presents stable final states; keyboard focus is visible; state meaning remains available without animation; controls have accessible names.

## Proposed implementation batches after approval

1. **Tokens and base rhythm:** consolidate shared variables, typography, radii, borders, shadows, and spacing without changing layout structure.
2. **Navigation and controls:** normalize active, hover, focus, pressed, and selected states.
3. **Route surfaces:** refine Activity, Inventory, Crew, Analytics, Billing, MIS, and Manager Vault one surface at a time.
4. **Motion pass:** remove duplicate animation overrides and implement the restrained motion model above.
5. **Responsive/accessibility pass:** test narrow fallback, focus, reduced motion, and state visibility.
6. **Verification:** syntax, test suite, `git diff --check`, source scans, and browser screenshots when a supported browser is available.

## Verification status

- Source audit: complete.
- Clean isolated worktree: complete.
- Before screenshot: blocked because no supported Chromium browser is available in the environment.
- Browser runtime/console QA: pending.
- Code edits: not started.
- Existing source/adapter/contract work in the original worktree: untouched.

## Approval gate

This audit deliberately stops before editing `rebuild-preview.html`. Approve the refinement scope and implementation batches before code changes begin.
