#!/usr/bin/env python3
"""Offline contract tests for guarded cliff projection recovery (no licensed art required)."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

ENSURE = Path(__file__).with_name('Ensure-ElizaWyCliffRuntimeProjection.py')
spec = importlib.util.spec_from_file_location('cliff_projection_guard', ENSURE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def png_fixture(width: int = 2, height: int = 2) -> bytes:
    # Guard checks contract hash and the PNG signature/IHDR geometry; these
    # fixture bytes are not source artwork and are never placed in the game.
    return module.PNG_HEADER + struct.pack('>I', 13) + b'IHDR' + struct.pack('>II', width, height) + b'\x08\x06\0\0\0'


class SourceProjectionGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source_bytes = png_fixture()
        v7_bytes = png_fixture(4, 4)
        output_bytes = png_fixture(2, 2) + b'approved-source-derivative'
        self.source_bytes, self.v7_bytes, self.output_bytes = source_bytes, v7_bytes, output_bytes
        self.rel_source = 'assets/source/licensed/lpc_revised/Terrain/cliff_summer.png'
        self.rel_v7 = 'content/assets/lpc/source/lpc-terrains-v7/terrain-map-v7.png'
        self.rel_output = 'assets/generated/worldgen_v0_1/terrain/elizawy_cliff_runtime_overlay_summer.png'
        self.rel_builder = 'tools/automation/terrain/Build-ElizaWyCliffRuntimeOverlayPass167Z109D.py'
        for rel, data in ((self.rel_source, source_bytes), (self.rel_v7, v7_bytes)):
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        self.contract = {
            'status': 'active', 'pass': '167Z109W3',
            'licensedSource': {'projectMount': self.rel_source, 'sha256': hashlib.sha256(source_bytes).hexdigest(), 'dimensionsPx': [2, 2]},
            'runtimeProjection': {
                'path': self.rel_output, 'sha256': hashlib.sha256(output_bytes).hexdigest(),
                'builder': self.rel_builder, 'v7Source': {'path': self.rel_v7, 'sha256': hashlib.sha256(v7_bytes).hexdigest()}
            }
        }
        provider = self.root / 'content/worldgen/authored_terrain_provider_authority_v0_1.json'
        provider.parent.mkdir(parents=True, exist_ok=True)
        provider.write_text(json.dumps({
            'status': 'active', 'revision': '167Z109W3-unified-authored-provider-v1',
            'cliffProvider': {'semanticGroundStrippedOnlyInDerivedOverlay': True},
            'ownership': {'V7': 'surface/plateau/toe semantic terrain pixels'},
        }), encoding='utf-8')
        contract_path = self.root / module.CONTRACT
        contract_path.parent.mkdir(parents=True, exist_ok=True)
        contract_path.write_text(json.dumps(self.contract), encoding='utf-8')

    def test_verified_projection_is_accepted(self):
        output = self.root / self.rel_output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(self.output_bytes)
        module.ensure_projection(self.root)
        self.assertEqual(output.read_bytes(), self.output_bytes)

    def test_existing_wrong_projection_preserved(self):
        output = self.root / self.rel_output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b'old-unapproved-artwork')
        with self.assertRaisesRegex(RuntimeError, 'unapproved cliff projection'):
            module.ensure_projection(self.root)
        self.assertEqual(output.read_bytes(), b'old-unapproved-artwork')

    def test_wrong_source_fails_without_output(self):
        (self.root / self.rel_source).write_bytes(b'unapproved licensed input')
        with self.assertRaisesRegex(RuntimeError, 'Pinned ElizaWy cliff source SHA-256 mismatch'):
            module.ensure_projection(self.root)
        self.assertFalse((self.root / self.rel_output).exists())

    def test_missing_projection_fails_with_verify_only(self):
        with self.assertRaisesRegex(RuntimeError, 'projection is absent'):
            module.ensure_projection(self.root, rebuild=False)
        self.assertFalse((self.root / self.rel_output).exists())

    def test_older_builder_candidate_cannot_publish_wrong_hash(self):
        builder = self.root / self.rel_builder
        builder.parent.mkdir(parents=True, exist_ok=True)
        builder.write_text('strip_semantic_ground = True\nimport pathlib,sys\npathlib.Path(sys.argv[sys.argv.index("--output")+1]).write_bytes(b"incorrect-artwork")\n', encoding='utf-8')
        with self.assertRaisesRegex(RuntimeError, 'builder are out of sync'):
            module.ensure_projection(self.root)
        self.assertFalse((self.root / self.rel_output).exists())

    def test_approved_builder_publishes_exact_artwork(self):
        builder = self.root / self.rel_builder
        builder.parent.mkdir(parents=True, exist_ok=True)
        builder.write_text('strip_semantic_ground = True\nimport pathlib,sys\npathlib.Path(sys.argv[sys.argv.index("--output")+1]).write_bytes(bytes.fromhex("' + self.output_bytes.hex() + '"))\n', encoding='utf-8')
        module.ensure_projection(self.root)
        self.assertEqual((self.root / self.rel_output).read_bytes(), self.output_bytes)

    def test_obsolete_projection_contract_rejected(self):
        self.contract['pass'] = '167Z109G'
        (self.root / module.CONTRACT).write_text(json.dumps(self.contract), encoding='utf-8')
        with self.assertRaisesRegex(RuntimeError, 'unexpected cliff projection authority'):
            module.ensure_projection(self.root)

    def test_missing_active_w3_provider_rejected(self):
        (self.root / 'content/worldgen/authored_terrain_provider_authority_v0_1.json').unlink()
        with self.assertRaises(FileNotFoundError):
            module.ensure_projection(self.root)

    def test_builder_that_restores_old_receiver_mask_rejected(self):
        builder = self.root / self.rel_builder
        builder.parent.mkdir(parents=True, exist_ok=True)
        builder.write_text('normalize_diagonal_receiver = True\nstrip_semantic_ground = True\n', encoding='utf-8')
        with self.assertRaisesRegex(RuntimeError, 'active W3 source projection policy'):
            module.ensure_projection(self.root)
        self.assertFalse((self.root / self.rel_output).exists())

    def test_escaping_path_rejected(self):
        self.contract['runtimeProjection']['path'] = '../overwrite-other-file.png'
        (self.root / module.CONTRACT).write_text(json.dumps(self.contract), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'unsafe project-relative'):
            module.ensure_projection(self.root)


if __name__ == '__main__':
    unittest.main(verbosity=2)
