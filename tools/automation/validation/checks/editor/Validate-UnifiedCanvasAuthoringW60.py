#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
errors: list[str] = []

def require_file(rel: str) -> Path:
    path = ROOT / rel
    if not path.is_file():
        errors.append(f"missing required file: {rel}")
    return path

def text(rel: str) -> str:
    path = require_file(rel)
    return path.read_text(encoding="utf-8") if path.is_file() else ""

def data(rel: str):
    path = require_file(rel)
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"invalid json {rel}: {exc}")
        return {}

def contains(rel: str, *needles: str) -> None:
    value = text(rel)
    for needle in needles:
        if needle not in value:
            errors.append(f"{rel} missing marker: {needle}")

# W57K10A: one UI/font lifetime and material reset.
contains(
    "apps/haven_editor_native/src/app/editor_text.rs",
    "editor_font_ready()",
    "gl_use_default_material();",
)
mod = text("apps/haven_editor_native/src/app/mod.rs")
if mod.count("initialize_editor_font()") != 1:
    errors.append("native editor bootstrap must initialize the editor font exactly once")
contains(
    "apps/haven_editor_native/src/app/mod.rs",
    "draw_bootstrap_screen",
    "Preparing editor font atlas",
    "Finalizing workspace",
    "STARTUP COMPLETE editor interactive",
    "mod canvas_tool_rack;",
    "mod canvas_layers;",
    "mod tool_registry;",
    "mod authoring_changeset;",
)
menu = text("apps/haven_editor_native/src/app/editor_menu.rs")
if "initialize_editor_font()" in menu:
    errors.append("editor menu/dev-client lifecycle must not rebuild the font atlas")

# W58: non-destructive defaults, shared rack, shared layer rail.
contains(
    "apps/haven_editor_native/src/app/canvas_tool_rack.rs",
    "Tool selected:",
    "activate_universal_tool",
    "UniversalTool::Collision",
)
contains(
    "apps/haven_editor_native/src/app/canvas_layers.rs",
    "Visual Overrides",
    "CanvasLayerKind::AuthoredPixels",
    "Collision",
    "Terrain Transitions",
    "Source Reference",
)
contains(
    "apps/haven_editor_native/src/app/draw.rs",
    "draw_canvas_tool_rack",
    "draw_canvas_layer_rail",
)
contains(
    "apps/haven_editor_native/src/app/input.rs",
    "handle_canvas_tool_rack_click",
    "handle_canvas_layer_rail_click",
)
contains("apps/haven_editor_native/src/app/mod.rs", "scene_edit_tool: SceneEditTool::Select")
contains("apps/haven_editor_native/src/app/pixel_studio.rs", "tool: PixelTool::Selection")

# W58A/B/C: explicit authoring scopes, versioned junctions and precision collision.
contains(
    "apps/haven_editor_native/src/app/scene_asset_context.rs",
    "Edit asset source (shared)",
    "Edit this cell / instance variant",
    "Edit selected region in Pixel Studio",
    "Edit building composite in Pixel Studio",
    "Edit entire scene chunk in Pixel Studio",
)
contains(
    "apps/haven_editor_native/src/app/world_asset_pixel_bridge.rs",
    "Collision Mask [8px default / 1px precision]",
    '"authoringResolutionPx": 1',
    '"defaultSnapPx": 8',
    '"allowedSnapPx": [32,16,8,4,2,1]',
    "authored_junction_variants_v1.json",
    '"pcgEligible": false',
    "record_authoring_change",
)
junctions = data("content/terrain/authored_junction_variants_v1.json")
if junctions.get("schema") != "havenwild.authored_junction_variants.v1":
    errors.append("authored junction registry schema mismatch")

# W59: deterministic changeset packaging.
contains(
    "apps/haven_editor_native/src/app/authoring_changeset.rs",
    "havenwild.authoring_changeset.v1",
    'format!("v{next:03}")',
)
contains("tools/control/ProjectCommandRegistry.ps1", "Package authoring changes", "PackageAuthoringChanges.ps1")
require_file("tools/control/PackageAuthoringChanges.ps1")

# W60: split overworld + yarn-board route surface.
contains(
    "apps/haven_editor_native/src/app/island_workspace.rs",
    "Scene Route Board",
    "map + yarn-board links",
    "Overworld / spatial map",
    "draw_route_scene_board",
)

# K10/K11 house typology and edge continuity.
starter = data("content/buildings/recipes/estate_starter_cottage_v1.json")
if starter.get("version") != "1.6.0-w57k10":
    errors.append("starter cottage is not on W57K10 certification version")
wall_ids = {entry.get("id") for entry in starter.get("levels", [{}])[0].get("wallRuns", [])}
for wall_id in ("gable_fill_base_left", "gable_fill_base", "gable_fill_base_right"):
    if wall_id not in wall_ids:
        errors.append(f"starter cottage missing {wall_id}")

two = data("content/buildings/recipes/estate_two_story_house_upgrade_v1.json")
if two.get("id") != "havenwild.estate.house_two_story_upgrade":
    errors.append("two-story Estate upgrade recipe missing")
if len(two.get("levels", [])) != 2:
    errors.append("two-story Estate upgrade must contain two structural levels")
if not two.get("connectors"):
    errors.append("two-story Estate upgrade must contain a stair connector")

catalog = data("content/buildings/building_recipe_catalog_v1.json")
if not any(entry.get("id") == "havenwild.estate.house_two_story_upgrade" for entry in catalog.get("entries", [])):
    errors.append("two-story Estate upgrade is absent from BuildingRecipe catalog")

# Contract files keep this batch normalized and portable toward Open2D/Cortex.
for rel in [
    "content/editor/native_editor_ui_authority_w57k10a_v1.json",
    "content/editor/canvas/universal_canvas_layer_tool_authority_w58_v1.json",
    "content/editor/pixel_editor/selection_junction_collision_authoring_w58abc_v1.json",
    "content/editor/authoring/authoring_changeset_authority_w59_v1.json",
    "content/editor/world_canvas/world_route_graph_board_w60_v1.json",
    "docs/current/HAVENWILD_W60_UNIFIED_AUTHORING_AUTHORITY.md",
]:
    require_file(rel)

if errors:
    print("FAIL: W57K10A-W60 unified authoring authority")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)
print("PASS: W57K10A-W60 unified authoring authority")
