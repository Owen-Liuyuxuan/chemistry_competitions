"""Detect CChO top-level headings; emit a reviewable boundary manifest, never guessed crops."""
from pathlib import Path
import json,re,unicodedata
R=Path(__file__).resolve().parents[1]
def norm(t):return re.sub(r'\s+','',unicodedata.normalize('NFKC',t))
def detect(rid):
 p=R/'catalog/pages'/f'{rid}.json'
 if not p.exists():return []
 rows=json.loads(p.read_text());found=[]
 for p in rows:
  for l in p['lines']:
   text=norm(l['text']);m=re.match(r'第(\d{1,2})[题趟颢]',text)
   if not m:continue
   n=int(m[1])
   if not 1<=n<=25:continue
   found.append(dict(number=n,title=unicodedata.normalize('NFKC',l['text']),page=p['page'],y=round(max(0,l['bbox'][1]-3),2)))
 return found
if __name__=='__main__':
 rows=[]
 for p in sorted((R/'catalog/pages').glob('ccho*.json')):
  h=detect(p.stem)
  # A repeated heading for the SAME question within a combined question/answer section
  # is not a new question. Keep first occurrence; retain repeats in the audit log.
  unique=[];seen=set()
  for x in h:
   if x['number'] not in seen:unique.append(x);seen.add(x['number'])
  rows.append(dict(resource_id=p.stem,role='solutions' if any(k in p.stem for k in ['solutions','grading','guide']) else 'problems',sections=unique,repeated_headings=len(h)-len(unique)))
 (R/'research/china/split_hints.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
 for r in rows: print(r['resource_id'],[x['number'] for x in r['sections']])
