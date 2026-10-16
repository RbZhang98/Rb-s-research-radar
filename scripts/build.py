import json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def build():
    for f in ['articles','status']:
        json.loads((ROOT/f'data/{f}.json').read_text())
    dist=ROOT/'dist'
    if dist.exists(): shutil.rmtree(dist)
    shutil.copytree(ROOT/'web',dist)
    shutil.copytree(ROOT/'data',dist/'data')
    for f in ['journals','rules']: shutil.copy(ROOT/f'config/{f}.json',dist/f'data/{f}.json')
    (dist/'.nojekyll').touch()
    print('Production build ready: dist/')
if __name__=='__main__': build()
