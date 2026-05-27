#!/usr/bin/env python3
from __future__ import annotations
import json, sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'hotel_sim.sqlite'
DRIP = ROOT / 'reports' / 'discord-drip-state.json'
SEEDED = ROOT / 'reports' / 'discord-seeded-incidents.json'
MEMORIES = ROOT / 'data' / 'replicants' / 'discord_memories.jsonl'

TYPE_OWNER = {
    'maintenance': 'Ben Wu / Maintenance',
    'housekeeping': 'Grace Liu / Housekeeping',
    'lost_item': 'Grace Liu / Housekeeping',
    'cleaning_delay': 'Grace Liu / Housekeeping',
    'dirty_room': 'Grace Liu / Housekeeping',
    'front_desk': 'Leo Wang / Front Desk',
    'reservation_change': 'Iris Tsai / Reservations',
    'overbooking': 'Iris Tsai / Reservations',
    'refund': 'Annie Chang / Finance',
    'payment_dispute': 'Annie Chang / Finance',
    'billing': 'Annie Chang / Finance',
    'vip_request': 'Kevin Huang / Guest Experience',
    'noise_complaint': 'Kevin Huang / Guest Experience',
    'noise': 'Kevin Huang / Guest Experience',
    'access': 'Leo Wang / Front Desk + Ben Wu / Maintenance',
    'safety': 'Maya Chen / General Manager',
}

def rows(sql: str, params=()):
    con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
    try: return [dict(r) for r in con.execute(sql, params).fetchall()]
    finally: con.close()

def posted_ids() -> set[str]:
    ids=set()
    for p in (SEEDED, DRIP):
        if p.exists():
            try: ids.update(json.loads(p.read_text()).get('posted', []))
            except Exception: pass
    return ids

def recent_memories(limit=8) -> list[dict[str, Any]]:
    if not MEMORIES.exists(): return []
    out=[]
    for line in MEMORIES.read_text().splitlines():
        if line.strip():
            try: out.append(json.loads(line))
            except Exception: pass
    return out[-limit:]

def live_summary(limit=12) -> dict[str, Any]:
    ids=posted_ids()
    placeholders=','.join('?' for _ in ids) or "''"
    if ids:
        incidents=rows(f'''SELECT * FROM incidents WHERE incident_id IN ({placeholders}) ORDER BY created_at DESC LIMIT ?''', (*ids, limit))
    else:
        incidents=rows('''SELECT * FROM incidents WHERE status IN ("open","in_progress","escalated") ORDER BY created_at DESC LIMIT ?''', (limit,))
    sev=Counter(i['severity'] for i in incidents)
    typ=Counter(i['type'] for i in incidents)
    sensitive=sum(1 for i in incidents if i.get('contains_sensitive'))
    by_owner=defaultdict(list)
    for i in incidents:
        by_owner[TYPE_OWNER.get(i['type'], 'Leo Wang / Front Desk')].append(i['incident_id'])
    urgent=[i for i in incidents if i['severity'] in ('urgent','high') or i['status']=='escalated'][:6]
    return {
        'hotel': 'NeMo Lodge',
        'posted_incidents_seen': len(ids),
        'recent_incidents': incidents[:limit],
        'severity_counts': dict(sev),
        'type_counts': dict(typ),
        'sensitive_recent_count': sensitive,
        'owner_queue': dict(by_owner),
        'urgent_or_escalated': urgent,
        'recent_staff_memories': recent_memories(),
    }

def render_summary() -> str:
    s=live_summary()
    lines=[
        '**NeMo Lodge live ops summary**',
        f"Tracked Discord-posted incidents: {s['posted_incidents_seen']}",
        f"Recent severity mix: {', '.join(f'{k}={v}' for k,v in sorted(s['severity_counts'].items())) or 'none'}",
        f"Privacy-sensitive recent incidents: {s['sensitive_recent_count']} — summarize only, do not expose private fields.",
        '',
        '**Urgent/escalated queue**',
    ]
    if s['urgent_or_escalated']:
        for i in s['urgent_or_escalated'][:5]:
            owner=TYPE_OWNER.get(i['type'], 'Leo Wang / Front Desk')
            lines.append(f"- `{i['incident_id']}` {i['severity']} {i['type']} room `{i['room_id']}` → {owner}: {i['guest_visible_summary']}")
    else:
        lines.append('- No urgent/escalated recent incidents in the tracked set.')
    lines += ['', '**Owner queues**']
    for owner, incs in sorted(s['owner_queue'].items()):
        lines.append(f"- {owner}: {', '.join('`'+x+'`' for x in incs[:6])}")
    if s['recent_staff_memories']:
        lines += ['', '**Recent staff memory signals**']
        for m in s['recent_staff_memories'][-5:]:
            lines.append(f"- {m['person']} ({m['role']}): {m['text'][:180]}")
    return '\n'.join(lines)

if __name__ == '__main__': print(render_summary())
