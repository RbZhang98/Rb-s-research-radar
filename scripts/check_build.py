"""Public artifact and migration integrity; no private data, no browser claims."""
import json,re
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Page(HTMLParser):
 def __init__(self):super().__init__();self.ids=set();self.refs=[]
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if 'id' in d:self.ids.add(d['id'])
  for key in ['href','src']:
   if d.get(key,'').startswith('./'):self.refs.append(d[key])
def check():
 d=ROOT/'dist';page=Page();page.feed((d/'index.html').read_text())
 for ref in page.refs:assert (d/ref).is_file(),ref
 for js in d.glob('*.js'):
  for ref in re.findall(r"from ['\"](\./[^'\"]+)['\"]",js.read_text()):assert (d/ref).is_file(),ref
  if js.name=='app.js':
   for id_ in re.findall(r"\$\('#([a-zA-Z]+)'\)",js.read_text()):assert id_ in page.ids,id_
 assert not list(d.rglob('*seen*')) and not (d/'backups').exists() and not (d/'data/lifecycle.json').exists()
 for radar,source in [('basic','articles'),('clinical','clinical-articles')]:
  manifest=json.loads((d/f'data/{radar}/manifest.json').read_text());rows=[]
  for chunk in manifest['chunks']:
   p=json.loads((d/f'data/{radar}'/chunk['file']).read_text());assert len(p)<=100;rows+=p
  assert len(rows)==len({p['id'] for p in rows})
  source_rows=json.loads((ROOT/f'data/{source}.json').read_text());assert {p['id'] for p in source_rows}<={p['id'] for p in rows}
  config='journals' if radar=='basic' else 'clinical-journals';names={j['id']:j['name'] for j in json.loads((d/f'data/{config}.json').read_text())}
  for p in rows:assert p['journal']==names[p['journalId']] and p['title'] and p['url'].startswith('https://')
  print(f'{radar}: {len(source_rows)} retained, {len(rows)} display rows; fixed shards and valid source names.')
 print('PASS: relative assets, DOM IDs, bounded shards, unique DOI records; dedup index and old snapshot excluded from Pages.')
if __name__=='__main__':check()
