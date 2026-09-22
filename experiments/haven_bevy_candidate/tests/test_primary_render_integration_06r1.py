"""Source contract only; hardware presentation requires user's Windows screenshot."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / 'src/main.rs').read_text(encoding='utf-8')
DIRECT = (ROOT / 'src/direct_atlas.rs').read_text(encoding='utf-8')

class CumulativeRenderContracts(unittest.TestCase):
    def test_primary_gui_camera_cannot_follow_offscreen(self):
        setup = MAIN.split('fn setup(',1)[1].split('fn report_original_sheet(',1)[0]
        self.assertIn('egui_settings.auto_create_primary_context = false;',setup)
        self.assertIn('commands.spawn((Camera2d, PrimaryEguiContext));',setup)
        self.assertLess(setup.index('PrimaryEguiContext));'),setup.index('RenderTarget::Image('))

    def test_normal_full_mode_renders_direct_atlas_without_offscreen(self):
        setup = MAIN.split('fn setup(',1)[1].split('fn report_original_sheet(',1)[0]
        branch = setup.split('if std::env::var("HAVENWILD_BEVY_OFFSCREEN_PROBE")',1)[1].split('let size = Extent3d',1)[0]
        self.assertIn('egui_textures.add_image(EguiTextureHandle::Strong(sheet.clone()));',branch)
        self.assertIn('return;',branch)
        self.assertIn('direct_atlas::draw_tiles(',MAIN)
        self.assertIn('painter.image(texture, tile_rect, uv, egui::Color32::WHITE);',DIRECT)

    def test_gpu_error_exit_and_approval_truth(self):
        self.assertIn('fn main() -> bevy::app::AppExit',MAIN)
        self.assertIn('.run()\n}',MAIN)
        self.assertIn('0 approved draw calls',MAIN)
        self.assertIn('GPU frame NOT screenshot-verified',MAIN)
        self.assertNotIn('fn main() {',MAIN)

if __name__ == '__main__': unittest.main()
