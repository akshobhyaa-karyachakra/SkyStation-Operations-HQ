#!/usr/bin/env python3
"""Validate published delivery snapshots without printing source identifiers."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from backend.delivery import build_delivery_projection

ROOT=Path(__file__).resolve().parent.parent

def main():
    p=argparse.ArgumentParser(); p.add_argument('--data-dir',type=Path,default=ROOT/'data'); p.add_argument('--start-date'); p.add_argument('--end-date'); a=p.parse_args()
    files=[a.data_dir/'flight_operations.snapshot.json',a.data_dir/'processing_qa.snapshot.json',a.data_dir/'report_submission.snapshot.json']
    if any(not f.exists() for f in files):
        print(json.dumps({'data_state':'unavailable','missing_snapshots':[f.name for f in files if not f.exists()]})); return 2
    try: snapshots=[json.loads(f.read_text()) for f in files]
    except (OSError,json.JSONDecodeError) as exc:
        print(json.dumps({'data_state':'needs_review','error':str(exc)})); return 1
    projection=build_delivery_projection(snapshots[0],snapshots[1],snapshots[2],a.start_date,a.end_date)
    summary={'schema_version':projection['schema_version'],'data_state':projection['data_state'],'period':projection['period'],'totals':projection['totals'],'quality':projection['quality'],'daily_days':len(projection['daily'])}
    print(json.dumps(summary,indent=2)); return 0 if projection['data_state'] in {'current','needs_review'} else 1

if __name__=='__main__': raise SystemExit(main())
