#!/usr/bin/env python3
"""Publish Flight -> Processing/QA -> Report snapshots as one safe batch.

Each adapter reads MONDAY_API_TOKEN server-side. No token is printed or stored.
A failed adapter leaves existing published snapshots untouched.
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
ADAPTERS=(
    ("flight_operations", ROOT/"scripts/sync_flight_operations.py"),
    ("processing_qa", ROOT/"scripts/sync_processing_qa.py"),
    ("report_submission", ROOT/"scripts/sync_report_submission.py"),
)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output-dir',type=Path,default=ROOT/'data'); args=parser.parse_args()
    if not os.environ.get('MONDAY_API_TOKEN'):
        print('MONDAY_API_TOKEN is required; no request was made',file=sys.stderr); return 2
    args.output_dir.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='delivery-sync-',dir=args.output_dir) as td:
        temp=Path(td); results=[]
        for name,script in ADAPTERS:
            out=temp/f'{name}.snapshot.json'
            run=subprocess.run([sys.executable,str(script),'--output',str(out)],cwd=ROOT,env=os.environ.copy(),capture_output=True,text=True)
            if run.returncode:
                print(f'{name}: failed; publish aborted',file=sys.stderr)
                if run.stderr: print(run.stderr.strip(),file=sys.stderr)
                return run.returncode
            try:
                body=json.loads(out.read_text()); count=len(body.get('records',[]))
            except (OSError,json.JSONDecodeError):
                print(f'{name}: invalid snapshot; publish aborted',file=sys.stderr); return 1
            results.append({'domain':name,'records':count,'synced_at':body.get('synced_at')})
        manifest={'schema_version':'snapshot-manifest.v1','published_at':datetime.now(timezone.utc).isoformat(),'domains':results}
        for name,_ in ADAPTERS: shutil.copy2(temp/f'{name}.snapshot.json',args.output_dir/f'{name}.snapshot.json')
        (args.output_dir/'snapshot-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        print(json.dumps(manifest,indent=2)); return 0

if __name__=='__main__': raise SystemExit(main())
