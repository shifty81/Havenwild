#!/usr/bin/env python3
"""Behavioral regression tests for the offline A01 source reconciler."""
from __future__ import annotations
import importlib.util
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[3] / "assets/Audit-LpcOgaSourceCoverageA01.py"
spec = importlib.util.spec_from_file_location("havenwild_source_coverage_a01", TOOL)
a01 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = a01
spec.loader.exec_module(a01)


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        self.root.mkdir()
        self.out = Path(self.temp.name) / "results"
        self.put(a01.DISCOVERY, {"packs": [
            {"id": "match", "title": "Match", "url": "https://opengameart.org/content/match", "selectedLicense": "CC0-1.0"},
            {"id": "unrouted", "title": "Unrouted", "url": "https://opengameart.org/content/unrouted"},
        ]})
        self.put(a01.OGA, {"sources": [
            {"id": "oga.lpc.match", "title": "Match", "sourcePage": "https://www.opengameart.org/content/match/", "selectedLicense": "CC0-1.0", "fileName": "match.png", "directUrl": "https://opengameart.org/files/match.png"},
            {"id": "elizawy.main", "title": "Pinned", "sourcePage": "https://opengameart.org/content/other", "acquisition": "existing_pinned_elizawy_repository", "localSourceRoot": "assets/source/licensed/lpc_revised", "selectedLicense": "OGA-BY-3.0"},
        ]})
        self.put(a01.QUEUE, {"queue": [{"id": "oga.lpc.match", "state": "APPROVED_ACQUIRE_REVIEW"}]})
        self.put(a01.BROWSER, {"entryCount": 2, "entries": [
            {"stableId": "a", "displayName": "A", "category": "nature", "sourcePath": "assets/source/licensed/lpc_revised/Objects/A.png", "imageSize": [64, 32], "sliceSize": [32, 32], "productionState": "needs_binding"},
            {"stableId": "b", "displayName": "B", "category": "nature", "sourcePath": "assets/source/licensed/lpc_revised/Objects/B.png", "imageSize": [32, 32], "sliceSize": [32, 32], "productionState": "reference_only"},
        ]})

    def put(self, path, data):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps(data), encoding="utf-8")

    def test_lean_checkout_is_not_misclassified_as_developer_machine(self):
        summary = a01.audit(self.root, self.out)
        self.assertEqual(summary["counts"]["discoveryExactPageMatches"], 1)
        self.assertEqual(summary["counts"]["discoveryWithoutExactRoute"], 1)
        self.assertEqual(summary["ogaMountStates"]["archive_absent_in_this_checkout"], 1)
        self.assertEqual(summary["lpcMountStates"]["source_absent_in_this_checkout"], 2)
        self.assertFalse(summary["lpcMountRootPresent"])
        self.assertTrue((self.out / "REPORT.md").is_file())
        self.assertFalse((self.root / "artifacts").exists(), "report must honor --output")

    def test_local_files_report_actual_dimensions_and_archive_hash(self):
        image = self.root / "assets/source/licensed/lpc_revised/Objects/A.png"
        image.parent.mkdir(parents=True, exist_ok=True)
        image.write_bytes(b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 128, 32))
        image_b = self.root / "assets/source/licensed/lpc_revised/Objects/B.png"
        image_b.write_bytes(b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 32, 32))
        archive = self.root / "assets/source/licensed/oga_lpc_prototypes/oga_lpc_match/source/match.png"
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_bytes(b"fake image source")
        extraction = archive.parent.parent / "extracted"
        extraction.mkdir()
        (extraction / "match.png").write_bytes(b"fake image source")
        summary = a01.audit(self.root, self.out, hash_sources=True)
        self.assertEqual(summary["lpcMountStates"]["image_dimensions_mismatch"], 1)
        self.assertEqual(summary["ogaMountStates"]["archive_and_extraction_present"], 1)
        self.assertIn("source_present", summary["lpcMountStates"])
        with (self.out / "oga_source_mounts.csv").open(encoding="utf-8") as handle:
            row = next(__import__("csv").DictReader(handle))
        self.assertEqual(len(row["sha256"]), 64)

    def test_unsafe_source_path_fails_closed(self):
        with self.assertRaises(ValueError):
            a01.safe_path(self.root, "../../outside.png")
        with self.assertRaises(ValueError):
            a01.safe_path(self.root, "C:/absolute/windows.png")

    def link_directory(self, target: Path, link: Path) -> None:
        link.parent.mkdir(parents=True, exist_ok=True)
        try:
            link.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError):
            if os.name != "nt":
                self.skipTest("directory symlinks unavailable")
            # Junction creation normally requires no developer-mode privilege.
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(target)],
                capture_output=True, text=True, check=False,
            )
            if result.returncode:
                self.skipTest("directory junctions unavailable: " + result.stderr)

    def test_external_declared_lpc_mount_works_in_normal_and_hash_modes(self):
        external = Path(self.temp.name) / "lpc-source-library"
        objects = external / "Objects"
        objects.mkdir(parents=True)
        png = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR"
        (objects / "A.png").write_bytes(png + struct.pack(">II", 64, 32))
        (objects / "B.png").write_bytes(png + struct.pack(">II", 32, 32))
        self.link_directory(external, self.root / "assets/source/licensed/lpc_revised")

        normal = a01.audit(self.root, self.out / "normal")
        hashed = a01.audit(self.root, self.out / "hashed", hash_sources=True)
        self.assertEqual(normal["lpcMountStates"], {"source_present": 2})
        self.assertEqual(hashed["lpcMountStates"], normal["lpcMountStates"])
        self.assertEqual(hashed["ogaMountStates"]["mounted_provider"], 1)
        with (self.out / "hashed/lpc_browser_sheet_mounts.csv").open(encoding="utf-8") as handle:
            rows = list(__import__("csv").DictReader(handle))
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(len(row["sha256"]) == 64 and not row["error"] for row in rows))

    def test_links_escaping_declared_mount_are_rejected(self):
        external = Path(self.temp.name) / "licensed-provider"
        external.mkdir()
        outside = Path(self.temp.name) / "unrelated-outside"
        outside.mkdir()
        (outside / "secret.png").write_bytes(b"private")
        self.link_directory(external, self.root / "assets/source/licensed/lpc_revised")
        self.link_directory(outside, external / "Objects")
        with self.assertRaisesRegex(ValueError, "escapes repository or authorized LPC mount"):
            a01.safe_path(self.root, "assets/source/licensed/lpc_revised/Objects/secret.png")

        self.link_directory(outside, self.root / "not_the_licensed_mount")
        with self.assertRaisesRegex(ValueError, "escapes repository or authorized LPC mount"):
            a01.safe_path(self.root, "not_the_licensed_mount/secret.png")


if __name__ == "__main__":
    unittest.main(verbosity=2)
