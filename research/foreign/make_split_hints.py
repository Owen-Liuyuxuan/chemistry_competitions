"""Generate audited, top-level question boundaries from printed document headings.

Coordinates are PDF points, top-left origin; page numbers are 1-based.
end_page/end_y are inclusive-page/exclusive-y crop ends and MUST be honored:
IChO question/answer booklets are interleaved with blank answer sheets.
"""
import json,re
from pathlib import Path
import fitz
ROOT=Path(__file__).resolve().parents[2];F=ROOT/'research/foreign';resources=json.loads((F/'resources.json').read_text());out=[]
def lines(p):
 return [(' '.join(s['text']for s in l['spans']).strip(),tuple(l['bbox'])) for b in p.get_text('dict')['blocks']for l in b.get('lines',[])]
def endpoint(d,p,y):
 if y<120 and p>1:return {'end_page':p-1,'end_y':round(d[p-2].rect.height,2)}
 return {'end_page':p,'end_y':round(max(0,y-3),2)}
def item(n,title,p,y,**kw):return dict(number=int(n),title=title.strip(),page=int(p),y=round(float(y),2),**kw)
def emit(r,role,sections,note=''):
 if not sections:return
 assert len({s['number']for s in sections})==len(sections),(r['id'],role)
 assert [s['number']for s in sections]==list(range(1,len(sections)+1)),(r['id'],role,sections)
 out.append(dict(resource_id=r['id'],role=role,sections=sections,notes=note))
def contiguous(d,starts,final_page=None):
 for i,s in enumerate(starts):
  if i+1<len(starts):s.update(endpoint(d,starts[i+1]['page'],starts[i+1]['y']))
  else:s.update(end_page=final_page or len(d),end_y=round(d[(final_page or len(d))-1].rect.height,2))
 return starts
# Primary sources only: alternative host records stay in catalog but don't create duplicate questions.
selected={'icho-2020-theoretical-combined','icho-2020-theoretical-mirror-combined','icho-2021-theoretical-host-problems','icho-2021-theoretical-host-combined','icho-2022-theoretical-combined'}
for r in resources:
 if r['status']!='downloaded':continue
 if r['competition']=='IChO':
  if not(r['id']in selected or (r['year']in[2023,2024,2025]and'-mirror-'in r['id'])or r['year']==2026):continue
  d=fitz.open(ROOT/r['local_path']);role='solutions'if r['kind']=='solutions'or r['id']in ['icho-2021-theoretical-host-combined','icho-2020-theoretical-mirror-combined']else'problems'
  if r['year']==2026:
   n=r['question_number'];text=d[0].get_text();ls=lines(d[0]);title=next((t for t,b in ls if re.match(r'^[TP]\d+\.',t)),f'{r["stage"]} Q{n}')
   # Single-question source uses original global question number, so emit without sequence assertion.
   out.append(dict(resource_id=r['id'],role=role,sections=[item(n,title,1,0,end_page=len(d),end_y=round(d[-1].rect.height,2))],notes='Organizer-supplied individual question PDF; all original pages retained.'))
  elif r['year']==2020:
   starts=[]
   if role=='problems':
    for i,p in enumerate(d):
     for t,b in lines(p):
      m=re.fullmatch(r'Problem\s+(\d+)',t)
      if m and i>6:starts.append(item(m[1],f'Problem {m[1]}',i+1,b[1]-3));break
    contiguous(d,starts,final_page=len(d)-1)
   else:
    problem_starts=[];sol_starts=[]
    for i,p in enumerate(d):
     for t,b in lines(p):
      m=re.fullmatch(r'Problem\s+(\d+)',t)
      if m and i>6:problem_starts.append((int(m[1]),i+1,b[1]))
      if t=='Solution:':sol_starts.append((i+1,b[1]))
    assert len(sol_starts)==9
    for i,(p,y)in enumerate(sol_starts):
     s=item(i+1,f'Problem {i+1} — official solution',p,y-3)
     if i<8:s.update(endpoint(d,problem_starts[i+1][1],problem_starts[i+1][2]))
     else:s.update(end_page=len(d)-1,end_y=round(d[-2].rect.height,2))
     starts.append(s)
   emit(r,role,starts)
  elif r['year']==2025:
   starts=[]
   for i,p in enumerate(d):
    ls=lines(p)
    for t,b in ls:
     m=re.match(r'^(\d+)\.\s+([A-Z].+)',t)
     if m and int(m[1])==len(starts)+1 and b[1]<300 and ('total'in p.get_text()[:600].lower()or r['stage']=='practical'):
      starts.append(item(m[1],m[2],i+1,max(0,b[1]-4)));break
   expected=3 if r['stage']=='practical'else 9;assert len(starts)==expected,(r['id'],starts)
   emit(r,role,contiguous(d,starts))
  else:
   # Qn, Sn or Mn printed headers define contiguous sections; An denotes blank answer booklet.
   prefix='M'if r['year']==2022 and role=='solutions'else('S'if r['year']==2023 and role=='solutions'else'Q')
   roles=[('problems','Q'),('solutions','M')]if r['year']==2022 else[(role,prefix)]
   for rr,pre in roles:
    sections=[]
    for i,p in enumerate(d):
     t=p.get_text();m=re.search(r'\b'+pre+r'(\d+)[-–]1\b',t[:250])
     if not m:continue
     n=int(m[1]);end=i
     for j in range(i+1,len(d)):
      hh=d[j].get_text()[:250]
      if re.search(r'\b'+pre+str(n)+r'[-–]\d+\b',hh):end=j
      else:break
     ls=t.splitlines();idx=next((k for k,s in enumerate(ls)if m[0]in s),0);title=' '.join(ls[idx+2:idx+5]);title=re.split(r'\d+%|Question|Points|Score',title)[0].strip()
     sections.append(item(n,title or f'Problem {n}',i+1,0,end_page=end+1,end_y=round(d[end].rect.height,2)))
    note='Printed section headers; excludes interleaved blank answer booklets.'
    if rr=='solutions'and r['year']in[2021,2024]:note+=' Solutions are embedded in the question text; this slice is an annotated original, not answer-only.'
    emit(r,rr,sections,note)
 elif r['competition']=='UKChO':
  d=fitz.open(ROOT/r['local_path']);sections=[]
  for i,p in enumerate(d):
   for t,b in lines(p):
    m=re.match(r'^Q?(\d+)\.?\s+This question is about\s+(.+)',t,re.I)
    if m:sections.append(item(m[1],m[2],i+1,b[1]-4));break
    mt=re.match(r'^This question is about\s+(.+)',t,re.I)
    if mt:
     mm=next((re.match(r'^(\d+)\.$',tt) for tt,bb in lines(p) if abs(bb[1]-b[1])<5 and bb[0]<75 and re.match(r'^(\d+)\.$',tt)),None)
     if mm:sections.append(item(mm[1],mt[1],i+1,b[1]-5));break
  expected=5 if r['year']in[2023,2024,2026]else 6;assert len(sections)==expected,(r['id'],sections)
  final_page={2020:14,2021:14,2022:15,2023:16,2024:15,2025:13,2026:14}[r['year']]if r['kind']=='problems'else len(d)
  emit(r,r['kind'],contiguous(d,sections,final_page),'Excludes cover, constants/periodic table and acknowledgements; full exam retains shared reference material.')
 elif r['competition']=='USNCO'and r['stage']=='national-ii':
  d=fitz.open(ROOT/r['local_path']);problems=[];solutions=[];solution_page=next(i+1 for i,p in enumerate(d)if re.search(r'USNCO\s+Part\s+2\s+SOLUTIONS',p.get_text(),re.I))
  if r['year']>=2022:
   for i,p in enumerate(d):
    if i+1>=solution_page:break
    for t,b in lines(p):
     m=re.match(r'Question\s+(\d+)\s+\(page\s+1\s+of',t,re.I)
     if m:problems.append(item(m[1],f'National II Q{m[1]}',i+1,b[1]-4));break
   # Last q ends at its last numbered question page; removes intentional blank pages before solutions.
   last_qpage=max(i+1 for i,p in enumerate(d)if i+1<solution_page and re.search(r'Question\s+8\s+\(page',p.get_text()))
  else:
   for i,p in enumerate(d):
    if i+1>=solution_page:break
    for t,b in lines(p):
     m=re.match(r'^(\d+)\.\s*\[\d+%\]',t)
     if m:problems.append(item(m[1],f'National II Q{m[1]}',i+1,b[1]-4))
   last_qpage=solution_page-1
  for i,p in enumerate(d):
   if i+1<solution_page:continue
   for t,b in lines(p):
    m=re.match(r'^([1-8])\.\s*(?:a[.\)]|$)',t)
    if m and b[0]<90 and int(m[1])==len(solutions)+1:solutions.append(item(m[1],f'National II Q{m[1]} — official solution',i+1,b[1]-4));break
  assert len(problems)==len(solutions)==8,(r['id'],problems,solutions)
  emit(r,'problems',contiguous(d,problems,last_qpage),'Single-column free-response problems. Shared reference page remains in full exam.')
  emit(r,'solutions',contiguous(d,solutions),'Scoring solution section, independent of preceding question paper.')
(F/'split_hints.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('documents/roles',len(out),'sections',sum(len(x['sections'])for x in out))
for x in out:print(x['resource_id'],x['role'],[(s['number'],s['page'],s['end_page'])for s in x['sections']])
