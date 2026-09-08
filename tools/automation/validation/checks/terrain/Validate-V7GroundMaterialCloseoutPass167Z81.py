#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
ATLAS_JSON = ROOT / "assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json"
ATLAS_PNG = ROOT / "assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.png"


def read_text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8-sig")


def read_json(relative: str):
    return json.loads(read_text(relative))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def binding_by_tile(payload: dict, tile_kind: str) -> dict:
    return next(entry for entry in payload["bindings"] if entry["tileKind"] == tile_kind)


def require_all_pair_shapes(entries: set[tuple[str, str, str, str]], first: str, second: str) -> None:
    missing = []
    for corners in itertools.product((first, second), repeat=4):
        if first not in corners or second not in corners:
            continue
        if corners not in entries:
            missing.append(corners)
    assert not missing, f"missing authored {first}/{second} tuple shapes: {missing[:3]}"


def main() -> int:
    checkpoint = read_json("content/checkpoints/pass167z80_checkpoint_v0_1.json")
    assert checkpoint["checkpointId"] == "Pass167Z80"
    assert checkpoint["lockedByUser"] is True
    assert checkpoint["policy"]["subsequentWorkUsesThisCheckpoint"] is True

    canonical = read_text("crates/haven_core/src/foundation/tile_object_catalog.rs")
    for source in (canonical,):
        production_start = source.index("pub const LPC_PRODUCTION_TERRAIN")
        production_end = source.index("];", production_start)
        production = source[production_start:production_end]
        editor_start = source.index("pub const LPC_MAPPED_EDITOR_TERRAIN")
        editor_end = source.index("];", editor_start)
        editor = source[editor_start:editor_end]
        for block in (production, editor):
            assert "TileKind::PebbleShore" in block
            assert "TileKind::MountainRock" in block
            assert "TileKind::MudBank" in block
            assert "TileKind::WateredSoil" not in block
        assert 'TileKind::PebbleShore => "Gravel"' in source
        assert 'TileKind::MountainRock => "Rock Ground"' in source
        assert 'TileKind::MudBank => "Mud"' in source
        assert 'TileKind::WateredSoil => "Watered Tilled Soil"' in source
        assert '"pebble_shore" | "pebble_ground" | "gravel"' in source
        assert '"mud_bank" | "mud"' in source

    palette = read_text("crates/haven_assets/src/asset_palette.rs")
    assert "TileKind::WetSand | TileKind::WateredSoil" in palette
    assert 'catalog.entry("tile/watered_soil").is_none()' in palette
    assert 'catalog.entry("tile/mud_bank").is_some()' in palette

    defaults = read_text("crates/haven_authoring/src/palette.rs")
    assert "BuildTool::Floor(TileKind::MudBank)" in defaults
    assert "BuildTool::Floor(TileKind::WateredSoil)" not in defaults

    bindings = read_json("content/assets/terrain_material_bindings_v0_2.json")
    gravel = binding_by_tile(bindings, "PebbleShore")
    rock = binding_by_tile(bindings, "MountainRock")
    mud = binding_by_tile(bindings, "MudBank")
    watered = binding_by_tile(bindings, "WateredSoil")
    assert gravel["material"] == "Gravel_1" and gravel["directPaintAllowed"] is True
    assert rock["material"] == "Rock_Dark" and rock["directPaintAllowed"] is True
    assert mud["material"] == "Mud_Brown" and mud["directPaintAllowed"] is True
    assert watered["directPaintAllowed"] is False
    assert watered["stateOwner"] == "watering_action_on_tilled_soil"

    closeout = read_json("content/terrain/v7_ground_material_closeout_v0_1.json")
    assert closeout["revision"] == "167Z81"
    assert closeout["checkpoint"] == "Pass167Z80"
    assert closeout["farmingState"]["generalMudBrush"] == "MudBank"
    assert closeout["farmingState"]["directPaintAllowed"] is False
    for material in closeout["materials"]:
        assert material["edgePolicy"] == "exact_tuple_else_owner_fill_workbench_candidate"
        assert "connectors" not in material
        assert isinstance(material.get("referenceStyleHints"), dict)
    assert closeout["nextLane"]["name"] == "derived_elevation_cliffs"
    assert closeout["nextLane"]["directCliffBrush"] is False

    mapped = "\n".join(
        read_text(path)
        for path in (
            "crates/haven_assets/src/lpc_mapped_terrain.rs",
            "crates/haven_assets/src/lpc_mapped_terrain/sampling.rs",
            "crates/haven_assets/src/lpc_mapped_terrain/tests.rs",
        )
    )
    assert "compatible_edge_bridge_entry_for_corners" not in mapped
    assert "AuthoredBridge" not in mapped
    assert "missing_gravel_pairs_do_not_proxy_unrelated_v7_materials" in mapped
    assert "missing_rock_pairs_do_not_proxy_unrelated_v7_materials" in mapped
    assert "mud_uses_exact_edges_only_and_routes_missing_pairs_to_diagnostics" in mapped
    assert "global_sampler_keeps_missing_gravel_grass_pair_unsupported_across_partition_edge" in mapped

    terrain_render = read_text("crates/haven_game/src/terrain_render.rs")
    assert "TileKind::MudBank => LPC_V7_MUD_BROWN" in terrain_render

    terrain_contract = read_text("crates/haven_core/src/terrain_contract.rs")
    overlay_start = terrain_contract.index("pub const fn visual_overlay")
    overlay_end = terrain_contract.index("pub const fn terrain_gameplay_profile", overlay_start)
    assert "TileKind::MudBank" not in terrain_contract[overlay_start:overlay_end]

    identity = read_text("crates/haven_world/src/terrain_identity_v2.rs")
    assert "!matches!(tile, TileKind::WateredSoil)" in identity
    assert "is_paintable_surface_v2(TileKind::MudBank)" in identity
    assert "!is_paintable_surface_v2(TileKind::WateredSoil)" in identity

    contacts = read_text("crates/haven_assets/src/authored_terrain_contacts.rs")
    assert "mountain_path_touching_general_gravel_keeps_its_v7_material" in contacts

    # W77 intentionally rebuilds the normalized atlas as exact material/tuple truth.
    # Historical byte hashes are not an authority boundary; semantic coverage is.
    assert ATLAS_JSON.is_file() and ATLAS_PNG.is_file()
    manifest = json.loads(ATLAS_JSON.read_text(encoding="utf-8-sig"))
    tile_map = manifest.get("tileKindTerrainMap", {})
    assert tile_map.get("stone_path") == "Stone_Tan"
    assert tile_map.get("pebble_shore") == "Gravel_1"
    assert tile_map.get("road") == "Dirt_Tan"
    assert tile_map.get("mountain_path") == "Dirt_Roots"
    assert tile_map.get("mud_bank") == "Mud_Brown"
    assert tile_map.get("wet_sand") == "Sand"
    assert "cliff" not in tile_map
    coverage = manifest.get("coverage", {})
    assert coverage.get("mappedSourceMaterials") == 15
    assert coverage.get("completeTwoMaterialPairs") == 48
    assert coverage.get("twoMaterialPairShapeTarget") == 14
    workbench = read_json("content/editor/terrain_transition_workbench/terrain_transition_workbench_v1.json")
    assert workbench.get("materialCount") == 15
    assert workbench.get("completeDirectPairCount") == 48
    assert workbench.get("missingPairCount") == 57
    assert len(workbench.get("documents", [])) == 57
    entries = {
        (
            entry["corners"]["topLeft"],
            entry["corners"]["topRight"],
            entry["corners"]["bottomLeft"],
            entry["corners"]["bottomRight"],
        )
        for entry in manifest["entries"]
    }
    for material in ("Gravel_1", "Rock_Dark", "Mud_Brown"):
        assert (material, material, material, material) in entries
    # Every pair advertised as complete must provide all 14 mixed 2x2 shapes.
    materials = sorted(set(tile_map.values()))
    complete_pairs = []
    for first, second in itertools.combinations(materials, 2):
        try:
            require_all_pair_shapes(entries, first, second)
        except AssertionError:
            continue
        complete_pairs.append((first, second))
    assert len(complete_pairs) == 48, f"expected 48 complete direct pairs, got {len(complete_pairs)}"

    print("Pass167Z81 V7 ground material closeout validated")
    print("- Pass167Z80 checkpoint locked")
    print("- Gravel, Rock Ground and Mud are direct V7 ground brushes")
    print("- Watered Tilled Soil remains a farming state")
    print("- exact-only mixed tuples verified; unsupported pairs route to W77 workbench")
    print("- normalized V7 atlas semantic coverage matches current exact-material authority")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
