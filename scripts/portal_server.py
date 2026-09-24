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
import secrets
import hashlib
import hmac
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from portal_metrics import build_metrics, build_person_work_heatmap, build_resource_calendar

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOTS = {
    "/api/crew": ROOT / "data" / "crew_repository.snapshot.json",
    "/api/activity": ROOT / "data" / "activity_repository.snapshot.json",
    "/api/flight": ROOT / "data" / "flight_operations.snapshot.json",
    "/api/site-activities": ROOT / "data" / "site_activities.snapshot.json",
    "/api/processing-qa": ROOT / "data" / "processing_qa.snapshot.json",
    "/api/report-submission": ROOT / "data" / "report_submission.snapshot.json",
    "/api/work-tracker": ROOT / "data" / "work_tracker.snapshot.json",
    "/api/daily-work-tracker": ROOT / "data" / "daily_work_tracker.snapshot.json",
    "/api/inventory": ROOT / "data" / "inventory.snapshot.json",
    "/api/incidents": ROOT / "data" / "incident_logs.snapshot.json",
    "/api/workflow-network": ROOT / "data" / "workflow_network.snapshot.json",
    "/api/billing": ROOT / "data" / "customer_repository_billing.snapshot.json",
}
TOKEN = os.environ.get("PORTAL_API_TOKEN")
DEV_LOCAL = os.environ.get("PORTAL_DEV_ALLOW_LOCAL") == "1"
MAX_AGE_SECONDS = int(os.environ.get("PORTAL_SNAPSHOT_MAX_AGE_SECONDS", "86400"))
CREW_PORTAL_STORE = Path(os.environ.get("CREW_PORTAL_STORE", ROOT / "data" / "crew_portal.records.json"))
CREW_PORTAL_FILES = Path(os.environ.get("CREW_PORTAL_FILES", ROOT / "data" / "crew-1to1-files"))
CREW_SCORE_VALUES = {"Needs improvement", "Developing", "Meets expectations", "Exceeds expectations"}
AUTH_DB = Path(os.environ.get("PORTAL_AUTH_DB", ROOT / "data" / "portal_auth.sqlite3"))
SESSION_TTL_SECONDS = int(os.environ.get("PORTAL_SESSION_TTL_SECONDS", "900"))
SESSION_COOKIE_NAME = "portal_session"
CSRF_COOKIE_NAME = "portal_csrf"
COOKIE_SECURE = os.environ.get("PORTAL_COOKIE_SECURE", "1") != "0"
COOKIE_SECURE_FLAG = "; Secure" if COOKIE_SECURE else ""
AUTH_LOCKOUT_THRESHOLD = int(os.environ.get("PORTAL_AUTH_LOCKOUT_THRESHOLD", "5"))
AUTH_LOCKOUT_SECONDS = int(os.environ.get("PORTAL_AUTH_LOCKOUT_SECONDS", "900"))
PASSWORD_ITERATIONS = 240_000
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


def _auth_connection() -> sqlite3.Connection:
    AUTH_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(AUTH_DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until REAL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            csrf_token_hash TEXT NOT NULL,
            expires_at REAL NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(username) REFERENCES users(username)
        );
        CREATE TABLE IF NOT EXISTS auth_audit (
            id TEXT PRIMARY KEY,
            action TEXT NOT NULL,
            username TEXT,
            created_at TEXT NOT NULL,
            remote_addr TEXT
        );
    """)
    return conn


def _normalize_username(value: str) -> str:
    return value.strip().casefold()


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt.hex()}${derived.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = stored.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        derived = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations))
        return hmac.compare_digest(derived.hex(), digest_hex)
    except (TypeError, ValueError):
        return False


def provision_user(db_path: Path, username: str, password: str, role: str = "manager") -> None:
    """Provision one account explicitly; this never runs automatically at server startup."""
    normalized = _normalize_username(username)
    if not normalized or len(password) < 12 or role not in {"manager", "editor", "read_only"}:
        raise ValueError("username, password length >= 12, and a supported role are required")
    now = datetime.now(timezone.utc).isoformat()
    global AUTH_DB
    previous = AUTH_DB
    AUTH_DB = Path(db_path)
    try:
        with _auth_connection() as conn:
            conn.execute("INSERT INTO users(username,password_hash,role,created_at,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(username) DO UPDATE SET password_hash=excluded.password_hash, role=excluded.role, enabled=1, failed_attempts=0, locked_until=NULL, updated_at=excluded.updated_at", (normalized, _hash_password(password), role, now, now))
    finally:
        AUTH_DB = previous


def _audit_auth(conn: sqlite3.Connection, action: str, username: str | None, remote_addr: str) -> None:
    conn.execute("INSERT INTO auth_audit(id,action,username,created_at,remote_addr) VALUES(?,?,?,?,?)", (str(uuid.uuid4()), action, username, datetime.now(timezone.utc).isoformat(), remote_addr))


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _session_user(self):
        raw_cookie = self.headers.get("Cookie", "")
        cookies = {}
        for part in raw_cookie.split(";"):
            if "=" in part:
                key, value = part.strip().split("=", 1)
                cookies[key] = value
        token = cookies.get(SESSION_COOKIE_NAME)
        if not token:
            return None
        try:
            with _auth_connection() as conn:
                row = conn.execute("SELECT u.username,u.role,u.enabled,s.csrf_token_hash,s.expires_at FROM sessions s JOIN users u ON u.username=s.username WHERE s.token_hash=?", (_token_hash(token),)).fetchone()
                if not row or not row["enabled"] or row["expires_at"] <= time.time():
                    if row:
                        conn.execute("DELETE FROM sessions WHERE token_hash=?", (_token_hash(token),))
                    return None
                return dict(row) | {"session_token": token, "csrf_cookie": cookies.get(CSRF_COOKIE_NAME)}
        except sqlite3.Error:
            return None

    def _csrf_valid(self, user) -> bool:
        if self.headers.get("Authorization", "") == f"Bearer {TOKEN}" and TOKEN:
            return True
        supplied = self.headers.get("X-CSRF-Token", "")
        cookie = user.get("csrf_cookie") if user else None
        return bool(user and supplied and cookie and hmac.compare_digest(supplied, cookie) and hmac.compare_digest(_token_hash(supplied), user["csrf_token_hash"]))

    def _authorized(self) -> bool:
        if DEV_LOCAL and self.client_address[0] in {"127.0.0.1", "::1"}:
            return True
        supplied = self.headers.get("Authorization", "")
        return (bool(TOKEN) and supplied == f"Bearer {TOKEN}") or self._session_user() is not None

    def _json(self, status: int, body: dict, extra_headers=None) -> None:
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        for key, value in extra_headers or []:
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _handle_login(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 64 * 1024 or self.headers.get("Content-Type", "").split(";", 1)[0] != "application/json":
                self._json(400, {"error": "invalid request"})
                return
            payload = json.loads(self.rfile.read(length))
            username = _normalize_username(str(payload.get("username", "")))
            password = payload.get("password")
            if not username or not isinstance(password, str):
                self._json(401, {"error": "invalid credentials"})
                return
            now = time.time()
            with _auth_connection() as conn:
                row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
                locked = bool(row and row["locked_until"] and row["locked_until"] > now)
                valid = bool(row and row["enabled"] and not locked and _verify_password(password, row["password_hash"]))
                if not valid:
                    if row and not locked:
                        attempts = int(row["failed_attempts"]) + 1
                        lock_until = now + AUTH_LOCKOUT_SECONDS if attempts >= AUTH_LOCKOUT_THRESHOLD else None
                        conn.execute("UPDATE users SET failed_attempts=?, locked_until=?, updated_at=? WHERE username=?", (attempts, lock_until, datetime.now(timezone.utc).isoformat(), username))
                    _audit_auth(conn, "login_failed", username if row else None, self.client_address[0])
                    self._json(401, {"error": "invalid credentials"})
                    return
                conn.execute("UPDATE users SET failed_attempts=0, locked_until=NULL, updated_at=? WHERE username=?", (datetime.now(timezone.utc).isoformat(), username))
                session_token = secrets.token_urlsafe(32)
                csrf_token = secrets.token_urlsafe(32)
                expires_at = now + SESSION_TTL_SECONDS
                conn.execute("DELETE FROM sessions WHERE username=?", (username,))
                conn.execute("INSERT INTO sessions(token_hash,username,csrf_token_hash,expires_at,created_at) VALUES(?,?,?,?,?)", (_token_hash(session_token), username, _token_hash(csrf_token), expires_at, datetime.now(timezone.utc).isoformat()))
                _audit_auth(conn, "login_success", username, self.client_address[0])
                cookies = [
                    ("Set-Cookie", f"{SESSION_COOKIE_NAME}={session_token}; Max-Age={SESSION_TTL_SECONDS}; Path=/; HttpOnly{COOKIE_SECURE_FLAG}; SameSite=Lax"),
                    ("Set-Cookie", f"{CSRF_COOKIE_NAME}={csrf_token}; Max-Age={SESSION_TTL_SECONDS}; Path=/{COOKIE_SECURE_FLAG}; SameSite=Lax"),
                ]
                self._json(200, {"user": {"username": username, "role": row["role"]}}, cookies)
        except (ValueError, json.JSONDecodeError, OSError, sqlite3.Error):
            self._json(400, {"error": "invalid request"})

    def do_POST(self) -> None:
        if self.path == "/api/auth/login":
            self._handle_login()
            return
        if self.path == "/api/auth/logout":
            user = self._session_user()
            if not user or not self._csrf_valid(user):
                self._json(401, {"error": "unauthorized"})
                return
            with _auth_connection() as conn:
                conn.execute("DELETE FROM sessions WHERE token_hash=?", (_token_hash(user["session_token"]),))
                _audit_auth(conn, "logout", user["username"], self.client_address[0])
            expired = f"{SESSION_COOKIE_NAME}=; Max-Age=0; Path=/; HttpOnly{COOKIE_SECURE_FLAG}; SameSite=Lax"
            self._json(200, {"ok": True}, [("Set-Cookie", expired)])
            return
        if not self.path.startswith("/api/crew-portal/"):
            self._json(404, {"error": "not found"})
            return
        if not self._authorized():
            self._json(401, {"error": "unauthorized"})
            return
        session_user = self._session_user()
        if session_user and session_user["role"] not in {"manager", "editor"}:
            self._json(403, {"error": "forbidden"})
            return
        if session_user and not self._csrf_valid(session_user):
            self._json(403, {"error": "csrf validation failed"})
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
        request = urlsplit(self.path)
        query = parse_qs(request.query)
        if request.path == "/api/auth/session":
            user = self._session_user()
            if not user:
                self._json(401, {"error": "unauthorized"})
                return
            self._json(200, {"user": {"username": user["username"], "role": user["role"]}, "expires_at": user["expires_at"]})
            return
        if request.path == "/manager-vault.html":
            if not self._session_user():
                self.send_response(302)
                self.send_header("Location", "/login.html?next=/manager-vault.html")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                return
            payload = (ROOT / "manager-vault.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if request.path in {"/api/resource-calendar", "/api/person-work-heatmap"}:
            if not self._authorized():
                self._json(401, {"error": "unauthorized"})
                return
            start_date = (query.get("start_date") or [None])[0]
            end_date = (query.get("end_date") or [None])[0]
            if not start_date or not end_date:
                self._json(400, {"error": "start_date and end_date are required"})
                return
            snapshot_path = SNAPSHOTS.get("/api/daily-work-tracker")
            state, updated_at = snapshot_state(snapshot_path) if snapshot_path else ("unavailable", None)
            if state in {"unavailable", "needs_review"} or snapshot_path is None:
                self._json(503, {"error": "daily work tracker snapshot unavailable", "data_state": state})
                return
            try:
                snapshot = json.loads(snapshot_path.read_text())
                records = snapshot.get("records", [])
                if request.path == "/api/resource-calendar":
                    body = build_resource_calendar(records, start_date, end_date, scope="team")
                else:
                    person_id = (query.get("person_id") or [None])[0]
                    if not person_id:
                        self._json(400, {"error": "person_id is required"})
                        return
                    grouping = (query.get("grouping") or ["category"])[0]
                    if grouping not in {"category", "customer"}:
                        self._json(400, {"error": "grouping must be category or customer"})
                        return
                    body = build_person_work_heatmap(records, person_id, start_date, end_date, grouping)
                body["source_state"] = state
                body["snapshot_updated_at"] = updated_at
                self._json(200, body)
            except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
                self._json(400, {"error": str(exc), "data_state": "needs_review"})
            return
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
