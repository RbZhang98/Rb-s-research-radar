"""Idempotent snapshot migration. Never reads/deletes private browser data."""
import datetime as dt,gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def migrate():
    state=ROOT/'data/lifecycle.json'
    if state.exists():print('Migration already completed; preserving existing history.');return
    raw=(ROOT/'data/articles.json').read_bytes();articles=json.loads(raw);seeds=[p for p in articles if p.get('grade')=='A']
    if len(seeds)!=16:raise RuntimeError(f'Expected exactly 16 A-level 1.0 seeds; found {len(seeds)}. Review snapshot before migration.')
    backup=ROOT/'backups/v1-articles-2026-10-16.json.gz';backup.parent.mkdir(exist_ok=True)
    with gzip.GzipFile(filename=str(backup),mode='wb',mtime=0) as f:f.write(raw)
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    index={p['id']:{'legacy':True,'firstSeenAt':None,'snapshotGrade':p['grade']} for p in articles}
    for p in seeds:
        p['legacyRecommendation']={k:p[k] for k in ['grade','score','reason','evidence','rulesVersion','pending'] if k in p}
        p['firstSeenAt']=None;p['discoveryKind']='legacy-seed'
    def write(name,value):(ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    write('data/articles.json',seeds);write('data/basic-seen.json',index);write('data/clinical-seen.json',{});write('data/clinical-articles.json',[]);write('data/transfer-candidates.json',[])
    write('data/lifecycle.json',{'version':2,'migratedAt':now,'launchDate':None,'snapshotSHA256':hashlib.sha256(raw).hexdigest(),'snapshotCount':len(articles),'seedIds':[p['id'] for p in seeds],'backup':str(backup.relative_to(ROOT))})
    for module,filename in [('basic','data/status.json'),('clinical','data/clinical-status.json')]:
        prior=json.loads((ROOT/filename).read_text()) if (ROOT/filename).exists() else {}
        prior.update({'newCount':0,'newIds':[],'total':len(seeds) if module=='basic' else 0,'retainedCount':len(seeds) if module=='basic' else 0,'activated':False})
        for j in prior.get('journals',[]):
            ps=[p for p in seeds if p['journalId']==j['id']] if module=='basic' else []
            j['total']=len(ps);j['missingAbstract']=sum(not p.get('abstract') for p in ps);j['bothSources']=sum(len(p['sources'])==2 for p in ps)
        write(filename,prior)
    print(f'Migrated {len(articles)} → {len(seeds)} seeds. Original compressed snapshot saved; online DOI index separate.')
if __name__=='__main__':migrate()
