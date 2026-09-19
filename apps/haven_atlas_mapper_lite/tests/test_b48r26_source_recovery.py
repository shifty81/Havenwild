#!/usr/bin/env python3
"""Run with python -m unittest discover -s apps/haven_atlas_mapper_lite/tests -p 'test_b48r26*.py'."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from PIL import Image

SCRIPT = Path(__file__).resolve().parents[1] / 'tools' / 'recover_eligible_summer_demo.py'
spec = importlib.util.spec_from_file_location('source_recovery', SCRIPT)
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)


def png_bytes(image):
    buf = io.BytesIO()
    image.save(buf, 'PNG')
    return buf.getvalue()


class SourceRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.source_root = self.repo / 'assets/source/licensed/lpc_revised/artist'
        self.source = self.source_root / 'Terrain/Grass (Summer).png'
        self.source.parent.mkdir(parents=True)
        image = Image.new('RGBA', (64, 32), (11, 22, 33, 255))
        image.paste((44, 55, 66, 255), (32, 0, 64, 32))
        self.original = png_bytes(image)
        self.source.write_bytes(self.original)
        self.pack = self.repo / 'original.zip'
        self.demo = self.repo / 'demo.zip'
        with zipfile.ZipFile(self.pack, 'w') as archive:
            archive.writestr('Terrain/Grass (Summer).png', self.original)
        with zipfile.ZipFile(self.demo, 'w') as archive:
            archive.writestr('_ Test Scenes/DemoGame - 2 - Summer.png', png_bytes(image))
        self.output = self.repo / 'artifacts/asset-intake/atlas-mapper/projects/candidate.mapper.json'

    def test_unique_original_tiles_create_editable_unapproved_project(self):
        evidence = recovery.recover(self.repo, self.source_root, self.pack, self.demo, self.output)
        project = json.loads(self.output.read_text())
        self.assertEqual(evidence['counts']['unique_match_candidate'], 2)
        self.assertEqual(len(project['pieces']), 2)
        self.assertEqual(project['schema'], 'havenwild.atlas_mapper_project.v0_7')
        self.assertEqual(project['heightmap'], [])
        self.assertTrue(all(p['semantic_role'] == 'reference_pixel_match_unreviewed' for p in project['pieces']))
        self.assertTrue(project['source_assets'][0]['source_sha256'])
        with self.assertRaises(FileExistsError):
            recovery.recover(self.repo, self.source_root, self.pack, self.demo, self.output)

    def test_modified_source_is_never_accepted(self):
        self.source.write_bytes(self.original + b'\x00')
        with self.assertRaises(ValueError):
            recovery.recover(self.repo, self.source_root, self.pack, self.demo, self.output)
        self.assertFalse(self.output.exists())

    def test_duplicate_appearance_remains_unresolved(self):
        image = Image.new('RGBA', (64, 32), (11, 22, 33, 255))
        self.original = png_bytes(image)
        self.source.write_bytes(self.original)
        with zipfile.ZipFile(self.pack, 'w') as archive:
            archive.writestr('Terrain/Grass (Summer).png', self.original)
        with zipfile.ZipFile(self.demo, 'w') as archive:
            archive.writestr('_ Test Scenes/DemoGame - 2 - Summer.png', self.original)
        with self.assertRaises(ValueError):
            recovery.recover(self.repo, self.source_root, self.pack, self.demo, self.output)
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
