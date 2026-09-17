#!/usr/bin/env python3
"""Offline regression checks for the non-mutating B12 cutover preflight."""
from __future__ import annotations

import importlib.util
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[3] / 'assets/Audit-ElizaWyOnlyCutoverB12.py'
spec = importlib.util.spec_from_file_location('elizawy_cutover_b12', SCRIPT)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def png(width: int, height: int) -> bytes:
    return b'\x89PNG\r\n\x1a\n' + struct.pack('>I', 13) + b'IHDR' + struct.pack('>II', width, height)


class CutoverTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.pin = 'a' * 40
        source = self.root / module.ALLOWED_MOUNT
        (source / 'Terrain').mkdir(parents=True)
        original = png(64, 32)
        (source / 'Terrain/terrain_summer.png').write_bytes(original)
        self.put(module.LOCK, {
            'repository': 'https://github.com/ElizaWy/LPC', 'commit': self.pin,
            'fullSourceProjectPath': module.ALLOWED_MOUNT,
            'requiredTopLevelPaths': ['Terrain'], 'requiredRootFiles': [],
            'requiredTerrainFiles': ['Terrain/terrain_summer.png'],
            'lockedFiles': [{'repositoryPath': 'Terrain/terrain_summer.png',
                             'projectPath': module.ALLOWED_MOUNT + '/Terrain/terrain_summer.png',
                             'width': 64, 'height': 32, 'sha256': module.digest(source / 'Terrain/terrain_summer.png')}],
        })
        self.put(module.PROJECT, {'source': {'repository': 'https://github.com/ElizaWy/LPC', 'commit': self.pin},
                                  'projectPolicy': {'sourceTreeIsImmutable': True}})
        self.put(module.LANE, {'sourceRepository': 'https://github.com/ElizaWy/LPC',
                               'sourceCommit': self.pin, 'allowedSourceRoot': module.ALLOWED_MOUNT,
                               'laneId': 'elizawy_mainland', 'rules': ['V7 tuple atlases may not be used as ElizaWy pixel fallback.']})
        self.put(module.FAMILY, {'mainlandTargetFamily': 'elizawy_mainland_v1',
                                 'activeOpenWorldFamily': 'lpc_terrain_v7_island_v1',
                                 'runtimeMode': 'v7_source_pure_certification',
                                 'families': [{'id': 'elizawy_mainland_v1', 'crossFamilyFallbackAllowed': False}]})
        self.put(module.INDEX, {'pack': {'rawFilesPackaged': False},
                                'summary': {'files': 1, 'unreadableImages': 0},
                                'records': [{'relativePath': 'LPC-main/Terrain/terrain_summer.png',
                                             'sha256': module.digest(source / 'Terrain/terrain_summer.png'),
                                             'sizeBytes': len(original), 'width': 64, 'height': 32}]})
        self.put(module.POLICY, {'source': {'commit': self.pin}, 'activation': {'enabled': False},
                                 'certification': {'visualApproval': False}})
        for paths in (module.RUNTIME_DEPENDENCIES, module.VALIDATOR_DEPENDENCIES):
            for path in paths:
                self.file(path, 'no superseded dependencies')

    def file(self, name: str, content: str):
        file = self.root / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding='utf-8')

    def put(self, name: str, value: dict):
        self.file(name, json.dumps(value))

    def test_inactive_v7_is_blocked_even_with_present_source(self):
        report = module.audit(self.root)
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertIn('active terrain still uses', '\n'.join(report['blockers']))
        self.assertEqual(report['sourceChecks']['present_required'], 1)

    def test_verified_candidate_does_not_claim_visual_approval(self):
        authority = json.loads((self.root / module.FAMILY).read_text())
        authority.update(activeOpenWorldFamily='elizawy_mainland_v1', runtimeMode='elizawy_certification')
        self.put(module.FAMILY, authority)
        report = module.audit(self.root, full_index=True)
        self.assertEqual(report['status'], 'SOURCE_AND_STATIC_READY_REQUIRES_VISUAL_CERTIFICATION')
        self.assertEqual(report['sourceChecks']['verified_indexed'], 1)

    def test_hash_mismatch_blocks_approval(self):
        image = self.root / module.ALLOWED_MOUNT / 'Terrain/terrain_summer.png'
        image.write_bytes(png(32, 32))
        report = module.audit(self.root, full_index=True)
        self.assertIn('pinned SHA-256 mismatch', '\n'.join(report['blockers']))
        self.assertEqual(report['sourceChecks']['mismatched_indexed'], 1)

    def test_missing_mount_fails_closed(self):
        image = self.root / module.ALLOWED_MOUNT / 'Terrain/terrain_summer.png'
        image.unlink()
        image.parent.rmdir()
        image.parent.parent.rmdir()
        report = module.audit(self.root)
        self.assertIn('licensed source mount absent', '\n'.join(report['blockers']))

    def test_index_traversal_rejected(self):
        data = json.loads((self.root / module.INDEX).read_text())
        data['records'][0]['relativePath'] = 'LPC-main/../secret.png'
        self.put(module.INDEX, data)
        report = module.audit(self.root, full_index=True)
        self.assertIn('indexed file rejected', '\n'.join(report['blockers']))

    def test_missing_policy_reports_error_not_activation(self):
        (self.root / module.POLICY).unlink()
        report = module.audit(self.root)
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertIn('missing or invalid authority', report['blockers'][0])


if __name__ == '__main__':
    unittest.main(verbosity=2)
