"""B48R28A independent shadow-gate tests; does not invoke PCC, Rust or a GUI."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path, PureWindowsPath
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[2] / "tools/architecture/parallel_migration.py"
spec = importlib.util.spec_from_file_location("hw_parallel_migration", SCRIPT)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def write(path: Path, data: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = data.encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


class ShadowParityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name) / 'baseline'
        self.candidate = Path(self.tmp.name) / 'candidate'
        self.base.mkdir(); self.candidate.mkdir()
        h = write(self.base / 'source/asset.dat', 'immutable artist source')
        write(self.candidate / 'source/asset.dat', 'immutable artist source')
        write(self.base / 'results/map.json', '{"height": 1,"layers":["cliff","water"]}')
        write(self.candidate / 'results/map.json', '{"layers":["cliff","water"], "height":1}')
        self.fixture = Path(self.tmp.name) / 'fixture.json'
        self.value = {"schema": tool.SCHEMA, "id": "plus-one-pond",
                      "inputs": [{"path": "source/asset.dat", "sha256": h}],
                      "outputs": [{"path": "results/map.json", "comparison": "json", "policy": "preserve"}]}
        self.save_fixture()

    def tearDown(self):
        self.tmp.cleanup()

    def save_fixture(self):
        self.fixture.write_text(json.dumps(self.value), encoding='utf-8')

    def test_semantically_equivalent_json_and_source_hash_pass_diagnostic(self):
        out = tool.compare_fixture(self.base, self.candidate, self.fixture)
        self.assertEqual(out['status'], 'MATCH_DIAGNOSTIC_ONLY')
        self.assertFalse(out['runtimeParityCertified'])
        self.assertEqual(out['pccFullGate'], 'NOT_RUN')

    def test_unreviewed_semantic_change_blocks(self):
        write(self.candidate / 'results/map.json', '{"height":2,"layers":["cliff","water"]}')
        out = tool.compare_fixture(self.base, self.candidate, self.fixture)
        self.assertEqual(out['status'], 'BLOCKED')
        self.assertEqual(out['cases'][-1]['firstDifference'], '$.height: value differs')

    def test_intentional_spec_difference_requires_separate_approval(self):
        candidate_json = '{"height":2,"layers":["cliff","water"]}'
        write(self.candidate / 'results/map.json', candidate_json)
        self.value['outputs'][0].update({'policy':'intentional',
            'expectedBaselineSha256': tool.digest((self.base/'results/map.json').read_bytes()),
            'expectedCandidateSha256': tool.digest(candidate_json.encode()),
            'rationale':'Intentional normalized behavior follows the newer elevation contract.'})
        self.save_fixture()
        self.assertEqual(tool.compare_fixture(self.base,self.candidate,self.fixture)['status'],
                         'REQUIRES_SPECIFICATION_APPROVAL')
        write(self.candidate / 'results/map.json', '{"height":3}')
        self.assertEqual(tool.compare_fixture(self.base,self.candidate,self.fixture)['status'], 'BLOCKED')

    def test_json_number_type_difference_blocks(self):
        write(self.candidate / 'results/map.json', '{"height":1.0,"layers":["cliff","water"]}')
        out=tool.compare_fixture(self.base,self.candidate,self.fixture)
        self.assertEqual(out['status'],'BLOCKED')
        self.assertIn('type differs', out['cases'][-1]['firstDifference'])

    def test_missing_output_is_rejected(self):
        (self.candidate/'results/map.json').unlink()
        with self.assertRaises(FileNotFoundError):
            tool.compare_fixture(self.base,self.candidate,self.fixture)

    def test_modified_immutable_input_blocks(self):
        write(self.candidate/'source/asset.dat', 'modified')
        self.assertEqual(tool.compare_fixture(self.base,self.candidate,self.fixture)['status'], 'BLOCKED')

    def test_fixture_paths_portable_on_windows_but_unsafe_input_rejected(self):
        # Simulate Windows Path behavior even when this suite runs on Linux.
        self.assertEqual(str(PureWindowsPath('source/asset.dat')), 'source\\asset.dat')
        with patch.object(tool, 'safe_rel', return_value=PureWindowsPath('source/asset.dat')):
            self.assertEqual(tool.canonical_rel('source/asset.dat'), 'source/asset.dat')
        self.assertEqual(tool.canonical_rel('source/asset.dat'), 'source/asset.dat')
        for invalid in (r'source\asset.dat', '../outside', 'C:/absolute', '', None):
            with self.subTest(invalid=invalid), self.assertRaises(tool.EvidenceError):
                tool.canonical_rel(invalid)

    def test_duplicate_and_traversal_paths_rejected(self):
        self.value['outputs'][0]['path'] = '../outside'
        self.save_fixture()
        with self.assertRaises(tool.EvidenceError):
            tool.compare_fixture(self.base,self.candidate,self.fixture)
        self.value['outputs'][0]['path'] = 'source/asset.dat'
        self.save_fixture()
        with self.assertRaises(tool.EvidenceError):
            tool.compare_fixture(self.base,self.candidate,self.fixture)

    def test_same_or_nested_roots_rejected(self):
        with self.assertRaises(tool.EvidenceError):
            tool.compare_fixture(self.base,self.base,self.fixture)
        with self.assertRaises(tool.EvidenceError):
            tool.compare_fixture(self.base,self.base/'source',self.fixture)

    def test_rejects_resolved_escape_without_symlink_privilege(self):
        """Exercise the actual root-boundary guard on every OS, including Windows without Developer Mode."""
        outside = Path(self.tmp.name) / 'outside.json'
        write(outside, '{}')
        outside_resolved = outside.resolve(strict=True)
        candidate_path = self.candidate / 'results/map.json'
        original_resolve = Path.resolve

        def resolve_with_redirect(path, *args, **kwargs):
            if path == candidate_path:
                return outside_resolved
            return original_resolve(path, *args, **kwargs)

        with patch.object(Path, 'resolve', resolve_with_redirect):
            with self.assertRaisesRegex(tool.EvidenceError, 'escapes root'):
                tool.compare_fixture(self.base, self.candidate, self.fixture)

    def test_rejects_symlink_escape(self):
        outside = Path(self.tmp.name) / 'outside.json'
        write(outside, '{}')
        destination = self.candidate / 'results/map.json'
        destination.unlink()
        try:
            destination.symlink_to(outside)
        except OSError as exc:
            # Windows without Developer Mode/admin privileges returns WinError 1314.
            # The privilege gate is not a product failure; the independent root-boundary
            # test above still exercises the security property on this machine.
            if getattr(exc, 'winerror', None) == 1314:
                self.skipTest('Windows account lacks symlink creation privilege (WinError 1314)')
            raise
        with self.assertRaisesRegex(tool.EvidenceError, 'escapes root'):
            tool.compare_fixture(self.base, self.candidate, self.fixture)

    def test_receipts_never_written_inside_sources(self):
        with self.assertRaises(tool.EvidenceError):
            tool.write_receipt({'status':'BLOCKED'},self.base/'receipt.json',[self.base,self.candidate])
        self.assertFalse((self.base/'receipt.json').exists())
        external = Path(self.tmp.name)/'reports/receipt.json'
        tool.write_receipt({'status':'BLOCKED'},external,[self.base,self.candidate])
        self.assertEqual(json.loads(external.read_text())['status'],'BLOCKED')

    def test_evidence_lock_fails_closed_without_git_or_ledger(self):
        report=tool.evidence_lock(self.base)
        self.assertEqual(report['status'],'EVIDENCE_INCOMPLETE')
        self.assertIsNone(report['lastApplied'])
        self.assertEqual(report['pccFullGate'],'NOT_RUN')

    def test_inventory_does_not_call_static_paths_live(self):
        record=tool.policy_inventory(self.base)
        self.assertTrue(all(r['runtimeActive'] != True for r in record['contracts']))

    def test_inventory_cli_does_not_crash(self):
        self.assertEqual(tool.main(['inventory','--root',str(self.base)]), 0)

    def test_bad_intentional_declaration_rejected(self):
        self.value['outputs'][0]['policy']='intentional'
        self.save_fixture()
        with self.assertRaises(tool.EvidenceError):
            tool.compare_fixture(self.base,self.candidate,self.fixture)


if __name__ == '__main__':
    unittest.main()
