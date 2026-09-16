import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "sync_workflow_network.py"
spec = importlib.util.spec_from_file_location("sync_workflow_network", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("could not load workflow network adapter")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def source(name, records):
    return {"board": {"id": module.BOARD_IDS[name], "name": name}, "snapshot": {"records": records}, "item_count": len(records)}


class WorkflowNetworkContractTests(unittest.TestCase):
    def test_builds_semantic_nodes_from_source_records(self):
        sources = {
            "activity_repository": source("activity_repository", [{"source_item_id": "a1", "data_state": "current"}]),
            "flight_operations": source("flight_operations", [{"source_item_id": "f1", "status": "Stuck", "data_state": "current", "activity_repository_relations": [{"monday_item_id": "a1", "board_id": module.BOARD_IDS["activity_repository"]}]}]),
            "processing_qa": source("processing_qa", [{"source_item_id": "p1", "status": "Working on it", "data_state": "current", "activity_repository_relations": [{"monday_item_id": "a1", "board_id": module.BOARD_IDS["activity_repository"]}]}]),
            "report_submission": source("report_submission", [{"source_item_id": "r1", "status": "Done", "data_state": "current", "activity_repository_relations": [{"monday_item_id": "a1", "board_id": module.BOARD_IDS["activity_repository"]}]}]),
            "site_activities": source("site_activities", []),
            "work_tracker": source("work_tracker", []),
            "incident_logs": source("incident_logs", [{"source_item_id": "i1", "status": "Open", "data_state": "current"}]),
        }
        network = module.build_network(sources, synced_at="2026-09-16T00:00:00+00:00")
        self.assertEqual(network["schema_version"], "workflow-network.v1")
        self.assertTrue(network["nodes"]["flight_operations"]["red"])
        self.assertEqual(network["nodes"]["incident_logs"]["attention"], 1)
        delivery = next(stage for stage in network["stages"] if stage["stage_id"] == "customer_delivery")
        self.assertEqual(delivery["record_count"], 1)
        self.assertIn("activity-to-flight", {edge["edge_id"] for edge in network["edges"]})
        self.assertIn("flight-to-incidents", {edge["edge_id"] for edge in network["edges"]})

    def test_does_not_infer_activity_to_incident_edge(self):
        sources = {name: source(name, []) for name in module.ADAPTERS}
        network = module.build_network(sources)
        self.assertFalse(any(edge["from"] == "activity_repository" and edge["to"] == "incident_logs" for edge in network["edges"]))
        self.assertEqual(module.validate(network), [])

    def test_missing_token_exits_without_request(self):
        import os
        import sys
        original = os.environ.pop("MONDAY_API_TOKEN", None)
        argv = sys.argv[:]
        sys.argv = ["sync_workflow_network.py"]
        try:
            self.assertEqual(module.main(), 2)
        finally:
            sys.argv = argv
            if original is not None:
                os.environ["MONDAY_API_TOKEN"] = original


if __name__ == "__main__":
    unittest.main()
