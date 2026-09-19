# Contributing to SkyStation Operations HQ

This repository contains the SkyStation internal operations portal, the public-safe TV wallboard, protected runtime adapters, source contracts, and project documentation.

## Before making a change

- Start from an up-to-date `main` branch.
- Create a focused branch such as `feature/activity-contract`, `fix/portal-state`, `polish/wallboard-motion`, or `docs/source-map`.
- Do not work directly on `main`.
- Keep local runtime snapshots, credentials, and generated caches out of Git.
- Read the relevant contract and decision-log documents before changing adapters, joins, metrics, or public projections.

## Local checks

```bash
uv run --with pytest pytest -q
python3 -m compileall -q scripts tests
python3 scripts/validate_public_surface.py
python3 - <<'PY'
from pathlib import Path
import re
for source in ("rebuild-preview.html", "public-wallboard.html"):
    html = Path(source).read_text(encoding="utf-8")
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S)
    Path(f"/tmp/{Path(source).stem}.js").write_text("\n".join(scripts), encoding="utf-8")
PY
node --check /tmp/rebuild-preview.js
node --check /tmp/public-wallboard.js
git diff --check
```

## Change boundaries

- Internal portal polish preserves routes, information architecture, labels, logic, and data flow.
- Public Wallboard redesign is a separate product track and must use public-safe projections.
- Browser code must not call Monday directly.
- Unsupported metrics stay omitted or in a review/unavailable state.
- Work Tracker is not a delivery workflow stage.
- Planned quantity is not delivered output.
- Stable source IDs and approved relations are required for joins.
- Credentials and secrets must never be committed; use `[REDACTED]` in documentation.

## Pull requests

Every pull request should explain the user-visible result, affected contracts or routes, verification performed, and any known limitation. Keep commits focused and avoid bundling unrelated dirty-worktree changes.

Changes to source contracts, security boundaries, public projections, or runtime authorization require explicit review from the relevant owner before merge.
