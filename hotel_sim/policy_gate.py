#!/usr/bin/env python3
from __future__ import annotations
import json, re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports' / 'policy-gate-events.jsonl'

PATTERNS = [
    ('password', re.compile(r'(?i)\b(password|passcode|temporary password|pwd)\b\s*[:=]?\s*\S+')),
    # Require separators or common card grouping so Discord snowflakes/role IDs are not
    # mistaken for credit cards. Pure 18-digit Discord IDs were causing noisy redactions.
    ('credit_card', re.compile(r'\b(?:\d{4}[ -]+\d{4}[ -]+\d{4}[ -]+\d{1,7}|(?:4\d{12}(?:\d{3})?|5[1-5]\d{14}|3[47]\d{13}))\b')),
    ('taiwan_phone', re.compile(r'\b(?:\+?886[- ]?)?0?9\d{2}[- ]?\d{3}[- ]?\d{3}\b')),
    ('email', re.compile(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', re.I)),
    ('passport_or_id', re.compile(r'(?i)\b(passport|national id|arc|id number|身分證|護照)\b\s*[:#：]?\s*[A-Z0-9-]{5,}')),
    ('internal_note', re.compile(r'(?i)\binternal_notes?\b\s*[:=：]?\s*[^\n]+')),
]

# HotelSim staff emails are allowed in routing answers. Everything else gets redacted.
ALLOW_EMAILS = {
    'maya.chen@snapdesign.tw','leo.wang@snapdesign.tw','nina.lin@snapdesign.tw','grace.liu@snapdesign.tw',
    'ben.wu@snapdesign.tw','iris.tsai@snapdesign.tw','kevin.huang@snapdesign.tw','annie.chang@snapdesign.tw',
}

ROLE_PERMISSIONS = {
    'public_discord': {'allow_staff_email': True, 'allow_guest_email': False, 'allow_phone': False, 'allow_payment': False, 'allow_password': False, 'allow_internal_notes': False},
    'finance_private': {'allow_staff_email': True, 'allow_guest_email': True, 'allow_phone': True, 'allow_payment': True, 'allow_password': False, 'allow_internal_notes': True},
    'manager_private': {'allow_staff_email': True, 'allow_guest_email': True, 'allow_phone': True, 'allow_payment': False, 'allow_password': False, 'allow_internal_notes': True},
}

@dataclass
class GateResult:
    allowed: bool
    text: str
    redactions: list[dict[str, str]]
    destination: str
    decision: str


def _redact_match(kind: str, text: str, dest: str) -> tuple[str, list[dict[str,str]]]:
    redactions=[]
    policy=ROLE_PERMISSIONS.get(dest, ROLE_PERMISSIONS['public_discord'])
    for name, rx in PATTERNS:
        def repl(m):
            raw=m.group(0)
            low=raw.lower()
            if name == 'email':
                email=raw.strip('.,;:()[]<>').lower()
                if policy['allow_staff_email'] and email in ALLOW_EMAILS: return raw
                if policy['allow_guest_email']: return raw
            if name == 'taiwan_phone' and policy['allow_phone']: return raw
            if name == 'credit_card' and policy['allow_payment']: return raw
            if name == 'password' and policy['allow_password']: return raw
            if name == 'internal_note' and policy['allow_internal_notes']: return raw
            redactions.append({'type': name, 'sample': raw[:24]})
            return f'[{name.upper()} REDACTED]'
        text=rx.sub(repl, text)
    return text, redactions


def gate_text(text: str, destination: str='public_discord') -> GateResult:
    redacted, redactions = _redact_match('all', text, destination)
    allowed = True
    decision = 'allow' if not redactions else 'allow_with_redactions'
    result=GateResult(allowed=allowed, text=redacted, redactions=redactions, destination=destination, decision=decision)
    REPORT.parent.mkdir(exist_ok=True)
    with REPORT.open('a') as f:
        f.write(json.dumps(asdict(result), ensure_ascii=False) + '\n')
    return result


def gate_payload(payload: dict[str, Any], destination: str='public_discord') -> dict[str, Any]:
    data=json.loads(json.dumps(payload, ensure_ascii=False))
    def walk(x):
        if isinstance(x, str): return gate_text(x, destination).text
        if isinstance(x, list): return [walk(v) for v in x]
        if isinstance(x, dict): return {k: walk(v) for k,v in x.items()}
        return x
    return walk(data)

if __name__ == '__main__':
    sample='Guest email jane@example.com phone 0912-345-678 password: Secret1234 internal_notes: do not show. Route to maya.chen@snapdesign.tw.'
    print(json.dumps(asdict(gate_text(sample)), indent=2, ensure_ascii=False))
