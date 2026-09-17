#!/usr/bin/env python3
"""Hermetic, network-free A02 source-intake regression suite."""
import importlib.util
import io
import json
import stat
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[3] / 'assets' / 'Intake-OgaLpcSourceA02.py'
spec = importlib.util.spec_from_file_location('haven_a02', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        registry = self.root / module.REGISTRY
        registry.parent.mkdir(parents=True)
        self.source = {'id': 'oga.lpc.test', 'title': 'Fixture Asset',
                       'sourcePage': 'https://opengameart.org/content/fixture',
                       'directUrl': 'https://opengameart.org/sites/default/files/fixture.zip',
                       'fileName': 'fixture.zip', 'selectedLicense': 'CC0-1.0',
                       'authors': ['Fixture Author'], 'roles': ['terrain.fixture']}
        registry.write_text(json.dumps({'sources': [self.source], 'revision': 'fixture'}))
        queue = self.root / module.QUEUE
        queue.parent.mkdir(parents=True, exist_ok=True)
        queue.write_text(json.dumps({'queue': [{'id': self.source['id'],
                          'state': 'APPROVED_ACQUIRE_REVIEW', 'license': 'CC0-1.0'}]}))
        self.archive = self.root / 'fixture.zip'
        self.zip_with({'art/tile.png': b'png data', 'credits.txt': b'Fixture Author CC0'})

    def tearDown(self):
        self.folder.cleanup()

    def zip_with(self, members):
        with zipfile.ZipFile(self.archive, 'w') as out:
            for key, value in members.items():
                out.writestr(key, value)

    def review(self):
        return {'reviewed_page': self.source['sourcePage'], 'reviewed_license': 'CC0-1.0'}

    def test_default_is_dry_run_and_unchanged(self):
        result = module.intake(self.root, 'oga.lpc.test', self.archive)
        self.assertEqual(result['status'], 'dry_run')
        self.assertFalse((self.root / module.MOUNT).exists())
        self.assertTrue(self.archive.is_file())

    def test_commit_requires_explicit_provenance_review(self):
        with self.assertRaisesRegex(ValueError, 'reviewed-source-page'):
            module.intake(self.root, 'oga.lpc.test', self.archive, commit=True)
        self.assertFalse((self.root / module.MOUNT).exists())

    def test_commit_is_immutable_and_does_not_publish(self):
        result = module.intake(self.root, 'oga.lpc.test', self.archive, commit=True, **self.review())
        self.assertEqual(result['status'], 'intaken_unpublished')
        target = module.source_mount(self.root, 'oga.lpc.test')
        record = json.loads((target / 'source_record.json').read_text())
        self.assertEqual(record['queueStateAtIntake'], 'APPROVED_ACQUIRE_REVIEW')
        self.assertFalse(record['runtimePromoted'])
        self.assertEqual(len(json.loads((target / 'extracted_files.json').read_text())), 2)
        self.assertEqual(module.digest_file(target / 'source' / 'fixture.zip'), record['sha256'])
        self.assertEqual(module.intake(self.root, 'oga.lpc.test', self.archive)['status'], 'already_intaken')
        self.zip_with({'different.png': b'other bytes'})
        with self.assertRaisesRegex(ValueError, 'refusing overwrite'):
            module.intake(self.root, 'oga.lpc.test', self.archive, commit=True, **self.review())

    def test_unqueued_or_license_mismatch_blocked(self):
        path = self.root / module.QUEUE
        path.write_text(json.dumps({'queue': []}))
        with self.assertRaisesRegex(ValueError, 'not approved'):
            module.intake(self.root, 'oga.lpc.test', self.archive)
        path.write_text(json.dumps({'queue': [{'id': 'oga.lpc.test',
                         'state': 'APPROVED_ACQUIRE_REVIEW', 'license': 'CC-BY-4.0'}]}))
        with self.assertRaisesRegex(ValueError, 'disagree on license'):
            module.intake(self.root, 'oga.lpc.test', self.archive)

    def test_path_traversal_and_symlink_rejected_without_mount(self):
        self.zip_with({'../escaped.png': b'unsafe'})
        with self.assertRaisesRegex(ValueError, 'unsafe archive member'):
            module.intake(self.root, 'oga.lpc.test', self.archive, commit=True, **self.review())
        self.assertFalse(module.source_mount(self.root, 'oga.lpc.test').exists())
        info = zipfile.ZipInfo('external_link')
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(self.archive, 'w') as out:
            out.writestr(info, 'out-of-tree')
        with self.assertRaisesRegex(ValueError, 'non-regular'):
            module.intake(self.root, 'oga.lpc.test', self.archive, commit=True, **self.review())
        self.assertFalse(module.source_mount(self.root, 'oga.lpc.test').exists())

    def test_tar_links_and_casefold_collisions_rejected(self):
        self.source['fileName'] = 'fixture.tar'
        (self.root / module.REGISTRY).write_text(json.dumps({'sources': [self.source]}))
        tar_path = self.root / 'fixture.tar'
        with tarfile.open(tar_path, 'w') as out:
            item = tarfile.TarInfo('shortcut')
            item.type = tarfile.SYMTYPE
            item.linkname = '../../escape'
            out.addfile(item)
        with self.assertRaisesRegex(ValueError, 'link/device'):
            module.intake(self.root, 'oga.lpc.test', tar_path, commit=True, **self.review())
        self.source['fileName'] = 'fixture.zip'
        (self.root / module.REGISTRY).write_text(json.dumps({'sources': [self.source]}))
        self.zip_with({'Art/P.png': b'a', 'art/p.png': b'b'})
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            module.intake(self.root, 'oga.lpc.test', self.archive, commit=True, **self.review())

    def test_list_preserves_unqueued_status(self):
        rows = module.list_sources(self.root)
        self.assertEqual(rows[0]['status'], 'ready_for_reviewed_download')
        (self.root / module.QUEUE).write_text(json.dumps({'queue': []}))
        self.assertEqual(module.list_sources(self.root)[0]['status'], 'needs_approval')


if __name__ == '__main__':
    unittest.main(verbosity=2)
