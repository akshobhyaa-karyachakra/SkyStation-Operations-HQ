import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from portal_metrics import build_metrics, build_person_work_heatmap, build_resource_calendar


def test_missing_sources_fail_closed_without_fixture_counts():
    result = build_metrics({"activity": None, "flight": None, "processing_qa": None, "report_submission": None, "inventory": None, "incidents": None})
    assert result["data_state"] == "unavailable"
    assert result["planned"]["total"] == 0
    assert result["execution"]["reports_with_links"] == 0


def test_complete_sources_aggregate_canonical_counts():
    result = build_metrics({
        "activity": {"schema_version": "planned_activity.v1", "records": [{"data_state": "current"}, {"data_state": "needs_review"}]},
        "flight": {"schema_version": "work_item.v1", "records": [{"status": "Done"}, {"status": "Stuck"}]},
        "processing_qa": {"schema_version": "work_item.v1", "records": [{"status": "Done"}]},
        "report_submission": {"schema_version": "work_item.v1", "records": [{"report_link": "https://example.test/report"}, {"report_link": None}]},
        "inventory": {"schema_version": "inventory_asset.v1", "records": [{"data_state": "needs_review"}]},
        "incidents": {"schema_version": "incident.v1", "records": [{"status": "Open"}, {"status": "Closed"}]},
    })
    assert result["data_state"] == "current"
    assert result["planned"] == {"total": 2, "needs_review": 1}
    assert result["execution"]["flight_status"] == {"Done": 1, "Stuck": 1}
    assert result["execution"]["reports_with_links"] == 1
    assert result["incidents"] == {"total": 2, "open": 1}


def work_item(item_id, date, owners, category="Inspection", status="Done"):
    return {
        "source_item_id": item_id,
        "name": item_id,
        "start_date": date,
        "end_date": date,
        "owner": [{"monday_user_id": owner, "name": name, "kind": "person"} for owner, name in owners],
        "category": category,
        "status": status,
        "data_state": "current",
    }


def test_resource_calendar_preserves_multi_owner_assignments_and_drilldown_ids():
    result = build_resource_calendar([
        work_item("a", "2026-09-20", [("1", "Aarya")]),
        work_item("b", "2026-09-20", [("1", "Aarya"), ("2", "Sai")], status="Stuck"),
    ], "2026-09-20", "2026-09-20")
    assert result["data_state"] == "current"
    assert result["dates"] == ["2026-09-20"]
    assert result["rows"][0]["owner_id"] == "1"
    assert result["rows"][0]["cells"][0]["count"] == 2
    assert result["rows"][0]["cells"][0]["shared_count"] == 1
    assert [item["source_item_id"] for item in result["rows"][0]["cells"][0]["items"]] == ["a", "b"]


def test_person_heatmap_marks_unassigned_review_and_does_not_infer_utilization():
    result = build_person_work_heatmap([
        work_item("a", "2026-09-20", [("1", "Aarya")], category="QC"),
        work_item("b", "2026-09-21", [], category="QC"),
    ], "1", "2026-09-20", "2026-09-21")
    assert result["data_state"] == "current"
    assert result["person_id"] == "1"
    assert result["rows"][0]["cells"][0]["count"] == 1
    assert "utilization" not in result
    assert result["unassigned_review_count"] == 1
