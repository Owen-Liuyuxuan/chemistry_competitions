"""Apply inspected OCR boundary corrections and select canonical CChO papers."""
import json
from pathlib import Path
from china_hints import detect
R=Path(__file__).resolve().parents[1]
# Coordinates refer to original PDF points, 1-based pages. Inspected against page renders/text.
FIX={
'ccho-2020-juesai-1':[(4,3,541.6,'第4题 铝粉的氧化与点火')],
'ccho-2020-official-1-solutions':[(6,4,462.5,'第6题 金属元素与氟化物')],
'ccho-2021-official-1-problems':[(2,1,249,'第2题 多样的氧物种'),(3,1,445,'第3题 硼的化合物'),(4,1,687,'第4题 碳的经典化合物与新的碳单质')],
'ccho-2022-official-1-problems':[(3,1,454.5,'第3题 锗的团簇化合物')],
'ccho-2022-official-1-solutions':[(2,1,655,'第2题 高压碳酸盐化学')],
'ccho-2023-official-1-problems':[(1,1,188,'第1题 镓的化合物'),(8,4,610.5,'第8题 有机化合物基本概念和反应')],
'ccho-2023-official-1-solutions':[(5,4,73.5,'第5题 简单的分子 复杂的反应')],
'ccho-2025-official-1-solutions':[(5,6,408,'第5题 Xe化合物的结构'),(9,14,702,'第9题 有机合成')],
'ccho-2026-official-1-problems':[(1,1,415,'第1题 磷化学')],
'ccho-2026-official-1-solutions':[(5,7,1208,'第5题 密堆积结构')],
'ccho-2025-final-theory-1':[(5,9,362.5,'第5题 水相变中的热力学与动力学')],
'ccho-2024-final-theory-1':[(1,3,26.5,'第1题 蚯蚓血红蛋白'),(2,3,130,'第2题 多彩的铝配合物'),(3,4,81,'第3题 硅基材料'),(4,5,199.5,'第4题 分光光度法测量平衡常数'),(5,7,20.5,'第5题 过氧乙酸：绿色环保型消毒剂'),(6,9,76,'第6题 IVB族元素化合物'),(7,11,203.5,'第7题 von Richter重排反应'),(8,13,49.5,'第8题 光化学反应与重排'),(9,14,93.5,'第9题 串联环化反应')]
}
def hint(rid,role):
 h=detect(rid);by={}
 for x in h:by.setdefault(x['number'],x)
 for n,p,y,t in FIX.get(rid,[]):by[n]=dict(number=n,title=t,page=p,y=y)
 sections=sorted(by.values(),key=lambda x:(x['page'],x['y']))
 return dict(resource_id=rid,role=role,sections=sections,notes='题号定位经顺序与连续性校验；OCR题名待人工逐字审校。')
rows=[];papers=[]
def add(pid,year,stage,q,a=None,note=''):
 papers.append(dict(id=pid,competition='CChO',year=year,stage=stage,title=f'{year} 中国化学奥林匹克 · {stage}',problem_resource_id=q,solution_resource_id=a,notes=note))
 for rid,role in [(q,'problems'),(a,'solutions')]:
  if rid and not any(r['resource_id']==rid and r['role']==role for r in rows):rows.append(hint(rid,role))
for year in range(2020,2027):
 add(f'ccho-{year}-preliminary-1',year,'初赛（省级赛）'+('第一场' if year==2022 else ''),f'ccho-{year}-official-1-problems',f'ccho-{year}-official-1-solutions')
 if year==2022:add('ccho-2022-preliminary-2',year,'初赛（省级赛）第二场','ccho-2022-official-2-problems','ccho-2022-official-2-solutions')
for year in range(2020,2024):
 for n in [1,2]:add(f'ccho-{year}-final-{n}',year,f'决赛理论第{n}场',f'ccho-{year}-juesai-{n}',f'ccho-{year}-juesai-grading-{n}' if year in [2021,2022] else None,'题面为第三方重排版；原分值等须与官方版本核对。')
add('ccho-2024-final-1',2024,'决赛理论第一场','ccho-2024-final-theory-1','ccho-2024-juesai-1-guide','题卷为扫描原卷；答案来自第三方命题评析，未经官方核验。')
add('ccho-2024-final-2',2024,'决赛理论第二场','ccho-2024-juesai-2-guide','ccho-2024-juesai-2-guide','暂仅取得第三方题答合编解析，原题页含解析；独立纯题卷待补。')
add('ccho-2025-final-1',2025,'决赛理论','ccho-2025-final-theory-1','ccho-2025-final-theory-1','题目与参考答案按小问交错排列，题面标签展示题答合编原件。')
# 2026 scans: 15 pages pure questions followed by 29 pages scoring reference.
rid='ccho-2026-final-theory';h=detect(rid)
for role,lo,hi in [('problems',1,15),('solutions',16,44)]:
 sec=[];seen=set()
 for x in h:
  if lo<=x['page']<=hi and x['number'] not in seen:sec.append(x);seen.add(x['number'])
 if role=='problems':sec.append(dict(number=6,page=9,y=537,title='第6题 薛定谔方程100周年'))
 sec.sort(key=lambda x:(x['page'],x['y']));sec[-1].update(end_page=hi,end_y=None)
 rows.append(dict(resource_id=rid,role=role,sections=sec,notes='原件题卷页1–15，答案页16–44，单独分切。'))
papers.append(dict(id='ccho-2026-final',competition='CChO',year=2026,stage='决赛理论',title='2026 中国化学奥林匹克 · 决赛理论',problem_resource_id=rid,solution_resource_id=rid,notes='第三方图片转载；理论试题与评分答案分段切分。'))
# Integrated practical experiments retain all apparatus and shared instructions.
for year in [2025,2026]:
 rid=f'ccho-{year}-final-practical';papers.append(dict(id=rid,competition='CChO',year=year,stage='决赛实验',title=f'{year} 中国化学奥林匹克 · 决赛实验',problem_resource_id=rid,solution_resource_id=None,notes='2025转载扫描仅含印刷页2–3，首张缺失，完整性待补。' if year==2025 else '保留耗材说明、实验任务及附图；标准答案尚未获取。'))
 rows.append(dict(resource_id=rid,role='problems',sections=[dict(number=1,title='EDTA配位滴定综合实验' if year==2025 else '环丙沙星与薄层色谱综合实验',page=1,y=0)],notes='多环节共享实验背景，按一个综合实验任务归档，不按操作步骤拆成独立题。'))
# 2026 practical has three numbered tasks sharing the ciprofloxacin introduction.
for h in rows:
 if h['resource_id']=='ccho-2026-final-practical':
  intro=dict(page=2,clip=[0,156,960,605])
  h['sections']=[
   dict(number=1,title='环丙沙星的合成路线设计',segments=[intro,dict(page=2,clip=[0,605,960,757])]),
   dict(number=2,title='环丙沙星中间体合成、TLC与减压蒸馏',segments=[dict(page=1,clip=[0,0,960,1355.25]),intro,dict(page=2,clip=[0,757,960,1356]),dict(page=3,clip=[0,0,960,1356]),dict(page=4,clip=[0,0,960,795])]),
   dict(number=3,title='环丙沙星的核磁共振谱分析',segments=[intro,dict(page=4,clip=[0,795,960,1356]),dict(page=5,clip=[0,0,960,1356]),dict(page=6,clip=[0,0,960,1356]),dict(page=7,clip=[0,0,960,1356])])]
  h['notes']='按原卷1–3题拆分，共享药物结构背景重复附入；第2题另附耗材表。'
for p in papers:
 if p['id']=='ccho-2026-final-practical':p['notes']='按合成设计、实验操作、核磁谱分析三个顶层任务分切；共享背景与耗材保留。标准答案尚未获取。'
(R/'research/china/selected_papers.json').write_text(json.dumps(papers,ensure_ascii=False,indent=2))
(R/'research/china/selected_hints.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
for row in rows:
 ns=[s['number'] for s in row['sections']]
 assert ns==list(range(1,len(ns)+1)),(row['resource_id'],ns)
print(len(papers),'papers;',sum(len(x['sections']) for x in rows),'question/solution sections; all numbering continuous')
