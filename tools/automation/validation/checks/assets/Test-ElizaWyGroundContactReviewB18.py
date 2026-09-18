#!/usr/bin/env python3
"""B18 source-contact regression tests. Reuse B17's synthetic seven-sheet fixture."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def module(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


b18 = module('havenwild_b18', 'tools/automation/assets/Build-ElizaWyGroundContactReviewB18.py')
b17_fixture = module('havenwild_b17_test_fixture',
                     'tools/automation/validation/checks/assets/Test-ElizaWyGroundSemanticProposalsB17.py')
CONFIG = json.loads((ROOT / b18.CONFIG).read_text(encoding='utf-8'))


class SourceContacts(unittest.TestCase):
    def setUp(self):
        self.fixture = b17_fixture.GroundSemanticReviewTests('test_all_ten_roles_and_42_source_placements')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.inv = self.fixture.inv
        self.b16 = self.fixture.b16
        self.b17 = self.fixture.check()
        self.b13 = {'status': 'SOURCE_REPRODUCED_WITH_QUARANTINE',
                    'source': {'verifiedFiles': 64365}, 'blockers': [],
                    'pinnedCommit': CONFIG['sourceCommit']}
        self.b14 = {'status': 'SOURCE_ONLY_CANDIDATE_CATALOGS_VERIFIED', 'blockers': [],
                    'newAuthoringProvider': CONFIG['sourceProvider'],
                    'runtimeCutover': False, 'productionApproval': False}
        self.cfg = copy.deepcopy(CONFIG)

    def check(self):
        return b18.certify(self.root, self.cfg, self.inv, self.b16, self.b17,
                           self.b13, self.b14)

    def test_complete_42_placements_and_exact_contact_counts(self):
        report = self.check()
        self.assertEqual(report['blockers'], [])
        self.assertEqual(report['status'], 'SOURCE_INTERNAL_CONTACTS_CATALOGUED_EXTERNAL_REVIEW_REQUIRED')
        self.assertEqual((report['candidateGroups'], report['sourcePlacements'],
                          report['internalGridPairs'], report['externalBoundarySlots'],
                          report['candidateContactPairs']), (10, 42, 229, 314, 55))
        self.assertFalse(report['runtimeCutover'])
        self.assertEqual(report['approvedTopologyRules'], 0)

    def test_every_source_contact_is_original_grid_only(self):
        report = self.check()
        self.assertEqual(sum(len(p['internalGridContacts']) for g in report['groups']
                             for p in g['placements']), 229)
        self.assertTrue(all(not edge['visualSeamApproved'] for g in report['groups']
                            for p in g['placements'] for edge in p['internalGridContacts']))
        self.assertTrue(all(p['status'] == 'UNSUPPORTED_UNTIL_AUTHORED_EVIDENCE'
                            for p in report['externalContactReviewQueue']))

    def test_original_png_byte_change_blocks(self):
        image = self.root/'assets/source/licensed/lpc_revised/Terrain/terrain_summer.png'
        image.write_bytes(b'tamper')
        self.assertTrue(any('original source missing or changed' in e for e in self.check()['blockers']))

    def test_changed_b16_board_blocks(self):
        board = self.root / self.cfg['b16Board']
        board.write_text('modified review', encoding='utf-8')
        self.assertTrue(any('B16 source board changed' in e for e in self.check()['blockers']))

    def test_b14_runtime_activation_blocks(self):
        self.b14['runtimeCutover'] = True
        self.assertTrue(any('B14 source-only routing' in e for e in self.check()['blockers']))

    def test_b13_missing_full_certification_blocks(self):
        self.b13['source']['verifiedFiles'] = 10
        self.assertTrue(any('B13 fully reproduced' in e for e in self.check()['blockers']))

    def test_b17_unapproved_state_is_mandatory(self):
        self.b17['proposals'][0]['visualApproval'] = True
        self.assertTrue(any('premature B17 approval' in e for e in self.check()['blockers']))

    def test_dropped_source_cell_blocks(self):
        self.b17['proposals'][3]['placements'][0]['sourceCellIds'].pop()
        self.assertTrue(any('assembly is incomplete' in e for e in self.check()['blockers']))

    def test_reordered_source_cells_blocks(self):
        ids = self.b17['proposals'][3]['placements'][0]['sourceCellIds']
        ids[0], ids[1] = ids[1], ids[0]
        self.assertTrue(any('incorrect B15 source cell' in e for e in self.check()['blockers']))

    def test_unexpected_rectangle_blocks(self):
        item = self.b17['proposals'][0]['placements'][0]
        item['sourceRectPixels'] = [item['sourceRectPixels'][0] + 32, *item['sourceRectPixels'][1:]]
        self.assertTrue(any('B16/B17 source placement changed' in e for e in self.check()['blockers']))

    def test_policy_can_never_grant_external_contacts(self):
        self.cfg['policy']['unreviewedContactPairsFailClosed'] = False
        self.assertTrue(any('unsafe or missing policy' in e for e in self.check()['blockers']))

    def test_production_enabled_is_rejected(self):
        self.cfg['policy']['productionApproval'] = True
        self.assertTrue(any('prematurely enables' in e for e in self.check()['blockers']))

    def test_duplicate_group_rejected(self):
        self.b17['proposals'][1]['candidateId'] = self.b17['proposals'][0]['candidateId']
        self.assertTrue(any('duplicate or unknown B17' in e for e in self.check()['blockers']))

    def test_review_board_remains_read_only_and_unapproved(self):
        report = self.check()
        text = b18.page(self.root, self.inv, report,
                        self.root/'WORKSPACE/generated/lpc/elizawy_ground_contact_review_b18.html')
        self.assertIn('NO EXTERNAL CONTACTS OR TOPOLOGY APPROVED', text)
        self.assertIn('ground.shore.strip', text)
        self.assertIn('UNSUPPORTED_UNTIL_AUTHORED_EVIDENCE', text)
        self.assertNotIn('runtimeCutover: true', text)

    def test_escape_outside_repo_rejected(self):
        with self.assertRaises(ValueError):
            b18.safe(self.root, '../../outside')


if __name__ == '__main__':
    unittest.main()
