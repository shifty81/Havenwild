#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
ARCH = ROOT / "crates/haven_world/src/archipelago_skeleton.rs"
EDITOR = ROOT / "crates/haven_game/src/runtime_editor_shell.rs"


def main() -> int:
    arch = ARCH.read_text(encoding="utf-8")
    editor = EDITOR.read_text(encoding="utf-8")
    failures: list[str] = []

    if "struct LandmassSpec" not in arch or "fn landmass(spec: LandmassSpec)" not in arch:
        failures.append("archipelago landmass construction is not routed through LandmassSpec")
    if "fn landmass(id:" in arch:
        failures.append("legacy ten-argument landmass helper remains")
    if "#[allow(clippy::too_many_arguments)]" in arch:
        failures.append("too_many_arguments is suppressed instead of refactored")

    retired_helpers = (
        "fn editor_cardinal_count(",
        "fn editor_neighbor_count(",
        "fn is_editor_water(",
        "fn is_editor_land_or_shore(",
    )
    remaining = [helper for helper in retired_helpers if helper in editor]
    if remaining:
        failures.append("unused legacy shore helpers remain: " + ", ".join(remaining))

    if failures:
        for failure in failures:
            print(f"V145I ERROR: {failure}")
        return 1

    print("Pass 145I archipelago Clippy cleanup validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
