"""Tests fail-closed bridge behavior without executing a real PCC gate."""
from __future__ import annotations
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

BRIDGE = Path(__file__).resolve().parents[1] / 'tools' / 'pcc_bridge.py'
spec = importlib.util.spec_from_file_location('havenwild_mapper_pcc_bridge', BRIDGE)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for rel in ('Cargo.toml', str(bridge.PROVIDER), 'tools/control/ProjectCommandRegistry.ps1'):
            file = self.root / rel
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text('fake for test', encoding='utf-8')

    def tearDown(self):
        self.tmp.cleanup()

    def test_discovery_only_and_unknown_command_fail_closed(self):
        with patch.object(bridge, 'keys', return_value={'pcc.status','audit.terrain-tuples'}):
            self.assertTrue(bridge.plan(self.root, 'pcc.status')['readOnly'])
            self.assertFalse(bridge.plan(self.root, 'audit.terrain-tuples')['readOnly'])
            with self.assertRaises(bridge.BridgeError):
                bridge.plan(self.root, 'rm -rf .')

    def test_run_requires_exact_confirmation_and_mutation_approval(self):
        with patch.object(bridge, 'keys', return_value={'audit.terrain-tuples'}), patch.object(bridge.subprocess, 'call') as called:
            args = ['run', '--root', str(self.root), '--key', 'audit.terrain-tuples']
            self.assertEqual(bridge.main(args), 2)
            self.assertEqual(bridge.main(args + ['--confirm-key','other']), 2)
            self.assertEqual(bridge.main(args + ['--confirm-key','audit.terrain-tuples']), 2)
            called.assert_not_called()
            called.return_value = 0
            self.assertEqual(bridge.main(args + ['--confirm-key','audit.terrain-tuples','--allow-mutation']), 0)
            called.assert_called_once()

    def test_dual_grid_inventory_does_not_claim_art_approval(self):
        path = self.root / bridge.TUPLES
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'signatureToTileId': {'5,5,5,5': 0}, 'duplicates': {},
                                    'uniqueSignatureCount':1, 'duplicateSignatureCount':0,
                                    'terrainOrdinalToCode':{'5':'Grass'}, 'declaredTileCount':1,
                                    'mappedTupleCount':1}), encoding='utf-8')
        spatial = self.root / bridge.SPATIAL
        spatial.parent.mkdir(parents=True, exist_ok=True)
        spatial.write_text('TerrainTuplePresentationOrigin', encoding='utf-8')
        report = bridge.tuple_report(self.root)
        self.assertEqual(report['uniqueSignatures'], 1)
        self.assertFalse(report['elizawySourceExactVisualCertified'])
        path.write_text('{"signatureToTileId":{},"duplicates":{},"uniqueSignatureCount":1,"duplicateSignatureCount":0}', encoding='utf-8')
        with self.assertRaises(bridge.BridgeError):
            bridge.tuple_report(self.root)

    def test_root_proof_required(self):
        (self.root / 'Cargo.toml').unlink()
        with self.assertRaises(bridge.BridgeError):
            bridge.project_root(str(self.root))


if __name__ == '__main__':
    unittest.main()
