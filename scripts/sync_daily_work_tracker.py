#!/usr/bin/env python3
"""Read-only sync for dated Daily Work Tracker occurrences.

Work Repository is the durable activity definition; Daily Work Tracker is the
execution grain used by the portal calendar and person heatmap.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DAILY_BOARD_ID = "5031430709"
CREW_BOARD_ID = "5030902067"
API_URL = "https://api.monday.com/v2"
API_VERSION = "2025-04"

DAILY_QUERY = """
query($board_id: ID!, $cursor: String) {
  boards(ids: [$board_id]) {
    id name updated_at
    items_page(limit: 500, cursor: $cursor) {
      cursor
      items {
        id name updated_at group { id title }
        column_values(ids: [
          "board_relation_mm7cgmva", "date_mm7cyfzf", "multiple_person_mm7cc3p3",
          "color_mm7cff43", "numeric_mm7cj5sz", "numeric_mm7c6bbm",
          "long_text_mm7cp323", "link_mm7cp87q", "dropdown_mm7c89ym",
          "dropdown_mm7c1gdq", "date_mm7f1rex", "date_mm7fn95t"
        ]) {
          id text value type
          ... on PeopleValue { persons_and_teams { id kind name } }
          ... on BoardRelationValue { linked_item_ids linked_items { id name board { id name } } }
        }
      }
    }
  }
}
"""

CREW_QUERY = """
query($board_id: ID!, $cursor: String) {
  boards(ids: [$board_id]) {
    id name updated_at
    items_page(limit: 500, cursor: $cursor) {
      cursor
      items {
        id name updated_at group { id title }
        column_values(ids: ["lookup_mm792kmk", "color_mm6mamdg"]) { id text value type }
      }
    }
  }
}
"""

USERS_QUERY = """
query { users(limit: 500) { id name } }
"""


def request(token: str, query: str, board_id: str, cursor: str | None) -> dict:
    body = json.dumps({"query": query, "variables": {"board_id": board_id, "cursor": cursor}}).encode()
    req = urllib.request.Request(API_URL, data=body, headers={
        "Authorization": token, "Content-Type": "application/json", "API-Version": API_VERSION,
    })
    with urllib.request.urlopen(req, timeout=60) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError("Monday query failed: " + "; ".join(e.get("message", "unknown error") for e in payload["errors"]))
    return payload


def request_users(token: str) -> list[dict]:
    body = json.dumps({"query": USERS_QUERY, "variables": {}}).encode()
    req = urllib.request.Request(API_URL, data=body, headers={
        "Authorization": token, "Content-Type": "application/json", "API-Version": API_VERSION,
    })
    with urllib.request.urlopen(req, timeout=60) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError("Monday user query failed: " + "; ".join(e.get("message", "unknown error") for e in payload["errors"]))
    return payload.get("data", {}).get("users", [])


def fetch_all(token: str, query: str, board_id: str) -> tuple[dict, list[dict]]:
    items, cursor = [], None
    while True:
        payload = request(token, query, board_id, cursor)
        boards = payload.get("data", {}).get("boards", [])
        if len(boards) != 1:
            raise ValueError(f"expected one board, received {len(boards)}")
        board = boards[0]
        page = board["items_page"]
        items.extend(page.get("items", []))
        cursor = page.get("cursor")
        if not cursor:
            return board, items


def _columns(item: dict) -> dict:
    return {column["id"]: column for column in item.get("column_values", [])}


def _people(column: dict) -> list[dict]:
    return [{"monday_user_id": str(person["id"]), "name": person.get("name"), "kind": person.get("kind")}
            for person in (column.get("persons_and_teams") or []) if person.get("kind") == "person"]


def _linked(column: dict) -> list[dict]:
    return [{"id": str(item["id"]), "name": item.get("name"), "board_id": str(item.get("board", {}).get("id"))}
            for item in (column.get("linked_items") or [])]


def _crew_teams(crew_items: list[dict], users: list[dict] | None = None) -> dict[str, str]:
    users_by_name = {str(user.get("name", "")).casefold(): str(user["id"]) for user in (users or []) if user.get("name")}
    if "srihari@skylarkdrones.com" in users_by_name:
        users_by_name["srihari s"] = users_by_name["srihari@skylarkdrones.com"]
    teams = {}
    for item in crew_items:
        columns = _columns(item)
        team = columns.get("lookup_mm792kmk", {}).get("text") or (item.get("group") or {}).get("title")
        person_id = users_by_name.get(str(item.get("name", "")).casefold())
        if team and person_id:
            teams[person_id] = team
    return teams


def normalize(board: dict, raw_items: list[dict], crew_items: list[dict] | None = None, users: list[dict] | None = None) -> dict:
    team_by_person = _crew_teams(crew_items or [], users)
    records = []
    for item in raw_items:
        columns = _columns(item)
        owners = _people(columns.get("multiple_person_mm7cc3p3", {}))
        repository = _linked(columns.get("board_relation_mm7cgmva", {}))
        work_date = columns.get("date_mm7cyfzf", {}).get("text") or None
        status = columns.get("color_mm7cff43", {}).get("text") or None
        work_type = columns.get("dropdown_mm7c89ym", {}).get("text") or None
        issues = []
        if not work_date: issues.append("missing_work_date")
        if not owners: issues.append("missing_owner")
        if not repository: issues.append("missing_work_repository_relation")
        if not status: issues.append("missing_daily_status")
        teams = sorted({team_by_person.get(owner["monday_user_id"]) for owner in owners if team_by_person.get(owner["monday_user_id"])})
        if not teams: issues.append("missing_team_context")
        records.append({
            "source_board_id": DAILY_BOARD_ID,
            "source_item_id": str(item["id"]),
            "source_updated_at": item.get("updated_at"),
            "name": item["name"],
            "stage": "daily_execution",
            "work_date": work_date,
            "work_repository": repository[0] if repository else None,
            "work_repository_item_id": repository[0]["id"] if repository else None,
            "owner": owners,
            "owner_ids": [owner["monday_user_id"] for owner in owners],
            "owner_names": [owner["name"] for owner in owners],
            "teams": teams,
            "team": teams[0] if len(teams) == 1 else (" / ".join(teams) if teams else None),
            "status": status,
            "priority": columns.get("dropdown_mm7c1gdq", {}).get("text") or None,
            "work_type": work_type,
            "planned_effort_hours": columns.get("numeric_mm7cj5sz", {}).get("text") or None,
            "actual_effort_hours": columns.get("numeric_mm7c6bbm", {}).get("text") or None,
            "notes": columns.get("long_text_mm7cp323", {}).get("text") or None,
            "evidence_url": columns.get("link_mm7cp87q", {}).get("text") or None,
            "start_date": columns.get("date_mm7f1rex", {}).get("text") or None,
            "completion_date": columns.get("date_mm7fn95t", {}).get("text") or None,
            "data_state": "needs_review" if issues else "current",
            "validation_issues": issues,
        })
    return {
        "schema_version": "daily_work_tracker.v1",
        "source": {"provider": "monday", "board_id": DAILY_BOARD_ID, "board_name": board.get("name"),
                   "semantic_scope": "dated_daily_execution_occurrences", "board_updated_at": board.get("updated_at"),
                   "work_repository_board_id": "5029561760", "crew_repository_board_id": CREW_BOARD_ID},
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "records": records,
    }


def validate(snapshot: dict) -> list[str]:
    records = snapshot.get("records", [])
    ids = [record.get("source_item_id") for record in records]
    errors = []
    if snapshot.get("schema_version") != "daily_work_tracker.v1": errors.append("unsupported schema")
    if len(ids) != len(set(ids)): errors.append("duplicate source item IDs")
    if any(record.get("stage") != "daily_execution" for record in records): errors.append("non-daily stage in Daily Work Tracker snapshot")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/daily_work_tracker.snapshot.json"))
    args = parser.parse_args()
    token = os.environ.get("MONDAY_API_TOKEN")
    if not token:
        print("MONDAY_API_TOKEN is required; no request was made", file=sys.stderr)
        return 2
    try:
        board, daily_items = fetch_all(token, DAILY_QUERY, DAILY_BOARD_ID)
        _, crew_items = fetch_all(token, CREW_QUERY, CREW_BOARD_ID)
        users = request_users(token)
        snapshot = normalize(board, daily_items, crew_items, users)
        errors = validate(snapshot)
        if errors:
            for error in errors: print("VALIDATION_ERROR: " + error, file=sys.stderr)
            return 1
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(snapshot, indent=2) + "\n")
        print(f"wrote {len(daily_items)} daily work occurrences to {args.output}")
        return 0
    except Exception as exc:
        print(f"SYNC_ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
