# Decision Log

Status: Active  
Last reviewed: 2026-09-19

## 2026-09-19 — Documentation system created

- Decision: maintain product, design, architecture, data, security, QA, release, and operations documents alongside implementation.
- Source: Discord planning thread and `docs/documentation-roadmap.md`.
- Effect: feature work must update affected documents before release.

## 2026-09-17 — Public Wallboard published

- Decision: use a separate six-screen fixed 16:9 public display.
- Commit: `0d27e67` for the latest UI fixes; earlier wallboard commits are in Git history.
- Effect: public display is separated from the internal portal shell and cycles through aggregate operational views.

## 2026-09-17 — Crew public presence source narrowed

- Decision: use Crew Repository `Availability` as the sole public daily-presence source.
- Effect: blank status becomes Awaiting confirmation; historical statuses are excluded; no inferred capacity/utilization.

## 2026-09-17 — Protected source boundary retained

- Decision: browser does not call Monday directly; server adapters and normalized snapshots remain the integration boundary.
- Effect: public/static UI must not contain secrets or raw protected source records.

## 2026-09-19 — Internal portal polish versus Public Dashboard redesign

- Decision: preserve the current overall structure, navigation, logic, routes, and data flow of the existing internal portal tabs; future work there is polish-only unless separately approved.
- Polish scope: spacing, alignment, typography, component consistency, responsive fixes, accessibility, loading/empty/error states, and restrained motion.
- Separate track: the Public Dashboard/Wallboard remains eligible for a broader redesign and will be planned independently.
- Source: `hermes_polish_prompt.pdf` and the Discord direction in this thread.
- Effect: do not apply the internal portal polish freeze to the Public Dashboard; do not redesign the internal portal tabs implicitly while polishing them.

## Open decisions

- Canonical business-logic Google Doc URL and owner.
- Production runtime/hosting for protected API.
- Manager Vault authentication and allowlist.
- Public wallboard runtime projection versus static preview mode.
- Final approved public metric list for the next wallboard revision.
