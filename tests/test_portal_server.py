import http.client
import importlib
import json
import sys
import threading
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


@pytest.fixture
def protected_server(tmp_path, monkeypatch):
    portal_server = importlib.import_module("portal_server")
    snapshot = tmp_path / "inventory.snapshot.json"
    snapshot.write_text(json.dumps({
        "schema_version": "inventory_asset.v1",
        "item_count": 1,
        "records": [{"source_item_id": "1", "data_state": "current"}],
    }))
    monkeypatch.setattr(portal_server, "SNAPSHOTS", {"/api/inventory": snapshot})
    monkeypatch.setattr(portal_server, "TOKEN", "test-token")
    monkeypatch.setattr(portal_server, "DEV_LOCAL", False)
    monkeypatch.setattr(portal_server, "MAX_AGE_SECONDS", 86400)
    server = portal_server.ThreadingHTTPServer(("127.0.0.1", 0), portal_server.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server, snapshot, portal_server
    finally:
        server.shutdown()
        thread.join(timeout=2)


def request(server, path, headers=None):
    conn = http.client.HTTPConnection(*server.server_address, timeout=3)
    conn.request("GET", path, headers=headers or {})
    response = conn.getresponse()
    body = response.read()
    conn.close()
    return response.status, json.loads(body)


def test_inventory_requires_authentication(protected_server):
    server, _, _ = protected_server
    status, body = request(server, "/api/inventory")
    assert status == 401
    assert body == {"error": "unauthorized"}


def test_inventory_authorized_response_is_current(protected_server):
    server, _, _ = protected_server
    status, body = request(server, "/api/inventory", {"Authorization": "Bearer test-token"})
    assert status == 200
    assert body["schema_version"] == "inventory_asset.v1"
    assert body["data_state"] == "current"
    assert body["item_count"] == 1


def test_invalid_snapshot_fails_closed(protected_server):
    server, snapshot, _ = protected_server
    snapshot.write_text("not-json")
    status, body = request(server, "/api/inventory", {"Authorization": "Bearer test-token"})
    assert status == 503
    assert body["data_state"] == "needs_review"


def test_direct_snapshot_access_is_blocked(protected_server):
    server, _, _ = protected_server
    status, body = request(server, "/data/inventory.snapshot.json")
    assert status == 404
    assert body["error"] == "direct data access disabled"
