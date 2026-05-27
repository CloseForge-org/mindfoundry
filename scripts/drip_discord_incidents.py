#!/usr/bin/env python3
from __future__ import annotations
import json, sqlite3
from pathlib import Path
from discord_utils import channel_ids, send

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'hotel_sim.sqlite'
STATE = ROOT / 'reports' / 'discord-drip-state.json'

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

def rows(sql, params=()):
    con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
    try: return [dict(r) for r in con.execute(sql, params).fetchall()]
    finally: con.close()

def load_state():
    if STATE.exists(): return json.loads(STATE.read_text())
    seeded=ROOT/'reports'/'discord-seeded-incidents.json'
    already=[]
    if seeded.exists(): already=json.loads(seeded.read_text()).get('posted', [])
    return {'posted': already, 'cursor_created_at': None, 'sent_log': []}

def save_state(s): STATE.write_text(json.dumps(s, indent=2, ensure_ascii=False))

def incident_message(i, msg=None):
    privacy = '⚠️ privacy-sensitive' if i['contains_sensitive'] else 'clean'
    body = msg['body'] if msg else i['guest_visible_summary']
    return f"**Live event · {i['incident_id']} · {i['severity'].upper()} · {i['type']}**\nRoom `{i['room_id']}` · reservation `{i['reservation_id']}` · status `{i['status']}` · {privacy}\nGuest says: {body}\n\nAgent instruction: route using policy + role memory. If sensitive, summarize only; do not expose private fields."

def staff_followup(i):
    if i['type'] in ('maintenance',): return 'Ben: I can check access constraints and estimate repair window. Need room access confirmation before dispatch.'
    if i['type'] in ('refund','payment_dispute'): return 'Annie: I will verify folio/refund policy privately. Do not post payment details in channel.'
    if i['type'] == 'billing': return 'Annie: I’ll verify billing privately against the folio. Channel reply should only mention next steps, not payment details.'
    if i['type'] == 'noise': return 'Kevin: I’ll handle guest recovery and coordinate a quiet-hours reminder without naming other guests.'
    if i['type'] == 'safety': return 'Maya: Treat as manager escalation. Confirm immediate safety facts first, then guest-safe instructions.'
    if i['type'] == 'access': return 'Leo: Front desk should verify identity privately, then coordinate access or maintenance if the lock is the issue.'
    if i['type'] in ('housekeeping','lost_item','cleaning_delay','dirty_room'): return 'Grace: I’ll check room board and assign cleaner. If guest-facing, keep reply simple and specific.'
    if i['severity'] in ('urgent','high'): return 'Maya: Please give me concise facts, policy source, guest-safe response, and escalation recommendation.'
    return 'Leo: Front desk will triage and confirm the guest-safe next step.'

def main(limit=3):
    ids=channel_ids(); s=load_state(); posted=set(s.get('posted', []))
    incidents=rows('''SELECT * FROM incidents ORDER BY created_at LIMIT 500''')
    sent=[]
    for i in incidents:
        if len(sent) >= limit: break
        if i['incident_id'] in posted: continue
        msg=rows('SELECT * FROM messages WHERE incident_id=? ORDER BY created_at LIMIT 1', (i['incident_id'],))
        ch=TYPE_CHANNEL.get(i['type'], 'front-desk')
        if ch not in ids: ch='nemo-lodge-lobby'
        out=send(ids[ch], incident_message(i, msg[0] if msg else None))[0]
        sent.append({'incident_id': i['incident_id'], 'channel': ch, 'message_id': out['id']})
        # Add a fake staff reply to make the channel feel alive.
        reply=send(ids[ch], staff_followup(i))[0]
        sent.append({'incident_id': i['incident_id'], 'channel': ch, 'message_id': reply['id'], 'kind':'staff_followup'})
        if i['status']=='escalated' or i['severity'] in ('urgent','high'):
            esc=send(ids['manager-escalations'], 'Escalation mirror:\n' + incident_message(i, msg[0] if msg else None))[0]
            sent.append({'incident_id': i['incident_id'], 'channel':'manager-escalations', 'message_id':esc['id']})
        posted.add(i['incident_id'])
    s['posted']=sorted(posted); s.setdefault('sent_log', []).extend(sent); save_state(s)
    print(json.dumps({'sent':sent,'posted_total':len(posted)}, indent=2, ensure_ascii=False))

if __name__ == '__main__': main()
