import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "sync_report_submission.py"
spec = importlib.util.spec_from_file_location("sync_report_submission", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("could not load Report Submission adapter")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def item(status="Done", activity=True, intake=False, link: str | None = "https://reports.example/1", blocker=None):
    return {"id": "123", "name": "A5 B_12 Thermography", "updated_at": "2026-08-27T00:00:00Z", "column_values": [
        {"id": "pulse_id_mm1gek5g", "text": "SS_REP-0001"},
        {"id": "color_mm1g9w3q", "text": status},
        {"id": "color_mm1sy1pv", "text": "Done" if status == "Done" else None},
        {"id": "dropdown_mm1sgtz8", "text": blocker},
        {"id": "link_mm1htkk8", "text": link},
        {"id": "board_relation_mm1gwp2a", "linked_items": ([{"id": "9", "name": "Activity", "board": {"id": "5027240228"}}] if activity else [])},
        {"id": "board_relation_mm5ag5sy", "linked_items": ([{"id": "8", "name": "Request", "board": {"id": "5028091149"}}] if intake else [])},
        {"id": "date_mm1h5gsw", "text": "2026-08-26"}, {"id": "date4", "text": "2026-08-26"},
        {"id": "date_mm1h7a47", "text": "2026-08-26"}, {"id": "date_mm1h35kq", "text": "2026-08-26"},
        {"id": "date_mm1ha6yw", "text": "2026-08-27"},
        {"id": "multiple_person_mm22yh1f", "persons_and_teams": [{"id": "7", "kind": "person", "name": "Aarya"}]},
    ]}


class ReportSubmissionContractTests(unittest.TestCase):
    def test_preserves_both_relations_and_delivery_evidence(self):
        record = module.normalize({"name": "3_Report Submission"}, [item(intake=True)])["records"][0]
        self.assertEqual(record["stage"], "report_submission")
        self.assertEqual(record["activity_repository_relations"][0]["board_id"], "5027240228")
        self.assertEqual(record["service_request_intake_relations"][0]["board_id"], "5028091149")
        self.assertEqual(record["report_link"], "https://reports.example/1")
        self.assertEqual(record["data_state"], "current")

    def test_done_without_link_is_review(self):
        record = module.normalize({}, [item(link=None)])["records"][0]
        self.assertIn("done_without_report_link", record["validation_issues"])
        self.assertEqual(record["data_state"], "needs_review")

    def test_stuck_without_reason_is_review(self):
        record = module.normalize({}, [item(status="Stuck", link=None)])["records"][0]
        self.assertIn("blocked_without_reason", record["validation_issues"])

    def test_missing_activity_relation_is_not_inferred(self):
        record = module.normalize({}, [item(activity=False)])["records"][0]
        self.assertEqual(record["activity_repository_relations"], [])
        self.assertIn("missing_activity_relation", record["validation_issues"])

    def test_live_snapshot_count_validator(self):
        records = [{"source_item_id": str(i), "stage": "report_submission"} for i in range(154)]
        self.assertEqual(module.validate({"schema_version": "work_item.v1", "records": records}), [])


if __name__ == "__main__":
    unittest.main()
