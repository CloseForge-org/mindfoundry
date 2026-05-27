#!/usr/bin/env python3
from __future__ import annotations
import json, sqlite3, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hotel_sim.replicants import build_replicants, retrieve, summary as replicant_summary

DB = ROOT / 'data' / 'hotel_sim.sqlite'
POLICY_DIR = ROOT / 'data' / 'policies'
UI_DIR = ROOT / 'ui'

def rows(sql, params=()):
    con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
    try:
        return [dict(r) for r in con.execute(sql, params).fetchall()]
    finally:
        con.close()

def one(sql, params=()):
    rs=rows(sql, params)
    return rs[0] if rs else None

class Handler(BaseHTTPRequestHandler):
    def send_json(self, obj, status=200):
        b=json.dumps(obj, ensure_ascii=False, indent=2).encode()
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
    def send_file(self, f: Path, content_type='text/html; charset=utf-8'):
        b=f.read_bytes()
        self.send_response(200); self.send_header('Content-Type', content_type); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        p=urllib.parse.urlparse(self.path); path=p.path; q=urllib.parse.parse_qs(p.query)
        try:
            if path in ('/', '/dashboard'):
                return self.send_file(UI_DIR / 'index.html')
            if path == '/health': return self.send_json({'ok': True, 'db': str(DB), 'exists': DB.exists()})
            if path == '/dashboard/summary':
                summary = {
                    'rooms': one('SELECT COUNT(*) AS c FROM rooms')['c'],
                    'bookers': one('SELECT COUNT(*) AS c FROM bookers')['c'],
                    'reservations': one('SELECT COUNT(*) AS c FROM reservations')['c'],
                    'staff': one('SELECT COUNT(*) AS c FROM staff')['c'],
                    'incidents': one('SELECT COUNT(*) AS c FROM incidents')['c'],
                    'open_incidents': one('SELECT COUNT(*) AS c FROM incidents WHERE status IN ("open","in_progress","escalated")')['c'],
                    'sensitive_incidents': one('SELECT COUNT(*) AS c FROM incidents WHERE contains_sensitive=1')['c'],
                    'zh_messages': one('SELECT COUNT(*) AS c FROM messages WHERE language="zh-TW"')['c'],
                    'en_messages': one('SELECT COUNT(*) AS c FROM messages WHERE language="en"')['c'],
                }
                return self.send_json(summary)
            if path == '/evaluations/baseline':
                f = ROOT / 'reports' / 'baseline-eval.json'
                if not f.exists(): return self.send_json({'error':'not_found'}, 404)
                return self.send_json(json.loads(f.read_text()).get('summary', {}))
            if path == '/replicants': return self.send_json(build_replicants())
            if path == '/replicants/summary': return self.send_json(replicant_summary())
            if path == '/rag/query':
                query=q.get('q',[''])[0].strip()
                if not query: return self.send_json({'error':'missing_query'}, 400)
                return self.send_json(retrieve(query, int(q.get('limit',['8'])[0])))
            if path == '/rooms': return self.send_json(rows('SELECT * FROM rooms ORDER BY room_id LIMIT ?', (int(q.get('limit',['50'])[0]),)))
            if path.startswith('/rooms/'):
                rid=path.split('/')[-1]; return self.send_json(one('SELECT * FROM rooms WHERE room_id=?',(rid,)) or {'error':'not_found'}, 200)
            if path == '/reservations/search':
                term=q.get('q',[''])[0]
                return self.send_json(rows('''SELECT r.*, b.full_name, b.zh_name, b.email, b.language FROM reservations r JOIN bookers b USING(booker_id)
                    WHERE r.reservation_id=? OR b.email LIKE ? OR b.full_name LIKE ? OR b.zh_name LIKE ? LIMIT 25''', (term, f'%{term}%', f'%{term}%', f'%{term}%')))
            if path.startswith('/guests/'):
                bid=path.split('/')[-1]
                return self.send_json({'booker': one('SELECT * FROM bookers WHERE booker_id=?',(bid,)), 'reservations': rows('SELECT * FROM reservations WHERE booker_id=? ORDER BY check_in',(bid,))})
            if path == '/incidents/open':
                return self.send_json(rows('SELECT * FROM incidents WHERE status IN ("open","in_progress","escalated") ORDER BY severity DESC, created_at LIMIT ?', (int(q.get('limit',['50'])[0]),)))
            if path.startswith('/incidents/'):
                iid=path.split('/')[-1]
                return self.send_json({'incident': one('SELECT * FROM incidents WHERE incident_id=?',(iid,)), 'messages': rows('SELECT * FROM messages WHERE incident_id=? ORDER BY created_at',(iid,))})
            if path == '/staff': return self.send_json(rows('SELECT * FROM staff ORDER BY staff_id'))
            if path == '/policies':
                return self.send_json([p.name for p in POLICY_DIR.glob('*.md')])
            if path.startswith('/policies/'):
                name=path.split('/')[-1]
                f=POLICY_DIR / name
                if not f.exists(): return self.send_json({'error':'not_found'}, 404)
                return self.send_json({'name':name, 'content':f.read_text()})
            return self.send_json({'error':'unknown_endpoint'},404)
        except Exception as e:
            return self.send_json({'error': type(e).__name__, 'message': str(e)},500)
    def log_message(self, fmt, *args):
        return

if __name__ == '__main__':
    import os
    port = int(os.environ.get('HOTELSIM_PORT', '8765'))
    print(f'[hotel-sim] retrieval API on http://127.0.0.1:{port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
