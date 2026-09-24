# System Architecture and Deployment

Status: In review  
Last reviewed: 2026-09-19

## Intended architecture

```text
Source boards / approved systems
        ↓
Protected server-side sync adapters
        ↓
Validated normalized snapshots
        ↓
Public-safe projection       Protected Manager Vault projection
        ↓                                  ↓
Public Wallboard / Central Dashboard     Authenticated Deep Dive
```

The browser never calls Monday directly. Stable source IDs and explicit relations are used for joins; display names are presentation values only.

## Current repository components

- Static portal UI: `rebuild-preview.html`.
- Static wallboard UI: `public-wallboard.html`.
- Protected API/runtime: `scripts/portal_server.py`.
- Sync adapters: activity repository, flight operations, site activities, processing/QA, report submission, work tracker, inventory, incident logs, customer billing, crew repository, role framework, and workflow network.
- Validation/tests: `tests/` and `scripts/validate_crew_snapshot.py`.
- GitHub Pages: static publication from `main`.

## Runtime boundaries

- `PORTAL_API_TOKEN` is required for protected API access unless an explicit loopback development bypass is enabled.
- `MONDAY_API_TOKEN` belongs only in server-side runtime configuration.
- Runtime snapshots remain outside the public repository.
- `/api/public-status` exposes only source state, schema version, and update timestamp.
- Missing or invalid snapshots produce explicit failure states; frontend fixtures must not replace them.

## Failure behavior

- No valid snapshot → `unavailable` / HTTP 503.
- Invalid contract → `needs_review` / HTTP 503.
- Older valid snapshot → `stale` with age/update timestamp.
- Sync failure with prior valid snapshot → serve the last valid protected snapshot with error state and age.

## Deployment state

- GitHub Pages deployment is working for the static preview.
- Documentation roadmap commit: `51c057e`.
- Full documentation baseline commit: `728d74f`.
- Latest UI publication before the documentation baseline: commit `0d27e67`.
- Production HTTPS reverse proxy, runtime secret configuration, scheduler, and Manager Vault authentication remain external configuration work. The selected authentication direction is a server-side username/password user store with password hashing, short-lived HttpOnly sessions, reset tokens, lockout/rate limiting, CSRF protection, generic authentication errors, manager allowlisting, and audit events. Passwords and reset tokens must never enter static HTML, Git, snapshots, logs, or Discord.

## Architecture decisions required next

- Confirm production hosting/runtime for `portal_server.py`.
- Confirm snapshot storage and retention.
- Confirm production auth database location, account-provisioning/reset procedure, session secret rotation, cookie policy, and manager allowlist.
- Confirm whether Public Wallboard reads a protected public projection at runtime or remains a static preview until that adapter is deployed.
