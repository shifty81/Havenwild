"""C7-C16 independent infrastructure tests; no Windows/GPU/PIE claims."""
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

TOOL = Path(__file__).resolve().parents[1] / 'tools'
ROOT = TOOL.parents[2]
sys.path.insert(0,str(TOOL))
import experiment_spine as spine
import draft_source_draw_plan as draft
import semantic_scene_plan as semantic

class SpineTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        (self.root/'Cargo.toml').write_text('[workspace]\n')
        candidate=self.root/spine.CANDIDATE
        candidate.mkdir(parents=True)
        self.original=(ROOT/'content/worldgen/scenes/terrain_acceptance/river_scene_v1.json').read_bytes()
        self.scene=self.root/'content/worldgen/scenes/terrain_acceptance/river_scene_v1.json'
        self.scene.parent.mkdir(parents=True)
        self.scene.write_bytes(self.original)
        self.src=candidate/'assets/source/Terrain/terrain_summer.png'
        self.src.parent.mkdir(parents=True)
        self.src.write_bytes(b'original-test-only')
        self.credits=candidate/'assets/source/Terrain/Credits.txt'
        self.credits.write_bytes(b'credits-test-only')
        self.gate=SimpleNamespace(SOURCE=Path('assets/source/Terrain/terrain_summer.png'),
            CREDITS=Path('assets/source/Terrain/Credits.txt'),
            SCENE=Path('content/worldgen/scenes/terrain_acceptance/river_scene_v1.json'))
        self.receipt={'lineage':{'branch':'experimental'},'sourceExactArtApproved':False,
            'worldRendererParity':False,'pieCertified':False,'sourceSha256':spine.sha(self.src.read_bytes()),
            'sceneSha256':spine.sha(self.original),'sceneId':'terrain_acceptance_river','size':[40,28]}
        m=self.root/'content/assets/intake/lpc_terrain_family_mapping_v0_3.json'
        m.parent.mkdir(parents=True)
        m.write_bytes((ROOT/'content/assets/intake/lpc_terrain_family_mapping_v0_3.json').read_bytes())
        self.mapping=m
        b=self.root/draft.BINDINGS
        b.parent.mkdir(parents=True)
        binding=json.loads((ROOT/draft.BINDINGS).read_text())
        binding['sourceSha256']=self.receipt['sourceSha256']
        binding['historicalMappingSha256']=spine.sha(m.read_bytes())
        b.write_text(json.dumps(binding))
        self.binding=b

    def open(self):
        return spine.open_session(self.root,self.receipt,self.gate)

    def edit(self,role='MudBank', command_id='edit-1',revision=0,x=0,y=0):
        return spine.edit(self.root,self.receipt,self.gate,command_id=command_id,
                          expected_revision=revision,x=x,y=y,role=role)

    def draft_receipt(self):
        sem=semantic.compile_plan(self.original,source_sha=self.receipt['sourceSha256'],
                                  fixture_sha=self.receipt['sceneSha256'])
        plan=draft.compile_draft(sem,self.mapping.read_bytes(),self.binding.read_bytes(),
                                 source_hash=self.receipt['sourceSha256'],fixture_hash=self.receipt['sceneSha256'])
        target=self.root/spine.CANDIDATE/'evidence/draft_source_draw_plan.json'
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(plan))
        return target

    def test_c7_context_has_one_pcc_and_no_publication(self):
        report=spine.context(self.root,self.receipt,self.gate)
        self.assertEqual(report['sceneId'],'terrain_acceptance_river')
        self.assertIn('HavenwildPccHost.ps1',report['pccAuthority'])
        self.assertFalse(report['canonicalSaveWriteAllowed'])
        self.assertFalse(report['actualGamePie'])

    def test_c8_source_stack_is_hash_verified_not_art_approved(self):
        stack=spine.source_stack(self.root,self.receipt,self.gate)
        self.assertEqual(stack['entries'][0]['creditsSha256'],spine.sha(self.credits.read_bytes()))
        self.assertFalse(stack['entries'][0]['visualApproval'])
        self.src.write_bytes(b'changed')
        with self.assertRaisesRegex(spine.SpineError,'source mismatched'):
            spine.source_stack(self.root,self.receipt,self.gate)

    def test_c9_open_is_isolated_and_repeat_open_does_not_reset(self):
        original=self.scene.read_bytes()
        session=self.open()
        self.assertEqual(session['documentRevision'],0)
        self.assertEqual(session['document']['sceneSize'],[40,28])
        self.edit()
        self.assertEqual(self.open()['documentRevision'],1)
        self.assertEqual(self.scene.read_bytes(),original)

    def test_c10_optimistic_revision_and_command_identity(self):
        self.open()
        self.edit()
        with self.assertRaisesRegex(spine.SpineError,'Stale edit revision'):
            self.edit(command_id='edit-2',revision=0)
        with self.assertRaisesRegex(spine.SpineError,'Command ID already used'):
            self.edit(command_id='edit-1',revision=1)
        with self.assertRaisesRegex(spine.SpineError,'source-supported'):
            self.edit(role='CliffFake',command_id='edit-3',revision=1)

    def test_c11_undo_redo_and_branching_revisions(self):
        self.open();self.edit()
        before=spine.step_history(self.root,self.receipt,self.gate,mode='undo',expected_revision=1)
        self.assertEqual(before['document']['layers']['terrain'][0][0],'Grass')
        after=spine.step_history(self.root,self.receipt,self.gate,mode='redo',expected_revision=2)
        self.assertEqual(after['document']['layers']['terrain'][0][0],'MudBank')
        spine.step_history(self.root,self.receipt,self.gate,mode='undo',expected_revision=3)
        changed=self.edit(role='RiverWater',command_id='branch-1',revision=4)
        self.assertEqual(len(changed['history']),1)
        with self.assertRaisesRegex(spine.SpineError,'Nothing available'):
            spine.step_history(self.root,self.receipt,self.gate,mode='redo',expected_revision=5)

    def test_c11_discarded_redo_id_cannot_be_reused(self):
        self.open();self.edit()
        spine.step_history(self.root,self.receipt,self.gate,mode='undo',expected_revision=1)
        self.edit(role='RiverWater',command_id='new-branch',revision=2)
        with self.assertRaisesRegex(spine.SpineError,'Command ID already used'):
            self.edit(command_id='edit-1',revision=3)

    def test_c12_single_atomic_snapshot_reopens_or_blocks_tamper(self):
        self.open();self.edit();self.assertEqual(spine.save_snapshot(self.root,self.receipt,self.gate)['revision'],1)
        self.assertEqual(spine.reopen(self.root,self.receipt,self.gate)['status'],'CANDIDATE_SAVE_REOPEN_EQUAL')
        self.assertEqual(self.scene.read_bytes(),self.original)
        path=self.root/spine.ARTIFACTS/spine.SAVED
        snapshot=json.loads(path.read_text());snapshot['document']['layers']['terrain'][0][0]='Grass'
        path.write_text(json.dumps(snapshot))
        with self.assertRaisesRegex(spine.SpineError,'snapshot evidence invalid'):
            spine.reopen(self.root,self.receipt,self.gate)

    def test_c13_mapper_queue_counts_all_cells_and_no_approval(self):
        self.open()
        queue=spine.mapper_queue(self.root,self.receipt,self.gate)
        self.assertEqual(sum(x['count'] for x in queue['roleTopologyVariants']),1120)
        self.assertGreater(len(queue['roleTopologyVariants']),3)
        self.assertFalse(queue['visuallyApproved'])
        self.assertFalse(queue['runtimePublished'])

    def test_c14_renderer_packets_contain_original_coords_no_certification(self):
        self.open();self.draft_receipt()
        packets=spine.render_packets(self.root,self.receipt,self.gate)
        self.assertEqual(packets['drawCount'],1120)
        self.assertEqual(packets['approvedDrawCount'],0)
        self.assertEqual(packets['packets'][0]['semanticTerrainRole'],'Grass')
        self.assertIsNone(packets['packets'][0]['elevation'])
        self.assertFalse(packets['runtimePublicationAllowed'])

    def test_c14_rejects_draft_receipt_changed_source_coords(self):
        self.open();path=self.draft_receipt()
        data=json.loads(path.read_text())
        data['draftRoleSourceRects']['Grass']=[0,0,32,32]
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(spine.SpineError,'differ from pinned'):
            spine.render_packets(self.root,self.receipt,self.gate)

    def test_c14_rejects_draft_receipt_changed_draw_cell(self):
        self.open();path=self.draft_receipt()
        data=json.loads(path.read_text());data['draws'][0]['sourceRectPx']=[0,0,32,32]
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(spine.SpineError,'draw entry altered'):
            spine.render_packets(self.root,self.receipt,self.gate)

    def test_c15_pie_receipt_is_snapshot_only_and_never_launches(self):
        self.open();spine.save_snapshot(self.root,self.receipt,self.gate)
        ticket=spine.pie_ticket(self.root,self.receipt,self.gate)
        self.assertFalse(ticket['launchAllowed'])
        self.assertFalse(ticket['serverAuthoritative'])
        self.assertIsNone(ticket['runtimeAck'])
        self.assertFalse(ticket['canonicalEstateMutationAllowed'])

    def test_c15_pie_requires_saved_snapshot(self):
        self.open()
        with self.assertRaises(spine.SpineError):
            spine.pie_ticket(self.root,self.receipt,self.gate)

    def test_c16_parity_reports_exact_changes_not_renderer_pass(self):
        self.open();self.edit()
        result=spine.parity(self.root,self.receipt,self.gate)
        self.assertEqual(result['changedCellCount'],1)
        self.assertEqual(result['changedCells'][0]['cell'],[0,0])
        self.assertFalse(result['worldRendererParity'])
        self.assertIsNone(result['runtimeAck'])

    def test_c16_readiness_fail_closed_and_no_green_claim(self):
        self.open();spine.source_stack(self.root,self.receipt,self.gate)
        report=spine.readiness(self.root,self.receipt,self.gate)
        self.assertTrue(report['components']['sourceStack']['present'])
        self.assertFalse(report['components']['pieTicket']['present'])
        self.assertFalse(report['macroquadRetirementAllowed'])
        self.assertFalse(report['promotionAllowed'])

    def test_replay_tamper_rejected(self):
        self.open();self.edit()
        path=self.root/spine.ARTIFACTS/spine.SESSION
        session=json.loads(path.read_text())
        session['history'][0]['before']='RiverWater'
        path.write_text(json.dumps(session))
        with self.assertRaisesRegex(spine.SpineError,'Journal replay mismatch'):
            spine.verified_session(self.root,self.receipt,self.gate)

    def test_replay_tamper_rejected_even_with_corrupt_document_hash(self):
        # Journal validation takes precedence, but never disables the document
        # checksum. This also covers the first Windows C16 gate failure.
        self.open();self.edit()
        path=self.root/spine.ARTIFACTS/spine.SESSION
        session=json.loads(path.read_text())
        session['history'][0]['before']='RiverWater'
        session['documentSha256']='0'*64
        path.write_text(json.dumps(session))
        with self.assertRaisesRegex(spine.SpineError,'Journal replay mismatch'):
            spine.verified_session(self.root,self.receipt,self.gate)

    def test_document_tamper_rejected_with_valid_journal(self):
        self.open();self.edit()
        path=self.root/spine.ARTIFACTS/spine.SESSION
        session=json.loads(path.read_text())
        # Keep a valid journal and document; tamper only with its checksum.
        session['documentSha256']='0'*64
        path.write_text(json.dumps(session))
        with self.assertRaisesRegex(spine.SpineError,'Session document hash changed without a command'):
            spine.verified_session(self.root,self.receipt,self.gate)

    def test_document_replay_difference_rejected_with_matching_hash(self):
        self.open();self.edit()
        path=self.root/spine.ARTIFACTS/spine.SESSION
        session=json.loads(path.read_text())
        # Rehashing unauthorized content must not make it a valid edit.
        session['document']['layers']['terrain'][0][0]='RiverWater'
        session['documentSha256']=spine.document_sha(session['document'])
        path.write_text(json.dumps(session))
        with self.assertRaisesRegex(spine.SpineError,'Session document differs from replayed journal'):
            spine.verified_session(self.root,self.receipt,self.gate)

    def test_elevation_one_is_real_and_missing_elevation_remains_unknown(self):
        doc=spine.fixture(self.root,self.receipt,self.gate)
        self.assertNotIn('elevation',doc['layers'])
        doc['layers']['elevation']=[[1]*40 for _ in range(28)]
        spine.check_scene(doc)
        doc['layers']['elevation'][0][0]=31
        with self.assertRaisesRegex(spine.SpineError,'Elevation'):
            spine.check_scene(doc)

    def test_candidate_symlink_denied(self):
        outside=self.root/'outside';outside.mkdir()
        evidence=self.root/spine.CANDIDATE/'evidence'
        try: evidence.symlink_to(outside)
        except (OSError,NotImplementedError):self.skipTest('OS symlinks unavailable')
        with self.assertRaisesRegex(spine.SpineError,'redirected'):
            spine.guard(self.root)

if __name__=='__main__':unittest.main()
