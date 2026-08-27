#!/usr/bin/env python3
"""Small protected portal runtime for the read-only normalized snapshots.

Production use requires PORTAL_API_TOKEN. For local-only development, set
PORTAL_DEV_ALLOW_LOCAL=1; this is accepted only on loopback requests.
"""
from __future__ import annotations

import json
import os
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

    def do_GET(self) -> None:
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
                sources[endpoint.removeprefix("/api/")] = {
                    "state": "current" if snapshot.exists() else "unavailable",
                    "schema_version": self._snapshot_schema(snapshot),
                }
            self._json(200, {"data_state": "current" if sources and all(v["state"] == "current" for v in sources.values()) else "unavailable", "sources": sources})
            return
        if self.path in SNAPSHOTS:
            if not self._authorized():
                self._json(401, {"error": "unauthorized"})
                return
            snapshot = SNAPSHOTS[self.path]
            if not snapshot.exists():
                self._json(503, {"error": "snapshot unavailable", "endpoint": self.path, "data_state": "unavailable"})
                return
            try:
                body = json.loads(snapshot.read_text())
                if not isinstance(body, dict) or not body.get("schema_version") or not isinstance(body.get("records"), list):
                    self._json(503, {"error": "snapshot invalid", "endpoint": self.path, "data_state": "unavailable"})
                    return
                self._json(200, body)
            except (OSError, json.JSONDecodeError):
                self._json(503, {"error": "snapshot invalid", "endpoint": self.path, "data_state": "unavailable"})
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
