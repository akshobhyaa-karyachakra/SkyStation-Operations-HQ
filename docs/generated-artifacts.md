# Generated artifacts

Generated files are outputs, not primary sources. Each generated artifact must have a source, generator, command, provenance, and verification record.

## Current artifact register

| Artifact | Status | Source | Generator | Verification |
|---|---|---|---|---|
| `docs/SkyStation-Operations-HQ-Project-Handoff.pdf` | Tracked release artifact | Repository documentation, source inspection, Git history, deployment state, and Discord decisions | Current generator is `/opt/data/build_skystation_handoff.py` outside this repository; migrate it into `scripts/` before the next regeneration | Text extraction and rendered-page checks were completed for the published artifact |
| `/opt/data/SkyStation-Operations-HQ-CONFLICTS.pdf` | Local review artifact, not tracked | `docs/CONFLICTS.md` | `/opt/data/build_conflicts_pdf.py` outside this repository | Local text extraction and rendered-page checks completed; not a repository deliverable |

## Rules

1. Keep generated PDFs under `docs/` only when they are intentional project deliverables; otherwise attach them to a release or review record.
2. Keep the source markdown and generator in the repository before regenerating a tracked artifact.
3. Record the source commit, generation date, generator command, and verification result in the artifact metadata or its companion document.
4. Never put credentials, tokens, private records, or unredacted source exports into a generated artifact.
5. Generated output must not be edited manually; fix the source or generator and regenerate it.
6. A source-document change that affects a generated artifact must either regenerate it in the same pull request or explicitly mark the artifact stale.
7. CI should verify that tracked generated files are present and that the generator/checker can run without network credentials.

## Required next hardening change

Move the handoff and conflicts PDF generators from `/opt/data/` into `scripts/`, add a deterministic local command, and add a text-extraction smoke check. Until that happens, the handoff PDF is valid as a reviewed artifact but not reproducible from a clean clone alone.
