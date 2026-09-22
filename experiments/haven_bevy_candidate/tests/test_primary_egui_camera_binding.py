"""The ForgeGUI context must stay on the primary window, never an offscreen camera.

Static source guard only: this does not claim GPU frame or PIE certification.
"""
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "src/main.rs"


class PrimaryEguiCameraBindingContracts(unittest.TestCase):
    def test_primary_context_pinned_before_offscreen_cameras(self):
        code = SOURCE.read_text(encoding="utf-8")
        setup = code.split("fn setup(", 1)[1].split("fn report_original_sheet(", 1)[0]
        settings = setup.index("egui_settings.auto_create_primary_context = false;")
        primary = setup.index("commands.spawn((Camera2d, PrimaryEguiContext));")
        first_offscreen = setup.index("RenderTarget::Image(")
        self.assertLess(settings, primary)
        self.assertLess(primary, first_offscreen)
        self.assertEqual(setup.count("commands.spawn((Camera2d, PrimaryEguiContext));"), 1)
        self.assertNotIn("commands.spawn(Camera2d);", setup)

    def test_gpu_draft_still_not_canonical(self):
        code = SOURCE.read_text(encoding="utf-8")
        self.assertIn("0 approved draw calls", code)
        self.assertIn("GPU screenshot NOT verified", code)


if __name__ == "__main__":
    unittest.main()
