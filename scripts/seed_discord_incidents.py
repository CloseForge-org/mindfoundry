#!/usr/bin/env python3
from __future__ import annotations
import json, sqlite3, hashlib
from pathlib import Path
from discord_utils import channel_ids, send

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'hotel_sim.sqlite'
STATE = ROOT / 'reports' / 'discord-seeded-incidents.json'

TYPE_CHANNEL = {
    'maintenance': 'maintenance',
    'housekeeping': 'housekeeping',
    'lost_item': 'housekeeping',
    'cleaning_delay': 'housekeeping',
    'dirty_room': 'housekeeping',
    'front_desk': 'front-desk',
    'reservation_change': 'reservations-revenue',
    'overbooking': 'reservations-revenue',
    'refund': 'finance-admin',
    'payment_dispute': 'finance-admin',
    'billing': 'finance-admin',
    'vip_request': 'guest-experience',
    'noise_complaint': 'guest-experience',
    'noise': 'guest-experience',
    'safety': 'manager-escalations',
    'access': 'front-desk',
}
ESCALATE_SEVERITIES = {'urgent', 'high'}

def rows(sql, params=()):
    con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
    try: return [dict(r) for r in con.execute(sql, params).fetchall()]
    finally: con.close()

def state():
    return json.loads(STATE.read_text()) if STATE.exists() else {'posted': []}

def save(s):
    STATE.write_text(json.dumps(s, indent=2, ensure_ascii=False))

def fmt(i):
    privacy = '⚠️ privacy-sensitive' if i['contains_sensitive'] else 'clean'
    return f"**{i['incident_id']} · {i['severity'].upper()} · {i['type']}**\nRoom `{i['room_id']}` · reservation `{i['reservation_id']}` · status `{i['status']}` · {privacy}\nGuest-visible: {i['guest_visible_summary']}\n\nRouting note: handle only within role permissions. Do not paste payment/ID/contact data into public channels."

def main():
    ids=channel_ids(); s=state(); posted=set(s['posted'])
    incidents=rows('''SELECT * FROM incidents
                      WHERE status IN ("open","in_progress","escalated")
                      ORDER BY CASE severity WHEN "urgent" THEN 1 WHEN "high" THEN 2 WHEN "medium" THEN 3 ELSE 4 END, created_at
                      LIMIT 16''')
    sent=[]
    for i in incidents:
        if i['incident_id'] in posted: continue
        ch=TYPE_CHANNEL.get(i['type'], 'front-desk')
        if ch not in ids: ch='nemo-lodge-lobby'
        msgs=send(ids[ch], fmt(i)); sent.append({'incident_id': i['incident_id'], 'channel': ch, 'message_id': msgs[0]['id']})
        if i['severity'] in ESCALATE_SEVERITIES or i['status']=='escalated':
            esc=send(ids['manager-escalations'], 'Escalation mirror:\n' + fmt(i))[0]
            sent.append({'incident_id': i['incident_id'], 'channel': 'manager-escalations', 'message_id': esc['id']})
        posted.add(i['incident_id'])
    s['posted']=sorted(posted); s.setdefault('sent_log', []).extend(sent); save(s)
    print(json.dumps({'sent': sent, 'posted_total': len(s['posted'])}, indent=2, ensure_ascii=False))

if __name__ == '__main__': main()
