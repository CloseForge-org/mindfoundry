#!/usr/bin/env python3
"""NeMo Lodge RAG bridge.

Flow:
  1. Reads new questions posted in the Discord ``#nemotron-rag`` channel.
  2. Calls the local HotelSim retrieval API at ``http://127.0.0.1:8765/rag/query``
     to pull cited replicant memories, policy snippets, and routing.
  3. Calls **NVIDIA NIM** (OpenAI-compatible Chat Completions at
     ``https://integrate.api.nvidia.com/v1/chat/completions``) with a
     Nemotron-family model to *synthesize* a grounded answer over the
     retrieved citations.
  4. Runs the synthesized answer through ``hotel_sim.policy_gate.apply_gate``
     to redact PII (passwords, guest emails, phone numbers, payment data,
     passport/ID numbers, ``internal_notes``) before it is sent to Discord.
  5. Posts a NeMo Lodge RAG card with route + guardrail + citations to
     ``#nemotron-rag`` and an audit summary to ``#agent-audit-log``.

Environment variables:
  NVIDIA_NIM_API_KEY   NVIDIA NIM API key (``nvapi-...``). Required.
  NVIDIA_NIM_MODEL     NIM model id, e.g. ``nvidia/llama-3.3-nemotron-super-49b-v1.5``.
  NVIDIA_NIM_BASE      Override base URL (default ``https://integrate.api.nvidia.com/v1``).
  NVIDIA_NIM_DISABLE   If set to ``1`` the bridge falls back to the deterministic
                       citation-only renderer (useful for offline demos).

The bridge degrades gracefully: if NIM is unreachable or no API key is
configured, it returns the deterministic citations-only card so the demo
still works.
"""
from __future__ import annotations
import json, os, re, urllib.parse, urllib.request
from pathlib import Path
from discord_utils import channel_ids, read, send
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hotel_sim.live_ops import render_summary
from hotel_sim.policy_gate import gate_text

STATE = ROOT / 'reports' / 'nemotron-rag-bridge-state.json'
LOCAL_API = 'http://127.0.0.1:8765'
BOT_USER_ID = None

# --- NVIDIA NIM config -----------------------------------------------------
NIM_API_KEY = os.environ.get('NVIDIA_NIM_API_KEY', '').strip()
NIM_MODEL = os.environ.get('NVIDIA_NIM_MODEL', 'nvidia/llama-3.3-nemotron-super-49b-v1.5').strip()
NIM_BASE = os.environ.get('NVIDIA_NIM_BASE', 'https://integrate.api.nvidia.com/v1').rstrip('/')
NIM_DISABLE = os.environ.get('NVIDIA_NIM_DISABLE', '') == '1'


def nemotron_synthesize(question: str, retrieval: dict) -> dict:
    """Call NVIDIA NIM chat completions with the retrieved citations.

    Returns ``{'text': str, 'model': str, 'used_nim': bool, 'error': Optional[str]}``.
    On failure (no key, network error, non-200), falls back to a deterministic
    citation card and surfaces the error in the returned dict.
    """
    citations = retrieval.get('citations', []) or []
    route_list = retrieval.get('recommended_route', []) or []
    guardrail = retrieval.get('guardrail', '')
    intents = retrieval.get('detected_intents', []) or []

    def deterministic(reason: str = '') -> dict:
        route = ', '.join(f"{x.get('person')} ({x.get('role')})" for x in route_list) or 'No specific owner matched'
        lines = [
            f"**NeMo Lodge RAG (citations-only fallback)**",
            f"Question: {question}",
            f"Detected intents: `{', '.join(intents) or 'none'}`",
            f"Recommended route: {route}",
            f"Guardrail: {guardrail}",
            'Citations:',
        ]
        for c in citations[:4]:
            who = c.get('person') or c.get('role') or 'Source'
            src = c.get('source', 'memory')
            text = (c.get('text', '') or '')[:260].replace('\n', ' ')
            lines.append(f"- {who} · `{src}`: {text}")
        return {'text': '\n'.join(lines), 'model': 'deterministic', 'used_nim': False, 'error': reason or None}

    if NIM_DISABLE:
        return deterministic('NVIDIA_NIM_DISABLE=1')
    if not NIM_API_KEY:
        return deterministic('NVIDIA_NIM_API_KEY not set')

    # Build a compact citation block for the LLM. Keep it small — NIM rate-limits
    # large requests and the deterministic retrieval already did the hard work.
    cite_lines = []
    for i, c in enumerate(citations[:6], start=1):
        who = c.get('person') or c.get('role') or 'Source'
        src = c.get('source', 'memory')
        text = (c.get('text', '') or '').strip().replace('\n', ' ')
        cite_lines.append(f"[{i}] {who} ({src}): {text[:400]}")
    citation_block = '\n'.join(cite_lines) or '(no citations retrieved)'
    route_str = ', '.join(f"{x.get('person')} ({x.get('role')})" for x in route_list) or 'unassigned'

    system = (
        "You are MindFoundry, the NeMo Lodge hotel ops agent. "
        "Answer ONLY from the numbered citations below. "
        "If the citations do not cover the question, say so explicitly. "
        "Never invent guest names, passwords, phone numbers, emails, payment details, "
        "passport/ID numbers, or internal_notes. Cite sources inline as [1], [2], etc. "
        "Be concise: 4-8 short bullets max."
    )
    user_msg = (
        f"Question: {question}\n\n"
        f"Detected intents: {', '.join(intents) or 'none'}\n"
        f"Recommended route: {route_str}\n"
        f"Privacy guardrail: {guardrail}\n\n"
        f"Citations:\n{citation_block}\n\n"
        "Respond with: (a) a 1-line direct answer, (b) up to 6 bullets with [n] citations, "
        "(c) one-line escalation/route recommendation."
    )
    payload = {
        'model': NIM_MODEL,
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user_msg},
        ],
        'temperature': 0.2,
        'top_p': 0.9,
        'max_tokens': 600,
        'stream': False,
    }
    req = urllib.request.Request(
        NIM_BASE + '/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {NIM_API_KEY}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read().decode('utf-8', 'replace')
            body = json.loads(raw)
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode('utf-8', 'replace')[:400]
        except Exception:
            err_body = ''
        return deterministic(f'NIM HTTPError {e.code}: {err_body}')
    except Exception as e:
        return deterministic(f'NIM exception: {type(e).__name__}: {e}')

    try:
        text = body['choices'][0]['message']['content'].strip()
    except Exception:
        return deterministic(f'NIM unexpected response: {str(body)[:300]}')

    # Compose final card. The free-form Nemotron text comes first, then a
    # compact verifiable citation list for judges.
    header = [
        f"**NeMo Lodge RAG · Nemotron**",
        f"Question: {question}",
        f"Model: `{NIM_MODEL}`",
        f"Guardrail: {guardrail}",
        '',
        text,
        '',
        'Sources:',
    ]
    for line in cite_lines:
        header.append(f'- {line}')
    return {'text': '\n'.join(header), 'model': NIM_MODEL, 'used_nim': True, 'error': None}


def state(): return json.loads(STATE.read_text()) if STATE.exists() else {'answered': []}
def save(s): STATE.write_text(json.dumps(s, indent=2, ensure_ascii=False))

def api(path):
    with urllib.request.urlopen(LOCAL_API + path, timeout=10) as resp:
        return json.loads(resp.read().decode())

def clean_question(content: str) -> str:
    content=re.sub(r'<@!?\d+>', '', content).strip()
    return content or 'What is going on at NeMo Lodge right now?'

def answer(q: str) -> dict:
    """Build a gated RAG answer for ``q``.

    Returns ``{'text': str, 'used_nim': bool, 'model': str, 'redactions': list,
    'nim_error': Optional[str]}``. ``text`` is already policy-gated and safe to
    post publicly to Discord.
    """
    r = api('/rag/query?q=' + urllib.parse.quote(q) + '&limit=5')
    live = ''
    if any(x in q.lower() for x in ['what is happening', 'right now', 'live', 'status', 'summary', 'going on', 'urgent', 'open incidents']):
        live = render_summary() + '\n\n'
    synth = nemotron_synthesize(q, r)
    gated = gate_text(synth['text'], destination='public_discord')
    final_text = live + gated.text
    return {
        'text': final_text,
        'used_nim': synth.get('used_nim', False),
        'model': synth.get('model', 'deterministic'),
        'redactions': gated.redactions,
        'nim_error': synth.get('error'),
    }

def main():
    ids=channel_ids(); ch=ids['nemotron-rag']; audit=ids['agent-audit-log']
    s=state(); answered=set(s['answered'])
    msgs=read(ch, 20)
    sent=[]
    for m in reversed(msgs):
        mid=m['id']
        if mid in answered: continue
        author=m.get('author', {})
        if author.get('bot'): continue
        content=m.get('content','').strip()
        if not content: continue
        q=clean_question(content)
        try:
            res = answer(q)
            out = send(ch, res['text'])[0]
            audit_line = (
                f"RAG answered `{mid}` in #nemotron-rag. "
                f"NIM={res['used_nim']} model=`{res['model']}` "
                f"redactions={len(res['redactions'])} "
                f"err={res['nim_error'] or 'none'} "
                f"Query: {q[:240]}"
            )
            audit_msg = send(audit, audit_line)[0]
            sent.append({
                'question_id': mid,
                'answer_id': out['id'],
                'audit_id': audit_msg['id'],
                'used_nim': res['used_nim'],
                'model': res['model'],
                'redactions': len(res['redactions']),
                'nim_error': res['nim_error'],
            })
        except Exception as e:
            out=send(ch, f"RAG bridge error: `{type(e).__name__}: {e}`")[0]
            sent.append({'question_id': mid, 'error_id': out['id'], 'error': str(e)})
        answered.add(mid)
    s['answered']=sorted(answered); s.setdefault('sent_log', []).extend(sent); save(s)
    print(json.dumps({'answered_now': sent, 'answered_total': len(s['answered'])}, indent=2, ensure_ascii=False))

if __name__ == '__main__': main()
