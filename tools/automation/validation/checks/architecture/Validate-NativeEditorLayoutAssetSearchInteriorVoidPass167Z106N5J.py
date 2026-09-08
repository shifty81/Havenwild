#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def fail(message: str) -> None:
    raise SystemExit(f"N5J native-editor layout/search/interior-void validation FAILED: {message}")


def read(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        fail(f"missing required source: {relative}")
    return path.read_text(encoding="utf-8")


def require(text: str, fragment: str, label: str) -> None:
    if fragment not in text:
        fail(label)


def main() -> None:
    scene_world = read("crates/haven_core/src/foundation/scene_world.rs")
    require(scene_world, "SceneKind::Interior => TileKind::Wall", "interior blank scenes must use wall-backed void authority")
    require(scene_world, "SceneKind::Cave => TileKind::CaveWall", "cave blank scenes must use cave-wall-backed void authority")
    scene_visual = read("crates/haven_core/src/foundation/scene_visual_bounds.rs")
    require(scene_visual, "pub fn is_renderable_cell", "SceneMap must expose renderable-cell culling")
    require(scene_visual, "pub fn renderable_bounds", "SceneMap must expose renderable bounds")

    runtime_draw = read("crates/haven_game/src/runtime_draw.rs")
    require(runtime_draw, "self.world.active().kind == SceneKind::Exterior", "runtime background must distinguish exterior from enclosed scenes")
    require(runtime_draw, "BLACK", "interior/cave runtime background must clear to void black")
    runtime_terrain = read("crates/haven_game/src/runtime_terrain_pass.rs")
    require(runtime_terrain, "if !scene.is_renderable_cell(x, y)", "runtime cell terrain pass must cull interior void")
    surface = read("crates/haven_game/src/terrain_scene_surface.rs")
    if surface.count("if !scene.is_renderable_cell(x, y)") < 2:
        fail("retained terrain surface must skip void in base and overlay lanes")

    scene_draw = read("apps/haven_editor_native/src/app/draw_scene_views.rs")
    require(scene_draw, "scene.kind == SceneKind::Exterior", "Scene Editor infinite grid must be exterior-only")
    require(scene_draw, "draw_scene_grid_overlay(scene, self.scene_canvas.zoom)", "Scene Editor grid must use renderable scene bounds")
    scene_helpers = read("apps/haven_editor_native/src/app/scene_render_helpers.rs")
    require(scene_helpers, "pub(crate) fn draw_scene_grid_overlay(scene: &SceneMap", "bounded Scene Editor grid helper missing")
    require(scene_helpers, "scene.renderable_bounds()", "Scene Editor must clip grid/border to renderable bounds")

    editor_types = read("apps/haven_editor_native/src/app/editor_types.rs")
    require(editor_types, "PixelLibraryFilter", "Pixel Assets search focus is missing")
    pixel_state = read("apps/haven_editor_native/src/app/pixel_studio.rs")
    require(pixel_state, "pub library_filter: String", "Pixel Assets search state is missing")
    require(pixel_state, "filtered_library_indices", "Pixel Assets filtered list authority is missing")
    pixel_layout = read("apps/haven_editor_native/src/app/pixel_studio_layout.rs")
    require(pixel_layout, "pixel_library_search_rect", "Pixel Assets compact search geometry is missing")
    require(pixel_layout, "PixelLibraryVisualRow", "Pixel Assets grouped list rows are missing")
    require(pixel_layout, '"Recent"', "Pixel Assets must expose a Recent group")
    pixel_panel = read("apps/haven_editor_native/src/app/pixel_library_panel.rs")
    require(pixel_panel, '"Pixel Assets"', "Pixel Assets list header is missing")
    require(pixel_panel, "PixelLibraryVisualRow::Group", "Pixel Assets groups are not rendered")
    require(pixel_panel, "draw_list_row", "Pixel Assets entries must use normalized list rows")
    require(pixel_panel, "pixel_library_clear_rect", "Pixel Assets compact search clear control is not interactive")
    require(pixel_panel, "filtered_library_indices().len()", "Pixel Assets wheel navigation must respect the active filter")

    palette = read("apps/haven_editor_native/src/app/asset_palette_panel.rs")
    require(palette, "asset_search_clear_rect", "Scene Assets compact search clear control is missing")
    require(palette, "draw_editor_widget_tone", "Scene Assets search must use quiet compact styling")
    require(palette, "draw_list_row(card", "Scene Assets must use list rows instead of loose card grid")
    if "const ASSET_PAGE_SIZE: usize = 4;" not in palette:
        fail("Scene Assets result list must stay within the normalized right-panel vertical budget")

    library = read("apps/haven_editor_native/src/app/asset_library_panel.rs")
    require(library, "library_search_clear_rect", "Content Library compact search clear control is missing")
    require(library, '"Search library..."', "Content Library compact search placeholder is missing")
    require(library, "draw_list_row(card", "Content Library must use compact list rows")

    world_ui = read("apps/haven_editor_native/src/app/world_surface_authoring_ui.rs")
    for heading in ("Authoring Layer", "Global Tool", "Transaction Actions"):
        require(world_ui, f'"{heading}"', f"world inspector section {heading!r} is missing")
    require(world_ui, "let active_brush_label = self.world_active_brush_label();", "world inspector must keep brush label in stable layout-owned storage")

    island = read("apps/haven_editor_native/src/app/island_workspace.rs")
    require(island, '"Islands"', "left island list section header is missing")
    require(island, "draw_list_row(row", "left island list must use normalized list rows")

    tests = read("crates/haven_core/src/foundation/foundation_tests.rs")
    require(tests, "interior_visual_mask_keeps_room_and_hides_unused_backing_grid", "interior void regression test is missing")
    require(tests, "exterior_visual_mask_keeps_complete_storage_grid", "exterior full-grid regression test is missing")

    print("N5J native editor layout, compact search, grouped asset lists, and interior void rendering validated")


if __name__ == "__main__":
    main()
