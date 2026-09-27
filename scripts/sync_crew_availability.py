#!/usr/bin/env python3
"""Ingest a saved Monday Crew Daily Availability response into SQLite.

The raw response may be supplied with --input. A future server-side Monday
adapter can write the same board/items payload and call ingest_board_payload.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from backend.crew_availability import ingest_board_payload, DEFAULT_DB

p=argparse.ArgumentParser(); p.add_argument('--input',required=True,type=Path); p.add_argument('--db',default=str(DEFAULT_DB)); a=p.parse_args()
payload=json.loads(a.input.read_text())
print(json.dumps(ingest_board_payload(payload,Path(a.db)),indent=2))
