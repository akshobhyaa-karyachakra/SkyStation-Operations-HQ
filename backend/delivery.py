"""Cross-board delivery projection for Flight -> Processing/QA -> Reports.

Inputs are normalized work_item.v1 snapshots produced by the existing read-only
adapters. Joins use Activity Repository relation IDs only; names never join.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from datetime import date

DONE_FLIGHT={"Done"}; PARTIAL_FLIGHT={"Partial Completion"}
DONE_PROCESSING={"Done"}; PARTIAL_PROCESSING={"Partially Completed"}
DONE_REPORT={"Done"}; PARTIAL_REPORT={"Partial Completion"}


def _relation_ids(record):
    return {str(x.get("monday_item_id")) for x in record.get("activity_repository_relations", []) if x.get("monday_item_id")}

def _in_range(value,start,end):
    if not value: return False
    try: d=date.fromisoformat(value[:10])
    except ValueError: return False
    return (not start or d>=date.fromisoformat(start)) and (not end or d<=date.fromisoformat(end))

def _index(records):
    out=defaultdict(list)
    for r in records:
        for key in _relation_ids(r): out[key].append(r)
    return out

def build_delivery_projection(flight_snapshot:dict, processing_snapshot:dict, report_snapshot:dict, start_date:str|None=None, end_date:str|None=None)->dict:
    flights=flight_snapshot.get("records",[]); processing=processing_snapshot.get("records",[]); reports=report_snapshot.get("records",[])
    fi=_index(flights); pi=_index(processing); ri=_index(reports)
    keys=set(fi)|set(pi)|set(ri); daily=defaultdict(lambda: Counter()); quality=Counter(); chains=[]
    for key in sorted(keys):
        f=fi.get(key,[]); p=pi.get(key,[]); r=ri.get(key,[])
        anchor=next((x.get("scheduled_date") for x in f if x.get("scheduled_date")),None)
        if not _in_range(anchor,start_date,end_date): continue
        issues=[]
        if not f: issues.append("missing_flight")
        if len(f)>1: issues.append("duplicate_flight_relation")
        if len(p)>1: issues.append("duplicate_processing_relation")
        if len(r)>1: issues.append("duplicate_report_relation")
        flight=f[0] if f else None; proc=p[0] if p else None; report=r[0] if r else None
        flown=bool(flight and flight.get("status") in DONE_FLIGHT|PARTIAL_FLIGHT)
        processed=bool(proc and proc.get("status") in DONE_PROCESSING|PARTIAL_PROCESSING)
        submitted=bool(report and report.get("status") in DONE_REPORT|PARTIAL_REPORT)
        customer_ready=bool(report and report.get("delivery_status")=="Done" and submitted and not report.get("validation_issues"))
        if not p: issues.append("missing_processing")
        if not r: issues.append("missing_report")
        if flight and flight.get("data_state")=="needs_review": issues.extend(flight.get("validation_issues",[]))
        if proc and proc.get("data_state")=="needs_review": issues.extend(proc.get("validation_issues",[]))
        if report and report.get("data_state")=="needs_review": issues.extend(report.get("validation_issues",[]))
        state="needs_review" if issues else "current"
        quality[state]+=1
        daily[anchor].update({"planned":1,"flown":int(flown),"processed":int(processed),"submitted":int(submitted),"customer_ready":int(customer_ready)})
        chains.append({"date":anchor,"stages":{"planned":1,"flown":int(flown),"processed":int(processed),"submitted":int(submitted),"customer_ready":int(customer_ready)},"data_state":state,"quality_issue_count":len(set(issues))})
    totals=Counter()
    for c in chains: totals.update(c["stages"])
    return {"schema_version":"delivery-summary.v1","data_state":"needs_review" if quality["needs_review"] else "current","period":{"start_date":start_date,"end_date":end_date},"totals":dict(totals),"quality":{"chains":sum(quality.values()),"current":quality["current"],"needs_review":quality["needs_review"]},"daily":[{"date":d,**dict(v)} for d,v in sorted(daily.items())]}
