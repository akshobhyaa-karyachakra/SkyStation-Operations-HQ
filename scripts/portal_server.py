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

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "data" / "crew_repository.snapshot.json"
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
        if self.path == "/api/crew":
            if not self._authorized():
                self._json(401, {"error": "unauthorized"})
                return
            if not SNAPSHOT.exists():
                self._json(503, {"error": "crew snapshot unavailable"})
                return
            try:
                self._json(200, json.loads(SNAPSHOT.read_text()))
            except (OSError, json.JSONDecodeError):
                self._json(503, {"error": "crew snapshot invalid"})
            return
        if self.path.startswith("/data/"):
            self._json(404, {"error": "direct data access disabled"})
            return
        super().do_GET()

    def log_message(self, format: str, *args) -> None:
        # Keep request logs useful without logging authorization headers or payloads.
        super().log_message(format, *args)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8767"))
    server = ThreadingHTTPServer((os.environ.get("HOST", "127.0.0.1"), port), Handler)
    print(f"portal server listening on {server.server_address[0]}:{port}")
    server.serve_forever()
