# SkyStation Operations HQ Product Requirements

Status: In review  
Version: 0.1 baseline  
Last reviewed: 2026-09-19

## Product purpose

SkyStation Operations HQ is a shared operational review surface for Skylark teams. It brings activity execution, inventory readiness, crew context, analytics, billing evidence, and customer-safe MIS reporting into one navigable workspace with traceable source boundaries.

## Users and surfaces

- Internal operations teams: review activity, delivery, readiness, crew presence, and exceptions.
- Managers: inspect protected evidence, owners, blockers, crew details, and source records.
- Customer-facing teams: prepare approved customer-safe MIS and delivery views.
- Public display viewers: see aggregate operational confidence through the fixed Public Wallboard.

## Current surfaces

- Portal shell: `rebuild-preview.html`, currently synthetic preview with route buttons for Activity, Public Wallboard, Inventory, Crew, Analytics, Billing, MIS, and Manager Vault.
- Public Wallboard: `public-wallboard.html`, six fixed 16:9 screens with public-safe aggregate content.
- Protected runtime: `scripts/portal_server.py`, fail-closed API boundary for source-backed projections.
- Manager Vault: planned/prototype boundary; production authentication is not complete.

## Public Wallboard requirements

The wallboard must answer, without scrolling or interaction:

1. How is the operation performing?
2. What is moving through the delivery chain?
3. What is the verified crew presence state?
4. Where is work active at region level?
5. What has been reported or delivered?
6. Is the operating system ready?

Each screen must fit inside one viewport, use aggregate public-safe data, show source/freshness state, and support automatic cycling, pause, previous/next, restart, hidden-tab pause, and reduced motion.

## Explicit non-goals

- No browser-to-Monday calls.
- No public names, board/item IDs, billing values, serial numbers, credentials, internal notes, or unresolved root-cause narratives.
- No inferred utilization, workload, capacity gap, availability from missing records, or completion from planning data.
- No production Manager Vault authentication in the current preview release.

## Current status

- Product/design baseline: implemented in source and published wallboard.
- Protected public projection: adapter/runtime work is in progress and not yet the hosted static wallboard source.
- Crew availability adapter: present; current source snapshot is validated in tests.
- Role framework adapter/tests: present in the working tree, not included in the latest published UI commit.
- Screenshot/browser visual QA: pending because the browser harness has not started.

## Success criteria

- Each public screen is independently understandable at 1920×1080 and 1366×768.
- Public output contains only approved fields and explicit state labels.
- Protected API routes fail closed without the runtime token.
- Source-backed values never silently become zeros or fixtures.
- Tests, public scan, visual QA, deployment, and rollback evidence are recorded before release.
