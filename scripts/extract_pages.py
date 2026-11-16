"""Cache native text lines or OCR lines with PDF-space bounding boxes.
OCR text is navigation metadata only; original page rendering remains authoritative.
"""
import concurrent.futures,csv,io,json,os,subprocess,tempfile
from pathlib import Path
import fitz
R=Path(__file__).resolve().parents[1]
TESS=R/'.tools/tesseract/usr/bin/tesseract'
TESSDATA=R/'.tools/tesseract/usr/share/tesseract-ocr/4.00/tessdata'
def extract(path):
 target=R/'catalog/pages'/f'{path.stem}.json'
 if target.exists():return path.stem,'cached'
 d=fitz.open(path);pages=[]
 for n,p in enumerate(d):
  lines=[]
  for b in p.get_text('dict')['blocks']:
   for l in b.get('lines',[]):
    t=''.join(s['text'] for s in l['spans']).strip()
    if t:lines.append(dict(text=t,bbox=list(l['bbox'])))
  mode='native'
  if len(''.join(l['text'] for l in lines))<45:
   mode='ocr';scale=min(2,1800/p.rect.width);pix=p.get_pixmap(matrix=fitz.Matrix(scale,scale));env=dict(os.environ,TESSDATA_PREFIX=str(TESSDATA),OMP_THREAD_LIMIT='1')
   with tempfile.TemporaryDirectory() as td:
    image=Path(td)/'page.png';pix.save(image)
    res=subprocess.run([str(TESS),str(image),'stdout','-l','chi_sim+eng','--psm','3','-c','tessedit_create_tsv=1'],env=env,capture_output=True,check=True,text=True)
   groups={}
   for row in csv.DictReader(io.StringIO(res.stdout),delimiter='\t',quoting=csv.QUOTE_NONE):
    if row.get('level')!='5' or not row.get('text','').strip():continue
    key=tuple(row[k] for k in ['block_num','par_num','line_num']);x,y,w,h=[int(row[k]) for k in ['left','top','width','height']];word=row['text'];g=groups.setdefault(key,dict(text=[],bbox=[x,y,x+w,y+h]));g['text'].append(word);bb=g['bbox'];bb[:]=[min(bb[0],x),min(bb[1],y),max(bb[2],x+w),max(bb[3],y+h)]
   lines=[dict(text=' '.join(g['text']),bbox=[v/scale for v in g['bbox']]) for g in groups.values()]
  pages.append(dict(page=n+1,width=p.rect.width,height=p.rect.height,mode=mode,lines=lines))
 target.parent.mkdir(exist_ok=True,parents=True);target.write_text(json.dumps(pages,ensure_ascii=False));return path.stem,len(pages)
if __name__=='__main__':
 import sys
 paths=list((R/'originals').rglob('*.pdf'))
 if len(sys.argv)>1:paths=[p for p in paths if sys.argv[1] in str(p)]
 with concurrent.futures.ProcessPoolExecutor(4) as ex:
  for name,count in ex.map(extract,paths):print(name,count,flush=True)
