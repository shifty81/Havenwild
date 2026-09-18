#!/usr/bin/env python3
"""B16 source rectangle review safety tests (self-contained synthetic B15 fixture)."""
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
SCRIPT = ROOT / 'tools/automation/assets/Build-ElizaWyGroundVisualCandidatesB16.py'
sp = importlib.util.spec_from_file_location('havenwild_b16', SCRIPT)
b16 = importlib.util.module_from_spec(sp)
sys.modules[sp.name] = b16
sp.loader.exec_module(b16)
CONTRACT = json.loads((ROOT / b16.REL).read_text(encoding='utf-8'))


class GroundVisualCandidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = copy.deepcopy(CONTRACT)
        sheet_specs = [(f'Terrain/terrain_{s}.png', 16, 26) for s in b16.SEASONS]
        sheet_specs += [('Terrain/tilled_soil.png', 8, 8), ('Terrain/ice-shallows.png', 6, 6)]
        self.sheets = []
        self.cells = []
        for rel, cols, rows in sheet_specs:
            source = self.root / 'assets/source/licensed/lpc_revised' / rel
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(('fixture:'+rel).encode('utf-8'))
            sha = hashlib.sha256(source.read_bytes()).hexdigest()
            self.sheets.append({'sourcePath': rel, 'columns': cols, 'rows': rows,
                                'dimensions': [cols*32, rows*32], 'sha256': sha,
                                'certifiedSource': True, 'independentCellPaintingApproved': False})
            for row in range(rows):
                for col in range(cols):
                    self.cells.append({'id': f'{rel}:{col}:{row}', 'sourcePath': rel,
                                       'column': col, 'row': row, 'sourceSha256': sha,
                                       'runtimeApproved': False, 'assemblyApproved': False})
        for rel in ('Terrain/Credits.txt', '_ Test Scenes/DemoGame - 2 - Summer.png'):
            path = self.root / 'assets/source/licensed/lpc_revised' / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'local source evidence')
        self.inv = {'sourceCommit': CONTRACT['sourceCommit'], 'sourceProvider': 'elizawy_lpc_revised',
                    'sourceRoot': 'assets/source/licensed/lpc_revised',
                    'sheets': self.sheets, 'cells': self.cells,
                    'summary': {'cellAddresses': 2180}, 'blockers': []}
        self.b15 = {'status': 'SOURCE_CELL_INVENTORY_READY_FOR_REVIEW',
                    'productionApproved': False, 'runtimeCutover': False, 'blockers': []}

    def check(self):
        return b16.validate(self.config, self.inv, self.b15, self.root)

    def test_all_ten_explicit_groups_are_source_only(self):
        result = self.check()
        self.assertFalse(result['blockers'], result['blockers'])
        self.assertEqual(result['candidateGroups'], 10)
        self.assertEqual(result['sourcePlacements'], 42)
        self.assertEqual(result['verifiedSourceSheets'], 7)
        self.assertFalse(result['runtimeCutover'])
        self.assertFalse(result['productionApproval'])
        self.assertTrue(all(not p['runtimeApproved'] and not p['visualApproved']
                            for c in result['candidates'] for p in c['placements']))

    def test_modified_source_is_rejected(self):
        path = self.root / 'assets/source/licensed/lpc_revised/Terrain/terrain_summer.png'
        path.write_bytes(b'modified')
        self.assertTrue(any('source is absent, changed' in x for x in self.check()['blockers']))

    def test_outside_sheet_is_rejected(self):
        self.config['candidates'][0]['rectCells'] = [15, 25, 2, 2]
        self.assertTrue(any('outside sheet' in x for x in self.check()['blockers']))

    def test_missing_assembly_cell_is_rejected(self):
        self.inv['cells'] = [c for c in self.inv['cells'] if c['id'] != 'Terrain/terrain_spring.png:4:1']
        self.assertTrue(any('unverified or prematurely approved' in x for x in self.check()['blockers']))

    def test_preapproved_source_is_rejected(self):
        self.inv['cells'][0]['runtimeApproved'] = True
        self.assertTrue(any('unverified or prematurely approved' in x for x in self.check()['blockers']))

    def test_premature_policy_is_rejected(self):
        self.config['hardRules']['publishRuntimeBindings'] = True
        self.assertIn('unsafe policy: publishRuntimeBindings', self.check()['blockers'])

    def test_wrong_source_revision_is_rejected(self):
        self.config['sourceCommit'] = 'invalid'
        self.assertTrue(any('pinned source identity' in x for x in self.check()['blockers']))

    def test_b15_not_certified_is_rejected(self):
        self.b15['status'] = 'BLOCKED'
        self.assertTrue(any('B15 ground source' in x for x in self.check()['blockers']))

    def test_missing_credits_is_rejected(self):
        (self.root / 'assets/source/licensed/lpc_revised/Terrain/Credits.txt').unlink()
        self.assertTrue(any('missing credits or demonstration' in x for x in self.check()['blockers']))

    def test_duplicate_candidate_is_rejected(self):
        self.config['candidates'].append(copy.deepcopy(self.config['candidates'][0]))
        self.assertTrue(any('duplicate/empty candidate' in x for x in self.check()['blockers']))


if __name__ == '__main__':
    unittest.main()
