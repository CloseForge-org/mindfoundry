#!/usr/bin/env python3
from __future__ import annotations
import json, re, hashlib
from pathlib import Path
from discord_utils import channel_ids, read, send

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'replicants' / 'discord_memories.jsonl'
STATE = ROOT / 'reports' / 'replicant-updater-state.json'

CHANNEL_ROLE = {
    'front-desk': ('Front Desk Manager', 'Leo Wang'),
    'housekeeping': ('Housekeeping Lead', 'Grace Liu'),
    'maintenance': ('Maintenance Lead', 'Ben Wu'),
    'reservations-revenue': ('Revenue & Reservations', 'Iris Tsai'),
    'guest-experience': ('Guest Experience Agent', 'Kevin Huang'),
    'finance-admin': ('Finance/Admin', 'Annie Chang'),
    'manager-escalations': ('General Manager', 'Maya Chen'),
}
STAFF_NAME_ROLE = {
    'maya': ('General Manager', 'Maya Chen'),
    'leo': ('Front Desk Manager', 'Leo Wang'),
    'nina': ('Night Auditor', 'Nina Lin'),
    'grace': ('Housekeeping Lead', 'Grace Liu'),
    'ben': ('Maintenance Lead', 'Ben Wu'),
    'iris': ('Revenue & Reservations', 'Iris Tsai'),
    'kevin': ('Guest Experience Agent', 'Kevin Huang'),
    'annie': ('Finance/Admin', 'Annie Chang'),
}
SIGNAL_WORDS = re.compile(r'(?i)\b(policy|privacy|guest-safe|route|routing|escalat|refund|folio|payment|repair|access|clean|room board|dispatch|vip|late checkout|do not post|private|sensitive|confirm|assign|triage)\b')

def load_state(): return json.loads(STATE.read_text()) if STATE.exists() else {'seen': []}
def save_state(s): STATE.write_text(json.dumps(s, indent=2, ensure_ascii=False))

def classify(channel: str, content: str):
    low=content.lower()
    for key, role in STAFF_NAME_ROLE.items():
        if low.startswith(key + ':') or low.startswith(key + '：'):
            return role
    return CHANNEL_ROLE.get(channel, ('Hotel Ops', 'NeMo Lodge Team'))

def is_memory_worthy(content: str) -> bool:
    if len(content.strip()) < 30: return False
    if content.startswith('**Live event'): return False
    if content.startswith('Escalation mirror:'): return False
    return bool(SIGNAL_WORDS.search(content))

def make_memory(channel, msg):
    content=msg.get('content','').strip()
    role, person = classify(channel, content)
    text=re.sub(r'^\w+\s*[:：]\s*', '', content).strip()
    mid=msg['id']
    return {
        'memory_id': hashlib.sha1(f'{channel}:{mid}'.encode()).hexdigest()[:12],
        'discord_message_id': mid,
        'channel': channel,
        'person': person,
        'role': role,
        'source': f'discord:{channel}',
        'kind': 'discord_staff_memory',
        'text': text,
        'created_at': msg.get('timestamp'),
    }

def append_new(memories):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('a') as f:
        for m in memories:
            f.write(json.dumps(m, ensure_ascii=False) + '\n')

def main():
    ids=channel_ids(); s=load_state(); seen=set(s.get('seen', [])); new=[]
    for channel in CHANNEL_ROLE:
        if channel not in ids: continue
        for m in reversed(read(ids[channel], 25)):
            if m['id'] in seen: continue
            seen.add(m['id'])
            if m.get('author',{}).get('bot') and not re.match(r'(?i)^(maya|leo|nina|grace|ben|iris|kevin|annie)[:：]', m.get('content','')):
                continue
            content=m.get('content','')
            if not is_memory_worthy(content): continue
            new.append(make_memory(channel, m))
    if new:
        append_new(new)
        audit=ids.get('agent-audit-log')
        if audit:
            by_role={}
            for m in new: by_role[m['role']]=by_role.get(m['role'],0)+1
            send(audit, 'Replicant updater: added memories from Discord — ' + ', '.join(f'{k}: {v}' for k,v in sorted(by_role.items())), audit=False)
    s['seen']=sorted(seen); s.setdefault('updates', []).extend(new); save_state(s)
    print(json.dumps({'new_memories': len(new), 'roles': sorted({m['role'] for m in new}), 'total_seen': len(seen)}, indent=2, ensure_ascii=False))

if __name__ == '__main__': main()
