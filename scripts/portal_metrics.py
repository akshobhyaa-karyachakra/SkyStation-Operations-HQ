"""Pure, read-only aggregation for the SkyStation portal."""
from __future__ import annotations

from collections import Counter
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
        "inventory": {"assets": len(inventory), "needs_review": sum(r.get("data_state") == "needs_review" for r in inventory)},
        "incidents": {"total": len(incidents), "open": sum((r.get("status") or "").lower() not in {"closed", "resolved"} for r in incidents)},
    }
