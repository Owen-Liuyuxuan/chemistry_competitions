"""Collect final papers from observed PDF links and a third-party image archive."""
from pathlib import Path
import requests,fitz,json,concurrent.futures
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parents[1]
def images():
 u='https://www.gk100.com/read_2528600252.htm';s=BeautifulSoup((R/'research/china/read_2528600252.htm.html').read_text(),'html.parser');article=s.select_one('article');sections={};section=None
 for el in article.find_all(['h3','b','img']):
  t=el.get_text(strip=True)
  if el.name=='h3' and t.startswith('二、'):break
  if el.name=='b' and '理论试题' in t:section='theory'
  if el.name=='b' and '实验试题' in t:section='practical'
  if el.name=='img' and section:sections.setdefault(section,[]).append(el['src'])
 rows=[]
 for stage,urls in sections.items():
  rid='ccho-2026-final-'+stage;folder=R/'originals/china'/rid;folder.mkdir(exist_ok=True)
  def fetch(pair):
   n,url=pair;p=folder/f'{n:02d}.png'
   if not p.exists():r=requests.get(url,timeout=40);r.raise_for_status();p.write_bytes(r.content)
   return p
  files=list(concurrent.futures.ThreadPoolExecutor(6).map(fetch,enumerate(urls,1)));d=fitz.open()
  for p in files:
   im=fitz.open(p);rect=im[0].rect;page=d.new_page(width=rect.width,height=rect.height);page.insert_image(rect,filename=str(p))
  path=folder.with_suffix('.pdf');d.save(path,deflate=True)
  rows.append(dict(id=rid,competition='CChO',year=2026,stage='决赛理论' if stage=='theory' else '决赛实验',kind='combined' if stage=='theory' else 'problems',title='2026 第40届中国化学奥林匹克 '+('决赛理论试题及参考答案' if stage=='theory' else '决赛实验试题'),source_url=u,landing_url=u,authority='高考100第三方转载，待与官方原件逐页核对',local_path=str(path.relative_to(R)),status='downloaded',image_based=True,pages=len(d),page_sources=urls,notes='页面图片按来源顺序汇编；理论中题卷与参考答案分开定位，实验答案来源标注待更新。'))
 return rows
if __name__=='__main__':
 rows=images();jobs=[('ccho-2024-final-theory-1',2024,'决赛理论第一场','problems','https://cdn.gaokzx.com/172994461523711.pdf'),('ccho-2025-final-theory-1',2025,'决赛理论第一场','combined','https://cdn.gaokzx.com/zixunzhan/第39届化学竞赛(决赛)第1场试题答案1761372347896.pdf'),('ccho-2025-final-practical',2025,'决赛实验','problems','https://cdn.zizzs.com/zixunzhan/2025年第39届全国中学生化学竞赛决赛实验试题1761451851938.pdf')]
 for rid,year,stage,kind,url in jobs:
  x=dict(id=rid,competition='CChO',year=year,stage=stage,kind=kind,title=f'{year} 中国化学奥林匹克 {stage}',source_url=url,landing_url=url,authority='自主选拔在线/北京高考在线转载',local_path=None,status='pending',notes='转载原件，官方性须据卷面核对。')
  try:
   res=requests.get(url,timeout=45);res.raise_for_status();d=fitz.open(stream=res.content,filetype='pdf');p=R/'originals/china'/f'{rid}.pdf';p.write_bytes(res.content);x.update(status='downloaded',local_path=str(p.relative_to(R)),pages=len(d))
  except Exception as e:x.update(status='fetch_failed',notes=str(e))
  rows.append(x)
 (R/'research/china/finals.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));print([(x['id'],x['status'],x.get('pages')) for x in rows])
