import json
from pathlib import Path
from backend.crew_availability import ingest_board_payload, public_projection

ROOT=Path(__file__).resolve().parents[1]

def test_live_seed_publishes_15_rows_per_date(tmp_path):
    payload=json.loads((ROOT/'data/runtime/crew-monday.raw.json').read_text())
    result=ingest_board_payload(payload,tmp_path/'crew.sqlite3')
    assert result['status']=='published'
    assert result['records']==225
    projection=public_projection('2026-07',tmp_path/'crew.sqlite3')
    assert len(projection['days'])==2
    assert all(day['total']==15 for day in projection['days'])

def test_public_projection_omits_source_identifiers(tmp_path):
    payload=json.loads((ROOT/'data/runtime/crew-monday.raw.json').read_text())
    ingest_board_payload(payload,tmp_path/'crew.sqlite3')
    projection=public_projection('2026-06',tmp_path/'crew.sqlite3')
    serialized=json.dumps(projection)
    assert '5031561606' not in serialized
    assert 'source_parent_id' not in serialized
    assert 'source_subitem_id' not in serialized
