"""Experimental safety-contract checks. Rust execution and GPU truth require Windows tests."""
import importlib.util
import json
import os
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
CANDIDATE = ROOT / 'experiments/haven_bevy_candidate'
spec = importlib.util.spec_from_file_location('candidate_gate_gpu', CANDIDATE / 'tools/candidate_gate.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class GpuDifferentialAndViewport(TestCase):
    def test_gpu_modes_registered_in_one_pcc_and_no_second_launcher(self):
        extension = (ROOT/'tools/control/PccCommandExtensions.ps1').read_text()
        host = (ROOT/'tools/control/PccCommandHost.ps1').read_text()
        action = (ROOT/'tools/control/HavenwildBevyCandidate.ps1').read_text()
        for key, name in [('run-dx12','RunDx12'), ('run-primary-probe','RunPrimaryProbe'),
                          ('run-dx12-primary-probe','RunDx12PrimaryProbe')]:
            self.assertIn('experimental.bevy.'+key, extension)
            self.assertIn('experimental.bevy.'+key, host)
            self.assertIn(name, host)
            self.assertIn(name, action)
        self.assertIn("$env:WGPU_BACKEND='dx12'", action)
        self.assertIn("$env:HAVENWILD_BEVY_PRIMARY_ONLY='1'", action)
        self.assertIn('return [int]$result', host)
    def test_probe_has_one_primary_camera_and_skips_both_offscreen_targets(self):
        src = (CANDIDATE/'src/main.rs').read_text()
        setup = src.split('fn setup(', 1)[1].split('fn report_original_sheet(',1)[0]
        self.assertIn('commands.spawn(Camera2d);', setup)
        first=setup.index('if state.content.primary_only {')
        self.assertLess(first, setup.index('RenderTarget::Image'))
        self.assertLess(first, setup.index('PreviewTarget(target_handle.clone())'))
        self.assertLess(first, setup.index('DraftTarget(handle.clone())'))
        self.assertIn('return;', setup[first:first+225])
        self.assertIn('image: Option<Res<PreviewTarget>>', src)
        self.assertIn('draft_image: Option<Res<DraftTarget>>', src)
        self.assertIn('source.primary_only = primary_only;', src)
    def test_viewport_is_presentation_only_and_pixel_precise(self):
        src=(CANDIDATE/'src/main.rs').read_text()
        vp=(CANDIDATE/'src/viewport.rs').read_text()
        for part in ('fn zoom_by(', 'fn image_rect(', 'fn cell_at(', 'fn cell_rect(', 'fn clamp_pan(', 'fn paint_grid('):
            self.assertIn(part, vp)
        self.assertIn('painter.image(texture_id, image_rect', src)
        self.assertIn('i.smooth_scroll_delta.y', src)
        self.assertNotIn('i.raw_scroll_delta', src)
        self.assertIn('self.world_view.cell_at(point, image_rect, self.scene_size)', src)
        self.assertIn('self.world_view.paint_grid(&painter, image_rect, self.scene_size)', src)
        self.assertIn('Neighbor topology is semantic only', src)
        self.assertIn('NOT APPROVED', src)
        self.assertNotIn('save_world_to_path', vp)
        self.assertIn('worldRendererParity', (CANDIDATE/'tools/candidate_gate.py').read_text())
    def test_run_receipt_never_claims_gpu_validation(self):
        text=(CANDIDATE/'tools/candidate_gate.py').read_text()
        self.assertIn("'gpuRendered':None",text)
        self.assertIn("'gpuValidation':'NOT_CAPTURED_BY_THIS_CARGO_EXIT_RECEIPT'",text)
        self.assertIn("'actualGpuBackend':'SEE_BEVY_ADAPTER_INFO_NOT_INFERRED'",text)
        self.assertIn("'primaryOnlyProbe':probe == '1'",text)
    def test_original_source_and_legacy_runtime_not_replaced(self):
        manifest=json.loads((ROOT/'content/architecture/havenwild_bevy_draft_role_bindings_v0_1.json').read_text())
        self.assertFalse(manifest['runtimePublicationAllowed'])
        self.assertFalse(manifest['sourceArtApproval'])
        self.assertFalse(manifest['worldRendererParity'])

if __name__ == '__main__': main()
