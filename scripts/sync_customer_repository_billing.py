#!/usr/bin/env python3
"""Read-only Customer Repository subitem billing sync."""
from __future__ import annotations
import argparse, json, os, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

PARENT_BOARD = "5028043141"
SUBITEM_BOARD = "5028043142"
API_URL = "https://api.monday.com/v2"
API_VERSION = "2025-04"
BILLING_COLUMNS = ["status", "date_mm4xwgdq", "board_relation_mm4xbyad", "text_mm78aet7", "text_mm78xmh9", "text_mm78rn5r", "text_mm78bavn", "color_mm782zsj", "date_mm784dnr", "numeric_mm78f2z0", "numeric_mm78eycx", "numeric_mm78mwxt", "file_mm78rt45", "long_text_mm785y7"]
QUERY = """
query($board_id: ID!, $cursor: String) {
  boards(ids: [$board_id]) {
    id name updated_at
    items_page(limit: 500, cursor: $cursor) { cursor items {
      id name
      subitems { id name updated_at column_values(ids: ["status","date_mm4xwgdq","board_relation_mm4xbyad","text_mm78aet7","text_mm78xmh9","text_mm78rn5r","text_mm78bavn","color_mm782zsj","date_mm784dnr","numeric_mm78f2z0","numeric_mm78eycx","numeric_mm78mwxt","file_mm78rt45","long_text_mm785y7"]) { id text value type ... on BoardRelationValue { linked_items { id name board { id name } } } } }
    }
  }
}
"""

def request(token, cursor):
    body=json.dumps({"query":QUERY,"variables":{"board_id":PARENT_BOARD,"cursor":cursor}}).encode()
    req=urllib.request.Request(API_URL,data=body,headers={"Authorization":token,"Content-Type":"application/json","API-Version":API_VERSION})
    with urllib.request.urlopen(req,timeout=60) as r: payload=json.load(r)
    if payload.get("errors"): raise RuntimeError("Monday query failed")
    return payload

def fetch_all(token):
    parents=[]; cursor=None
    while True:
        boards=request(token,cursor).get("data",{}).get("boards",[])
        if len(boards)!=1: raise ValueError("expected one Customer Repository board")
        board=boards[0]; page=board["items_page"]; parents.extend(page.get("items",[])); cursor=page.get("cursor")
        if not cursor:return board,parents

def relations(c):
    return [{"monday_item_id":str(x["id"]),"name":x.get("name"),"board_id":str((x.get("board") or {}).get("id")),"board_name":(x.get("board") or {}).get("name")} for x in c.get("linked_items",[])]

def normalize(board,parents):
    records=[]; issues=[]
    for parent in parents:
        for item in parent.get("subitems") or []:
            c={x["id"]:x for x in item.get("column_values",[])}
            inv=relations(c.get("board_relation_mm4xbyad",{}))
            row={"source_board_id":SUBITEM_BOARD,"source_item_id":str(item["id"]),"customer_parent_id":str(parent["id"]),"customer_name":parent["name"],"name":item["name"],"source_updated_at":item.get("updated_at"),"installation_status":c.get("status",{}).get("text") or None,"activation_date":c.get("date_mm4xwgdq",{}).get("text") or None,"inventory_relations":inv,"sap_number":c.get("text_mm78aet7",{}).get("text") or None,"po_number":c.get("text_mm78xmh9",{}).get("text") or None,"invoice_number":c.get("text_mm78rn5r",{}).get("text") or None,"service_sheet_number":c.get("text_mm78bavn",{}).get("text") or None,"billing_status":c.get("color_mm782zsj",{}).get("text") or None,"billing_period":c.get("date_mm784dnr",{}).get("text") or None,"basic_billing_value":c.get("numeric_mm78f2z0",{}).get("text") or None,"gst_rate":c.get("numeric_mm78eycx",{}).get("text") or None,"gross_billing_value":c.get("numeric_mm78mwxt",{}).get("text") or None,"billing_evidence":c.get("file_mm78rt45",{}).get("text") or None,"billing_notes":c.get("long_text_mm785y7",{}).get("text") or None}
            row["data_state"]="current"; row["validation_issues"]=[]
            if any(r.get("board_id")!= "5028042389" for r in inv): row["validation_issues"].append("unexpected_inventory_relation_target")
            if row["billing_status"]=="Invoiced" and not row["invoice_number"]: row["validation_issues"].append("invoiced_without_invoice_number")
            if row["billing_status"] in {"Ready for invoice","Invoiced"} and not row["basic_billing_value"]: row["validation_issues"].append("billing_state_without_basic_value")
            if row["validation_issues"]: row["data_state"]="needs_review"
            records.append(row)
    return {"schema_version":"billing.v1","source":{"provider":"monday","parent_board_id":PARENT_BOARD,"subitem_board_id":SUBITEM_BOARD,"board_name":"Subitems of SkyStation Customer Repository","board_updated_at":board.get("updated_at")},"synced_at":datetime.now(timezone.utc).isoformat(),"records":records}

def validate(snapshot):
    rs=snapshot.get("records",[]); ids=[r.get("source_item_id") for r in rs]; return ([] if snapshot.get("schema_version")=="billing.v1" else ["unsupported schema"]) + (["duplicate source item IDs"] if len(ids)!=len(set(ids)) else [])

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",type=Path,default=Path("data/customer_repository_billing.snapshot.json")); a=ap.parse_args(); token=os.environ.get("MONDAY_API_TOKEN")
    if not token: print("MONDAY_API_TOKEN is required; no request was made",file=sys.stderr); return 2
    try:
        board,parents=fetch_all(token); snap=normalize(board,parents); errors=validate(snap)
        if errors:
            for e in errors: print("VALIDATION_ERROR: "+e,file=sys.stderr)
            return 1
        a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(snap,indent=2)+"\n"); print(f"wrote {len(snap['records'])} billing subitems to {a.output}"); return 0
    except Exception as e: print("SYNC_ERROR: "+str(e),file=sys.stderr); return 1

if __name__ == "__main__": raise SystemExit(main())
