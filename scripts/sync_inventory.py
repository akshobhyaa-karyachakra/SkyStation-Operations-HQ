#!/usr/bin/env python3
"""Read-only SkyStation Inventory sync into a normalized asset snapshot."""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BOARD_ID = "5028042389"
CUSTOMER_BOARD_ID = "5028043141"
CUSTOMER_SUBITEM_BOARD_ID = "5028043142"
INCIDENT_BOARD_ID = "5030309792"
API_URL = "https://api.monday.com/v2"
API_VERSION = "2025-04"

QUERY = """
query($board_id: ID!, $cursor: String) {
  boards(ids: [$board_id]) {
    id name updated_at
    items_page(limit: 500, cursor: $cursor) {
      cursor
      items {
        id name updated_at group { id title }
        column_values(ids: [
          "text_mm2qw26e", "text_mm3rb17h", "color_mm2q9923",
          "board_relation_mm2qgehm", "location_mm2qk3qr", "timerange_mm4ws6n3",
          "date_mm4wawf6", "board_relation_mm4x8z0a", "numeric_mm5bjaex",
          "board_relation_mm5r9a4m"
        ]) {
          id text value type
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


def _relations(column: dict) -> list[dict]:
    return [{"monday_item_id": str(x["id"]), "name": x.get("name"),
             "board_id": str((x.get("board") or {}).get("id")),
             "board_name": (x.get("board") or {}).get("name")}
            for x in (column.get("linked_items") or [])]


def normalize(board: dict, raw_items: list[dict]) -> dict:
    records = []
    for item in raw_items:
        columns = {c["id"]: c for c in item.get("column_values", [])}
        customer = _relations(columns.get("board_relation_mm2qgehm", {}))
        repository = _relations(columns.get("board_relation_mm4x8z0a", {}))
        incidents = _relations(columns.get("board_relation_mm5r9a4m", {}))
        asset_type = columns.get("text_mm2qw26e", {}).get("text") or None
        serial = columns.get("text_mm3rb17h", {}).get("text") or None
        condition = columns.get("color_mm2q9923", {}).get("text") or None
        issues = []
        if not asset_type:
            issues.append("missing_asset_type")
        if not serial:
            issues.append("missing_serial_or_unit_identifier")
        if len(customer) > 1:
            issues.append("multiple_customer_relations")
        if customer and any(r.get("board_id") != CUSTOMER_BOARD_ID for r in customer):
            issues.append("unexpected_customer_relation_target")
        if repository and any(r.get("board_id") != CUSTOMER_SUBITEM_BOARD_ID for r in repository):
            issues.append("unexpected_customer_subitem_relation_target")
        if incidents and any(r.get("board_id") != INCIDENT_BOARD_ID for r in incidents):
            issues.append("unexpected_incident_relation_target")
        records.append({
            "source_board_id": BOARD_ID, "source_item_id": str(item["id"]),
            "name": item["name"], "group_id": str((item.get("group") or {}).get("id")) if item.get("group") else None,
            "group_title": (item.get("group") or {}).get("title"), "asset_type": asset_type,
            "serial_or_unit_id": serial, "condition": condition,
            "customer_relations": customer, "customer_repository_subitem_relations": repository,
            "incident_relations": incidents,
            "location": columns.get("location_mm2qk3qr", {}).get("text") or None,
            "scheduled_maintenance": columns.get("timerange_mm4ws6n3", {}).get("text") or None,
            "last_maintenance": columns.get("date_mm4wawf6", {}).get("text") or None,
            "cycle_count": columns.get("numeric_mm5bjaex", {}).get("text") or None,
            "source_updated_at": item.get("updated_at"),
            "data_state": "needs_review" if issues else "current", "validation_issues": issues,
        })
    return {"schema_version": "inventory_asset.v1",
            "source": {"provider": "monday", "board_id": BOARD_ID, "board_name": board.get("name"),
                       "customer_board_id": CUSTOMER_BOARD_ID, "customer_subitem_board_id": CUSTOMER_SUBITEM_BOARD_ID,
                       "incident_board_id": INCIDENT_BOARD_ID, "board_updated_at": board.get("updated_at")},
            "synced_at": datetime.now(timezone.utc).isoformat(), "records": records}


def validate(snapshot: dict) -> list[str]:
    records = snapshot.get("records", [])
    ids = [r.get("source_item_id") for r in records]
    errors = []
    if snapshot.get("schema_version") != "inventory_asset.v1": errors.append("unsupported schema")
    if len(records) != 121: errors.append(f"expected 121 items, received {len(records)}")
    if len(ids) != len(set(ids)): errors.append("duplicate source item IDs")
    for record in records:
        if any(r.get("board_id") != CUSTOMER_BOARD_ID for r in record.get("customer_relations", [])): errors.append("customer relation target mismatch")
        if any(r.get("board_id") != CUSTOMER_SUBITEM_BOARD_ID for r in record.get("customer_repository_subitem_relations", [])): errors.append("customer subitem relation target mismatch")
        if any(r.get("board_id") != INCIDENT_BOARD_ID for r in record.get("incident_relations", [])): errors.append("incident relation target mismatch")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/inventory.snapshot.json"))
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
        print(f"wrote {len(items)} inventory assets to {args.output}")
        return 0
    except Exception as exc:
        print(f"SYNC_ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
