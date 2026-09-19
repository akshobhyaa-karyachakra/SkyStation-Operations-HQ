import importlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
module = importlib.import_module("sync_crew_repository")


def payload(records):
    items = []
    for record in records:
        cols = []
        for cid, value in record.get("columns", {}).items():
            entry = {"id": cid, "text": value}
            if cid == "multiple_person_mm6msyq2":
                entry["persons_and_teams"] = value
            if cid == "board_relation_mm79kcd6":
                entry["linked_items"] = value
            cols.append(entry)
        items.append({"id": record["id"], "name": record["name"], "group": {"id": record["group_id"], "title": record["group"]}, "column_values": cols})
    return {"data": {"boards": [{"id": module.BOARD_ID, "name": "SkyStation Crew Repository", "updated_at": "2026-09-11T00:00:00Z", "items_page": {"items": items}}]}}


def record(i, availability="Available", group="Site Operations", team_lead="", manager=None):
    return {
        "id": str(i),
        "name": f"Person {i}",
        "group_id": f"group-{group}",
        "group": group,
        "columns": {
            "color_mm6mamdg": availability,
            "board_relation_mm79kcd6": [{"linked_item_id": "700", "linked_item_name": "Operator"}],
            "lookup_mm792kmk": "Engineering",
            "multiple_person_mm6msyq2": manager or [],
            "boolean_mm6m50k9": team_lead,
            "lookup_mm79sxzf": "B1",
            "text_mm6mx08z": "India",
            "boolean_mm6mvm85": "v",
            "date_mm6mm5pf": "2026-01-01",
            "email_mm6mx3gz": f"person{i}@example.com",
            "long_text_mm6mswwm": "",
        },
    }


def test_live_shape_allows_current_board_growth_and_counts_active_employed():
    records = [record(i) for i in range(16)] + [record(99, "Terminated")]
    snapshot = module.normalize(payload(records))
    assert len(snapshot["records"]) == 17
    assert module.validate(snapshot) == []
    assert sum(not r["historical"] for r in snapshot["records"]) == 16
    assert sum(r["availability"] == "On Leave" for r in snapshot["records"]) == 0


def test_on_leave_is_active_employed_but_not_available_now():
    snapshot = module.normalize(payload([record(1, "On Leave")]))
    person = snapshot["records"][0]
    assert person["employment_status"] == "Active"
    assert person["historical"] is False
    assert person["availability"] == "On Leave"


def test_team_lead_is_boolean_designation_and_manager_preserves_people_id():
    snapshot = module.normalize(payload([record(1, team_lead="v", manager=[{"id": 42, "kind": "person", "name": "Manager"}])]))
    person = snapshot["records"][0]
    assert person["team_lead"] is True
    assert person["manager"] == [{"monday_user_id": "42", "name": "Manager", "kind": "person"}]


def test_role_relation_and_live_mirrors_replace_deleted_text_role_and_band_columns():
    snapshot = module.normalize(payload([record(1)]))
    person = snapshot["records"][0]
    assert person["role_relation"] == {
        "monday_item_ids": ["700"],
        "items": [{"monday_item_id": "700", "name": "Operator"}],
    }
    assert person["team"] == "Engineering"
    assert person["band"] == "B1"
    assert "official_role" not in person


def test_missing_role_relation_is_needs_review_and_never_name_matched():
    item = record(1)
    item["columns"]["board_relation_mm79kcd6"] = []
    item["name"] = "Operator"
    snapshot = module.normalize(payload([item]))
    person = snapshot["records"][0]
    assert person["role_relation"] == {"monday_item_ids": [], "items": []}
    assert person["data_state"] == "needs_review"
    assert "missing_role_relation" in person["needs_review"]
    assert person["role_relation"]["items"] == []


def test_multiple_role_relations_are_needs_review_for_single_value_column():
    item = record(1)
    item["columns"]["board_relation_mm79kcd6"] = [
        {"linked_item_id": "700", "linked_item_name": "Operator"},
        {"linked_item_id": "701", "linked_item_name": "Other Operator"},
    ]
    snapshot = module.normalize(payload([item]))
    person = snapshot["records"][0]
    assert person["data_state"] == "needs_review"
    assert "multiple_role_relations" in person["needs_review"]


def test_duplicate_monday_ids_fail_validation():
    records = [record(1), record(1)]
    snapshot = module.normalize(payload(records))
    assert "duplicate Monday item IDs" in module.validate(snapshot)


def test_validator_accepts_current_17_record_shape(tmp_path):
    snapshot = {
        "schema_version": "crew.v1",
        "item_count": 17,
        "records": [
            {"monday_item_id": str(i), "name": f"Person {i}", "team_group": "Site Operations", "role_relation": {"monday_item_ids": ["700"], "items": [{"monday_item_id": "700", "name": "Operator"}]}, "availability": "Available", "manager": [], "historical": False, "data_state": "current", "needs_review": []}
            for i in range(16)
        ] + [{"monday_item_id": "16", "name": "Former Person", "team_group": "Site Operations", "role_relation": {"monday_item_ids": ["700"], "items": [{"monday_item_id": "700", "name": "Operator"}]}, "availability": "Terminated", "manager": [], "historical": True, "data_state": "current", "needs_review": []}],
    }
    path = tmp_path / "crew.json"
    path.write_text(json.dumps(snapshot))
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_crew_snapshot.py"), str(path)], capture_output=True, text=True)
    assert result.returncode == 0
    assert "17 records" in result.stdout
    assert "16 active" in result.stdout
