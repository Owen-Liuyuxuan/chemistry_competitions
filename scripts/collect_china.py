"""Archive official CChO announcements and their image pages, preserving source URLs."""
from pathlib import Path
import concurrent.futures, json, requests, fitz
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
SOURCES=[(2020,'a3811','a3821'),(2021,'a4486','a4496'),(2022,'a4867','a4883'),(2022,'a4905','a4918'),(2023,'a5452','a5459'),(2024,'a6093','a6107'),(2025,'a6890','a6899'),(2026,'a7491','a7499')]
def collect(job):
 year,slug,kind,slot=job
 url=f'https://www.chemsoc.org.cn/notice/{slug}.html'
 rid=f'ccho-{year}-official-{slot}-{kind}'
 out=dict(id=rid,competition='CChO',year=year,stage='初赛'+('第二场' if slot==2 else ''),kind=kind,title=f'{year} 中国化学奥林匹克 初赛'+('第二场' if slot==2 else '')+('试题' if kind=='problems' else '参考答案'),source_url=url,landing_url=url,authority='中国化学会官方',status='pending',local_path=None,notes='官网图像原件；PDF由原始图像无损汇编。')
 try:
  r=requests.get(url,timeout=35);r.raise_for_status();s=BeautifulSoup(r.content,'html.parser');body=s.select_one('.news-con');title=s.select_one('h1').get_text(' ',strip=True)
  if '试题' not in title or (kind=='solutions' and '答案' not in title):raise ValueError('announcement title mismatch: '+title)
  folder=ROOT/'originals/china'/rid;folder.mkdir(parents=True,exist_ok=True)
  (ROOT/'research/china'/f'{slug}.html').write_bytes(r.content)
  imgs=[requests.compat.urljoin(url,i['src']) for i in body.select('img[src]')]
  out['page_sources']=imgs
  if not imgs:
   out.update(status='source_only',notes='公告已核实，但未提取到图像附件。');return out
  doc=fitz.open()
  for n,imurl in enumerate(imgs,1):
   ir=requests.get(imurl,timeout=45);ir.raise_for_status();p=folder/f'{n:02d}.jpg';p.write_bytes(ir.content)
   im=fitz.open(stream=ir.content);rect=im[0].rect;page=doc.new_page(width=rect.width,height=rect.height);page.insert_image(rect,stream=ir.content)
  path=ROOT/'originals/china'/f'{rid}.pdf';doc.save(path,deflate=True);out.update(status='downloaded',local_path=str(path.relative_to(ROOT)),pages=len(doc),image_based=True)
 except Exception as e:out.update(status='fetch_failed',notes=str(e))
 return out
if __name__=='__main__':
 jobs=[]
 for year,q,a in SOURCES:
  slot=2 if q=='a4905' else 1
  for slug,kind in [(q,'problems'),(a,'solutions')]:jobs.append((year,slug,kind,slot))
 rows=list(concurrent.futures.ThreadPoolExecutor(6).map(collect,jobs));(ROOT/'research/china/official.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));print([(r['id'],r['status'],r.get('pages')) for r in rows])
