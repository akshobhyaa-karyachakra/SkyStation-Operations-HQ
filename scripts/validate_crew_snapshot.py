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
    if snapshot.get("item_count") != len(records):
        errors.append(f"item_count mismatch: metadata={snapshot.get('item_count')}, records={len(records)}")
    active_statuses = {"Available", "Deployed", "On Leave"}
    active_count = sum(r.get("availability") in active_statuses for r in records)
    if active_count + sum(r.get("availability") in {"Terminated", "Resigned"} for r in records) > len(records):
        errors.append("invalid availability classification")
    for record in records:
        for field in ("monday_item_id", "name", "team_group", "official_role"):
            if not record.get(field):
                errors.append(f"{record.get('name') or record.get('monday_item_id')}: missing {field}")
        if len(record.get("manager", [])) > 1:
            errors.append(f"{record['name']}: multiple managers")
    return errors


path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/crew_repository.snapshot.json")
snapshot = json.loads(path.read_text())
errors = validate(snapshot)
if errors:
    for error in errors:
        print("VALIDATION_ERROR: " + error)
    raise SystemExit(1)
print(f"valid crew snapshot: {len(snapshot['records'])} records; {sum(r.get('availability') in {'Available', 'Deployed', 'On Leave'} for r in snapshot['records'])} active; {sum(r.get('availability') in {'Terminated', 'Resigned'} for r in snapshot['records'])} historical")
