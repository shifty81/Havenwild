#!/usr/bin/env python3
"""Validate the terrain material, biome, and asset-library planning registries."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
TERRAIN_REGISTRY = ROOT / "content/assets/terrain_material_registry_v0_1.json"
BIOME_REGISTRY = ROOT / "content/worldgen/biome_registry_v0_1.json"
ASSET_LIBRARY = ROOT / "content/assets/havenwild_asset_library_v0_1.json"
MATRIX = ROOT / "docs/TERRAIN_COMPLETION_MATRIX.md"
TILE_CATALOG = ROOT / "crates/haven_core/src/foundation/tile_object_catalog.rs"
MAPPED_TERRAIN = ROOT / "crates/haven_assets/src/lpc_mapped_terrain.rs"

EXPECTED_CODES = {
    "grass",
    "tall_grass",
    "sand",
    "wet_sand",
    "pebble_shore",
    "road",
    "stone_path",
    "mountain_path",
    "wood_floor",
    "plank_floor",
    "stone_floor",
    "brick_floor",
    "wall",
    "cliff",
    "mountain_rock",
    "dirt",
    "bridge",
    "cave_floor",
    "cave_wall",
    "tilled_soil",
    "watered_soil",
    "crop_seedling",
    "greenhouse_zone",
    "water",
    "shallow_water",
    "deep_water",
    "ocean_deep",
    "ocean_shallow",
    "river_water",
    "river_mouth_blend",
    "shore_foam",
    "mud_bank",
}

REQUIRED_BIOMES = {
    "temperate",
    "coastal",
    "forest",
    "farm",
    "town",
    "highlands",
    "river_wetland",
    "cave",
    "interior",
    "winter",
    "greenhouse",
}

VALID_PAINT_MODES = {"direct", "advanced", "generated", "deferred"}
VALID_STATUSES = {"production", "preview", "incomplete", "deferred"}
VALID_GROUPS = {"Ground", "Shore", "Water", "Paths", "Rock", "Cave", "Interior", "Farm", "Deferred"}


def load_json(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"V126: missing {path.relative_to(ROOT)}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"V126: invalid json {path.relative_to(ROOT)}: {exc}") from exc


def require_text(path: Path, needles: list[str]) -> None:
    if not path.is_file():
        raise SystemExit(f"V126: missing {path.relative_to(ROOT)}")
    payload = path.read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in payload]
    if missing:
        raise SystemExit(f"V126: {path.relative_to(ROOT)} missing {missing}")


def rust_tile_codes() -> set[str]:
    source = TILE_CATALOG.read_text(encoding="utf-8")
    match = re.search(r"pub const ALL: \[TileKind; 32\] = \[(.*?)\];", source, re.S)
    if not match:
        raise SystemExit("V126: could not locate TileKind::ALL")
    variants = re.findall(r"TileKind::([A-Za-z0-9_]+)", match.group(1))
    code_map = {
        "Grass": "grass",
        "TallGrass": "tall_grass",
        "Sand": "sand",
        "WetSand": "wet_sand",
        "PebbleShore": "pebble_shore",
        "Road": "road",
        "StonePath": "stone_path",
        "MountainPath": "mountain_path",
        "WoodFloor": "wood_floor",
        "PlankFloor": "plank_floor",
        "StoneFloor": "stone_floor",
        "BrickFloor": "brick_floor",
        "Wall": "wall",
        "Cliff": "cliff",
        "MountainRock": "mountain_rock",
        "Dirt": "dirt",
        "Bridge": "bridge",
        "CaveFloor": "cave_floor",
        "CaveWall": "cave_wall",
        "TilledSoil": "tilled_soil",
        "WateredSoil": "watered_soil",
        "Crop": "crop_seedling",
        "GreenhouseZone": "greenhouse_zone",
        "Water": "water",
        "ShallowWater": "shallow_water",
        "DeepWater": "deep_water",
        "OceanDeep": "ocean_deep",
        "OceanShallow": "ocean_shallow",
        "RiverWater": "river_water",
        "RiverMouthBlend": "river_mouth_blend",
        "ShoreFoam": "shore_foam",
        "MudBank": "mud_bank",
    }
    try:
        return {code_map[variant] for variant in variants}
    except KeyError as exc:
        raise SystemExit(f"V126: TileKind::ALL includes unmapped variant {exc.args[0]}") from exc


def validate_terrain_registry() -> dict[str, dict]:
    registry = load_json(TERRAIN_REGISTRY)
    if registry.get("schema") != "havenwild.terrain_material_registry.v0_1":
        raise SystemExit("V126: terrain material registry schema mismatch")
    materials = registry.get("materials", [])
    if not isinstance(materials, list):
        raise SystemExit("V126: terrain materials must be a list")
    by_code: dict[str, dict] = {}
    for material in materials:
        code = material.get("code")
        if code in by_code:
            raise SystemExit(f"V126: duplicate terrain material {code}")
        by_code[code] = material
        if material.get("paintMode") not in VALID_PAINT_MODES:
            raise SystemExit(f"V126: {code} has invalid paintMode {material.get('paintMode')}")
        if material.get("status") not in VALID_STATUSES:
            raise SystemExit(f"V126: {code} has invalid status {material.get('status')}")
        if material.get("editorGroup") not in VALID_GROUPS:
            raise SystemExit(f"V126: {code} has invalid editorGroup {material.get('editorGroup')}")
        if not material.get("topology"):
            raise SystemExit(f"V126: {code} missing topology")
        if not material.get("validBiomes"):
            raise SystemExit(f"V126: {code} missing validBiomes")

    codes = set(by_code)
    if codes != EXPECTED_CODES:
        raise SystemExit(
            "V126: terrain registry code mismatch: "
            f"missing={sorted(EXPECTED_CODES - codes)} extra={sorted(codes - EXPECTED_CODES)}"
        )
    rust_codes = rust_tile_codes()
    if codes != rust_codes:
        raise SystemExit(
            "V126: registry does not match TileKind::ALL: "
            f"missing={sorted(rust_codes - codes)} extra={sorted(codes - rust_codes)}"
        )

    if by_code["wet_sand"]["paintMode"] != "generated":
        raise SystemExit("V126: wet_sand must be generated")
    if by_code["shore_foam"]["paintMode"] != "generated":
        raise SystemExit("V126: shore_foam must be generated")
    if by_code["river_mouth_blend"]["paintMode"] != "generated":
        raise SystemExit("V126: river_mouth_blend must be generated")
    if by_code["greenhouse_zone"]["paintMode"] != "deferred":
        raise SystemExit("V126: greenhouse_zone must be deferred")
    if by_code["greenhouse_zone"]["topology"] != "interior_scene_transition_marker":
        raise SystemExit("V126: greenhouse_zone must be an interior scene transition marker")
    if by_code["stone_path"]["category"] == by_code["pebble_shore"]["category"]:
        raise SystemExit("V126: stone_path and pebble_shore must not share the same semantic category")
    for code in ["cliff", "mountain_rock"]:
        if by_code[code]["topology"] != "structural_rock":
            raise SystemExit(f"V126: {code} must use structural_rock topology")

    return by_code


def validate_biome_registry(materials: dict[str, dict]) -> None:
    registry = load_json(BIOME_REGISTRY)
    if registry.get("schema") != "havenwild.biome_registry.v0_1":
        raise SystemExit("V126: biome registry schema mismatch")
    defaults = registry.get("defaults", {})
    if defaults.get("dayLengthRealSeconds") != 3600:
        raise SystemExit("V126: biome defaults must keep one in-game day at 3600 real seconds")
    if defaults.get("terrainDetailVariationPercent") != 50:
        raise SystemExit("V126: default terrain detail variation must be 50")
    if defaults.get("rareDetailPercent") != 5:
        raise SystemExit("V126: default rare detail percent must be 5")

    biomes = registry.get("biomes", [])
    ids = {biome.get("id") for biome in biomes}
    if ids != REQUIRED_BIOMES:
        raise SystemExit(
            "V126: biome registry mismatch: "
            f"missing={sorted(REQUIRED_BIOMES - ids)} extra={sorted(ids - REQUIRED_BIOMES)}"
        )
    material_codes = set(materials)
    for biome in biomes:
        biome_id = biome["id"]
        for key in ["requiredTerrain", "generatedTerrain"]:
            unknown = sorted(set(biome.get(key, [])) - material_codes)
            if unknown:
                raise SystemExit(f"V126: biome {biome_id} references unknown {key}: {unknown}")
        if not biome.get("sceneScopes"):
            raise SystemExit(f"V126: biome {biome_id} missing sceneScopes")
        if not biome.get("seasons"):
            raise SystemExit(f"V126: biome {biome_id} missing seasons")
    if "greenhouse_zone" in next(b for b in biomes if b["id"] == "temperate").get("requiredTerrain", []):
        raise SystemExit("V126: greenhouse_zone must not be temperate overworld terrain")


def validate_asset_library() -> None:
    library = load_json(ASSET_LIBRARY)
    if library.get("schema") != "havenwild.asset_library.v0_1":
        raise SystemExit("V126: asset library schema mismatch")
    sources = library.get("sources", [])
    ids = {source.get("id") for source in sources}
    for required in ["lpc_terrains_v7", "havenwild_production_environment_pass60", "lpc_dependency_external"]:
        if required not in ids:
            raise SystemExit(f"V126: asset library missing {required}")
    for source in sources:
        if source.get("status") not in {"production", "preview", "source_only", "blocked"}:
            raise SystemExit(f"V126: asset source {source.get('id')} has invalid status")
        if not source.get("bakeTargets"):
            raise SystemExit(f"V126: asset source {source.get('id')} missing bakeTargets")
    terrain_source = next(source for source in sources if source.get("id") == "lpc_terrains_v7")
    if terrain_source.get("primaryImage") != "content/assets/lpc/source/lpc-terrains-v7/terrain-v7.png":
        raise SystemExit("V126: lpc_terrains_v7 primary image must be terrain-v7.png")
    if terrain_source.get("generatedCompanionImage") != "content/assets/lpc/source/lpc-terrains-v7/terrain-map-v7.png":
        raise SystemExit("V126: lpc_terrains_v7 must declare terrain-map-v7 as generated companion")


def main() -> int:
    materials = validate_terrain_registry()
    validate_biome_registry(materials)
    validate_asset_library()
    require_text(
        MATRIX,
        [
            "Havenwild Terrain Completion Matrix",
            "| wet_sand | Shore | generated | incomplete |",
            "| greenhouse_zone | Deferred | deferred | deferred |",
            "Pass121",
            "Pass122",
            "canonical terrain-v7 source-family normalization",
            "Pass126",
        ],
    )
    require_text(
        MAPPED_TERRAIN,
        [
            "TileKind::Sand | TileKind::WetSand => Some(LpcMappedTerrainMaterial::Sand)",
            "TileKind::Cliff | TileKind::MountainRock => None",
        ],
    )
    require_text(
        ROOT / "tools/build/Build.sh",
        ["Validate-TerrainMaterialRegistryV126.py"],
    )
    require_text(
        ROOT / "tools/automation/validation/validate.py",
        ["Validate-TerrainMaterialRegistryV126.py"],
    )
    print("V126 OK: terrain material, biome, and asset-library registries are locked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
