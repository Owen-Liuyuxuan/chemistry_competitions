"""Build provenance catalog and render original question/solution crops.

All crop coordinates use original PDF points and 1-based page numbers.
No solutions are generated. Topic labels are heuristic metadata, not expert review.
"""
from pathlib import Path
import collections,hashlib,json,re,unicodedata,fitz
R=Path(__file__).resolve().parents[1]
DATE='2026-11-16'
# Reuse a rendered crop only when its source bytes, page and geometry are unchanged.
previous={};old_catalog=R/'catalog/catalog.json'
if old_catalog.exists():
 old=json.loads(old_catalog.read_text());old_rs={r['id']:r for r in old['resources']}
 for q in old['questions']:
  for role in ['problem','solution']:
   b=q.get(role)
   if b:
    for seg in b['segments']:previous[seg['image']]=(old_rs[b['resource_id']]['sha256'],seg['page'],seg['clip'])

def read(p):return json.loads((R/p).read_text())
def write(p,data):
 p=R/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def normalized(text):return re.sub(r'\s+','',unicodedata.normalize('NFKC',text)).lower()
TAXONOMY={
'化学计量':['stoichiomet','molar mass','moles','hydration','mass percent','化学计量','摩尔','反应方程式'],
'气体与物态':['gases','gas law','partial pressure','STP','气体','蒸气压'],
'酸碱平衡':['acid','base','pH','pKa','buffer','酸碱','缓冲','水解'],
'氧化还原':['redox','oxidation','reduction','氧化还原','氧化数'],
'光谱与表征':['NMR','spectro','spectra','核磁','光谱','红外','质谱'],
'无机化学':['无机','元素','inorganic','halogen','oxide','metal','氟化','氯化','氧化物','硼','磷','砷','镓','铬','锗','碘','硒'],
'配位化学':['配位','配合物','coordination','ligand','complex','晶体场','过渡金属','螯合'],
'结构化学':['结构','晶体','晶胞','密堆积','点群','crystal','structure','symmetry','orbital','富勒烯','钙钛矿'],
'有机化学':['有机','organic','alkene','alkyne','aromatic','stereochem','carbonyl','羰基','亲核','亲电','碳正离子','卡宾'],
'有机合成':['合成','synthesis','synthetic','mechanism','反应机理','环化','重排','天然产物','环加成'],
'物理化学':['热力学','动力学','平衡','thermodynam','kinetic','equilibrium','enthalpy','entropy','gibbs','quantum','量子','薛定谔','蒸气压'],
'分析化学':['滴定','分析','titration','analytical','spectro','absorbance','chromatograph','核磁','nmr','定量','色谱','测定'],
'电化学':['电化学','electrochem','electrode','cellpotential','电极','电池','电解','nernst'],
'实验操作':['实验','laboratory','practical','滴定','操作','distill','分离','提纯','tlc'],
'生物化学':['生物','bio','dna','protein','enzyme','氨基酸','蛋白','酶','代谢'],
'材料化学':['材料','material','polymer','nanopart','纳米','高分子','半导体','催化','cataly'],
'化学工程':['化工','工程','processdesign','reactor','分离工艺','工艺','生产','装置','流程'],
'绿色化学':['绿色','环境','green','carboncapture','废水','环保','碳捕集','二氧化碳']}
COMP=[('CChO','中国化学奥林匹克','高中','初赛（省级赛）与全国决赛；按实际场次收录。'),('IChO','国际化学奥林匹克','高中','理论与实验，2020–2022远程届次无正式实验考试。'),('UKChO','英国化学奥林匹克','高中','RSC Round 1公开题卷与评分标准。'),('USNCO','美国化学奥林匹克','高中','全国赛I选择题、II笔答、III实验。'),('CNUL','全国大学生化学实验竞赛','本科','非每年举办，2021/2024/2026为第12/13/14届。'),('CNIC','全国大学生化学实验创新设计大赛','本科','开放项目型赛事，按章程、作品及任务资料索引。'),('CHEMDES','全国大学生化工设计竞赛','本科','相关化工类开放设计赛事，非统一闭卷化学试卷。'),('IChTo','国际青年化学家锦标赛','高中','研究与答辩型赛事；核对后确认为高中，列入国外相关赛事调研。')]
resources=[]
for p in ['research/china/resources.json','research/china/official.json','research/china/finals.json','research/foreign/resources.json','research/undergraduate/resources.json']:
 resources.extend(read(p))
rs={}
for r in resources:
 r['status']=r.get('status','source_only').replace('-','_');r['checked_at']=DATE
 if r.get('local_path'):
  p=R/r['local_path'];raw=p.read_bytes();r['sha256']=hashlib.sha256(raw).hexdigest();r['size_bytes']=len(raw)
  with fitz.open(p) as d:r['pages']=len(d)
 # Raw text previews are collection diagnostics, not public titles.
 r.pop('text_preview',None);rs[r['id']]=r
rs['ccho-2025-final-practical']['notes']+=' 下载原件只有印刷页2–3，缺少首张；不得视为完整试卷。'
rs['usnco-2022-national-i-combined']['notes']+=' 附件末页是2022 Local Section答案，与National题卷错配，已排除答案配对。'
for year in [2024]:
 for n in [1,2]:
  r=rs[f'ccho-{year}-juesai-{n}-guide'];r['authority']='第三方教学评析（非官方评分标准）';r['notes']='题目与第三方解析交错排版；不可称为官方答案。'
papers=read('research/china/selected_papers.json');hints=read('research/china/selected_hints.json')
# Foreign manifests already exclude blank answer booklets and repeated headings.
fh=[h for h in read('research/foreign/split_hints.json') if not h['resource_id'].startswith('usnco')]
fh.extend(read('research/foreign/usnco_split_hints.json'))
for h in fh:
 rid=h['resource_id'];r=rs[rid];pid=f"{r['competition'].lower()}-{r['year']}-{r['stage']}";h['paper_id']=pid
 if not any(p['id']==pid for p in papers):papers.append(dict(id=pid,competition=r['competition'],year=r['year'],stage=r['stage'],title=f"{r['year']} {r['competition']} · {r['stage']}",problem_resource_id=None,solution_resource_id=None,notes=''))
 p=next(p for p in papers if p['id']==pid)
 key='problem_resource_id' if h['role']=='problems' else 'solution_resource_id'
 # IChO2026 is published as original individual question files, tracked separately.
 if not p[key]:p[key]=rid
 if '-q' in rid:p['notes']='官方按单题发布；各题可打开其独立原件，下方下载提供整卷汇编。'
 hints.append(h)
for r in resources:
 if r['competition']=='CHEMDES' and r.get('local_path'):
  pid=r['id'];papers.append(dict(id=pid,competition=r['competition'],year=r['year'],stage='开放设计任务',title=r['title'],problem_resource_id=pid,solution_resource_id=None,notes=r['notes'],format='open_project'))
  hints.append(dict(resource_id=pid,paper_id=pid,role='problems',sections=[dict(number=1,title=r['title'].split('：')[-1],page=2,y=0)],notes='开放项目，不存在唯一标准答案。'))
# Attach canonical Chinese hints to their selected paper.
for h in hints:
 if 'paper_id' not in h:
  key='problem_resource_id' if h['role']=='problems' else 'solution_resource_id'
  matches=[p for p in papers if p[key]==h['resource_id']]
  assert len(matches)==1,(h['resource_id'],matches)
  h['paper_id']=matches[0]['id']
# IChO2026: produce a faithful full-exam compilation while retaining individual provenance.
for p in papers:
 if p['competition']=='IChO' and p['year']==2026:
  for role,key in [('problems','problem_resource_id'),('solutions','solution_resource_id')]:
   hs=sorted([h for h in hints if h['paper_id']==p['id'] and h['role']==role],key=lambda h:h['sections'][0]['number'])
   rid=p['id']+'-assembled-'+role;path=R/'originals/foreign'/f'{rid}.pdf'
   if not path.exists():
    d=fitz.open()
    for h in hs:
     with fitz.open(R/rs[h['resource_id']]['local_path']) as src:d.insert_pdf(src)
    d.save(path,deflate=True);d.close()
   rr=dict(id=rid,competition='IChO',year=2026,stage=p['stage'],kind=role,title=p['title']+' 整卷汇编',source_url=rs[hs[0]['resource_id']]['landing_url'],landing_url=rs[hs[0]['resource_id']]['landing_url'],authority='官方独立单题PDF顺序汇编',local_path=str(path.relative_to(R)),status='downloaded',notes='由官方单题文件按题号合并，单题原件与来源完整保留。',components=[h['resource_id'] for h in hs],checked_at=DATE)
   b=path.read_bytes();rr.update(sha256=hashlib.sha256(b).hexdigest(),size_bytes=len(b));rr['pages']=len(fitz.open(path));rs[rid]=rr;p[key]=rid
questions={};docs={};cache={};audit=[]
def doc(rid):
 if rid not in docs:docs[rid]=fitz.open(R/rs[rid]['local_path'])
 return docs[rid]
def segments_for(h,i):
 s=h['sections'][i];d=doc(h['resource_id'])
 if 'segments' in s:return s['segments']
 pn=s['page'];y=s['y'];endp=s.get('end_page');endy=s.get('end_y')
 if endp is None:
  if i+1<len(h['sections']):n=h['sections'][i+1];endp=n['page'];endy=n['y']
  else:endp=len(d);endy=d[-1].rect.height
 if endy is None:endy=d[endp-1].rect.height
 out=[]
 for page in range(pn,endp+1):
  r=d[page-1].rect;top=y if page==pn else 0;bottom=endy if page==endp else r.height
  if bottom-top>1:out.append(dict(page=page,clip=[0,top,r.width,bottom]))
 return out
for h in hints:
 print('render',h['resource_id'],h['role'],flush=True)
 rid=h['resource_id'];p=next(p for p in papers if p['id']==h['paper_id']);d=doc(rid)
 for i,s in enumerate(h['sections']):
  n=s['number'];qid=f"{p['id']}-q{n}";q=questions.setdefault(qid,dict(id=qid,paper_id=p['id'],competition=p['competition'],year=p['year'],stage=p['stage'],number=n,title='',tags=[],text_excerpt='',problem=None,solution=None,review_status='machine_checked',notes=p.get('notes',''),classification_method='keyword-assisted; unreviewed'))
  role='problem' if h['role']=='problems' else 'solution';out=[];text=[];ocr_used=False
  for j,seg in enumerate(segments_for(h,i)):
   pn=seg['page'];clip=fitz.Rect(seg['clip']);page=d[pn-1];assert 1<=pn<=len(d) and not clip.is_empty and (page.rect+(-0.02,-0.02,0.02,0.02)).contains(clip),(rid,n,seg);clip &= page.rect
   target=R/'derived'/rid/f'q{n:02d}-{role}-{j+1:02d}.webp';target.parent.mkdir(parents=True,exist_ok=True)
   spec=(rs[rid]['sha256'],pn,[round(v,3) for v in clip])
   if not target.exists() or previous.get(str(target.relative_to(R))) != spec:
    scale=min(2.2,1600/clip.width);pix=page.get_pixmap(matrix=fitz.Matrix(scale,scale),clip=clip)
    from PIL import Image
    im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);im.save(target,quality=90,method=4)
   out.append(dict(page=pn,clip=[round(v,3) for v in clip],image=str(target.relative_to(R)),sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
   t=page.get_text(clip=clip)
   if len(t.strip())<20:
    ocr_used=True
    if rid not in cache:
     cp=R/'catalog/pages'/f'{rid}.json';cache[rid]=read(str(cp.relative_to(R))) if cp.exists() else []
    if cache[rid]:t=' '.join(l['text'] for l in cache[rid][pn-1]['lines'] if clip.intersects(fitz.Rect(l['bbox'])))
   text.append(t)
  assert q[role] is None,(qid,role)
  q[role]=dict(resource_id=rid,segments=out,notes=h.get('notes',''))
  if role=='problem':
   title=unicodedata.normalize('NFKC',s.get('title',f'第{n}题'));title=re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])','',title)
   # OCR may misread formula glyphs: labels are supplementary and always link to original.
   title=re.sub(r'[(（][^()（）]*分[^()（）]*[)）]','',title);title=re.sub(r'\s+[0-9IS]+\s*分.*$','',title).strip();q['excerpt_method']='ocr' if ocr_used else 'native';q['title']=title.strip()[:110];full=' '.join(text);q['text_excerpt']=re.sub(r'\s+',' ',unicodedata.normalize('NFKC',full)).strip()[:420];norm=normalized(full+' '+title)
   q['tags']=[tag for tag,words in TAXONOMY.items() if any(normalized(w) in norm for w in words)]
   if not q['tags']:q['tags']=['综合化学']
   if p['competition']=='CHEMDES':q['tags']=['化学工程','过程设计','绿色化学'];q['format']='open_project'
   if h.get('notes'):q['notes']+=' '+h['notes']
questions=list(questions.values())
for q in questions:
 if q['id']=='ccho-2026-final-q4':q['title']='第4题 电化学 CO₂ 捕集与浓缩'
 if q['id']=='ccho-2026-final-q9':q['title']='第9题 有机氟试剂'
 if q['id']=='ccho-2026-preliminary-1-q7':q['title']='第7题 电化学 N₂ 还原'
assert all(q['problem'] for q in questions)
for p in papers:p['question_ids']=[q['id'] for q in questions if q['paper_id']==p['id']]
coverage=[]
for p in papers:
 qs=[q for q in questions if q['paper_id']==p['id']];paired=sum(bool(q['solution']) for q in qs);r=rs[p['problem_resource_id']]
 coverage.append(dict(competition=p['competition'],year=p['year'],stage=p['stage'],title=p['title'],status='project_based' if p.get('format')=='open_project' else 'downloaded',source_url=r['landing_url'],notes=f'{len(qs)}道/项已索引，{paired}道已关联参考答案。'+p['notes']))
# Retain research-only undergraduate competitions and explicit event status records.
for r in resources:
 if r['competition'] in ['CNUL','CNIC','IChTo'] or r['status'] in ['not_held','not_published','cancelled','not_annual','postponed']:
  coverage.append(dict(competition=r['competition'],year=r['year'],stage=r['stage'],title=r['title'],status=r['status'] if not r.get('local_path') else ('partial' if r['kind']=='report' else r['status']),notes=r.get('notes',''),source_url=r.get('landing_url') or r['source_url'],resource_id=r['id']))
coverage.extend([
 dict(competition='CChO',year=2020,stage='决赛实验',status='not_held',notes='中国化学会确认本届取消实验，改为两场综合理论考试。',source_url='https://www.chemsoc.org.cn/a3859.html'),
 dict(competition='CChO',year=2024,stage='决赛实验',status='missing',notes='官方赛事报道确认举办实验考试；本次未取得可靠完整题卷与答案。',source_url='https://www.chemsoc.org.cn/news/internal/a6170.html'),
 dict(competition='CChO',year=2025,stage='决赛实验原件完整性',status='partial',notes='已归档转载PDF印刷第2–3页，首张缺失；标准答案未取得。',source_url=rs['ccho-2025-final-practical']['source_url'])])
write('catalog/resources.json',list(rs.values()));write('catalog/papers.json',papers);write('catalog/questions.json',questions);write('catalog/coverage.json',coverage);write('catalog/taxonomy.json',TAXONOMY)
write('catalog/catalog.json',dict(updated_at=DATE,resources=list(rs.values()),papers=papers,questions=questions,coverage=coverage,competitions=[dict(id=id,name=name,audience=audience,description=description) for id,name,audience,description in COMP]))
for d in docs.values():d.close()
print(json.dumps(dict(resources=len(rs),papers=len(papers),questions=len(questions),paired=sum(bool(q['solution']) for q in questions),by_competition=dict(collections.Counter(q['competition'] for q in questions))),ensure_ascii=False))
