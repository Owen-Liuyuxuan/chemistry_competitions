"""Create the same portable static archive for local preview and GitHub Pages."""
from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parents[1];out=R/'dist';out.mkdir(exist_ok=True)
for name in ['index.html','style.css','app.js']:shutil.copy2(R/'web'/name,out/name)
(out/'data').mkdir(exist_ok=True);shutil.copy2(R/'catalog/catalog.json',out/'data/catalog.json')
# Only PDF originals referenced by catalog are copied; raw page images remain in source archive.
rows=json.loads((R/'catalog/resources.json').read_text())
for row in rows:
 if row.get('local_path'):
  src=R/row['local_path'];target=out/row['local_path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
if (out/'derived').exists():shutil.rmtree(out/'derived')
shutil.copytree(R/'derived',out/'derived')
(out/'.nojekyll').touch();print('Built',out)
