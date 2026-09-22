"""Static guard for the Bevy/egui candidate's offscreen render-target format.

Does not certify GPU rendering, source-art mapping, game parity, or PIE.
"""
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "src/main.rs"


class OffscreenTextureFormatContracts(unittest.TestCase):
    def test_source_preview_uses_egui_compatible_rgba_srgb(self):
        rust = SOURCE.read_text(encoding="utf-8")
        preview = rust.split('label: Some("havenwild.source.preview")', 1)[1]
        preview = preview.split("let target_handle = images.add(target)", 1)[0]
        self.assertIn("format: TextureFormat::Rgba8UnormSrgb,", preview)

    def test_river_target_uses_egui_compatible_rgba_srgb(self):
        rust = SOURCE.read_text(encoding="utf-8")
        draft = rust.split('label: Some("havenwild.unapproved_world_draft")', 1)[1]
        draft = draft.split("let handle=images.add(world_target)", 1)[0]
        self.assertIn("format:TextureFormat::Rgba8UnormSrgb,", draft)
        self.assertNotIn("Bgra8UnormSrgb", rust)

    def test_draft_remains_unapproved(self):
        rust = SOURCE.read_text(encoding="utf-8")
        self.assertIn("0 approved draw calls", rust)
        self.assertIn("no world rendering parity claimed", rust)
