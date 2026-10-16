"""Real API smoke test in an isolated copy; never activates the release checkout."""
import json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='radar-smoke-') as directory:
    tmp=Path(directory)
    for name in ['scripts','config','data']:shutil.copytree(ROOT/name,tmp/name)
    if (ROOT/'.cache').exists():shutil.copytree(ROOT/'.cache',tmp/'.cache')
    # Reuse previously fetched public responses when still within TTL.
    for cache in (ROOT.parent/'.cache').glob('*.json'):
        dest=tmp/'.cache'/cache.name;dest.parent.mkdir(exist_ok=True)
        if not dest.exists():shutil.copy2(cache,dest)
    subprocess.run([sys.executable,'scripts/activate_v2.py'],cwd=tmp,check=True)
    report={'isolation':'temporary checkout; release lifecycle not activated','runs':[]}
    for radar in ['basic','clinical']:
        command=[sys.executable,'scripts/radar.py','--radar',radar]
        result=subprocess.run(command,cwd=tmp,capture_output=True,text=True)
        (ROOT/f'reports/v2-smoke-{radar}.log').write_text(result.stdout+result.stderr)
        name='status' if radar=='basic' else 'clinical-status';status=json.loads((tmp/f'data/{name}.json').read_text())
        report['runs'].append({'radar':radar,'exitCode':result.returncode,'fetchOk':status['fetchOk'],'retained':status['total'],'new':status['newCount'],'journalsOk':sum(j['ok'] for j in status['journals'])})
        if result.returncode:raise RuntimeError(f'{radar} API smoke test incomplete; see log')
    seedids=set(json.loads((ROOT/'data/lifecycle.json').read_text())['seedIds']);current=json.loads((tmp/'data/articles.json').read_text());assert seedids<={p['id'] for p in current}
    assert all(p['grade'] in ['A','B'] for p in current)
    report['original16Preserved']=True
    (ROOT/'reports/v2-collection-smoke.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
