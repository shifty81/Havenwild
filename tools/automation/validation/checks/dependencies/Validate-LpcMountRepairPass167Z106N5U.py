#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[5]
SCRIPT = ROOT / "tools/automation/dependencies/Ensure-LpcDependency.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"LPC mount repair validation FAILED: {message}")


spec = importlib.util.spec_from_file_location("havenwild_lpc_dependency", SCRIPT)
require(spec is not None and spec.loader is not None, "unable to import Ensure-LpcDependency.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

source = SCRIPT.read_text(encoding="utf-8")
require("def path_entry_exists" in source, "lexical filesystem-entry predicate is missing")
require("path.lstat()" in source, "repair path must inspect the directory entry without following it")
require("FILE_ATTRIBUTE_REPARSE_POINT" in source, "Windows reparse-point fallback is missing")
require("def replace_directory_entry" in source, "transactional destination replacement helper is missing")
require("getattr(exc, \"winerror\", None) != 183" in source, "WinError 183 retry contract is missing")
require("replace_directory_entry(staging, destination)" in source, "LPC mount still uses direct staging.rename")

with tempfile.TemporaryDirectory(prefix="havenwild-lpc-mount-repair-") as temp_root_text:
    temp_root = Path(temp_root_text)
    target = temp_root / "target"
    destination = temp_root / "lpc_revised"
    staging = temp_root / "lpc_revised.tmp"
    target.mkdir()
    (target / "sentinel.txt").write_text("target\n", encoding="utf-8")

    module.create_directory_link(target, destination)
    shutil.rmtree(target)
    require(module.path_entry_exists(destination), "dangling directory-link entry was not detected")

    staging.mkdir()
    (staging / "mounted.txt").write_text("replacement\n", encoding="utf-8")
    module.replace_directory_entry(staging, destination)

    require(destination.is_dir(), "replacement destination was not installed")
    require((destination / "mounted.txt").is_file(), "replacement payload is missing")
    require(not module.path_entry_exists(staging), "staging entry remained after replacement")

print("LPC mount repair V167Z106N5U validated")
