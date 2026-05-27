#!/usr/bin/env python3
from __future__ import annotations
import json, re, sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from hotel_sim.live_ops import render_summary

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'hotel_sim.sqlite'
REPORT = ROOT / 'reports' / 'workspace-provisioning.json'
POLICY_DIR = ROOT / 'data' / 'policies'
DISCORD_MEMORIES = ROOT / 'data' / 'replicants' / 'discord_memories.jsonl'

ROLE_TO_EMAIL = {
    'General Manager': 'maya.chen@snapdesign.tw',
    'Front Desk Manager': 'leo.wang@snapdesign.tw',
    'Night Auditor': 'nina.lin@snapdesign.tw',
    'Housekeeping Lead': 'grace.liu@snapdesign.tw',
    'Maintenance Lead': 'ben.wu@snapdesign.tw',
    'Revenue & Reservations': 'iris.tsai@snapdesign.tw',
    'Guest Experience Agent': 'kevin.huang@snapdesign.tw',
    'Finance/Admin': 'annie.chang@snapdesign.tw',
}

ROLE_TO_GROUP = {
    'General Manager': 'managers@snapdesign.tw',
    'Front Desk Manager': 'frontdesk@snapdesign.tw',
    'Night Auditor': 'frontdesk@snapdesign.tw',
    'Housekeeping Lead': 'housekeeping@snapdesign.tw',
    'Maintenance Lead': 'maintenance@snapdesign.tw',
    'Revenue & Reservations': 'reservations@snapdesign.tw',
    'Guest Experience Agent': 'guest-experience@snapdesign.tw',
    'Finance/Admin': 'finance@snapdesign.tw',
}

TYPE_KEYWORDS = {
    'maintenance': ['maintenance', 'ac', 'air conditioning', 'plumbing', 'lock', 'electricity', 'broken', 'repair', '維修', '冷氣', '水管', '門鎖'],
    'housekeeping': ['housekeeping', 'clean', 'dirty', 'linen', 'towel', 'lost item', 'cleaning', '清潔', '毛巾', '遺失'],
    'refund': ['refund', 'deposit', 'invoice', 'payment', 'charge', 'folio', '退款', '押金', '發票', '付款'],
    'reservation_change': ['reservation', 'date', 'extend', 'late checkout', 'early check in', 'room change', '入住', '退房', '改期', '延住'],
    'vip': ['vip', 'service recovery', 'amenity', 'complaint', 'angry', '貴賓', '客訴'],
    'privacy': ['privacy', 'passport', 'phone', 'email', 'credit card', 'id', 'personal data', '隱私', '護照', '電話', '信用卡'],
    'billing': ['billing', 'double charge', 'charged', 'invoice', 'folio', '扣款', '重複扣款', '帳單'],
    'noise': ['noise', 'loud', 'party', '吵', '噪音'],
    'safety': ['safety', 'smoke', 'burning', 'fire', '燒焦', '煙', '安全'],
    'access': ['access', 'key', 'door', 'lock', 'cannot enter', '進不去', '鑰匙', '門'],
}

ROUTE_HINTS = {
    'maintenance': 'Maintenance Lead',
    'housekeeping': 'Housekeeping Lead',
    'refund': 'Finance/Admin',
    'reservation_change': 'Revenue & Reservations',
    'vip': 'Guest Experience Agent',
    'privacy': 'General Manager',
    'billing': 'Finance/Admin',
    'noise': 'Guest Experience Agent',
    'safety': 'General Manager',
    'access': 'Front Desk Manager',
}

def rows(sql: str, params=()):
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute(sql, params).fetchall()]
    finally:
        con.close()

def load_workspace() -> dict[str, Any]:
    if not REPORT.exists():
        return {'provisioned': False}
    r = json.loads(REPORT.read_text())
    return {
        'provisioned': True,
        'users_created': sum(1 for x in r.get('users', []) if x.get('status') in ('created','exists')),
        'groups_created': sum(1 for x in r.get('groups', []) if x.get('group') and x.get('status') in ('created','exists')),
        'drives_created': sum(1 for x in r.get('drives_docs', []) if x.get('drive') and x.get('status') in ('created','exists')),
    }

def policy_snippets() -> list[dict[str, str]]:
    out=[]
    for f in sorted(POLICY_DIR.glob('*.md')):
        text=f.read_text()
        for para in [p.strip() for p in text.split('\n\n') if p.strip()]:
            out.append({'source': f.name, 'text': para[:900]})
    return out

def discord_memories() -> list[dict[str, Any]]:
    if not DISCORD_MEMORIES.exists(): return []
    out=[]
    for line in DISCORD_MEMORIES.read_text().splitlines():
        if not line.strip(): continue
        try: out.append(json.loads(line))
        except json.JSONDecodeError: continue
    return out

def build_replicants() -> list[dict[str, Any]]:
    staff = rows('SELECT * FROM staff ORDER BY staff_id')
    dm = discord_memories()
    reps=[]
    for s in staff:
        incidents = rows('''SELECT type, severity, status, contains_sensitive, guest_visible_summary, internal_notes
                            FROM incidents WHERE assigned_staff_id=? ORDER BY created_at DESC LIMIT 12''', (s['staff_id'],))
        type_counts={}
        for i in incidents:
            type_counts[i['type']] = type_counts.get(i['type'], 0) + 1
        memories = [
            {'kind': 'profile', 'source': 'sqlite.staff', 'text': f"{s['name']} / {s['zh_name']} is {s['role']} ({s['zh_role']}). Responsibilities: {s['responsibilities']}."},
            {'kind': 'behavior', 'source': 'sqlite.staff', 'text': f"Working style: {s['personality']}. Shift: {s['shift_start']}–{s['shift_end']}. Clearance: {s['clearance']}."},
            {'kind': 'workspace', 'source': 'google.workspace', 'text': f"Workspace identity: {ROLE_TO_EMAIL.get(s['role'])}; primary group: {ROLE_TO_GROUP.get(s['role'])}."},
        ]
        if type_counts:
            memories.append({'kind': 'experience', 'source': 'sqlite.incidents', 'text': f"Recent handled incident mix: {', '.join(f'{k}={v}' for k,v in sorted(type_counts.items()))}."})
        for i in incidents[:4]:
            memories.append({'kind': 'case', 'source': 'sqlite.incidents', 'text': f"Handled {i['severity']} {i['type']} case: {i['guest_visible_summary']} Sensitive={bool(i['contains_sensitive'])}."})
        for m in [x for x in dm if x.get('role') == s['role']][-8:]:
            memories.append({'kind': m.get('kind','discord_staff_memory'), 'source': m.get('source','discord'), 'text': m.get('text','')})
        reps.append({
            'staff_id': s['staff_id'],
            'name': s['name'],
            'zh_name': s['zh_name'],
            'role': s['role'],
            'email': ROLE_TO_EMAIL.get(s['role']),
            'group': ROLE_TO_GROUP.get(s['role']),
            'clearance': s['clearance'],
            'memory_count': len(memories),
            'memories': memories,
        })
    return reps

def tokenize(q: str) -> set[str]:
    return set(re.findall(r'[a-zA-Z0-9\u4e00-\u9fff]+', q.lower()))

def score_text(query_terms: set[str], text: str) -> int:
    t = text.lower()
    return sum(2 if term in t else 0 for term in query_terms) + sum(1 for term in query_terms if len(term) > 3 and any(w.startswith(term[:4]) for w in t.split()))

def classify_query(q: str) -> list[str]:
    low=q.lower(); hits=[]
    for kind, kws in TYPE_KEYWORDS.items():
        if any(k in low for k in kws): hits.append(kind)
    return hits or ['reservation_change' if 'checkout' in low or 'check' in low else 'vip']

def retrieve(q: str, limit: int = 8) -> dict[str, Any]:
    terms = tokenize(q)
    kinds = classify_query(q)
    wants_live = any(x in q.lower() for x in ['what is happening', 'right now', 'live', 'status', 'summary', 'going on', 'urgent', 'open incidents'])
    chunks=[]
    if wants_live:
        chunks.append({'score': 999, 'person': None, 'role': 'Live Ops', 'kind': 'live_ops_summary', 'source': 'sqlite+discord.reports', 'text': render_summary()})
    for rep in build_replicants():
        for m in rep['memories']:
            chunks.append({'score': score_text(terms, m['text']) + (3 if any(k.replace('_',' ') in m['text'].lower() for k in kinds) else 0), 'person': rep['name'], 'role': rep['role'], **m})
    for p in policy_snippets():
        chunks.append({'score': score_text(terms, p['text']) + (4 if any(k in p['text'].lower() for k in ['privacy','refund','routing','escalat']) else 0), 'person': None, 'role': 'Policy', 'kind': 'policy', **p})
    chunks=sorted(chunks, key=lambda x: x['score'], reverse=True)
    route_roles=[]
    for k in kinds:
        role=ROUTE_HINTS.get(k)
        if role and role not in route_roles: route_roles.append(role)
    if 'vip' in kinds and 'General Manager' not in route_roles: route_roles.append('General Manager')
    reps={r['role']:r for r in build_replicants()}
    answer = {
        'query': q,
        'detected_intents': kinds,
        'recommended_route': [{'role': role, 'person': reps.get(role,{}).get('name'), 'email': reps.get(role,{}).get('email'), 'why': f'Matched {role} ownership for {", ".join(kinds)}'} for role in route_roles],
        'guardrail': 'Retrieve policy and role memory before action. Do not reveal payment, ID, phone, email, or internal notes to guests unless the role and policy explicitly allow it.',
        'draft_next_step': 'Ask the assigned teammate for missing context, cite the policy source, then draft a guest-safe reply for human approval.',
        'citations': [{k:v for k,v in c.items() if k != 'score'} | {'score': c['score']} for c in chunks[:limit]],
    }
    return answer

def summary() -> dict[str, Any]:
    reps=build_replicants(); ws=load_workspace()
    return {'replicants': len(reps), 'memories': sum(r['memory_count'] for r in reps), 'workspace': ws, 'example_query': retrieve('How should we handle a late checkout request from a VIP guest?', 5)}

if __name__ == '__main__':
    print(json.dumps(summary(), ensure_ascii=False, indent=2))
