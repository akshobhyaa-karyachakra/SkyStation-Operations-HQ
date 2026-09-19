#!/usr/bin/env python3
"""Check that tracked generated deliverables have their repository sources."""
from pathlib import Path

required = {
    Path("docs/SkyStation-Operations-HQ-Project-Handoff.pdf"): b"%PDF-",
}
for artifact, magic in required.items():
    if not artifact.is_file():
        raise SystemExit(f"Missing generated artifact: {artifact}")
    if artifact.read_bytes()[: len(magic)] != magic:
        raise SystemExit(f"Invalid generated artifact header: {artifact}")

for source in (Path("docs/generated-artifacts.md"), Path("docs/documentation-roadmap.md")):
    if not source.is_file():
        raise SystemExit(f"Missing generated-artifact source documentation: {source}")

print("PASS: generated artifact presence and headers")
