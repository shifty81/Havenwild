#!/usr/bin/env python3
"""Focused validation for Pass 167Z58 application-content staging repair."""
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
STAGE_PATH = ROOT / "tools" / "automation" / "release" / "Stage-ApplicationContent.py"
BUILD_SH = ROOT / "tools" / "build" / "Build.sh"
BUILD_PS1 = ROOT / "tools" / "build" / "Build.ps1"


def load_stage_module():
    spec = importlib.util.spec_from_file_location("havenwild_stage_application_content", STAGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {STAGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    errors: list[str] = []
    stage_source = STAGE_PATH.read_text(encoding="utf-8")
    for token in (
        "_absolute_without_resolving",
        "licensed_source_roots",
        "is_under_licensed_source",
        "prune_staged_dependency_development",
        "staged_forbidden_paths",
        "Windows dependency mounts are directory junctions",
    ):
        if token not in stage_source:
            errors.append(f"staging helper missing Z58 token: {token}")
    if "current.resolve().relative_to((ROOT / \"assets\").resolve())" in stage_source:
        errors.append("staging helper still uses the junction-breaking resolved-relative check")

    for path, tokens in (
        (BUILD_SH, ("Stage-ApplicationContent.py", "copy_application_content")),
        (BUILD_PS1, ("Stage-ApplicationContent.py", "Copy-ApplicationContent")),
    ):
        source = path.read_text(encoding="utf-8")
        for token in tokens:
            if token not in source:
                errors.append(f"{path.relative_to(ROOT)} missing staging token: {token}")

    try:
        stage = load_stage_module()
        callback_names = [".git", "tests", "tsconfig.json", "Terrain"]
        ignored = stage.licensed_ignore(
            str(stage.LICENSED_SOURCE_ROOT / "lpc_revised"), callback_names
        )
        expected = {".git", "tests", "tsconfig.json"}
        if ignored != expected:
            errors.append(f"licensed ignore mismatch: expected {sorted(expected)}, got {sorted(ignored)}")

        with tempfile.TemporaryDirectory(prefix="havenwild-z58-stage-") as temp:
            destination = Path(temp)
            mounted = destination / "assets" / "source" / "licensed" / "lpc_revised"
            (mounted / ".git").mkdir(parents=True)
            (mounted / ".git" / "config").write_text("fixture", encoding="utf-8")
            (mounted / "tests").mkdir()
            (mounted / "tests" / "fixture.txt").write_text("fixture", encoding="utf-8")
            (mounted / "__pycache__").mkdir()
            (mounted / "node_modules").mkdir()
            (mounted / "tsconfig.json").write_text("{}", encoding="utf-8")
            (mounted / "Terrain").mkdir()
            production = mounted / "Terrain" / "terrain_summer.png"
            production.write_bytes(b"fixture")

            removed = stage.prune_staged_dependency_development(destination)
            if len(removed) != 5:
                errors.append(f"expected 5 staged development paths removed, got {len(removed)}")
            if stage.staged_forbidden_paths(destination):
                errors.append("forbidden dependency-development paths remain after staging cleanup")
            if not production.is_file():
                errors.append("staging cleanup removed a production LPC source asset")
    except Exception as exc:  # pragma: no cover - validator must report full failure
        errors.append(f"staging behavior fixture failed: {exc}")

    if errors:
        print("\n".join(f"Pass 167Z58: {error}" for error in errors))
        return 1
    print("Pass 167Z58 application-content staging repair validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
