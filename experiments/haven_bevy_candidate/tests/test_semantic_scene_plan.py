"""Semantic scene contract tests; neither graphics nor asset approval is implied."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
SCRIPT = BASE / 'tools/semantic_scene_plan.py'
spec = importlib.util.spec_from_file_location('semantic_scene_plan', SCRIPT)
scene_plan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scene_plan)

class ScenePlanTests(unittest.TestCase):
    def setUp(self):
        self.scene = {'kind':'worldgen_scene', 'sceneId':'test-river',
                      'sceneSize':[3,2], 'tileSize':[32,32],
                      'layers':{'terrain':[['Grass','RiverWater','Grass'],
                                           ['Grass','MudBank','Grass']]}}
        self.raw = json.dumps(self.scene).encode()
    def make(self):
        return scene_plan.compile_plan(self.raw, source_sha='a'*64,
                                       fixture_sha=scene_plan.sha(self.raw))
    def test_deterministic_complete_cell_order_and_counts(self):
        plan = self.make()
        self.assertEqual(plan['semanticCellCount'], 6)
        self.assertEqual(plan['unmappedCellCount'], 6)
        self.assertEqual(plan['roleCounts'], {'Grass':4,'MudBank':1,'RiverWater':1})
        self.assertEqual([(c['x'],c['y']) for c in plan['cells']],
                         [(0,0),(1,0),(2,0),(0,1),(1,1),(2,1)])
        self.assertEqual(plan, self.make())
    def test_real_neighbor_roles_and_boundaries(self):
        plan = self.make()
        self.assertEqual(plan['cells'][1]['neighborsNESW'],
                         [None,'Grass','MudBank','Grass'])
        self.assertEqual(plan['cells'][0]['neighborsNESW'],
                         [None,'RiverWater','Grass',None])
    def test_no_fabricated_art_or_height_or_certification(self):
        plan = self.make()
        self.assertFalse(plan['sourceExactArtApproved'])
        self.assertFalse(plan['worldRendererParity'])
        self.assertEqual(plan['approvedDrawCallCount'], 0)
        self.assertTrue(all(c['sourceRectPx'] is None for c in plan['cells']))
        self.assertIn('elevation', plan['notInferred'])
    def test_fails_closed_stale_hash(self):
        with self.assertRaisesRegex(scene_plan.ScenePlanError,'hash mismatch'):
            scene_plan.compile_plan(self.raw, source_sha='a'*64, fixture_sha='0'*64)
    def test_fails_closed_bad_grid_and_source(self):
        for bad in ([[1,2,3],['Grass','MudBank','Grass']], [['Grass'],['Grass']]):
            scene = json.loads(self.raw); scene['layers']['terrain'] = bad
            raw = json.dumps(scene).encode()
            with self.assertRaises(scene_plan.ScenePlanError):
                scene_plan.compile_plan(raw, source_sha='a'*64, fixture_sha=scene_plan.sha(raw))
        with self.assertRaises(scene_plan.ScenePlanError):
            scene_plan.compile_plan(self.raw, source_sha='z'*64,
                                    fixture_sha=scene_plan.sha(self.raw))
    def test_nonobject_scene_and_layers_fail_closed(self):
        for scene in ([], {'kind':'worldgen_scene','sceneId':'x', 'sceneSize':[1,1],
                           'tileSize':[32,32],'layers':[]}):
            raw=json.dumps(scene).encode()
            with self.assertRaises(scene_plan.ScenePlanError):
                scene_plan.compile_plan(raw,source_sha='a'*64,fixture_sha=scene_plan.sha(raw))

    def test_candidate_only_atomic_evidence_and_repeat(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'experiments/haven_bevy_candidate').mkdir(parents=True)
            plan = self.make()
            path = scene_plan.write_candidate_plan(root, plan)
            before = path.read_bytes()
            self.assertEqual(scene_plan.write_candidate_plan(root,plan).read_bytes(), before)
            self.assertEqual(json.loads(before)['roleCounts']['Grass'],4)
            self.assertEqual(list(root.rglob('*.json')), [path])
    def test_candidate_evidence_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            c = root/'experiments/haven_bevy_candidate';c.mkdir(parents=True)
            outside = root/'outside'; outside.mkdir()
            try:
                (c/'evidence').symlink_to(outside, target_is_directory=True)
            except (OSError,NotImplementedError):
                self.skipTest('symlink unavailable')
            with self.assertRaisesRegex(scene_plan.ScenePlanError,'symlink'):
                scene_plan.write_candidate_plan(root,self.make())
    def test_real_fixture_1120_cells_if_present(self):
        root=BASE.parents[1]
        real=root/scene_plan.SCENE_PATH
        if not real.exists():
            self.skipTest('full source fixture not available')
        raw=real.read_bytes()
        plan=scene_plan.compile_plan(raw,source_sha='a'*64,fixture_sha=scene_plan.sha(raw))
        self.assertEqual(plan['semanticCellCount'],1120)
        self.assertEqual(plan['unmappedCellCount'],1120)
        self.assertEqual(plan['roleCounts'],{'Grass':868,'MudBank':56,'RiverWater':196})

if __name__=='__main__':
    unittest.main()
