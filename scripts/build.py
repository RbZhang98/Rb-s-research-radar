"""Build public metadata only; never publish dedup indexes, snapshots or local notes."""
import json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def build():
    dist=ROOT/'dist'
    if dist.exists():shutil.rmtree(dist)
    shutil.copytree(ROOT/'web',dist);(dist/'data').mkdir()
    for name in ['journals','rules','clinical-journals','clinical-rules']:shutil.copy(ROOT/f'config/{name}.json',dist/f'data/{name}.json')
    for radar,article_file,status_file in [('basic','articles','status'),('clinical','clinical-articles','clinical-status')]:
        rows=json.loads((ROOT/f'data/{article_file}.json').read_text());retained=len(rows)
        if radar=='basic':rows+=json.loads((ROOT/'data/transfer-candidates.json').read_text())
        rows.sort(key=lambda p:p['date'],reverse=True);folder=dist/'data'/radar;folder.mkdir();chunks=[]
        for i in range(0,len(rows),100):
            page=rows[i:i+100];file=f'page-{i//100+1:04d}.json';(folder/file).write_text(json.dumps(page,ensure_ascii=False,separators=(',',':')))
            chunks.append({'file':file,'start':min(p['date'] for p in page),'end':max(p['date'] for p in page),'count':len(page)})
        (folder/'manifest.json').write_text(json.dumps({'radar':radar,'retainedCount':retained,'displayCount':len(rows),'chunks':chunks},ensure_ascii=False))
        shutil.copy(ROOT/f'data/{status_file}.json',dist/f'data/{status_file}.json')
    (dist/'.nojekyll').touch();print('Production ready: fixed-size public shards (≤100 records); raw index and backup excluded.')
if __name__=='__main__':build()
