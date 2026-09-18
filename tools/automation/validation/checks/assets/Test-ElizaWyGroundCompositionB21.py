#!/usr/bin/env python3
"""B21 source-pixel composition checks. Runs without source mount or Pillow."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[5]
SCRIPT = ROOT / 'tools/automation/assets/Build-ElizaWyGroundCompositionB21.py'
spec = importlib.util.spec_from_file_location('havenwild_elizawy_b21', SCRIPT)
b21 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = b21
spec.loader.exec_module(b21)
CFG = json.loads((ROOT / b21.ROOT_REL_CONFIG).read_text(encoding='utf-8'))


def fake_contract():
    digests={f'Terrain/terrain_{s}.png':s*64 for s in b21.SEASONS}
    cells=[];masters=[]
    for y in range(26):
        for x in range(16):
            bindings={s:{'sourcePath':f'Terrain/terrain_{s}.png','sourceSha256':digests[f'Terrain/terrain_{s}.png'],
                         'sourceRect':[x*32,y*32,32,32],'sourceCellId':f'id-{s}-{x}-{y}'} for s in b21.SEASONS}
            rid='unused-region'
            for r in CFG['repeatableSurfaces']:
                if r['canonicalCell']==[x,y]:rid=r['expectedRegion']
            key=f'canon-{x}-{y}'
            cells.append({'column':x,'row':y,'canonicalId':key,'sourceRegionId':rid,'seasonBindings':bindings})
            masters.append({'column':x,'row':y,'canonicalId':key,'seasonBindings':bindings})
    regions=[]
    for r in CFG['resizeExperiments']:
        regions.append({'regionId':r['expectedRegion'],'rectCells':r['rectCells'],'paintApproved':False})
    regions.extend({'regionId':f'filler-{i}'} for i in range(45))
    b19={'schema':'havenwild.elizawy_master_ground_layout_generated.b19','sourceCommit':b21.PIN,
         'geometry':{'canonicalCells':416,'seasonSourceBindings':2080},'masterCells':masters,
         'blockers':[],'productionApproval':False,'runtimeCutover':False}
    b20={'schema':'havenwild.elizawy_source_region_coverage_generated.b20','sourceCommit':b21.PIN,
         'status':'CANONICAL_SOURCE_REGIONS_COVERED_SEMANTICS_UNAPPROVED','geometry':{'regionSlots':416,'regions':47},
         'cells':cells,'regions':regions,'sourceSha256':digests,'blockers':[],
         'runtimeCutover':False,'productionApproval':False}
    rgba=b'\x22\x44\x66\xff'*(512*832)
    sources={s:(512,832,rgba) for s in b21.SEASONS}
    return b19,b20,sources,digests


class SurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.master,cls.regions,cls.images,cls.digests=fake_contract()

    def verify(self,cfg=None,master=None,regions=None,images=None,digests=None):
        return b21.validate(cfg or copy.deepcopy(CFG), master or self.master,regions or self.regions,
                            images or self.images,digests or self.digests)

    def test_synthetic_valid_layout(self):
        report=self.verify()
        self.assertEqual(report['blockers'],[])
        self.assertEqual(report['geometry']['seasonalRepeatBindings'],15)
        self.assertFalse(report['runtimeCutover'])
        self.assertFalse(report['productionApproval'])
        self.assertTrue(all(s['sourcePixelRepeatVerified'] for s in report['surfaces']))
        self.assertEqual(len(report['resizeExperiments']),2)

    def test_rgba_exact_edges(self):
        tile=b'\x00\x0a\x0b\xff'*(32*32)
        self.assertEqual(b21.edge_mismatch(tile),{'horizontalPixels':0,'verticalPixels':0,'fullyOpaque':True})

    def test_tampered_water_edge_rejected(self):
        images=copy.deepcopy(self.images)
        width,height,rgba=images['summer'];pixels=bytearray(rgba)
        index=(17*32*width+12*32)*4
        pixels[index]=255
        images['summer']=(width,height,bytes(pixels))
        self.assertIn('not exactly repeatable/opaque: ground.water.base.visual/summer',self.verify(images=images)['blockers'])

    def test_transparent_source_rejected(self):
        images=copy.deepcopy(self.images);w,h,p=images['spring'];pixels=bytearray(p)
        index=(1*32*w+4*32)*4+3;pixels[index]=0
        images['spring']=(w,h,bytes(pixels))
        self.assertIn('not exactly repeatable/opaque: ground.grass.base/spring',self.verify(images=images)['blockers'])

    def test_hash_mismatch_rejected(self):
        digests=copy.deepcopy(self.digests);digests['Terrain/terrain_summer.png']='tampered'
        self.assertTrue(any('source hash' in e for e in self.verify(digests=digests)['blockers']))

    def test_canonical_coordinate_change_rejected(self):
        cfg=copy.deepcopy(CFG);cfg['repeatableSurfaces'][0]['canonicalCell']=[4,2]
        self.assertTrue(any('unsafe relabeling' in e for e in self.verify(cfg=cfg)['blockers']))

    def test_water_relabel_grass_rejected(self):
        cfg=copy.deepcopy(CFG);cfg['repeatableSurfaces'][0]['visualMaterial']='open_water_appearance'
        self.assertTrue(any('unsafe relabeling' in e for e in self.verify(cfg=cfg)['blockers']))

    def test_duplicate_surface_id_rejected(self):
        cfg=copy.deepcopy(CFG);cfg['repeatableSurfaces'][1]['id']=cfg['repeatableSurfaces'][0]['id']
        self.assertTrue(any('duplicates' in e for e in self.verify(cfg=cfg)['blockers']))

    def test_runtime_policy_cannot_be_enabled(self):
        cfg=copy.deepcopy(CFG);cfg['safety']['editorRuntimeBindings']=True
        self.assertTrue(any('safety policy' in e for e in self.verify(cfg=cfg)['blockers']))

    def test_existing_b20_must_stay_unapproved(self):
        b20=copy.deepcopy(self.regions);b20['runtimeCutover']=True
        self.assertTrue(any('B20 complete' in e for e in self.verify(regions=b20)['blockers']))

    def test_unverified_assembly_rejected(self):
        cfg=copy.deepcopy(CFG);cfg['resizeExperiments'][0]['rectCells']=[1,0,3,3]
        self.assertTrue(any('changed exact source assembly' in e for e in self.verify(cfg=cfg)['blockers']))

    def test_assembly_preview_not_approved(self):
        report=self.verify()
        self.assertEqual(report['approvedResizes'],0)
        self.assertTrue(all(not r['resizeApproved'] for r in report['resizeExperiments']))
        self.assertFalse(any(r['topologyApproved'] for r in report['resizeExperiments']))

    def test_nine_slice_3x3_original(self):
        self.assertEqual(b21.nine_grid([2,4,3,3],3,3), [[(x,y) for x in range(2,5)] for y in range(4,7)])

    def test_nine_slice_7x5_repeats_only_middle(self):
        grid=b21.nine_grid([0,10,3,3],7,5)
        self.assertEqual(grid[0],[(0,10)]+[(1,10)]*5+[(2,10)])
        self.assertEqual(grid[2][3],(1,11))
        self.assertEqual(grid[-1][-1],(2,12))

    def test_png_roundtrip_via_b19_decoder_when_present(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/'preview.png'
            b21.write_rgba_png(p,32,32,b'\x10\x20\x30\xff'*1024)
            # check exact PNG structure even if the prior decoder is not available in a synthetic test
            data=p.read_bytes();self.assertTrue(data.startswith(b'\x89PNG\r\n\x1a\n'))
            self.assertEqual(struct.unpack_from('>II',data,16),(32,32))
            if (ROOT/'tools/automation/assets/Build-ElizaWyMasterGroundB19.py').is_file():
                self.assertEqual(b21.load_b19(ROOT).rgba_png(p), (32,32,b'\x10\x20\x30\xff'*1024))

    def test_preview_repeat_composition(self):
        rgba=b'\xa0\x70\x20\xff'*(32*32)
        image=(32,32,rgba)
        self.assertEqual(b21.compose(image,[[(0,0)]*4 for _ in range(3)]),(128,96,rgba[:128]*0 + b''.join((rgba[row*128:(row+1)*128]*4) for _ in range(3) for row in range(32))))

    def test_repeat_seams_zero_for_uniform_assembly(self):
        e=b21.repeated_seams(next(iter(self.images.values())),[0,10,3,3],7,5)
        self.assertEqual(e['repeatedContacts'],34)
        self.assertEqual(e['horizontalMismatchedEdgePixels'],0)
        self.assertEqual(e['verticalMismatchedEdgePixels'],0)
        self.assertFalse(e['resizeApproved'])

    def test_strict_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            for bad in ('../outside','/tmp/test','', './nested/../../escape'):
                with self.assertRaises(ValueError):b21.safe(Path(temp),bad)


if __name__=='__main__': unittest.main()
