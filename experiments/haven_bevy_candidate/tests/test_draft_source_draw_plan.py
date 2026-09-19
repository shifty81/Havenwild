"""Source-exact DRAFT coordinates only; no image approval, GPU run or PIE claims."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

CANDIDATE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('candidate_draft',CANDIDATE/'tools/draft_source_draw_plan.py')
draft=importlib.util.module_from_spec(spec)
spec.loader.exec_module(draft)

class DraftTests(unittest.TestCase):
    def setUp(self):
        self.source='a'*64;self.fixture='b'*64
        self.mapping={'schema':'havenwild.lpc_terrain_family_mapping.v0_4',
         'source':'assets/source/licensed/lpc_revised/Terrain/terrain_summer.png',
         'cellSize':32,'grid':[16,26],
         'baseTiles':{'grass':{'cells':[[3,1]]},'river_water':{'cells':[[12,16]]},
                      'mud_bank':{'cells':[[3,4]]}}}
        self.map_raw=json.dumps(self.mapping).encode()
        self.bindings={'schema':'havenwild.experimental.manual_draft_role_bindings.v0_1',
           'sourceFamily':'ElizaWy','source':'Terrain/terrain_summer.png',
           'sourceSha256':self.source,'historicalMapping':'content/assets/intake/lpc_terrain_family_mapping_v0_3.json',
           'historicalMappingSha256':draft.sha(self.map_raw),
           'selectionPolicy':'EXPLICIT_FIRST_CELL_ONLY_NO_ADJACENCY_NO_AUTOTILE',
           'roleBindings':[{'sceneRole':role,'historicalBaseTile':tile,'sourceVariantIndex':0}
              for role,tile in [('Grass','grass'),('RiverWater','river_water'),('MudBank','mud_bank')]],
           'reviewStatus':'DRAFT_SOURCE_COORDINATES_NOT_VISUALLY_APPROVED','sourceArtApproval':False,
           'worldRendererParity':False,'runtimePublicationAllowed':False}
        self.semantic={'schema':'havenwild.experimental.semantic_scene_plan.v0_1',
           'status':'SEMANTIC_DEBUG_ONLY_NOT_RENDERER_PARITY','originalSourceSha256':self.source,
           'sceneSha256':self.fixture,'sceneId':'terrain_acceptance_river','sizeTiles':[40,28],
           'semanticCellCount':1120,'unmappedCellCount':1120,'approvedDrawCallCount':0,
           'sourceExactArtApproved':False,'worldRendererParity':False,'pieCertified':False,
           'cells':[{'x':i%40,'y':i//40,'terrainRole':['Grass','RiverWater','MudBank'][i%3],
                    'sourceRectPx':None,'visualStatus':'UNMAPPED_ELIZAWY_REVIEW_REQUIRED'} for i in range(1120)]}
    def compile(self):
        return draft.compile_draft(self.semantic,self.map_raw,json.dumps(self.bindings).encode(),
                                   source_hash=self.source,fixture_hash=self.fixture)
    def test_1120_source_exact_rectangles_explicit_only(self):
        plan=self.compile();self.assertEqual(plan['unreviewedDrawCount'],1120)
        self.assertEqual(plan['draws'][0]['sourceRectPx'],[96,32,32,32])
        self.assertEqual(plan['draws'][1]['sourceRectPx'],[384,512,32,32])
        self.assertEqual(plan['draws'][2]['sourceRectPx'],[96,128,32,32])
        self.assertEqual(plan['approvedDrawCallCount'],0)
        self.assertFalse(plan['sourceExactArtApproved'])
        self.assertFalse(plan['runtimePublicationAllowed'])
        self.assertEqual(plan,self.compile())
    def test_missing_or_unbound_role_blocks_not_guessed(self):
        self.semantic['cells'][10]['terrainRole']='Cliff'
        with self.assertRaises(draft.ScenePlanError):self.compile()
    def test_stale_mapping_hash_blocks(self):
        self.bindings['historicalMappingSha256']='0'*64
        with self.assertRaisesRegex(draft.ScenePlanError,'sha'):self.compile()
    def test_claimed_approval_blocks(self):
        for field in ('sourceArtApproval','worldRendererParity','runtimePublicationAllowed'):
            self.bindings[field]=True
            with self.assertRaises(draft.ScenePlanError):self.compile()
            self.bindings[field]=False
    def test_out_of_bounds_and_implicit_variant_block(self):
        self.mapping['baseTiles']['grass']['cells'][0]=[16,1]
        self.map_raw=json.dumps(self.mapping).encode()
        self.bindings['historicalMappingSha256']=draft.sha(self.map_raw)
        with self.assertRaisesRegex(draft.ScenePlanError,'outside'):self.compile()
        self.mapping['baseTiles']['grass']['cells'][0]=[3,1]
        self.map_raw=json.dumps(self.mapping).encode()
        self.bindings['historicalMappingSha256']=draft.sha(self.map_raw)
        self.bindings['roleBindings'][0]['sourceVariantIndex']=1
        with self.assertRaises(draft.ScenePlanError):self.compile()
    def test_tampered_semantic_plan_blocks(self):
        self.semantic['cells'][1]['sourceRectPx']=[0,0,32,32]
        with self.assertRaises(draft.ScenePlanError):self.compile()
    def test_evidence_writes_only_candidate_is_atomic(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'experiments/haven_bevy_candidate').mkdir(parents=True)
            plan=self.compile();p=draft.write_draft(root,plan)
            data=p.read_bytes();self.assertEqual(draft.write_draft(root,plan).read_bytes(),data)
            self.assertEqual(len(list(root.rglob('*.json'))),1)
    def test_symlink_evidence_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);c=root/'experiments/haven_bevy_candidate';c.mkdir(parents=True)
            outside=root/'outside';outside.mkdir()
            try:(c/'evidence').symlink_to(outside,target_is_directory=True)
            except (OSError,NotImplementedError):self.skipTest('symlink unavailable')
            with self.assertRaisesRegex(draft.ScenePlanError,'redirected'):
                draft.write_draft(root,self.compile())
    def test_actual_historical_mapping_and_river_fixture_if_full_checkout(self):
        root=CANDIDATE.parents[1]
        mapping=root/'content/assets/intake/lpc_terrain_family_mapping_v0_3.json'
        fixture=root/'content/worldgen/scenes/terrain_acceptance/river_scene_v1.json'
        if not mapping.is_file() or not fixture.is_file():self.skipTest('needs complete source checkout')
        import sys
        sys.path.insert(0,str(CANDIDATE/'tools'))
        import semantic_scene_plan
        self.assertEqual(draft.sha(mapping.read_bytes()),'280735da3be341cbbb6a085d45fc14673886a94d24d2b34473ff48878f038307')
        b=(root/draft.BINDINGS).read_bytes()
        sem=semantic_scene_plan.compile_plan(fixture.read_bytes(),source_sha=json.loads(b)['sourceSha256'],fixture_sha=draft.sha(fixture.read_bytes()))
        self.assertEqual(draft.compile_draft(sem,mapping.read_bytes(),b,
            source_hash=json.loads(b)['sourceSha256'],fixture_hash=sem['sceneSha256'])['unreviewedDrawCount'],1120)

if __name__=='__main__':unittest.main()
