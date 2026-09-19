#!/usr/bin/env python3
"""Read-only Monday adapter for the SkyStation role framework."""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT_BOARD = "5031376976"
SUBITEM_BOARD = "5031377037"
API_URL = "https://api.monday.com/v2"
API_VERSION = "2025-04"
PARENT_COLUMNS = [
    "dropdown_mm792xk4", "dropdown_mm797pdx", "long_text_mm794f3t",
    "long_text_mm79bmf8", "long_text_mm79jzma", "long_text_mm79bswk",
    "long_text_mm79qbfy", "color_mm79mv5d",
]
SUBITEM_COLUMNS = ["numeric_mm79pyxm"]
QUERY = """
query($board_id: ID!, $cursor: String, $column_ids: [String!]) {
  boards(ids: [$board_id]) {
    id name updated_at
    items_page(limit: 500, cursor: $cursor) {
      cursor
      items {
        id name updated_at
        column_values(ids: $column_ids) { id text value }
        subitems { id name updated_at }
      }
    }
  }
}
"""


def request(token: str, board_id: str, cursor: str | None) -> dict:
    body = json.dumps({"query": QUERY, "variables": {"board_id": board_id, "cursor": cursor, "column_ids": PARENT_COLUMNS if board_id == PARENT_BOARD else SUBITEM_COLUMNS}}).encode()
    req = urllib.request.Request(API_URL, data=body, headers={"Authorization": token, "Content-Type": "application/json", "API-Version": API_VERSION})
    with urllib.request.urlopen(req, timeout=60) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError("Monday query failed")
    return payload


def _fetch_board(token: str, board_id: str) -> tuple[dict, list[dict]]:
    items: list[dict] = []
    cursor = None
    board = None
    while True:
        boards = request(token, board_id, cursor).get("data", {}).get("boards", [])
        if len(boards) != 1:
            raise ValueError(f"expected one Monday board {board_id}")
        board = boards[0]
        page = board.get("items_page") or {}
        items.extend(page.get("items") or [])
        cursor = page.get("cursor")
        if not cursor:
            return board, items


def fetch_all(token: str) -> tuple[dict, list[dict], dict, list[dict]]:
    parent_board, parents = _fetch_board(token, PARENT_BOARD)
    subitem_board, subitems = _fetch_board(token, SUBITEM_BOARD)
    return parent_board, parents, subitem_board, subitems


def _columns(item: dict) -> dict[str, dict]:
    return {str(value.get("id")): value for value in item.get("column_values") or []}


def _text(columns: dict[str, dict], column_id: str) -> str | None:
    value = columns.get(column_id) or {}
    text = value.get("text")
    return str(text).strip() if text is not None and str(text).strip() else None


def _weight(columns: dict[str, dict]) -> float | str | None:
    text = _text(columns, "numeric_mm79pyxm")
    if text is None:
        return None
    try:
        return float(text.replace(",", ""))
    except (TypeError, ValueError):
        return text


def normalize(parent_board: dict, parents: list[dict], subitems: list[dict]) -> dict:
    subitems_by_id = {str(item.get("id")): item for item in subitems}
    roles = []
    metadata = []
    for parent in parents:
        links = parent.get("subitems") or []
        linked_ids = [str(link.get("id")) if link.get("id") is not None else None for link in links]
        if not links:
            metadata.append({"source_item_id": str(parent["id"]) if parent.get("id") is not None else None, "name": parent.get("name")})
            continue
        columns = _columns(parent)
        competencies = []
        for linked_id in linked_ids:
            item = (subitems_by_id.get(linked_id) if linked_id is not None else None) or next((x for x in links if x.get("id") is not None and str(x.get("id")) == linked_id), {"id": linked_id})
            item_columns = _columns(item)
            competencies.append({
                "source_item_id": linked_id if linked_id != "None" else None,
                "name": item.get("name"),
                "weight": _weight(item_columns),
            })
        total = sum(weight for weight in (entry["weight"] for entry in competencies) if isinstance(weight, (int, float)))
        roles.append({
            "source_item_id": str(parent["id"]) if parent.get("id") is not None else None,
            "name": parent.get("name"),
            "team": _text(columns, "dropdown_mm792xk4"),
            "band": _text(columns, "dropdown_mm797pdx"),
            "role_purpose": _text(columns, "long_text_mm794f3t"),
            "primary_accountability": _text(columns, "long_text_mm79bmf8"),
            "core_expectation": _text(columns, "long_text_mm79jzma"),
            "level_differentiation": _text(columns, "long_text_mm79bswk"),
            "promotion_gate": _text(columns, "long_text_mm79qbfy"),
            "framework_state": _text(columns, "color_mm79mv5d"),
            "competencies": competencies,
            "weight_total": float(total),
            "source_updated_at": parent.get("updated_at"),
        })
    return {
        "schema_version": "role-framework.v1",
        "data_state": "current",
        "source": {"provider": "monday", "parent_board_id": PARENT_BOARD, "subitem_board_id": SUBITEM_BOARD, "parent_board_updated_at": parent_board.get("updated_at")},
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "roles": roles,
        "records": roles,
        "metadata": {"non_role_parent_items": metadata},
    }


def validate(snapshot: dict) -> list[str]:
    errors: set[str] = set()
    if snapshot.get("schema_version") != "role-framework.v1":
        errors.add("unsupported schema")
    roles = snapshot.get("roles") or []
    role_ids = [role.get("source_item_id") for role in roles]
    if any(not role_id for role_id in role_ids):
        errors.add("missing role source item ID")
    if len(role_ids) != len(set(role_ids)):
        errors.add("duplicate role source item IDs")
    competency_ids = []
    for role in roles:
        competencies = role.get("competencies") or []
        for competency in competencies:
            competency_id = competency.get("source_item_id")
            competency_ids.append(competency_id)
            if not competency_id:
                errors.add("missing competency source item ID")
            weight = competency.get("weight")
            if weight is None or weight == "":
                errors.add("missing competency weight")
            elif not isinstance(weight, (int, float)) or isinstance(weight, bool):
                errors.add("non-numeric competency weight")
        if abs(sum(weight for weight in (c.get("weight") for c in competencies) if isinstance(weight, (int, float))) - 100.0) > 1e-6:
            errors.add("role competency weights must total 100")
    if len(competency_ids) != len(set(competency_ids)):
        errors.add("duplicate competency source item IDs")
    return sorted(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "role_framework.snapshot.json")
    args = parser.parse_args()
    token = os.environ.get("MONDAY_API_TOKEN")
    if not token:
        print("MONDAY_API_TOKEN is required; no request was made", file=sys.stderr)
        return 2
    try:
        parent_board, parents, _subitem_board, subitems = fetch_all(token)
        snapshot = normalize(parent_board, parents, subitems)
        errors = validate(snapshot)
        if errors:
            for error in errors:
                print("VALIDATION_ERROR: " + error, file=sys.stderr)
            return 1
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(snapshot, indent=2) + "\n")
        print(f"wrote {len(snapshot['roles'])} roles to {args.output}")
        return 0
    except Exception as exc:
        print("SYNC_ERROR: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
