#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
required = {
    "apps/haven_editor_native/src/app/world_canvas_context.rs": [
        "Generate this island",
        "Generate all islands",
        "Open assigned scene",
    ],
    "apps/haven_editor_native/src/app/island_authoring.rs": [
        "open_world_canvas_context_menu",
        "generate_selected_landmass",
        "generate_all_landmasses",
        "connect_generated_island_harbor",
        "restore_generated_harbor_routes",
    ],
    "crates/haven_world/src/island_pcg.rs": [
        "pub fn generate_landmass",
        "populate_scene_from_coastline",
        "generate_coastline_raster",
        "add_adjacent_scene_transitions",
        "land_cells",
        "harbor_rectangle_id",
    ],
    "crates/haven_world/src/region_graph.rs": [
        "IslandHarbor",
        "SeaRoute",
        "connect_generated_island_harbor",
    ],
    "apps/haven_editor_native/src/app/editor_menu.rs": [
        "save_all_editor_documents",
        "save_world_to_path",
        "EDITOR_WORLD_SAVE_PATH",
        "Export Island PNGs",
    ],
    "tools/build/Build.ps1": [
        "Build-ApplicationBinaries",
        "Build/HavenwildClient",
        '"client" { Build-ClientBinary }',
    ],
    "tools/build/Build.sh": [
        "build_apps",
        "Build/HavenwildClient/HavenwildClient.exe",
        "client) build_client",
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

contract_path = ROOT / "content/editor/world_canvas/island_context_pcg_harbor_contract_v0_1.json"
contract = json.loads(contract_path.read_text(encoding="utf-8"))
if not contract["requirements"]["proceduralIsland"]["multiScene"]:
    raise SystemExit("contract must require multi-scene islands")
if contract["requirements"]["regionGraph"]["linkKind"] != "sea_route":
    raise SystemExit("contract must require sea_route harbor links")
print("World canvas island PCG / harbor routing validation passed.")
