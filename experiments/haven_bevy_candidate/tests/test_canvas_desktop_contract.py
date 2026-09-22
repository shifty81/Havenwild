"""Contract guard for the candidate-only canvas desktop; not GPU certification."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / 'src/main.rs'
DESKTOP = ROOT / 'src/desktop.rs'

class CanvasDesktopContracts(unittest.TestCase):
    def test_game_canvas_only_center_surface(self):
        src = MAIN.read_text(encoding='utf-8')
        setup = src.split('let mut shell = ForgeShellState::new(', 1)[1].split('    App::new()', 1)[0]
        center = re.findall(r'ModularSurfaceState::new\([^\n]*SurfaceDock::Center\)', setup)
        self.assertEqual(len(center), 1, center)
        self.assertIn('"world_draft"', center[0])
        self.assertIn('shell.hide_surface(id);', setup)
        self.assertIn('desktop::show_task_shelf(root, shell);', src)
        self.assertIn('shell.open_surface("world_draft");', src)

    def test_only_real_tools_registered_no_fake_studio_shortcuts(self):
        code = DESKTOP.read_text(encoding='utf-8')
        main = MAIN.read_text(encoding='utf-8')
        ids = re.findall(r'^    \("([a-z_]+)", "[^"\n]+"\),$', code, flags=re.M)
        self.assertEqual(len(ids), 7)
        for identity in ids:
            self.assertIn(f'ModularSurfaceState::new("{identity}"', main)
        self.assertNotIn('("pixel_studio",', code)
        self.assertNotIn('("animation_studio",', code)
        self.assertIn('No fake Pixel/Animation/Logic/Sound', code)

    def test_existing_authorities_not_replaced(self):
        main = MAIN.read_text(encoding='utf-8')
        self.assertIn('verify_source_and_scene()', main)
        self.assertIn('show_application_shell(root, ctx, spec, shell, theme, content)', main)
        self.assertIn('sourceExactArtApproved', (ROOT / 'tools/candidate_gate.py').read_text(encoding='utf-8'))

if __name__ == '__main__':
    unittest.main()
