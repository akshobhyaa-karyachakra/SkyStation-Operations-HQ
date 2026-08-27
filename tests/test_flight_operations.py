import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "sync_flight_operations.py"
spec = importlib.util.spec_from_file_location("sync_flight_operations", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("could not load Flight Operations adapter")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def item(status="Done", relation=True, blocker=None, completion: str | None = "2026-08-27"):
    return {
        "id": "123",
        "name": "Baiya - AC Monitoring",
        "updated_at": "2026-08-27T00:00:00Z",
        "column_values": [
            {"id": "pulse_id_mm1gek5g", "text": "SS_FO-0001"},
            {"id": "date4", "text": "2026-08-27"},
            {"id": "color_mm1g9w3q", "text": status},
            {"id": "multiple_person_mm1ra8c2", "persons_and_teams": [{"id": "7", "kind": "person", "name": "Aarya"}]},
            {"id": "multiple_person_mm1h1fts", "persons_and_teams": []},
            {"id": "board_relation_mm1gwp2a", "linked_items": ([{"id": "9", "name": "Baiya - AC Monitoring", "board": {"id": "5027240228", "name": "Activity"}}] if relation else [])},
            {"id": "dropdown_mm1s419z", "text": blocker},
            {"id": "date_mm1h9es2", "text": completion},
        ],
    }


class FlightOperationsContractTests(unittest.TestCase):
    def test_normalizes_execution_and_activity_relation(self):
        record = module.normalize({"name": "1_Flight Operations"}, [item()])["records"][0]
        self.assertEqual(record["stage"], "flight")
        self.assertEqual(record["activity_id"], "SS_FO-0001")
        self.assertEqual(record["activity_repository_relations"][0]["board_id"], "5027240228")
        self.assertEqual(record["data_state"], "current")

    def test_stuck_without_blocker_is_review(self):
        record = module.normalize({"name": "1_Flight Operations"}, [item(status="Stuck", blocker=None, completion=None)])["records"][0]
        self.assertEqual(record["data_state"], "needs_review")
        self.assertIn("stuck_without_blocker", record["validation_issues"])

    def test_missing_relation_is_not_inferred_from_name(self):
        record = module.normalize({"name": "1_Flight Operations"}, [item(relation=False)])["records"][0]
        self.assertEqual(record["activity_repository_relations"], [])
        self.assertIn("missing_activity_relation", record["validation_issues"])

    def test_live_snapshot_count_validator(self):
        records = [{"source_item_id": str(i), "stage": "flight", "activity_repository_relations": []} for i in range(21)]
        self.assertEqual(module.validate({"schema_version": "work_item.v1", "records": records}), [])


if __name__ == "__main__":
    unittest.main()