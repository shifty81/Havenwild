#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def load(path: str):
    return json.loads(read(path))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAILED Pass167Z104 cliff footprint normalization: {message}")


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    require(data[:8] == b"\x89PNG\r\n\x1a\n", f"PNG signature: {path}")
    require(data[12:16] == b"IHDR", f"PNG IHDR: {path}")
    return struct.unpack(">II", data[16:24])


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_rect(span: list[int]) -> list[int]:
    x, y, width, height = span
    return [x * 32, y * 32, width * 32, height * 32]


def rect_in_bounds(rect: list[int], width: int, height: int) -> bool:
    x, y, w, h = rect
    return x >= 0 and y >= 0 and w > 0 and h > 0 and x + w <= width and y + h <= height


def indexed_record(relative_path: str) -> dict:
    index = load("content/assets/intake/external_pack_indexes/elizawy_lpc_main.json")
    target = f"LPC-main/{relative_path}"
    for record in index["records"]:
        if record.get("relativePath") == target:
            return record
    raise SystemExit(f"FAILED Pass167Z104 cliff footprint normalization: missing locked ElizaWy index record {target}")


def main() -> None:
    current = ROOT / "content/worldgen/structural_cliff_autotile_authority_v0_1.json"
    if current.is_file():
        current_authority = json.loads(current.read_text(encoding="utf-8-sig"))
        if current_authority.get("pass") in {"167Z107", "167Z109C", "167Z109D", "167Z109G"} and current_authority.get("status") == "active":
            print("Historical cliff validator superseded by Pass167Z107 structural cliff autotile authority")
        return

    authority = load("content/worldgen/cliff_asset_footprint_recipe_normalization_v0_1.json")
    require(authority["pass"] == "167Z104", "authority pass")
    require(
        authority["measurementModel"]["criticalRule"]
        == "32x32 source cells are addresses, not automatically independent 1x1 world assets.",
        "source-grid/address rule",
    )
    gate = authority["runtimeGate"]
    require(gate["cliffDrawingEnabled"] is False, "renderer stays disabled")
    require(gate["proceduralCliffCollision"] == "fail_open", "collision stays fail-open")
    require(gate["individualSourceCellPromotionAllowed"] is False, "cell promotion forbidden")

    # OGA source is packaged and can be byte/dimension verified offline.
    oga_path = ROOT / "content/assets/oga_lpc/source/terrain/cliffs_grass_top/LPC_cliffs_grass.png"
    require(png_dimensions(oga_path) == (384, 288), "OGA source dimensions")
    require(
        sha256(oga_path) == "1a0c25904aaacf373c54311eecca9933a9b122e4c3cb2e4cfe8e19ab06feb82a",
        "OGA source hash",
    )
    oga = load("content/assets/oga_lpc/manifests/oga_lpc_cliff_recipe_catalog_v0_2.json")
    require(oga["sourceDimensions"] == [384, 288], "OGA catalog dimensions")
    require(oga["runtimeStatus"] == "quarantined", "OGA quarantine")
    require(oga["recipes"] == [], "OGA runtime recipes remain empty")
    require(oga["sourceGridPurpose"].startswith("32x32 source addressing"), "OGA source grid purpose")
    assemblies = {row["id"]: row for row in oga["sourceAssemblies"]}
    for required_id, required_span in {
        "grass_pillar": [5, 0, 3, 5],
        "cave_host": [0, 5, 3, 3],
        "ramp_crossing": [3, 5, 6, 4],
        "ladder": [9, 4, 1, 3],
        "rope_bridge_or_suspension": [10, 4, 2, 3],
    }.items():
        require(required_id in assemblies, f"OGA assembly {required_id}")
        row = assemblies[required_id]
        require(row["sourceGridSpan"] == required_span, f"OGA span {required_id}")
        require(row["sourceRectPx"] == grid_rect(required_span), f"OGA rect {required_id}")
        require(rect_in_bounds(row["sourceRectPx"], 384, 288), f"OGA bounds {required_id}")
        require(row["worldVisualFootprintTiles"] is None, f"OGA world footprint remains explicit/unset {required_id}")
        require(row["structuralHostMask"] is None, f"OGA host mask remains explicit/unset {required_id}")

    # Locked ElizaWy metadata must match the audited family authority without requiring the external mount.
    eliza = load("content/worldgen/elizawy_cliff_sheet_role_catalog_v0_1.json")
    require(eliza["revision"].startswith("167Z104"), "ElizaWy role-catalog revision")
    require(eliza["grid"]["independentCellPlacementAllowed"] is False, "ElizaWy cells non-placeable")
    require(eliza["reviewRegionPolicy"]["regionsAreRuntimeRecipes"] is False, "review windows are not recipes")
    windows = {row["id"]: row for row in eliza["normalizedAssemblyWindows"]}
    expected_windows = {
        "bare_rounded_plateau_template": [0, 0, 5, 5],
        "bare_square_plateau_template": [5, 0, 3, 5],
        "grass_rounded_plateau_template": [0, 5, 5, 4],
        "grass_square_plateau_template": [5, 5, 3, 4],
        "narrow_cave_host": [6, 9, 1, 3],
        "wide_cave_host": [7, 9, 3, 3],
        "ladder_column_a": [11, 9, 1, 3],
        "ladder_column_b": [13, 9, 1, 3],
    }
    for key, span in expected_windows.items():
        require(windows[key]["sourceGridSpan"] == span, f"ElizaWy window {key}")
        require(windows[key]["sourceRectPx"] == grid_rect(span), f"ElizaWy rect {key}")
        require(rect_in_bounds(windows[key]["sourceRectPx"], 512, 448), f"ElizaWy bounds {key}")
        require(windows[key]["worldVisualFootprintTiles"] is None, f"ElizaWy world footprint unset {key}")

    for source in [
        "Terrain/cliff_spring.png",
        "Terrain/cliff_summer.png",
        "Terrain/cliff_autumn.png",
        "Terrain/cliff_winter.png",
        "Terrain/cliff_winter_ice.png",
    ]:
        record = indexed_record(source)
        require([record["width"], record["height"]] == [512, 448], f"locked dimensions {source}")
        matching = next(row for row in eliza["seasonalSheets"] if row["sourcePath"] == source)
        require(record["sha256"] == matching["sha256"], f"locked hash {source}")
    require(eliza["geometryAudit"]["identicalAlphaGeometryAcrossSeasons"] is True, "season geometry parity")

    # Rocks, Cliffs is object art only.
    rock = load("content/assets/lpc/elizawy_rocks_cliffs_object_catalog_v0_1.json")
    require(rock["sourceDimensionsPx"] == [192, 128], "rock-object sheet dimensions")
    require(rock["structuralCliffProvider"] is False, "rock-object sheet not structural")
    require(len(rock["components"]) == 10, "rock-object connected component audit")
    record = indexed_record("Terrain/Rocks, Cliffs.png")
    require([record["width"], record["height"]] == [192, 128], "locked rock dimensions")
    require(record["sha256"] == rock["sha256"], "locked rock hash")

    family = load("content/assets/lpc/lpc_revised_terrain_family_authority_v0_1.json")
    structural = next(row for row in family["families"] if row["id"] == "structural_cliffs")
    rocks = next(row for row in family["families"] if row["id"] == "rocks")
    require("Terrain/Rocks, Cliffs.png" not in structural["sources"], "rocks removed from structural source family")
    require("Terrain/Rocks, Cliffs.png" in rocks["sources"], "rocks retained in object family")
    require(rocks["structuralCliffProvider"] is False, "rocks family structural false")

    brushes = load("content/editor/lpc_terrain_feature_brush_catalog_v0_1.json")
    cliff_brush = next(row for row in brushes["brushGroups"] if row["id"] == "levels_and_cliff_recipes")
    rock_brush = next(row for row in brushes["brushGroups"] if row["id"] == "rocks")
    require("Rocks, Cliffs.png" not in cliff_brush["sources"], "rocks removed from cliff brush")
    require("Rocks, Cliffs.png" in rock_brush["sources"], "rocks remain object brush")

    # Waterfall is multi-cell animation/connector source, not 1x1 terrain.
    waterfall = load("content/assets/lpc/elizawy_waterfall_connector_catalog_v0_1.json")
    require(waterfall["sourceDimensionsPx"] == [512, 608], "waterfall dimensions")
    require(waterfall["independentCellPlacementAllowed"] is False, "waterfall cells non-placeable")
    groups = waterfall["frameGroups"]
    south = [row for row in groups if row["visualRole"] == "south_facing_animated_frame"]
    west = [row for row in groups if row["visualRole"] == "west_facing_animated_frame"]
    east = [row for row in groups if row["visualRole"] == "east_facing_animated_frame"]
    require(len(south) == len(west) == len(east) == 4, "four audited frames per primary direction")
    require(all(row["sourceGridSpan"][2:] == [3, 5] for row in south), "south waterfall 3x5 frames")
    require(all(row["sourceGridSpan"][2:] == [2, 7] for row in west + east), "side waterfall 2x7 frames")
    record = indexed_record("Terrain/Waterfall.png")
    require([record["width"], record["height"]] == [512, 608], "locked waterfall dimensions")
    require(record["sha256"] == waterfall["sha256"], "locked waterfall hash")

    # Generic 32x32 slice catalog may expose addresses, but cannot imply independent placement.
    slices = load("content/assets/lpc/lpc_slice_catalog_v0_1.json")
    by_name = {row["displayName"]: row for row in slices["sheets"]}
    for name in [
        "Terrain/cliff_spring",
        "Terrain/cliff_summer",
        "Terrain/cliff_autumn",
        "Terrain/cliff_winter",
        "Terrain/cliff_winter_ice",
    ]:
        row = by_name[name]
        require(row["independentCellPlacementAllowed"] is False, f"slice catalog cliff placement {name}")
        require(row["modularUse"] == "multi_cell_structural_recipe_required", f"slice catalog cliff use {name}")
    require(by_name["Terrain/Rocks, Cliffs"]["structuralCliffProvider"] is False, "slice catalog rock classification")
    require(by_name["Terrain/Waterfall"]["modularUse"] == "animated_multi_cell_connector_recipe_required", "slice waterfall classification")

    workflow = load("content/editor/pixel_studio_cliff_workflow_v0_2.json")
    require(workflow["revision"].startswith("167Z104"), "Pixel Studio workflow revision")
    require(workflow["documentSetup"]["canvasModel"]["sourcePixelsMutable"] is False, "source canvas read-only")
    require(workflow["documentSetup"]["canvasModel"]["sourceSelectionDoesNotDefineWorldFootprint"] is True, "selection/footprint separation")
    providers = {row["id"]: row["state"] for row in workflow["currentProviders"]}
    require(providers["oga_lpc_grass_top_cliffs"].startswith("quarantined"), "Pixel Studio OGA quarantine")

    collision = load("content/worldgen/structural_collision_cliff_assembly_authority_v0_1.json")
    require(collision["activeVisualProvider"]["sourceDimensions"] == [384, 288], "stale 250x188 dimensions removed")
    require(collision["activeVisualProvider"]["sourceGridCellIsWorldFootprint"] is False, "collision authority footprint separation")
    require(collision["collisionPolicy"]["proceduralCollisionEnabled"] is False, "procedural collision remains disabled")

    runtime_draw = read("crates/haven_game/src/runtime_structural_cliff_draw.rs")
    z106 = ROOT / "content/worldgen/elizawy_cliff_runtime_preview_certification_v0_1.json"
    if z106.is_file():
        preview = load("content/worldgen/elizawy_cliff_runtime_preview_certification_v0_1.json")
        require(preview["pass"] == "167Z106", "Z106 preview pass")
        require(preview["runtimeGate"]["collision"] == "fail_open", "Z106 collision remains fail-open")
        require("SOUTH_FACE_SOURCE" in runtime_draw and "draw_texture_ex" in runtime_draw, "certified ElizaWy preview supersedes renderer quarantine")
    else:
        require("pub(super) fn draw_structural_cliffs(&self) {}" in runtime_draw, "runtime renderer remains quarantined")

    generator = read("tools/automation/assets/Promote-LpcRuntimeAssets.py")
    require('name.startswith("cliff_")' in generator, "promotion generator cliff classification")
    require('name in {"rocks, grasslands.png", "rocks, cliffs.png"}' in generator, "promotion generator rock classification")
    require("def independent_cell_placement_allowed" in generator, "promotion generator placement rule")

    for doc in [
        "docs/audits/HAVENWILD_CLIFF_ASSET_FOOTPRINT_RECIPE_AUDIT_PASS167Z104.md",
        "docs/archive/pass_history/PASS167Z104_CLIFF_ASSET_FOOTPRINT_AND_RECIPE_NORMALIZATION.md",
    ]:
        require((ROOT / doc).is_file(), f"documentation {doc}")

    print("Pass167Z104 cliff asset footprint and recipe normalization validation passed")


if __name__ == "__main__":
    main()
