"""Pure, read-only aggregation for the SkyStation portal."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Any


def _records(snapshot: dict | None) -> list[dict[str, Any]]:
    return list(snapshot.get("records", [])) if isinstance(snapshot, dict) and isinstance(snapshot.get("records"), list) else []


def _state(snapshots: dict[str, dict | None]) -> str:
    return "current" if snapshots and all(v is not None for v in snapshots.values()) else "unavailable"


def build_metrics(snapshots: dict[str, dict | None]) -> dict[str, Any]:
    """Return canonical metrics without filling gaps from fixtures or inference."""
    activity = _records(snapshots.get("activity"))
    flight = _records(snapshots.get("flight"))
    qa = _records(snapshots.get("processing_qa"))
    reports = _records(snapshots.get("report_submission"))
    inventory = _records(snapshots.get("inventory"))
    incidents = _records(snapshots.get("incidents"))
    inventory_condition = Counter(r.get("condition") or "Condition not provided" for r in inventory)
    inventory_types = Counter(r.get("asset_type") or "Type not provided" for r in inventory)
    inventory_pending = {
        "condition_not_provided": sum(not r.get("condition") for r in inventory),
        "type_not_provided": sum(not r.get("asset_type") for r in inventory),
        "serial_not_provided": sum(not r.get("serial_or_unit_id") for r in inventory),
        "location_not_provided": sum(not r.get("location") for r in inventory),
    }
    return {
        "schema_version": "portal_metrics.v1",
        "data_state": _state(snapshots),
        "sources": {name: (snap.get("schema_version") if isinstance(snap, dict) else None) for name, snap in snapshots.items()},
        "planned": {"total": len(activity), "needs_review": sum(r.get("data_state") == "needs_review" for r in activity)},
        "execution": {
            "flights": len(flight),
            "flight_status": dict(Counter(r.get("status") or "No status" for r in flight)),
            "qa_items": len(qa),
            "report_items": len(reports),
            "reports_with_links": sum(bool(r.get("report_link")) for r in reports),
        },
        "inventory": {
            "assets": len(inventory),
            "needs_review": sum(r.get("data_state") == "needs_review" for r in inventory),
            "condition_counts": dict(inventory_condition),
            "type_counts": dict(inventory_types),
            "pending_fields": inventory_pending,
        },
        "incidents": {"total": len(incidents), "open": sum((r.get("status") or "").lower() not in {"closed", "resolved"} for r in incidents)},
    }


def _date_range(start_date: str, end_date: str) -> list[str]:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    if end < start:
        raise ValueError("end_date must be on or after start_date")
    return [(start + timedelta(days=offset)).isoformat() for offset in range((end - start).days + 1)]


def _work_date(record: dict[str, Any]) -> str | None:
    return record.get("work_date") or record.get("execution_date") or record.get("start_date") or record.get("planned_date") or record.get("end_date")


def _owners(record: dict[str, Any]) -> list[dict[str, str]]:
    raw = record.get("owner") or record.get("owners") or []
    return [
        {"id": str(person.get("monday_user_id") or person.get("id")), "name": person.get("name") or "Unnamed person"}
        for person in raw
        if isinstance(person, dict) and (person.get("monday_user_id") or person.get("id"))
    ]


def _allocation_item(record: dict[str, Any], shared: bool) -> dict[str, Any]:
    return {
        "source_item_id": str(record.get("source_item_id")),
        "name": record.get("name"),
        "status": record.get("status") or "No status",
        "category": record.get("category") or record.get("work_type") or "Work",
        "customer": record.get("customer"),
        "site": record.get("site"),
        "data_state": record.get("data_state") or "needs_review",
        "shared_assignment": shared,
        "evidence_links": record.get("evidence_links") or record.get("file_evidence") or [],
    }


def build_resource_calendar(records: list[dict[str, Any]], start_date: str, end_date: str) -> dict[str, Any]:
    """Build a date-by-owner allocation grid without inferring capacity."""
    dates = _date_range(start_date, end_date)
    date_index = {value: index for index, value in enumerate(dates)}
    grouped: dict[str, dict[str, Any]] = {}
    unassigned = 0
    for record in records:
        work_date = _work_date(record)
        if work_date not in date_index:
            continue
        owners = _owners(record)
        if not owners:
            unassigned += 1
            continue
        shared = len(owners) > 1
        for owner in owners:
            row = grouped.setdefault(owner["id"], {"owner_id": owner["id"], "owner_name": owner["name"], "cells": [[] for _ in dates]})
            row["cells"][date_index[work_date]].append(_allocation_item(record, shared))
    rows = []
    for row in sorted(grouped.values(), key=lambda item: item["owner_name"].lower()):
        cells = []
        for items in row.pop("cells"):
            counts = Counter(item["status"] for item in items)
            cells.append({
                "count": len(items),
                "shared_count": sum(item["shared_assignment"] for item in items),
                "status_counts": dict(counts),
                "items": items,
            })
        row["cells"] = cells
        rows.append(row)
    return {"schema_version": "resource_calendar.v1", "data_state": "current", "start_date": start_date, "end_date": end_date, "dates": dates, "rows": rows, "unassigned_review_count": unassigned, "no_capacity_inference": True}


def build_person_work_heatmap(records: list[dict[str, Any]], person_id: str, start_date: str, end_date: str, grouping: str = "category") -> dict[str, Any]:
    """Build one person's dated work density; counts are evidence, not performance."""
    dates = _date_range(start_date, end_date)
    date_index = {value: index for index, value in enumerate(dates)}
    groups: dict[str, list[list[dict[str, Any]]]] = defaultdict(lambda: [[] for _ in dates])
    unassigned_review_count = 0
    person_id = str(person_id)
    for record in records:
        work_date = _work_date(record)
        if work_date not in date_index:
            continue
        owners = _owners(record)
        if not owners:
            unassigned_review_count += 1
            continue
        owner_ids = {owner["id"] for owner in owners}
        if person_id not in owner_ids:
            continue
        group = record.get("customer") or "Uncategorised" if grouping == "customer" else record.get("category") or record.get("work_type") or "Work"
        groups[group][date_index[work_date]].append(_allocation_item(record, len(owners) > 1))
    rows = []
    for label in sorted(groups, key=str.lower):
        cells = []
        for items in groups[label]:
            cells.append({"count": len(items), "shared_count": sum(item["shared_assignment"] for item in items), "status_counts": dict(Counter(item["status"] for item in items)), "items": items})
        rows.append({"label": label, "cells": cells})
    return {"schema_version": "person_work_heatmap.v1", "data_state": "current", "person_id": person_id, "grouping": grouping, "start_date": start_date, "end_date": end_date, "dates": dates, "rows": rows, "unassigned_review_count": unassigned_review_count, "no_utilization_inference": True}
