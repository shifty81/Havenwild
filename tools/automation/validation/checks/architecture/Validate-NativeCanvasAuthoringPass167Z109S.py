#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def line_count(rel: str) -> int:
    return len(text(rel).splitlines())


def main() -> int:
    # Carry Q repository gates and R world/terrain bridge forward while S becomes
    # the single current normalization validator in the 10-check source profile.
    domain = load("content/architecture/master_domain_registry_v0_1.json")
    require(domain["revision"].startswith("167Z109S"), "master domain registry is not S authority")
    require(domain["policy"]["domainCount"] == 7, "normalization must stay at seven project foundations")
    require(len(domain["domains"]) == 7, "domain registry count drifted")
    require(domain["policy"]["noFeatureSpecificFrameworks"] is True, "scope guard regressed")
    authoring = next(item for item in domain["domains"] if item["id"] == "authoring")
    require("canvas_coordinate_transform" in authoring["owns"], "authoring domain does not own canvas transform")
    require("visible_region_queries" in authoring["owns"], "authoring domain does not own visible-region queries")

    current = ROOT / "docs/current"
    expected = {
        "README.md", "CURRENT_SOURCE_HANDOFF.md", "ROADMAP.md", "DEVELOPMENT_LAYOUT.md",
        "ROOT_LAYOUT.md", "SOURCE_ONLY_BOOTSTRAP.md", "SOURCE_PACKAGING.md", "VALIDATION_ARCHITECTURE.md",
    }
    require({p.name for p in current.iterdir() if p.is_file()} == expected, "docs/current must contain exactly eight current-state documents")
    require(not list(current.glob("PASS*.md")), "historical pass documents returned to docs/current")

    for retired in [
        "content/animation", "content/packs", "web/editor",
        "content/build/validator_registry_v2.json", "content/build/generated_output_registry_v1.json",
    ]:
        require(not (ROOT / retired).exists(), f"retired path still active: {retired}")

    # Keep the R bridge present. S must not replace terrain authority while
    # normalizing the editor canvas.
    bridge = load("content/architecture/world_terrain_authority_bridge_v0_1.json")
    require(bridge["revision"].startswith("167Z109R"), "R world/terrain bridge unexpectedly changed")
    require(bridge["behaviorPreserving"] is True, "R world/terrain bridge parity contract regressed")
    require((ROOT / "crates/haven_world/src/terrain_runtime_recipe.rs").is_file(), "SurfaceTerrainRecipeV1 source missing")

    canvas_contract = load("content/architecture/native_canvas_authoring_authority_v0_1.json")
    require(canvas_contract["revision"].startswith("167Z109S"), "native canvas contract is not S authority")
    require(canvas_contract["behaviorPreserving"] is True, "S must remain behavior preserving")
    compatibility = canvas_contract["compatibility"]
    for key in [
        "gameVisualsUnchanged", "terrainProvidersUnchanged", "worldSeedsUnchanged",
        "saveSchemaUnchanged", "editorWorkspaceLayoutSchemaUnchanged", "f3RuntimeBehaviorUnchanged",
    ]:
        require(compatibility[key] is True, f"S compatibility guarantee missing: {key}")

    authoring_lib = text("crates/haven_authoring/src/lib.rs")
    canvas = text("crates/haven_authoring/src/canvas.rs")
    require("pub mod canvas;" in authoring_lib, "shared canvas module is not exported")
    for token in [
        "pub struct AuthoringCanvasTransform",
        "pub struct CanvasPoint",
        "pub struct CanvasRect",
        "pub fn screen_to_world",
        "pub fn world_to_screen",
        "pub fn screen_to_grid_cell",
        "pub fn visible_grid_bounds",
        "pub fn visible_grid_bounds_in_world",
    ]:
        require(token in canvas, f"shared canvas authority token missing: {token}")
    require(line_count("crates/haven_authoring/src/canvas.rs") <= 320, "shared canvas authority became oversized")

    editor_lib = text("crates/haven_editor/src/lib.rs")
    require("AuthoringCanvasTransform" in editor_lib, "haven_editor compatibility surface does not re-export canvas transform")
    require("EditorSelection" in editor_lib and "EditorCommandBus" in editor_lib, "shared selection/command compatibility re-export regressed")

    camera = text("apps/haven_editor_native/src/app/canvas_camera.rs")
    require("AuthoringCanvasTransform" in camera, "native camera does not use shared canvas transform")
    require("fn authoring_transform" in camera, "native canvas adapter missing")
    require("fn display_rect" not in camera, "duplicate native display-rect transform remains")
    require("camera.screen_to_world" not in camera, "native pan/hit testing still bypasses shared transform")
    require("screen_to_grid_cell" in camera, "native grid-pick adapter missing")
    require("visible_grid_bounds" in camera, "native visible-grid adapter missing")

    world_authoring = text("apps/haven_editor_native/src/app/world_surface_authoring.rs")
    scene_views = text("apps/haven_editor_native/src/app/draw_scene_views.rs")
    world_preview = text("apps/haven_editor_native/src/app/world_surface_editor.rs")
    scene_render = text("apps/haven_editor_native/src/app/scene_render_helpers.rs")
    require("screen_to_grid_cell(viewport, bounds, mouse, 1.0)" in world_authoring, "world tile picking bypasses shared grid transform")
    require("screen_to_grid_cell(viewport, self.scene_canvas_bounds(), mouse, 1.0)" in scene_views, "scene tile picking bypasses shared grid transform")
    require("visible_grid_bounds_in_world" in world_preview, "world preview local clipping bypasses shared visible-grid query")
    require("visible_cells" in scene_render, "scene renderer does not receive a visible-cell window")
    require("for y in visible_cells.min.y..=visible_cells.max.y" in scene_render, "scene terrain/zone loops are not visibly bounded")

    shell = text("apps/haven_editor_native/src/app/ui_shell.rs")
    require("Never pretend the window is larger than the actual drawable area" in shell, "responsive shell regression: fake minimum drawable area returned")
    require("MIN_CANVAS_W" in shell, "canvas-priority panel compression contract missing")
    require("bottom_dock_overlays_without_resizing_center_canvas" in shell, "bottom dock canvas-stability test missing")

    registry = load("content/build/validator_registry_v3.json")
    source = [entry for entry in registry["validators"] if "source" in entry.get("profiles", [])]
    require(len(source) == 10, f"source validation profile must remain 10 current-authority checks, got {len(source)}")
    current_ids = {entry["id"] for entry in source}
    require("architecture.native-canvas-authoring-v167z109s" in current_ids, "S validator is not current source authority")
    require("architecture.world-terrain-authority-bridge-v167z109r" not in current_ids, "R validator should move to full historical/subsystem certification")

    diagnostic = text("crates/haven_game/src/runtime_diagnostics.rs")
    require("Pass 167Z109S" in diagnostic, "runtime diagnostic checkpoint not advanced to S")

    print("Pass167Z109S native canvas/shared authoring normalization validated")
    print("- seven-domain scope guard preserved")
    print("- R world/terrain bridge preserved")
    print("- one shared positive-Y screen/world/grid transform")
    print("- scene/world visible-cell queries share headless clipping")
    print("- shared EditorSelection/EditorCommandBus authority retained")
    print("- responsive canvas-priority shell retained")
    print("- game/save/provider/F3 behavior remains parity-targeted")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Pass167Z109S validation FAILED: {exc}")
        raise SystemExit(1)
