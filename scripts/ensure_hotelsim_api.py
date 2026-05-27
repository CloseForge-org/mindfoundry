#!/usr/bin/env python3
from __future__ import annotations
import subprocess, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PID = ROOT / 'reports' / 'hotelsim-api.pid'
LOG = ROOT / 'reports' / 'hotelsim-api.log'
URL = 'http://127.0.0.1:8765/health'

def healthy():
    try:
        with urllib.request.urlopen(URL, timeout=2) as r:
            return r.status == 200
    except Exception:
        return False

def main():
    if healthy():
        print('HotelSim API already healthy')
        return
    LOG.parent.mkdir(exist_ok=True)
    f=LOG.open('ab')
    proc=subprocess.Popen([sys.executable, str(ROOT/'api'/'server.py')], cwd=ROOT, stdout=f, stderr=f, start_new_session=True)
    PID.write_text(str(proc.pid))
    for _ in range(20):
        time.sleep(.25)
        if healthy():
            print(f'HotelSim API started pid={proc.pid}')
            return
    raise SystemExit('HotelSim API failed to become healthy')

if __name__ == '__main__': main()
