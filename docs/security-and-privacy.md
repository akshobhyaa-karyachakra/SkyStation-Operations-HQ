# Security, Privacy, and Threat Model

Status: In review  
Last reviewed: 2026-09-19

## Trust boundaries

1. External source systems and their credentials.
2. Protected sync/runtime environment.
3. Normalized snapshots.
4. Public static/projection surface.
5. Authenticated Manager Vault.

## Protected assets

- API keys, OAuth secrets, passwords, tokens, and connection strings.
- Monday item, board, People, and relation IDs.
- Individual crew names, email, manager, availability history, notes, and performance context.
- Billing values, invoice/payment data, serial numbers, incident narratives, and internal root-cause notes.
- Raw source snapshots and logs containing sensitive fields.

## Public Wallboard allowlist

- Team and region aggregates.
- Approved operational counts and rates.
- Public source/freshness state.
- Customer-safe delivery/readiness outcomes.
- Clearly labelled synthetic or awaiting-source states.

## Public Wallboard denylist

- Credentials and secrets.
- Personal names and individual records.
- Monday board/item/People/relation IDs.
- Billing and financial values.
- Asset serial numbers and replacement costs.
- Internal incident descriptions and unresolved root-cause notes.
- Internal board names and private workflow comments.

## Threats and controls

- Source leakage → filter at adapter/projection time, not only with CSS/UI hiding.
- Browser credential exposure → browser never calls Monday directly.
- Stale data presented as current → carry state and timestamp through every projection.
- Missing data presented as zero → explicit unavailable/needs-review states.
- Name-based incorrect joins → stable explicit relation IDs only.
- Public route exposing protected fixture data → fail closed before rendering protected content.
- Secret persistence → replace any detected secret with `[REDACTED]`; never preserve values.

## Release security gate

Before release, scan source and hosted output for credentials, token-like strings, internal IDs, names, billing terms, raw notes, and prohibited fields. Verify unauthorized protected requests, public projection filtering, stale/invalid responses, and no direct source-system calls from browser JavaScript.
