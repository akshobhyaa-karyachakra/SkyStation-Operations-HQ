#!/usr/bin/env python3
"""Small protected portal runtime for the read-only normalized snapshots.

Production use requires PORTAL_API_TOKEN. For local-only development, set
PORTAL_DEV_ALLOW_LOCAL=1; this is accepted only on loopback requests.
"""
from __future__ import annotations

import base64
import binascii
import json
import os
import time
import uuid
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from portal_metrics import build_metrics

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOTS = {
    "/api/crew": ROOT / "data" / "crew_repository.snapshot.json",
    "/api/activity": ROOT / "data" / "activity_repository.snapshot.json",
    "/api/flight": ROOT / "data" / "flight_operations.snapshot.json",
    "/api/site-activities": ROOT / "data" / "site_activities.snapshot.json",
    "/api/processing-qa": ROOT / "data" / "processing_qa.snapshot.json",
    "/api/report-submission": ROOT / "data" / "report_submission.snapshot.json",
    "/api/work-tracker": ROOT / "data" / "work_tracker.snapshot.json",
    "/api/inventory": ROOT / "data" / "inventory.snapshot.json",
    "/api/incidents": ROOT / "data" / "incident_logs.snapshot.json",
}
TOKEN = os.environ.get("PORTAL_API_TOKEN")
DEV_LOCAL = os.environ.get("PORTAL_DEV_ALLOW_LOCAL") == "1"
MAX_AGE_SECONDS = int(os.environ.get("PORTAL_SNAPSHOT_MAX_AGE_SECONDS", "86400"))
CREW_PORTAL_STORE = Path(os.environ.get("CREW_PORTAL_STORE", ROOT / "data" / "crew_portal.records.json"))
CREW_PORTAL_FILES = Path(os.environ.get("CREW_PORTAL_FILES", ROOT / "data" / "crew-1to1-files"))
CREW_SCORE_VALUES = {"Needs improvement", "Developing", "Meets expectations", "Exceeds expectations"}
MAX_PORTAL_BODY = 12 * 1024 * 1024


def _empty_crew_portal() -> dict:
    return {"schema_version": "crew_portal.v1", "role_lenses": [], "responsibilities": [], "performance": [], "edit_requests": [], "one_to_ones": [], "audit": []}


def _load_crew_portal() -> dict:
    if not CREW_PORTAL_STORE.exists():
        return _empty_crew_portal()
    try:
        body = json.loads(CREW_PORTAL_STORE.read_text())
        if body.get("schema_version") != "crew_portal.v1":
            raise ValueError("unsupported crew portal schema")
        return body
    except (OSError, json.JSONDecodeError, ValueError):
        raise ValueError("crew portal store unavailable")


def _save_crew_portal(body: dict) -> None:
    CREW_PORTAL_STORE.parent.mkdir(parents=True, exist_ok=True)
    temp = CREW_PORTAL_STORE.with_suffix(CREW_PORTAL_STORE.suffix + ".tmp")
    temp.write_text(json.dumps(body, indent=2) + "\n")
    temp.replace(CREW_PORTAL_STORE)


def _audit(body: dict, action: str, actor: str, entity_id: str) -> dict:
    entry = {"audit_id": str(uuid.uuid4()), "action": action, "actor": actor, "entity_id": entity_id, "timestamp": datetime.now(timezone.utc).isoformat()}
    body["audit"].append(entry)
    return entry


def snapshot_state(snapshot: Path) -> tuple[str, str | None]:
    if not snapshot.exists():
        return "unavailable", None
    try:
        body = json.loads(snapshot.read_text())
        if not isinstance(body, dict) or not body.get("schema_version") or not isinstance(body.get("records"), list):
            return "needs_review", None
        age = max(0, time.time() - snapshot.stat().st_mtime)
        return ("stale" if age > MAX_AGE_SECONDS else "current"), datetime.fromtimestamp(snapshot.stat().st_mtime, timezone.utc).isoformat()
    except (OSError, json.JSONDecodeError, ValueError):
        return "needs_review", None


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _authorized(self) -> bool:
        if DEV_LOCAL and self.client_address[0] in {"127.0.0.1", "::1"}:
            return True
        supplied = self.headers.get("Authorization", "")
        return bool(TOKEN) and supplied == f"Bearer {TOKEN}"

    def _json(self, status: int, body: dict) -> None:
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self) -> None:
        if not self.path.startswith("/api/crew-portal/"):
            self._json(404, {"error": "not found"})
            return
        if not self._authorized():
            self._json(401, {"error": "unauthorized"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_PORTAL_BODY:
                self._json(413, {"error": "request too large or empty"})
                return
            raw = self.rfile.read(length)
            if self.headers.get("Content-Type", "").split(";", 1)[0] != "application/json":
                self._json(415, {"error": "application/json required"})
                return
            payload = json.loads(raw)
            body = _load_crew_portal()
            actor = self.headers.get("X-Portal-Actor-Id", "authenticated-user")
            now = datetime.now(timezone.utc).isoformat()
            if self.path == "/api/crew-portal/role-lenses":
                responsibilities = payload.get("responsibilities")
                if not payload.get("person_id") or not payload.get("role_name") or not isinstance(responsibilities, list) or not responsibilities:
                    self._json(400, {"error": "person_id, role_name, and responsibilities are required"})
                    return
                ids = [str(item.get("id", "")) for item in responsibilities]
                total = sum(float(item.get("weight", 0)) for item in responsibilities)
                if len(ids) != len(set(ids)) or any(not item.get("id") or not item.get("title") for item in responsibilities):
                    self._json(400, {"error": "role lens responsibilities must have unique ids and titles"})
                    return
                if total != 100:
                    self._json(400, {"error": "role lens weights must total 100"})
                    return
                person_id = str(payload["person_id"])
                version = 1 + max((r.get("version", 0) for r in body.get("role_lenses", []) if r.get("person_id") == person_id), default=0)
                record = {"id": str(uuid.uuid4()), "person_id": person_id, "role_name": payload["role_name"], "band": payload.get("band"), "responsibilities": responsibilities, "weight_total": int(total), "effective_from": payload.get("effective_from"), "version": version, "status": "Active", "created_at": now, "created_by": actor}
                body.setdefault("role_lenses", []).append(record)
                audit = _audit(body, "role_lens_created", actor, record["id"])
            elif self.path == "/api/crew-portal/performance":
                if payload.get("score") not in CREW_SCORE_VALUES:
                    self._json(400, {"error": "invalid score", "allowed": sorted(CREW_SCORE_VALUES)})
                    return
                if not payload.get("person_id") or not payload.get("period"):
                    self._json(400, {"error": "person_id and period are required"})
                    return
                role_lens_id = payload.get("role_lens_id")
                role_lens = next((r for r in body.get("role_lenses", []) if r.get("id") == role_lens_id and r.get("person_id") == str(payload["person_id"])), None) if role_lens_id else None
                if role_lens_id and role_lens is None:
                    self._json(400, {"error": "role_lens_id is invalid for person"})
                    return
                ratings = payload.get("ratings", {})
                calculated_score = None
                if role_lens:
                    if not isinstance(ratings, dict) or any(float(value) < 0 or float(value) > 5 for value in ratings.values()):
                        self._json(400, {"error": "ratings must be between 0 and 5"})
                        return
                    if any(item["id"] not in ratings for item in role_lens["responsibilities"]):
                        self._json(400, {"error": "ratings are required for every role-lens responsibility"})
                        return
                    calculated_score = round(sum(float(item["weight"]) * float(ratings[item["id"]]) / 5 for item in role_lens["responsibilities"]), 2)
                record = {"id": str(uuid.uuid4()), "person_id": str(payload["person_id"]), "period": payload["period"], "score": payload["score"], "role_lens_id": role_lens_id, "role_lens_version": role_lens.get("version") if role_lens else None, "ratings": ratings, "calculated_score": calculated_score, "goals": payload.get("goals", ""), "evidence": payload.get("evidence", []), "manager_review": payload.get("manager_review", "Pending"), "employee_acknowledged": bool(payload.get("employee_acknowledged", False)), "created_at": now, "created_by": actor, "status": "Open"}
                body["performance"].append(record)
                audit = _audit(body, "performance_created", actor, record["id"])
            elif self.path == "/api/crew-portal/responsibilities":
                if not payload.get("person_id") or not payload.get("title"):
                    self._json(400, {"error": "person_id and title are required"})
                    return
                record = {"id": str(uuid.uuid4()), "person_id": str(payload["person_id"]), "title": payload["title"], "scope": payload.get("scope", ""), "effective_date": payload.get("effective_date"), "status": payload.get("status", "Active"), "version": 1, "created_at": now, "created_by": actor}
                body["responsibilities"].append(record)
                audit = _audit(body, "responsibility_created", actor, record["id"])
            elif self.path == "/api/crew-portal/requests":
                if not payload.get("person_id") or not payload.get("requested_change"):
                    self._json(400, {"error": "person_id and requested_change are required"})
                    return
                request_type = payload.get("request_type", "responsibility_edit")
                record = {"id": str(uuid.uuid4()), "person_id": str(payload["person_id"]), "request_type": request_type, "requested_change": payload["requested_change"], "reason": payload.get("reason", ""), "status": "Pending", "created_at": now, "created_by": actor}
                body["edit_requests"].append(record)
                audit = _audit(body, "responsibility_edit_requested" if request_type == "responsibility_edit" else "crew_edit_requested", actor, record["id"])
            elif self.path == "/api/crew-portal/one-to-ones":
                if not payload.get("person_id") or not payload.get("meeting_month") or not payload.get("filename") or not payload.get("content_base64"):
                    self._json(400, {"error": "person_id, meeting_month, filename, and content_base64 are required"})
                    return
                content = base64.b64decode(payload["content_base64"], validate=True)
                if not content.startswith(b"%PDF-") or len(content) > 10 * 1024 * 1024:
                    self._json(400, {"error": "invalid PDF file"})
                    return
                version = 1 + sum(1 for r in body["one_to_ones"] if r.get("person_id") == str(payload["person_id"]) and r.get("meeting_month") == payload["meeting_month"])
                file_id = str(uuid.uuid4())
                CREW_PORTAL_FILES.mkdir(parents=True, exist_ok=True)
                (CREW_PORTAL_FILES / f"{file_id}.pdf").write_bytes(content)
                record = {"id": file_id, "person_id": str(payload["person_id"]), "meeting_month": payload["meeting_month"], "filename": payload["filename"], "version": version, "upload_status": "Stored", "storage_key": f"{file_id}.pdf", "uploaded_at": now, "uploaded_by": actor}
                body["one_to_ones"].append(record)
                audit = _audit(body, "one_to_one_uploaded", actor, record["id"])
            else:
                self._json(404, {"error": "not found"})
                return
            _save_crew_portal(body)
            self._json(201, {"record": record, "audit": audit})
        except (ValueError, json.JSONDecodeError, OSError, binascii.Error):
            self._json(503, {"error": "crew portal storage unavailable", "data_state": "needs_review"})

    def do_GET(self) -> None:
        if self.path == "/api/crew-portal/role-lenses":
            if not self._authorized():
                self._json(401, {"error": "unauthorized"})
                return
            try:
                body = _load_crew_portal()
                self._json(200, {"schema_version": body["schema_version"], "role_lenses": body.get("role_lenses", [])})
            except ValueError:
                self._json(503, {"error": "crew portal store unavailable", "data_state": "needs_review"})
            return
        if self.path == "/api/crew-portal":
            if not self._authorized():
                self._json(401, {"error": "unauthorized"})
                return
            try:
                self._json(200, _load_crew_portal())
            except ValueError:
                self._json(503, {"error": "crew portal store unavailable", "data_state": "needs_review"})
            return
        if self.path == "/api/metrics":
            if not self._authorized():
                self._json(401, {"error": "unauthorized"})
                return
            snapshots = {}
            for name, snapshot in ((p.removeprefix("/api/"), path) for p, path in SNAPSHOTS.items()):
                try:
                    snapshots[name] = json.loads(snapshot.read_text()) if snapshot.exists() else None
                except (OSError, json.JSONDecodeError):
                    snapshots[name] = None
            self._json(200, build_metrics(snapshots))
            return
        if self.path == "/api/public-status":
            sources = {}
            for endpoint, snapshot in SNAPSHOTS.items():
                state, updated_at = snapshot_state(snapshot)
                sources[endpoint.removeprefix("/api/")] = {
                    "state": state,
                    "schema_version": self._snapshot_schema(snapshot),
                    "updated_at": updated_at,
                }
            overall = "current" if sources and all(v["state"] == "current" for v in sources.values()) else ("needs_review" if any(v["state"] == "needs_review" for v in sources.values()) else ("stale" if any(v["state"] == "stale" for v in sources.values()) else "unavailable"))
            self._json(200, {"data_state": overall, "sources": sources})
            return
        if self.path in SNAPSHOTS:
            if not self._authorized():
                self._json(401, {"error": "unauthorized"})
                return
            snapshot = SNAPSHOTS[self.path]
            state, updated_at = snapshot_state(snapshot)
            if state == "unavailable":
                self._json(503, {"error": "snapshot unavailable", "endpoint": self.path, "data_state": state})
                return
            if state == "needs_review":
                self._json(503, {"error": "snapshot invalid", "endpoint": self.path, "data_state": state})
                return
            try:
                body = json.loads(snapshot.read_text())
                body["data_state"] = state
                body["snapshot_updated_at"] = updated_at
                self._json(200, body)
            except (OSError, json.JSONDecodeError, TypeError):
                self._json(503, {"error": "snapshot invalid", "endpoint": self.path, "data_state": "needs_review"})
            return
        if self.path.startswith("/data/"):
            self._json(404, {"error": "direct data access disabled"})
            return
        super().do_GET()

    @staticmethod
    def _snapshot_schema(snapshot: Path) -> str | None:
        if not snapshot.exists():
            return None
        try:
            body = json.loads(snapshot.read_text())
            return body.get("schema_version") if isinstance(body, dict) else None
        except (OSError, json.JSONDecodeError):
            return None

    def log_message(self, format: str, *args) -> None:
        # Keep request logs useful without logging authorization headers or payloads.
        super().log_message(format, *args)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8767"))
    server = ThreadingHTTPServer((os.environ.get("HOST", "127.0.0.1"), port), Handler)
    print(f"portal server listening on {server.server_address[0]}:{port}")
    server.serve_forever()
