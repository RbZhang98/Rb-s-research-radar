"""Public retention policy; private IndexedDB snapshots are never read or modified."""
import datetime as dt

def retain(existing,raw,index,*,radar,now,launch_date,rediscover_legacy=False):
    history={p['id']:dict(p) for p in existing}; new_ids=[]; transfers=[]
    for row in raw:
        p=dict(row); key=p['id']; seen=index.get(key); legacy=bool(seen and seen.get('legacy'))
        first=(seen or {}).get('firstSeenAt') or now
        index[key]={**(seen or {}),'firstSeenAt':None if legacy and not seen.get('firstSeenAt') else first,'lastSeenAt':now,'lastGrade':p['grade']}
        if key in history:
            old=history[key]
            if old.get('legacyRecommendation'):
                # The 16 curated 1.0 seeds retain their original recommendation.
                for field,value in old['legacyRecommendation'].items():p[field]=value
                for field in ['doi','title','abstract','journal','date']:p[field]=old[field]
            history[key]={**old,**p,'firstSeenAt':old.get('firstSeenAt'),'discoveryKind':old.get('discoveryKind','new')};continue
        if legacy and not rediscover_legacy:continue
        if radar=='clinical' and p['date']<launch_date:continue
        fresh=not seen and p['date']>=launch_date
        p['firstSeenAt']=first;p['lastSeenAt']=now;p['discoveryKind']='new' if fresh else 'historical-rediscovery'
        if radar=='basic' and p['grade'] not in ['A','B']:
            if p.get('inspirationScore',0)>=2 and not legacy and first[:10]>=str(dt.date.fromisoformat(now[:10])-dt.timedelta(days=14)):
                p['temporary']=True;p['expiresAt']=(dt.datetime.fromisoformat(first)+dt.timedelta(days=14)).isoformat();transfers.append(p)
            continue
        if radar=='clinical' and p.get('studyType')=='更正 / 通知':continue
        history[key]=p
        if fresh:new_ids.append(key)
    return sorted(history.values(),key=lambda p:(p['date'],p['id']),reverse=True),index,new_ids,transfers
