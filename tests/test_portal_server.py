import http.client
import importlib
import json
import sys
import threading
import time
from http.cookies import SimpleCookie
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
    work_snapshot = tmp_path / "work_tracker.snapshot.json"
    work_snapshot.write_text(json.dumps({
        "schema_version": "work_item.v1",
        "records": [{
            "source_item_id": "work-1", "name": "Example work", "start_date": "2026-09-20",
            "owner": [{"monday_user_id": "1", "name": "Example Person", "kind": "person"}],
            "category": "Inspection", "status": "Done", "data_state": "current",
        }],
    }))
    daily_snapshot = tmp_path / "daily_work_tracker.snapshot.json"
    daily_snapshot.write_text(json.dumps({
        "schema_version": "daily_work_tracker.v1",
        "records": [{
            "source_item_id": "daily-1", "name": "Example daily work", "work_date": "2026-09-20",
            "owner": [{"monday_user_id": "1", "name": "Example Person", "kind": "person"}],
            "teams": ["Site Operations"], "team": "Site Operations", "work_type": "One Time",
            "status": "Done", "data_state": "current",
        }],
    }))
    monkeypatch.setattr(portal_server, "SNAPSHOTS", {"/api/inventory": snapshot, "/api/crew": crew_snapshot, "/api/work-tracker": work_snapshot, "/api/daily-work-tracker": daily_snapshot})
    portal_store = tmp_path / "crew_portal.json"
    monkeypatch.setattr(portal_server, "CREW_PORTAL_STORE", portal_store)
    monkeypatch.setattr(portal_server, "CREW_PORTAL_FILES", tmp_path / "crew-files")
    monkeypatch.setattr(portal_server, "TOKEN", "test-token")
    monkeypatch.setattr(portal_server, "DEV_LOCAL", False)
    monkeypatch.setattr(portal_server, "MAX_AGE_SECONDS", 86400)
    monkeypatch.setattr(portal_server, "AUTH_DB", tmp_path / "auth.sqlite3")
    monkeypatch.setattr(portal_server, "SESSION_TTL_SECONDS", 900)
    monkeypatch.setattr(portal_server, "AUTH_LOCKOUT_THRESHOLD", 3)
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
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        parsed = body.decode()
    return response.status, parsed


def post_json(server, path, body, headers=None):
    payload = json.dumps(body).encode()
    request_headers = {"Content-Type": "application/json", "Content-Length": str(len(payload)), **(headers or {})}
    conn = http.client.HTTPConnection(*server.server_address, timeout=3)
    conn.request("POST", path, body=payload, headers=request_headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    return response.status, json.loads(data)


def post_response(server, path, body, headers=None):
    payload = json.dumps(body).encode()
    request_headers = {"Content-Type": "application/json", "Content-Length": str(len(payload)), **(headers or {})}
    conn = http.client.HTTPConnection(*server.server_address, timeout=3)
    conn.request("POST", path, body=payload, headers=request_headers)
    response = conn.getresponse()
    data = response.read()
    headers = {}
    for key, value in response.getheaders():
        if key in headers:
            headers[key] = headers[key] + [value] if isinstance(headers[key], list) else [headers[key], value]
        else:
            headers[key] = value
    result = {"status": response.status, "headers": headers, "body": data}
    conn.close()
    return result


def cookie_value(headers, name):
    cookie = SimpleCookie()
    values = headers.get("Set-Cookie", "")
    if isinstance(values, list):
        values = "\n".join(values)
    cookie.load(values)
    return cookie[name].value if name in cookie else None


def test_inventory_requires_authentication(protected_server):
    server, _, _ = protected_server
    status, body = request(server, "/api/inventory")
    assert status == 401
    assert body == {"error": "unauthorized"}


def test_login_fails_closed_when_no_user_is_provisioned(protected_server):
    server, _, _ = protected_server
    result = post_response(server, "/api/auth/login", {"username": "manager", "password": "anything"})
    assert result["status"] == 401
    assert json.loads(result["body"]) == {"error": "invalid credentials"}
    assert "Set-Cookie" not in result["headers"]


def test_login_creates_session_and_protects_manager_shell(protected_server):
    server, _, portal_server = protected_server
    portal_server.provision_user(portal_server.AUTH_DB, "manager", "correct-password", "manager")
    before, _ = request(server, "/manager-vault.html")
    assert before == 302
    result = post_response(server, "/api/auth/login", {"username": "manager", "password": "correct-password"})
    assert result["status"] == 200
    session = cookie_value(result["headers"], portal_server.SESSION_COOKIE_NAME)
    csrf = cookie_value(result["headers"], portal_server.CSRF_COOKIE_NAME)
    assert session and csrf
    status, body = request(server, "/api/auth/session", {"Cookie": f"{portal_server.SESSION_COOKIE_NAME}={session}"})
    assert status == 200
    assert body["user"]["username"] == "manager"
    conn = http.client.HTTPConnection(*server.server_address, timeout=3)
    conn.request("GET", "/manager-vault.html", headers={"Cookie": f"{portal_server.SESSION_COOKIE_NAME}={session}"})
    response = conn.getresponse(); html = response.read().decode(); conn.close()
    assert response.status == 200
    assert "Manager Vault" in html


def test_wrong_password_is_generic_and_locks_after_threshold(protected_server):
    server, _, portal_server = protected_server
    portal_server.provision_user(portal_server.AUTH_DB, "manager", "correct-password", "manager")
    for _ in range(3):
        result = post_response(server, "/api/auth/login", {"username": "manager", "password": "wrong"})
        assert result["status"] == 401
        assert json.loads(result["body"]) == {"error": "invalid credentials"}
    result = post_response(server, "/api/auth/login", {"username": "manager", "password": "correct-password"})
    assert result["status"] == 401
    assert json.loads(result["body"]) == {"error": "invalid credentials"}


def test_logout_revokes_session(protected_server):
    server, _, portal_server = protected_server
    portal_server.provision_user(portal_server.AUTH_DB, "manager", "correct-password", "manager")
    result = post_response(server, "/api/auth/login", {"username": "manager", "password": "correct-password"})
    session = cookie_value(result["headers"], portal_server.SESSION_COOKIE_NAME)
    csrf = cookie_value(result["headers"], portal_server.CSRF_COOKIE_NAME)
    headers = {"Cookie": f"{portal_server.SESSION_COOKIE_NAME}={session}; {portal_server.CSRF_COOKIE_NAME}={csrf}", "X-CSRF-Token": csrf}
    logout = post_response(server, "/api/auth/logout", {}, headers)
    assert logout["status"] == 200
    status, _ = request(server, "/api/auth/session", {"Cookie": f"{portal_server.SESSION_COOKIE_NAME}={session}"})
    assert status == 401


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


def test_resource_calendar_requires_authentication(protected_server):
    server, _, _ = protected_server
    status, body = request(server, "/api/resource-calendar?start_date=2026-09-20&end_date=2026-09-20")
    assert status == 401
    assert body == {"error": "unauthorized"}


def test_resource_calendar_returns_source_backed_rows(protected_server):
    server, _, _ = protected_server
    status, body = request(server, "/api/resource-calendar?start_date=2026-09-20&end_date=2026-09-20", {"Authorization": "Bearer test-token"})
    assert status == 200
    assert body["schema_version"] == "resource_calendar.v1"
    assert body["rows"][0]["owner_id"] == "team:Site Operations"


def test_person_heatmap_returns_selected_person_context(protected_server):
    server, _, _ = protected_server
    status, body = request(server, "/api/person-work-heatmap?person_id=1&start_date=2026-09-20&end_date=2026-09-20", {"Authorization": "Bearer test-token"})
    assert status == 200
    assert body["schema_version"] == "person_work_heatmap.v1"
    assert body["person_id"] == "1"


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


def test_crew_portal_role_lenses_start_empty(protected_server):
    server, _, _ = protected_server
    status, body = request(server, "/api/crew-portal/role-lenses", {"Authorization": "Bearer test-token"})
    assert status == 200
    assert body["role_lenses"] == []


def test_crew_portal_creates_role_lens_with_valid_100_percent_weights(protected_server):
    server, _, _ = protected_server
    status, body = post_json(server, "/api/crew-portal/role-lenses", {
        "person_id": "1", "role_name": "Operations B2", "band": "B2",
        "responsibilities": [
            {"id": "execution", "title": "Operational Execution", "weight": 60},
            {"id": "reporting", "title": "Reporting & Documentation", "weight": 40},
        ], "effective_from": "2026-09-01",
    }, {"Authorization": "Bearer test-token", "X-Portal-Actor-Id": "manager-1"})
    assert status == 201
    assert body["record"]["weight_total"] == 100
    assert body["record"]["version"] == 1
    assert body["audit"]["action"] == "role_lens_created"


def test_crew_portal_rejects_role_lens_weights_not_equal_to_100(protected_server):
    server, _, _ = protected_server
    status, body = post_json(server, "/api/crew-portal/role-lenses", {
        "person_id": "1", "role_name": "Operations B2",
        "responsibilities": [{"id": "execution", "title": "Execution", "weight": 80}],
    }, {"Authorization": "Bearer test-token"})
    assert status == 400
    assert body["error"] == "role lens weights must total 100"


def test_monthly_review_calculates_from_role_lens_weights(protected_server):
    server, _, _ = protected_server
    lens_status, lens = post_json(server, "/api/crew-portal/role-lenses", {
        "person_id": "1", "role_name": "Operations B2", "responsibilities": [
            {"id": "execution", "title": "Execution", "weight": 60},
            {"id": "reporting", "title": "Reporting", "weight": 40},
        ],
    }, {"Authorization": "Bearer test-token"})
    assert lens_status == 201
    status, body = post_json(server, "/api/crew-portal/performance", {
        "person_id": "1", "period": "2026-09", "score": "Meets expectations",
        "role_lens_id": lens["record"]["id"],
        "ratings": {"execution": 5, "reporting": 3},
    }, {"Authorization": "Bearer test-token"})
    assert status == 201
    assert body["record"]["role_lens_id"] == lens["record"]["id"]
    assert body["record"]["calculated_score"] == 84
