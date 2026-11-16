import concurrent.futures,hashlib,json,re
from pathlib import Path
import requests,fitz
root=Path(__file__).resolve().parents[2];folder=root/'research/foreign';out=root/'originals/foreign';records=json.loads((folder/'resources.json').read_text());new=[]
for a in json.load(open(folder/'pianeta-links.json')):
 u=a['url'];name=u.rsplit('/',1)[-1];edition=int(re.search(r'/(\d+)icho/',u)[1]);year=edition+1968;text=' '.join(a['text'].split()).lower()
 if 'preparatory'in name.lower() or 'prep_'in name.lower() or '_ITA.'in name or not any(x in text for x in ['exam','problems & solutions']):continue
 if year in [2021,2022]:continue
 if year==2020 and 'Problems-Solutions'not in name:continue
 if year==2026:continue
 stage='practical'if ('practical'in text or 'experiment'in text)else'theoretical';kind='solutions'if ('solution'in text and 'problems &'not in text)else('combined'if 'problems & solutions'in text else'problems');id=f'icho-{year}-{stage}-mirror-{kind}'
 new.append(dict(id=id,competition='IChO',year=year,stage=stage,kind=kind,title=f'IChO {year} {stage} {kind}',source_url=u,landing_url='https://www.pianetachimica.it/olimpiadi/test_olimpiadi.htm',authority='official-document-mirror',local_path=None,status='located',notes='Official English document hosted by independent PianetaChimica archive; document identity checked. Mirror is not the organizer.',accessed_at='2026-11-16'))
def dl(r):
 try:
  res=requests.get(r['source_url'],timeout=50);res.raise_for_status();assert res.content.startswith(b'%PDF');p=out/(r['id']+'.pdf');p.write_bytes(res.content);d=fitz.open(p);t='\n'.join(p.get_text()for p in d);r.update(status='downloaded',local_path=str(p.relative_to(root)),pages=len(d),sha256=hashlib.sha256(res.content).hexdigest(),bytes=len(res.content),identity_excerpt=t[:1200],text_characters=len(t));(folder/(p.stem+'.txt')).write_text(t);print(r['id'],len(d),flush=True)
 except Exception as e:r['notes']+=' '+str(e);r['status']='download-failed';print(r['id'],'ERR',str(e),flush=True)
 return r
with concurrent.futures.ThreadPoolExecutor(max_workers=5)as ex:new=list(ex.map(dl,new))
records.extend(new);(folder/'resources.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');print('TOTAL',len(records),'PDFs',sum(x['status']=='downloaded'for x in records))
