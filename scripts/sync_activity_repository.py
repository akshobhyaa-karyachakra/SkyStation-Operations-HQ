#!/usr/bin/env python3
"""Read-only Activity Repository sync into the planned_activity model."""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BOARD_ID = "5027240228"
API_URL = "https://api.monday.com/v2"
API_VERSION = "2025-04"

QUERY = """
query($board_id: ID!, $cursor: String) {
  boards(ids: [$board_id]) {
    id
    name
    updated_at
    items_page(limit: 500, cursor: $cursor) {
      cursor
      items {
        id
        name
        updated_at
        column_values(ids: [
          \"multiple_person_mm1g7qjb\", \"multiple_person_mm1gvaap\",
          \"color_mm1gsat9\", \"color_mm1g3h74\", \"dropdown_mm3rv0jk\",
          \"text_mm3rqdg7\", \"text_mm1rrn73\", \"date_mm3t9qdk\",
          \"board_relation_mm2qwdd3\"
        ]) {
          id
          text
          value
          type
          ... on PeopleValue { persons_and_teams { id kind name } }
          ... on BoardRelationValue { linked_items { id name board { id name } } }
        }
      }
    }
  }
}
"""


def request(token: str, cursor: str | None) -> dict:
    body = json.dumps({"query": QUERY, "variables": {"board_id": BOARD_ID, "cursor": cursor}}).encode()
    req = urllib.request.Request(API_URL, data=body, headers={
        "Authorization": token, "Content-Type": "application/json", "API-Version": API_VERSION,
    })
    with urllib.request.urlopen(req, timeout=60) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError("Monday query failed: " + "; ".join(e.get("message", "unknown error") for e in payload["errors"]))
    return payload


def fetch_all(token: str) -> tuple[dict, list[dict]]:
    pages, items, cursor = [], [], None
    while True:
        payload = request(token, cursor)
        boards = payload.get("data", {}).get("boards", [])
        if len(boards) != 1:
            raise ValueError(f"expected one board, received {len(boards)}")
        page = boards[0]["items_page"]
        pages.append({"count": len(page.get("items", [])), "cursor": page.get("cursor")})
        items.extend(page.get("items", []))
        cursor = page.get("cursor")
        if not cursor:
            return boards[0], items


def _people(column: dict) -> list[dict]:
    return [
        {"monday_user_id": str(p["id"]), "name": p.get("name"), "kind": p.get("kind")}
        for p in (column.get("persons_and_teams") or []) if p.get("kind") == "person"
    ]


def normalize(board: dict, raw_items: list[dict]) -> dict:
    records = []
    for item in raw_items:
        columns = {c["id"]: c for c in item.get("column_values", [])}
        active = (columns.get("color_mm1g3h74", {}).get("text") or None)
        activity_type = columns.get("color_mm1gsat9", {}).get("text") or None
        cadence = columns.get("dropdown_mm3rv0jk", {}).get("text") or None
        relations = [
            {"monday_item_id": str(x["id"]), "name": x.get("name"), "board_id": str((x.get("board") or {}).get("id"))}
            for x in (columns.get("board_relation_mm2qwdd3", {}).get("linked_items") or [])
        ]
        records.append({
            "source_board_id": BOARD_ID,
            "source_item_id": str(item["id"]),
            "name": item["name"],
            "source_updated_at": item.get("updated_at"),
            "owner": _people(columns.get("multiple_person_mm1g7qjb", {})),
            "co_owner": _people(columns.get("multiple_person_mm1gvaap", {})),
            "activity_type": activity_type,
            "active_state": active,
            "weekly_frequency": cadence,
            "planned_quantity": columns.get("text_mm1rrn73", {}).get("text") or None,
            "site_quantity": columns.get("text_mm3rqdg7", {}).get("text") or None,
            "assignment_date": columns.get("date_mm3t9qdk", {}).get("text") or None,
            "customer_relations": relations,
            "data_state": "needs_review" if not active or not activity_type or not relations else "current",
        })
    return {
        "schema_version": "planned_activity.v1",
        "source": {"provider": "monday", "board_id": BOARD_ID, "board_name": board.get("name"), "board_updated_at": board.get("updated_at")},
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "records": records,
    }


def validate(snapshot: dict) -> list[str]:
    records = snapshot.get("records", [])
    errors = []
    ids = [r.get("source_item_id") for r in records]
    if snapshot.get("schema_version") != "planned_activity.v1": errors.append("unsupported schema")
    if len(ids) != len(set(ids)): errors.append("duplicate source item IDs")
    if len(records) != 72: errors.append(f"expected 72 items, received {len(records)}")
    if any(not r.get("name") or not r.get("source_item_id") for r in records): errors.append("missing item identity")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/activity_repository.snapshot.json"))
    args = parser.parse_args()
    token = os.environ.get("MONDAY_API_TOKEN")
    if not token:
        print("MONDAY_API_TOKEN is required; no request was made", file=sys.stderr)
        return 2
    try:
        board, items = fetch_all(token)
        snapshot = normalize(board, items)
        errors = validate(snapshot)
        if errors:
            for error in errors: print("VALIDATION_ERROR: " + error, file=sys.stderr)
            return 1
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(snapshot, indent=2) + "\n")
        print(f"wrote {len(items)} planned activities to {args.output}")
        return 0
    except Exception as exc:
        print(f"SYNC_ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
