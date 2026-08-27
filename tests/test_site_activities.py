import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "sync_site_activities.py"
spec = importlib.util.spec_from_file_location("sync_site_activities", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("could not load Site Activities adapter")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def item(relation_board: str | None = "5027240228", activity_date: str | None = "2026-08-27", planned_date: str | None = None):
    return {"id": "123", "name": "Site Visit", "updated_at": "2026-08-27T00:00:00Z", "column_values": [
        {"id": "pulse_id_mm1gek5g", "text": "SS_SA-0001"},
        {"id": "date_mm3stezz", "text": planned_date},
        {"id": "date4", "text": activity_date},
        {"id": "multiple_person_mm1ra8c2", "persons_and_teams": [{"id": "7", "kind": "person", "name": "Aarya"}]},
        {"id": "board_relation_mm1gwp2a", "linked_items": ([{"id": "9", "name": "Activity", "board": {"id": relation_board}}] if relation_board else [])},
        {"id": "dropdown_mm1s419z", "text": None},
    ]}


class SiteActivitiesContractTests(unittest.TestCase):
    def test_activity_repository_relation_and_execution_date(self):
        record = module.normalize({"name": "4_Site Activities"}, [item()])["records"][0]
        self.assertEqual(record["stage"], "site_activity")
        self.assertEqual(record["activity_repository_relations"][0]["board_id"], "5027240228")
        self.assertEqual(record["activity_date"], "2026-08-27")
        self.assertEqual(record["data_state"], "current")

    def test_other_allowed_relation_is_preserved_separately(self):
        record = module.normalize({}, [item(relation_board="5028043141")])["records"][0]
        self.assertEqual(record["activity_repository_relations"], [])
        self.assertEqual(record["other_relation_targets"][0]["board_id"], "5028043141")
        self.assertEqual(record["data_state"], "current")

    def test_missing_activity_date_is_review(self):
        record = module.normalize({}, [item(activity_date=None)])["records"][0]
        self.assertIn("missing_activity_date", record["validation_issues"])

    def test_missing_relation_is_not_inferred(self):
        record = module.normalize({}, [item(relation_board=None)])["records"][0]
        self.assertEqual(record["activity_repository_relations"], [])
        self.assertIn("missing_relation", record["validation_issues"])

    def test_live_snapshot_count_validator(self):
        records = [{"source_item_id": str(i), "stage": "site_activity"} for i in range(44)]
        self.assertEqual(module.validate({"schema_version": "work_item.v1", "records": records}), [])


if __name__ == "__main__":
    unittest.main()
