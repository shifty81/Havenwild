#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
required = {
    "crates/haven_world/src/island_pcg.rs": [
        "occupied_scene_cells",
        "moved_scene_cell_assemblies_grow_coast_against_empty_grid_slots",
    ],
    "crates/haven_world/src/island_coastline.rs": [
        "assembly_edge_penalty",
        "occupied_scene_cells",
        "missing_scene_slot_is_treated_as_open_water",
    ],
    "crates/haven_world/src/scene_rectangles.rs": [
        "impl SceneRectangleManifest",
        "pub fn save_to_path(&self, path: &str)",
    ],
    "crates/haven_world/src/harbor_routes.rs": [
        "HarborRouteCatalog",
        "HARBOR_ROUTE_CATALOG_PATH",
        "pub fn connect",
        "harbor_route_pairs_are_unique_and_order_independent",
    ],
    "apps/haven_editor_native/src/app/island_workspace.rs": [
        "move_selected_scene_cell",
        "Begin Route Here",
        "Connect Route to Selected",
        "apply_custom_harbor_routes",
        "Save All persists the island assembly",
    ],
    "apps/haven_editor_native/src/app/editor_menu.rs": [
        "manifest.save_to_path(SCENE_RECTANGLE_MANIFEST_PATH)",
        "self.harbor_routes.save_to_path(HARBOR_ROUTE_CATALOG_PATH)",
        "export_island_preview_pngs",
        "archipelago.png",
        "draw_preview_line",
    ],
    "apps/haven_editor_native/src/app/input.rs": [
        "KeyCode::F5",
        "move_selected_scene_cell(-1, 0)",
        "let base_y = rect.y + 416.0",
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

contract = json.loads(
    (ROOT / "content/editor/world_canvas/structural_archipelago_workspace_contract_v0_1.json")
    .read_text(encoding="utf-8")
)
accounting = contract["scene_accounting"]
if accounting["generated_exterior_scene_cells"] != 63:
    raise SystemExit("structural archipelago contract must retain 63 exterior scene cells")
if accounting["expected_world_scene_total_after_generation"] != 72:
    raise SystemExit("structural archipelago contract must retain the 72-scene total")


archipelago_preview = ROOT / "content/worldgen/island_previews/archipelago.png"
if not archipelago_preview.exists() or archipelago_preview.stat().st_size == 0:
    raise SystemExit("assembled archipelago PNG preview is missing")

routes = json.loads(
    (ROOT / "content/worldgen/harbor_routes_v0_1.json").read_text(encoding="utf-8")
)
if routes.get("schema") != "havenwild.harbor_routes.v001":
    raise SystemExit("harbor route catalog schema is incorrect")

print("Island assembly, Save All, and harbor-route validation passed.")
