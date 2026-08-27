import importlib.util
import unittest
from pathlib import Path

path = Path(__file__).parents[1] / "scripts" / "sync_inventory.py"
spec = importlib.util.spec_from_file_location("sync_inventory", path)
if spec is None or spec.loader is None:
    raise RuntimeError("could not load inventory adapter")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def col(id, text=None, linked_items=None):
    value = {"id": id, "text": text}
    if linked_items is not None:
        value["linked_items"] = linked_items
    return value


class InventoryContractTests(unittest.TestCase):
    def test_preserves_group_serial_and_relation_ids(self):
        item = {"id": "1", "name": "SS2_001", "updated_at": "2026-08-27T00:00:00Z",
                "group": {"id": "topics", "title": "SkyStations"}, "column_values": [
                    col("text_mm2qw26e", "SkyStation 2"), col("text_mm3rb17h", "SN1"), col("color_mm2q9923", "Good"),
                    col("board_relation_mm2qgehm", linked_items=[{"id": "10", "name": "Adani", "board": {"id": "5028043141", "name": "Customer"}}]),
                    col("board_relation_mm4x8z0a", linked_items=[{"id": "11", "name": "A1", "board": {"id": "5028043142", "name": "Subitems"}}]),
                    col("board_relation_mm5r9a4m", linked_items=[]), col("location_mm2qk3qr", "Khavda"),
                    col("timerange_mm4ws6n3"), col("date_mm4wawf6"), col("numeric_mm5bjaex", "12")
                ]}
        rec = module.normalize({"name": "SkyStation Inventory"}, [item])["records"][0]
        self.assertEqual(rec["group_id"], "topics")
        self.assertEqual(rec["serial_or_unit_id"], "SN1")
        self.assertEqual(rec["customer_relations"][0]["monday_item_id"], "10")
        self.assertEqual(rec["cycle_count"], "12")

    def test_missing_type_and_serial_are_review(self):
        item = {"id": "1", "name": "unknown", "column_values": [col("color_mm2q9923", "Good")]}
        rec = module.normalize({}, [item])["records"][0]
        self.assertIn("missing_asset_type", rec["validation_issues"])
        self.assertIn("missing_serial_or_unit_identifier", rec["validation_issues"])

    def test_wrong_relation_target_is_review(self):
        item = {"id": "1", "name": "x", "column_values": [col("text_mm2qw26e", "Drone"), col("text_mm3rb17h", "SN"),
            col("board_relation_mm2qgehm", linked_items=[{"id": "9", "board": {"id": "999"}}])]}
        rec = module.normalize({}, [item])["records"][0]
        self.assertIn("unexpected_customer_relation_target", rec["validation_issues"])

    def test_live_snapshot_count_validator(self):
        records = [{"source_item_id": str(i)} for i in range(121)]
        self.assertEqual(module.validate({"schema_version": "inventory_asset.v1", "records": records}), [])


if __name__ == "__main__":
    unittest.main()
