import importlib.util
import unittest
from pathlib import Path

path = Path(__file__).parents[1] / "scripts" / "sync_incident_logs.py"
spec = importlib.util.spec_from_file_location("sync_incident_logs", path)
if spec is None or spec.loader is None:
    raise RuntimeError("could not load incident adapter")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def c(id, text=None, linked=None):
    value = {"id": id, "text": text}
    if linked is not None: value["linked_items"] = linked
    return value


class IncidentContractTests(unittest.TestCase):
    def test_preserves_incident_and_relation_ids(self):
        item = {"id": "1", "name": "ERR-1", "updated_at": "2026-08-27T00:00:00Z", "group": {"id": "g", "title": "New / Intake"}, "column_values": [
            c("text_mm5rg586", "ERR-1"), c("date_mm5rb3vs", "2026-08-27"), c("color_mm5r9mz6", "Under Review"),
            c("color_mm5rdvzk", "High"), c("color_mm5rg2cn", "Needs Evidence"), c("multiple_person_mm5rrm68"),
            c("board_relation_mm5r9hjx", linked=[{"id": "10", "board": {"id": "5028042389"}}]),
            c("board_relation_mm5r5f9b", linked=[{"id": "11", "board": {"id": "5028043141"}}]),
            c("board_relation_mm5re9f7", linked=[{"id": "12", "board": {"id": "5027240228"}}]),
        ]}
        rec = module.normalize({}, [item])["records"][0]
        self.assertEqual(rec["incident_ref"], "ERR-1")
        self.assertEqual(rec["relations"]["activity"][0]["monday_item_id"], "12")
        self.assertEqual(rec["data_state"], "current")

    def test_closed_without_closure_date_is_review(self):
        item = {"id": "1", "name": "ERR-1", "column_values": [c("text_mm5rg586", "ERR-1"), c("color_mm5r9mz6", "Closed"), c("color_mm5rg2cn", "Final")]}
        rec = module.normalize({}, [item])["records"][0]
        self.assertIn("closed_without_closure_date", rec["validation_issues"])

    def test_live_snapshot_count_validator(self):
        records = [{"source_item_id": str(i), "incident_ref": f"ERR-{i}"} for i in range(10)]
        self.assertEqual(module.validate({"schema_version": "incident.v1", "records": records}), [])


if __name__ == "__main__": unittest.main()
