"""ForgePY Havenwild GUI console regression; stdlib-only and display-free."""
from __future__ import annotations
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]


def module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


gui = module("havenwild_forgepy_gui_test", ROOT / ".forgepy/gui/pcc_gui.py")
runtime = module("havenwild_forgepy_runtime_test", ROOT / ".forgepy/runtime/forgepy.py")


class TestHeadlessConsole(unittest.TestCase):
    def test_piped_backend_uses_unbuffered_python(self):
        argv = gui.backend_argv(ROOT, "status")
        self.assertEqual(argv[1], "-u")
        self.assertEqual(argv[-1], "status")
        self.assertIn("forgepy.py", argv[2])

    def test_havenwild_green_supersedes_stale_generic_forgepy_failure(self):
        generic = {"greenCurrent": False, "lastGate": {"result": "FAIL"}}
        pcc = {"schema": "havenwild.pcc_quick_state.v1", "gateState": "GREEN",
               "publicationEligible": True, "branch": "experimental"}
        label, color, reason = gui.dashboard_certification(generic, pcc)
        self.assertEqual(label, "GREEN")
        self.assertEqual(color, gui.GOOD)
        self.assertIn("Havenwild PCC", reason)
        self.assertTrue(gui.publication_decision({**pcc, "syncState": "LOCAL_AHEAD_GREEN_UNPUBLISHED",
                             "gitState": "Modified (3 path(s))", "quickCertificationReceipt": True})[0])

    def test_havenwild_stale_and_absent_quick_state_never_show_generic_green(self):
        generic = {"greenCurrent": True, "lastGate": {"result": "PASS"}}
        for state, expected in (("STALE", "PCC STALE"), ("OTHER_LANE", "OTHER LANE"),
                                ("NONE", "NOT CERTIFIED")):
            pcc = {"schema": "havenwild.pcc_quick_state.v1", "gateState": state,
                   "publicationEligible": False, "branch": "experimental"}
            label, color, _ = gui.dashboard_certification(generic, pcc)
            self.assertEqual(label, expected)
            self.assertEqual(color, gui.WARN)
            self.assertFalse(gui.publication_decision(pcc)[0])
        self.assertEqual(gui.dashboard_certification(generic, {})[0], "PCC UNAVAILABLE")

    def test_windows_gui_launch_hides_console_and_inherits_pipes(self):
        fake_startup = type("FakeStartupInfo", (), {"dwFlags": 0, "wShowWindow": None})
        with patch.object(gui.subprocess, "STARTUPINFO", fake_startup, create=True), \
             patch.object(gui.subprocess, "CREATE_NO_WINDOW", 0x08000000, create=True), \
             patch.object(gui.subprocess, "CREATE_NEW_PROCESS_GROUP", 0x200, create=True):
            options = gui.gui_process_options(windows=True, group=True)
        self.assertTrue(options["creationflags"] & 0x08000000)
        self.assertTrue(options["creationflags"] & 0x200)
        self.assertEqual(options["startupinfo"].wShowWindow, 0)
        self.assertEqual(options["env"]["PYTHONUNBUFFERED"], "1")
        self.assertEqual(options["env"]["FORGEPY_GUI_HEADLESS"], "1")

    def test_console_navigation_does_not_hide_work_area(self):
        app = gui.PCCApp.__new__(gui.PCCApp)
        app.log_text = Mock()
        app.frames = {"Dashboard": Mock()}
        app.nav_buttons = {"Dashboard": Mock()}
        app.show_page("Logs")
        app.log_text.focus_set.assert_called_once()
        app.frames["Dashboard"].pack_forget.assert_not_called()

    def test_runtime_stream_is_unbuffered_hidden_and_captures_both_streams(self):
        captured = {}

        class FakeStdout(io.BytesIO):
            def fileno(self):
                return 123

        class FakeProcess:
            pid = 9876
            stdout = FakeStdout(b"stdout line\nstderr line\n")

            def poll(self):
                return 0

            def wait(self):
                return 0

        fake_startup = type("FakeStartupInfo", (), {"dwFlags": 0, "wShowWindow": None})

        def fake_spawn(*args, **kwargs):
            captured.update(kwargs)
            return FakeProcess()

        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            log = work / "piped.log"
            with patch.object(runtime.subprocess, "STARTUPINFO", fake_startup, create=True), \
                 patch.object(runtime.subprocess, "CREATE_NO_WINDOW", 0x08000000, create=True), \
                 patch.object(runtime.subprocess, "CREATE_NEW_PROCESS_GROUP", 0x200, create=True), \
                 patch.object(runtime.subprocess, "Popen", fake_spawn), \
                 patch.object(runtime.os, "read", side_effect=[b"stdout line\nstderr line\n", b""]), \
                 patch.dict(runtime.os.environ, {"FORGEPY_GUI_HEADLESS": "1"}), \
                 patch.object(runtime.os, "name", "nt"):
                code = runtime.stream(["fake.exe"], work, log)
            self.assertEqual(code, 0)
            self.assertEqual(captured["creationflags"] & 0x08000000, 0x08000000)
            self.assertEqual(captured["creationflags"] & 0x200, 0x200)
            self.assertEqual(captured["startupinfo"].wShowWindow, 0)
            self.assertEqual(captured["env"]["PYTHONUNBUFFERED"], "1")
            self.assertEqual(captured["stdin"], subprocess.DEVNULL)
            self.assertEqual(log.read_text(encoding="utf-8"), "stdout line\nstderr line\n")

    def test_runtime_stream_real_pipe_and_persistent_log(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "child.log"
            code = runtime.stream(
                [sys.executable, "-c", "import sys; print('STDOUT'); print('STDERR', file=sys.stderr)"],
                Path(td), log,
            )
            self.assertEqual(code, 0)
            self.assertIn("STDOUT", log.read_text(encoding="utf-8"))
            self.assertIn("STDERR", log.read_text(encoding="utf-8"))

    def test_gui_backend_output_is_captured_without_display(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".forgepy/runtime").mkdir(parents=True)
            # Test child args without running an actual project PCC.
            (root / ".forgepy/runtime/forgepy.py").write_text("print('READY')\n", encoding="utf-8")
            cp = gui.run_capture(root, "status")
            self.assertEqual(cp.returncode, 0, cp.stdout)
            self.assertEqual(cp.stdout.strip(), "READY")

    def test_gui_log_directory_rejects_redirect_outside_project(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            config = root / ".forgepy/state/generated.project.control.json"
            config.parent.mkdir(parents=True)
            config.write_text(json.dumps({"stateDirectory": "../../escape/../.."}), encoding="utf-8")
            app = gui.PCCApp.__new__(gui.PCCApp)
            app.root_path = root
            self.assertEqual(app.state_dir(), root / ".forgepy/state")

    def test_gui_operation_transcript_is_persisted_and_streamed(self):
        import queue
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".forgepy/runtime").mkdir(parents=True)
            (root / ".forgepy/runtime/forgepy.py").write_text(
                "import sys; print('FIRST', flush=True); print('SECOND', file=sys.stderr, flush=True)\n",
                encoding="utf-8",
            )
            app = gui.PCCApp.__new__(gui.PCCApp)
            app.root_path = root
            app.busy = False
            app.proc = None
            app._operation_log = None
            app._operation_log_path = None
            app._log_chunks = 0
            app.log_text = Mock()
            app.console_path_label = Mock()
            app.output_queue = queue.Queue()
            app.set_busy = Mock()
            app.state_dir = lambda: root / ".forgepy/state"
            app.run_backend("status")
            chunks = []
            while True:
                kind, value = app.output_queue.get(timeout=8)
                if kind == "log":
                    app.append_log(value)
                    chunks.append(value)
                elif kind == "done":
                    app.append_log(f"[GUI] Exit code: {value[1]}\n")
                    self.assertEqual(value[1], 0)
                    break
                else:
                    self.fail(f"unexpected GUI event {kind}: {value}")
            self.assertTrue(app._operation_log_path.is_file())
            evidence = app._operation_log_path.read_text(encoding="utf-8")
            self.assertIn("FIRST", evidence)
            self.assertIn("SECOND", evidence)
            self.assertIn("[GUI] Exit code: 0", evidence)
            self.assertIn("FIRST", "".join(chunks))
            app._operation_log.close()

    def test_publication_requires_project_pcc_green_and_pending_changes(self):
        valid = {"branch": "experimental", "gateState": "GREEN", "publicationEligible": True,
                 "gitState": "Modified (1 path(s))", "quickCertificationReceipt": True,
                 "syncState": "LOCAL_AHEAD_GREEN_UNPUBLISHED", "localPatch": "B48R28C16R4"}
        self.assertTrue(gui.publication_decision(valid)[0])
        for changes in (
            {"gateState": "STALE"}, {"publicationEligible": False},
            {"quickCertificationReceipt": False}, {"branch": "other"},
            {"syncState": "MATCH"},
        ):
            with self.subTest(changes=changes):
                self.assertFalse(gui.publication_decision({**valid, **changes})[0])
        clean_ahead = {**valid, "gitState": "Clean", "quickCertificationReceipt": False}
        self.assertTrue(gui.publication_decision(clean_ahead)[0])

    def test_pcc_commands_are_exact_and_never_use_raw_git_push(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            host = root / "tools/control/HavenwildPccHost.ps1"
            host.parent.mkdir(parents=True)
            host.write_text("# fixture", encoding="utf-8")
            full = gui.pcc_command_argv(root, "pcc-full")
            publish = gui.pcc_command_argv(root, "pcc-publish")
            self.assertEqual(full[-2:], ["-Command", "validation.full-quality-gate"])
            self.assertEqual(publish[-2:], ["-Command", "source-control.commit-push-green"])
            self.assertIn("-NonInteractive", publish)
            self.assertNotIn("git", publish[:1])
            with self.assertRaises(KeyError):
                gui.pcc_command_argv(root, "push")
            host.unlink()
            with self.assertRaises(FileNotFoundError):
                gui.pcc_command_argv(root, "pcc-publish")

    def test_quick_state_reads_existing_pcc_without_mutating_it(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            script = root / "tools/control/PccQuickState.py"
            script.parent.mkdir(parents=True)
            state = {"schema": "havenwild.pcc_quick_state.v1", "branch": "experimental",
                     "gateState": "GREEN", "publicationEligible": True}
            script.write_text("import json; print(json.dumps(" + repr(state) + "))\n", encoding="utf-8")
            self.assertEqual(gui.load_pcc_quick_state(root), state)
            self.assertEqual(script.read_text(encoding="utf-8"), "import json; print(json.dumps(" + repr(state) + "))\n")
            script.write_text("print('NOT_JSON')\n", encoding="utf-8")
            self.assertEqual(gui.load_pcc_quick_state(root)["gateState"], "UNAVAILABLE")

    def test_dashboard_pcc_publish_uses_same_headless_stream_and_log(self):
        import queue
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            app = gui.PCCApp.__new__(gui.PCCApp)
            app.root_path = root
            app.busy = False
            app.proc = None
            app._operation_log = None
            app._operation_log_path = None
            app._log_chunks = 0
            app.log_text = Mock()
            app.console_path_label = Mock()
            app.output_queue = queue.Queue()
            app.set_busy = Mock()
            app.state_dir = lambda: root / ".forgepy/state"
            with patch.object(gui, "pcc_command_argv", return_value=[sys.executable, "-u", "-c", "print('PCC-PUBLISH-EVIDENCE')"]):
                app.run_backend("pcc-publish")
                while True:
                    kind, payload = app.output_queue.get(timeout=8)
                    if kind == "log":
                        app.append_log(payload)
                    elif kind == "done":
                        app.append_log(f"[GUI] Exit code: {payload[1]}\n")
                        self.assertEqual(payload[1], 0)
                        break
                    else:
                        self.fail(f"unexpected GUI event {kind}: {payload}")
            log = app._operation_log_path.read_text(encoding="utf-8")
            self.assertIn("PCC-PUBLISH-EVIDENCE", log)
            self.assertIn("[GUI] Exit code: 0", log)
            app._operation_log.close()

    def test_dashboard_publish_button_is_guarded_during_busy(self):
        app = gui.PCCApp.__new__(gui.PCCApp)
        app.pcc_state = {"branch": "experimental", "gateState": "GREEN", "publicationEligible": True,
                         "gitState": "Modified (1 path(s))", "quickCertificationReceipt": True,
                         "syncState": "LOCAL_AHEAD_GREEN_UNPUBLISHED"}
        app.publish_button = Mock()
        app.publish_status = Mock()
        app.busy = False
        app._update_publish_button()
        self.assertEqual(app.publish_button.configure.call_args.kwargs["state"], "normal")
        app.busy = True
        app._update_publish_button()
        self.assertEqual(app.publish_button.configure.call_args.kwargs["state"], "disabled")

    def test_copy_console_all_copies_entire_text_not_selection(self):
        app = gui.PCCApp.__new__(gui.PCCApp)
        app.window = Mock()
        app.footer = Mock()
        app.log_text = Mock()
        app.log_text.get.return_value = "all output\nincluding previous lines"
        app.copy_console_all()
        app.log_text.get.assert_called_once_with("1.0", "end-1c")
        app.window.clipboard_append.assert_called_once_with("all output\nincluding previous lines")

    def test_copy_full_log_uses_complete_persisted_bytes_and_cap(self):
        with tempfile.TemporaryDirectory() as td:
            app = gui.PCCApp.__new__(gui.PCCApp)
            app.window = Mock()
            app.footer = Mock()
            app._operation_log = None
            app._operation_log_path = Path(td) / "gui.log"
            app._operation_log_path.write_text("complete\ntranscript\n", encoding="utf-8")
            app.copy_full_operation_log()
            app.window.clipboard_append.assert_called_once_with("complete\ntranscript\n")
            app.window.reset_mock()
            with app._operation_log_path.open("ab") as file:
                file.truncate(17 * 1024 * 1024)
            app.copy_full_operation_log()
            app.window.clipboard_append.assert_not_called()

    def test_pcc_apply_routes_through_existing_noninteractive_host(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            host = root / "tools/control/HavenwildPccHost.ps1"
            host.parent.mkdir(parents=True)
            host.write_text("# stub", encoding="utf-8")
            argv = gui.pcc_command_argv(root, "pcc-apply")
            self.assertEqual(argv[-2:], ["-Command", "updates.apply-pending"])
            self.assertIn("-NonInteractive", argv)

    def test_zip_preflight_refuses_multiple_pending_and_renamed_copy(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            name = "Havenwild_CUMULATIVE_PCC_Patch_test.zip"
            manifest = {"schema": "havenwild.root_patch.v1", "project": "Havenwild",
                        "patchId": "test", "files": [{"path": "foo"}],
                        "lineage": {"baselineBranch": "experimental"}}
            with gui.zipfile.ZipFile(root / name, "w") as z:
                z.writestr("PATCH_MANIFEST.json", gui.json.dumps(manifest))
            rows = [{"path": name, "kind": "transport-zip"}]
            allowed, reason = gui.pcc_zip_apply_decision(root, name, rows)
            self.assertTrue(allowed, reason)
            (root / "Havenwild_Patch_extra.patch").write_text("diff", encoding="utf-8")
            self.assertFalse(gui.pcc_zip_apply_decision(root, name, rows)[0])
            self.assertFalse(gui.is_havenwild_intake_name("Havenwild_CUMULATIVE_PCC_Patch_test (1).zip"))
            self.assertFalse(gui.is_havenwild_intake_name("Havenwild_FULL_SOURCE_TEST.zip"))

    def test_zip_button_uses_pcc_and_never_generic_patch_engine(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            name = "Havenwild_CUMULATIVE_PCC_Patch_safe.zip"
            manifest = {"schema": "havenwild.root_patch.v1", "project": "Havenwild",
                        "patchId": "safe", "files": [{"path": "foo"}]}
            with gui.zipfile.ZipFile(root / name, "w") as z:
                z.writestr("PATCH_MANIFEST.json", gui.json.dumps(manifest))
            app = gui.PCCApp.__new__(gui.PCCApp)
            app.root_path = root
            app.window = Mock()
            app.patch_rows = [{"path": name, "kind": "transport-zip"}]
            app.selected_patch = Mock(return_value=app.patch_rows[0])
            app.run_backend = Mock()
            with patch.object(gui.messagebox, "askyesno", return_value=True):
                app.apply_selected_patch()
            app.run_backend.assert_called_once_with("pcc-apply")
            app.run_backend.reset_mock()
            (root / "Havenwild_Patch_other.patch").write_text("unrelated", encoding="utf-8")
            app.append_log = Mock()
            with patch.object(gui.messagebox, "showwarning"):
                app.apply_selected_patch()
            app.run_backend.assert_not_called()

    def test_pcc_script_has_noninteractive_apply_branch(self):
        host = Path(__file__).resolve().parents[2] / "tools/control/HavenwildPccHost.ps1"
        self.assertTrue(host.is_file())
        self.assertIn("elseif($Command -eq 'updates.apply-pending')", host.read_text(encoding="utf-8"))
        self.assertIn("Invoke-PccPatchIntake -ResumeCommand 'updates.apply-pending'", host.read_text(encoding="utf-8"))

    def test_zip_manifest_rejects_wrong_project_or_redirect(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            name = "Havenwild_Patch_bad.zip"
            with gui.zipfile.ZipFile(root / name, "w") as z:
                z.writestr("PATCH_MANIFEST.json", gui.json.dumps({"schema": "bad", "project": "other"}))
            with self.assertRaises(ValueError):
                gui.inspect_havenwild_zip(root, name)
            with self.assertRaises(ValueError):
                gui.inspect_havenwild_zip(root, "../outside.zip")

    def test_unterminated_output_reaches_runtime_log(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "partial.log"
            code = runtime.stream(
                [sys.executable, "-c", "import sys; sys.stdout.write('WITHOUT_NEWLINE'); sys.stdout.flush()"],
                Path(td), log,
            )
            self.assertEqual(code, 0)
            self.assertEqual(log.read_text(encoding="utf-8"), "WITHOUT_NEWLINE")

    def test_windowless_fallback_does_not_launch_menu(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch.object(gui.subprocess, "call", side_effect=AssertionError("unexpected console")):
                self.assertEqual(gui.cli_fallback(root, "no display"), 2)
            self.assertIn("no display", (root / ".forgepy/state/logs/gui-startup-error.log").read_text())


if __name__ == "__main__":
    unittest.main()
