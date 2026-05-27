#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, random, sqlite3
from datetime import datetime, timedelta
from pathlib import Path

EN_FIRST = ['Alex','Jamie','Morgan','Taylor','Casey','Jordan','Riley','Avery','Sam','Chris','Dana','Robin','Cameron','Quinn','Drew','Skyler']
EN_LAST = ['Chen','Lin','Wang','Lee','Huang','Chang','Liu','Wu','Tsai','Yang','Khan','Patel','Smith','Garcia','Kim','Tanaka']
ZH_LAST = ['陳','林','王','李','黃','張','劉','吳','蔡','楊','周','許']
ZH_FIRST = ['怡君','家豪','志明','雅婷','俊傑','佳蓉','冠宇','思涵','柏翰','佩芬','子晴','承恩']
CHANNELS = ['email','line','phone','front_desk','discord_internal']
INCIDENT_TYPES = ['maintenance','housekeeping','front_desk','billing','noise','lost_item','access','reservation_change','vip_request','safety']
SEVERITIES = ['low','medium','high','urgent']
LANGS = ['en','zh-TW']
ROOM_TYPES = [('standard', 0.55), ('deluxe', 0.25), ('family', 0.10), ('suite', 0.07), ('accessible', 0.03)]

STAFF = [
    ('S001','Maya Chen','陳美雅','General Manager','總經理','final escalation, policy exceptions, safety, VIP recovery','calm, decisive, dislikes vague summaries'),
    ('S002','Leo Wang','王立偉','Front Desk Manager','櫃檯經理','check-in/out, guest complaints, room moves','fast responder, sometimes overpromises'),
    ('S003','Nina Lin','林妮娜','Night Auditor','夜班稽核','overnight incidents, payments log, after-hours triage','precise, cautious with money'),
    ('S004','Grace Liu','劉佳蓉','Housekeeping Lead','房務主管','room readiness, cleaning defects, linen, minibar checks','direct, terse, hates last-minute room swaps'),
    ('S005','Ben Wu','吳柏翰','Maintenance Lead','維修主管','AC, plumbing, locks, electrical, preventive maintenance','practical, asks for room number first'),
    ('S006','Iris Tsai','蔡怡君','Revenue & Reservations','訂房收益','booking changes, rates, overbooking, OTA issues','analytical, policy-bound'),
    ('S007','Kevin Huang','黃冠宇','Guest Experience Agent','賓客服務','VIPs, amenities, service recovery, bilingual replies','warm, creative, may miss privacy boundaries'),
    ('S008','Annie Chang','張雅婷','Finance/Admin','財務行政','refunds, deposits, invoices, tax IDs, privacy-sensitive records','meticulous, slow without complete evidence'),
]

ROUTE = {
    'maintenance': 'S005', 'housekeeping': 'S004', 'front_desk': 'S002', 'billing': 'S008',
    'noise': 'S002', 'lost_item': 'S004', 'access': 'S002', 'reservation_change': 'S006',
    'vip_request': 'S007', 'safety': 'S001'
}

def pick_weighted(items):
    r=random.random(); acc=0
    for item,w in items:
        acc+=w
        if r<=acc: return item
    return items[-1][0]

def connect(db: Path):
    con=sqlite3.connect(db)
    con.execute('PRAGMA foreign_keys=ON')
    return con

def schema(con):
    con.executescript('''
    DROP TABLE IF EXISTS audit_logs; DROP TABLE IF EXISTS messages; DROP TABLE IF EXISTS incidents;
    DROP TABLE IF EXISTS reservations; DROP TABLE IF EXISTS bookers; DROP TABLE IF EXISTS rooms; DROP TABLE IF EXISTS staff;
    CREATE TABLE rooms(room_id TEXT PRIMARY KEY, floor INTEGER, room_number TEXT, room_type TEXT, status TEXT, privacy_zone TEXT);
    CREATE TABLE bookers(booker_id TEXT PRIMARY KEY, full_name TEXT, zh_name TEXT, email TEXT, phone TEXT, language TEXT, loyalty_tier TEXT, privacy_level TEXT);
    CREATE TABLE reservations(reservation_id TEXT PRIMARY KEY, booker_id TEXT REFERENCES bookers, room_id TEXT REFERENCES rooms,
      check_in TEXT, check_out TEXT, status TEXT, source TEXT, adults INTEGER, children INTEGER, rate_twd INTEGER, internal_notes TEXT);
    CREATE TABLE staff(staff_id TEXT PRIMARY KEY, name TEXT, zh_name TEXT, role TEXT, zh_role TEXT, responsibilities TEXT, personality TEXT,
      shift_start TEXT, shift_end TEXT, clearance TEXT);
    CREATE TABLE incidents(incident_id TEXT PRIMARY KEY, reservation_id TEXT REFERENCES reservations, room_id TEXT REFERENCES rooms,
      type TEXT, severity TEXT, status TEXT, created_at TEXT, updated_at TEXT, assigned_staff_id TEXT REFERENCES staff,
      guest_visible_summary TEXT, internal_notes TEXT, contains_sensitive INTEGER DEFAULT 0);
    CREATE TABLE messages(message_id TEXT PRIMARY KEY, incident_id TEXT REFERENCES incidents, sender_type TEXT, sender_id TEXT,
      channel TEXT, language TEXT, created_at TEXT, body TEXT, sensitive INTEGER DEFAULT 0);
    CREATE TABLE audit_logs(audit_id TEXT PRIMARY KEY, created_at TEXT, actor TEXT, action TEXT, resource_type TEXT, resource_id TEXT, decision TEXT);
    CREATE INDEX idx_res_booker ON reservations(booker_id); CREATE INDEX idx_inc_status ON incidents(status, severity);
    CREATE INDEX idx_msg_time ON messages(created_at);
    ''')

def generate(out: Path, seed: int=42):
    random.seed(seed)
    out.parent.mkdir(parents=True, exist_ok=True)
    con=connect(out); schema(con)
    cur=con.cursor()
    # rooms
    rooms=[]
    for i in range(1,251):
        floor=(i-1)//25+2; num=f'{floor}{(i-1)%25+1:02d}'; rt=pick_weighted(ROOM_TYPES)
        status=random.choice(['vacant_clean','vacant_dirty','occupied','out_of_order']) if random.random()<0.08 else 'vacant_clean'
        rooms.append((f'R{i:03d}',floor,num,rt,status,'guest_stay'))
    cur.executemany('INSERT INTO rooms VALUES (?,?,?,?,?,?)', rooms)
    # staff
    shifts=['07:00','15:00','23:00']
    for idx,s in enumerate(STAFF):
        start=shifts[idx%3]; end={'07:00':'15:00','15:00':'23:00','23:00':'07:00'}[start]
        clearance='high' if s[0] in ['S001','S003','S008'] else 'standard'
        cur.execute('INSERT INTO staff VALUES (?,?,?,?,?,?,?,?,?,?)', (*s,start,end,clearance))
    # bookers
    bookers=[]
    for i in range(1,2501):
        en=f'{random.choice(EN_FIRST)} {random.choice(EN_LAST)}'; zh=f'{random.choice(ZH_LAST)}{random.choice(ZH_FIRST)}'
        lang=random.choices(LANGS, weights=[0.55,0.45])[0]
        tier=random.choices(['none','silver','gold','platinum'], weights=[.65,.2,.1,.05])[0]
        bookers.append((f'B{i:04d}',en,zh,f'guest{i:04d}@example.test',f'+886-900-{i:06d}',lang,tier,'pii'))
    cur.executemany('INSERT INTO bookers VALUES (?,?,?,?,?,?,?,?)', bookers)
    # reservations counts: remaining singles + repeaters
    counts=[1]*2050 + [2]*300 + [3]*100 + [4]*50
    assert len(counts)==2500 and sum(counts)==3150
    base=datetime(2026,6,1,0,0)
    rid=1; reservations=[]
    sources=['direct','booking.com','agoda','expedia','walk_in','corporate']
    for bi,cnt in enumerate(counts, start=1):
        last_start=base+timedelta(days=random.randint(-90,20))
        for j in range(cnt):
            nights=random.choices([1,2,3,4,5,7], weights=[.28,.27,.2,.12,.08,.05])[0]
            check_in=last_start+timedelta(days=random.randint(10,45)*j)
            room=random.choice(rooms)[0]
            status='checked_in' if datetime(2026,6,15) <= check_in <= datetime(2026,6,16) else random.choice(['confirmed','completed','cancelled'])
            note=random.choice(['','Prefers quiet room','Late arrival','Do not disclose stay details','Potential VIP','Prior complaint about noise'])
            reservations.append((f'RSV{rid:05d}',f'B{bi:04d}',room,check_in.isoformat(),(check_in+timedelta(days=nights)).isoformat(),status,random.choice(sources),random.randint(1,3),random.choice([0,0,1,2]),random.randint(2800,12800),note))
            rid+=1
    cur.executemany('INSERT INTO reservations VALUES (?,?,?,?,?,?,?,?,?,?,?)', reservations)
    # incidents + messages over 2 days
    sim_start=datetime(2026,6,15,6,0); incs=[]; msgs=[]; audits=[]
    for i in range(1,501):
        res=random.choice(reservations); typ=random.choice(INCIDENT_TYPES); sev=random.choices(SEVERITIES, weights=[.35,.42,.18,.05])[0]
        created=sim_start+timedelta(minutes=random.randint(0,48*60-1)); status=random.choices(['open','in_progress','resolved','escalated'], weights=[.34,.28,.32,.06])[0]
        staff=ROUTE[typ]; sensitive=1 if typ=='billing' or random.random()<.08 else 0
        en_body={
            'maintenance':'The AC is not cooling and the room feels hot.', 'housekeeping':'The room was not fully cleaned before check-in.',
            'front_desk':'Can I check in early or change rooms?', 'billing':'I think I was charged twice. Please check my card.',
            'noise':'The next room is very loud.', 'lost_item':'I left something in the room after checkout.',
            'access':'My key card does not work.', 'reservation_change':'I need to change my dates.',
            'vip_request':'Can you prepare a birthday amenity?', 'safety':'There is a strong burning smell near the hallway.'}[typ]
        zh_body={
            'maintenance':'房間冷氣不冷，現在很熱。', 'housekeeping':'入住前房間沒有打掃乾淨。',
            'front_desk':'我可以提早入住或換房嗎？', 'billing':'我好像被重複扣款了，請幫我確認。',
            'noise':'隔壁房間非常吵。', 'lost_item':'退房後我發現東西忘在房間。',
            'access':'我的房卡不能用。', 'reservation_change':'我需要更改入住日期。',
            'vip_request':'可以幫忙準備生日小禮物嗎？', 'safety':'走廊附近有很重的燒焦味。'}[typ]
        lang=random.choice(LANGS); body=en_body if lang=='en' else zh_body
        incs.append((f'INC{i:04d}',res[0],res[2],typ,sev,status,created.isoformat(),(created+timedelta(minutes=random.randint(5,240))).isoformat(),staff,body,('Contains payment/card issue' if sensitive else 'Operational context only'),sensitive))
        msgs.append((f'MSG{i:05d}',f'INC{i:04d}','guest',res[1],random.choice(CHANNELS),lang,created.isoformat(),body,sensitive))
        audits.append((f'AUD{i:05d}',created.isoformat(),'simulator','route_incident','incident',f'INC{i:04d}',f'assigned_to={staff}; expected_type={typ}; severity={sev}'))
    cur.executemany('INSERT INTO incidents VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', incs)
    cur.executemany('INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?)', msgs)
    cur.executemany('INSERT INTO audit_logs VALUES (?,?,?,?,?,?,?)', audits)
    con.commit(); con.close()
    return {'rooms':250,'bookers':2500,'reservations':3150,'staff':8,'incidents':500,'messages':500,'db':str(out)}

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--out', default='data/hotel_sim.sqlite'); ap.add_argument('--seed', type=int, default=42)
    args=ap.parse_args(); print(json.dumps(generate(Path(args.out), args.seed), indent=2))
