"""Static-only Bevy source residency checks; never claims Rust/GPU success."""
import unittest
from pathlib import Path

SOURCE=Path(__file__).resolve().parents[1]/'src/main.rs'

class RuntimeEvidenceContractTests(unittest.TestCase):
    def test_single_original_handle_shared_with_both_cameras(self):
        rust=SOURCE.read_text(encoding='utf-8')
        self.assertEqual(rust.count('asset_server.load(SOURCE_REL)'),1)
        self.assertIn('struct OriginalSheet(Handle<Image>);',rust)
        self.assertIn('commands.insert_resource(OriginalSheet(sheet.clone()));',rust)
        self.assertIn('Sprite::from_image(sheet.clone())',rust)
        self.assertIn('image:sheet.clone()',rust)
    def test_image_residency_is_not_misreported_as_gpu_pixels(self):
        rust=SOURCE.read_text(encoding='utf-8')
        self.assertIn('images.get(&sheet.0)',rust)
        self.assertIn('extent.width == SOURCE_W && extent.height == SOURCE_H',rust)
        self.assertIn('CPU asset only; GPU screenshot NOT verified',rust)
        self.assertIn('GPU visual parity NOT certified', (SOURCE.parents[1]/'tools/candidate_gate.py').read_text())
        self.assertIn('(report_original_sheet, gui).chain()',rust)
        self.assertNotIn('sourceExactArtApproved: true',rust)

if __name__=='__main__': unittest.main()
