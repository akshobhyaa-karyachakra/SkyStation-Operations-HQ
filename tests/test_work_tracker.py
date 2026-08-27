import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "sync_work_tracker.py"
spec = importlib.util.spec_from_file_location("sync_work_tracker", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("could not load Work Tracker adapter")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def item(status="In Progress", owner=True, end_date=None):
    return {"id": "123", "name": "Internal task", "updated_at": "2026-08-27T00:00:00Z", "column_values": [
        {"id": "pulse_id_mm59p0n3", "text": "SS_WT-0001"},
        {"id": "date_mm53ct31", "text": "2026-08-26"},
        {"id": "date_mm4sr6k2", "text": end_date},
        {"id": "color_mm4spkpm", "text": status},
        {"id": "color_mm4sqdxz", "text": "High"},
        {"id": "multiple_person_mm4s27gp", "persons_and_teams": ([{"id": "7", "kind": "person", "name": "Aarya"}] if owner else [])},
        {"id": "dropdown_mm4sktjr", "text": "Development"},
        {"id": "text_mm4sz5me", "text": "note"}, {"id": "text_mm6a7946", "text": None},
        {"id": "file_mm53hzbr", "value": None},
    ]}


class WorkTrackerContractTests(unittest.TestCase):
    def test_normalizes_internal_work_and_owner_id(self):
        record = module.normalize({"name": "6_Work Tracker"}, [item()])["records"][0]
        self.assertEqual(record["stage"], "internal_work")
        self.assertEqual(record["owner"][0]["monday_user_id"], "7")
        self.assertEqual(record["data_state"], "current")

    def test_done_without_end_date_is_review(self):
        record = module.normalize({}, [item(status="Done", end_date=None)])["records"][0]
        self.assertIn("done_without_end_date", record["validation_issues"])

    def test_active_without_owner_is_review(self):
        record = module.normalize({}, [item(owner=False)])["records"][0]
        self.assertIn("active_task_without_owner", record["validation_issues"])

    def test_live_snapshot_count_validator(self):
        records = [{"source_item_id": str(i), "stage": "internal_work"} for i in range(43)]
        self.assertEqual(module.validate({"schema_version": "work_item.v1", "records": records}), [])


if __name__ == "__main__":
    unittest.main()
