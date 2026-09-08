#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[5]


def load(rel: str) -> dict:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Terrain style/cliff/F3: missing {rel}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def text(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Terrain style/cliff/F3: missing {rel}")
    return path.read_text(encoding="utf-8-sig")


def fail(message: str) -> None:
    raise SystemExit(f"Terrain style/cliff/F3: {message}")


def main() -> int:
    v7 = load("content/worldgen/v7_terrain_role_catalog_v0_1.json")
    eliza = load("content/worldgen/elizawy_terrain_role_catalog_v0_1.json")
    eliza_cliffs = load("content/worldgen/elizawy_cliff_sheet_role_catalog_v0_1.json")
    isolation = load("content/worldgen/elizawy_tile_lane_isolation_contract_v0_1.json")
    cliff = load("content/worldgen/cliff_authoring_contract_v0_1.json")
    family = load("content/worldgen/terrain_visual_family_authority_v0_1.json")
    f3 = load("content/editor/f3_terrain_style_workspace_v0_1.json")
    bindings = load("content/assets/terrain_material_bindings_v0_2.json")
    palette = load("content/terrain/havenwild_terrain_authoring_palette_v1.json")
    oga = load("content/assets/oga_lpc/manifests/oga_lpc_cliff_cell_catalog_v0_1.json")

    materials = v7.get("materials", [])
    if len(materials) != 34:
        fail(f"expected 34 V7 materials, found {len(materials)}")
    if any(item.get("structuralCliffFace") is not False for item in materials):
        fail("a V7 surface material was promoted as a structural cliff face")
    required_v7 = {
        "Rock_White", "Rock_Gray", "Rock_Dark", "Rock_Black",
        "Stone_White", "Stone_Tan", "Mudstone_Gray", "Mudstone_Brown",
        "Hole_Brown", "Hole_Black", "Snow_1", "Snow_2", "Ice", "Lava",
    }
    found_v7 = {item.get("materialId") for item in materials}
    missing_v7 = sorted(required_v7 - found_v7)
    if missing_v7:
        fail(f"V7 role catalog is missing terrain families: {missing_v7}")

    if eliza.get("crossFamilyFallbackAllowed") is not False:
        fail("ElizaWy role catalog allows cross-family fallback")
    if eliza.get("sourceCommit") != isolation.get("sourceCommit"):
        fail("ElizaWy role catalog and isolation contract disagree on source commit")
    family_ids = {item.get("id") for item in eliza.get("families", [])}
    for required in {
        "seasonal_ground_water_coast", "seasonal_structural_cliffs",
        "farm_soil", "winter_shallows", "waterfall_features", "rock_props",
    }:
        if required not in family_ids:
            fail(f"ElizaWy terrain role catalog is missing {required}")

    grid = eliza_cliffs.get("grid", {})
    expected_grid = {"tileSize": [32, 32], "columns": 16, "rows": 14, "cellCount": 224}
    if any(grid.get(key) != value for key, value in expected_grid.items()):
        fail(f"unexpected ElizaWy cliff grid: {grid}")
    if grid.get("independentCellPlacementAllowed") is not False:
        fail("ElizaWy source grid was incorrectly treated as independent 1x1 asset authority")
    sheets = eliza_cliffs.get("seasonalSheets", [])
    if len(sheets) != 5:
        fail(f"expected five seasonal ElizaWy cliff sheets, found {len(sheets)}")
    alpha_hashes = {sheet.get("alphaMaskSha256") for sheet in sheets}
    if len(alpha_hashes) != 1 or None in alpha_hashes:
        fail("ElizaWy seasonal cliff sheets do not share one audited alpha geometry")
    if eliza_cliffs.get("geometryAudit", {}).get("identicalAlphaGeometryAcrossSeasons") is not True:
        fail("ElizaWy cliff geometry parity is not certified")
    cells = eliza_cliffs.get("cells", [])
    if len(cells) != 224:
        fail(f"expected all 224 ElizaWy cliff cells to be audited, found {len(cells)}")
    if sum(bool(cell.get("occupied")) for cell in cells) != eliza_cliffs["geometryAudit"]["occupiedCellCount"]:
        fail("ElizaWy occupied-cell count disagrees with geometry audit")
    if eliza_cliffs.get("capabilityConclusion", {}).get("supportsFlatGroundBrush") is not False:
        fail("ElizaWy connected cliff art was incorrectly approved as a flat ground brush")
    if eliza_cliffs.get("capabilityConclusion", {}).get("runtimePromotionComplete") is not False:
        fail("ElizaWy cliff recipes were marked production-complete before mapping")

    # When the external dependency is mounted, re-certify checksums and alpha geometry.
    mounted_root = ROOT / "assets/source/licensed/lpc_revised/Terrain"
    mounted = []
    for sheet in sheets:
        source_name = Path(sheet["sourcePath"]).name
        source = mounted_root / source_name
        if not source.is_file():
            continue
        mounted.append(source_name)
        data = source.read_bytes()
        if hashlib.sha256(data).hexdigest() != sheet["sha256"]:
            fail(f"mounted ElizaWy cliff checksum changed: {source_name}")
        with Image.open(source).convert("RGBA") as image:
            if list(image.size) != sheet["dimensions"]:
                fail(f"mounted ElizaWy cliff dimensions changed: {source_name}")
            alpha = hashlib.sha256(image.getchannel("A").tobytes()).hexdigest()
            if alpha != sheet["alphaMaskSha256"]:
                fail(f"mounted ElizaWy cliff alpha geometry changed: {source_name}")

    binding_source = text("crates/haven_assets/src/terrain_material_bindings.rs")
    for token in [
        "DerivedElevationStructure,",
        "TerrainRenderMode::DerivedElevationStructure",
        "derived_cliff_mode_loads_without_disabling_the_material_registry",
    ]:
        if token not in binding_source:
            fail(f"Rust terrain render-mode authority is missing: {token}")

    cliff_binding = next((item for item in bindings.get("bindings", []) if item.get("tileKind") == "Cliff"), None)
    if cliff_binding is None:
        fail("terrain bindings do not declare Cliff")
    if cliff_binding.get("directPaintAllowed") is not False:
        fail("terrain bindings still allow direct Cliff painting")
    if cliff_binding.get("renderMode") != "derived_elevation_structure":
        fail("Cliff binding is not owned by derived elevation structure")
    if cliff_binding.get("material") is not None or "tupleFallbackMaterial" in cliff_binding:
        fail("Cliff binding still declares a flat material or tuple fallback")

    palette_text = json.dumps(palette, sort_keys=True)
    if '"tile": "Cliff"' in palette_text or '"tileKind": "Cliff"' in palette_text:
        fail("authoring palette still contains a direct Cliff entry")

    defaults = text("crates/haven_editor/src/palette_defaults.rs")
    if "BuildTool::Floor(TileKind::Cliff)" in defaults:
        fail("default editor palette still exposes flat Cliff")
    generation = text("crates/haven_game/src/terrain_generation.rs")
    if "return TileKind::Cliff" in generation:
        fail("exterior height generation still emits flat Cliff tiles")
    for token in [
        "exterior_height_classification_never_returns_flat_cliff_tiles",
        "highland_rockline_selects_horizontal_rock_ground",
        "height >= mountain_level",
        "TileKind::MountainRock",
    ]:
        if token not in generation:
            fail(f"terrain generation regression guard missing: {token}")

    startup = text("crates/haven_game/src/runtime_startup.rs")
    for token in [
        "migrate_legacy_exterior_flat_cliff_tiles",
        "TileKind::MountainRock",
        "TileKind::Grass",
    ]:
        if token not in startup:
            fail(f"legacy flat-cliff migration is missing {token}")
    save_lib = text("crates/haven_save/src/lib.rs")
    version_marker = "CURRENT_CLIENT_GENERATION_VERSION: u32 = "
    if version_marker not in save_lib:
        fail("client generation version marker is missing")
    version = int(save_lib.split(version_marker, 1)[1].split(";", 1)[0].strip())
    if version < 10:
        fail("client generation version predates the source-pure V7 migration baseline 10")

    editor_state = text("crates/haven_game/src/editor_state.rs")
    for label in ["Ground", "Elevation", "Topology", "Sources"]:
        if f'\"{label}\"' not in editor_state:
            fail(f"F3 terrain workspace is missing {label} tab")
    map_editor = text("crates/haven_game/src/map_edit_runtime.rs")
    for token in ["Highland-", "Highland+", "Face step Δ2", "do not paint Cliff as a flat ground tile"]:
        if token not in map_editor:
            fail(f"F3 elevation workflow is missing: {token}")
    native_bridge = text("apps/haven_editor_native/src/app/world_asset_pixel_bridge.rs")
    if "if tile == TileKind::Cliff" not in native_bridge or "reviewed_v7_pure_fill_semantic_id(tile)" not in native_bridge:
        fail("native editor does not preserve structural Cliff exclusion plus exact material source authority")

    tab_ids = [item.get("id") for item in f3.get("tabs", [])]
    if tab_ids != ["world", "ground", "props", "zones", "elevation", "topology", "rules", "sources"]:
        fail(f"unexpected F3 tab authority: {tab_ids}")
    if f3.get("elevationControls", {}).get("directCliffPaintAllowed") is not False:
        fail("F3 workspace contract allows direct Cliff painting")

    providers = {item.get("id"): item for item in cliff.get("providers", [])}
    if providers.get("v7_surface_highlands", {}).get("status") != "surface_only":
        fail("V7 structural-cliff conclusion changed")
    elizawy_status = providers.get("elizawy_seasonal_cliffs", {}).get("status")
    if elizawy_status not in {
        "source_and_geometry_audited_runtime_recipe_mapping_pending",
        "indexed_seasonal_connected_region_recipes_in_progress",
        "source_audited_multi_cell_recipe_certification_pending",
        "runtime_primary_structural_cliff_authority_n5r",
    }:
        fail("ElizaWy cliff provider audit state is incorrect")
    provider_source = text("crates/haven_assets/src/elizawy_cliff_provider.rs")
    if elizawy_status == "runtime_primary_structural_cliff_authority_n5r":
        for token in ["ElizaWyCliffCertification::RuntimeCertified", "is_repeatable_vertical_body"]:
            if token not in provider_source:
                fail(f"promoted ElizaWy cliff provider is missing runtime certification marker: {token}")

    pure_families = {item.get("id"): item for item in family.get("families", [])}
    if pure_families.get("lpc_terrain_v7_island_v1", {}).get("directCliffPaintAllowed") is not False:
        fail("pure V7 family allows direct Cliff painting")
    if pure_families.get("elizawy_mainland_v1", {}).get("directCliffPaintAllowed") is not False:
        fail("pure ElizaWy family allows direct Cliff painting")

    nonempty_oga = [cell for cell in oga.get("cells", []) if not cell.get("empty")]
    if any(cell.get("review_state") != "unreviewed" for cell in nonempty_oga):
        fail("OGA cliff cells were promoted without semantic review")

    print(
        "Terrain style/cliff/F3 authority validated: "
        f"34 V7 surfaces, {len(cells)} ElizaWy cliff cells, "
        f"{len(sheets)} seasonal sheets, {len(mounted)} mounted sheets rechecked, "
        "no direct F3 Cliff brush or height-band Cliff generation"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
