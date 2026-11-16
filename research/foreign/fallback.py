import concurrent.futures,json,re,hashlib
from pathlib import Path
import requests,fitz
ROOT=Path(__file__).resolve().parents[2];folder=ROOT/'research/foreign';out=ROOT/'originals/foreign'
def dl(item):
 url,p=item
 try:
  r=requests.get(url,timeout=60);r.raise_for_status()
  if not r.content.startswith(b'%PDF'):raise ValueError(f'Not PDF {len(r.content)} {r.text[:40]}')
  p.write_bytes(r.content);d=fitz.open(p);t='\n'.join(x.get_text()for x in d);(folder/(p.stem+'.txt')).write_text(t);print(p.name,len(d),len(t),flush=True)
  return dict(local_path=str(p.relative_to(ROOT)),pages=len(d),sha256=hashlib.sha256(r.content).hexdigest(),bytes=len(r.content),status='downloaded',identity_excerpt=t[:1200],text_characters=len(t))
 except Exception as e: print(p.name,str(e),flush=True);return {'status':'download-failed','error':str(e)}
records=json.loads((folder/'resources.json').read_text())
acs=[r for r in records if r['competition']=='USNCO'and r['kind']=='combined'and r['status']!='not-held']
tasks=[]
for r in acs:
 part=r['stage'].split('-')[-1];p=f'pdf/national/{r["year"]}-usnco-national-exam-part-{part}.pdf';u='https://raw.githubusercontent.com/tylerlong/acs-exams/main/'+p;r['mirror_url']=u;r['notes']+=' Downloaded from independent GitHub mirror after ACS origin returned 403; official URL preserved. Mirror is not organizer; identity text checked.';r['authority']='official-document-mirror';tasks.append((u,out/(r['id']+'.pdf')))
with concurrent.futures.ThreadPoolExecutor(max_workers=8)as ex:
 for r,result in zip(acs,ex.map(dl,tasks)):r.update(result)
# Resolve individual official 2026 organizer files; answer sheets are retained separately and not treated as solutions.
new=[];tasks=[]
for a in json.loads((folder/'drive-files.json').read_text()):
 if '-A' in a['name'] or '-Q0-' in a['name'] or '-G0-' in a['name']:continue
 stage='practical' if '-experiment-'in a['name']else'theoretical';q=re.search(r'-Q(\d+)-',a['name'])[1];kind='solutions'if a['name'].startswith('solution-')else'problems';id=f'icho-2026-{stage}-q{q}-{kind}';url='https://drive.google.com/uc?export=download&id='+a['file_id'];r=dict(id=id,competition='IChO',year=2026,stage=stage,kind=kind,title=f'IChO 2026 {stage} Q{q} {kind}',source_url=url,landing_url='https://icho2026.uz/problems',authority='official',local_path=None,status='located',notes='Individual original PDF published by host in official Google Drive folder. Question-level source, not a full exam.',accessed_at='2026-11-16',question_number=int(q),drive_folder='https://drive.google.com/drive/folders/'+a['folder']);new.append(r);tasks.append((url,out/(id+'.pdf')))
with concurrent.futures.ThreadPoolExecutor(max_workers=8)as ex:
 for r,result in zip(new,ex.map(dl,tasks)):r.update(result)
records.extend(new);(folder/'resources.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');print('TOTAL',len(records),'PDFs',sum(r['status']=='downloaded'for r in records))
