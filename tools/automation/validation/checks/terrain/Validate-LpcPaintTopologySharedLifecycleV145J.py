#!/usr/bin/env python3
"""Guard V114 against requiring retired local shoreline helpers."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def main() -> int:
    validator = (ROOT / "tools/automation/validation/checks/terrain/Validate-LpcPaintTopologyStabilityV114.py").read_text(encoding="utf-8")
    runtime = (ROOT / "crates/haven_game/src/runtime_editor_shell.rs").read_text(encoding="utf-8")
    world = (ROOT / "crates/haven_world/src/autotile/shoreline_resolver.rs").read_text(encoding="utf-8")

    if '"editor_neighbor_count"' in validator:
        raise SystemExit("V145J: V114 still requires retired editor_neighbor_count helper")
    required = [
        '"normalize_shore_water_lifecycle_region"',
        '"SHORE_WATER_NORMALIZE_PAD"',
        '"SHORE_WATER_NORMALIZE_PASSES"',
    ]
    for token in required:
        if token not in validator:
            raise SystemExit(f"V145J: V114 missing shared lifecycle guard {token}")
    if "normalize_shore_water_lifecycle_region(" not in runtime:
        raise SystemExit("V145J: runtime editor no longer delegates to shared shoreline lifecycle")
    if "pub fn normalize_shore_water_lifecycle_region(" not in world:
        raise SystemExit("V145J: shared shoreline lifecycle resolver is missing")
    for retired in ["fn editor_neighbor_count(", "fn editor_cardinal_count(", "fn is_editor_water(", "fn is_editor_land_or_shore("]:
        if retired in runtime:
            raise SystemExit(f"V145J: retired helper returned: {retired}")
    print("Pass 145J V114 shared shoreline lifecycle compatibility validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
