"""Crew Daily Availability storage and public projection.

SQLite is the checked-in development/runtime adapter; the schema is deliberately
relational and can be migrated to PostgreSQL without changing the projection.
No Monday or Discord identifiers are returned by public_projection().
"""
from __future__ import annotations
import json, sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "crew_availability.sqlite3"
STATUSES = {"In Office", "Work from home", "Deployed", "Partially available", "Partially available / Half Day", "Leave or absent", "Unknown"}
PUBLIC_STATUS = {"Partially available": "Partially available / Half Day"}

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS sync_runs (
 id INTEGER PRIMARY KEY, source TEXT NOT NULL, started_at TEXT NOT NULL,
 finished_at TEXT, status TEXT NOT NULL, records_read INTEGER NOT NULL DEFAULT 0,
 error TEXT
);
CREATE TABLE IF NOT EXISTS raw_board_snapshots (
 id INTEGER PRIMARY KEY, sync_run_id INTEGER NOT NULL, board_id TEXT NOT NULL,
 captured_at TEXT NOT NULL, payload_json TEXT NOT NULL,
 FOREIGN KEY(sync_run_id) REFERENCES sync_runs(id)
);
CREATE TABLE IF NOT EXISTS crew_members (
 id INTEGER PRIMARY KEY, source_person_id TEXT UNIQUE, name TEXT NOT NULL,
 active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS crew_availability_daily (
 id INTEGER PRIMARY KEY, date TEXT NOT NULL, crew_member_id INTEGER NOT NULL,
 status TEXT NOT NULL, source_parent_id TEXT, source_subitem_id TEXT,
 source_updated_at TEXT, sync_run_id INTEGER NOT NULL, data_state TEXT NOT NULL DEFAULT 'current',
 validation_errors TEXT, UNIQUE(date, crew_member_id),
 FOREIGN KEY(crew_member_id) REFERENCES crew_members(id), FOREIGN KEY(sync_run_id) REFERENCES sync_runs(id)
);
CREATE INDEX IF NOT EXISTS idx_availability_date ON crew_availability_daily(date);
"""

def connect(path: Path = DEFAULT_DB) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db

def _now(): return datetime.now(timezone.utc).isoformat()

def _status(value):
    value = (value or "Unknown").strip()
    return PUBLIC_STATUS.get(value, value if value in STATUSES else "Unknown")

def ingest_board_payload(payload: dict, db_path: Path = DEFAULT_DB) -> dict:
    """Atomically ingest a Monday-shaped board payload after structural validation."""
    board = payload.get("board") or {}
    items = payload.get("items") or []
    if str(board.get("id")) != "5031561606": raise ValueError("unexpected Crew Daily Availability board")
    run_at = _now(); db = connect(db_path)
    run = db.execute("INSERT INTO sync_runs(source,started_at,status) VALUES(?,?,?)", ("monday", run_at, "running")); run_id = run.lastrowid
    try:
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        db.execute("INSERT INTO raw_board_snapshots(sync_run_id,board_id,captured_at,payload_json) VALUES(?,?,?,?)", (run_id, str(board["id"]), run_at, raw))
        rows=[]; names={}
        for item in items:
            day = (item.get("column_values") or {}).get("date_mm7h1mkp")
            if not day or date.fromisoformat(day).weekday() > 4: continue
            subs = item.get("subitems") or []
            for sub in subs:
                name = (sub.get("name") or "").strip(); vals=sub.get("column_values") or {}
                status = _status(vals.get("color_mm7jvcg0"))
                if not name: raise ValueError(f"blank crew member on {day}")
                rows.append((day,name,status,str(item.get("id") or ""),str(sub.get("id") or ""),sub.get("updated_at")))
                names[name]=1
        if not rows: raise ValueError("no weekday availability rows found")
        db.execute("DELETE FROM crew_availability_daily")
        for name in sorted(names):
            db.execute("INSERT INTO crew_members(source_person_id,name,active) VALUES(?,?,1) ON CONFLICT(source_person_id) DO UPDATE SET name=excluded.name,active=1", (f"name:{name}",name))
        for day in sorted({r[0] for r in rows}):
            count=sum(r[0]==day for r in rows)
            if count != 15: raise ValueError(f"{day} has {count} rows; expected 15")
        for day,name,status,parent,subid,updated in rows:
            member=db.execute("SELECT id FROM crew_members WHERE source_person_id=?",(f"name:{name}",)).fetchone()
            db.execute("INSERT INTO crew_availability_daily(date,crew_member_id,status,source_parent_id,source_subitem_id,source_updated_at,sync_run_id) VALUES(?,?,?,?,?,?,?)", (day,member[0],status,parent,subid,updated,run_id))
        db.execute("UPDATE sync_runs SET finished_at=?,status=?,records_read=? WHERE id=?",(_now(),"published",len(rows),run_id)); db.commit()
        return {"sync_run_id":run_id,"status":"published","dates":len({r[0] for r in rows}),"records":len(rows)}
    except Exception as exc:
        db.rollback(); db.execute("UPDATE sync_runs SET finished_at=?,status=?,error=? WHERE id=?",(_now(),"failed",str(exc),run_id)); db.commit(); raise
    finally: db.close()

def public_projection(month: str | None = None, db_path: Path = DEFAULT_DB, include_people: bool = False) -> dict:
    db=connect(db_path)
    where="WHERE a.date LIKE ?" if month else ""; args=(f"{month}-%",) if month else ()
    rows=db.execute(f"SELECT a.date,m.name,a.status FROM crew_availability_daily a JOIN crew_members m ON m.id=a.crew_member_id AND m.active=1 {where} ORDER BY a.date,m.name",args).fetchall()
    grouped={}
    for r in rows:
        d=grouped.setdefault(r["date"], {"date":r["date"],"counts":{}})
        d["counts"][r["status"]]=d["counts"].get(r["status"],0)+1
        if include_people: d.setdefault("people",[]).append({"name":r["name"],"status":r["status"]})
    for d in grouped.values():
        d["total"]=sum(d["counts"].values())
    latest=db.execute("SELECT finished_at,status FROM sync_runs ORDER BY id DESC LIMIT 1").fetchone(); db.close()
    return {"schema_version":"crew-availability.v1","source_state":"current" if latest and latest["status"]=="published" else "unavailable","synced_at":latest["finished_at"] if latest else None,"month":month,"days":list(grouped.values())}
