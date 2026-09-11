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
    crew_snapshot = tmp_path / "crew_repository.snapshot.json"
    crew_snapshot.write_text(json.dumps({
        "schema_version": "crew.v1",
        "item_count": 1,
        "records": [{"monday_item_id": "1", "name": "Example Person", "availability": "Available"}],
    }))
    monkeypatch.setattr(portal_server, "SNAPSHOTS", {"/api/inventory": snapshot, "/api/crew": crew_snapshot})
    portal_store = tmp_path / "crew_portal.json"
    monkeypatch.setattr(portal_server, "CREW_PORTAL_STORE", portal_store)
    monkeypatch.setattr(portal_server, "CREW_PORTAL_FILES", tmp_path / "crew-files")
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


def post_json(server, path, body, headers=None):
    payload = json.dumps(body).encode()
    request_headers = {"Content-Type": "application/json", "Content-Length": str(len(payload)), **(headers or {})}
    conn = http.client.HTTPConnection(*server.server_address, timeout=3)
    conn.request("POST", path, body=payload, headers=request_headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    return response.status, json.loads(data)


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


def test_crew_requires_authentication(protected_server):
    server, _, _ = protected_server
    status, body = request(server, "/api/crew")
    assert status == 401
    assert body == {"error": "unauthorized"}


def test_crew_authorized_response_has_protected_schema(protected_server):
    server, _, _ = protected_server
    status, body = request(server, "/api/crew", {"Authorization": "Bearer test-token"})
    assert status == 200
    assert body["schema_version"] == "crew.v1"
    assert body["data_state"] == "current"
    assert body["item_count"] == 1
    assert body["records"][0]["monday_item_id"] == "1"


def test_crew_invalid_snapshot_fails_closed(protected_server):
    server, _, portal_server = protected_server
    crew_snapshot = portal_server.SNAPSHOTS["/api/crew"]
    crew_snapshot.write_text("not-json")
    status, body = request(server, "/api/crew", {"Authorization": "Bearer test-token"})
    assert status == 503
    assert body["data_state"] == "needs_review"


def test_crew_direct_snapshot_access_is_blocked(protected_server):
    server, _, _ = protected_server
    status, body = request(server, "/data/crew_repository.snapshot.json")
    assert status == 404
    assert body["error"] == "direct data access disabled"


def test_crew_portal_requires_authentication(protected_server):
    server, _, _ = protected_server
    status, body = request(server, "/api/crew-portal")
    assert status == 401
    assert body == {"error": "unauthorized"}


def test_crew_portal_returns_protected_records(protected_server):
    server, _, _ = protected_server
    status, body = request(server, "/api/crew-portal", {"Authorization": "Bearer test-token"})
    assert status == 200
    assert body["schema_version"] == "crew_portal.v1"
    assert body["responsibilities"] == []
    assert body["performance"] == []
    assert body["edit_requests"] == []
    assert body["one_to_ones"] == []


def test_crew_portal_accepts_named_score_and_creates_audit_record(protected_server):
    server, _, _ = protected_server
    status, body = post_json(server, "/api/crew-portal/performance", {
        "person_id": "1", "period": "2026-09", "score": "Meets expectations",
        "goals": "Complete assigned QA handoffs", "evidence": ["https://example.test/evidence/1"],
    }, {"Authorization": "Bearer test-token"})
    assert status == 201
    assert body["record"]["score"] == "Meets expectations"
    assert body["audit"]["action"] == "performance_created"


def test_crew_portal_rejects_unsupported_score(protected_server):
    server, _, _ = protected_server
    status, body = post_json(server, "/api/crew-portal/performance", {
        "person_id": "1", "period": "2026-09", "score": "4/5",
    }, {"Authorization": "Bearer test-token"})
    assert status == 400
    assert body["error"] == "invalid score"


def test_crew_portal_accepts_responsibility_edit_request(protected_server):
    server, _, _ = protected_server
    status, body = post_json(server, "/api/crew-portal/requests", {
        "person_id": "1", "request_type": "responsibility_edit",
        "requested_change": "Own monthly QA review", "reason": "Role scope update",
    }, {"Authorization": "Bearer test-token"})
    assert status == 201
    assert body["record"]["status"] == "Pending"
    assert body["audit"]["action"] == "responsibility_edit_requested"


def test_crew_portal_accepts_pdf_upload_as_versioned_record(protected_server):
    server, _, _ = protected_server
    pdf = b"%PDF-1.7\nexample"
    import base64
    status, body = post_json(server, "/api/crew-portal/one-to-ones", {
        "person_id": "1", "meeting_month": "2026-09", "filename": "one-to-one.pdf",
        "content_base64": base64.b64encode(pdf).decode(),
    }, {"Authorization": "Bearer test-token"})
    assert status == 201
    assert body["record"]["upload_status"] == "Stored"
    assert body["record"]["version"] == 1
    assert body["audit"]["action"] == "one_to_one_uploaded"
