#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[5]
SCRIPT = ROOT / "tools/automation/characters/Ensure-UniversalLpcGenerator.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"Universal LPC mount repair validation FAILED: {message}")


spec = importlib.util.spec_from_file_location("havenwild_universal_lpc_dependency", SCRIPT)
require(spec is not None and spec.loader is not None, "unable to import Ensure-UniversalLpcGenerator.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

source = SCRIPT.read_text(encoding="utf-8")
require("def path_entry_exists" in source, "lexical filesystem-entry predicate is missing")
require("path.lstat()" in source, "repair path must inspect directory entries without following junction targets")
require("FILE_ATTRIBUTE_REPARSE_POINT" in source, "Windows reparse-point fallback is missing")
require("def is_directory_link" in source, "directory-link classifier is missing")
require("unable to clear stale Universal LPC mount" in source, "mount destination cleanup assertion is missing")
require("mount_mode = create_link(destination.resolve(), mount)" in source, "cached source path does not always verify/remount the project mount")

with tempfile.TemporaryDirectory(prefix="havenwild-universal-lpc-mount-repair-") as temp_root_text:
    temp_root = Path(temp_root_text)
    old_target = temp_root / "old-target"
    new_target = temp_root / "new-target"
    destination = temp_root / "universal_lpc_generator"
    old_target.mkdir()
    new_target.mkdir()
    (new_target / "sentinel.txt").write_text("new target\n", encoding="utf-8")

    module.create_link(old_target, destination)
    shutil.rmtree(old_target)
    require(module.path_entry_exists(destination), "dangling Universal LPC directory-link entry was not detected")

    mode = module.create_link(new_target, destination)
    require(mode in {"junction", "symlink", "physical_copy", "existing_mount"}, f"unexpected remount mode {mode}")
    require(destination.is_dir(), "replacement Universal LPC mount was not installed")
    require((destination / "sentinel.txt").is_file(), "replacement mount does not resolve to the new target")
    require(module._same_directory(new_target.resolve(), destination), "replacement mount is not bound to the intended target")

print("Universal LPC mount repair V167Z106N5V validated")
