#!/usr/bin/env python3
from pathlib import Path
import csv, json, secrets, string, os
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'workspace-imports'
SECURE=Path.home()/'.openclaw'/'secure'/'hotel-sim'
DOMAIN='snapdesign.tw'
STAFF=[
('maya.chen','Maya','Chen','陳美雅','General Manager'),('leo.wang','Leo','Wang','王立偉','Front Desk Manager'),('nina.lin','Nina','Lin','林妮娜','Night Auditor'),('grace.liu','Grace','Liu','劉佳蓉','Housekeeping Lead'),('ben.wu','Ben','Wu','吳柏翰','Maintenance Lead'),('iris.tsai','Iris','Tsai','蔡怡君','Revenue & Reservations'),('kevin.huang','Kevin','Huang','黃冠宇','Guest Experience Agent'),('annie.chang','Annie','Chang','張雅婷','Finance/Admin')]
GROUPS={'managers':['maya.chen','leo.wang','nina.lin','grace.liu','ben.wu','iris.tsai','kevin.huang','annie.chang'],'frontdesk':['leo.wang','nina.lin'],'housekeeping':['grace.liu'],'maintenance':['ben.wu'],'reservations':['iris.tsai'],'finance':['annie.chang'],'guest-experience':['kevin.huang']}
def pw():
 a=string.ascii_letters+string.digits+'!@#$%^&*';
 while True:
  p=''.join(secrets.choice(a) for _ in range(18))
  if any(c.islower() for c in p) and any(c.isupper() for c in p) and any(c.isdigit() for c in p): return p
OUT.mkdir(parents=True, exist_ok=True); SECURE.mkdir(parents=True, exist_ok=True)
passwords={f'{u}@{DOMAIN}':pw() for u,_,_,_,_ in STAFF}
with (OUT/'users-google-admin-import.csv').open('w',newline='') as f:
 w=csv.writer(f)
 w.writerow(['First Name [Required]','Last Name [Required]','Email Address [Required]','Password [Required]','Org Unit Path [Required]','Change Password at Next Sign-In'])
 for u,first,last,zh,role in STAFF:
  w.writerow([first,last,f'{u}@{DOMAIN}',passwords[f'{u}@{DOMAIN}'],'/', 'FALSE'])
with (OUT/'groups.json').open('w') as f:
 json.dump({f'{g}@{DOMAIN}':[f'{m}@{DOMAIN}' for m in members] for g,members in GROUPS.items()},f,indent=2)
secure=SECURE/'fake-staff-passwords-prepared.json'; secure.write_text(json.dumps(passwords,indent=2)); os.chmod(secure,0o600)
print(json.dumps({'csv':str(OUT/'users-google-admin-import.csv'),'groups':str(OUT/'groups.json'),'passwords':str(secure)},indent=2))
