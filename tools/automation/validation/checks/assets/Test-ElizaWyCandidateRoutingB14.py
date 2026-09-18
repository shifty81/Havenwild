#!/usr/bin/env python3
"""B14 new-authoring provider and catalog quarantine fixture tests."""
from __future__ import annotations
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
SCRIPT=ROOT/'tools/automation/assets/Audit-ElizaWyCandidateRoutingB14.py'
spec=importlib.util.spec_from_file_location('b14_candidate_router',SCRIPT)
assert spec and spec.loader
b14=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=b14
spec.loader.exec_module(b14)

class CandidateRoutingTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix='havenwild-b14-')
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        for name in (b14.AUTH,b14.FOUND,b14.COVER,b14.EDITOR,b14.LIBRARY,b14.CANDIDATE,b14.FAMILY):
            file=self.root/name
            file.parent.mkdir(parents=True,exist_ok=True)
            file.write_bytes((ROOT/name).read_bytes())

    def edit(self,rel,fn):
        p=self.root/rel
        obj=json.loads(p.read_text(encoding='utf8'))
        fn(obj)
        p.write_text(json.dumps(obj),encoding='utf8')

    def report(self,good=True):
        p=self.root/b14.REPORT;p.parent.mkdir(parents=True,exist_ok=True)
        (self.root/'assets/source/licensed/lpc_revised').mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps({'status':'SOURCE_REPRODUCED_WITH_QUARANTINE' if good else 'BLOCKED',
            'pinnedCommit':b14.PIN, 'source':{'verificationDepth':'full_file_hashes','verifiedFiles':len(b14.DOMAINS),
             'missingIndexed':0,'mismatchedIndexed':0,'unexpectedFiles':0,'invalidImages':0},
            'historicalInventory':{'indexedFiles':len(b14.DOMAINS)},'quarantinedAssets':[{'relativePath':'Characters/broken.png'}],
            'blockers':[] if good else ['missing'], 'productionApproval':False}),encoding='utf8')

    def catalogs(self,uncertified=True):
        for domain in b14.DOMAINS:
            p=self.root/b14.CATALOG/f'{domain}.json';p.parent.mkdir(parents=True,exist_ok=True)
            rec={'candidateProvider':'elizawy_lpc_revised','productionApproved':not uncertified,
                 'sourceKind':'image' if domain == 'characters' else 'documentation',
                 'sourceSizeBytes':0,'sourcePath':'Characters/broken.png' if domain == 'characters' else domain + '/Credits.txt',
                 'productionState':'QUARANTINED' if domain == 'characters' else 'SOURCE_ONLY_UNMAPPED'}
            p.write_text(json.dumps({'newAuthoringProvider':'elizawy_lpc_revised',
                'productionApprovedRecordCount':0,'sourceCommit':b14.PIN,'recordCount':1,'records':[rec]}),encoding='utf8')

    def test_staged_without_optional_local_evidence(self):
        r=b14.validate(self.root)
        self.assertEqual(r['status'],'POLICY_STAGED_NOT_RUNTIME_ACTIVE')
        self.assertFalse(r['runtimeCutover'])
        self.assertFalse(r['productionApproval'])

    def test_requires_full_index_when_requested(self):
        self.assertEqual(b14.validate(self.root,True)['status'],'BLOCKED')
        self.report(good=False)
        self.assertEqual(b14.validate(self.root,True)['status'],'BLOCKED')

    def test_verified_candidate_catalogs_not_production(self):
        self.report()
        self.catalogs()
        r=b14.validate(self.root,True)
        self.assertEqual(r['status'],'SOURCE_ONLY_CANDIDATE_CATALOGS_VERIFIED')
        self.assertFalse(r['productionApproval'])
        self.assertFalse(r['runtimeCutover'])

    def test_non_elizawy_provider_fails(self):
        self.edit(b14.EDITOR,lambda d:d['providers'].append('universal_lpc_character_generator'))
        self.assertIn('editor source-library provider selection is mixed',b14.validate(self.root)['blockers'])

    def test_premature_runtime_activation_fails(self):
        self.edit(b14.CANDIDATE,lambda d:d['activation'].update(enabled=True))
        self.assertEqual(b14.validate(self.root)['status'],'BLOCKED')

    def test_unreviewed_promotion_fails(self):
        self.edit(b14.LIBRARY,lambda d:d['collections'][0].update(allowRuntimePromotion=True))
        self.assertEqual(b14.validate(self.root)['status'],'BLOCKED')

    def test_catalog_false_promotion_fails(self):
        self.report();self.catalogs(uncertified=False)
        self.assertEqual(b14.validate(self.root,True)['status'],'BLOCKED')

    def test_quarantine_required(self):
        self.report();self.catalogs()
        p=self.root/b14.CATALOG/'characters.json'
        data=json.loads(p.read_text());data['records'][0]['productionState']='SOURCE_ONLY_UNMAPPED'
        p.write_text(json.dumps(data))
        self.assertEqual(b14.validate(self.root,True)['status'],'BLOCKED')

    def test_builder_marks_empty_png_quarantined(self):
        p=ROOT/'tools/automation/assets/Build-ElizaWyProjectAssetAuditV167Z38.py'
        sp=importlib.util.spec_from_file_location('b14_original_catalog_builder',p)
        m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m)
        source=self.root/'mocksource';bad=source/'Characters/broken.png'
        bad.parent.mkdir(parents=True);bad.write_bytes(b'')
        authority={'domains':[{'id':'characters','sourcePrefixes':['Characters/'],
                                 'catalog':'WORKSPACE/generated/lpc/catalogs/characters.json'}]}
        item=m.build_record(bad,source,authority,{},False)
        self.assertEqual(item['productionState'],'QUARANTINED')
        self.assertFalse(item['productionApproved'])
        good=bad.with_name('good.png')
        good.write_bytes(b'\x89PNG\r\n\x1a\n'+b'\0\0\0\rIHDR'+(32).to_bytes(4,'big')*2)
        item=m.build_record(good,source,authority,{},False)
        self.assertEqual(item['productionState'],'SOURCE_ONLY_UNMAPPED')

if __name__=='__main__': unittest.main()
