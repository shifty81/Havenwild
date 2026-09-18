#!/usr/bin/env python3
"""Offline B13 regression fixtures; no network or writes to project sources."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[3] / 'assets/Certify-ElizaWySourceB13.py'
spec = importlib.util.spec_from_file_location('havenwild_elizawy_b13', SCRIPT)
assert spec and spec.loader
b13 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = b13
spec.loader.exec_module(b13)
DIAGNOSTIC_PATH = SCRIPT.with_name('Diagnose-ElizaWyTextHashB13R1.py')
diag_spec = importlib.util.spec_from_file_location('havenwild_elizawy_b13r1_diagnostic', DIAGNOSTIC_PATH)
assert diag_spec and diag_spec.loader
diag = importlib.util.module_from_spec(diag_spec)
sys.modules[diag_spec.name] = diag
diag_spec.loader.exec_module(diag)


def png() -> bytes:
    return b'\x89PNG\r\n\x1a\n' + struct.pack('>I', 13) + b'IHDR' + struct.pack('>II', 32, 32)


class SourceTruthTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='havenwild-b13-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.pin = 'a' * 40
        self.repo = 'https://github.com/ElizaWy/LPC'
        self.mount = self.root / 'assets/source/licensed/lpc_revised'
        self.mount.mkdir(parents=True)
        self.image = 'Terrain/terrain_summer.png'
        self.broken = 'Characters/Clothing/Charcoal/Emotes.png'
        self.put(self.image, png())
        self.put(self.broken, b'')
        self.put('Credits.txt', b'Source credits reference only\n')
        for folder in b13.SOURCE_FOLDERS:
            (self.mount / folder).mkdir(exist_ok=True)
            if folder not in ('Terrain', 'Characters'):
                self.put(folder + '/Credits.txt', b'Fixture attribution\n')
        self.lock = {
            'repository': self.repo, 'commit': self.pin,
            'fullSourceProjectPath': 'assets/source/licensed/lpc_revised',
            'sourceMountProvenance': 'WORKSPACE/generated/lpc/elizawy_source_mount_v167z38.json',
            'requiredRootFiles': ['Credits.txt'], 'requiredTerrainFiles': [self.image],
            'lockedFiles': [{'repositoryPath': self.image,
                'projectPath': 'assets/source/licensed/lpc_revised/' + self.image,
                'sha256': hashlib.sha256(png()).hexdigest(), 'width': 32, 'height': 32}],
        }
        self.write('content/assets/intake/lpc_source_lock_v0_1.json', self.lock)
        self.write('content/assets/lpc/lpc_project_asset_authority_v0_1.json',
                   {'source': {'repository': self.repo, 'commit': self.pin}})
        self.write('content/assets/intake/elizawy_only_cutover_candidate_b12.json',
                   {'source': {'repository': self.repo, 'commit': self.pin},
                    'activation': {'enabled': False}})
        self.records = [self.rec(self.image, png(), width=32, height=32),
                        self.rec(self.broken, b'', imageError='original zero-byte'),
                        self.rec('Credits.txt', b'Source credits reference only\n')]
        for folder in b13.SOURCE_FOLDERS:
            if folder not in ('Terrain', 'Characters'):
                self.records.append(self.rec(folder + '/Credits.txt', b'Fixture attribution\n'))
        self.save_index()
        self.write('WORKSPACE/generated/lpc/elizawy_source_mount_v167z38.json',
                   {'expectedCommit': self.pin, 'verified': True})

    def put(self, relative, content):
        path = self.mount / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')

    @staticmethod
    def rec(relative, content, **extra):
        return {'relativePath': 'LPC-main/' + relative, 'extension': Path(relative).suffix.lower(),
                'sizeBytes': len(content), 'sha256': hashlib.sha256(content).hexdigest(), **extra}

    def save_index(self):
        self.write('content/assets/intake/external_pack_indexes/elizawy_lpc_main.json', {
            'pack': {'sourceUrl': self.repo, 'rawFilesPackaged': False},
            'summary': {'files': len(self.records), 'images': 2, 'unreadableImages': 1},
            'records': self.records,
        })

    def test_requires_actual_source_mount(self):
        self.mount.rename(self.root / 'missing_mount')
        r = b13.certify(self.root)
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertEqual(r['historicalInventory']['quarantinedImageCount'], 1)

    def test_metadata_only_not_approved(self):
        r = b13.certify(self.root)
        self.assertEqual(r['status'], 'SOURCE_MOUNTED_NEEDS_FULL_HASH_AUDIT')
        self.assertFalse(r['productionApproval'])
        self.assertEqual(r['tileCertification'], 'NOT_PERFORMED')

    def test_full_reproduction_quarantines_unreadable_image(self):
        r = b13.certify(self.root, full_index=True)
        self.assertEqual(r['status'], 'SOURCE_REPRODUCED_WITH_QUARANTINE')
        self.assertEqual(r['source']['hashedFiles'], len(self.records))
        self.assertEqual(len(r['quarantinedAssets']), 1)
        self.assertFalse(r['quarantinedAssets'][0]['productionEligible'])

    def test_crlf_text_accepted_only_when_index_bytes_reproduced(self):
        self.put('Credits.txt', b'Source credits reference only\r\n')
        r = b13.certify(self.root, full_index=True)
        self.assertEqual(r['status'], 'SOURCE_REPRODUCED_WITH_QUARANTINE')
        self.assertEqual(r['source']['lineEndingEquivalent'], 1)
        self.assertEqual(r['source']['verifiedFiles'], len(self.records))
        self.assertEqual(r['source']['hashedFiles'], len(self.records) - 1)
        evidence = r['source']['lineEndingEvidence'][0]
        self.assertEqual(evidence['path'], 'Credits.txt')
        self.assertEqual(evidence['transform'], 'crlf_to_lf')
        self.assertFalse(r['productionApproval'])

    def test_lf_text_accepted_when_historical_index_was_crlf(self):
        old = b'Source credits reference only\n'
        index_content = old.replace(b'\n', b'\r\n')
        self.records[2] = self.rec('Credits.txt', index_content)
        self.save_index()
        r = b13.certify(self.root, full_index=True)
        self.assertEqual(r['status'], 'SOURCE_REPRODUCED_WITH_QUARANTINE')
        self.assertEqual(r['source']['lineEndingEquivalent'], 1)
        self.assertEqual(r['source']['lineEndingEvidence'][0]['transform'], 'lf_to_crlf')

    def test_real_text_change_still_fails_closed(self):
        self.put('Credits.txt', b'Source credits altered\r\n')
        r = b13.certify(self.root, full_index=True)
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertEqual(r['source']['mismatchedIndexed'], 1)
        self.assertEqual(r['source']['lineEndingEquivalent'], 0)
        self.assertEqual(r['source']['mismatchExamples'][0]['path'], 'Credits.txt')
        self.assertEqual(r['source']['mismatchExamples'][0]['reason'],
                         'content_differs_after_both_exact_line_ending_checks')

    def test_png_differences_never_normalized(self):
        self.put(self.image, png() + b'\r\n')
        r = b13.certify(self.root, full_index=True)
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertEqual(r['source']['mismatchedIndexed'], 1)
        self.assertEqual(r['source']['lineEndingEquivalent'], 0)
        self.assertEqual(r['source']['mismatchExamples'][0]['reason'],
                         'binary_or_oversized_text_differs')

    def test_same_size_different_content_fails_closed(self):
        self.put('Credits.txt', b'Source credits reference onlz\n')
        r = b13.certify(self.root, full_index=True)
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertEqual(r['source']['mismatchExamples'][0]['path'], 'Credits.txt')

    def test_missing_file_diagnostic_is_explicit(self):
        (self.mount / 'Credits.txt').unlink()
        r = b13.certify(self.root, full_index=True)
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertEqual(r['source']['missingIndexed'], 1)
        self.assertEqual(r['source']['missingExamples'][0]['path'], 'Credits.txt')

    def test_fast_text_diagnostic_reports_exact_proof(self):
        self.put('Credits.txt', b'Source credits reference only\r\n')
        result = diag.diagnose(self.root)
        self.assertEqual(result['status'], 'TEXT_DIAGNOSTIC_OK_NOT_SOURCE_CERTIFICATION')
        self.assertEqual(result['lineEndingEquivalent'], 1)
        self.assertFalse(result['artworkChecked'])
        self.assertFalse(result['productionApproval'])

    def test_fast_text_diagnostic_blocks_real_change(self):
        self.put('Credits.txt', b'Source credits DIFFERENT\r\n')
        result = diag.diagnose(self.root)
        self.assertEqual(result['status'], 'TEXT_DIAGNOSTIC_BLOCKED')
        self.assertEqual(result['different'], 1)
        self.assertFalse(result['artworkChecked'])

    def test_corrupted_source_fails_closed(self):
        self.put(self.image, png() + b'bad')
        r = b13.certify(self.root, full_index=True)
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertEqual(r['source']['mismatchedIndexed'], 1)

    def test_unexpected_source_file_fails_closed(self):
        self.put('Terrain/unindexed.png', png())
        r = b13.certify(self.root, full_index=True)
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertEqual(r['source']['unexpectedFiles'], 1)

    def test_path_traversal_fails_closed(self):
        self.records[0]['relativePath'] = 'LPC-main/Terrain/../escape.png'
        self.save_index()
        r = b13.certify(self.root, full_index=True)
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertGreater(r['historicalInventory']['invalidIndexRecords'], 0)

    def test_mismatched_pin_fails_closed(self):
        self.lock['commit'] = 'b' * 40
        self.write('content/assets/intake/lpc_source_lock_v0_1.json', self.lock)
        self.assertEqual(b13.certify(self.root)['status'], 'BLOCKED')

    def test_unverified_source_provenance_fails_closed(self):
        self.write('WORKSPACE/generated/lpc/elizawy_source_mount_v167z38.json',
                   {'expectedCommit': self.pin, 'verified': False})
        self.assertEqual(b13.certify(self.root, full_index=True)['status'], 'BLOCKED')


if __name__ == '__main__':
    unittest.main(verbosity=2)
