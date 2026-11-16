"""Locate official USNCO questions/keys without generating replacement text.

Coordinates are PDF points and page numbers are one-based. Explicit segments
handle the two-column MC sheets, shared prompts, and non-contiguous lab sheets.
"""
from pathlib import Path
import json
import re
import fitz

ROOT = Path(__file__).resolve().parents[1]


def lines(page):
    return [("".join(s['text'] for s in line['spans']).strip(), list(line['bbox']))
            for block in page.get_text('dict')['blocks'] for line in block.get('lines', [])]


def segment(doc, p, y0=48, y1=748, x0=35, x1=578):
    rect = doc[p].rect
    if y1 >= 730:
        # Avoid slicing the copyright footer or a standalone page number in half.
        # Several official PDFs put these at 743 pt, just above our body limit.
        footer_tops = [box[1] for text, box in lines(doc[p])
                       if box[1] > 700 and ('Property of ACS USNCO' in text
                           or re.fullmatch(r'(?:Page )?\d+', text))]
        if footer_tops:
            y1 = min(y1, min(footer_tops)-4)
    return {'page': p+1, 'clip': [round(x0, 2), round(max(0,y0), 2), round(min(rect.width,x1), 2), round(min(rect.height,y1), 2)]}


def section(n, segments, title=None, notes=''):
    assert segments and all(s['clip'][2] > s['clip'][0] and s['clip'][3] > s['clip'][1] for s in segments)
    return dict(number=n, title=title or f'第{n}题', page=segments[0]['page'], y=segments[0]['clip'][1],
                x0=segments[0]['clip'][0], x1=segments[0]['clip'][2],
                end_page=segments[-1]['page'], end_y=segments[-1]['clip'][3],
                segments=segments, notes=notes)


def span(doc, start, end, top=48, bottom=748):
    p0,y0=start; p1,y1=end
    return [segment(doc,p,y0 if p==p0 else top,y1 if p==p1 else bottom)
            for p in range(p0,p1+1) if (y1 if p==p1 else bottom) > (y0 if p==p0 else top)+1]


def multiple_choice(doc, rid, year):
    key_page = next(p for p,page in enumerate(doc) if re.search(r'\bKEY\b',page.get_text()) and 'Answer' in page.get_text())
    found=[]
    all_starts=[]
    for p in range(2,key_page):
        for text,box in lines(doc[p]):
            m=re.match(r'^(\d{1,2})\.(?:\s+|$)',text)
            if m and (35<=box[0]<=55 or 315<=box[0]<=337):
                n=int(m.group(1));col=0 if box[0]<300 else 1
                if n<=64:all_starts.append((n,p,box[1],col,text))
    candidates={}
    for item in all_starts:
        if item[0]<=60:
            assert item[0] not in candidates,(rid,item[0])
            candidates[item[0]]=item
    assert sorted(candidates)==list(range(1,61)),(rid,sorted(candidates))
    shared={}
    for p in range(2,key_page):
        for text,box in lines(doc[p]):
            m=re.match(r'Questions (\d+)\s*(?:and|[-–])\s*(\d+)',text)
            if m:
                n1,n2=map(int,m.groups());col=0 if box[0]<300 else 1
                first=candidates[n1]
                assert p==first[1] and col==first[3]
                common=segment(doc,p,box[1]-3,first[2]-3,35 if col==0 else 315,300 if col==0 else 578)
                shared[n1]=common;shared[n2]=common
    for n in range(1,61):
        _,p,y,col,text=candidates[n]
        same=sorted((i for i in all_starts if i[1]==p and i[3]==col and i[2]>y+1),key=lambda x:x[2])
        end=same[0][2]-3 if same else 748
        # A shared preamble may be the first thing after the preceding question.
        for common in shared.values():
            if common['page']==p+1 and common['clip'][0]==(35 if col==0 else 315) and common['clip'][1]>y:
                end=min(end,common['clip'][1])
        for t,b in lines(doc[p]):
            if re.match(r'END OF (?:TEST|EXAM)',t) and (b[0]<300)==(col==0) and b[1]>y:end=min(end,b[1]-3)
        segs=[]
        if n in shared:segs.append(shared[n])
        segs.append(segment(doc,p,y-3,end,35 if col==0 else 315,300 if col==0 else 578))
        title=re.sub(r'^\d+\.\s*','',text)
        found.append(section(n,segs,f'选择题 {n} · {title[:100]}','双栏原题按列切分；排除第61–64项反馈问卷。'+('含共用题干。' if n in shared else '')))
    if year==2022:
        assert 'Local Section Exam' in doc[key_page].get_text()
        return [{'resource_id':rid,'role':'problems','sections':found,'notes':'原附件末页误附Local Section Exam答案；不作为National I参考答案配对。'}]
    keys=[]
    words=doc[key_page].get_text('words')
    for word in words:
        m=re.fullmatch(r'(\d{1,2})\.',word[4])
        if not m:continue
        n=int(m.group(1))
        if not 1<=n<=60:continue
        col=0 if word[0]<300 else 1
        x0,x1=(95,220) if col==0 else (383,510)
        matches=[w for w in words if abs(w[1]-word[1])<2 and re.fullmatch('[ABCD]',w[4]) and x0<w[0]<x1]
        assert len(matches)==1,(rid,n,matches)
        box=segment(doc,key_page,word[1]-.2,word[3]+.2,x0,x1)
        keys.append(section(n,[box],f'选择题 {n} · 官方答案 {matches[0][4]}','只切出对应题号与官方选项字母；非解释性解答。'))
    assert len(keys)==60,(rid,len(keys))
    return [{'resource_id':rid,'role':'problems','sections':found},{'resource_id':rid,'role':'solutions','sections':sorted(keys,key=lambda s:s['number'])}]


def written(doc,rid,year):
    first_solution=next(p for p,page in enumerate(doc) if re.search(r'USNCO Part 2 Solutions',page.get_text(),re.I))
    starts=[]
    if year>=2022:
        for p in range(first_solution):
            for text,box in lines(doc[p]):
                m=re.match(r'Question ([1-8])\s*\(page 1 of',text)
                if m:starts.append((int(m.group(1)),p,box[1]-3))
    else:
        for p in range(first_solution):
            for text,box in lines(doc[p]):
                m=re.match(r'^([1-8])\.\s*\[\d+%',text)
                if m:starts.append((int(m.group(1)),p,box[1]-3))
    assert [s[0] for s in starts]==list(range(1,9)),(rid,starts)
    solution_starts=[]
    for p in range(first_solution,len(doc)):
        for text,box in lines(doc[p]):
            m=re.match(r'^([1-8])\.\s*(?:a\.|$)',text)
            if m and box[0]<85:solution_starts.append((int(m.group(1)),p,box[1]-3))
    assert [s[0] for s in solution_starts]==list(range(1,9)),(rid,solution_starts)
    problems=[];solutions=[]
    for index,(n,p,y) in enumerate(starts):
        if index<7:end=starts[index+1][1:]
        else:
            # Do not append blank sheets following Question 8.
            last=first_solution-1
            if year>=2022:
                q8=[j for j in range(p,first_solution) if re.search(r'Question 8\s*\(page',doc[j].get_text())]
                last=max(q8)
            end=(last,748)
            for text,box in lines(doc[last]):
                if re.match(r'END OF (?:TEST|EXAM)',text):end=(last,box[1]-3)
        segs=span(doc,(p,y),end)
        # A new question starts on a new page; strip the otherwise empty strip
        # before its header, while preserving continuations on the last page.
        if index<7 and segs[-1]['page']==end[0]+1 and segs[-1]['clip'][3]-segs[-1]['clip'][1]<60:segs.pop()
        problems.append(section(n,segs,f'简答题 {n}','保留对应题目的连续原页及作答空间。'))
    for index,(n,p,y) in enumerate(solution_starts):
        end=solution_starts[index+1][1:] if index<7 else (len(doc)-1,748)
        segs=span(doc,(p,y),end)
        if index<7 and segs[-1]['page']==end[0]+1 and segs[-1]['clip'][3]-segs[-1]['clip'][1]<45:segs.pop()
        solutions.append(section(n,segs,f'简答题 {n} · 官方参考解答'))
    return [{'resource_id':rid,'role':'problems','sections':problems},{'resource_id':rid,'role':'solutions','sections':solutions}]


def laboratory(doc,rid,year):
    prompt_page=2
    heads=[]
    safety=None
    for text,box in lines(doc[prompt_page]):
        m=re.fullmatch(r'Lab Problem ([12])',text)
        if m:heads.append((int(m.group(1)),box[1]-3))
        if text=='Safety Considerations':safety=box[1]-3
    assert len(heads)==2
    sheets={1:[],2:[]}
    for p,page in enumerate(doc):
        if p<3:continue
        for text,box in lines(page):
            m=re.match(r'Answer Sheet for Laboratory Practical Problem ([12])',text)
            if m:sheets[int(m.group(1))].append((p,box[1]-3))
    assert sheets[1] and sheets[2]
    p1,y1=sheets[1][0];p2,y2=sheets[2][0]
    blank=next((p for p in range(p2+1,len(doc)) if re.search(r'page.*(?:left )?blank',doc[p].get_text(),re.I)),None)
    examiner=next((p for p in range(p2+1,len(doc)) if 'EXAMINER’S INSTRUCTIONS' in doc[p].get_text() or "EXAMINER'S INSTRUCTIONS" in doc[p].get_text()),len(doc))
    last_sheet=(blank if blank is not None else examiner)-1
    problems=[]
    for n,start in heads:
        end=heads[1][1] if n==1 else 748
        segs=[]
        if safety is not None:segs.append(segment(doc,prompt_page,safety,heads[0][1]))
        segs.append(segment(doc,prompt_page,start,end))
        begin,end_page=(p1,p2-1) if n==1 else (p2,last_sheet)
        segs.extend(segment(doc,p,y1 if p==p1 else y2 if p==p2 else 48,748) for p in range(begin,end_page+1))
        prompt=doc[prompt_page].get_text(clip=fitz.Rect(35,start,578,end))
        excerpt=' '.join(prompt.split());excerpt=re.sub(r'^Lab Problem [12]\s*(?:Question:)?\s*','',excerpt)
        problems.append(section(n,segs,f'实验 {n} · {excerpt[:105]}','含共同安全要求、对应题干与该题答题纸；不包含考官材料。'))
    solutions=[]
    if year in [2025,2026]:
        assert len(sheets[1])==len(sheets[2])==2
        s1,sy1=sheets[1][1];s2,sy2=sheets[2][1]
        last=len(doc)-1
        if re.search(r'page.*(?:left )?blank',doc[last].get_text(),re.I):last-=1
        for n,a,b,starty in [(1,s1,s2-1,sy1),(2,s2,last,sy2)]:
            solutions.append(section(n,[segment(doc,p,starty if p==a else 48,748) for p in range(a,b+1)],f'实验 {n} · 官方评分标准与样例结果'))
    else:
        rubric=[]
        for p in range(examiner+1,len(doc)):
            for text,box in lines(doc[p]):
                m=re.match(r'^Lab Problem ([12])(?: Prompt:)?$',text)
                if m:rubric.append((int(m.group(1)),p,box[1]-3))
        assert [r[0] for r in rubric]==([1] if year==2024 else [1,2]),(rid,rubric)
        for index,(n,p,y) in enumerate(rubric):
            end=rubric[index+1][1:] if index+1<len(rubric) else (len(doc)-1,748)
            segs=span(doc,(p,y),end)
            if index+1<len(rubric) and segs[-1]['clip'][3]-segs[-1]['clip'][1]<10:segs.pop()
            solutions.append(section(n,segs,f'实验 {n} · 官方评分标准与样例结果','2024原始合并文件只附实验1评分，实验2不建立答案关联。' if year==2024 else ''))
    return [{'resource_id':rid,'role':'problems','sections':problems},{'resource_id':rid,'role':'solutions','sections':solutions}]


def main():
    rows=json.loads((ROOT/'research/foreign/resources.json').read_text())
    out=[]
    for row in rows:
        if row['competition']!='USNCO' or not row.get('local_path'):continue
        doc=fitz.open(ROOT/row['local_path']);stage=row['stage']
        function={'national-i':multiple_choice,'national-ii':written,'national-iii':laboratory}[stage]
        result=function(doc,row['id'],row['year']);out.extend(result)
        print(row['id'],[(x['role'],len(x['sections'])) for x in result])
    target=ROOT/'research/foreign/usnco_split_hints.json'
    target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print('Wrote',target,'sections',sum(len(x['sections']) for x in out))

if __name__=='__main__':main()
