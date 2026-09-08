#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
required = {
    "crates/haven_world/src/island_pcg.rs": [
        "generate_coastline_raster",
        "populate_scene_from_coastline",
        "land_cells",
        "mountain_cells,",
        "every_manifest_landmass_generates_as_one_scene_cell_assembly",
    ],
    "crates/haven_world/src/island_coastline.rs": [
        "organic_island_field",
        "smooth_noise",
        "assembly_edge_penalty",
        "distance_from_sources",
        "TileKind::Grass",
        "TileKind::Sand",
        "TileKind::OceanShallow",
    ],
    "apps/haven_editor_native/src/app/island_workspace.rs": [
        "draw_world_routes_workspace",
        "draw_landmass_list",
        "select_landmass",
        "handle_world_routes_click",
        "Refresh Harbor Node",
        "Reroll Archipelago Seed",
    ],
    "apps/haven_editor_native/src/app/editor_menu.rs": [
        "EditorMenuKind",
        '"File"',
        '"Edit"',
        '"View"',
        '"Help"',
        '"Save All"',
        "export_island_preview_pngs",
        "content/worldgen/island_previews",
    ],
    "apps/haven_editor_native/src/app/world_surface_editor.rs": [
        "options.selected_landmass_id",
        "world_scene_grid_bounds_for_landmass",
        "ProjectSceneId::new(assignment.scene_code.as_str())",
        "No global world-surface data available",
    ],
}

for rel, markers in required.items():
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f"missing required file: {rel}")
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            raise SystemExit(f"{rel} missing marker: {marker}")

manifest = json.loads((ROOT / "content/worldgen/scene_rectangle_manifest_v0_8.json").read_text(encoding="utf-8"))
standard = [entry for entry in manifest["scene_rectangles"] if entry.get("grid_x") is not None and entry.get("grid_y") is not None]
landmasses = {entry["landmass_id"] for entry in standard}
if len(standard) != 63:
    raise SystemExit(f"expected 63 exterior scene cells, found {len(standard)}")
if len(landmasses) != 10:
    raise SystemExit(f"expected 10 island landmasses, found {len(landmasses)}")
print("Structural archipelago / island workspace validation passed with promoted mountain terrain.")
