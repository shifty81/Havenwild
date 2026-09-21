"""Contract guard for Rust E0308 caught by the first real Windows candidate build.

This is static regression coverage only; it is not a Rust compile or a GPU test.
The parent-Ui integration is sourced from bevy_egui 0.42's example/ui.rs.
"""
from pathlib import Path
import re
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'src/main.rs'


class EguiRootUiContractTests(unittest.TestCase):
    def test_root_context_is_converted_to_viewport_ui_before_panel(self):
        rust = SOURCE.read_text(encoding='utf-8')
        gui = rust.split('fn gui(', 1)[1].split('\nfn main()', 1)[0]
        self.assertIn('let ctx = contexts.ctx_mut()?;', gui)
        self.assertIn('let mut viewport_ui = egui::Ui::new(', gui)
        self.assertIn('ctx.clone(),', gui)
        self.assertIn('egui::UiBuilder::new()', gui)
        self.assertIn('.layer_id(egui::LayerId::background())', gui)
        self.assertIn('.max_rect(ctx.viewport_rect())', gui)
        self.assertLess(gui.index('let mut viewport_ui'), gui.index('egui::CentralPanel'))
        self.assertEqual(gui.count('egui::CentralPanel::default().show(&mut viewport_ui, |root| {'), 1)

    def test_forge_shell_receives_ui_and_same_context(self):
        rust = SOURCE.read_text(encoding='utf-8')
        gui = rust.split('fn gui(', 1)[1].split('\nfn main()', 1)[0]
        self.assertIn('show_application_shell(root, ctx, spec, shell, theme, content);', gui)
        self.assertNotRegex(gui, r'CentralPanel::default\(\)\.show\(ctx\s*,')
        self.assertNotIn('show_application_shell(ctx,', gui)

    def test_original_source_and_draft_constraints_untouched(self):
        rust = SOURCE.read_text(encoding='utf-8')
        self.assertIn('const SOURCE_SHA: &str = "1251a6ea556330190ccb1e3af166eb69fbec4b7a3f7d51c1f54728abd75bd752"', rust)
        self.assertIn('UNAPPROVED', rust)
        self.assertIn('let sheet: Handle<Image> = asset_server.load(SOURCE_REL);', rust)
        self.assertIn('Sprite::from_image(sheet.clone())', rust)
        self.assertEqual(rust.count('asset_server.load(SOURCE_REL)'), 1)
        self.assertIn('draft_source_cells.iter().enumerate()', rust)
        self.assertNotIn('macroquad::', rust)


if __name__ == '__main__':
    unittest.main()
