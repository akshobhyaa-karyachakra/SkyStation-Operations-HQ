import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "sync_daily_work_tracker.py"
spec = importlib.util.spec_from_file_location("sync_daily_work_tracker", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("could not load Daily Work Tracker adapter")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def daily_item(owner_ids=("7",), status="Done", work_date="2026-09-20", relation=True):
    people = [{"id": uid, "kind": "person", "name": "Aarya" if uid == "7" else "Sai"} for uid in owner_ids]
    columns = [
        {"id": "date_mm7cyfzf", "text": work_date},
        {"id": "multiple_person_mm7cc3p3", "persons_and_teams": people},
        {"id": "color_mm7cff43", "text": status},
        {"id": "dropdown_mm7c89ym", "text": "One Time"},
        {"id": "dropdown_mm7c1gdq", "text": "High"},
        {"id": "numeric_mm7cj5sz", "text": "4"},
        {"id": "numeric_mm7c6bbm", "text": None},
        {"id": "long_text_mm7cp323", "text": "evidence"},
        {"id": "link_mm7cp87q", "text": "https://example.test/evidence"},
        {"id": "date_mm7f1rex", "text": work_date},
        {"id": "date_mm7fn95t", "text": work_date if status == "Done" else None},
        {"id": "board_relation_mm7cgmva", "linked_items": ([{"id": "900", "name": "Repository definition", "board": {"id": "5029561760", "name": "Work Repository"}}] if relation else [])},
    ]
    return {"id": "800", "name": "Daily occurrence", "updated_at": "2026-09-20T12:00:00Z", "column_values": columns}


def test_daily_tracker_normalizes_repository_relation_and_team_context():
    record = module.normalize({"name": "6_Daily Work Tracker"}, [daily_item()], [{"id": "crew-7", "name": "Aarya Vira", "group": {"title": "SkyStation Operations"}, "column_values": [{"id": "lookup_mm792kmk", "text": None}]}], [{"id": "7", "name": "Aarya Vira"}])["records"][0]
    assert record["stage"] == "daily_execution"
    assert record["work_repository_item_id"] == "900"
    assert record["team"] == "SkyStation Operations"
    assert record["data_state"] == "current"


def test_daily_tracker_flags_missing_relation_and_team():
    record = module.normalize({}, [daily_item(relation=False)], [])["records"][0]
    assert "missing_work_repository_relation" in record["validation_issues"]
    assert "missing_team_context" in record["validation_issues"]
    assert record["data_state"] == "needs_review"


def test_daily_tracker_preserves_multiple_people():
    record = module.normalize({}, [daily_item(owner_ids=("7", "8"))], [
        {"id": "crew-7", "name": "Aarya Vira", "group": {"title": "CAD"}, "column_values": [{"id": "lookup_mm792kmk", "text": None}]},
        {"id": "crew-8", "name": "Sai Akshobhyaa Vrinda", "group": {"title": "SkyStation Operations"}, "column_values": [{"id": "lookup_mm792kmk", "text": None}]},
    ], [{"id": "7", "name": "Aarya Vira"}, {"id": "8", "name": "Sai Akshobhyaa Vrinda"}])["records"][0]
    assert record["owner_ids"] == ["7", "8"]
    assert record["teams"] == ["CAD", "SkyStation Operations"]


def test_daily_tracker_uses_verified_user_name_join_for_crew_groups():
    record = module.normalize({}, [daily_item()], [
        {"id": "crew-7", "name": "Srihari S", "group": {"title": "CAD"}, "column_values": [{"id": "lookup_mm792kmk", "text": None}]},
    ], [{"id": "7", "name": "srihari@skylarkdrones.com"}])["records"][0]
    assert record["team"] == "CAD"
