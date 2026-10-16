import unittest
from unittest.mock import patch
from scripts import radar as r

class MetadataTests(unittest.TestCase):
    def test_doi_normalization(self):
        self.assertEqual(r.doi('HTTPS://doi.org/10.1234/ABC '),'10.1234/abc')
        self.assertEqual(r.doi('doi: 10.1234/ABC'),'10.1234/abc')
    def test_jats_clean(self):
        self.assertEqual(r.clean('<jats:p>A &amp; B</jats:p>'),'A & B')
    def test_dates(self):
        self.assertEqual(r.date_parts({'date-parts':[[2026,9]]}),'2026-09-01')
        self.assertIsNone(r.date_parts({'date-parts':[[2026,13,1]]}))
    def test_merge_enrichment(self):
        j={'id':'bone-research','name':'Bone Research'}
        a=r.record(j,'Bone formation','', '2026-09-22','10.1/ABC','Crossref','x')
        b=r.record(j,'Bone formation','Osteoblast signaling drives bone formation.', '2026-09-20','10.1/abc','Europe PMC','y')
        merged=r.merge([a],[b]); self.assertEqual(len(merged),1)
        self.assertEqual(set(merged[0]['sources']),{'Crossref','Europe PMC'})
        self.assertTrue(merged[0]['abstract']); self.assertEqual(merged[0]['date'],'2026-09-20')
    def test_specific_bone_mechanism(self):
        c=r.classify({'title':'Osteoblast and osteoclast signaling regulates bone formation','abstract':'Osteocyte differentiation controls bone remodeling.'})
        self.assertEqual(c['grade'],'A'); self.assertFalse(c['pending'])
    def test_generic_inflammation_is_not_recommended(self):
        c=r.classify({'title':'Macrophage inflammation and cytokine signaling','abstract':'Immune cells in lung disease respond to nanoparticles.'})
        self.assertEqual(c['grade'],'C')
    def test_nano_does_not_imply_relevance(self):
        self.assertEqual(r.classify({'title':'DNA nanomaterials for drug delivery','abstract':'Nanoparticles deliver therapeutics.'})['grade'],'C')
    def test_missing_abstract_not_A(self):
        c=r.classify({'title':'Osteoblast osteoclast osteogenesis bone remodeling signaling','abstract':''})
        self.assertNotEqual(c['grade'],'A');self.assertTrue(c['pending'])
    def test_stem_only_pending(self):
        c=r.classify({'title':'Stem cell tissue repair','abstract':'A new stem cell lineage mechanism.'})
        self.assertTrue(c['pending']);self.assertNotEqual(c['grade'],'A')
    def test_epmc_pagination_and_issn_rejection(self):
        j={'id':'nature','name':'Nature','issns':['0028-0836']}
        row={'id':'1','title':'Bone formation','firstPublicationDate':'2026-09-20','journalInfo':{'journal':{'issn':'0028-0836'}}}
        bad={**row,'id':'2','journalInfo':{'journal':{'issn':'0000-0000'}}}
        with patch.object(r,'get',side_effect=[{'resultList':{'result':[row,bad]},'nextCursorMark':'page2'},{'resultList':{'result':[]}}]) as mock:
            rows,meta=r.fetch_epmc(j,'2026-09-16','2026-10-16')
            self.assertEqual(len(rows),1);self.assertEqual(meta['rejected'],1);self.assertEqual(mock.call_count,2)
    def test_crossref_issn_and_date_guard(self):
        j={'id':'nature','name':'Nature','issns':['0028-0836']}
        base={'title':['title'],'DOI':'10.1/xyz','ISSN':['0028-0836'],'published-online':{'date-parts':[[2026,9,20]]}}
        with patch.object(r,'get',return_value={'message':{'items':[base,{**base,'ISSN':['0000-0000']},{**base,'published-online':{'date-parts':[[2025,1,1]]}}]}}):
            rows,meta=r.fetch_crossref(j,'2026-09-16','2026-10-16');self.assertEqual(len(rows),1);self.assertEqual(meta['rejected'],1)
    def test_http_retry_and_cache(self):
        import io,tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d, patch.object(r,'ROOT',Path(d)), patch.object(r,'time') as clock, patch.object(r,'urlopen',side_effect=[OSError('temporary'),io.BytesIO(b'{"ok":true}')]) as request:
            clock.time.return_value=0
            self.assertEqual(r.get('https://example.com'),{'ok':True});self.assertEqual(request.call_count,2)
            self.assertEqual(r.get('https://example.com'),{'ok':True});self.assertEqual(request.call_count,2)

if __name__=='__main__':unittest.main()

class NoticeTests(unittest.TestCase):
    def test_correction_is_archive(self):
        self.assertEqual(r.classify({'title':'Author Correction: Osteoblast osteoclast bone remodeling signaling','abstract':'Osteogenesis and bone regeneration pathways.'})['grade'],'C')
    def test_crossref_queries_all_issns(self):
        j={'id':'nature','name':'Nature','issns':['0028-0836','1476-4687']}
        with patch.object(r,'_fetch_crossref_issn',return_value=([],{'rejected':0})) as mock:
            r.fetch_crossref(j,'2026-09-16','2026-10-16'); self.assertEqual(mock.call_count,2)
            self.assertEqual(mock.call_args_list[1].args[0]['issns'][0],'1476-4687')

class MarrowSpecificityTests(unittest.TestCase):
    def test_generic_bone_marrow_immune_not_high(self):
        p={'title':'Stem cell single-cell bone marrow niche','abstract':'Macrophage immune signaling regulates lineage differentiation in the bone marrow niche.'}
        c=r.classify(p);self.assertNotEqual(c['grade'],'A');self.assertTrue(c['pending'])
    def test_encoded_tags_cleaned(self):
        self.assertEqual(r.clean('Ctsk&lt;sup&gt;+&lt;/sup&gt;'),'Ctsk +')
