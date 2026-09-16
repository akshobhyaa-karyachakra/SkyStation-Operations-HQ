#!/usr/bin/env python3
"""Build a read-only, source-grounded workflow-network snapshot from Monday adapters."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
ADAPTERS = {
    "activity_repository": "sync_activity_repository.py",
    "flight_operations": "sync_flight_operations.py",
    "processing_qa": "sync_processing_qa.py",
    "report_submission": "sync_report_submission.py",
    "site_activities": "sync_site_activities.py",
    "work_tracker": "sync_work_tracker.py",
    "incident_logs": "sync_incident_logs.py",
}
BOARD_IDS = {
    "activity_repository": "5027240228",
    "flight_operations": "5027240883",
    "processing_qa": "5027256991",
    "report_submission": "5027265596",
    "site_activities": "5028018276",
    "work_tracker": "5029561760",
    "incident_logs": "5030309792",
}


def _load_adapter(name: str):
    path = SCRIPTS / ADAPTERS[name]
    spec = importlib.util.spec_from_file_location(f"workflow_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {name} adapter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fetch_sources(token: str) -> dict[str, dict]:
    """Fetch every source completely; no first-page-only snapshots are accepted."""
    sources = {}
    for name in ADAPTERS:
        module = _load_adapter(name)
        board, raw_items = module.fetch_all(token)
        snapshot = module.normalize(board, raw_items)
        sources[name] = {
            "board": board,
            "snapshot": snapshot,
            "item_count": len(raw_items),
        }
    return sources


def _status_counts(records: list[dict], key: str = "status") -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        value = record.get(key) or "Unknown"
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _relations(record: dict, *keys: str) -> list[dict]:
    result = []
    for key in keys:
        value = record.get(key)
        if isinstance(value, list):
            result.extend(value)
    return result


def _stage(name: str, board_id: str, records: list[dict], *, state_rules: dict) -> dict:
    needs_review = sum(1 for record in records if record.get("data_state") == "needs_review")
    return {
        "stage_id": name,
        "source_board_id": board_id,
        "record_count": len(records),
        "needs_review_count": needs_review,
        "status_counts": _status_counts(records),
        "state_rules": state_rules,
        "source_item_ids": [str(record["source_item_id"]) for record in records],
    }


def build_network(sources: dict[str, dict], synced_at: str | None = None) -> dict:
    """Create visual state summaries without inferring joins from names."""
    records = {name: data["snapshot"].get("records", []) for name, data in sources.items()}
    activity = records["activity_repository"]
    flight = records["flight_operations"]
    processing = records["processing_qa"]
    reports = records["report_submission"]
    incidents = records["incident_logs"]

    relation_edges = []
    for stage_name in ("flight_operations", "processing_qa", "report_submission"):
        for record in records[stage_name]:
            for relation in _relations(record, "activity_repository_relations"):
                if relation.get("board_id") == BOARD_IDS["activity_repository"]:
                    relation_edges.append({
                        "from_stage": "activity_repository",
                        "to_stage": stage_name,
                        "source_item_id": str(record["source_item_id"]),
                        "source_relation_item_id": str(relation["monday_item_id"]),
                    })
    incident_ids = [str(record["source_item_id"]) for record in incidents]
    broken_flight = [record for record in flight if record.get("status") in {"Stuck", "Not Done", "Blocked"}]
    broken_processing = [record for record in processing if record.get("status") in {"Stuck", "Not Done", "Blocked"}]
    broken_reports = [record for record in reports if record.get("status") in {"Stuck", "Not Done", "Blocked"}]
    open_incidents = [record for record in incidents if record.get("status") not in {"Closed", "Resolved", "Done"}]
    report_done = sum(1 for record in reports if record.get("status") == "Done")

    stages = [
        _stage("activity_repository", BOARD_IDS["activity_repository"], activity, state_rules={"active_is_planned": True}),
        _stage("flight_operations", BOARD_IDS["flight_operations"], flight, state_rules={"blocked_statuses": ["Stuck", "Not Done", "Blocked"]}),
        _stage("processing_qa", BOARD_IDS["processing_qa"], processing, state_rules={"blocked_statuses": ["Stuck", "Not Done", "Blocked"]}),
        _stage("report_submission", BOARD_IDS["report_submission"], reports, state_rules={"delivery_count_uses": "status=Done", "missing_dates_are_unknown": True}),
        _stage("incident_logs", BOARD_IDS["incident_logs"], incidents, state_rules={"open_statuses_are_red": True}),
        {
            "stage_id": "customer_delivery",
            "source_board_id": BOARD_IDS["report_submission"],
            "record_count": report_done,
            "needs_review_count": sum(1 for record in reports if record.get("data_state") == "needs_review"),
            "status_counts": {"Delivered": report_done, "Pending evidence": max(0, len(reports) - report_done)},
            "state_rules": {"derived_from": "report_submission.status", "no_customer_relation_inferred": True},
            "source_item_ids": [str(record["source_item_id"]) for record in reports if record.get("status") == "Done"],
        },
    ]
    node_state = {
        "activity_repository": {"attention": 0, "red": False},
        "flight_operations": {"attention": len(broken_flight), "red": bool(broken_flight)},
        "processing_qa": {"attention": len(broken_processing), "red": bool(broken_processing)},
        "report_submission": {"attention": len(broken_reports), "red": bool(broken_reports)},
        "incident_logs": {"attention": len(open_incidents), "red": bool(open_incidents)},
        "customer_delivery": {"attention": max(0, len(reports) - report_done), "red": False},
    }
    edges = [
        {"edge_id": "activity-to-flight", "from": "activity_repository", "to": "flight_operations", "semantic": "planned_to_execution"},
        {"edge_id": "flight-to-processing", "from": "flight_operations", "to": "processing_qa", "semantic": "execution_to_processing"},
        {"edge_id": "processing-to-report", "from": "processing_qa", "to": "report_submission", "semantic": "processing_to_delivery_evidence"},
        {"edge_id": "report-to-customer", "from": "report_submission", "to": "customer_delivery", "semantic": "submitted_to_customer_delivery"},
        {"edge_id": "flight-to-incidents", "from": "flight_operations", "to": "incident_logs", "semantic": "incident_branch"},
    ]
    return {
        "schema_version": "workflow-network.v1",
        "data_state": "current",
        "source": {"provider": "monday", "boards": BOARD_IDS},
        "synced_at": synced_at or datetime.now(timezone.utc).isoformat(),
        "stages": stages,
        "nodes": node_state,
        "edges": edges,
        "relation_edges": relation_edges,
        "incident_source_item_ids": incident_ids,
        "quality": {
            "total_source_records": sum(len(value) for value in records.values()),
            "source_record_counts": {name: len(value) for name, value in records.items()},
            "broken_record_counts": {"flight_operations": len(broken_flight), "processing_qa": len(broken_processing), "report_submission": len(broken_reports)},
            "open_incident_count": len(open_incidents),
        },
    }


def validate(network: dict) -> list[str]:
    errors = []
    if network.get("schema_version") != "workflow-network.v1": errors.append("unsupported schema")
    if not network.get("stages"): errors.append("missing stages")
    if not network.get("edges"): errors.append("missing semantic edges")
    stage_ids = [stage.get("stage_id") for stage in network.get("stages", [])]
    if len(stage_ids) != len(set(stage_ids)): errors.append("duplicate stage IDs")
    edge_ids = [edge.get("edge_id") for edge in network.get("edges", [])]
    if len(edge_ids) != len(set(edge_ids)): errors.append("duplicate edge IDs")
    if any(edge.get("from") == "activity_repository" and edge.get("to") == "incident_logs" for edge in network.get("edges", [])):
        errors.append("unsupported activity-to-incident edge")
    if any(not node.get("source_item_ids") for node in network.get("stages", []) if node.get("stage_id") != "customer_delivery" and node.get("record_count", 0) > 0):
        errors.append("stage count has no source IDs")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "workflow_network.snapshot.json")
    args = parser.parse_args()
    token = os.environ.get("MONDAY_API_TOKEN")
    if not token:
        print("MONDAY_API_TOKEN is required; no request was made", file=sys.stderr)
        return 2
    try:
        sources = fetch_sources(token)
        network = build_network(sources)
        errors = validate(network)
        if errors:
            for error in errors: print("VALIDATION_ERROR: " + error, file=sys.stderr)
            return 1
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(network, indent=2) + "\n")
        print(f"wrote workflow network snapshot with {network['quality']['total_source_records']} source records to {args.output}")
        return 0
    except Exception as exc:
        print(f"SYNC_ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
