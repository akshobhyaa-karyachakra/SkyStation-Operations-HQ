import importlib.util
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("billing_sync", ROOT / "scripts" / "sync_customer_repository_billing.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CustomerRepositoryBillingTests(unittest.TestCase):
    def test_normalizes_current_latest_billing_fields(self):
        snap = MODULE.normalize({"name": "Subitems of SkyStation Customer Repository", "updated_at": "2026-09-16T00:00:00Z"}, [{"id": "1", "name": "ACME", "subitems": [{"id": "2", "name": "Bikaner - SkyStation 1", "updated_at": "2026-09-16T00:00:00Z", "column_values": [{"id": "color_mm782zsj", "text": "Invoiced"}, {"id": "text_mm78rn5r", "text": "INV-1"}, {"id": "numeric_mm78f2z0", "text": "520000"}, {"id": "board_relation_mm4xbyad", "linked_items": [{"id": "3", "name": "SS2_009", "board": {"id": "5028042389", "name": "SkyStation Inventory"}}]}]}]}])
        self.assertEqual(snap["schema_version"], "billing.v1")
        self.assertEqual(snap["records"][0]["customer_name"], "ACME")
        self.assertEqual(snap["records"][0]["invoice_number"], "INV-1")
        self.assertEqual(snap["records"][0]["data_state"], "current")

    def test_invoiced_without_invoice_is_review(self):
        snap = MODULE.normalize({"name": "x"}, [{"id": "1", "name": "x", "subitems": [{"id": "2", "name": "x", "column_values": [{"id": "color_mm782zsj", "text": "Invoiced"}]}]}])
        self.assertEqual(snap["records"][0]["data_state"], "needs_review")
        self.assertIn("invoiced_without_invoice_number", snap["records"][0]["validation_issues"])

    def test_missing_secret_makes_no_request(self):
        env = os.environ.copy(); env.pop("MONDAY_API_TOKEN", None)
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "sync_customer_repository_billing.py")], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("no request was made", result.stderr)


if __name__ == "__main__":
    unittest.main()
