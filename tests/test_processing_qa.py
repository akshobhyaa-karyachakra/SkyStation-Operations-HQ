import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "sync_processing_qa.py"
spec = importlib.util.spec_from_file_location("sync_processing_qa", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("could not load Processing & QA adapter")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def item(status="Working on it", relation=True, blocker=None, completion=None):
    return {
        "id": "123",
        "name": "A5 B_12 Thermography",
        "updated_at": "2026-08-27T00:00:00Z",
        "column_values": [
            {"id": "pulse_id_mm1gek5g", "text": "SS_CAD-0001"},
            {"id": "multiple_person_mm22hxev", "persons_and_teams": [{"id": "7", "kind": "person", "name": "Aarya"}]},
            {"id": "date_mm1h5gsw", "text": "2026-08-26"},
            {"id": "date4", "text": "2026-08-26"},
            {"id": "date_mm1h7a47", "text": "2026-08-26"},
            {"id": "board_relation_mm1gwp2a", "linked_items": ([{"id": "9", "name": "Thermography", "board": {"id": "5027240228", "name": "Activity"}}] if relation else [])},
            {"id": "color_mm1g9w3q", "text": status},
            {"id": "dropdown_mm1skymk", "text": blocker},
            {"id": "date_mm1hcqss", "text": completion},
            {"id": "multiple_person_mm1hxa4v", "persons_and_teams": []},
            {"id": "file_mm65zqx", "value": None},
        ],
    }


class ProcessingQAContractTests(unittest.TestCase):
    def test_preserves_handoff_dates_and_relation(self):
        record = module.normalize({"name": "2_Processing and QA"}, [item()])["records"][0]
        self.assertEqual(record["stage"], "processing_qa")
        self.assertEqual(record["processing_start_date"], "2026-08-26")
        self.assertEqual(record["activity_repository_relations"][0]["board_id"], "5027240228")
        self.assertEqual(record["data_state"], "current")

    def test_unlinked_completed_item_is_review(self):
        record = module.normalize({"name": "2_Processing and QA"}, [item(status="Done", relation=False, completion="2026-08-26")])["records"][0]
        self.assertEqual(record["activity_repository_relations"], [])
        self.assertIn("missing_activity_relation", record["validation_issues"])

    def test_stuck_without_blocker_is_review(self):
        record = module.normalize({"name": "2_Processing and QA"}, [item(status="Stuck")])["records"][0]
        self.assertIn("stuck_without_blocker", record["validation_issues"])

    def test_live_snapshot_count_validator(self):
        records = [{"source_item_id": str(i), "stage": "processing_qa", "activity_repository_relations": []} for i in range(14)]
        self.assertEqual(module.validate({"schema_version": "work_item.v1", "records": records}), [])


if __name__ == "__main__":
    unittest.main()