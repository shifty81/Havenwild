#!/usr/bin/env python3
"""Validate authoritative shore/water generated-material lifecycle."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
RESOLVER = ROOT / "crates/haven_world/src/autotile/shoreline_resolver.rs"
RESOLVER_TESTS = ROOT / "crates/haven_world/src/autotile/shoreline_resolver_tests.rs"
AUTOTILE_MOD = ROOT / "crates/haven_world/src/autotile/mod.rs"
GAME_MAIN = ROOT / "crates/haven_game/src/main.rs"
EDITOR = ROOT / "crates/haven_game/src/runtime_editor_shell.rs"
REGISTRY = ROOT / "content/assets/terrain_material_registry_v0_1.json"
DOC = ROOT / "docs/PASS138_SHORE_WATER_LIFECYCLE_20260720.md"


def require_text(path: Path, needles: list[str]) -> None:
    if not path.is_file():
        raise SystemExit(f"V138: missing {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f"V138: {path.relative_to(ROOT)} missing {missing}")


def main() -> int:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    materials = {entry["code"]: entry for entry in registry["materials"]}
    for code in ["wet_sand", "shore_foam", "river_mouth_blend", "ocean_shallow", "ocean_deep"]:
        if materials[code]["paintMode"] != "generated":
            raise SystemExit(f"V138: {code} must remain generated")

    require_text(
        RESOLVER,
        [
            "pub struct ShoreWaterLifecycleReport",
            "pub fn normalize_shore_water_lifecycle_region",
            "TileKind::Sand if water_cardinal > 0",
            "TileKind::WetSand if water_cardinal == 0",
            "TileKind::ShoreFoam if foam_shore_cardinal == 0 || water_cardinal == 0",
            "TileKind::ShallowWater",
            "Some(TileKind::ShoreFoam)",
            "TileKind::RiverWater if ocean_cardinal > 0",
            "Some(TileKind::RiverMouthBlend)",
            "TileKind::RiverMouthBlend if river_cardinal == 0 || ocean_cardinal == 0",
            "TileKind::OceanDeep if land_or_shore_neighbors > 0",
        ],
    )
    require_text(
        RESOLVER_TESTS,
        [
            "lifecycle_generates_and_removes_wet_sand",
            "lifecycle_generates_and_removes_shore_foam",
            "lifecycle_generates_and_cleans_river_mouths",
            "lifecycle_keeps_ocean_deep_behind_ocean_shallow",
        ],
    )
    require_text(AUTOTILE_MOD, ["normalize_shore_water_lifecycle_region", "ShoreWaterLifecycleReport"])
    require_text(GAME_MAIN, ["normalize_shore_water_lifecycle_region"])
    require_text(
        EDITOR,
        [
            "let _report = normalize_shore_water_lifecycle_region(",
            "SHORE_WATER_NORMALIZE_PASSES",
            "Shared lifecycle rules include the original guarded contracts",
        ],
    )
    require_text(ROOT / "content/validation/validation_manifest_v1.json", ["Validate-ShoreWaterLifecycleV138.py"])
    require_text(DOC, ["Wet-sand lifecycle", "Foam lifecycle", "River-mouth lifecycle", "Ocean-depth lifecycle"])
    print("V138 OK: shore/water generated-material lifecycle is shared, bounded, and guarded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
