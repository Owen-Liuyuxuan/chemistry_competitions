"""Verify all archived source hashes, crop geometry, pairing and deployed references."""
from pathlib import Path
import collections,hashlib,json,fitz
from PIL import Image
R=Path(__file__).resolve().parents[1];data=json.loads((R/'catalog/catalog.json').read_text());resources={r['id']:r for r in data['resources']};papers={p['id']:p for p in data['papers']};questions={q['id']:q for q in data['questions']};docs={};images=0
assert len(resources)==len(data['resources']);assert len(papers)==len(data['papers']);assert len(questions)==len(data['questions'])
for r in resources.values():
 if r.get('local_path'):
  path=R/r['local_path'];assert path.is_file(),path;assert hashlib.sha256(path.read_bytes()).hexdigest()==r['sha256'],path
  with fitz.open(path) as d:assert len(d)==r['pages']
for q in questions.values():
 assert q['paper_id'] in papers and q['id'] in papers[q['paper_id']]['question_ids']
 assert 2020<=q['year']<=2026 and q['problem'] and q['tags']
 for role in ['problem','solution']:
  if not q[role]:continue
  block=q[role];r=resources[block['resource_id']]
  if r['id'] not in docs:docs[r['id']]=fitz.open(R/r['local_path'])
  d=docs[r['id']];assert block['segments']
  for s in block['segments']:
   assert 1<=s['page']<=len(d);clip=fitz.Rect(s['clip']);assert clip.width>0 and clip.height>0 and (d[s['page']-1].rect+(-0.02,-0.02,0.02,0.02)).contains(clip),(q['id'],s)
   path=R/s['image'];assert path.is_file();assert hashlib.sha256(path.read_bytes()).hexdigest()==s['sha256'];im=Image.open(path);assert im.width>5 and im.height>3;images+=1
  if q['competition']=='USNCO' and q['year']==2022 and q['stage']=='national-i':assert role!='solution'
for p in papers.values():
 nums=sorted(questions[id]['number'] for id in p['question_ids']);assert nums==list(range(1,len(nums)+1)),(p['id'],nums)
 assert p['problem_resource_id'] in resources
for d in docs.values():d.close()
if (R/'dist').exists():
 for q in questions.values():
  for b in [q['problem'],q['solution']]:
   if b:
    for s in b['segments']:assert (R/'dist'/s['image']).is_file()
 for r in resources.values():
  if r.get('local_path'):assert (R/'dist'/r['local_path']).is_file()
print(f"PASS: {len(resources)} resources, {len(papers)} paper/task records, {len(questions)} questions, {images} image segments. All hashes, geometry, pairing exclusions and static paths checked.")
