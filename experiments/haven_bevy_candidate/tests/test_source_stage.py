"""Source staging and fail-closed checks; independent of Windows Rust build."""
import importlib.util
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / 'tools/prepare_source.py'
spec = importlib.util.spec_from_file_location('source_stage_r28b', PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class OriginalInputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.zip_path = self.base / 'Terrain.zip'

    def create_archive(self, image=b'\x89PNG\r\n\x1a\nX', credits=b'credit'):
        with zipfile.ZipFile(self.zip_path, 'w') as z:
            z.writestr(m.SOURCE, image)
            z.writestr(m.CREDITS, credits)

    def test_candidate_is_isolated_and_macroquad_free_by_manifest(self):
        candidate = PATH.parents[1]
        manifest = (candidate / 'Cargo.toml').read_text()
        source = (candidate / 'src/main.rs').read_text()
        self.assertIn('[workspace]', manifest)
        self.assertIn('bevy = "=0.19.0"', manifest)
        self.assertIn('bevy_egui = "=0.42.0"', manifest)
        self.assertIn('forge_gui_shell', manifest)
        self.assertNotIn('macroquad', manifest.lower())
        self.assertIn('RenderTarget::Image', source)
        self.assertIn('show_application_shell(', source)
        self.assertIn('verify_source_and_scene()', source)

    def test_reference_original_hash_is_pinned(self):
        self.assertEqual(m.EXPECTED_SOURCE_SHA, '1251a6ea556330190ccb1e3af166eb69fbec4b7a3f7d51c1f54728abd75bd752')

    def test_fake_original_is_rejected(self):
        self.create_archive()
        with self.assertRaisesRegex(m.SourceError, 'differs'):
            m.original_bytes(self.zip_path)

    def test_missing_credits_fail_closed(self):
        with zipfile.ZipFile(self.zip_path, 'w') as z:
            z.writestr(m.SOURCE, b'PNG')
        with self.assertRaisesRegex(m.SourceError, 'Credits'):
            m.original_bytes(self.zip_path)

    def test_large_archive_rejected(self):
        self.zip_path.write_bytes(b'X' * 50_000_001)
        with self.assertRaisesRegex(m.SourceError, 'large archive'):
            m.original_bytes(self.zip_path)

    def test_atomic_write_preserves_existing_original(self):
        dst = self.base / 'source.png'
        m.atomic_write(dst, b'original')
        m.atomic_write(dst, b'original')
        self.assertEqual(dst.read_bytes(), b'original')
        with self.assertRaisesRegex(m.SourceError, 'different bytes'):
            m.atomic_write(dst, b'mutated')
        self.assertEqual(dst.read_bytes(), b'original')

    def test_symlink_does_not_escape_candidate(self):
        destination = self.base / 'outside'
        destination.write_bytes(b'protected')
        alias = self.base / 'alias'
        try:
            alias.symlink_to(destination)
        except (OSError, NotImplementedError):
            self.skipTest('Host has no symlink privilege')
        with self.assertRaisesRegex(m.SourceError, 'symlink'):
            m.atomic_write(alias, b'attack')
        self.assertEqual(destination.read_bytes(), b'protected')

    def test_fixture_dimension_mismatch_blocked(self):
        root = self.base / 'repo'
        p = root / m.SCENE
        p.parent.mkdir(parents=True)
        p.write_text(json.dumps({'kind':'worldgen_scene','sceneId':'x','sceneSize':[2,2],
                                 'tileSize':[32,32],'layers':{'terrain':[['Grass']]}}))
        with self.assertRaisesRegex(m.SourceError, 'incomplete'):
            m.fixture_details(root)

    def test_fixture_valid_data(self):
        root = self.base / 'repo'
        p = root / m.SCENE
        p.parent.mkdir(parents=True)
        p.write_text(json.dumps({'kind':'worldgen_scene','sceneId':'x','sceneSize':[2,1],
                                 'tileSize':[32,32],'layers':{'terrain':[['Grass','Water']]}}))
        data = m.fixture_details(root)
        self.assertEqual(data['semanticCells'], 2)
        self.assertEqual(data['sceneId'], 'x')

    def test_missing_archive_blocked(self):
        with self.assertRaisesRegex(m.SourceError, 'missing'):
            m.original_bytes(self.zip_path)

if __name__ == '__main__':
    unittest.main()
