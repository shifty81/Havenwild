#!/usr/bin/env python3
"""Regression fixtures for Havenwild project-local physical LPC source mode."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[3] / "dependencies/Ensure-LpcDependency.py"
spec = importlib.util.spec_from_file_location("havenwild_self_contained_lpc", SCRIPT)
assert spec is not None and spec.loader is not None
lpc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lpc)


def png(width: int = 32, height: int = 32) -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\x0dIHDR" + struct.pack(">II", width, height)


class SelfContainedTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="havenwild-a01r2-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "Havenwild"
        self.root.mkdir()
        self.mount_rel = "assets/source/licensed/lpc_revised"
        self.mount = self.root / self.mount_rel
        self.checkout = self.root / ".local/dependencies/lpc/fakecommit"
        self.checkout.mkdir(parents=True)
        self.write_source(self.checkout)
        self.lock = {
            "repository": "https://example.invalid/lpc.git",
            "commit": "fakecommit",
            "fullSourceProjectPath": self.mount_rel,
            "requiredTopLevelPaths": ["FX", "Terrain"],
            "requiredRootFiles": ["Credits.txt"],
            "requiredTerrainFiles": ["Terrain/terrain_summer.png"],
            "lockedFiles": [{
                "repositoryPath": "Terrain/terrain_summer.png",
                "projectPath": self.mount_rel + "/Terrain/terrain_summer.png",
                "width": 32, "height": 32,
                "sha256": hashlib.sha256(png()).hexdigest(),
            }],
        }
        self.catalog = self.root / "content/editor/assets/lpc_world_source_browser_v1.json"
        self.catalog.parent.mkdir(parents=True)
        self.catalog.write_text(json.dumps({
            "sourceCommit": "fakecommit", "entryCount": 2,
            "entries": [
                {"sourcePath": self.mount_rel + "/Terrain/terrain_summer.png", "imageSize": [32, 32]},
                {"sourcePath": self.mount_rel + "/FX/Splash.png", "imageSize": [32, 32]},
            ],
        }), encoding="utf-8")
        self.orig_root = lpc.ROOT
        self.orig_lock = lpc.LOCK_PATH
        self.orig_provenance = lpc.SOURCE_MOUNT_PROVENANCE
        lpc.ROOT = self.root
        lpc.LOCK_PATH = self.root / "content/assets/intake/lpc_source_lock_v0_1.json"
        lpc.LOCK_PATH.parent.mkdir(parents=True)
        lpc.LOCK_PATH.write_text(json.dumps(self.lock), encoding="utf-8")
        lpc.SOURCE_MOUNT_PROVENANCE = self.root / "WORKSPACE/generated/lpc/source.json"
        self.addCleanup(self.restore)

    def restore(self) -> None:
        lpc.ROOT = self.orig_root
        lpc.LOCK_PATH = self.orig_lock
        lpc.SOURCE_MOUNT_PROVENANCE = self.orig_provenance

    def link_directory(self, link: Path, target: Path) -> None:
        # On Windows a real junction works without developer-mode symlink rights
        # and reproduces the reported cached-checkout topology.
        if os.name == "nt":
            args = ["mklink", "/J", str(link), str(target)]
            subprocess.run(
                ["cmd.exe", "/d", "/s", "/c", subprocess.list2cmdline(args)],
                check=True, capture_output=True, text=True,
            )
        else:
            link.symlink_to(target, target_is_directory=True)

    def write_source(self, path: Path) -> None:
        (path / "FX").mkdir(parents=True, exist_ok=True)
        (path / "Terrain").mkdir(parents=True, exist_ok=True)
        (path / "Credits.txt").write_text("test-only credits\n", encoding="utf-8")
        (path / "FX/Splash.png").write_bytes(png())
        (path / "Terrain/terrain_summer.png").write_bytes(png())

    @unittest.skipUnless(shutil.which("git"), "Git required for parent-repository regression")
    def test_parent_havenwild_commit_is_not_mistaken_for_export_commit(self) -> None:
        """Full Gate regression: Git discovers Havenwild HEAD from an LPC export."""
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(self.root), "-c", "user.name=Fixture",
             "-c", "user.email=fixture@example.invalid", "commit", "-q",
             "--allow-empty", "-m", "Havenwild fixture commit"],
            check=True, capture_output=True,
        )
        project_head = subprocess.run(
            ["git", "-C", str(self.root), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        self.assertNotEqual(project_head, self.lock["commit"])
        self.write_source(self.mount)
        self.assertIsNone(lpc.checkout_head(self.mount))
        with mock.patch.dict(os.environ, {"HAVENWILD_LPC_SOURCE_MODE": "copy"}):
            # Fully populated export must take the no-copy path, then write
            # provenance without substituting the enclosing project HEAD.
            with mock.patch.object(lpc, "ensure_checkout") as acquisition:
                self.assertEqual(lpc.main(), 0)
                acquisition.assert_not_called()
        record = json.loads(lpc.SOURCE_MOUNT_PROVENANCE.read_text(encoding="utf-8"))
        self.assertEqual(record["expectedCommit"], self.lock["commit"])
        self.assertIsNone(record["observedCommit"])
        self.assertEqual(record["verificationMode"], "locked_export_structure_and_sha256")
        self.assertEqual(record["mountMode"], "copy_or_export")
        self.assertTrue((self.mount / "FX/Splash.png").is_file())

    @unittest.skipUnless(shutil.which("git"), "Git required for copy-and-provenance regression")
    def test_parent_havenwild_git_does_not_break_full_junction_repair(self) -> None:
        """Reproduce the user log all the way through physical copy + provenance."""
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(self.root), "-c", "user.name=Fixture",
             "-c", "user.email=fixture@example.invalid", "commit", "-q",
             "--allow-empty", "-m", "Havenwild fixture commit"],
            check=True, capture_output=True,
        )
        self.mount.parent.mkdir(parents=True)
        self.link_directory(self.mount, self.checkout)
        with mock.patch.dict(os.environ, {"HAVENWILD_LPC_SOURCE_MODE": "copy"}):
            with mock.patch.object(lpc, "ensure_checkout", return_value=self.checkout):
                self.assertEqual(lpc.main(), 0)
        self.assertFalse(lpc.is_directory_link(self.mount))
        self.assertTrue((self.mount / "FX/Splash.png").is_file())
        record = json.loads(lpc.SOURCE_MOUNT_PROVENANCE.read_text(encoding="utf-8"))
        self.assertIsNone(record["observedCommit"])
        self.assertEqual(record["verificationMode"], "locked_export_structure_and_sha256")
        self.assertTrue((self.checkout / "FX/Splash.png").is_file())

    def test_export_with_invalid_browser_file_cannot_claim_provenance(self) -> None:
        self.write_source(self.mount)
        (self.mount / "FX/Splash.png").unlink()
        with self.assertRaisesRegex(RuntimeError, "incomplete source"):
            lpc.write_source_mount_provenance(self.lock, self.mount, "copy")
        self.assertFalse(lpc.SOURCE_MOUNT_PROVENANCE.exists())

    @unittest.skipUnless(shutil.which("git"), "Git required for source-repo pin regression")
    def test_real_source_git_commit_must_still_match_lock(self) -> None:
        self.write_source(self.mount)
        subprocess.run(["git", "init", "-q", str(self.mount)], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(self.mount), "-c", "user.name=Fixture",
             "-c", "user.email=fixture@example.invalid", "commit", "-q",
             "--allow-empty", "-m", "Wrong LPC revision"],
            check=True, capture_output=True,
        )
        self.assertIsNotNone(lpc.checkout_head(self.mount))
        with self.assertRaisesRegex(RuntimeError, "LPC source commit mismatch"):
            lpc.write_source_mount_provenance(self.lock, self.mount, "link")
        self.assertFalse(lpc.SOURCE_MOUNT_PROVENANCE.exists())

    def test_complete_checkout_preflight(self) -> None:
        good, detail = lpc.validate_complete_source_tree(self.checkout, self.lock)
        self.assertTrue(good, detail)

    def test_missing_browser_sheet_is_hard_failure(self) -> None:
        (self.checkout / "FX/Splash.png").unlink()
        good, detail = lpc.validate_complete_source_tree(self.checkout, self.lock)
        self.assertFalse(good)
        self.assertIn("missing browser sheet", detail)

    def test_broken_checkout_preserves_existing_junction(self) -> None:
        old = self.root / "old"
        self.write_source(old)
        self.mount.parent.mkdir(parents=True)
        self.link_directory(self.mount, old)
        (self.checkout / "FX/Splash.png").unlink()
        with mock.patch.dict(os.environ, {"HAVENWILD_LPC_SOURCE_MODE": "copy"}):
            with self.assertRaisesRegex(RuntimeError, "old mount preserved"):
                lpc.mount_full_source_tree(self.checkout, self.lock)
        self.assertTrue(lpc.is_directory_link(self.mount))
        self.assertTrue((old / "FX/Splash.png").is_file())

    def test_copy_replaces_only_junction_and_is_physical(self) -> None:
        old = self.root / "old"
        self.write_source(old)
        self.mount.parent.mkdir(parents=True)
        self.link_directory(self.mount, old)
        with mock.patch.dict(os.environ, {"HAVENWILD_LPC_SOURCE_MODE": "copy"}):
            mode = lpc.mount_full_source_tree(self.checkout, self.lock)
        self.assertEqual(mode, "copy")
        self.assertFalse(lpc.is_directory_link(self.mount))
        self.assertTrue((self.mount / "FX/Splash.png").is_file())
        self.assertTrue((old / "FX/Splash.png").is_file())

    def test_existing_junction_to_cached_checkout_is_safe_to_convert(self) -> None:
        # Exact Windows incident: the existing LPC junction resolves to the
        # same pinned cache selected for the physical copy.
        self.mount.parent.mkdir(parents=True)
        self.link_directory(self.mount, self.checkout)
        lpc.validate_checkout_location(self.checkout, self.mount)
        with mock.patch.dict(os.environ, {"HAVENWILD_LPC_SOURCE_MODE": "copy"}):
            self.assertEqual(lpc.mount_full_source_tree(self.checkout, self.lock), "copy")
        self.assertFalse(lpc.is_directory_link(self.mount))
        self.assertTrue((self.mount / "FX/Splash.png").is_file())
        self.assertTrue((self.checkout / "FX/Splash.png").is_file())

    def test_main_with_live_cached_checkout_junction(self) -> None:
        # The user's real scenario must be covered through main(), not just
        # through the mount helper's location validation.
        self.mount.parent.mkdir(parents=True)
        self.link_directory(self.mount, self.checkout)
        with mock.patch.dict(os.environ, {"HAVENWILD_LPC_SOURCE_MODE": "copy"}):
            with mock.patch.object(lpc, "ensure_checkout", return_value=self.checkout):
                self.assertEqual(lpc.main(), 0)
        self.assertFalse(lpc.is_directory_link(self.mount))
        self.assertTrue((self.checkout / "FX/Splash.png").is_file())
        self.assertTrue((self.mount / "FX/Splash.png").is_file())

    def test_default_mode_is_a_physical_copy(self) -> None:
        self.mount.parent.mkdir(parents=True)
        self.link_directory(self.mount, self.checkout)
        with mock.patch.dict(os.environ, {"HAVENWILD_LPC_SOURCE_MODE": ""}):
            # Empty mode is invalid by design; test an absent key instead.
            os.environ.pop("HAVENWILD_LPC_SOURCE_MODE", None)
            self.assertEqual(lpc.mount_full_source_tree(self.checkout, self.lock), "copy")
        self.assertFalse(lpc.is_directory_link(self.mount))

    def test_genuinely_nested_copy_target_is_rejected(self) -> None:
        unsafe_target = self.checkout / "nested_destination"
        with self.assertRaisesRegex(RuntimeError, "recursively copy"):
            lpc.validate_checkout_location(self.checkout, unsafe_target)

    def test_source_checkout_containing_havenwild_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "parent directories"):
            lpc.validate_checkout_location(self.root.parent, self.mount)

    def test_redirected_destination_parent_is_rejected(self) -> None:
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        self.link_directory(self.root / "assets", outside)
        with self.assertRaisesRegex(RuntimeError, "destination parent outside"):
            lpc.validate_checkout_location(self.checkout, self.mount)

    def test_existing_physical_source_is_never_deleted(self) -> None:
        self.write_source(self.mount)
        (self.mount / "personal_note.txt").write_text("preserve user files\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "refusing to overwrite an existing physical"):
            lpc.replace_directory_entry(self.checkout, self.mount)
        self.assertTrue((self.mount / "personal_note.txt").is_file())
        self.assertTrue((self.checkout / "FX/Splash.png").is_file())

    def test_explicit_copy_mode_converts_even_valid_junction(self) -> None:
        old = self.root / "old"
        self.write_source(old)
        self.mount.parent.mkdir(parents=True)
        self.link_directory(self.mount, old)
        with mock.patch.dict(os.environ, {"HAVENWILD_LPC_SOURCE_MODE": "copy"}):
            with mock.patch.object(lpc, "ensure_checkout", return_value=self.checkout) as acquisition:
                self.assertEqual(lpc.main(), 0)
                acquisition.assert_called_once()
        self.assertFalse(lpc.is_directory_link(self.mount))
        self.assertTrue((self.mount / "FX/Splash.png").is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
