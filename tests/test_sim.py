#!/usr/bin/env python3
import sqlite3, subprocess, sys, time, urllib.request, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'hotel_sim.sqlite'

def test_counts():
    con=sqlite3.connect(DB)
    expected={'rooms':250,'bookers':2500,'reservations':3150,'staff':8,'incidents':500,'messages':500}
    for table,count in expected.items():
        got=con.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        assert got == count, (table, got, count)
    multi=con.execute('SELECT COUNT(*) FROM (SELECT booker_id, COUNT(*) c FROM reservations GROUP BY booker_id HAVING c=2)').fetchone()[0]
    assert multi == 300
    assert con.execute('SELECT COUNT(*) FROM (SELECT booker_id, COUNT(*) c FROM reservations GROUP BY booker_id HAVING c=3)').fetchone()[0] == 100
    assert con.execute('SELECT COUNT(*) FROM (SELECT booker_id, COUNT(*) c FROM reservations GROUP BY booker_id HAVING c=4)').fetchone()[0] == 50

def test_privacy_sensitive_incidents_exist():
    con=sqlite3.connect(DB)
    assert con.execute('SELECT COUNT(*) FROM incidents WHERE contains_sensitive=1').fetchone()[0] > 0
    assert con.execute('SELECT COUNT(*) FROM messages WHERE language="zh-TW"').fetchone()[0] > 0
    assert con.execute('SELECT COUNT(*) FROM messages WHERE language="en"').fetchone()[0] > 0

def test_api_health():
    proc=subprocess.Popen([sys.executable, str(ROOT/'api'/'server.py')], cwd=ROOT)
    try:
        time.sleep(0.5)
        data=json.load(urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=3))
        assert data['ok'] and data['exists']
        staff=json.load(urllib.request.urlopen('http://127.0.0.1:8765/staff', timeout=3))
        assert len(staff) == 8
    finally:
        proc.terminate(); proc.wait(timeout=3)

if __name__ == '__main__':
    test_counts(); test_privacy_sensitive_incidents_exist(); test_api_health(); print('ok')
