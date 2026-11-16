"""Normalize manually verified collection records, without changing source PDFs."""
import collections,hashlib,json,re
from pathlib import Path
import fitz
root=Path(__file__).resolve().parents[2];folder=root/'research/foreign';path=folder/'resources.json';r=json.loads(path.read_text())
for x in r:
 if x['competition']=='IChO' and x['year']==2026 and x['status']=='located':
  x['status']='folder-resolved';x['notes']='Official folder resolved into individual question/solution PDF records in this catalog.'
 if x['competition']=='IChO' and x['year']==2024 and x['kind']=='solutions':x['notes']+=' Marked exam PDF contains questions, worked scoring content, and blank answer sheets; do not mistake trailing blank sheets for solutions.'
 if x['competition']=='USNCO' and x['kind']=='solutions'and x['status']=='download-failed':x['notes']+=' Supplementary volunteer annotations only; short answer key is already present in national Part I combined PDF.'
 if x['local_path']:
  p=root/x['local_path'];d=fitz.open(p);assert x['pages']==len(d);assert x['sha256']==hashlib.sha256(p.read_bytes()).hexdigest();x['identity_checked']='PDF page count, extracted title/body, expected exam part, source path';x['language']='en'
  if x['competition']=='USNCO':
   t=d[0].get_text();assert str(x['year'])in t;assert 'CHEMISTRY OLYMPIAD'in t.upper();x['identity_checked']+='; year and Chemistry Olympiad visible on cover'
  if x['competition']=='UKChO':
   t='\n'.join(p.get_text()for p in d);assert str(x['year'])in t;assert 'OLYMPIAD'in t.upper();x['identity_checked']+='; year and Olympiad visible in document'
for year in [2020,2021,2022]:
 r.append(dict(id=f'icho-{year}-practical-not-held',competition='IChO',year=year,stage='practical',kind='problems',title=f'IChO {year} practical exam not held',source_url='https://icho2026.uz/problems',landing_url='https://icho2026.uz/problems',authority='official',local_path=None,status='not-held',notes='Remote-access IChO edition; final competition consisted of theoretical examination only. Practical preparatory problems are distinct from an actual practical examination.',accessed_at='2026-11-16'))
# Alternate files remain catalogued with explicit duplicate relationships.
groups=collections.defaultdict(list)
for x in r:
 if x.get('sha256'):groups[x['sha256']].append(x)
for group in groups.values():
 if len(group)>1:
  for x in group[1:]:x['duplicate_of']=group[0]['id']
assert len({x['id']for x in r})==len(r)
path.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
# Produce deterministic extraction hints for each IChO PDF's printed Q/S/M headers.
hints=[]
for x in r:
 if x['status']!='downloaded'or x['competition']!='IChO':continue
 d=fitz.open(root/x['local_path']);h=[]
 for i,p in enumerate(d):
  t=p.get_text();m=re.search(r'\b([QSM])(\d+)[-–]1\b',t[:250])
  if m:h.append(dict(page=i+1,printed_header=m[0],question_number=int(m[2]),role='solutions'if m[1]in'SM'else'problems',title_hint=' '.join(t[:200].split())))
 hints.append(dict(resource_id=x['id'],pages=len(d),printed_section_starts=h))
(folder/'section-hints.json').write_text(json.dumps(hints,ensure_ascii=False,indent=2)+'\n')
print('records',len(r),'downloaded',sum(x['status']=='downloaded'for x in r),'unique PDFs',len(groups));print(collections.Counter((x['competition'],x['status'])for x in r))
