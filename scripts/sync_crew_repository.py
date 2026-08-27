#!/usr/bin/env python3
"""Read-only Monday Crew Repository sync.

Requires MONDAY_API_TOKEN at runtime. The token is never persisted or printed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BOARD_ID = "5030902067"
API_URL = "https://api.monday.com/v2"
API_VERSION = "2025-04"

QUERY = """
query($board_id: ID!) {
  boards(ids: [$board_id]) {
    id
    name
    updated_at
    items_page(limit: 500) {
      items {
        id
        name
        group { id title }
        column_values(ids: [
          \"color_mm6mamdg\", \"text_mm6mk51e\", \"multiple_person_mm6msyq2\",
          \"boolean_mm6m50k9\", \"text_mm6mg4v2\", \"text_mm6mx08z\",
          \"boolean_mm6mvm85\", \"date_mm6mm5pf\", \"email_mm6mx3gz\", \"long_text_mm6mswwm\"
        ]) {
          id
          text
          value
          type
          ... on PeopleValue { persons_and_teams { id kind name } }
        }
      }
    }
  }
}
"""

COLUMN_MAP = {
    "color_mm6mamdg": "availability",
    "text_mm6mk51e": "official_role",
    "multiple_person_mm6msyq2": "manager",
    "boolean_mm6m50k9": "team_lead",
    "text_mm6mg4v2": "band",
    "text_mm6mx08z": "region_location",
    "boolean_mm6mvm85": "daily_tracking_required",
    "date_mm6mm5pf": "start_date",
    "email_mm6mx3gz": "email",
    "long_text_mm6mswwm": "notes",
}


def request(token: str) -> dict:
    body = json.dumps({"query": QUERY, "variables": {"board_id": BOARD_ID}}).encode()
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={"Authorization": token, "Content-Type": "application/json", "API-Version": API_VERSION},
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError("Monday query failed: " + "; ".join(e.get("message", "unknown error") for e in payload["errors"]))
    return payload


def normalize(payload: dict) -> dict:
    boards = payload.get("data", {}).get("boards", [])
    if len(boards) != 1:
        raise ValueError(f"Expected exactly one board, received {len(boards)}")
    board = boards[0]
    records = []
    for item in board.get("items_page", {}).get("items", []):
        fields = {}
        for column in item.get("column_values", []):
            key = COLUMN_MAP.get(column.get("id"))
            if not key:
                continue
            if key == "manager":
                people = column.get("persons_and_teams") or []
                fields["manager"] = [
                    {"monday_user_id": str(p["id"]), "name": p.get("name"), "kind": p.get("kind")}
                    for p in people if p.get("kind") == "person"
                ]
            elif key == "team_lead" or key == "daily_tracking_required":
                fields[key] = column.get("text") == "v"
            else:
                fields[key] = column.get("text") or None
        group = item.get("group") or {}
        availability = fields.get("availability")
        records.append({
            "monday_item_id": str(item["id"]),
            "name": item["name"],
            "team_group_id": group.get("id"),
            "team_group": group.get("title"),
            "official_role": fields.get("official_role"),
            "band": fields.get("band"),
            "manager": fields.get("manager", []),
            "team_lead": fields.get("team_lead", False),
            "region_location": fields.get("region_location"),
            "availability": availability,
            "employment_status": "Historical" if availability in {"Terminated", "Resigned"} else "Active",
            "historical": availability in {"Terminated", "Resigned"},
            "daily_tracking_required": fields.get("daily_tracking_required", False),
            "start_date": fields.get("start_date"),
            "email": fields.get("email"),
            "notes": fields.get("notes"),
        })
    return {
        "schema_version": "crew.v1",
        "source": {"provider": "monday", "board_id": BOARD_ID, "board_name": board.get("name"), "board_updated_at": board.get("updated_at")},
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "records": records,
    }


def validate(snapshot: dict) -> list[str]:
    errors = []
    records = snapshot.get("records", [])
    ids = [r.get("monday_item_id") for r in records]
    if len(ids) != len(set(ids)):
        errors.append("duplicate Monday item IDs")
    if len(records) != 15:
        errors.append(f"expected 15 records, received {len(records)}")
    active = [r for r in records if not r.get("historical")]
    if len(active) != 14:
        errors.append(f"expected 14 active records, received {len(active)}")
    for r in records:
        if not r.get("monday_item_id") or not r.get("name") or not r.get("team_group"):
            errors.append(f"missing identity/team fields for {r.get('name') or r.get('monday_item_id')}")
        if len(r.get("manager", [])) > 1:
            errors.append(f"multiple managers for {r['name']}")
    by_name = {r["name"]: r for r in records}
    for name in ("Aarya Vira", "Ammar Dali"):
        if by_name.get(name, {}).get("team_group") != "SkyStation Operations":
            errors.append(f"{name} is not in SkyStation Operations")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/crew_repository.snapshot.json"))
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    token = os.environ.get("MONDAY_API_TOKEN")
    if not token:
        print("MONDAY_API_TOKEN is required; no request was made", file=sys.stderr)
        return 2
    try:
        snapshot = normalize(request(token))
        errors = validate(snapshot)
        if errors:
            for error in errors:
                print("VALIDATION_ERROR: " + error, file=sys.stderr)
            return 1
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(snapshot, indent=2) + "\n")
        print(f"wrote {len(snapshot['records'])} records to {args.output}")
        return 0
    except Exception as exc:
        print(f"SYNC_ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
