#!/usr/bin/env python3
"""B17 semantic candidate safety tests, using the real B16 algorithm and synthetic files."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SCRIPT = ROOT / 'tools/automation/assets/Build-ElizaWyGroundSemanticProposalsB17.py'
sp = importlib.util.spec_from_file_location('havenwild_b17', SCRIPT)
b17 = importlib.util.module_from_spec(sp)
sys.modules[sp.name] = b17
sp.loader.exec_module(b17)
CONFIG = json.loads((ROOT / b17.CONFIG).read_text(encoding='utf-8'))
B16_CFG = json.loads((ROOT / 'content/worldgen/elizawy_ground_visual_candidates_b16.json').read_text(encoding='utf-8'))


class GroundSemanticReviewTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.cfg = copy.deepcopy(CONFIG)
        self.old = copy.deepcopy(B16_CFG)
        sheet_specs = [(f'Terrain/terrain_{s}.png', 16, 26) for s in b17.SEASONS]
        sheet_specs += [('Terrain/tilled_soil.png', 8, 8), ('Terrain/ice-shallows.png', 6, 6)]
        self.sheets, self.cells = [], []
        for rel, cols, rows in sheet_specs:
            source = self.root/'assets/source/licensed/lpc_revised'/rel
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(f'unchanged:{rel}'.encode('utf-8'))
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            self.sheets.append({'sourcePath': rel, 'columns': cols, 'rows': rows,
                                'dimensions': [cols*32, rows*32], 'sha256': digest,
                                'certifiedSource': True, 'independentCellPaintingApproved': False})
            for row in range(rows):
                for col in range(cols):
                    self.cells.append({'id': f'{rel}:{col}:{row}', 'sourcePath': rel, 'column': col,
                                       'row': row, 'sourceSha256': digest,
                                       'runtimeApproved': False, 'assemblyApproved': False})
        self.inv = {'sourceCommit': CONFIG['sourceCommit'], 'sourceProvider': CONFIG['sourceProvider'],
                    'sourceRoot': 'assets/source/licensed/lpc_revised', 'sheets': self.sheets,
                    'cells': self.cells, 'summary': {'cellAddresses': 2180}, 'blockers': []}
        result = []
        for candidate in self.old['candidates']:
            rect = candidate['rectCells']
            paths = ([f'Terrain/terrain_{season}.png' for season in b17.SEASONS]
                     if candidate['kind'] == 'seasonal' else [candidate['sheet']])
            entries = []
            for path in paths:
                sheet = next(s for s in self.sheets if s['sourcePath'] == path)
                cellids = [f'{path}:{x}:{y}' for y in range(rect[1], rect[1]+rect[3])
                           for x in range(rect[0], rect[0]+rect[2])]
                entries.append({'sourcePath': path, 'sourceSha256': sheet['sha256'],
                                'rectPixels': [v*32 for v in rect], 'sourceCellIds': cellids,
                                'season': next((s for s in b17.SEASONS
                                                if path == f'Terrain/terrain_{s}.png'), None),
                                'sourceVerified': True, 'visualApproved': False,
                                'runtimeApproved': False})
            result.append({'id': candidate['id'], 'placements': entries})
        self.b16 = {'sourceCommit': CONFIG['sourceCommit'], 'sourceProvider': CONFIG['sourceProvider'],
                    'status': 'SOURCE_RECT_CANDIDATES_READY_FOR_VISUAL_REVIEW',
                    'blockers': [], 'productionApproval': False, 'runtimeCutover': False,
                    'visualApproval': False, 'approvedMappings': 0, 'approvedAssemblies': 0,
                    'cliffWaterfallCertification': 'NOT_PERFORMED',
                    'verifiedSourceSheets': 7,
                    'verifiedSources': {s['sourcePath']: {'sha256': s['sha256'],
                                                        'dimensions': s['dimensions']} for s in self.sheets},
                    'candidateGroups': 10, 'sourcePlacements': 42, 'candidates': result}
        html = self.root / self.cfg['b16Board']
        html.parent.mkdir(parents=True, exist_ok=True)
        html.write_text('<h1>B16 ElizaWy ground review</h1>', encoding='utf-8')

    def check(self):
        return b17.certify(self.root, self.cfg, self.inv, self.b16, self.old)

    def test_all_ten_roles_and_42_source_placements(self):
        result = self.check()
        self.assertEqual(result['blockers'], [])
        self.assertEqual(result['candidateGroups'], 10)
        self.assertEqual(result['sourcePlacements'], 42)
        self.assertEqual(result['approvedSemanticMappings'], 0)
        self.assertEqual(result['status'], 'SEMANTIC_PROPOSALS_READY_FOR_EXPLICIT_REVIEW')
        self.assertTrue(all(p['runtimeApproved'] is False and p['visualApproval'] is False
                            and p['neighborTopology'] == 'UNRESOLVED' for p in result['proposals']))

    def test_original_sheet_mutation_blocks(self):
        target = self.root/'assets/source/licensed/lpc_revised/Terrain/terrain_summer.png'
        target.write_bytes(b'altered')
        self.assertTrue(any('original source' in s for s in self.check()['blockers']))

    def test_legacy_source_identity_blocks(self):
        self.cfg['sourceProvider'] = 'lpc_terrain_v7'
        self.assertTrue(any('source identity' in s for s in self.check()['blockers']))

    def test_dropped_group_blocks(self):
        self.cfg['proposals'].pop()
        self.assertTrue(any('account for all' in s for s in self.check()['blockers']))

    def test_duplicate_role_blocks(self):
        self.cfg['proposals'][1]['semanticRole'] = self.cfg['proposals'][0]['semanticRole']
        self.assertTrue(any('invalid or duplicated' in s for s in self.check()['blockers']))

    def test_assembly_as_fill_blocks(self):
        self.cfg['proposals'][3]['componentKind'] = 'single_cell_surface'
        self.assertTrue(any('assembly misrepresented' in s for s in self.check()['blockers']))

    def test_missing_assembly_cell_blocks(self):
        self.b16['candidates'][3]['placements'][0]['sourceCellIds'].pop()
        self.assertTrue(any('incomplete or repeated' in s for s in self.check()['blockers']))

    def test_mislabeled_source_cell_blocks(self):
        self.b16['candidates'][0]['placements'][0]['sourceCellIds'][0] = self.b16['candidates'][1]['placements'][0]['sourceCellIds'][0]
        self.assertTrue(any('does not match original B15' in s for s in self.check()['blockers']))

    def test_water_depth_inference_blocks(self):
        self.cfg['proposals'][7]['semanticRole'] = 'water.deep'
        self.assertTrue(any('water depth inferred' in s for s in self.check()['blockers']))

    def test_premature_runtime_activation_blocks(self):
        self.cfg['policy']['productionApproval'] = True
        self.assertTrue(any('premature activation' in s for s in self.check()['blockers']))

    def test_premature_b16_visual_approval_blocks(self):
        self.b16['visualApproval'] = True
        self.assertTrue(any('approval invariants' in s for s in self.check()['blockers']))

    def test_source_rect_mutation_blocks(self):
        self.b16['candidates'][0]['placements'][0]['rectPixels'][0] += 32
        self.assertTrue(any('invalid source rectangle' in s for s in self.check()['blockers']))

    def test_missing_visual_board_blocks(self):
        (self.root/self.cfg['b16Board']).unlink()
        self.assertTrue(any('review board missing' in s for s in self.check()['blockers']))

    def test_incorrect_season_mapping_blocks(self):
        self.cfg['proposals'][0]['seasonAppearances'].pop('winter')
        self.assertTrue(any('season appearance' in s for s in self.check()['blockers']))

    def test_unsafe_relative_path_blocks(self):
        with self.assertRaises(ValueError):
            b17.safe(self.root, '../../outside')

    def test_render_board_uses_source_without_approving(self):
        result = self.check()
        html = b17.page(self.root, self.cfg, self.inv, result,
                        self.root/'WORKSPACE/generated/lpc/elizawy_ground_semantic_review_b17.html')
        self.assertIn('NOT APPROVED', html)
        self.assertIn('Terrain/terrain_summer.png', html)
        self.assertIn('ground.shore.strip', html)
        self.assertNotIn('lpc_terrain_v7', html)


if __name__ == '__main__':
    unittest.main()
