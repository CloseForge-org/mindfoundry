#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, secrets, string, sys, time
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

ROOT = Path(__file__).resolve().parents[1]
SECURE = Path.home() / '.openclaw' / 'secure' / 'hotel-sim'
CLIENT_SECRET = Path.home() / '.openclaw' / 'credentials' / 'google-client-secret.json'
TOKEN = SECURE / 'snapdesign-workspace-token.json'
SERVICE_ACCOUNT_KEY = SECURE / 'hotelsim-workspace-provisioner-scanflow-tw.json'
PASSWORDS = SECURE / 'fake-staff-passwords.json'
DOMAIN = 'snapdesign.tw'
SCOPES = [
    'https://www.googleapis.com/auth/admin.directory.user',
    'https://www.googleapis.com/auth/admin.directory.group',
    'https://www.googleapis.com/auth/admin.directory.group.member',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/spreadsheets',
]

STAFF = [
    ('maya.chen','Maya','Chen','陳美雅','General Manager','managers'),
    ('leo.wang','Leo','Wang','王立偉','Front Desk Manager','frontdesk'),
    ('nina.lin','Nina','Lin','林妮娜','Night Auditor','frontdesk'),
    ('grace.liu','Grace','Liu','劉佳蓉','Housekeeping Lead','housekeeping'),
    ('ben.wu','Ben','Wu','吳柏翰','Maintenance Lead','maintenance'),
    ('iris.tsai','Iris','Tsai','蔡怡君','Revenue & Reservations','reservations'),
    ('kevin.huang','Kevin','Huang','黃冠宇','Guest Experience Agent','guest-experience'),
    ('annie.chang','Annie','Chang','張雅婷','Finance/Admin','finance'),
]
GROUPS = {
    'managers': 'HotelSim Managers',
    'frontdesk': 'HotelSim Front Desk',
    'housekeeping': 'HotelSim Housekeeping',
    'maintenance': 'HotelSim Maintenance',
    'reservations': 'HotelSim Reservations',
    'finance': 'HotelSim Finance',
    'guest-experience': 'HotelSim Guest Experience',
}
DRIVES = {
    'HotelSim Policies': ['managers','frontdesk','housekeeping','maintenance','reservations','finance','guest-experience'],
    'HotelSim Front Desk': ['managers','frontdesk','guest-experience'],
    'HotelSim Housekeeping': ['managers','housekeeping','frontdesk'],
    'HotelSim Maintenance': ['managers','maintenance','frontdesk'],
    'HotelSim Finance': ['managers','finance'],
}
DOCS = {
    'HotelSim Policies': {
        'HotelSim Privacy Policy / 隱私規則': (ROOT/'data'/'policies'/'privacy.md').read_text(),
        'HotelSim Refund Policy / 退款政策': (ROOT/'data'/'policies'/'refunds.md').read_text(),
        'HotelSim Routing Rules / 分派規則': (ROOT/'data'/'policies'/'routing.md').read_text(),
    },
    'HotelSim Front Desk': {
        'Daily Arrivals and Departures / 每日入住退房': 'Synthetic front-desk workspace. Canonical data lives in SQLite.\nUse this as messy human-facing context only.',
    },
    'HotelSim Housekeeping': {
        'Room Readiness Board / 房務清潔狀態': 'Synthetic housekeeping board. No payment or private guest details should appear here.',
    },
    'HotelSim Maintenance': {
        'Maintenance Work Orders / 維修工單': 'Synthetic maintenance work orders. Include room number, issue, urgency, and access constraints only.',
    },
    'HotelSim Finance': {
        'Refunds Deposits Invoices / 退款押金發票': 'Restricted finance workspace. Contains privacy-sensitive concepts for permission testing.',
    },
}

def temp_password():
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
    while True:
        p = ''.join(secrets.choice(alphabet) for _ in range(18))
        if any(c.islower() for c in p) and any(c.isupper() for c in p) and any(c.isdigit() for c in p): return p

def creds():
    SECURE.mkdir(parents=True, exist_ok=True)
    c = None
    if TOKEN.exists():
        c = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if not c or not c.valid:
        if c and c.expired and c.refresh_token:
            c.refresh(Request())
        else:
            if not CLIENT_SECRET.exists(): raise SystemExit(f'Missing client secret: {CLIENT_SECRET}')
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
            c = flow.run_local_server(
                port=0,
                prompt='consent',
                login_hint=f'jarvis-hotelsim@{DOMAIN}',
                include_granted_scopes='true',
            )
        TOKEN.write_text(c.to_json())
        os.chmod(TOKEN, 0o600)
    return c

def delegated_creds(subject: str):
    if not SERVICE_ACCOUNT_KEY.exists():
        raise SystemExit(f'Missing service account key: {SERVICE_ACCOUNT_KEY}')
    c = service_account.Credentials.from_service_account_file(str(SERVICE_ACCOUNT_KEY), scopes=SCOPES)
    return c.with_subject(subject)

def service(name, version, c):
    return build(name, version, credentials=c, cache_discovery=False)

def exists(call, not_found=False):
    try: return call.execute()
    except HttpError as e:
        if e.resp.status == 404 and not_found is not False: return not_found
        raise

def create_users(admin):
    existing_passwords = json.loads(PASSWORDS.read_text()) if PASSWORDS.exists() else {}
    results=[]
    for username, first, last, zh, role, group in STAFF:
        email=f'{username}@{DOMAIN}'
        found = exists(admin.users().get(userKey=email), not_found=None)
        if found:
            results.append({'user': email, 'status': 'exists'})
            continue
        pw = temp_password(); existing_passwords[email] = pw
        body={
            'primaryEmail': email,
            'name': {'givenName': first, 'familyName': last, 'fullName': f'{first} {last}'},
            'password': pw,
            'changePasswordAtNextLogin': False,
            'orgUnitPath': '/',
            'relations': [{'value': role, 'type': 'custom', 'customType': 'HotelSim Role'}],
            'customSchemas': {},
        }
        admin.users().insert(body=body).execute()
        results.append({'user': email, 'status': 'created', 'role': role, 'zh_name': zh})
    PASSWORDS.write_text(json.dumps(existing_passwords, indent=2))
    os.chmod(PASSWORDS, 0o600)
    return results

def create_groups(admin):
    results=[]
    for local, name in GROUPS.items():
        email=f'{local}@{DOMAIN}'
        found = exists(admin.groups().get(groupKey=email), not_found=None)
        if not found:
            admin.groups().insert(body={'email': email, 'name': name, 'description': f'{name} sandbox group for AI hotel simulation'}).execute()
            results.append({'group': email, 'status': 'created'})
        else:
            results.append({'group': email, 'status': 'exists'})
    # memberships
    for username, first, last, zh, role, group in STAFF:
        g=f'{group}@{DOMAIN}'; u=f'{username}@{DOMAIN}'
        try:
            admin.members().insert(groupKey=g, body={'email': u, 'role':'MEMBER'}).execute()
            results.append({'member': u, 'group': g, 'status': 'added'})
        except HttpError as e:
            if e.resp.status in (400,409):
                results.append({'member': u, 'group': g, 'status': 'exists'})
            else: raise
    # managers group includes all leads/finance for broad access
    for username, *_ in STAFF:
        if username in ('maya.chen',): continue
        if username in ('leo.wang','nina.lin','grace.liu','ben.wu','iris.tsai','kevin.huang','annie.chang'):
            try: admin.members().insert(groupKey=f'managers@{DOMAIN}', body={'email': f'{username}@{DOMAIN}', 'role':'MEMBER'}).execute()
            except HttpError as e:
                if e.resp.status not in (400,409): raise
    return results

def get_drive_id(drive, name):
    page=None
    while True:
        resp=drive.drives().list(pageToken=page, pageSize=100).execute()
        for d in resp.get('drives',[]):
            if d.get('name') == name: return d['id']
        page=resp.get('nextPageToken')
        if not page: break
    return None

def create_doc(drive, docs, drive_id, name, content):
    # avoid duplicate by exact name in drive root-ish
    q = f"name='{name.replace(chr(39), chr(92)+chr(39))}' and trashed=false"
    files = drive.files().list(q=q, corpora='drive', driveId=drive_id, includeItemsFromAllDrives=True, supportsAllDrives=True, fields='files(id,name,mimeType)').execute().get('files', [])
    if files: return {'file': name, 'status': 'exists', 'id': files[0]['id']}
    meta={'name': name, 'mimeType':'application/vnd.google-apps.document', 'driveId': drive_id, 'parents':[drive_id]}
    f=drive.files().create(body=meta, supportsAllDrives=True, fields='id').execute()
    docs.documents().batchUpdate(documentId=f['id'], body={'requests':[{'insertText': {'location': {'index': 1}, 'text': content}}]}).execute()
    return {'file': name, 'status': 'created', 'id': f['id']}

def create_drives_and_docs(drive, docs):
    results=[]; drive_ids={}
    for name, groups in DRIVES.items():
        did=get_drive_id(drive, name)
        if not did:
            did=drive.drives().create(requestId=f'hotelsim-{name.lower().replace(" ","-")}-{int(time.time())}', body={'name':name}).execute()['id']
            results.append({'drive': name, 'status': 'created', 'id': did})
        else:
            results.append({'drive': name, 'status': 'exists', 'id': did})
        drive_ids[name]=did
        for g in groups:
            try:
                drive.permissions().create(fileId=did, supportsAllDrives=True, sendNotificationEmail=False, body={'type':'group','role':'reader' if name=='HotelSim Policies' else 'writer','emailAddress':f'{g}@{DOMAIN}'}).execute()
                results.append({'drive': name, 'permission': f'{g}@{DOMAIN}', 'status': 'added'})
            except HttpError as e:
                if e.resp.status in (400,403,409):
                    results.append({'drive': name, 'permission': f'{g}@{DOMAIN}', 'status': f'skipped:{e.resp.status}'})
                else: raise
    for dname, files in DOCS.items():
        for fname, content in files.items():
            results.append(create_doc(drive, docs, drive_ids[dname], fname, content))
    return results

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--skip-drive', action='store_true'); ap.add_argument('--dry-run', action='store_true'); ap.add_argument('--delegated-admin', default=f'jarvis-hotelsim@{DOMAIN}', help='Use domain-wide delegated service-account auth as this Workspace admin. Set empty string to use OAuth.')
    args=ap.parse_args()
    if args.dry_run:
        print(json.dumps({'users':[f'{s[0]}@{DOMAIN}' for s in STAFF], 'groups':[f'{g}@{DOMAIN}' for g in GROUPS], 'drives':list(DRIVES)}, indent=2)); return
    c=delegated_creds(args.delegated_admin) if args.delegated_admin else creds(); admin=service('admin','directory_v1',c); drive=service('drive','v3',c); docs=service('docs','v1',c)
    report={'users':create_users(admin), 'groups':create_groups(admin)}
    if not args.skip_drive: report['drives_docs']=create_drives_and_docs(drive, docs)
    out=ROOT/'reports'/'workspace-provisioning.json'; out.parent.mkdir(exist_ok=True); out.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({'ok': True, 'report': str(out), 'passwords': str(PASSWORDS)}, indent=2))

if __name__ == '__main__': main()
