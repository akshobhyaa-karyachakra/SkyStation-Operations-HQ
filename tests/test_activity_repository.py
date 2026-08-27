import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "sync_activity_repository.py"
spec = importlib.util.spec_from_file_location("sync_activity_repository", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("could not load Activity Repository adapter")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ActivityRepositoryContractTests(unittest.TestCase):
    def test_normalizes_ids_and_relations_without_name_joins(self):
        item = {
            "id": "123",
            "name": "Khavda - Worksite Monitoring",
            "updated_at": "2026-08-27T00:00:00Z",
            "column_values": [
                {"id": "multiple_person_mm1g7qjb", "persons_and_teams": [{"id": "7", "kind": "person", "name": "Aarya"}]},
                {"id": "multiple_person_mm1gvaap", "persons_and_teams": []},
                {"id": "color_mm1gsat9", "text": "Worksite Monitoring"},
                {"id": "color_mm1g3h74", "text": "Yes"},
                {"id": "dropdown_mm3rv0jk", "text": "Wednesday"},
                {"id": "date_mm3t9qdk", "text": "2026-08-27"},
                {"id": "board_relation_mm2qwdd3", "linked_items": [{"id": "9", "name": "Customer", "board": {"id": "5028043141", "name": "Customers"}}]},
            ],
        }
        record = module.normalize({"name": "SkyStation Activity Repository"}, [item])["records"][0]
        self.assertEqual(record["source_item_id"], "123")
        self.assertEqual(record["owner"][0]["monday_user_id"], "7")
        self.assertEqual(record["customer_relations"][0]["monday_item_id"], "9")
        self.assertEqual(record["data_state"], "current")

    def test_missing_relation_is_review_not_customer_inference(self):
        item = {"id": "123", "name": "Internal Support", "column_values": [
            {"id": "color_mm1gsat9", "text": "One Time Activity"},
            {"id": "color_mm1g3h74", "text": "On Demand"},
            {"id": "board_relation_mm2qwdd3", "linked_items": []},
        ]}
        record = module.normalize({"name": "SkyStation Activity Repository"}, [item])["records"][0]
        self.assertEqual(record["customer_relations"], [])
        self.assertEqual(record["data_state"], "needs_review")

    def test_snapshot_validator_requires_current_live_count(self):
        snapshot = {"schema_version": "planned_activity.v1", "records": [{"source_item_id": str(i), "name": "x"} for i in range(72)]}
        self.assertEqual(module.validate(snapshot), [])


if __name__ == "__main__":
    unittest.main()