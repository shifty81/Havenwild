#!/usr/bin/env python3
"""Regression tests for B20 full-sheet source-region coverage and fail-closed policy."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[5]
SOURCE=ROOT/'tools/automation/assets/Build-ElizaWyGroundRegionsB20.py'
loader=importlib.util.spec_from_file_location('hw_elizawy_b20',SOURCE)
mod=importlib.util.module_from_spec(loader)
loader.loader.exec_module(mod)
CFG=ROOT/'content/worldgen/elizawy_ground_regions_b20.json'


def fixture():
    cfg=json.loads(CFG.read_text(encoding='utf-8'))
    blanks=set()
    for region in cfg['regions']:
        if region['classification']=='source_blank':
            x,y,w,h=region['rectCells']
            blanks.update((c,r) for r in range(y,y+h) for c in range(x,x+w))
    cells=[]
    for r in range(26):
        for c in range(16):
            group=None
            if (c,r)==(13,16):group='ground.water.surface.visual'
            if (c,r)==(13,23):group='ground.water.dark.visual'
            cells.append({'canonicalId':f'elizawy.ground.master.c{c:02d}.r{r:02d}',
                          'column':c,'row':r,'canonicalRectPixels':[c*32,r*32,32,32],
                          'alphaEvidenceSummer':{'type':'EMPTY' if (c,r) in blanks else 'OPAQUE','opaquePixels':0 if (c,r) in blanks else 1024},
                          'sourceGroupCandidate':group,'seasonOverrides':[],
                          'paintApproved':False,'runtimeApproved':False,'collisionApproved':False,
                          'seasonBindings':{s:{'sourcePath':f'Terrain/terrain_{s}.png',
                                               'sourceSha256':s*64,'sourceRect':[c*32,r*32,32,32],
                                               'sourceCellId':f'fixture.{s}.{c}.{r}'} for s in mod.SEASONS}})
    groups=[{'candidateId':f'fixture.group.{i}','resizeMode':'NOT_INDEPENDENT_WATER_FILL'} for i in range(8)]
    groups.extend([{'candidateId':'ground.water.surface.visual','resizeMode':'NOT_INDEPENDENT_WATER_FILL'},
                   {'candidateId':'ground.water.dark.visual','resizeMode':'NOT_INDEPENDENT_WATER_FILL'}])
    b19={'schema':'havenwild.elizawy_master_ground_layout_generated.b19',
         'sourceCommit':mod.PIN,'sourceProvider':'elizawy_lpc_revised',
         'canonicalSource':'Terrain/terrain_summer.png','blockers':[],
         'geometry':{'canonicalCells':416,'seasonSourceBindings':2080},
         'approvedSemanticMappings':0,'approvedTopologyRules':0,'runtimeBindingsPublished':0,
         'productionApproval':False,'runtimeCutover':False,'masterCells':cells,'candidateGroups':groups}
    hashes={f'Terrain/terrain_{s}.png':s*64 for s in mod.SEASONS}
    return cfg,b19,hashes


class B20Tests(unittest.TestCase):
    def run_check(self,edit=None):
        cfg,b19,hashes=fixture()
        if edit:edit(cfg,b19,hashes)
        return mod.validate(cfg,b19,hashes)

    def test_exhaustive_one_authority_all_cells(self):
        out=self.run_check()
        self.assertFalse(out['blockers'],out['blockers'])
        self.assertEqual(out['status'],'CANONICAL_SOURCE_REGIONS_COVERED_SEMANTICS_UNAPPROVED')
        self.assertEqual(out['geometry']['regionSlots'],416)
        self.assertEqual(out['geometry']['unassignedRegionCells'],0)
        self.assertEqual(out['geometry']['seasonBindings'],2080)
        self.assertEqual(out['geometry']['regions'],47)
        self.assertFalse(out['runtimeCutover'])
        self.assertEqual(out['approvedSemanticMappings'],0)

    def test_reject_overlap(self):
        out=self.run_check(lambda cfg,b,h:cfg['regions'].append(copy.deepcopy(cfg['regions'][0])))
        self.assertTrue(any('duplicate/empty region' in e or 'overlapping source' in e for e in out['blockers']))

    def test_reject_gap(self):
        out=self.run_check(lambda cfg,b,h:cfg['regions'].pop())
        self.assertTrue(any('unassigned canonical' in e for e in out['blockers']))

    def test_reject_blanks_with_artwork(self):
        def change(cfg,b,h):
            cell=next(c for c in b['masterCells'] if (c['column'],c['row'])==(12,0))
            cell['alphaEvidenceSummer']['type']='OPAQUE'
        out=self.run_check(change)
        self.assertTrue(any('transparent source region' in e for e in out['blockers']))

    def test_reject_artwork_region_without_artwork(self):
        def change(cfg,b,h):
            target=cfg['regions'][0]['rectCells'];x,y,w,hh=target
            for c in b['masterCells']:
                if x<=c['column']<x+w and y<=c['row']<y+hh:
                    c['alphaEvidenceSummer']['type']='EMPTY'
        out=self.run_check(change)
        self.assertTrue(any('source art region actually contains no artwork' in e for e in out['blockers']))

    def test_reject_premature_paint(self):
        out=self.run_check(lambda cfg,b,h:cfg['regions'][0].update(allowPaint=True))
        self.assertTrue(any('unsafe' in e for e in out['blockers']))

    def test_reject_runtime_approval(self):
        out=self.run_check(lambda cfg,b,h:b.update(runtimeCutover=True))
        self.assertTrue(any('B19 must' in e for e in out['blockers']))

    def test_reject_changed_artwork_hash(self):
        out=self.run_check(lambda cfg,b,h:h.update({'Terrain/terrain_summer.png':'a'*64}))
        self.assertTrue(any('original pinned PNG changed' in e for e in out['blockers']))

    def test_reject_season_coordinate_drift(self):
        out=self.run_check(lambda cfg,b,h:b['masterCells'][0]['seasonBindings']['winter'].update(sourceRect=[0,32,32,32]))
        self.assertTrue(any('season binding drift' in e for e in out['blockers']))

    def test_reject_water_fill_regression(self):
        def change(cfg,b,h):
            next(g for g in b['candidateGroups'] if g['candidateId']=='ground.water.dark.visual')['resizeMode']='repeat_fill'
        out=self.run_check(change)
        self.assertTrue(any('reclassified as fill' in e for e in out['blockers']))

    def test_reject_path_traversal(self):
        with self.assertRaises(ValueError):
            mod.safe(ROOT,'../../outside')

    def test_no_runtime_propagation_in_html(self):
        cfg,b19,hashes=fixture()
        out=mod.validate(cfg,b19,hashes)
        html=mod.page(out,ROOT,ROOT/'WORKSPACE/generated/lpc/b20.html')
        self.assertIn('No cells, seams',html)
        self.assertIn('terrain_summer.png',html)
        self.assertIn('winter_ice',html)
        self.assertNotIn('data:image/png;base64',html)


if __name__=='__main__':unittest.main()
