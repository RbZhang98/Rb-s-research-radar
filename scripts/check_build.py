"""Static production integrity check; does not claim browser QA."""
import json,re
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Page(HTMLParser):
    def __init__(self):super().__init__();self.ids=set();self.refs=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if 'id' in d:self.ids.add(d['id'])
        for key in ('href','src'):
            if d.get(key,'').startswith('./'):self.refs.append(d[key])
def check():
    d=ROOT/'dist';page=Page();page.feed((d/'index.html').read_text())
    for ref in page.refs:assert (d/ref).is_file(),ref
    js=(d/'app.js').read_text()
    for id_ in re.findall(r"\$\('#([a-zA-Z]+)'\)",js):assert id_ in page.ids,id_
    papers=json.loads((d/'data/articles.json').read_text());status=json.loads((d/'data/status.json').read_text())
    assert len(papers)==len({p['id'] for p in papers})
    assert len({p['doi'] for p in papers if p['doi']})==sum(bool(p['doi']) for p in papers)
    names={j['id']:j['name'] for j in json.loads((d/'data/journals.json').read_text())}
    assert len(status['journals'])==len(names)
    for p in papers:
        assert p['journal']==names[p['journalId']]
        assert p['title'] and p['date'] and p['sources'] and p['url'].startswith('https://')
        assert p['grade'] in ['A','B','C'] and (p['grade']!='A' or p['abstract'])
        assert '中文总结' not in p
    assert (d/'filter.js').is_file() and (d/'.nojekyll').is_file()
    print(f'Production integrity PASS: {len(papers)} records, {len(names)} journals; assets, DOM IDs, DOI uniqueness, metadata fields and grade safeguards valid.')
if __name__=='__main__':check()
