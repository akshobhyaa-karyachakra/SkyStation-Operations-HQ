# QA and Release Plan

Status: In review  
Last reviewed: 2026-09-19

## Current baseline

- Repository suite at the last UI release: 76 passed.
- GitHub Pages deployment: successful for commits through the documentation baseline.
- Inline HTML JavaScript parsing: passed for portal and wallboard.
- Public wallboard: six fixed screens, no-scroll CSS contract, public scan passed.
- Browser screenshot QA: pending because the available browser harness has not started.

## Required checks per feature

1. Read source and document the intended behavior.
2. Add/adjust contract or unit tests.
3. Parse/check JavaScript and Python syntax.
4. Run `git diff --check`.
5. Run `uv run --with pytest pytest -q`.
6. Run public-safety and secret scans.
7. Check console/runtime errors in a real browser when available.
8. Check 1920×1080, 1366×768, and narrow fallback behavior.
9. Verify no accidental horizontal/vertical scrolling in Display Mode.
10. Verify hosted artifact after deployment.

## Wallboard acceptance

- Every screen is independently understandable without hover or click.
- Six screens cycle, pause, resume, previous, next, and restart correctly.
- Hidden tab pauses; reduced motion produces final states.
- Main portal return link works.
- Favicon resolves from the delivered path.
- Public content contains no prohibited identifiers or private detail.

## Analytics acceptance

- Analytics route initializes the 3D/network surface without a manual refresh.
- Re-entering Analytics remeasures and rerenders the canvas.
- Daily/weekly/monthly states change visible data, not just selected styling.
- Missing or invalid source states remain visible and do not become zeros.

## Release evidence

Record commit SHA, test output, public scan output, deployment run ID/status, hosted URL, and known limitations. Do not claim screenshot QA if the browser could not render the page.
