#!/usr/bin/env python3
"""Validate a normalized Crew Repository snapshot without contacting Monday."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def validate(snapshot: dict) -> list[str]:
    errors: list[str] = []
    records = snapshot.get("records", [])
    ids = [r.get("monday_item_id") for r in records]
    names = [r.get("name") for r in records]
    if snapshot.get("schema_version") != "crew.v1":
        errors.append("unsupported schema_version")
    if len(ids) != len(set(ids)):
        errors.append("duplicate Monday item IDs")
    if len(names) != len(set(names)):
        errors.append("duplicate crew names")
    if len(records) != 15:
        errors.append(f"expected 15 records, received {len(records)}")
    if sum(not r.get("historical") for r in records) != 14:
        errors.append("expected 14 active records")
    for record in records:
        for field in ("monday_item_id", "name", "team_group", "official_role", "availability"):
            if not record.get(field):
                errors.append(f"{record.get('name') or record.get('monday_item_id')}: missing {field}")
        if len(record.get("manager", [])) > 1:
            errors.append(f"{record['name']}: multiple managers")
    by_name = {r["name"]: r for r in records}
    for name in ("Aarya Vira", "Ammar Dali"):
        if by_name.get(name, {}).get("team_group") != "SkyStation Operations":
            errors.append(f"{name}: wrong team group")
    return errors


path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/crew_repository.snapshot.json")
snapshot = json.loads(path.read_text())
errors = validate(snapshot)
if errors:
    for error in errors:
        print("VALIDATION_ERROR: " + error)
    raise SystemExit(1)
print(f"valid crew snapshot: {len(snapshot['records'])} records; 14 active; 1 historical")
