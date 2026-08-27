#!/usr/bin/env python3
"""Read-only Incident Logs sync into a normalized incident snapshot."""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BOARD_ID = "5030309792"
INVENTORY_BOARD_ID = "5028042389"
CUSTOMER_BOARD_ID = "5028043141"
ACTIVITY_BOARD_ID = "5027240228"
API_URL = "https://api.monday.com/v2"
API_VERSION = "2025-04"

COLUMN_IDS = [
    "text_mm5rg586", "text_mm5r80cf", "date_mm5rb3vs", "text_mm5rp4dc", "text_mm5ryhz9",
    "text_mm5rxgz5", "text_mm5rbnz3", "long_text_mm5r8xd5", "long_text_mm5r49e6",
    "text_mm5rqx30", "link_mm5rg1h4", "file_mm5rf29q", "link_mm5r9vnb", "multiple_person_mm5rrm68",
    "long_text_mm5rcg6n", "color_mm5r9mz6", "color_mm5rdvzk", "color_mm5r69g0", "color_mm5r8cma",
    "color_mm5rg2cn", "date_mm5rgats", "date_mm5rk13d", "dropdown_mm5ra2at", "dropdown_mm5rtyrw",
    "dropdown_mm5rdpg3", "dropdown_mm5rdb2e", "long_text_mm5rdf2y", "board_relation_mm5r9hjx",
    "board_relation_mm5r5f9b", "board_relation_mm5re9f7", "multiple_person_mm5rcqsf", "multiple_person_mm5rb6ay",
    "color_mm5shmfk", "color_mm5sdw7a", "long_text_mm5ss3en",
]

QUERY = """
query($board_id: ID!, $cursor: String) {
  boards(ids: [$board_id]) {
    id name updated_at
    items_page(limit: 500, cursor: $cursor) {
      cursor
      items {
        id name updated_at group { id title }
        column_values(ids: ["text_mm5rg586","text_mm5r80cf","date_mm5rb3vs","text_mm5rp4dc","text_mm5ryhz9","text_mm5rxgz5","text_mm5rbnz3","long_text_mm5r8xd5","long_text_mm5r49e6","text_mm5rqx30","link_mm5rg1h4","file_mm5rf29q","link_mm5r9vnb","multiple_person_mm5rrm68","long_text_mm5rcg6n","color_mm5r9mz6","color_mm5rdvzk","color_mm5r69g0","color_mm5r8cma","color_mm5rg2cn","date_mm5rgats","date_mm5rk13d","dropdown_mm5ra2at","dropdown_mm5rtyrw","dropdown_mm5rdpg3","dropdown_mm5rdb2e","long_text_mm5rdf2y","board_relation_mm5r9hjx","board_relation_mm5r5f9b","board_relation_mm5re9f7","multiple_person_mm5rcqsf","multiple_person_mm5rb6ay","color_mm5shmfk","color_mm5sdw7a","long_text_mm5ss3en"]) {
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
    req = urllib.request.Request(API_URL, data=body, headers={"Authorization": token, "Content-Type": "application/json", "API-Version": API_VERSION})
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
        if len(boards) != 1: raise ValueError(f"expected one board, received {len(boards)}")
        board = boards[0]
        page = board["items_page"]
        items.extend(page.get("items", []))
        cursor = page.get("cursor")
        if not cursor: return board, items


def _people(column: dict) -> list[dict]:
    return [{"monday_user_id": str(p["id"]), "name": p.get("name"), "kind": p.get("kind")}
            for p in (column.get("persons_and_teams") or []) if p.get("kind") == "person"]


def _relations(column: dict) -> list[dict]:
    return [{"monday_item_id": str(x["id"]), "name": x.get("name"),
             "board_id": str((x.get("board") or {}).get("id")), "board_name": (x.get("board") or {}).get("name")}
            for x in (column.get("linked_items") or [])]


def _evidence(value: str | None) -> list[str]:
    return [part.strip() for part in (value or "").split(",") if part.strip()]


def normalize(board: dict, raw_items: list[dict]) -> dict:
    records = []
    for item in raw_items:
        c = {x["id"]: x for x in item.get("column_values", [])}
        status = c.get("color_mm5r9mz6", {}).get("text") or None
        report_quality = c.get("color_mm5rg2cn", {}).get("text") or None
        report_link = c.get("link_mm5rg1h4", {}).get("text") or None
        files = _evidence(c.get("file_mm5rf29q", {}).get("text"))
        issues = []
        if not c.get("text_mm5rg586", {}).get("text"): issues.append("missing_incident_ref")
        if not status: issues.append("missing_incident_status")
        if status == "Closed" and not c.get("date_mm5rk13d", {}).get("text"): issues.append("closed_without_closure_date")
        if status == "Closed" and report_quality != "Final": issues.append("closed_without_final_report")
        if report_quality == "Final" and not report_link and not files: issues.append("final_report_without_evidence_link")
        relations = {
            "inventory": _relations(c.get("board_relation_mm5r9hjx", {})),
            "customer": _relations(c.get("board_relation_mm5r5f9b", {})),
            "activity": _relations(c.get("board_relation_mm5re9f7", {})),
        }
        for key, expected in (("inventory", INVENTORY_BOARD_ID), ("customer", CUSTOMER_BOARD_ID), ("activity", ACTIVITY_BOARD_ID)):
            if any(r.get("board_id") != expected for r in relations[key]): issues.append(f"unexpected_{key}_relation_target")
        records.append({
            "source_board_id": BOARD_ID, "source_item_id": str(item["id"]), "name": item["name"],
            "group_id": str((item.get("group") or {}).get("id")) if item.get("group") else None,
            "group_title": (item.get("group") or {}).get("title"), "incident_ref": c.get("text_mm5rg586", {}).get("text") or None,
            "incident_date": c.get("date_mm5rb3vs", {}).get("text") or None, "incident_time": c.get("text_mm5rp4dc", {}).get("text") or None,
            "site_name": c.get("text_mm5ryhz9", {}).get("text") or None, "dock_model": c.get("text_mm5rxgz5", {}).get("text") or None,
            "drone_model": c.get("text_mm5rbnz3", {}).get("text") or None, "error_code_message": c.get("text_mm5r80cf", {}).get("text") or None,
            "error_description": c.get("long_text_mm5r8xd5", {}).get("text") or None, "resolution": c.get("long_text_mm5r49e6", {}).get("text") or None,
            "reported_through": c.get("text_mm5rqx30", {}).get("text") or None, "owner": _people(c.get("multiple_person_mm5rrm68", {})),
            "reported_by_person": _people(c.get("multiple_person_mm5rcqsf", {})), "actual_operator": _people(c.get("multiple_person_mm5rb6ay", {})),
            "status": status, "severity": c.get("color_mm5rdvzk", {}).get("text") or None,
            "root_cause_confirmed": c.get("color_mm5r69g0", {}).get("text") or None, "repeat_incident": c.get("color_mm5r8cma", {}).get("text") or None,
            "report_quality": report_quality, "source": c.get("dropdown_mm5ra2at", {}).get("text") or None,
            "category": c.get("dropdown_mm5rtyrw", {}).get("text") or None, "failure_stage": c.get("dropdown_mm5rdpg3", {}).get("text") or None,
            "external_escalation": c.get("dropdown_mm5rdb2e", {}).get("text") or None,
            "operational_impact": c.get("long_text_mm5rdf2y", {}).get("text") or None,
            "next_action": c.get("long_text_mm5rcg6n", {}).get("text") or None,
            "report_link": report_link, "evidence_links": files + _evidence(c.get("link_mm5r9vnb", {}).get("text")),
            "target_closure_date": c.get("date_mm5rgats", {}).get("text") or None, "closure_date": c.get("date_mm5rk13d", {}).get("text") or None,
            "closure_blocker": c.get("color_mm5shmfk", {}).get("text") or None, "escalation_level": c.get("color_mm5sdw7a", {}).get("text") or None,
            "missing_to_close": c.get("long_text_mm5ss3en", {}).get("text") or None,
            "relations": relations, "source_updated_at": item.get("updated_at"),
            "data_state": "needs_review" if issues else "current", "validation_issues": sorted(set(issues)),
        })
    return {"schema_version": "incident.v1", "source": {"provider": "monday", "board_id": BOARD_ID, "board_name": board.get("name"), "board_updated_at": board.get("updated_at")}, "synced_at": datetime.now(timezone.utc).isoformat(), "records": records}


def validate(snapshot: dict) -> list[str]:
    records = snapshot.get("records", [])
    refs = [r.get("incident_ref") for r in records]
    errors = []
    if snapshot.get("schema_version") != "incident.v1": errors.append("unsupported schema")
    if len(records) != 10: errors.append(f"expected 10 incidents, received {len(records)}")
    if len([r.get("source_item_id") for r in records]) != len(set(r.get("source_item_id") for r in records)): errors.append("duplicate source item IDs")
    if len(refs) != len(set(x for x in refs if x)): errors.append("duplicate incident references")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, default=Path("data/incident_logs.snapshot.json")); args = parser.parse_args()
    token = os.environ.get("MONDAY_API_TOKEN")
    if not token: print("MONDAY_API_TOKEN is required; no request was made", file=sys.stderr); return 2
    try:
        board, items = fetch_all(token); snapshot = normalize(board, items); errors = validate(snapshot)
        if errors:
            for error in errors: print("VALIDATION_ERROR: " + error, file=sys.stderr)
            return 1
        args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(snapshot, indent=2) + "\n")
        print(f"wrote {len(items)} incidents to {args.output}"); return 0
    except Exception as exc:
        print(f"SYNC_ERROR: {exc}", file=sys.stderr); return 1


if __name__ == "__main__": raise SystemExit(main())
