"""Direct atlas route: source/static checks, not proof of Windows GPU pixels."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / 'src/main.rs').read_text(encoding='utf-8')
DIRECT = (ROOT / 'src/direct_atlas.rs').read_text(encoding='utf-8')


class DirectAtlasContracts(unittest.TestCase):
    def test_default_is_single_camera_and_atlas_upload(self):
        setup = MAIN.split('fn setup(', 1)[1].split('fn report_original_sheet(', 1)[0]
        self.assertLess(setup.index('if state.content.primary_only {'), setup.index('if std::env::var("HAVENWILD_BEVY_OFFSCREEN_PROBE")'))
        branch = setup.split('if std::env::var("HAVENWILD_BEVY_OFFSCREEN_PROBE")', 1)[1].split('let size = Extent3d', 1)[0]
        self.assertIn('egui_textures.add_image(EguiTextureHandle::Strong(sheet.clone()));', branch)
        self.assertIn('return;', branch)
        self.assertIn('DIRECT_ATLAS_GPU_DRAFT', setup)
        default_branch = setup.index('if std::env::var("HAVENWILD_BEVY_OFFSCREEN_PROBE")')
        self.assertLess(setup.index('return;', default_branch), setup.index('RenderTarget::Image'))

    def test_world_and_atlas_use_exact_same_original_texture(self):
        gui = MAIN.split('fn gui(', 1)[1].split('fn main()', 1)[0]
        self.assertEqual(gui.count('contexts.image_id(&sheet.0)'), 2)
        self.assertIn('state.content.direct_atlas_mode = direct;', gui)
        self.assertIn('direct_atlas::draw_tiles(', MAIN)
        self.assertIn('painter.image(texture, tile_rect, uv, egui::Color32::WHITE);', DIRECT)
        self.assertIn('let x = cell[0] as f32 * TILE_PX as f32;', DIRECT)
        self.assertIn('let y = cell[1] as f32 * TILE_PX as f32;', DIRECT)

    def test_no_authoritative_assets_or_false_gpu_certification(self):
        self.assertIn('verify_source_and_scene()', MAIN)
        self.assertIn('0 approved draw calls', MAIN)
        self.assertIn('GPU frame NOT screenshot-verified', MAIN)
        self.assertIn('not source mapping approval, native renderer parity, or PIE', DIRECT)


if __name__ == '__main__':
    unittest.main()
