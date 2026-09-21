"""R10 isolated git-index and native PCC publication regression tests.

Does not invoke Havenwild's real Git checkout or a remote. Requires Git and Python.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


authority = load("havenwild_r10_authority_test", "tools/control/HavenwildGateAuthority.py")
quick = load("havenwild_r10_quick_test", "tools/control/PccQuickState.py")
gui = load("havenwild_r10_gui_test", ".forgepy/gui/pcc_gui.py")
forge = load("havenwild_r10_forge_test", ".forgepy/runtime/forgepy.py")


@unittest.skipUnless(shutil.which("git"), "isolated Git executable required")
class CertifiedIndexTests(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.root = Path(td.name)
        self.git("init", "-q")
        self.git("config", "user.name", "R10 isolated test")
        self.git("config", "user.email", "r10@example.invalid")
        self.write("source.txt", "before")
        self.write(".forgepy/state/last-green.json", '{"result":"old"}')
        self.write(".forgepy/cache/repository.scan.v1.json", "cache")
        self.write("experiments/haven_bevy_candidate/evidence/semantic_scene_plan.json", "candidate")
        self.write("experiments/haven_bevy_candidate/target/debug/deps/generated.o", "object")
        self.git("add", "-A")
        self.git("commit", "-qm", "baseline")
        self.write("source.txt", "after")
        self.write(".forgepy/state/last-green.json", '{"result":"stale"}')
        self.write("experiments/haven_bevy_candidate/target/debug/deps/new.o", "object2")
        self.git("add", "-f", "-A")  # simulate original dangerous staging
        self.snap = {"paths": ["source.txt"], "requiredRuntimeMediaPaths": [], "pathCount": 1}
        self.marker = {"governedPaths": ["source.txt"]}

    def write(self, rel: str, value: str) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    def git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", "-C", str(self.root), *args], check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def test_nested_outputs_and_volatiles_are_excluded(self):
        for rel in ("experiments/haven_bevy_candidate/target/debug/a.o",
                    "tools/build/target/debug/output", ".forgepy/state/last-green.json",
                    ".forgepy/cache/repository.scan.v1.json",
                    "experiments/haven_bevy_candidate/evidence/semantic_scene_plan.json",
                    ".pytest_cache/cache", "crates/x/__pycache__/x.pyc"):
            with self.subTest(rel=rel):
                self.assertTrue(authority.ignored(rel), rel)
                self.assertTrue(quick.generated_path(rel), rel)
        for rel in ("experiments/haven_bevy_candidate/Cargo.lock",
                    ".forgepy/gui/pcc_gui.py", ".forgepy/runtime/forgepy.py",
                    "tools/build/Build.sh", "docs/audits/R2_FULL_SOURCE_FILE_MANIFEST.json"):
            self.assertFalse(authority.ignored(rel), rel)

    def test_governed_tree_walk_excludes_nested_target_and_volatile_receipts(self):
        import hashlib
        manifest = self.root / "content/runtime_media_manifest_v1.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        media = self.root / "content/ui/required.png"
        media.parent.mkdir(parents=True, exist_ok=True)
        media.write_bytes(b"test-only-media")
        manifest.write_text(json.dumps({
            "schema": "havenwild.runtime_media_manifest.v1",
            "assets": [{"id": "unit-test", "path": "content/ui/required.png",
                        "requiredForCleanCheckout": True,
                        "sha256": hashlib.sha256(media.read_bytes()).hexdigest()}],
        }), encoding="utf-8")
        paths, _ = authority.governed_paths(self.root)
        self.assertIn("source.txt", paths)
        self.assertIn("content/ui/required.png", paths)
        self.assertFalse(any(authority.retired_generated(rel) for rel in paths))

    def test_stage_retires_only_generated_index_and_preserves_worktree(self):
        with patch.object(authority, "certify_matches", return_value=(True, self.snap, "")), \
             patch.object(authority, "REQUIRED_BOOTSTRAP_PATHS", ()):
            got = authority.stage_certified(self.root, self.marker)
        self.assertEqual(got, self.snap)
        changed = self.git("diff", "--cached", "--name-status").stdout.splitlines()
        self.assertIn("M\tsource.txt", changed)
        self.assertIn("D\t.forgepy/state/last-green.json", changed)
        self.assertIn("D\texperiments/haven_bevy_candidate/target/debug/deps/generated.o", changed)
        self.assertFalse(any(line.startswith("A\t") and ("/target/" in line or "/evidence/" in line) for line in changed))
        self.assertEqual(self.git("ls-files", "--", "experiments/haven_bevy_candidate/target").stdout, "")
        self.assertTrue((self.root / "experiments/haven_bevy_candidate/target/debug/deps/generated.o").is_file())
        self.assertTrue((self.root / ".forgepy/state/last-green.json").is_file())

    def test_unrelated_staged_changes_block_before_mutating_index(self):
        self.write("surprise.txt", "unapproved")
        self.git("add", "surprise.txt")
        before = self.git("diff", "--cached", "--name-status").stdout
        with patch.object(authority, "certify_matches", return_value=(True, self.snap, "")):
            with self.assertRaisesRegex(authority.AuthorityError, "unrelated staged"):
                authority.stage_certified(self.root, self.marker)
        self.assertEqual(before, self.git("diff", "--cached", "--name-status").stdout)

    def test_quick_fingerprint_ignores_staging_churn_but_detects_source_edits(self):
        receipt1, paths1, _ = quick.worktree_fingerprint(self.root)
        self.git("restore", "--staged", "--", "experiments/haven_bevy_candidate/target")
        receipt2, paths2, _ = quick.worktree_fingerprint(self.root)
        self.assertEqual(paths1, paths2)
        self.assertEqual(receipt1, receipt2)
        self.write("source.txt", "another source edit")
        receipt3, _, _ = quick.worktree_fingerprint(self.root)
        self.assertNotEqual(receipt2, receipt3)


class PccDelegationTests(unittest.TestCase):
    def test_experimental_push_has_pre_transfer_source_and_head_guards(self):
        bridge = (ROOT / "tools/control/GitSourceControl.ps1").read_text(encoding="utf-8")
        push = bridge.split("function Push-ExperimentalGreen {", 1)[1].split("# CC8E16:", 1)[0]
        for proof in ("$marker.committedCommit -ne $head", "'--action' 'Status'",
                      "[string]$sourceStatus.gateState -ne 'GREEN'",
                      "$sourceStatus.publicationEligible -ne $true",
                      "diff --cached --quiet"):
            self.assertIn(proof, push)
        self.assertLess(push.index("diff --cached --quiet"), push.index("push -u origin experimental"))

    def test_gui_git_button_invokes_authoritative_publisher(self):
        app = gui.PCCApp.__new__(gui.PCCApp)
        app.publish_green = unittest.mock.Mock()
        app.commit_green()
        app.publish_green.assert_called_once_with()
        self.assertEqual(gui.PCC_GUI_COMMANDS["pcc-publish"], "source-control.commit-push-green")

    def test_generic_cli_never_stages_or_pushes_havenwild(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for rel in ("tools/control/HavenwildPccHost.ps1", "tools/control/HavenwildGateAuthority.py"):
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("placeholder", encoding="utf-8")
            with patch.object(forge, "git", side_effect=AssertionError("generic Git must not run")):
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(forge.commit_green(root), 2)
                    self.assertEqual(forge.git_push_safe(root), 2)
                self.assertIn("Havenwild PCC", output.getvalue())


if __name__ == "__main__":
    unittest.main()
