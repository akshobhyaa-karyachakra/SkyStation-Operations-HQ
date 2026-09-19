# Repository map

This repository has two maintained browser surfaces and a protected runtime boundary.

## Maintained public entry points

- `index.html` — redirect-only entry to the internal portal preview.
- `rebuild-preview.html` — maintained internal Operations HQ synthetic preview. It is authentication-free and contains no live Monday data.
- `public-wallboard.html` — maintained six-screen public-safe TV wallboard. It must contain aggregate, non-sensitive projections only.

## Compatibility aliases

- `design-preview.html` — legacy URL retained as a redirect to `rebuild-preview.html`.
- `skystation-operations-intelligence-v5.html` — legacy V5 URL retained as a redirect to `rebuild-preview.html`.
- `404.html` — recovery page linking only to maintained entry points.

Legacy aliases must remain small redirects. They must not contain old synthetic people, customer, billing, asset, or internal operational examples.

## Protected runtime and source boundary

- `scripts/portal_server.py` — protected read-only runtime server and API boundary.
- `scripts/sync_*.py` — source adapters and snapshot validators.
- `data/` — local/runtime snapshots, ignored by Git and never published through GitHub Pages.
- `tests/` — source-contract, adapter, server, and public-boundary tests.
- `docs/` — contracts, product decisions, architecture, QA, operations, and generated-document sources.

## Generated or review artifacts

- `docs/SkyStation-Operations-HQ-Project-Handoff.pdf` — generated handoff artifact; its source and regeneration rules are documented in `docs/generated-artifacts.md`.
- `.impeccable/live/config.json` — design-tool configuration for the maintained portal file; it is not runtime application configuration.

## Root-directory rule

New product surfaces should not be added as unrelated root HTML files. Add the active entry point to this map, add a route/ownership note, and update the quality workflow before publishing it.
