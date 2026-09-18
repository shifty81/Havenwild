#!/usr/bin/env python3
"""Offline regression coverage for source-ground inventory and fail-closed review."""
import hashlib
import importlib.util
import json
import shutil
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[3] / 'assets' / 'Build-ElizaWyGroundCellReviewB15.py'
spec = importlib.util.spec_from_file_location('b15_ground_review', SCRIPT)
b15 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = b15
spec.loader.exec_module(b15)


def png(w, h):
    def chunk(name, payload):
        return struct.pack('>I', len(payload)) + name + payload + struct.pack('>I', zlib.crc32(name + payload) & 0xffffffff)
    header = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>2I5B', w, h, 8, 6, 0, 0, 0)
    raw = b''.join(b'\0' + b'\0\0\0\xff' * w for _ in range(h))
    return header + chunk(b'IHDR', ihdr) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')


class GroundTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        source_work = Path(__file__).resolve().parents[5]
        for rel in ['content/worldgen/elizawy_ground_cell_contract_b15.json',
                    'content/worldgen/elizawy_ground_review_decisions_b15.json']:
            dest = self.root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_work / rel, dest)
        self.config = json.loads((self.root / 'content/worldgen/elizawy_ground_cell_contract_b15.json').read_text())
        self.index = {'records': []}
        catalog = {'domain': 'terrain', 'sourceCommit': self.config['sourceCommit'],
                   'newAuthoringProvider': self.config['provider'], 'records': []}
        for spec in self.config['groundSheets'] + self.config['supplementalSheets']:
            rel = spec['path']
            path = self.root / self.config['sourceRoot'] / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = png(64, 32)
            path.write_bytes(payload)
            catalog['records'].append({'sourcePath': rel, 'stableAssetId': 'lpc.terrain.' + rel,
                                       'productionApproved': False, 'productionState': 'SOURCE_ONLY_UNMAPPED',
                                       'candidateProvider': self.config['provider'], 'dimensions': [64,32]})
            self.index['records'].append({'relativePath': 'LPC-main/' + rel,
                                          'sizeBytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest(),
                                          'width': 64, 'height': 32})
        self.save_index()
        self.write(self.config['terrainCatalog'], catalog)
        self.write(self.config['b13Report'], {'status': 'SOURCE_REPRODUCED_WITH_QUARANTINE',
                   'pinnedCommit': self.config['sourceCommit'], 'source': {
                       'verifiedFiles': 64365, 'missingIndexed': 0, 'mismatchedIndexed': 0}, 'blockers': []})
        self.write(self.config['b14Report'], {'status': 'SOURCE_ONLY_CANDIDATE_CATALOGS_VERIFIED',
                   'newAuthoringProvider': self.config['provider'], 'runtimeCutover': False,
                   'productionApproval': False, 'blockers': []})

    def write(self, rel, obj):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj), encoding='utf-8')

    def save_index(self):
        self.write(self.config['sourceIndex'], self.index)

    def test_all_seven_exact_source_sheets_enumerated_without_promotion(self):
        outcome = b15.run(self.root)
        self.assertEqual(outcome['status'], 'SOURCE_CELL_INVENTORY_READY_FOR_REVIEW')
        self.assertEqual(outcome['sourceSheetsVerified'], 7)
        self.assertEqual(outcome['sourceCellAddresses'], 14)
        self.assertIs(outcome['runtimeCutover'], False)
        self.assertIs(outcome['productionApproved'], False)
        inv = json.loads((self.root / self.config['generatedInventory']).read_text())
        self.assertTrue(all(rec['semanticRole'] is None and rec['runtimeApproved'] is False for rec in inv['cells']))
        self.assertTrue((self.root / self.config['generatedReviewBoard']).is_file())

    def test_tampered_sheet_rejected_without_false_visual_promotion(self):
        path = self.root / self.config['sourceRoot'] / self.config['groundSheets'][0]['path']
        path.write_bytes(path.read_bytes() + b'drift')
        result = b15.run(self.root)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertTrue(any('historical source byte mismatch' in msg for msg in result['blockers']))

    def test_missing_sheet_rejected(self):
        (self.root / self.config['sourceRoot'] / self.config['groundSheets'][0]['path']).unlink()
        self.assertEqual(b15.run(self.root)['status'], 'BLOCKED')

    def test_corrupt_png_dimensions_rejected(self):
        path = self.root / self.config['sourceRoot'] / self.config['groundSheets'][0]['path']
        path.write_bytes(png(45, 32))
        self.assertTrue(any('grid' in m for m in b15.run(self.root)['blockers']))

    def test_old_b13_report_rejected(self):
        self.write(self.config['b13Report'], {'status': 'BLOCKED', 'pinnedCommit': self.config['sourceCommit'],
                                             'source': {'verifiedFiles': 49282}, 'blockers': []})
        self.assertTrue(any('B13' in m for m in b15.run(self.root)['blockers']))

    def test_bad_b14_cutover_rejected(self):
        self.write(self.config['b14Report'], {'status': 'SOURCE_ONLY_CANDIDATE_CATALOGS_VERIFIED',
                                             'newAuthoringProvider': self.config['provider'],
                                             'runtimeCutover': True, 'productionApproval': False,
                                             'blockers': []})
        self.assertTrue(any('B14' in m for m in b15.run(self.root)['blockers']))

    def test_unknown_mapping_rejected(self):
        self.write(self.config['reviewDecisions'], {'schema': 'havenwild.elizawy_ground_review_decisions.b15',
                   'sourceCommit': self.config['sourceCommit'],
                   'reviewedMappings': [{'sourceCellId': 'made.up', 'semanticRole': 'Grass',
                                         'reviewEvidence': 'test evidence'}],
                   'reviewedAssemblies': [], 'certifiedRuntimeBindings': []})
        result = b15.run(self.root)
        self.assertTrue(any('unknown' in m for m in result['blockers']))

    def test_premature_production_approval_rejected(self):
        id_ = b15.source_cell_id(self.config['groundSheets'][0]['path'], 0, 0)
        self.write(self.config['reviewDecisions'], {'schema': 'havenwild.elizawy_ground_review_decisions.b15',
                   'sourceCommit': self.config['sourceCommit'],
                   'reviewedMappings': [{'sourceCellId': id_, 'semanticRole': 'Grass',
                                         'reviewEvidence': 'test evidence', 'productionApproved': True}],
                   'reviewedAssemblies': [], 'certifiedRuntimeBindings': []})
        self.assertTrue(any('cannot approve' in m for m in b15.run(self.root)['blockers']))

    def test_assemblies_not_accepted_as_independent_cells(self):
        self.write(self.config['reviewDecisions'], {'schema': 'havenwild.elizawy_ground_review_decisions.b15',
                   'sourceCommit': self.config['sourceCommit'], 'reviewedMappings': [],
                   'reviewedAssemblies': [{'id': 'fake'}], 'certifiedRuntimeBindings': []})
        self.assertTrue(any('assemblies' in m for m in b15.run(self.root)['blockers']))

    def test_path_traversal_rejected(self):
        self.assertRaises(ValueError, b15.inside, self.root, '../outside')

    def test_cell_addresses_distinct_and_stable(self):
        a = b15.source_cell_id('Terrain/terrain_summer.png', 1, 2)
        self.assertEqual(a, b15.source_cell_id('Terrain/terrain_summer.png', 1, 2))
        self.assertNotEqual(a, b15.source_cell_id('Terrain/terrain_autumn.png', 1, 2))

    def test_review_board_is_source_only(self):
        b15.run(self.root)
        board = (self.root / self.config['generatedReviewBoard']).read_text()
        self.assertIn('NOT certified terrain cells', board)
        self.assertNotIn('V7.png', board)
        self.assertIn('terrain_spring.png', board)


if __name__ == '__main__':
    unittest.main()
