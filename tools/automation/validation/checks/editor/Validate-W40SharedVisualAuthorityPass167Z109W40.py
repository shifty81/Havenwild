#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def req(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8-sig")


def main() -> int:
    render_cargo = text("crates/haven_render/Cargo.toml")
    render_lib = text("crates/haven_render/src/lib.rs")
    shared_cliff = text("crates/haven_render/src/structural_cliff_visual.rs")
    cliff_compat = text("crates/haven_game/src/runtime_structural_cliff_shapes.rs")
    runtime_cliff = text("crates/haven_game/src/runtime_structural_cliff_draw.rs")
    terrain_pass = text("crates/haven_game/src/runtime_terrain_pass.rs")
    runtime_draw = text("crates/haven_game/src/runtime_draw.rs")
    continuous_surface = text("crates/haven_world/src/continuous_surface.rs")
    continuous_surface_tests = text("crates/haven_world/src/continuous_surface_tests.rs")
    editor_atlas = text("apps/haven_editor_native/src/app/atlas_render.rs")
    editor_scene = text("apps/haven_editor_native/src/app/scene_render_helpers.rs")
    editor_views = text("apps/haven_editor_native/src/app/draw_scene_views.rs")
    editor_cache = text("apps/haven_editor_native/src/app/structural_cliff_preview.rs")

    req('haven_world = { path = "../haven_world" }' in render_cargo,
        "haven_render must depend on canonical haven_world structural semantics")
    req("pub mod structural_cliff_visual;" in render_lib,
        "shared structural cliff module is not exported")
    req("pub struct CliffVisualRecipeV1" in shared_cliff,
        "shared cliff visual recipe missing")
    req("pub fn resolve_cliff_visual_recipe_v1" in shared_cliff,
        "shared cliff visual resolver missing")
    req("authored_face_segments_for_edge" in shared_cliff,
        "edge-specific uniform-height resolution did not move into shared authority")
    req("pub(super) use haven_render::structural_cliff_visual::*;" in cliff_compat,
        "runtime compatibility surface is not routed through haven_render")
    req("resolve_cliff_visual_recipe_v1(center" in runtime_cliff,
        "runtime cliff renderer is not consuming the shared recipe")
    req("resolve_cliff_visual_recipe_v1(center" in editor_atlas,
        "native editor cliff renderer is not consuming the shared recipe")
    req("draw_structural_cliffs(" in editor_atlas and "structural_cliff_bridge" in editor_views,
        "native editor structural cliff preview path is not wired")
    req("resolve_tavern_map_elevation_cliffs_v2" in editor_cache,
        "editor structural cache does not use canonical cliff bridge")
    req("editor_bridge_feeds_the_shared_visual_recipe" in editor_cache,
        "editor/shared cliff certification test missing")

    req("pub fn object_foot_world" in render_lib and "pub fn stamp_foot_world" in render_lib,
        "shared placeable bottom-center root helpers missing")
    req("collision_rect()" in render_lib and "interaction_rect()" in render_lib,
        "shared roots must derive from collision first and interaction second")
    req("object_foot_tiles(*object)" in editor_atlas,
        "native editor object atlas placement does not use canonical object foot")
    req("commands.sort_by" in editor_scene and "stamp.sort_y()" in editor_scene
        and "object.sort_y()" in editor_scene,
        "native editor placeables are not depth sorted from authored sort points")
    req("stamp_foot_tiles" in editor_scene and "object_foot_tiles" in editor_scene,
        "native editor canonical foot diagnostics missing")

    # W39 regression guards. Authored exteriors must remain SceneMap authority;
    # only generated chunk/PCG IDs enter the continuous renderer.
    req("parse_generated_chunk_scene_id(active_scene_id).is_some()" in terrain_pass
        and "parse_pcg_surface_scene_id(active_scene_id).is_some()" in terrain_pass,
        "W39 terrain dispatch guard missing")
    req("SceneKind::Exterior && generated_surface" in terrain_pass,
        "authored exterior terrain may be forced back through continuous rendering")
    req("SceneKind::Exterior && generated_surface" in runtime_draw,
        "authored exterior actor dispatch may be forced back through continuous rendering")
    req("let Some(active_region) = active_pcg_region.as_deref() else" in continuous_surface,
        "dormant PCG partitions can replace authored exterior chunk bindings")
    req("dormant_pcg_partition_cannot_replace_active_legacy_farmstead_chunk" in continuous_surface_tests,
        "W39 Farmstead/PCG manifest regression test missing")
    req("pixel_snapped_screen_origin" in runtime_cliff,
        "W39 structural cliff pixel-snap seam correction was lost")

    print("Pass167Z109W40 shared visual authority checkpoint validated")
    print("- shared cliff recipe is consumed by runtime and native editor")
    print("- canonical bottom-center roots and editor depth sorting are present")
    print("- W39 authored-exterior and dormant-PCG guards are preserved")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Pass167Z109W40 validation FAILED: {exc}")
        raise SystemExit(1)
