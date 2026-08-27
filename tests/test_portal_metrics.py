import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from portal_metrics import build_metrics


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
