#!/usr/bin/env python3
"""Read-only Work Tracker sync into the normalized work_item model."""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BOARD_ID = "5029561760"
API_URL = "https://api.monday.com/v2"
API_VERSION = "2025-04"

QUERY = """
query($board_id: ID!, $cursor: String) {
  boards(ids: [$board_id]) {
    id name updated_at
    items_page(limit: 500, cursor: $cursor) {
      cursor
      items {
        id name updated_at
        column_values(ids: [
          \"pulse_id_mm59p0n3\", \"date_mm53ct31\", \"date_mm4sr6k2\",
          \"color_mm4spkpm\", \"color_mm4sqdxz\", \"multiple_person_mm4s27gp\",
          \"text_mm4sz5me\", \"dropdown_mm4sktjr\", \"file_mm53hzbr\", \"text_mm6a7946\"
        ]) {
          id text value type
          ... on PeopleValue { persons_and_teams { id kind name } }
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
    items, cursor = [], None
    while True:
        payload = request(token, cursor)
        boards = payload.get("data", {}).get("boards", [])
        if len(boards) != 1:
            raise ValueError(f"expected one board, received {len(boards)}")
        board = boards[0]
        page = board["items_page"]
        items.extend(page.get("items", []))
        cursor = page.get("cursor")
        if not cursor:
            return board, items


def _people(column: dict) -> list[dict]:
    return [{"monday_user_id": str(p["id"]), "name": p.get("name"), "kind": p.get("kind")}
            for p in (column.get("persons_and_teams") or []) if p.get("kind") == "person"]


def _files(column: dict) -> list[dict | str]:
    value = column.get("value")
    if not value:
        return []
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed.get("files", []) if isinstance(parsed, dict) else []
        except (TypeError, json.JSONDecodeError):
            return [{"url": part.strip()} for part in value.split(",") if part.strip()]
    return []


def normalize(board: dict, raw_items: list[dict]) -> dict:
    records = []
    for item in raw_items:
        columns = {c["id"]: c for c in item.get("column_values", [])}
        status = columns.get("color_mm4spkpm", {}).get("text") or None
        owner = _people(columns.get("multiple_person_mm4s27gp", {}))
        start_date = columns.get("date_mm53ct31", {}).get("text") or None
        end_date = columns.get("date_mm4sr6k2", {}).get("text") or None
        issues = []
        if not status:
            issues.append("missing_task_status")
        if status == "Done" and not end_date:
            issues.append("done_without_end_date")
        if status in {"In Progress", "Stuck", "Partially Completed"} and not owner:
            issues.append("active_task_without_owner")
        records.append({
            "source_board_id": BOARD_ID,
            "source_item_id": str(item["id"]),
            "work_id": columns.get("pulse_id_mm59p0n3", {}).get("text") or None,
            "name": item["name"],
            "stage": "internal_work",
            "source_updated_at": item.get("updated_at"),
            "status": status,
            "priority": columns.get("color_mm4sqdxz", {}).get("text") or None,
            "owner": owner,
            "category": columns.get("dropdown_mm4sktjr", {}).get("text") or None,
            "start_date": start_date,
            "end_date": end_date,
            "notes": columns.get("text_mm4sz5me", {}).get("text") or None,
            "text_evidence": columns.get("text_mm6a7946", {}).get("text") or None,
            "file_evidence": _files(columns.get("file_mm53hzbr", {})),
            "data_state": "needs_review" if issues else "current",
            "validation_issues": issues,
        })
    return {
        "schema_version": "work_item.v1",
        "source": {"provider": "monday", "board_id": BOARD_ID, "board_name": board.get("name"),
                   "semantic_scope": "internal_work_only", "board_updated_at": board.get("updated_at")},
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "records": records,
    }


def validate(snapshot: dict) -> list[str]:
    records = snapshot.get("records", [])
    ids = [r.get("source_item_id") for r in records]
    errors = []
    if snapshot.get("schema_version") != "work_item.v1": errors.append("unsupported schema")
    if len(ids) != len(set(ids)): errors.append("duplicate source item IDs")
    if len(records) != 43: errors.append(f"expected 43 items, received {len(records)}")
    if any(r.get("stage") != "internal_work" for r in records): errors.append("non-internal stage in Work Tracker snapshot")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/work_tracker.snapshot.json"))
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
        print(f"wrote {len(items)} internal work items to {args.output}")
        return 0
    except Exception as exc:
        print(f"SYNC_ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
