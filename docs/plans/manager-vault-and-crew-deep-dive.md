# Manager Vault and Crew Deep-Dive Implementation Plan

> **For Hermes:** Use the subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Create a public central dashboard with a protected Manager Vault where authorized managers can edit role lenses, responsibility weights, monthly reviews, and confidential 1:1 evidence for a selected Crew member.

**Architecture:** Keep the public dashboard and Manager Vault as separate access surfaces. The public surface reads only customer-safe operational summaries; the protected surface reads protected APIs and owns manager edits. Crew deep dive remains the single context for the selected person, while role-lens definitions, responsibility weights, monthly score inputs, review history, PDF evidence, and audit events are connected through stable internal person and record IDs.

**Tech Stack:** Existing static preview (`rebuild-preview.html`), protected shell (`index.html`), Python portal server (`scripts/portal_server.py`), JSON runtime storage for the preview/prototype, protected API tests in `tests/test_portal_server.py`, and Crew readiness tests in `tests/test_crew_repository.py`.

---

## Product structure

### Public central dashboard

- Shows the approved operational overview and safe aggregate states.
- Does not expose the six manager tabs, employee performance records, responsibilities, edit requests, 1:1 PDFs, manager notes, credentials, snapshots, or protected API responses.
- Uses explicit unavailable, needs-review, stale, and authentication states when protected data is required.
- Provides a clearly labelled entry point to the Manager Vault without revealing whether a specific person or confidential record exists.

### Manager Vault

- Separate protected route and navigation shell.
- Requires server-side authentication before returning protected HTML data or API responses.
- Uses role-based authorization: manager, approved manager/editor, and read-only approved personnel.
- Shows the six management tabs only after authorization succeeds.
- Records login/session events and every protected mutation in an audit trail.
- Uses short-lived sessions and short-lived PDF download URLs; never stores credentials in the repository, fixtures, public HTML, or logs.

### Selected-person deep dive

- The selected Crew person is established once from the Crew directory and remains the context for all edits.
- The deep dive contains Role Lens, Responsibilities, Update monthly review, Review history, edit requests, and monthly 1:1 evidence.
- No duplicate person selector appears inside any of these panels.

---

## Data and logic contracts

### Role lens

A role lens is a versioned definition containing:

- role ID and display name;
- band/level;
- responsibility/KPI definitions;
- weightage for each responsibility;
- effective-from date and optional effective-to date;
- editor, timestamp, and audit event;
- status: draft, active, superseded, or needs review.

The active role lens is selected for the person. Changing it must refresh the visible responsibility rows and monthly score inputs before the manager can save the monthly review.

### Responsibility weightage

- Weightage is editable inside **Operation Role Lens → Responsibilities**.
- The editor must show each responsibility, current weight, editable weight, total weight, and validation state.
- Total weight must equal 100 before activation.
- Duplicate responsibility IDs are rejected.
- A save creates a new version rather than overwriting history.
- A role-lens change does not silently rewrite already closed monthly reviews; it applies to new or explicitly reopened review periods.

### Monthly scoring

- Each monthly review references the person, active role-lens version, review period, reviewer, and responsibility ratings.
- The cumulative score is calculated from the active role-lens weights and the entered ratings.
- The named performance rating remains a separate human-entered field: Needs improvement, Developing, Meets expectations, or Exceeds expectations.
- Closed reviews retain the exact role-lens version and weights used at the time of calculation.
- A role-lens change marks an open review as requiring recalculation/review and explains why the score changed.
- No productivity, capacity, ranking, or unsupported performance metric is inferred.

### Review history and 1:1 evidence

- Each month row is clickable from the selected person’s deep dive.
- Clicking a month opens the right-side drawer for that person and month.
- The drawer shows review status, role-lens version, responsibility weights, entered ratings, calculated score, named rating, evidence state, manager note, audit events, and the authorized 1:1 PDF record.
- PDF records include version, uploader, upload timestamp, file type, review month, access policy, and audit reference.
- Unauthorized users cannot enumerate confidential record existence or metadata.

---

## Implementation sequence

### Task 1: Freeze the Manager Vault information architecture

**Files:** `docs/plans/manager-vault-and-crew-deep-dive.md`, approved Crew logic contract, `index.html`, `rebuild-preview.html`.

- Define the public route, protected Vault route, six protected tabs, and selected-person deep-dive states.
- Mark which fields are public, manager-only, approved-editor-only, and confidential.
- Confirm the public preview contains synthetic data only.
- Acceptance: a route/access matrix exists before auth or UI changes begin.

### Task 2: Add protected route and authorization boundaries

**Files:** `scripts/portal_server.py`, `tests/test_portal_server.py`.

- Add protected Manager Vault route handling with fail-closed authentication.
- Add authorization checks to every protected Crew read/write route.
- Return non-enumerable unauthorized responses for confidential records.
- Add tests for unauthenticated access, read-only access, approved manager access, and denied mutations.
- Acceptance: protected HTML and APIs reveal no six-tab content before authorization.

### Task 3: Create role-lens and responsibility schemas

**Files:** `scripts/portal_server.py`, `data/` runtime schema module if introduced, `tests/test_portal_server.py`.

- Define role-lens version, responsibility, weight, effective period, editor, and audit fields.
- Validate responsibility IDs, numeric weights, total weight of exactly 100, and version concurrency.
- Keep runtime storage outside Git and preserve source framework references.
- Acceptance: invalid totals, duplicate IDs, missing editor metadata, and stale versions are rejected.

### Task 4: Build the Manager Vault shell

**Files:** `index.html`, `scripts/portal_server.py`, protected API tests.

- Add the protected Vault entry route and authenticated shell.
- Render six tabs only after authorization succeeds.
- Keep public central dashboard navigation separate from Vault navigation.
- Add visible current-user, authorization state, and sign-out controls without exposing secrets.
- Acceptance: public users see the public dashboard only; approved users see the six tabs after authentication.

### Task 5: Add Role Lens editing in the selected-person deep dive

**Files:** `index.html`, `scripts/portal_server.py`, `tests/test_portal_server.py`.

- Add an explicit Edit role lens action.
- Show responsibility rows with editable weightage, total weight, validation, effective date, and version state.
- Add Save draft, Activate version, and Cancel actions according to authorization.
- Display the selected person and active role-lens version in the same panel.
- Acceptance: managers can edit weightage to a valid 100% total, activate a new version, and see the version in the person deep dive.

### Task 6: Connect role-lens changes to monthly score inputs

**Files:** `index.html`, scoring logic module/server route, `tests/test_portal_server.py`.

- Render monthly score rows from the active role-lens version, not from hardcoded person defaults.
- Recalculate the cumulative score whenever weights or ratings change.
- Show a review-required state when an open review references a superseded lens.
- Preserve closed review scores and their historical weights.
- Acceptance: changing a responsibility weight changes the calculated open-month score and does not mutate a closed month.

### Task 7: Complete month history drawer and PDF evidence

**Files:** `index.html`, `scripts/portal_server.py`, `tests/test_portal_server.py`.

- Make every review-history month open the existing right-side drawer.
- Show month-specific score, role-lens version, weights, ratings, notes, evidence state, audit trail, and PDF version.
- Add authorized PDF view/download behavior with short-lived URLs.
- Acceptance: the drawer always matches the selected person and month; unauthorized users cannot enumerate PDF records.

### Task 8: Add audit and change history

**Files:** `scripts/portal_server.py`, runtime storage schema, `tests/test_portal_server.py`.

- Record login, role-lens draft, activation, responsibility edit, weight change, monthly review save, PDF upload, view, and download events.
- Record actor, timestamp, person ID, record ID, previous version, new version, and reason where required.
- Make audit history visible in the manager drawer while keeping it out of the public dashboard.
- Acceptance: every protected mutation has a verifiable audit event.

### Task 9: Keep the public preview safe and structurally separate

**Files:** `rebuild-preview.html`, preview checks.

- Show only clearly synthetic workflow states and no real employee or confidential records.
- Keep Manager Vault controls out of the public surface; use a labelled preview affordance only if visual review requires it.
- Verify route containment, no credential strings, no direct protected API calls, and no confidential PDF metadata.
- Acceptance: public HTML remains synthetic, unauthenticated, and non-persistent.

### Task 10: Verify and deploy in gates

**Files:** tests and deployment checks.

- Run Python compilation and protected API tests.
- Extract and run `node --check` for every embedded script.
- Run `git diff --check`.
- Perform hosted HTTP checks after propagation.
- When browser tooling becomes available, verify public route, Vault login, six-tab visibility, selected-person editing, role-weight recalculation, month drawer, and PDF view at desktop and narrow widths.
- Do not call the feature production-ready until auth, authorization, audit, protected API, and hosted checks all pass.

---

## Design principles

- Design for the manager’s decision flow: select person → inspect role lens → edit responsibility/weight → review recalculated monthly score → attach evidence → save with audit history.
- Keep the public dashboard calm and useful; move sensitive depth into the Vault rather than hiding sensitive controls in public cards.
- Treat role-lens versions as historical contracts, not mutable labels.
- Never recalculate closed historical reviews against today’s role lens.
- Make every state visible: draft, active, superseded, needs review, unavailable, unauthorized, and stale.
- Use synthetic preview data only; production records remain behind protected APIs.
