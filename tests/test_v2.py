import copy,gzip,hashlib,json,unittest
from pathlib import Path
from scripts.radar import authors_crossref,authors_epmc,add_metadata,merge,classify,record,read
from scripts.clinical import classify_clinical
from scripts.lifecycle import retain
ROOT=Path(__file__).resolve().parents[1]
class MigrationTests(unittest.TestCase):
 def test_exact_original_seeds_preserved(self):
  state=read('data/lifecycle.json');raw=gzip.decompress((ROOT/state['backup']).read_bytes());old=json.loads(raw);seeds={p['id']:p for p in old if p['grade']=='A'};current={p['id']:p for p in read('data/articles.json')}
  self.assertEqual(hashlib.sha256(raw).hexdigest(),state['snapshotSHA256']);self.assertEqual(len(seeds),16)
  for id_,p in seeds.items():
   for f in ['doi','title','abstract','journal','date']:self.assertEqual(p[f],current[id_][f])
   self.assertEqual(current[id_]['legacyRecommendation']['grade'],'A')
  if not state.get('launchDate'):self.assertEqual(set(current),set(seeds))
 def test_no_deleted_legacy_reentry(self):
  old={'id':'10.1/old','doi':'10.1/old','date':'2026-10-14','title':'Bone formation','abstract':'Bone','grade':'A'}
  history,index,new,_=retain([], [old],{'10.1/old':{'legacy':True,'firstSeenAt':None}},radar='basic',now='2026-10-16T12:00:00+00:00',launch_date='2026-10-16')
  self.assertEqual(history,[]);self.assertEqual(new,[])
 def test_explicit_rediscovery_is_not_new(self):
  p={'id':'10.1/old','date':'2026-10-01','grade':'B'}
  h,_,new,_=retain([],[p],{'10.1/old':{'legacy':True}},radar='basic',now='2026-10-16T12:00:00+00:00',launch_date='2026-10-16',rediscover_legacy=True)
  self.assertEqual(h[0]['discoveryKind'],'historical-rediscovery');self.assertFalse(new)
 def test_new_and_repeat_and_low_retention(self):
  raw=[{'id':'a','date':'2026-10-16','grade':'A'},{'id':'b','date':'2026-10-16','grade':'C'}]
  h,index,new,_=retain([],raw,{},radar='basic',now='2026-10-16T12:00:00+00:00',launch_date='2026-10-16');self.assertEqual(new,['a']);self.assertEqual(len(h),1);self.assertEqual(len(index),2)
  h,index,new,_=retain(h,raw,index,radar='basic',now='2026-10-16T13:00:00+00:00',launch_date='2026-10-16');self.assertEqual(new,[]);self.assertEqual(len(h),1)
 def test_clinical_launch_and_all_grades(self):
  raw=[{'id':'old','date':'2026-10-15','grade':'A'},{'id':'new','date':'2026-10-16','grade':'C','studyType':'临床前研究'}]
  h,_,new,_=retain([],raw,{},radar='clinical',now='2026-10-16T12:00:00+00:00',launch_date='2026-10-16');self.assertEqual([x['id'] for x in h],['new']);self.assertEqual(new,['new'])
 def test_transfer_candidate_not_longterm(self):
  raw=[{'id':'t','date':'2026-10-16','grade':'C','inspirationScore':3}];now='2026-10-16T12:00:00+00:00'
  h,index,new,c=retain([],raw,{},radar='basic',now=now,launch_date='2026-10-16');self.assertFalse(h);self.assertEqual(c[0]['temporary'],True)
  h,index,new,c=retain([],raw,index,radar='basic',now='2026-11-02T12:00:00+00:00',launch_date='2026-10-16');self.assertFalse(c)
class EvidenceTests(unittest.TestCase):
 def test_crossref_author_links_not_inferred(self):
  a=authors_crossref({'author':[{'given':'Jane','family':'Doe','affiliation':[{'name':'University A'}]},{'family':'Smith'}]})
  self.assertEqual(a[0]['affiliations'],['University A']);self.assertEqual(a[1]['affiliations'],[])
 def test_epmc_affiliation_relation(self):
  a=authors_epmc({'authorList':{'author':[{'fullName':'Jane Doe','authorAffiliationDetailsList':{'authorAffiliation':[{'affiliation':'Department X'}]}},{'fullName':'Other'}]}})
  self.assertEqual(a[0]['affiliations'],['Department X']);self.assertEqual(a[1]['affiliations'],[])
 def test_same_doi_clinical_does_not_mutate_basic(self):
  p={'id':'10.1/x','title':'Macrophages in a randomized controlled trial','abstract':'Lung inflammation.','date':'2026-10-16','sources':['Crossref'],'sourceIds':{},'doi':'10.1/x'}
  basic=merge([],[copy.deepcopy(p)]);original=copy.deepcopy(basic);clinical=merge([],[copy.deepcopy(p)],classify_clinical);self.assertEqual(basic,original);self.assertNotEqual(clinical[0]['grade'],basic[0]['grade'])
 def test_transfer_not_bone_proof(self):
  c=classify({'title':'Ligand spacing and receptor clustering regulate cell fate','abstract':'Substrate stiffness controls YAP/TAZ and Piezo1.'});self.assertEqual(c['grade'],'C');self.assertGreater(c['inspirationScore'],1);self.assertIn('未验证',c['evidenceScope'])
 def test_fak_not_fake(self):
  c=classify({'title':'A fake signal','abstract':'No physical mechanism'});self.assertNotIn('FAK',c['transferMechanisms'])
 def test_rct_and_review_types(self):
  p={'title':'A randomized controlled trial of dental implants','abstract':'Patients randomized to two groups.','publicationTypes':['Randomized Controlled Trial']}
  c=classify_clinical(p);self.assertEqual(c['grade'],'A');self.assertFalse(c['pending']);self.assertEqual(classify_clinical({'title':'Narrative review of implants','abstract':'','publicationTypes':['Review']})['grade'],'B')
