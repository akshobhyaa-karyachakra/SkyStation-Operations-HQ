import importlib.util
import json
import os
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("role_framework_sync", ROOT / "scripts" / "sync_role_framework.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def parent(item_id, name, subitems=None, values=None):
    return {
        "id": str(item_id),
        "name": name,
        "subitems": subitems or [],
        "column_values": values or [],
    }


def subitem(item_id, name, weight, updated_at="2026-09-17T00:00:00Z"):
    return {
        "id": str(item_id),
        "name": name,
        "updated_at": updated_at,
        "column_values": [
            {"id": "numeric_mm79pyxm", "text": str(weight), "value": json.dumps({"number": weight})}
        ],
    }


def role_values():
    return [
        {"id": "dropdown_mm792xk4", "text": "Engineering"},
        {"id": "dropdown_mm797pdx", "text": "L3"},
        {"id": "long_text_mm794f3t", "text": "Own the platform"},
        {"id": "long_text_mm79bmf8", "text": "Ship reliable systems"},
        {"id": "long_text_mm79jzma", "text": "Raise the bar"},
        {"id": "long_text_mm79bswk", "text": "Scope and autonomy"},
        {"id": "long_text_mm79qbfy", "text": "Demonstrated impact"},
        {"id": "color_mm79mv5d", "text": "Active"},
    ]


def test_normalizes_roles_with_stable_parent_and_competency_ids():
    parents = [parent("100", "Platform Engineer", [{"id": "200", "name": "Technical delivery"}, {"id": "201", "name": "Leadership"}], role_values())]
    board = {"id": MODULE.PARENT_BOARD, "name": "SkyStation Role Framework", "updated_at": "2026-09-17T00:00:00Z"}
    snapshot = MODULE.normalize(board, parents, [subitem("200", "Technical delivery", 60), subitem("201", "Leadership", 40)])

    assert snapshot["schema_version"] == "role-framework.v1"
    assert snapshot["roles"][0]["source_item_id"] == "100"
    assert snapshot["roles"][0]["competencies"] == [
        {"source_item_id": "200", "name": "Technical delivery", "weight": 60.0},
        {"source_item_id": "201", "name": "Leadership", "weight": 40.0},
    ]
    assert snapshot["roles"][0]["weight_total"] == 100.0
    assert snapshot["data_state"] == "current"


def test_validation_rejects_duplicate_ids_missing_and_non_numeric_weights_and_bad_totals():
    snapshot = {
        "schema_version": "role-framework.v1",
        "roles": [
            {"source_item_id": "1", "competencies": [
                {"source_item_id": "9", "name": "A", "weight": None},
                {"source_item_id": "9", "name": "B", "weight": "bad"},
            ], "weight_total": 40},
            {"source_item_id": "1", "competencies": []},
        ],
    }
    errors = MODULE.validate(snapshot)
    assert "duplicate role source item IDs" in errors
    assert "duplicate competency source item IDs" in errors
    assert "missing competency weight" in errors
    assert "non-numeric competency weight" in errors
    assert "role competency weights must total 100" in errors


def test_validation_rejects_missing_role_and_competency_ids():
    snapshot = MODULE.normalize(
        {"id": MODULE.PARENT_BOARD, "updated_at": "2026-09-17T00:00:00Z"},
        [{"id": None, "name": "Broken Role", "updated_at": None, "column_values": [], "subitems": [{"id": None, "name": "Broken competency"}]}],
        [],
    )
    errors = MODULE.validate(snapshot)
    assert "missing role source item ID" in errors
    assert "missing competency source item ID" in errors


def test_missing_token_fails_before_any_request(tmp_path):
    env = os.environ.copy()
    env.pop("MONDAY_API_TOKEN", None)
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "sync_role_framework.py"), "--output", str(tmp_path / "snapshot.json")],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "no request was made" in result.stderr
    assert not (tmp_path / "snapshot.json").exists()


def test_fetch_all_queries_parent_and_generated_subitem_board(monkeypatch):
    calls = []

    def fake_request(token, board_id, cursor):
        calls.append((token, board_id, cursor))
        if board_id == MODULE.PARENT_BOARD:
            return {"data": {"boards": [{"id": MODULE.PARENT_BOARD, "name": "Roles", "items_page": {"cursor": None, "items": []}}]}}
        return {"data": {"boards": [{"id": MODULE.SUBITEM_BOARD, "name": "Competencies", "items_page": {"cursor": None, "items": []}}]}}

    monkeypatch.setattr(MODULE, "request", fake_request)
    MODULE.fetch_all("secret")
    assert calls == [("secret", MODULE.PARENT_BOARD, None), ("secret", MODULE.SUBITEM_BOARD, None)]


@pytest.fixture
def protected_role_server(tmp_path, monkeypatch):
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "scripts"))
    import portal_server

    snapshot = tmp_path / "role_framework.snapshot.json"
    snapshot.write_text(json.dumps({"schema_version": "role-framework.v1", "roles": [], "records": []}))
    monkeypatch.setattr(portal_server, "SNAPSHOTS", {"/api/role-framework": snapshot})
    monkeypatch.setattr(portal_server, "TOKEN", "test-token")
    monkeypatch.setattr(portal_server, "DEV_LOCAL", False)
    monkeypatch.setattr(portal_server, "MAX_AGE_SECONDS", 86400)
    server = portal_server.ThreadingHTTPServer(("127.0.0.1", 0), portal_server.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server, snapshot
    finally:
        server.shutdown()
        thread.join(timeout=2)


def _get(server, path, headers=None):
    request = urllib.request.Request(f"http://127.0.0.1:{server.server_port}{path}", headers=headers or {})
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def test_role_framework_endpoint_requires_auth_and_serves_snapshot(protected_role_server):
    server, _ = protected_role_server
    assert _get(server, "/api/role-framework")[0] == 401
    status, body = _get(server, "/api/role-framework", {"Authorization": "Bearer test-token"})
    assert status == 200
    assert body["data_state"] == "current"


def test_role_framework_endpoint_marks_stale_snapshot(protected_role_server, monkeypatch):
    server, snapshot = protected_role_server
    monkeypatch.setattr(__import__("portal_server"), "MAX_AGE_SECONDS", -1)
    status, body = _get(server, "/api/role-framework", {"Authorization": "Bearer test-token"})
    assert status == 200
    assert body["data_state"] == "stale"


def test_role_framework_endpoint_returns_unavailable_and_needs_review(protected_role_server):
    server, snapshot = protected_role_server
    snapshot.unlink()
    assert _get(server, "/api/role-framework", {"Authorization": "Bearer test-token"})[0] == 503
    snapshot.write_text("not-json")
    status, body = _get(server, "/api/role-framework", {"Authorization": "Bearer test-token"})
    assert status == 503
    assert body["data_state"] == "needs_review"
