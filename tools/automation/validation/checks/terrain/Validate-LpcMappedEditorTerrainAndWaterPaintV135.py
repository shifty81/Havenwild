#!/usr/bin/env python3
"""Guard terrain-v7 editor exposure, shore paint normalization, and F3 toggle."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
EDITOR_TERRAIN = [
    "Grass",
    "TallGrass",
    "Dirt",
    "Sand",
    "WetSand",
    "PebbleShore",
    "Road",
    "StonePath",
    "MountainPath",
    "CaveFloor",
    "TilledSoil",
    "WateredSoil",
    "Water",
    "ShallowWater",
    "DeepWater",
    "OceanDeep",
    "OceanShallow",
    "RiverWater",
    "RiverMouthBlend",
    "ShoreFoam",
    "MudBank",
]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(path: str, needles: list[str]) -> None:
    text = read(path)
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f"V135: {path} missing {missing}")


def require_any(paths: list[str], needles: list[str]) -> None:
    payloads = [(path, read(path)) for path in paths if (ROOT / path).is_file()]
    if not payloads:
        raise SystemExit(f"V135: none of these files exist: {paths}")
    missing = [
        needle
        for needle in needles
        if not any(needle in payload for _, payload in payloads)
    ]
    if missing:
        raise SystemExit(
            f"V135: {', '.join(path for path, _ in payloads)} missing {missing}"
        )


def forbid(path: str, needles: list[str]) -> None:
    text = read(path)
    present = [needle for needle in needles if needle in text]
    if present:
        raise SystemExit(f"V135: {path} contains forbidden stale text {present}")


def main() -> int:
    tile_catalog = "crates/haven_core/src/foundation/tile_object_catalog.rs"
    palette = "crates/haven_editor/src/palette_defaults.rs"
    runtime_draw = "crates/haven_game/src/runtime_draw.rs"
    runtime_input = "crates/haven_game/src/runtime_input.rs"
    editor_shell = "crates/haven_game/src/runtime_editor_shell.rs"
    shore_tests = "crates/haven_game/src/runtime_editor_shell/shore_water_tests.rs"
    mapped_terrain = "crates/haven_assets/src/lpc_mapped_terrain.rs"
    mapped_terrain_tests = "crates/haven_assets/src/lpc_mapped_terrain_tests.rs"

    require(
        tile_catalog,
        [
            "pub const LPC_MAPPED_EDITOR_TERRAIN: [TileKind; 23]",
            "pub fn is_lpc_mapped_editor_terrain(self) -> bool",
        ]
        + [f"TileKind::{name}" for name in EDITOR_TERRAIN],
    )
    if "TileKind::Cliff,\n        TileKind::MountainRock,\n        TileKind::CaveFloor," in read(
        tile_catalog
    ).split("pub const LPC_MAPPED_EDITOR_TERRAIN", 1)[1].split("];", 1)[0]:
        raise SystemExit("V135: structural cliff/mountain rock leaked into mapped editor terrain")

    require(
        palette,
        [f"BuildTool::Floor(TileKind::{name})" for name in EDITOR_TERRAIN],
    )

    require(
        runtime_draw,
        [
            "tile.is_lpc_mapped_editor_terrain()",
            "TileKind::LPC_MAPPED_EDITOR_TERRAIN.len()",
            "terrain-map-v7 materials",
            '"generated"',
            '"overlay"',
            '"preview"',
        ],
    )

    require(
        runtime_input,
        [
            "if self.dev_mode {",
            "self.dev_mode = false;",
            "format!(\"Editor closed; edits saved to {}\", self.save_paths.world)",
        ],
    )
    forbid(runtime_input, ["KeyCode::LeftShift", "KeyCode::RightShift", "let closing"])
    forbid(runtime_draw, ["Shift+F3 close"])

    require(
        editor_shell,
        [
            "const SHORE_WATER_NORMALIZE_PAD: i32 = 4;",
            "const SHORE_WATER_NORMALIZE_PASSES: usize = 3;",
            "for _ in 0..SHORE_WATER_NORMALIZE_PASSES",
            "tile == TileKind::DeepWater && land_or_shore_neighbors > 0",
        ],
    )
    require(
        shore_tests,
        [
            "editor_sand_painted_over_deep_water_gets_wide_shallow_buffer",
            "editor_pebble_shore_painted_over_water_gets_shallow_buffer",
            "editor_road_painted_near_water_gets_shallow_buffer",
        ],
    )

    require(
        mapped_terrain,
        [
            "should_force_shore_fallback",
            "contains_water_and_land(corners)",
            "corners.contains(&LpcMappedTerrainMaterial::WaterDeep)",
            '#[path = "lpc_mapped_terrain_tests.rs"]',
        ],
    )
    require_any(
        [mapped_terrain, mapped_terrain_tests],
        [
            "missing_pebble_shore_water_tuples_do_not_fallback_to_square_land",
            "missing_road_water_tuples_do_not_fallback_to_square_land",
            "missing_mountain_path_water_tuples_do_not_fallback_to_square_land",
            "deep_water_land_tuples_use_stable_shore_fallbacks_instead_of_stale_exacts",
        ],
    )

    audit_path = ROOT / "content/assets/lpc/lpc_tuple_coverage_audit_v0_1.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    totals = audit.get("totals", {})
    exact = int(totals.get("exact", 0))
    fallback = int(totals.get("fallback", 0))
    if exact + fallback != 1536:
        raise SystemExit(
            f"V135: tuple coverage must resolve all 1536 patterns, found {exact}+{fallback}"
        )
    if fallback <= 0:
        raise SystemExit("V135: fallback count unexpectedly vanished; promotion audit may be stale")

    manifest_path = ROOT / "assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    terrain_map = manifest.get("tileKindTerrainMap", {})
    for tile_code in [
        "grass",
        "tall_grass",
        "dirt",
        "sand",
        "wet_sand",
        "pebble_shore",
        "road",
        "stone_path",
        "mountain_path",
        "cave_floor",
        "tilled_soil",
        "watered_soil",
        "water",
        "shallow_water",
        "deep_water",
        "ocean_deep",
        "ocean_shallow",
        "river_water",
        "river_mouth_blend",
        "shore_foam",
        "mud_bank",
    ]:
        if tile_code not in terrain_map:
            raise SystemExit(f"V135: mapped editor tile {tile_code} missing from terrain manifest")

    require("tools/build/Build.sh", ["Validate-LpcMappedEditorTerrainAndWaterPaintV135.py"])
    require("tools/automation/validation/validate.py", ["Validate-LpcMappedEditorTerrainAndWaterPaintV135.py"])
    print(
        "V135 OK: terrain-v7 editor brushes expose mapped semantics, all tuple patterns resolve, water-adjacent paint normalizes, and F3 toggles the editor"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
