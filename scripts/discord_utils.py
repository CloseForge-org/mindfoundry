#!/usr/bin/env python3
from __future__ import annotations
import json, time, urllib.request, urllib.error
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hotel_sim.policy_gate import gate_text

CFG = Path.home() / '.openclaw' / 'openclaw.json'
CHANNEL_REPORT = ROOT / 'reports' / 'discord-secondoffice-channels.json'
API = 'https://discord.com/api/v10'


def bot_token() -> str:
    cfg = json.loads(CFG.read_text())
    return cfg['channels']['discord']['token']


def headers() -> dict[str, str]:
    return {
        'Authorization': f'Bot {bot_token()}',
        'Content-Type': 'application/json',
        'User-Agent': 'OpenClaw-HotelSim/1.0',
    }


def request(method: str, path: str, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(API + path, data=data, headers=headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            text = resp.read().decode()
            return json.loads(text) if text else None
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors='replace')
        raise RuntimeError(f'Discord API {method} {path} failed {e.code}: {msg}')


def channel_ids() -> dict[str, str]:
    report = json.loads(CHANNEL_REPORT.read_text())
    return {c['name']: c['id'] for c in report['channels']}


def send(channel_id: str, content: str, destination: str = 'public_discord', audit: bool = True):
    gated = gate_text(content, destination)
    content = gated.text
    # Discord hard limit is 2000 chars; keep chunks conservative.
    chunks=[]
    s=content
    while len(s) > 1900:
        cut=s.rfind('\n', 0, 1900)
        if cut < 500: cut=1900
        chunks.append(s[:cut]); s=s[cut:].lstrip()
    chunks.append(s)
    out=[]
    for chunk in chunks:
        out.append(request('POST', f'/channels/{channel_id}/messages', {'content': chunk}))
        time.sleep(0.7)
    if audit and gated.redactions:
        try:
            ids = channel_ids()
            audit_id = ids.get('agent-audit-log')
            if audit_id and audit_id != channel_id:
                kinds = ', '.join(sorted({r['type'] for r in gated.redactions}))
                request('POST', f'/channels/{audit_id}/messages', {'content': f'Policy gate: `{gated.decision}` for outbound Discord post. Redacted: {kinds}.'})
                time.sleep(0.7)
        except Exception:
            pass
    return out


def read(channel_id: str, limit: int = 10):
    return request('GET', f'/channels/{channel_id}/messages?limit={limit}')
