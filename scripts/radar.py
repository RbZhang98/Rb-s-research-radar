"""Metadata-only collector. Python standard library; no private API credentials."""
import argparse, concurrent.futures, datetime as dt, hashlib, html, json, os, re, sys, time
from pathlib import Path
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError
ROOT=Path(__file__).resolve().parents[1]
def read(path, default=None):
    p=ROOT/path
    return json.loads(p.read_text()) if p.exists() else default

def write(path, value):
    p=ROOT/path; p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix('.tmp'); tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n'); tmp.replace(p)

def clean(s):
    return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',html.unescape(s or '')))).strip()

def doi(s):
    return re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)','',s or '',flags=re.I).strip().lower()

def date_parts(v):
    p=v.get('date-parts',[[]])[0] if v else []
    if not p: return None
    try: return dt.date(*(p+[1,1])[:3]).isoformat()
    except (ValueError,TypeError): return None

def get(url, ttl=21600):
    key=hashlib.sha256(url.encode()).hexdigest(); path=ROOT/'.cache'/f'{key}.json'
    if path.exists() and time.time()-path.stat().st_mtime < ttl: return json.loads(path.read_text())
    error=None
    for attempt in range(4):
        try:
            with urlopen(Request(url,headers={'User-Agent':'ResearchRadar/1.0 (metadata research tracker)','Accept':'application/json'}),timeout=45) as r: value=json.load(r)
            path.parent.mkdir(exist_ok=True); path.write_text(json.dumps(value)); return value
        except Exception as e:
            if isinstance(e,HTTPError) and e.code in (400,404): raise
            error=e
            if attempt<3: time.sleep(min(2**attempt,8))
    raise RuntimeError(f'{type(error).__name__}: {error}')

def classify(p):
    r=read('config/rules.json'); title=p['title'].lower(); text=title+' '+p.get('abstract','').lower()
    def hits(terms, corpus=None): return [w for w in terms if re.search(r'(?<![a-z])'+re.escape(w),text if corpus is None else corpus)]
    matches={k:hits(v) for k,v in r['topics'].items()}; matches={k:v for k,v in matches.items() if v}
    bone=hits(r['bone_context'],re.sub(r'\bbone marrow\b','marrow',text)); immune=hits(r['immune_context']); mech=hits(r['mechanism'])
    score=sum(min(len(v),3)*(3 if k[0] in 'ABC' else 1) for k,v in matches.items())
    if bone and immune: matches.setdefault('D 骨免疫与炎症微环境',[]).extend(immune[:3]); score+=3
    if bone and mech: score+=2
    # Generic inflammation/macrophages/nanomaterials alone receive no domain score.
    grade='A' if score>=r['thresholds']['A'] and bone else 'B' if score>=r['thresholds']['B'] else 'C'
    pending=not p.get('abstract') or (not bone and bool(matches))
    notice=bool(re.match(r'^(author correction|publisher correction|correction|retraction|erratum|editorial)[: ]',title))
    if notice: grade='C'; score=0
    if pending and grade=='A': grade='B'
    return {'grade':grade,'score':score,'topics':list(matches),'pending':pending,'evidence':matches,
            'reason':('规则命中：'+'；'.join(', '.join(v) for v in matches.values()) if matches else '未发现明确的目标领域词汇，作为低相关元数据归档。')+('；摘要缺失或仅有可迁移线索，待人工确认。' if pending else '；分级仅表示关键词证据，未经语义或人工验证。'),'rulesVersion':r['version']}

def record(j,title,abstract,date,d,source,sourceid,rawdate=None):
    d=doi(d)
    return {'id':d or f'{source}:{sourceid}','doi':d,'title':clean(title),'abstract':clean(abstract),'journal':j['name'],'journalId':j['id'],'date':date,'datePrecision':rawdate or 'day','url':f'https://doi.org/{quote(d,safe="/()")}' if d else f'https://europepmc.org/article/MED/{sourceid}','sources':[source],'sourceIds':{source:str(sourceid)}}

def fetch_epmc(j,start,end):
    query='('+' OR '.join(f'ISSN:{i}' for i in j['issns'])+f') AND FIRST_PDATE:[{start} TO {end}]'
    cursor='*'; out=[]; rejected=0
    while True:
        v=get('https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+urlencode({'query':query,'format':'json','resultType':'core','pageSize':1000,'cursorMark':cursor}))
        rows=v.get('resultList',{}).get('result',[])
        for x in rows:
            ji=x.get('journalInfo',{}); journal=ji.get('journal',{})
            if not set(j['issns']) & {journal.get('issn'),journal.get('essn')}: rejected+=1; continue
            out.append(record(j,x.get('title',''),x.get('abstractText',''),x.get('firstPublicationDate'),x.get('doi'), 'Europe PMC',x.get('id')))
        nxt=v.get('nextCursorMark')
        if not rows or not nxt or nxt==cursor: break
        cursor=nxt
    return out, {'rejected':rejected,'query':query}

def _fetch_crossref_issn(j,start,end):
    cursor='*'; out=[]; rejected=0
    while True:
        url=f'https://api.crossref.org/journals/{j["issns"][0]}/works?'+urlencode({'filter':f'from-pub-date:{start},until-pub-date:{end},type:journal-article','rows':1000,'cursor':cursor})
        v=get(url)['message']; rows=v['items']
        for x in rows:
            if not set(j['issns']) & set(x.get('ISSN',[])): rejected+=1; continue
            dates=[(date_parts(x.get(k)),x.get(k,{}).get('date-parts',[[]])[0]) for k in ['published-online','published-print','published','issued']]
            valid=[(d,p) for d,p in dates if d]; date,parts=min(valid) if valid else (None,[])
            if not date or not start<=date<=end: continue
            out.append(record(j,(x.get('title') or [''])[0],x.get('abstract',''),date,x.get('DOI'),'Crossref',x.get('DOI'),'day' if len(parts)==3 else 'month' if len(parts)==2 else 'year'))
        nxt=v.get('next-cursor')
        if not rows or len(rows)<1000 or not nxt or nxt==cursor: break
        cursor=nxt
    return out, {'rejected':rejected,'query':f'ISSN {j["issns"][0]}, publication {start}..{end}'}

def fetch_crossref(j,start,end):
    # Crossref /journals/{issn}/works can contain only one format's deposits.
    # Query every verified ISSN; normalize and merge downstream.
    records=[]; rejected=0; unsupported=[]
    for issn in j['issns']:
        query_j={**j,'issns':[issn]+[i for i in j['issns'] if i!=issn]}
        try: rows,meta=_fetch_crossref_issn(query_j,start,end)
        except HTTPError as e:
            if e.code!=404: raise
            unsupported.append(issn); continue
        records.extend(rows); rejected+=meta['rejected']
    if len(unsupported)==len(j['issns']): raise RuntimeError('No Crossref journal endpoint for configured ISSNs')
    unique={p['id']:p for p in records}
    return list(unique.values()), {'rejected':rejected,'unsupportedIssns':unsupported,'query':f'ISSNs {", ".join(j["issns"])}, publication {start}..{end}'}

def merge(old,new):
    result={x['id']:dict(x) for x in old}
    for x in new:
        if not x['title'] or not x['date']: continue
        if x['id'] in result:
            p=result[x['id']]; p['sources']=sorted(set(p['sources']+x['sources'])); p.setdefault('sourceIds',{}).update(x['sourceIds'])
            if len(x['abstract'])>len(p.get('abstract','')): p['abstract']=x['abstract']
            if x['date']<p['date']: p['date']=x['date']; p['datePrecision']=x['datePrecision']
        else: result[x['id']]=x
    for p in result.values():
        p['title']=clean(p['title']); p['abstract']=clean(p.get('abstract','')); p.update(classify(p))
    return sorted(result.values(),key=lambda p:(p['date'],p['id']),reverse=True)

def verify(j):
    normalize=lambda s:re.sub('[^a-z0-9]','',s.lower())
    checks=[]
    for issn in j['issns']:
        url=f'https://api.crossref.org/journals/{issn}'
        try: v=get(url)['message']
        except HTTPError as e:
            if e.code!=404: raise
            # A valid electronic ISSN may have no Crossref journal registry entry.
            url='https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+urlencode({'query':'ISSN:'+issn,'format':'json','resultType':'core','pageSize':1})
            rows=get(url).get('resultList',{}).get('result',[])
            journal=rows[0].get('journalInfo',{}).get('journal',{}) if rows else {}
            v={'title':journal.get('title',''),'ISSN':[journal.get('issn'),journal.get('essn')]}
        checks.append({'issn':issn,'registryName':v['title'],'registryIssns':v['ISSN'],'verified':normalize(v['title'])==normalize(j['name']) and issn in v['ISSN'],'source':url})
    return {'id':j['id'],'name':j['name'],'verified':all(c['verified'] for c in checks),'checks':checks}

def run(args):
    journals=read('config/journals.json')
    if args.journals: journals=[j for j in journals if j['id'] in args.journals.split(',')]
    attempt_at=dt.datetime.now(dt.timezone.utc).isoformat(); now=attempt_at; end=args.end or dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).date().isoformat()
    start=args.start or (dt.date.fromisoformat(end)-dt.timedelta(days=14)).isoformat()
    old=read('data/articles.json',[]); previous=read('data/status.json',{}); statuses=[]; rows=[]; verifications=[]
    def safe_verify(j):
        try: return verify(j)
        except Exception as e: return {'id':j['id'],'verified':False,'error':str(e)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        verifications=list(pool.map(safe_verify,journals))
    def task(j,source,fn):
        begin=time.monotonic()
        try:
            if not next(v for v in verifications if v['id']==j['id'])['verified']: raise RuntimeError('ISSN registry verification failed')
            records,meta=fn(j,start,end)
            return records,{'journalId':j['id'],'source':source,'ok':True,'count':len(records),'finishedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'seconds':round(time.monotonic()-begin,2),**meta}
        except Exception as e: return [],{'journalId':j['id'],'source':source,'ok':False,'error':str(e),'count':0}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(task,j,s,fn) for j in journals for s,fn in [('Europe PMC',fetch_epmc),('Crossref',fetch_crossref)]]
        for future in concurrent.futures.as_completed(futures):
            records,status=future.result(); rows.extend(records); statuses.append(status); print(json.dumps(status,ensure_ascii=False),flush=True)
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    articles=merge(old,rows); oldids={p['id'] for p in old}; newids=[p['id'] for p in articles if p['id'] not in oldids]
    byjournal=[]
    for j in journals:
        ss=[s for s in statuses if s['journalId']==j['id']]; good=all(s['ok'] for s in ss)
        prior=next((x for x in previous.get('journals',[]) if x['id']==j['id']),{})
        ps=[p for p in articles if p['journalId']==j['id']]
        byjournal.append({'id':j['id'],'name':j['name'],'ok':good,'lastSuccess':now if good else prior.get('lastSuccess'),'sources':ss,'total':len(ps),'missingAbstract':sum(not p['abstract'] for p in ps),'bothSources':sum(len(p['sources'])==2 for p in ps)})
    success=all(s['ok'] for s in statuses)
    status={'attemptAt':attempt_at,'lastSuccess':now if success and len(journals)==len(read('config/journals.json')) else previous.get('lastSuccess'),'fetchOk':success,'publication':'local-unpublished','window':{'start':start,'end':end},'newCount':len(newids),'newIds':newids,'total':len(articles),'journals':byjournal,'verification':verifications}
    write('data/articles.json',articles); write('data/status.json',status)
    write('reports/last-run.json',status)
    print(f'TOTAL={len(articles)} NEW={len(newids)} JOURNALS_OK={sum(j["ok"] for j in byjournal)}/{len(journals)}')
    return 0 if success else 1
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--start'); p.add_argument('--end'); p.add_argument('--journals'); sys.exit(run(p.parse_args()))
