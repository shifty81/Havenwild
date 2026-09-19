"""PCC candidate normalization tests: no Rust/GPU/Windows certification is inferred."""
from __future__ import annotations
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

CANDIDATE = Path(__file__).resolve().parents[1]
ROOT = CANDIDATE.parents[1]
SCRIPT = CANDIDATE / 'tools/candidate_gate.py'
spec = importlib.util.spec_from_file_location('hw_candidate_gate', SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def done(cmd, code=0, text=''):
    return subprocess.CompletedProcess(cmd, code, stdout=text, stderr='')


class CandidateGateTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.candidate = self.root / gate.CANDIDATE
        self.candidate.mkdir(parents=True)
        for path in ('Cargo.toml', 'tools/forge/HavenwildPccProvider.py'):
            dst = self.root / path
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text('root provider' if path.endswith('py') else '[workspace]')
        (self.candidate / 'Cargo.toml').write_text((CANDIDATE / 'Cargo.toml').read_text())
        self.source = self.candidate / gate.SOURCE
        self.source.parent.mkdir(parents=True)
        self.source.write_bytes(b'original source bytes')
        self.credits = self.candidate / gate.CREDITS
        self.credits.write_bytes(b'artist credits')
        self.fixture = self.root / gate.SCENE
        self.fixture.parent.mkdir(parents=True)
        self.scene = {'kind': 'worldgen_scene', 'tileSize': [32, 32], 'sceneId': 'real-fixture',
                      'sceneSize': [40, 28], 'layers': {'terrain': [['Grass']*16 + ['MudBank','RiverWater','RiverWater','RiverWater','RiverWater','RiverWater','MudBank'] + ['Grass']*17 for _ in range(28)]}}
        self.fixture.write_text(json.dumps(self.scene))
        self.receipt = self.candidate / gate.RECEIPT
        self.receipt.parent.mkdir(parents=True)
        self.receipt.write_text(json.dumps({
            'sourceSha256': gate.digest(self.source.read_bytes()),
            'creditsSha256': gate.digest(self.credits.read_bytes()),
            'publicationStatus': 'candidate_only', 'originalSourceMutated': False,
            'canonicalSaveMutated': False, 'branch': 'experimental', 'baselineAncestor': True,
            'fixture': {'path': gate.SCENE.as_posix(),
                        'sha256': gate.digest(self.fixture.read_bytes()),
                        'sceneId': self.scene['sceneId'], 'dimensions': [40, 28]},
        }))
        # Test-only explicit historical donor and pinned candidate role binding.
        # No production asset or source is modified by this test setup.
        historical = self.root / 'content/assets/intake/lpc_terrain_family_mapping_v0_3.json'
        historical.parent.mkdir(parents=True)
        historical.write_text(json.dumps({
            'schema':'havenwild.lpc_terrain_family_mapping.v0_4',
            'source':'assets/source/licensed/lpc_revised/Terrain/terrain_summer.png',
            'cellSize':32,'grid':[16,26],
            'baseTiles':{'grass':{'cells':[[3,1]]},'river_water':{'cells':[[12,16]]},
                         'mud_bank':{'cells':[[3,4]]}}
        }))
        bindings = self.root / 'content/architecture/havenwild_bevy_draft_role_bindings_v0_1.json'
        bindings.parent.mkdir(parents=True,exist_ok=True)
        binding = json.loads((ROOT/'content/architecture/havenwild_bevy_draft_role_bindings_v0_1.json').read_text())
        binding['sourceSha256'] = gate.digest(self.source.read_bytes())
        binding['historicalMappingSha256'] = gate.digest(historical.read_bytes())
        bindings.write_text(json.dumps(binding))
        self.source_pin = patch.object(gate, 'SOURCE_SHA', gate.digest(self.source.read_bytes()))
        self.source_pin.start()
        self.addCleanup(self.source_pin.stop)
        self.git_pin = patch.object(gate, 'git', side_effect=lambda root, *args: (
            done(args, text='experimental\n') if 'symbolic-ref' in args else
            done(args, text=gate.BASELINE+'\n') if 'rev-parse' in args else done(args)
        ))
        self.mock_git = self.git_pin.start()
        self.addCleanup(self.git_pin.stop)

    def test_verifies_actual_inputs_without_certification_claim(self):
        result = gate.verify(self.root)
        self.assertEqual(result['semanticCells'], 1120)
        self.assertFalse(result['sourceExactArtApproved'])
        self.assertFalse(result['worldRendererParity'])
        self.assertEqual(result['pccFullGate'], 'NOT_RUN_BY_THIS_TOOL')

    def test_main_or_detached_branch_rejected(self):
        self.mock_git.side_effect = lambda root, *args: (
            done(args, text='main\n') if 'symbolic-ref' in args else done(args, text=gate.BASELINE+'\n'))
        with self.assertRaisesRegex(gate.GateError, 'Experimental branch'):
            gate.verify(self.root)

    def test_wrong_ancestry_rejected(self):
        self.mock_git.side_effect = lambda root, *args: (
            done(args, text='experimental\n') if 'symbolic-ref' in args else
            done(args, text=gate.BASELINE+'\n') if 'rev-parse' in args else done(args, code=1))
        with self.assertRaisesRegex(gate.GateError, 'descended'):
            gate.verify(self.root)

    def test_staging_receipt_from_main_or_unknown_lane_rejected(self):
        evidence = json.loads(self.receipt.read_text())
        evidence['branch'] = 'main'
        self.receipt.write_text(json.dumps(evidence))
        with self.assertRaisesRegex(gate.GateError, 'Stale/incorrect'):
            gate.verify(self.root)
        evidence['branch'] = 'experimental'
        evidence['baselineAncestor'] = None
        self.receipt.write_text(json.dumps(evidence))
        with self.assertRaisesRegex(gate.GateError, 'Stale/incorrect'):
            gate.verify(self.root)

    def test_source_tamper_rejected(self):
        self.source.write_bytes(b'tampered')
        with self.assertRaisesRegex(gate.GateError, 'source bytes differ'):
            gate.verify(self.root)

    def test_credits_tamper_rejected(self):
        self.credits.write_bytes(b'tampered')
        with self.assertRaisesRegex(gate.GateError, 'Stale/incorrect'):
            gate.verify(self.root)

    def test_fixture_mutation_rejected(self):
        self.scene['layers']['terrain'][0][0] = 'NotGrass'
        self.fixture.write_text(json.dumps(self.scene))
        with self.assertRaisesRegex(gate.GateError, 'changed since source staging'):
            gate.verify(self.root)

    def test_malformed_grid_rejected_even_with_new_receipt(self):
        self.scene['layers']['terrain'] = [['Grass']]
        self.fixture.write_text(json.dumps(self.scene))
        evidence = json.loads(self.receipt.read_text())
        evidence['fixture']['sha256'] = gate.digest(self.fixture.read_bytes())
        self.receipt.write_text(json.dumps(evidence))
        with self.assertRaisesRegex(gate.GateError, 'incomplete'):
            gate.verify(self.root)

    def test_missing_receipt_rejected(self):
        self.receipt.unlink()
        with self.assertRaisesRegex(gate.GateError, 'receipt are missing'):
            gate.verify(self.root)

    def test_incorrect_publication_status_rejected(self):
        evidence = json.loads(self.receipt.read_text())
        evidence['publicationStatus'] = 'certified'
        self.receipt.write_text(json.dumps(evidence))
        with self.assertRaisesRegex(gate.GateError, 'Stale/incorrect'):
            gate.verify(self.root)

    def test_candidate_symlink_rejected(self):
        alternative = self.root / 'fake-source'
        alternative.write_bytes(self.source.read_bytes())
        self.source.unlink()
        try:
            self.source.symlink_to(alternative)
        except (OSError, NotImplementedError):
            self.skipTest('OS does not permit symlinks')
        with self.assertRaisesRegex(gate.GateError, 'symlink'):
            gate.verify(self.root)

    def test_cargo_only_after_verified_source_and_correct_manifest(self):
        with patch.object(gate.subprocess, 'call', return_value=0) as cargo:
            self.assertEqual(gate.run(self.root, 'build'), 0)
            args,kwargs = cargo.call_args
            self.assertEqual(args[0][0:2], ['cargo', 'check'])
            self.assertEqual(Path(args[0][3]), self.candidate/'Cargo.toml')
            self.assertEqual(kwargs['cwd'], self.candidate)
            cargo.reset_mock()
            self.source.write_bytes(b'altered')
            with self.assertRaises(gate.GateError):
                gate.run(self.root, 'run')
            cargo.assert_not_called()

    def test_scene_plan_is_pcc_gated_and_candidate_only(self):
        self.assertEqual(gate.run(self.root, 'scene-plan'), 0)
        output = self.candidate / 'evidence/semantic_scene_plan.json'
        self.assertTrue(output.is_file())
        plan = json.loads(output.read_text())
        self.assertEqual(plan['semanticCellCount'], 1120)
        self.assertEqual(plan['unmappedCellCount'], 1120)
        self.assertEqual(plan['approvedDrawCallCount'], 0)
        self.assertFalse(plan['worldRendererParity'])
        self.assertEqual(plan['cells'][0]['terrainRole'], 'Grass')
        self.assertFalse((self.root/'evidence/semantic_scene_plan.json').exists())

    def test_scene_plan_refuses_fixture_change_before_writing(self):
        self.fixture.write_text(self.fixture.read_text() + ' ')
        with self.assertRaisesRegex(gate.GateError, 'changed since source staging'):
            gate.run(self.root, 'scene-plan')
        self.assertFalse((self.candidate/'evidence/semantic_scene_plan.json').exists())

    def test_gpu_draft_pcc_action_stays_unapproved_and_isolated(self):
        self.assertEqual(gate.run(self.root, 'draft-plan'), 0)
        path=self.candidate/'evidence/draft_source_draw_plan.json'
        value=json.loads(path.read_text())
        self.assertEqual(value['unreviewedDrawCount'],1120)
        self.assertEqual(value['approvedDrawCallCount'],0)
        self.assertFalse(value['sourceExactArtApproved'])
        self.assertFalse(value['runtimePublicationAllowed'])
        self.assertEqual(value['draws'][0]['sourceRectPx'],[96,32,32,32])
        self.assertFalse((self.root/'evidence/draft_source_draw_plan.json').exists())

    def test_gpu_draft_missing_historical_mapping_blocks_cargo(self):
        (self.root/'content/assets/intake/lpc_terrain_family_mapping_v0_3.json').unlink()
        with patch.object(gate.subprocess,'call',return_value=0) as cargo:
            with self.assertRaises(OSError):gate.run(self.root,'build')
            cargo.assert_not_called()

    def test_gpu_draft_claimed_art_approval_blocks_cargo(self):
        path=self.root/'content/architecture/havenwild_bevy_draft_role_bindings_v0_1.json'
        cfg=json.loads(path.read_text());cfg['sourceArtApproval']=True
        path.write_text(json.dumps(cfg))
        with patch.object(gate.subprocess,'call',return_value=0) as cargo:
            with self.assertRaises(ValueError):gate.run(self.root,'run')
            cargo.assert_not_called()

    def test_pcc_registration_has_single_authority(self):
        ext=(ROOT/'tools/control/PccCommandExtensions.ps1').read_text()
        host=(ROOT/'tools/control/PccCommandHost.ps1').read_text()
        script=(ROOT/'tools/control/HavenwildBevyCandidate.ps1').read_text()
        for action in ['status', 'verify', 'scene-plan', 'draft-plan', 'build', 'run']:
            self.assertEqual(ext.count("Key='experimental.bevy."+action+"'"), 1)
            self.assertIn("'experimental.bevy."+action+"'", host)
        self.assertIn('Invoke-PccCommandKey', host)
        self.assertIn('candidate_gate.py', script)
        self.assertNotIn('InvokeRootPatchIntake.ps1', script)
        self.assertNotIn('HavenwildTools.cmd', script)

    def test_run_hydrates_only_absent_inputs_before_cargo(self):
        saved=(self.source.read_bytes(),self.credits.read_bytes(),self.receipt.read_bytes())
        self.source.unlink();self.credits.unlink();self.receipt.unlink()
        def hydrate(root):
            self.source.write_bytes(saved[0]);self.credits.write_bytes(saved[1]);self.receipt.write_bytes(saved[2])
        with patch.object(gate,'prepare_missing_inputs',side_effect=hydrate) as staging, \
             patch.object(gate.subprocess,'call',return_value=0) as cargo:
            self.assertEqual(gate.run(self.root,'run'),0)
            staging.assert_called_once_with(self.root)
            cargo.assert_called_once()

    def test_run_never_repairs_a_tampered_staged_source(self):
        self.source.write_bytes(b'tampered')
        with patch.object(gate,'prepare_missing_inputs',wraps=gate.prepare_missing_inputs) as staging, \
             patch.object(gate.subprocess,'call',return_value=0) as cargo:
            with self.assertRaisesRegex(gate.GateError,'source bytes differ'):
                gate.run(self.root,'run')
            staging.assert_called_once()
            cargo.assert_not_called()

    def test_run_rejects_incomplete_source_with_receipt(self):
        self.credits.unlink()
        with patch.object(gate.subprocess,'call',return_value=0) as cargo:
            with self.assertRaisesRegex(gate.GateError,'inconsistent evidence'):
                gate.run(self.root,'run')
            cargo.assert_not_called()

    def test_verify_remains_read_only_when_stage_missing(self):
        self.source.unlink();self.credits.unlink();self.receipt.unlink()
        with patch.object(gate,'prepare_missing_inputs') as staging:
            with self.assertRaisesRegex(gate.GateError,'missing'):
                gate.run(self.root,'verify')
            staging.assert_not_called()

    def test_branch_checked_before_source_auto_discovery(self):
        self.source.unlink();self.credits.unlink();self.receipt.unlink()
        self.mock_git.side_effect=lambda root,*args: (
            done(args,text='main\n') if 'symbolic-ref' in args else
            done(args,text=gate.BASELINE+'\n'))
        with patch.object(gate.subprocess,'call',return_value=0) as cargo:
            with self.assertRaisesRegex(gate.GateError,'Experimental branch'):
                gate.run(self.root,'run')
            self.assertFalse((self.candidate/'evidence/source_stage.json').exists())
            cargo.assert_not_called()


if __name__=='__main__':
    unittest.main()
