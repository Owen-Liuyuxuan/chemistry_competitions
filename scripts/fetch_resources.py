"""Restore missing PDF originals using the audited source registry, without overwriting files.

Image-assembled originals use collect_china/collect_finals; generated compilations use build_catalog.
"""
from pathlib import Path
import hashlib,json,requests
R=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 for row in json.loads((R/'catalog/resources.json').read_text()):
  name=row.get('local_path')
  if not name or (R/name).exists():continue
  if row.get('image_based') or row.get('components'):
   print('ASSEMBLY REQUIRED',row['id']);continue
  url=row.get('mirror_url') or row['source_url']
  response=requests.get(url,timeout=60);response.raise_for_status();raw=response.content
  if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError(f"Source changed; inspect instead of overwriting: {row['id']}")
  p=R/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);print('restored',name)
