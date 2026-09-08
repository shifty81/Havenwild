#!/usr/bin/env python3
"""Validate the LPC terrain-map-v7 replacement path and canonical material bindings."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SOURCE = ROOT / "content/assets/lpc/source/lpc-terrains-v7"
MANIFEST = ROOT / "assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json"
ATLAS = ROOT / "assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.png"
PREVIEW = ROOT / "docs/assets/previews/havenwild_lpc_mapped_terrain_v7_pass114.png"
BINDINGS = ROOT / "content/assets/terrain_material_bindings_v0_2.json"
BINDINGS_RS = ROOT / "crates/haven_assets/src/terrain_material_bindings.rs"


def require_text(path: str, needles: list[str]) -> None:
    payload = (ROOT / path).read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in payload]
    if missing:
        raise SystemExit(f"V122: {path} missing {missing}")


def binding_map() -> dict[str, dict]:
    payload = json.loads(BINDINGS.read_text(encoding="utf-8"))
    if payload.get("schema") != "havenwild.terrain_material_bindings.v0_2":
        raise SystemExit("V122: wrong canonical terrain binding schema")
    bindings = payload.get("bindings")
    if not isinstance(bindings, list) or not bindings:
        raise SystemExit("V122: canonical terrain binding registry is empty")
    result: dict[str, dict] = {}
    for binding in bindings:
        tile_kind = binding.get("tileKind")
        if not isinstance(tile_kind, str) or not tile_kind:
            raise SystemExit("V122: canonical terrain binding missing tileKind")
        if tile_kind in result:
            raise SystemExit(f"V122: duplicate canonical terrain binding for {tile_kind}")
        result[tile_kind] = binding
    return result


def require_binding(bindings: dict[str, dict], tile_kind: str, **expected: object) -> None:
    binding = bindings.get(tile_kind)
    if binding is None:
        raise SystemExit(f"V122: missing canonical terrain binding for {tile_kind}")
    mismatched = {
        key: (binding.get(key), value)
        for key, value in expected.items()
        if binding.get(key) != value
    }
    if mismatched:
        raise SystemExit(f"V122: invalid canonical binding for {tile_kind}: {mismatched}")


def main() -> int:
    for path in [
        SOURCE / "CREDITS-terrain.txt",
        SOURCE / "terrain-map-v7.tsx",
        SOURCE / "terrain-map-v7.png",
        SOURCE / "terrain-v7.tsx",
        SOURCE / "terrain-v7.png",
        MANIFEST,
        ATLAS,
        PREVIEW,
        BINDINGS,
        BINDINGS_RS,
    ]:
        if not path.is_file():
            raise SystemExit(f"V122: missing {path.relative_to(ROOT)}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("id") != "lpc_mapped_terrain_v7_32":
        raise SystemExit("V122: wrong mapped terrain manifest id")

    entries = manifest.get("entries", [])
    # Pass 150's canonical material separation legitimately changes duplicate
    # elimination. Validate meaningful topology coverage instead of the obsolete
    # exact 5,760-entry floor.
    if len(entries) < 5_700:
        raise SystemExit(
            f"V122: mapped terrain manifest has unexpectedly low tuple coverage ({len(entries)})"
        )

    coverage = manifest.get("coverage", {})
    if coverage.get("mappedTileKinds", 0) < 20:
        raise SystemExit("V122: natural terrain tile-kind coverage regressed")
    if coverage.get("mappedSourceMaterials", 0) < 16:
        raise SystemExit("V122: mapped LPC source-material coverage regressed")
    if coverage.get("completeTwoMaterialPairs", 0) < 59:
        raise SystemExit("V122: complete 14-shape pair coverage regressed")

    fill_variants = coverage.get("pureFillVariantCounts", {})
    for material, minimum in {
        "Grass": 5,
        "Dirt_Brown": 4,
        "Sand": 5,
        "Rock_Gray": 4,
        "Water": 4,
    }.items():
        if fill_variants.get(material, 0) < minimum:
            raise SystemExit(f"V122: pure-fill variants regressed for {material}")

    topology_counts = coverage.get("topologyCounts", {})
    for topology in [
        "fill",
        "outer_corner",
        "inner_corner",
        "edge",
        "diagonal_split",
        "junction_3_material",
        "junction_4_material",
    ]:
        if topology_counts.get(topology, 0) < 1:
            raise SystemExit(f"V122: missing mapped topology class {topology}")

    tuples = {
        (
            entry["corners"]["topLeft"],
            entry["corners"]["topRight"],
            entry["corners"]["bottomLeft"],
            entry["corners"]["bottomRight"],
        )
        for entry in entries
    }
    for terrain in [
        "Grass",
        "Dirt_Brown",
        "Sand",
        "Water_Shallows_Sand",
        "Water",
        "Water_Deep",
    ]:
        pure = (terrain, terrain, terrain, terrain)
        if pure not in tuples:
            raise SystemExit(f"V122: missing pure mapped fill tuple {terrain}")
    if ("Sand", "Grass", "Grass", "Grass") not in tuples:
        raise SystemExit("V122: missing sand/grass mixed corner tuple")

    bindings = binding_map()
    require_binding(bindings, "WetSand", material="Sand", renderMode="generated_band", overlay="wet_sand")
    require_binding(bindings, "PebbleShore", material="Gravel_1", renderMode="corner_tuple")
    require_binding(bindings, "StonePath", material="Stone_Tan", renderMode="corner_tuple")
    require_binding(bindings, "MountainPath", material="Dirt_Roots", renderMode="corner_tuple")
    require_binding(bindings, "RiverMouthBlend", material="Water_Shallows_Dirt", renderMode="corner_tuple")
    require_binding(bindings, "Bridge", material=None, renderMode="structure", tupleFallbackMaterial="Dirt_Tan")
    require_binding(bindings, "ShoreFoam", material=None, renderMode="overlay", overlay="shore_foam", tupleFallbackMaterial="Water_Shallows_Sand")

    if bindings["PebbleShore"].get("material") == bindings["StonePath"].get("material"):
        raise SystemExit("V122: PebbleShore and StonePath must remain semantically distinct")
    if bindings["MountainPath"].get("material") == bindings["Road"].get("material"):
        raise SystemExit("V122: MountainPath and Road must remain semantically distinct")

    require_text(
        "crates/haven_assets/src/lpc_mapped_terrain.rs",
        [
            "LPC_MAPPED_TERRAIN_ATLAS_PATH",
            "lpc_mapped_terrain_entry_for_map",
            "lpc_mapped_terrain_transition_covers_map_cell",
            "lpc_mapped_terrain_owns_map_cell",
            "lpc_mapped_terrain_preview_entry",
            "deterministic_fill_variant",
            "mapped_terrain_corners_for_map_tile",
            "is_mixed",
            "canonical_corner_tuple_material(tile)",
            "CARGO_MANIFEST_DIR",
        ],
    )
    require_text(
        "crates/haven_assets/src/terrain_material_bindings.rs",
        [
            "TERRAIN_MATERIAL_BINDINGS_PATH",
            "canonical_corner_tuple_material",
            "TileKind::WetSand",
            "TileKind::PebbleShore",
            "TileKind::StonePath",
            "TileKind::ShoreFoam",
        ],
    )
    require_text(
        "crates/haven_game/src/runtime_terrain_pass.rs",
        [
            "lpc_mapped_terrain_transition_covers_map_cell(map, cell.x, cell.y)",
            "self.lpc_mapped_terrain_atlas.is_some()",
            "TILE_SIZE + 0.20",
            "draw_tile_transition_overlays(",
            "cell.transitions",
            "transition_atlas",
        ],
    )
    require_text(
        "crates/haven_game/src/runtime_assets.rs",
        ["lpc_mapped_terrain_atlas_path", "lpc_mapped_terrain:"],
    )
    require_text(
        "tools/build/Build.sh",
        ["build mapped LPC terrain replacement atlas"],
    )
    print(
        "V122 OK: mapped LPC topology and Pass 150 canonical terrain bindings are wired and guarded"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
