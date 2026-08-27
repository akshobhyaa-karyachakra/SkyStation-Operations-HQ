#!/usr/bin/env python3
"""Read-only Report Submission sync into the normalized work_item model."""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BOARD_ID = "5027265596"
ACTIVITY_BOARD_ID = "5027240228"
SERVICE_INTAKE_BOARD_ID = "5028091149"
API_URL = "https://api.monday.com/v2"
API_VERSION = "2025-04"

# IDs are taken from the verified live board schema. Keep names out of joins.
QUERY = """
query($board_id: ID!, $cursor: String) {
  boards(ids: [$board_id]) {
    id name updated_at
    items_page(limit: 500, cursor: $cursor) {
      cursor
      items {
        id name updated_at
        column_values(ids: [
          \"pulse_id_mm1gek5g\", \"color_mm1g9w3q\", \"color_mm1sy1pv\",
          \"dropdown_mm1sgtz8\", \"link_mm1htkk8\", \"board_relation_mm1gwp2a\",
          \"board_relation_mm5ag5sy\", \"date_mm1h5gsw\", \"date4\",
          \"date_mm1h7a47\", \"date_mm1h35kq\", \"date_mm1ha6yw\",
          \"multiple_person_mm22yh1f\"
        ]) {
          id text value type
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


def _relations(column: dict) -> list[dict]:
    return [{"monday_item_id": str(x["id"]), "name": x.get("name"),
             "board_id": str((x.get("board") or {}).get("id"))}
            for x in (column.get("linked_items") or [])]


def normalize(board: dict, raw_items: list[dict]) -> dict:
    records = []
    for item in raw_items:
        columns = {c["id"]: c for c in item.get("column_values", [])}
        activity_relations = _relations(columns.get("board_relation_mm1gwp2a", {}))
        intake_relations = _relations(columns.get("board_relation_mm5ag5sy", {}))
        status = columns.get("color_mm1g9w3q", {}).get("text") or None
        delivery_status = columns.get("color_mm1sy1pv", {}).get("text") or None
        blocker = columns.get("dropdown_mm1sgtz8", {}).get("text") or None
        report_link = columns.get("link_mm1htkk8", {}).get("text") or None
        issues = []
        if not activity_relations:
            issues.append("missing_activity_relation")
        if any(r.get("board_id") != ACTIVITY_BOARD_ID for r in activity_relations):
            issues.append("activity_relation_targets_unexpected_board")
        if any(r.get("board_id") != SERVICE_INTAKE_BOARD_ID for r in intake_relations):
            issues.append("intake_relation_targets_unexpected_board")
        if not status:
            issues.append("missing_submission_status")
        if status in {"Stuck", "Not Done"} and not blocker:
            issues.append("blocked_without_reason")
        if status == "Done" and not report_link:
            issues.append("done_without_report_link")
        records.append({
            "source_board_id": BOARD_ID,
            "source_item_id": str(item["id"]),
            "activity_id": columns.get("pulse_id_mm1gek5g", {}).get("text") or None,
            "name": item["name"],
            "stage": "report_submission",
            "source_updated_at": item.get("updated_at"),
            "status": status,
            "delivery_status": delivery_status,
            "owner": _people(columns.get("multiple_person_mm22yh1f", {})),
            "activity_repository_relations": activity_relations,
            "service_request_intake_relations": intake_relations,
            "planned_date": columns.get("date_mm1h5gsw", {}).get("text") or None,
            "report_start_date": columns.get("date4", {}).get("text") or None,
            "report_due_date": columns.get("date_mm1h7a47", {}).get("text") or None,
            "report_ready_date": columns.get("date_mm1h35kq", {}).get("text") or None,
            "submission_date": columns.get("date_mm1ha6yw", {}).get("text") or None,
            "report_link": report_link,
            "blocker": blocker,
            "data_state": "needs_review" if issues else "current",
            "validation_issues": issues,
        })
    return {
        "schema_version": "work_item.v1",
        "source": {"provider": "monday", "board_id": BOARD_ID, "board_name": board.get("name"),
                   "activity_board_id": ACTIVITY_BOARD_ID, "service_intake_board_id": SERVICE_INTAKE_BOARD_ID,
                   "board_updated_at": board.get("updated_at")},
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "records": records,
    }


def validate(snapshot: dict) -> list[str]:
    records = snapshot.get("records", [])
    ids = [r.get("source_item_id") for r in records]
    errors = []
    if snapshot.get("schema_version") != "work_item.v1": errors.append("unsupported schema")
    if len(ids) != len(set(ids)): errors.append("duplicate source item IDs")
    if len(records) != 154: errors.append(f"expected 154 items, received {len(records)}")
    if any(r.get("stage") != "report_submission" for r in records): errors.append("non-report stage in Report Submission snapshot")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/report_submission.snapshot.json"))
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
        print(f"wrote {len(items)} report submission work items to {args.output}")
        return 0
    except Exception as exc:
        print(f"SYNC_ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
