"""Production first-run activation, idempotent. Not executed in PR CI."""
import datetime as dt
try: from scripts.radar import read,write
except ModuleNotFoundError: from radar import read,write
state=read('data/lifecycle.json')
if not state:raise RuntimeError('Run migration before activation')
if not state.get('launchDate'):
    state['launchDate']=dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).date().isoformat()
    state['activatedAt']=dt.datetime.now(dt.timezone.utc).isoformat();write('data/lifecycle.json',state)
print('V2 production accumulation begins:',state['launchDate'])
