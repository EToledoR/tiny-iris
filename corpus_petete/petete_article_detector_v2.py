#!/usr/bin/env python3
"""Detect likely Petete article headings directly from pdftotext -bbox-layout HTML.

Conservative: it detects typography/geometry patterns, not meaning or OCR fixes.
It outputs candidate headings and tentative article page spans.
"""
import argparse, html, json, re
from pathlib import Path


def pages_from_bbox(path):
    s=Path(path).read_text(encoding='utf-8',errors='replace')
    out=[]
    for pno,pm in enumerate(re.finditer(r'<page[^>]*>(.*?)</page>',s,re.S),1):
        chunk=pm.group(1)
        pm0=re.search(r'<page[^>]*width="([\d.]+)" height="([\d.]+)"', '<page'+pm.group(0).split('<page',1)[1].split('>',1)[0]+'>')
        width=float(pm0.group(1)) if pm0 else 1150.0
        height=float(pm0.group(2)) if pm0 else 1500.0
        lines=[]
        for li,lm in enumerate(re.finditer(r'<line([^>]*)>(.*?)</line>',chunk,re.S)):
            attrs=dict(re.findall(r'(xMin|yMin|xMax|yMax)="([^"]+)"',lm.group(1)))
            words=[]
            for wm in re.finditer(r'<word([^>]*)>(.*?)</word>',lm.group(2),re.S):
                wa=dict(re.findall(r'(xMin|yMin|xMax|yMax)="([^"]+)"',wm.group(1)))
                if not wa: continue
                raw=re.sub(r'<[^>]+>','',wm.group(2))
                words.append((float(wa['xMin']),float(wa['yMin']),float(wa['xMax']),float(wa['yMax']),html.unescape(raw)))
            if words:
                text=' '.join(w[4] for w in sorted(words))
                x0=min(w[0] for w in words); y0=min(w[1] for w in words)
                x1=max(w[2] for w in words); y1=max(w[3] for w in words)
                lines.append({'id':li,'x0':x0,'y0':y0,'x1':x1,'y1':y1,'h':y1-y0,'text':text})
        out.append({'page':pno,'width':width,'height':height,'lines':lines})
    return out


def letters(s): return [c for c in s if c.isalpha()]
def upper_ratio(s):
    a=letters(s); return sum(c.isupper() for c in a)/len(a) if a else 0

def clean(s): return re.sub(r'\s+',' ',s).strip()

def line_score(line):
    t=clean(line['text']); n=len(t); h=line['h']; w=line['x1']-line['x0']
    score=0; reasons=[]
    if n < 4: return -99, ['too-short']
    if h >= 30 and 8 <= n <= 120: score += 9; reasons.append('very-large-title-font')
    if h >= 17: score += 5; reasons.append('large-font')
    elif h >= 15.5: score += 2; reasons.append('medium-font')
    else: score -= 3; reasons.append('small-font')
    ur=upper_ratio(t)
    if ur >= .80: score += 5; reasons.append('uppercase')
    elif ur >= .55: score += 2; reasons.append('mixed-uppercase')
    if t.startswith(('¿','¡')): score += 2; reasons.append('question')
    if n <= 60: score += 1; reasons.append('compact')
    if n > 120: score -= 3; reasons.append('long')
    if w < 120 and n < 30: score -= 3; reasons.append('small-label')
    if line['y0'] > 1450: score -= 5; reasons.append('footer')
    weird=sum(c in '^~`|\\@#$%{}[]' for c in t)
    if weird: score -= min(3,weird); reasons.append('ocr-garbage')
    return score,reasons

def detect(page, threshold=7):
    ls=page['lines']; cand=[]
    for i,l in enumerate(ls):
        score,reasons=line_score(l)
        if score < threshold: continue
        # Diagram labels tend to be tiny and are already penalised; also reject
        # lines embedded in dense runs of normal body text.
        cand.append({'line':i,'score':score,'reasons':reasons,'text':clean(l['text']),
                     'bbox':[round(l['x0'],1),round(l['y0'],1),round(l['x1'],1),round(l['y1'],1)]})
    return cand

def combine_heading_lines(page,cands):
    """Join adjacent heading lines when they are vertically close and x-aligned."""
    by={c['line']:c for c in cands}; used=set(); groups=[]
    for c in cands:
        i=c['line']
        if i in used: continue
        group=[c]; used.add(i); j=i+1
        while j in by:
            a=group[-1]; b=by[j]
            ay=a['bbox'][1]; byy=b['bbox'][1]
            gap=byy-a['bbox'][3]
            ax0,ax1=a['bbox'][0],a['bbox'][2]; bx0,bx1=b['bbox'][0],b['bbox'][2]
            overlap=max(0,min(ax1,bx1)-max(ax0,bx0))/max(1,min(ax1-ax0,bx1-bx0))
            if gap <= 18 and overlap >= .25:
                group.append(b); used.add(j); j+=1
            else: break
        groups.append(group)
    result=[]
    for g in groups:
        text=' '.join(x['text'] for x in g)
        result.append({'page':page['page'],'lines':[x['line'] for x in g],
                       'score':sum(x['score'] for x in g),
                       'text':clean(text),'bbox':[min(x['bbox'][0] for x in g),min(x['bbox'][1] for x in g),max(x['bbox'][2] for x in g),max(x['bbox'][3] for x in g)],
                       'max_line_height':max(x['bbox'][3]-x['bbox'][1] for x in g),
                       'reasons':sorted(set(r for x in g for r in x['reasons']))})
    return result

def classify(c):
    t=c['text']; h=c['bbox'][3]-c['bbox'][1]
    # Explicitly keep this weak: these are useful review hints, not truth.
    if c.get('max_line_height', h) >= 30 and len(t) < 120: return 'likely_title'
    if t.startswith(('¿','¡')): return 'likely_section_heading'
    if upper_ratio(t)>.75: return 'likely_heading'
    return 'heading_candidate'

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('input'); ap.add_argument('-o','--output',default='petete_article_candidates_v2.json')
    ap.add_argument('--threshold',type=int,default=7); ap.add_argument('--min-page',type=int); ap.add_argument('--max-page',type=int)
    args=ap.parse_args()
    pages=pages_from_bbox(args.input)
    if args.min_page: pages=[p for p in pages if p['page']>=args.min_page]
    if args.max_page: pages=[p for p in pages if p['page']<=args.max_page]
    candidates=[]
    for p in pages:
        c=combine_heading_lines(p,detect(p,args.threshold))
        for x in c:
            x['type']=classify(x); candidates.append(x)
    # Tentative spans: each strong candidate begins a new article. Page 1 is
    # retained as an explicit unknown start when no title was detected before it.
    starts=[c for c in candidates if c['type']=='likely_title' and (c.get('max_line_height', c['bbox'][3]-c['bbox'][1]) >= 30 or c['page']==1)]
    starts.sort(key=lambda c:(c['page'],c['bbox'][1]))
    articles=[]
    for i,s in enumerate(starts):
        end=starts[i+1]['page']-1 if i+1<len(starts) else (pages[-1]['page'] if pages else 0)
        articles.append({'article_id':i+1,'title':s['text'],'start_page':s['page'],'end_page':end,
                         'title_candidate':s,'status':'review'})
    out={'source':Path(args.input).name,'method':'bbox-line-heuristic-v2','candidates':candidates,'articles':articles}
    Path(args.output).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print('CANDIDATES')
    for c in candidates:
        print(f"P{c['page']:03d} {c['type']:24s} score={c['score']:2d}  {c['text']}")
    print('\nTENTATIVE ARTICLES')
    for a in articles:
        print(f"{a['article_id']:03d}. P{a['start_page']}-{a['end_page']}  {a['title']}")

if __name__=='__main__': main()
