#!/usr/bin/env python3
"""Validate editor shore/water normalization contract."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
EDITOR_SHELL = ROOT / "crates/haven_game/src/runtime_editor_shell.rs"
EDITOR_SHELL_TESTS = ROOT / "crates/haven_game/src/runtime_editor_shell/shore_water_tests.rs"
TERRAIN_REGISTRY = ROOT / "content/assets/terrain_material_registry_v0_1.json"
MATRIX = ROOT / "docs/TERRAIN_COMPLETION_MATRIX.md"


def require_text(path: Path, needles: list[str]) -> None:
    if not path.is_file():
        raise SystemExit(f"V127: missing {path.relative_to(ROOT)}")
    payload = path.read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in payload]
    if missing:
        raise SystemExit(f"V127: {path.relative_to(ROOT)} missing {missing}")


def main() -> int:
    registry = json.loads(TERRAIN_REGISTRY.read_text(encoding="utf-8"))
    materials = {material["code"]: material for material in registry["materials"]}
    for code in ["wet_sand", "shore_foam", "river_mouth_blend", "ocean_shallow", "ocean_deep"]:
        if materials[code]["paintMode"] != "generated":
            raise SystemExit(f"V127: {code} must remain generated terrain")
    if materials["sand"]["paintMode"] != "direct":
        raise SystemExit("V127: sand must remain direct paint terrain")
    if materials["shallow_water"]["paintMode"] != "direct":
        raise SystemExit("V127: shallow_water must remain direct paint terrain")
    if materials["deep_water"]["paintMode"] != "direct":
        raise SystemExit("V127: deep_water must remain direct paint terrain")

    require_text(
        EDITOR_SHELL,
        [
            "normalize_editor_shore_water_band",
            "normalize_shore_water_lifecycle_region",
            "SHORE_WATER_NORMALIZE_PAD",
            "SHORE_WATER_NORMALIZE_PASSES",
            "Sand touching cardinal water becomes wet sand.",
            "Wet sand away from cardinal water normalizes back to sand.",
            "tile == TileKind::Sand && water_cardinal > 0",
            "tile == TileKind::WetSand && water_cardinal == 0",
            "tile == TileKind::DeepWater && land_or_shore_neighbors > 0",
            "tile == TileKind::ShallowWater",
        ],
    )
    require_text(
        EDITOR_SHELL_TESTS,
        [
            "editor_sand_touching_water_becomes_wet_sand",
            "editor_diagonal_sand_water_contact_stays_dry_sand",
            "editor_inland_wet_sand_normalizes_back_to_sand",
            "editor_deep_water_touching_land_becomes_shallow",
            "editor_deep_water_diagonal_to_shore_becomes_shallow_for_corner_mapping",
        ],
    )
    require_text(
        MATRIX,
        [
            "| wet_sand | Shore | generated | incomplete | Auto-generate from sand touching cardinal water",
            "| shallow_water | Water | direct | preview | Enforce as land/deep-water border; render through terrain-v7 Water",
            "| deep_water | Water | direct | preview | Prevent direct 8-neighbor shore contact with a shallow-water buffer",
        ],
    )
    require_text(ROOT / "tools/build/Build.sh", ["Validate-ShoreWaterNormalizationV127.py"])
    require_text(ROOT / "tools/automation/validation/validate.py", ["Validate-ShoreWaterNormalizationV127.py"])
    print("V127 OK: editor shore/water normalization is guarded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
