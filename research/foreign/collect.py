"""Download verified foreign contest links, retaining hashes and PDF identity evidence."""
import concurrent.futures,hashlib,json,re,time
from pathlib import Path
import requests,fitz
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'originals/foreign'; records=[]
def add(comp,year,stage,kind,url,landing,notes=''):
 records.append(dict(id=f'{comp.lower()}-{year}-{stage}-{kind}',competition=comp,year=year,stage=stage,kind=kind,title=f'{comp} {year} {stage} {kind}',source_url=url,landing_url=landing,authority='official',local_path=None,status='located',notes=notes,accessed_at='2026-11-16'))
acs='https://www.acs.org/education/olympiad/prepare-for-exams.html'
for u in json.load(open(ROOT/'research/foreign/acs-observed-urls.json')):
 y=int(re.search(r'/(20\d\d)[_-]',u)[1]);part=re.search(r'part[_-](iii|ii|i)(?:-|\.)',u)[1];kind='solutions' if ('solutions' in u or 'annotation' in u) else 'combined'
 add('USNCO',y,'national-'+part,kind,u,acs,'ACS exam PDF contains answer key / detailed solutions; Part I supplementary annotations are separate records.')
for y in [2020,2021]:
 add('USNCO',y,'national-iii','problems',acs,acs,'Official archive explicitly lists Part III as omitted; no practical exam held.')
 records[-1]['status']='not-held'
for y,ids in {2026:[546364,546365],2025:[539831,539829],2024:[533932,533929],2023:[525063,525062],2022:[518812,518813],2021:[515431,515423],2020:[515424,515426]}.items():
 for kind,n in zip(['problems','solutions'],ids):add('UKChO',y,'round-1',kind,f'https://edu.rsc.org/download?ac={n}','https://edu.rsc.org/uk-chemistry-olympiad/chemistry-olympiad-past-papers/1641.article','Official RSC Education download; document link observed on official archive.')
for a in json.load(open(ROOT/'research/foreign/icho2026problems-links.json')):
 if a['url'].endswith('.pdf'):
  y=int(re.search(r'20\d\d',a['text'])[0]);add('IChO',y,'theoretical','combined',a['url'],'https://icho2026.uz/problems','Past paper hosted by 2026 organizer; contents inspected to distinguish theory/practical/solutions.')
for a in json.load(open(ROOT/'research/foreign/icho2021problems-links.json')):
 if a['text'] in ['Official English version','Official English version with Solution']:
  add('IChO',2021,'theoretical-host','combined' if 'Solution' in a['text'] else 'problems',a['url'],'https://www.icho2021.org/problems/icho2021/')
for a in json.load(open(ROOT/'research/foreign/icho2026problems-links.json')):
 if 'Exam ' in a['text']:
  stage='practical' if 'Practical' in a['text'] else 'theoretical';kind='solutions' if 'Solutions' in a['text'] else 'problems';add('IChO',2026,stage,kind,a['url'],'https://icho2026.uz/problems','Official public Google Drive folder; direct PDF not yet resolved.')
def get(r):
 if r['status']=='not-held' or 'drive.google.com/drive/folders/' in r['source_url']:return r
 p=OUT/(r['id']+'.pdf')
 try:
  if not p.exists():
   response=requests.get(r['source_url'],timeout=50);response.raise_for_status()
   if not response.content.startswith(b'%PDF'):raise ValueError(f'Not PDF: {response.status_code}, {len(response.content)} bytes')
   p.write_bytes(response.content)
  d=fitz.open(p);text='\n'.join(x.get_text() for x in d)
  r.update(local_path=str(p.relative_to(ROOT)),status='downloaded',pages=len(d),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size,identity_excerpt=text[:1200],text_characters=len(text))
  (ROOT/'research/foreign'/(r['id']+'.txt')).write_text(text)
  print(r['id'],len(d),len(text),flush=True)
 except Exception as e:r.update(status='download-failed',notes=r['notes']+' '+str(e));print(r['id'],'ERROR',str(e),flush=True)
 return r
with concurrent.futures.ThreadPoolExecutor(max_workers=8)as ex:records=list(ex.map(get,records))
(ROOT/'research/foreign/resources.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
print('TOTAL',len(records),'DOWNLOADED',sum(x['status']=='downloaded'for x in records))
