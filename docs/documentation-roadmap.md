# SkyStation Operations HQ Documentation Roadmap

Status: working documentation system for the portal build.

This roadmap keeps product, design, architecture, data, security, implementation, and release decisions synchronized with the codebase. Each document has one job and one canonical location. Do not create a second document for the same truth; update or link the existing one.

## Documentation rules

1. **Write the decision before the implementation.** A feature does not enter build until its user outcome, information boundary, source, and acceptance criteria are recorded.
2. **Keep one source of truth per topic.** The existing business-logic Google Doc remains the canonical logic/rules source until it is deliberately migrated or linked here.
3. **Link, do not copy.** Repository documents may summarize a Google Doc, but they must record its title, URL, owner, last-reviewed date, and the sections they depend on.
4. **Every document has a status.** Use `Draft`, `In review`, `Approved`, `Superseded`, or `Archived`.
5. **Every implementation change updates its companion documents in the same work slice.** A changed route updates the information architecture; a changed source field updates the data contract; a changed security boundary updates the threat model and production checklist.
6. **Public and protected surfaces are documented separately.** Public Wallboard and Central Dashboard rules must never be inferred from Manager Vault rules.
7. **Use evidence labels.** Mark statements as `Source-backed`, `Derived`, `Design decision`, `Assumption`, or `Awaiting confirmation`.

## Canonical document set

### 1. Product Requirements Document — create first

**Canonical path:** `docs/product-requirements.md`

**Purpose:** Define why the portal exists, who uses each surface, the jobs to be done, scope, non-goals, success measures, and release phases.

**Must contain:**

- Product purpose and user groups.
- Public Wallboard, Central Dashboard, Deep Dive, Manager Vault, and integration boundaries.
- User problems and management questions each module answers.
- In-scope and out-of-scope capabilities.
- Public-safe information boundary.
- Success criteria and launch gates.
- Open questions and decision owners.

**Update when:** scope, audience, priority, or launch criteria changes.

**Current inputs:** `PRODUCT.md`, the existing logic Google Doc, and the Discord decisions in this thread.

### 2. Business Logic and Rules — existing Google Doc

**Canonical source:** existing Google Doc owned by the product/operations owner.

**Purpose:** Define operational rules and interpretation: planned versus executed work, report due dates, crew availability, source precedence, status transitions, inclusion/exclusion rules, and unsupported metrics.

**Repository companion:** `docs/business-logic-index.md`

The companion should contain only a linked index, not a duplicate copy:

- Google Doc title and URL.
- Owner and review cadence.
- Rule categories.
- Which code/data-contract files implement each category.
- Last synchronized date.
- Unresolved rules requiring product confirmation.

**Update when:** a metric definition, status meaning, source precedence, or calculation changes.

### 3. Information Architecture and Route Map

**Canonical path:** `docs/information-architecture.md`

**Purpose:** Define the portal shell, routes, navigation, display modes, public/protected surfaces, and how users move between them.

**Must contain:**

- Route map for Portal, Public Wallboard, Central Dashboard, Deep Dive, and Manager Vault.
- Navigation labels and ownership.
- Entry/exit paths, including Wallboard → Main Portal.
- Display Mode behavior and auto-cycle rules.
- Authentication boundaries.
- Empty, loading, stale, unavailable, and needs-review states.

**Current inputs:** `docs/frontend-design-plan.md`, `rebuild-preview.html`, and the wallboard decisions.

### 4. UX and Visual Design Specification

**Canonical path:** `docs/ux-design-spec.md`

**Purpose:** Make the visual and interaction system explicit before each screen is built.

**Must contain:**

- Design tokens, typography, spacing, color/status semantics, and icon rules.
- Component inventory and composition rules.
- Screen-by-screen wireframes or annotated layouts.
- TV wallboard rules for 1920×1080, 1366×768, and narrow fallback.
- Motion principles and reduced-motion behavior.
- Accessibility requirements.
- Screenshot references and visual acceptance criteria.

**Current inputs:** `docs/frontend-design-plan.md`, `PRODUCT.md`, and the portal implementation.

### 5. System Architecture and Deployment

**Canonical path:** `docs/architecture.md`

**Purpose:** Explain how the browser, protected server, sync workers, snapshots, authentication, and deployment fit together.

**Must contain:**

- Context diagram.
- Runtime/container diagram.
- Browser → protected API → normalized snapshot flow.
- Public projection versus Manager Vault data flow.
- Secrets and credential boundaries.
- Hosting, reverse proxy, scheduler, storage, and deployment model.
- Failure behavior and recovery paths.
- Environments and configuration ownership.

**Current inputs:** `scripts/portal_server.py`, `docs/production-readiness.md`, `docs/data-contract.md`, and `.github/` deployment configuration.

### 6. Data Contract and Source Map

**Canonical paths:**

- `docs/data-contract.md`
- `docs/monday-source-map.md`
- `docs/analytics-monday-workflow-contract.md`

**Purpose:** Define canonical sources, normalized entities, stable joins, derived fields, freshness states, public projection rules, and prohibited inference.

These documents already exist and should be maintained rather than replaced. Add a short index and cross-links from the PRD and architecture document.

**Update when:** a source board, column, relation, normalized field, adapter, snapshot schema, or public projection changes.

### 7. API and Runtime Contract

**Canonical path:** `docs/api-contract.md`

**Purpose:** Document protected and public endpoints independently from frontend implementation.

**Must contain:**

- Endpoint list and methods.
- Authentication requirements.
- Request/response examples with redacted values.
- Schema versions.
- Freshness and failure responses.
- Public versus protected fields.
- Rate limits and caching expectations.
- Contract-test references.

**Update when:** an endpoint, schema, auth requirement, error state, or projection changes.

### 8. Security, Privacy, and Threat Model

**Canonical path:** `docs/security-and-privacy.md`

**Purpose:** Make the public/protected boundary reviewable before production access is enabled.

**Must contain:**

- Assets and trust boundaries.
- Threats to public exposure, source leakage, secrets, authentication, and stale data.
- Public Wallboard allowlist and denylist.
- Manager Vault authorization model.
- Secret handling rules.
- Logging and audit requirements.
- Abuse cases and mitigations.
- Security release checklist.

**Update when:** a new data source, route, auth flow, public metric, integration, or deployment surface is added.

### 9. Architecture Decision Records

**Canonical path:** `docs/adr/ADR-XXXX-title.md`

**Purpose:** Preserve important decisions without hiding them inside chat or implementation commits.

Create an ADR for decisions that affect future work, such as:

- Public Wallboard as a separate static projection.
- Monday accessed only through protected server adapters.
- Crew `Availability` as the sole public daily-presence source.
- Stable relation IDs instead of display-name joins.
- Six-screen wallboard cycle.
- Manager Vault boundary.
- Fail-closed behavior for missing/invalid snapshots.

Each ADR should contain: context, decision, alternatives, consequences, status, owner, and date.

### 10. Implementation Plan and Milestones

**Canonical paths:**

- `docs/plans/portal-roadmap.md`
- Feature-specific plans under `docs/plans/`

**Purpose:** Turn approved product/design/architecture decisions into small buildable slices with exact files, tests, and verification commands.

**Required structure:** goal, architecture, tasks, dependencies, acceptance criteria, test plan, rollout/rollback, and documentation updates.

Existing plans such as `docs/frontend-redesign-execution-plan.md`, `docs/analytics-build-plan.md`, and `docs/plans/manager-vault-and-crew-deep-dive.md` should be indexed from the roadmap rather than replaced.

### 11. QA, Verification, and Release Plan

**Canonical path:** `docs/qa-and-release.md`

**Purpose:** Define how every slice is verified before it is published.

**Must contain:**

- Unit and contract tests.
- API authorization tests.
- Public-safety scans.
- Browser console and runtime checks.
- Visual QA at target viewports.
- Accessibility and reduced-motion checks.
- Data freshness and failure-state checks.
- Deployment verification.
- Rollback steps.
- Release evidence required in the PR/commit.

The current 76-test baseline and the browser-harness limitation belong here as dated evidence, not as permanent acceptance criteria.

### 12. Operations Runbook

**Canonical path:** `docs/operations-runbook.md`

**Purpose:** Help an operator deploy, sync, diagnose, and recover the portal without relying on chat history.

**Must contain:**

- Local development commands.
- Snapshot sync and validation commands.
- Environment variables by owner; never values.
- Deployment and Pages verification.
- Common failure states.
- Stale/unavailable/needs-review response.
- Log locations and safe redaction rules.
- Rollback and incident escalation.

### 13. Decision and Change Log

**Canonical path:** `docs/decision-log.md`

**Purpose:** Keep a compact chronological record of approved changes that do not warrant a full ADR.

Each entry should include date, decision, source, affected files/documents, owner, and follow-up.

Use ADRs for durable architecture choices; use this log for smaller product, content, and delivery decisions.

## Build-along documentation cadence

### Phase A — Product and boundary

Create or confirm:

1. Product Requirements Document.
2. Business Logic index linking the existing Google Doc.
3. Information Architecture and Route Map.
4. Initial Security and Privacy boundary.

**Gate:** user groups, public/protected surfaces, scope, and source-of-truth rules are approved.

### Phase B — Experience and architecture

Create or update:

1. UX and Visual Design Specification.
2. System Architecture and Deployment.
3. Data Contract and Source Map.
4. Initial ADRs.

**Gate:** every planned screen has a source, state model, layout, and verification path.

### Phase C — Implementation

For each feature slice, update side by side:

1. Feature implementation plan.
2. Relevant UX section.
3. Relevant data/API contract.
4. Relevant ADR or decision-log entry.
5. Tests and QA acceptance criteria.

**Gate:** code and documents describe the same behavior before merge.

### Phase D — Release and operation

Update:

1. QA and Release Plan with actual evidence.
2. Operations Runbook with the deployed path and recovery steps.
3. Decision Log with the release decision.
4. Production Readiness with remaining external configuration.

**Gate:** hosted artifact, source commit, tests, public-safety scan, and rollback path are all identified.

## Ownership model

- **Product/operations owner:** product requirements, business logic, public information boundary, priorities.
- **Design owner:** UX specification, visual language, wallboard compositions, motion, accessibility.
- **Engineering owner:** architecture, API/runtime contract, implementation plans, ADRs.
- **Data/integration owner:** source map, normalized data contracts, sync behavior, freshness states.
- **Release/operations owner:** QA/release plan, deployment evidence, runbook, rollback.

One person may hold multiple roles, but every document should still name the role responsible for keeping it current.

## Immediate document sequence

The next documentation work should happen in this order:

1. Create `docs/business-logic-index.md` and link the existing Google Doc.
2. Create `docs/product-requirements.md` from `PRODUCT.md`, the existing logic rules, and the approved public-wallboard scope.
3. Create `docs/information-architecture.md` for the current portal, Public Wallboard, and future Manager Vault.
4. Create `docs/architecture.md` from the current protected adapter and snapshot implementation.
5. Create `docs/security-and-privacy.md` before production authentication or public runtime data is enabled.
6. Create `docs/qa-and-release.md` and move the current verification checklist into it.
7. Create the first ADRs for public projection, source boundaries, crew availability, and six-screen wallboard design.
8. Maintain these documents in the same PR/commit as the implementation they govern.

## Definition of documentation done

A feature is documentation-complete when:

- its user outcome and scope are in the PRD or feature brief;
- its screen and interaction behavior are in the UX specification;
- its source and calculation rules are in the data/business-logic contract;
- its runtime boundary is in the architecture/API/security documents;
- its durable decisions are in an ADR or decision log;
- its implementation plan names files and tests;
- its release evidence and operational recovery steps are recorded.
