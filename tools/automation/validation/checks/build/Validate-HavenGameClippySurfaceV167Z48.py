#!/usr/bin/env python3
"""Validate Pass 167Z48 Haven game Clippy surface repair wiring."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def require(path: str) -> str:
    file_path = ROOT / path
    if not file_path.is_file():
        raise SystemExit(f"missing required file: {path}")
    return file_path.read_text(encoding="utf-8")


def main() -> int:
    failures: list[str] = []
    script = require("tools/automation/project/Repair-HavenGameClippySurfaceV167Z48.py")
    for needle in (
        "167Z48-haven-game-clippy-surface-repair-v1",
        "repair_game_scratch_fields",
        "repair_creator_surface",
        "repair_superseded_title_art",
        "repair_compositor_clippy",
        "repair_default_initializers",
        "repair_staged_ui_lints",
    ):
        if needle not in script:
            failures.append(f"repair script missing {needle}")

    build_sh = require("tools/build/Build.sh")
    if "repair_haven_game_clippy_surface" not in build_sh:
        failures.append("Build.sh does not call the Z48 repair")
    if not re.search(
        r"repair_frontend_runtime_surface\s*\nrepair_haven_game_clippy_surface\s*\n",
        build_sh,
    ):
        failures.append("Build.sh repair ordering is not frontend then Clippy")

    build_ps1 = require("tools/build/Build.ps1")
    if "function Repair-HavenGameClippySurface" not in build_ps1:
        failures.append("Build.ps1 does not define the Z48 repair")
    if "Repair-FrontendRuntimeSurface\n    Repair-HavenGameClippySurface" not in build_ps1:
        failures.append("Build.ps1 repair ordering is not frontend then Clippy")

    summary = require("manifests/normalization/pass167z48/SUMMARY.json")
    if '"pass": "167Z48"' not in summary:
        failures.append("normalization summary has the wrong pass")

    if failures:
        raise SystemExit("Pass 167Z48 validation failed:\n- " + "\n- ".join(failures))
    print("Pass 167Z48 Haven game Clippy surface contract validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
