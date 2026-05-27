#!/usr/bin/env python3
import json, sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'data'/'hotel_sim.sqlite'
OUT=ROOT/'data'/'messages'/'two_day_event_stream.jsonl'
con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open('w') as f:
    for r in con.execute('''SELECT m.*, i.type, i.severity, i.status, i.assigned_staff_id, i.room_id, i.reservation_id
                            FROM messages m JOIN incidents i USING(incident_id)
                            ORDER BY m.created_at, m.message_id'''):
        f.write(json.dumps(dict(r), ensure_ascii=False)+'\n')
print(OUT)
