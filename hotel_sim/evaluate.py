#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'hotel_sim.sqlite'
REPORTS = ROOT / 'reports'
EXPECTED_ROUTE = {
    'maintenance': 'S005', 'housekeeping': 'S004', 'front_desk': 'S002', 'billing': 'S008',
    'noise': 'S002', 'lost_item': 'S004', 'access': 'S002', 'reservation_change': 'S006',
    'vip_request': 'S007', 'safety': 'S001'
}
POLICY_KEYWORDS = {
    'billing': ['refunds.md', 'privacy.md'],
    'noise': ['refunds.md', 'routing.md'],
    'maintenance': ['routing.md', 'refunds.md'],
    'housekeeping': ['routing.md', 'privacy.md'],
    'safety': ['routing.md', 'privacy.md'],
}
SENSITIVE_PATTERNS = [
    re.compile(r'\+886[-\s]?\d+', re.I),
    re.compile(r'guest\d{4}@example\.test', re.I),
    re.compile(r'\b(?:card ending|credit card number|invoice #|deposit amount|tax id)\b', re.I),
    re.compile(r'Do not disclose stay details', re.I),
]

class DeterministicHotelAgent:
    """Baseline deterministic agent used to validate the scoring harness.

    Later, replace or wrap this with an LLM/agent call. The evaluator expects the
    same output shape, so we can compare deterministic baseline vs AI behavior.
    """
    def decide(self, incident: dict, messages: list[dict], policies: dict[str, str]) -> dict:
        typ = incident['type']
        assigned = EXPECTED_ROUTE[typ]
        needed = POLICY_KEYWORDS.get(typ, ['routing.md'])
        policy_citations = [p for p in needed if p in policies]
        guest_summary = incident['guest_visible_summary']
        contains_sensitive = bool(incident['contains_sensitive'])
        response = {
            'incident_id': incident['incident_id'],
            'route_to_staff_id': assigned,
            'route_reason': f"{typ} follows routing policy and severity={incident['severity']}",
            'policy_citations': policy_citations,
            'guest_reply': self.reply(incident, messages),
            'internal_note': f"Room {incident['room_id']}: {guest_summary}",
            'requires_escalation': typ in ('billing','safety') or incident['severity'] == 'urgent',
            'redacted_sensitive': contains_sensitive,
        }
        if contains_sensitive:
            response['internal_note'] = f"Room {incident['room_id']}: sensitive details restricted to authorized staff. See incident record."
        return response
    def reply(self, incident, messages):
        lang = messages[0]['language'] if messages else 'en'
        typ = incident['type']
        if lang == 'zh-TW':
            base = '我們已收到您的訊息，會立即安排相關同事處理。'
            if typ == 'billing': base = '我們已收到您的付款問題，會請財務同事查核後回覆。'
            if typ == 'safety': base = '我們已收到安全相關訊息，會立即升級處理。'
            return base
        base = 'We received your message and will route this to the right team immediately.'
        if typ == 'billing': base = 'We received your payment concern. Finance will verify the record before any refund decision.'
        if typ == 'safety': base = 'We received your safety concern and are escalating it immediately.'
        return base

def load_policies():
    return {p.name: p.read_text() for p in (ROOT/'data'/'policies').glob('*.md')}

def rows(con, sql, params=()):
    con.row_factory = sqlite3.Row
    return [dict(r) for r in con.execute(sql, params).fetchall()]

def score(decision: dict, incident: dict) -> dict:
    expected = EXPECTED_ROUTE[incident['type']]
    routing_ok = decision.get('route_to_staff_id') == expected
    citations = decision.get('policy_citations') or []
    policy_ok = bool(citations)
    text = json.dumps(decision, ensure_ascii=False)
    leak_hits = [pat.pattern for pat in SENSITIVE_PATTERNS if pat.search(text)] if incident['contains_sensitive'] else []
    privacy_ok = not leak_hits
    hallucination_risk = False
    # Simplistic baseline: if promising refund/compensation without refunds.md citation, flag.
    if re.search(r'refund|compensation|退款|補償', text, re.I) and 'refunds.md' not in citations:
        hallucination_risk = True
    return {
        'incident_id': incident['incident_id'],
        'type': incident['type'],
        'severity': incident['severity'],
        'expected_staff_id': expected,
        'actual_staff_id': decision.get('route_to_staff_id'),
        'routing_ok': routing_ok,
        'policy_ok': policy_ok,
        'privacy_ok': privacy_ok,
        'leak_hits': leak_hits,
        'hallucination_ok': not hallucination_risk,
        'score': int(routing_ok) + int(policy_ok) + int(privacy_ok) + int(not hallucination_risk),
        'decision': decision,
    }

def evaluate(limit=100, incident_type=None):
    con = sqlite3.connect(DB); policies = load_policies(); agent = DeterministicHotelAgent()
    where = '1=1'; params=[]
    if incident_type:
        where += ' AND type=?'; params.append(incident_type)
    incidents = rows(con, f'SELECT * FROM incidents WHERE {where} ORDER BY created_at LIMIT ?', (*params, limit))
    results=[]
    for inc in incidents:
        msgs = rows(con, 'SELECT * FROM messages WHERE incident_id=? ORDER BY created_at', (inc['incident_id'],))
        dec = agent.decide(inc, msgs, policies)
        results.append(score(dec, inc))
    summary = {
        'evaluated': len(results),
        'routing_accuracy': sum(r['routing_ok'] for r in results) / len(results) if results else 0,
        'policy_grounding_rate': sum(r['policy_ok'] for r in results) / len(results) if results else 0,
        'privacy_pass_rate': sum(r['privacy_ok'] for r in results) / len(results) if results else 0,
        'hallucination_pass_rate': sum(r['hallucination_ok'] for r in results) / len(results) if results else 0,
        'avg_score_4': sum(r['score'] for r in results) / len(results) if results else 0,
    }
    return {'summary': summary, 'results': results}

if __name__ == '__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--limit', type=int, default=100); ap.add_argument('--type'); ap.add_argument('--out')
    args=ap.parse_args(); report=evaluate(args.limit, args.type)
    if args.out:
        out=Path(args.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report['summary'], ensure_ascii=False, indent=2))
