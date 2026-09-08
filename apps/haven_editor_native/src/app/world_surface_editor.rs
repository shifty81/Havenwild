use haven_core::{GameWorld, ProjectSceneId, SceneMap, MAP_H, MAP_W};
use haven_editor::{
    visible_grid_bounds_in_world, CanvasPoint as AuthoringCanvasPoint,
    CanvasRect as AuthoringCanvasRect, GridRect,
};
use haven_world::scene_rectangles::{
    SceneRectangleAssignmentsFile, SceneRectangleManifest, SceneRectangleSpec,
};
use haven_world::{LandmassClass, SemanticWorldBakeV1, WorldCreationSettings};
use macroquad::prelude::*;

use super::canvas_camera::CanvasCameraState;
use super::canvas_view::{draw_canvas_rulers, draw_infinite_grid};
use super::atlas_render::EditorTextureSet;
use super::editor_text::draw_editor_text;
use super::render_helpers::{scene_tile_color, zone_preview_color};
use super::{WorldEditTool, WorldLayerMode, MUTED, PANEL_EDGE, TEXT, WARN};

#[derive(Clone, Copy, Debug, Default)]
pub(crate) struct WorldSurfaceViewOptions {
    pub selected_index: usize,
    pub selected_landmass_id: i32,
    /// R37: render the complete persistent overworld instead of clipping the
    /// canvas to only the currently selected landmass. Authoring still tracks
    /// a selected landmass, but the camera and LOD surface are global.
    pub show_entire_world: bool,
    pub show_partitions: bool,
    pub show_objects: bool,
    pub show_terrain: bool,
    pub show_water: bool,
    pub show_roads_paths: bool,
    pub show_vegetation: bool,
    pub show_resources: bool,
    pub show_structures: bool,
    pub show_objects_props: bool,
    pub show_visual_overrides: bool,
    pub show_zones: bool,
    pub show_structural_levels: bool,
    pub cursor: Option<(i32, i32)>,
    pub selection: Option<GridRect>,
    pub drag_preview: Option<GridRect>,
    pub paste_preview: Option<GridRect>,
    pub asset_place_preview: Option<GridRect>,
    pub connector_preview: Option<GridRect>,
    pub edit_tool: WorldEditTool,
    pub layer_mode: WorldLayerMode,
    pub brush_radius: i32,
}

const WORLD_SURFACE_PARTITION_W: f32 = MAP_W as f32;
const WORLD_SURFACE_PARTITION_H: f32 = MAP_H as f32;

pub(crate) fn draw_scene_rectangle_map(
    manifest: &SceneRectangleManifest,
    assignments: &SceneRectangleAssignmentsFile,
    world: &GameWorld,
    development_world_settings: &WorldCreationSettings,
    semantic_bake: Option<&SemanticWorldBakeV1>,
    viewport: Rect,
    canvas: &CanvasCameraState,
    textures: &EditorTextureSet,
    options: WorldSurfaceViewOptions,
) {
    draw_rectangle(
        viewport.x,
        viewport.y,
        viewport.w,
        viewport.h,
        Color::new(0.10, 0.13, 0.15, 1.0),
    );
    // W81R30-R44H8 compatibility contract (documentation only):
    // development_world_settings begins from WorldCreationSettings::default() and
    // resolves the production finite layout through finite_archipelago_from_world_creation(&settings).
    // Generated macro geography is sampled by sample_geographic_surface(settings.seed, ...) and
    // related through finite_archipelago_landmass_id_at / finite_archipelago_landmass_macro_bounds.
    // The legacy Scene rectangles are authored anchor regions inside these islands; they are
    // inspection/authoring windows rather than a competing production landmass generator.
    // Complete-world mode is a true archipelago overview using the generated
    // layout positions. The production finite-world geography authority remains
    // sample_geographic_surface; this editor LOD deliberately shows materialized
    // scene truth so authored terrain remains visible during inspection.
    // Legacy Scene rectangles are authored anchor windows, not an alternate
    // geography generator. Their tile-grid coordinates are landmass-local and
    // overlap between islands, so they must never be used as the world LOD.
    if options.show_entire_world {
        draw_archipelago_overview(
            manifest,
            world,
            development_world_settings,
            semantic_bake,
            viewport,
            canvas,
            options,
        );
        return;
    }

    let Some(bounds) = world_scene_grid_bounds_for_landmass(manifest, options.selected_landmass_id) else {
        draw_editor_text(
            "No selected landmass surface data available",
            viewport.x + 16.0,
            viewport.y + 36.0,
            22.0,
            WARN,
        );
        return;
    };

    let camera = canvas.camera(viewport, bounds);
    set_camera(&camera);
    let visible = canvas.visible_world_rect(viewport, bounds);
    let pixels_per_tile = viewport.w / visible.w.max(1.0);
    draw_rectangle(
        visible.x,
        visible.y,
        visible.w,
        visible.h,
        if options.show_water {
            Color::new(0.08, 0.15, 0.18, 1.0)
        } else {
            Color::new(0.055, 0.060, 0.065, 1.0)
        },
    );

    for (index, rectangle) in manifest.scene_rectangles.iter().enumerate() {
        if !rectangle_is_overworld_surface(rectangle) {
            continue;
        }
        if !options.show_entire_world && rectangle.landmass_id != options.selected_landmass_id {
            continue;
        }
        let target = world_scene_grid_rect(manifest, rectangle);
        if !rects_intersect(target, visible) {
            continue;
        }
        let assigned_scene = assignments
            .assignment_for_rectangle(&rectangle.scene_id)
            .and_then(|assignment| {
                world.scene_by_id(&ProjectSceneId::new(assignment.scene_code.as_str()))
            });
        if let Some(scene) = assigned_scene {
            draw_scene_surface_into_rect(
                scene,
                target,
                visible,
                pixels_per_tile,
                options.show_terrain,
                options.show_water,
                options.show_roads_paths,
                options.show_structures,
                options.show_structural_levels,
            );
            if options.show_visual_overrides {
                textures.draw_scene_visual_overrides(
                    scene,
                    haven_editor::GridPos { x: target.x as i32, y: target.y as i32 },
                );
            }
            if options.show_zones {
                draw_scene_zone_overlay(scene, target, visible, pixels_per_tile);
            }
            if options.show_structural_levels {
                draw_scene_structural_level_overlay(scene, target, visible, pixels_per_tile);
            }
            if options.show_objects
                || options.show_water
                || options.show_roads_paths
                || options.show_structural_levels
            {
                draw_scene_object_overlay(
                    scene,
                    target,
                    visible,
                    pixels_per_tile,
                    options.show_vegetation,
                    options.show_resources,
                    options.show_structures,
                    options.show_objects_props,
                    options.show_water,
                    options.show_roads_paths,
                    options.show_structural_levels,
                );
            }
        } else {
            draw_rectangle(
                target.x,
                target.y,
                target.w,
                target.h,
                Color::new(0.16, 0.25, 0.26, 0.94),
            );
            draw_editor_text(
                "generation pending",
                target.x + 5.0,
                target.y + 17.0,
                12.0,
                WARN,
            );
        }

        if options.show_partitions {
            let selected = index == options.selected_index;
            draw_rectangle_lines(
                target.x,
                target.y,
                target.w,
                target.h,
                if selected { 1.8 } else { 0.75 },
                if selected { TEXT } else { PANEL_EDGE },
            );
            draw_rectangle(
                target.x,
                target.y,
                32.0_f32.min(target.w),
                4.0,
                Color::new(0.02, 0.03, 0.04, 0.72),
            );
            draw_editor_text(
                &format!(
                    "{},{}",
                    rectangle.grid_x.unwrap_or(0),
                    rectangle.grid_y.unwrap_or(0)
                ),
                target.x + 1.5,
                target.y + 3.2,
                3.5,
                TEXT,
            );
        }
    }

    if options.show_structural_levels && pixels_per_tile >= 2.5 {
        // Structural edge diagnostics remain scoped to the active landmass so
        // the complete-world LOD view does not accidentally imply that a
        // diagnostic operation is editing every island at once.
        draw_structural_edge_diagnostics(
            manifest,
            assignments,
            world,
            options.selected_landmass_id,
            visible,
            canvas.zoom,
        );
    }
    if pixels_per_tile >= 6.0 {
        draw_infinite_grid(visible, 1.0, 8, canvas.zoom);
    }
    for (rect, color) in [
        (options.selection, Color::new(0.30, 0.76, 1.0, 0.82)),
        (options.drag_preview, WARN),
        (options.paste_preview, Color::new(0.32, 0.78, 0.55, 0.94)),
        (options.asset_place_preview, Color::new(0.82, 0.58, 1.0, 0.96)),
        (options.connector_preview, Color::new(0.38, 0.92, 0.58, 0.98)),
    ] {
        if let Some(rect) = rect {
            let width = rect.width().max(1) as f32;
            let height = rect.height().max(1) as f32;
            draw_rectangle(
                rect.min.x as f32,
                rect.min.y as f32,
                width,
                height,
                Color::new(color.r, color.g, color.b, 0.10),
            );
            draw_rectangle_lines(
                rect.min.x as f32,
                rect.min.y as f32,
                width,
                height,
                (0.14 / canvas.zoom.max(0.20)).min(0.20),
                color,
            );
        }
    }
    if let Some((cursor_x, cursor_y)) = options.cursor {
        if matches!(
            options.edit_tool,
            WorldEditTool::Paint | WorldEditTool::Erase
        ) {
            let radius = options.brush_radius.max(0);
            let brush = Rect::new(
                (cursor_x - radius) as f32,
                (cursor_y - radius) as f32,
                (radius * 2 + 1) as f32,
                (radius * 2 + 1) as f32,
            );
            draw_rectangle(
                brush.x,
                brush.y,
                brush.w,
                brush.h,
                Color::new(1.0, 0.78, 0.24, 0.06),
            );
            draw_rectangle_lines(
                brush.x,
                brush.y,
                brush.w,
                brush.h,
                (0.10 / canvas.zoom.max(0.20)).min(0.16),
                WARN,
            );
        }
        let cursor = Rect::new(cursor_x as f32, cursor_y as f32, 1.0, 1.0);
        if rects_intersect(cursor, visible) {
            draw_rectangle(
                cursor.x,
                cursor.y,
                cursor.w,
                cursor.h,
                Color::new(1.0, 0.78, 0.24, 0.18),
            );
            draw_rectangle_lines(
                cursor.x,
                cursor.y,
                cursor.w,
                cursor.h,
                (0.12 / canvas.zoom.max(0.20)).min(0.18),
                WARN,
            );
        }
    }
    set_default_camera();
    draw_canvas_rulers(viewport, visible, 1.0, "Tile");

    draw_rectangle_lines(
        viewport.x, viewport.y, viewport.w, viewport.h, 1.0, PANEL_EDGE,
    );
    draw_rectangle(
        viewport.x + 8.0,
        viewport.y + 8.0,
        430.0,
        44.0,
        Color::new(0.04, 0.05, 0.05, 0.78),
    );
    draw_editor_text(
        &format!(
            "{} | {} layer | {} tool | brush {}x{}",
            if options.show_entire_world { "Havenwild Development World" } else { "Selected Landmass" },
            options.layer_mode.label(),
            options.edit_tool.label(),
            options.brush_radius * 2 + 1,
            options.brush_radius * 2 + 1
        ),
        viewport.x + 16.0,
        viewport.y + 25.0,
        17.0,
        TEXT,
    );
    draw_editor_text(
        if options.show_entire_world {
            "Entire persistent world • zoom from archipelago LOD to native 32px terrain • selected landmass remains the edit authority"
        } else {
            "Selected landmass focus • storage partitions are diagnostics only"
        },
        viewport.x + 16.0,
        viewport.y + 44.0,
        13.0,
        MUTED,
    );
}

fn draw_archipelago_overview(
    _manifest: &SceneRectangleManifest,
    world: &GameWorld,
    development_world_settings: &WorldCreationSettings,
    semantic_bake: Option<&SemanticWorldBakeV1>,
    viewport: Rect,
    canvas: &CanvasCameraState,
    options: WorldSurfaceViewOptions,
) {
    let Some(bake) = semantic_bake else {
        draw_editor_text(
            "No canonical semantic world bake is available",
            viewport.x + 16.0,
            viewport.y + 36.0,
            22.0,
            WARN,
        );
        return;
    };
    let Some(bounds) = world_archipelago_overview_bounds(bake) else {
        draw_editor_text(
            "Canonical semantic world bake has invalid bounds",
            viewport.x + 16.0,
            viewport.y + 36.0,
            22.0,
            WARN,
        );
        return;
    };

    let camera = canvas.camera(viewport, bounds);
    set_camera(&camera);
    let visible = canvas.visible_world_rect(viewport, bounds);
    let pixels_per_unit = viewport.w / visible.w.max(1.0);

    // The semantic bake is the same complete deterministic low-LOD authority
    // used by the runtime M-map. This removes the old second geography made
    // from SceneRectangleSpec::world_rect_preview_px.
    draw_rectangle(
        visible.x,
        visible.y,
        visible.w,
        visible.h,
        if options.show_water {
            Color::new(0.055, 0.18, 0.25, 1.0)
        } else {
            Color::new(0.050, 0.055, 0.060, 1.0)
        },
    );
    draw_semantic_world_bake(
        bake,
        visible,
        options.show_terrain,
        options.show_water,
        options.show_structural_levels,
        options.show_vegetation,
    );

    // Exact materialized exterior scenes overlay the coarse bake at the same
    // continuous-surface coordinates consumed by gameplay. This makes live
    // authoring visible without allowing a preview-layout file to reposition
    // the underlying world.
    let surface_manifest = haven_world::ContinuousSurfaceManifest::for_world(world);
    for binding in &surface_manifest.exterior_bindings {
        let Some(scene) = world.scene_by_id(&binding.scene_id) else {
            continue;
        };
        let target = Rect::new(
            (binding.chunk.x * MAP_W as i32) as f32,
            (binding.chunk.y * MAP_H as i32) as f32,
            MAP_W as f32,
            MAP_H as f32,
        );
        if rects_intersect(target, visible) {
            draw_scene_surface_scaled_into_rect(
                scene,
                target,
                pixels_per_unit,
                options.show_terrain,
                options.show_water,
                options.show_roads_paths,
                options.show_structures,
                options.show_structural_levels,
            );
            if (options.show_objects
                || options.show_water
                || options.show_roads_paths
                || options.show_structural_levels)
                && pixels_per_unit >= 0.35
            {
                draw_scene_object_overlay(
                    scene,
                    target,
                    visible,
                    pixels_per_unit,
                    options.show_vegetation,
                    options.show_resources,
                    options.show_structures,
                    options.show_objects_props,
                    options.show_water,
                    options.show_roads_paths,
                    options.show_structural_levels,
                );
            }
            if options.show_partitions && pixels_per_unit >= 0.55 {
                draw_rectangle_lines(
                    target.x,
                    target.y,
                    target.w,
                    target.h,
                    0.8,
                    PANEL_EDGE,
                );
            }
        }
    }

    if let Some(selected_bounds) = world_overview_landmass_rect(
        development_world_settings,
        options.selected_landmass_id,
    ) {
        draw_rectangle_lines(
            selected_bounds.x,
            selected_bounds.y,
            selected_bounds.w,
            selected_bounds.h,
            (2.0 / pixels_per_unit.max(0.01)).min(28.0),
            Color::new(1.0, 0.55, 0.18, 0.95),
        );
    }

    if pixels_per_unit >= 0.08 {
        for landmark in &bake.landmarks {
            draw_editor_text(
                &landmark.label,
                landmark.world_x as f32 + 8.0 / pixels_per_unit.max(0.01),
                landmark.world_y as f32,
                (11.0 / pixels_per_unit.max(0.01)).min(80.0),
                if landmark.capital { TEXT } else { MUTED },
            );
        }
    }

    set_default_camera();
    draw_rectangle_lines(
        viewport.x,
        viewport.y,
        viewport.w,
        viewport.h,
        1.0,
        PANEL_EDGE,
    );
    draw_rectangle(
        viewport.x + 8.0,
        viewport.y + 8.0,
        520.0_f32.min(viewport.w - 16.0),
        48.0,
        Color::new(0.04, 0.05, 0.05, 0.82),
    );
    draw_editor_text(
        "Havenwild Development World | Canonical Runtime Geography",
        viewport.x + 16.0,
        viewport.y + 25.0,
        17.0,
        TEXT,
    );
    draw_editor_text(
        "Runtime semantic bake + materialized surface overlays • click a major landmass to edit",
        viewport.x + 16.0,
        viewport.y + 45.0,
        13.0,
        MUTED,
    );
}

fn draw_semantic_world_bake(
    bake: &SemanticWorldBakeV1,
    visible: Rect,
    show_terrain: bool,
    show_water: bool,
    show_structural_levels: bool,
    show_vegetation: bool,
) {
    if bake.cols == 0 || bake.rows == 0 {
        return;
    }
    let cell_w = bake.span_w as f32 / bake.cols as f32;
    let cell_h = bake.span_h as f32 / bake.rows as f32;
    for row in 0..bake.rows {
        let y = bake.origin_y as f32 + row as f32 * cell_h;
        if y + cell_h < visible.y || y > visible.y + visible.h {
            continue;
        }
        let mut col = 0usize;
        while col < bake.cols {
            let code = bake.cells[row * bake.cols + col];
            let code_visible = match code {
                0 | 1 | 8 => show_water,
                4 | 5 | 6 => show_structural_levels,
                11 => show_vegetation,
                _ => show_terrain,
            };
            let mut run_end = col + 1;
            while run_end < bake.cols && bake.cells[row * bake.cols + run_end] == code {
                run_end += 1;
            }
            let x = bake.origin_x as f32 + col as f32 * cell_w;
            let width = (run_end - col) as f32 * cell_w + 0.02;
            let run_rect = Rect::new(x, y, width, cell_h + 0.02);
            if code_visible && rects_intersect(run_rect, visible) {
                draw_rectangle(x, y, width, cell_h + 0.02, semantic_world_map_color(code));
            }
            col = run_end;
        }
    }
}

/// Mirrors the runtime world-map palette for the shared semantic map codes.
fn semantic_world_map_color(code: u8) -> Color {
    match code {
        0 => Color::from_rgba(13, 48, 82, 255),
        1 => Color::from_rgba(47, 113, 149, 255),
        2 => Color::from_rgba(206, 188, 121, 255),
        4 => Color::from_rgba(67, 112, 58, 255),
        5 => Color::from_rgba(83, 96, 66, 255),
        6 => Color::from_rgba(65, 54, 43, 255),
        8 => Color::from_rgba(63, 133, 158, 255),
        11 => Color::from_rgba(38, 94, 48, 255),
        _ => Color::from_rgba(55, 129, 66, 255),
    }
}

fn draw_scene_surface_scaled_into_rect(
    scene: &SceneMap,
    target: Rect,
    pixels_per_unit: f32,
    show_terrain: bool,
    show_water: bool,
    show_roads_paths: bool,
    show_structures: bool,
    show_structural_levels: bool,
) {
    let preview_step = if pixels_per_unit >= 2.0 {
        1
    } else if pixels_per_unit >= 1.0 {
        2
    } else if pixels_per_unit >= 0.45 {
        4
    } else {
        8
    };
    let width = target.w.max(1.0).round() as i32;
    let height = target.h.max(1.0).round() as i32;
    let mut py = 0;
    while py < height {
        let block_h = preview_step.min(height - py);
        let mut px = 0;
        while px < width {
            let block_w = preview_step.min(width - px);
            let source_x = (((px as f32 + block_w as f32 * 0.5) / width as f32)
                * MAP_W as f32)
                .floor()
                .clamp(0.0, (MAP_W - 1) as f32) as i32;
            let source_y = (((py as f32 + block_h as f32 * 0.5) / height as f32)
                * MAP_H as f32)
                .floor()
                .clamp(0.0, (MAP_H - 1) as f32) as i32;
            let tile = scene.map.get(source_x, source_y);
            if world_surface_tile_visible(
                tile,
                show_terrain,
                show_water,
                show_roads_paths,
                show_structures,
                show_structural_levels,
            ) {
                draw_rectangle(
                    target.x + px as f32,
                    target.y + py as f32,
                    block_w as f32 + 0.02,
                    block_h as f32 + 0.02,
                    scene_tile_color(tile),
                );
            }
            px += preview_step;
        }
        py += preview_step;
    }
}

fn draw_structural_edge_diagnostics(
    manifest: &SceneRectangleManifest,
    assignments: &SceneRectangleAssignmentsFile,
    world: &GameWorld,
    landmass_id: i32,
    visible: Rect,
    zoom: f32,
) {
    let partition_index = manifest
        .scene_rectangles
        .iter()
        .filter(|entry| rectangle_is_overworld_surface(entry) && entry.landmass_id == landmass_id)
        .filter_map(|rectangle| {
            let assignment = assignments.assignment_for_rectangle(&rectangle.scene_id)?;
            let scene = world.scene_by_id(&ProjectSceneId::new(assignment.scene_code.as_str()))?;
            Some(((rectangle.grid_x?, rectangle.grid_y?), scene))
        })
        .collect::<std::collections::HashMap<_, _>>();

    let min_x = visible.x.floor() as i32;
    let min_y = visible.y.floor() as i32;
    let max_x = (visible.x + visible.w).ceil() as i32;
    let max_y = (visible.y + visible.h).ceil() as i32;
    let line_width = (0.12 / zoom.max(0.20)).min(0.18);
    let color = Color::new(1.0, 0.48, 0.20, 0.88);
    for y in min_y..max_y {
        for x in min_x..max_x {
            let Some(level) = indexed_global_surface_sample(&partition_index, x, y) else {
                continue;
            };
            if let Some(east_level) = indexed_global_surface_sample(&partition_index, x + 1, y) {
                if east_level != level {
                    draw_line(
                        (x + 1) as f32,
                        y as f32,
                        (x + 1) as f32,
                        (y + 1) as f32,
                        line_width,
                        color,
                    );
                }
            }
            if let Some(south_level) = indexed_global_surface_sample(&partition_index, x, y + 1) {
                if south_level != level {
                    draw_line(
                        x as f32,
                        (y + 1) as f32,
                        (x + 1) as f32,
                        (y + 1) as f32,
                        line_width,
                        color,
                    );
                }
            }
        }
    }
}

fn indexed_global_surface_sample(
    partition_index: &std::collections::HashMap<(i32, i32), &SceneMap>,
    global_x: i32,
    global_y: i32,
) -> Option<u8> {
    let partition_w = MAP_W as i32;
    let partition_h = MAP_H as i32;
    let partition = (
        global_x.div_euclid(partition_w),
        global_y.div_euclid(partition_h),
    );
    let local_x = global_x.rem_euclid(partition_w);
    let local_y = global_y.rem_euclid(partition_h);
    let scene = partition_index.get(&partition)?;
    Some(
        scene
            .map
            .get_structural_level(local_x, local_y)
            .unwrap_or(0),
    )
}

pub(crate) fn world_scene_grid_rect(
    _manifest: &SceneRectangleManifest,
    rectangle: &SceneRectangleSpec,
) -> Rect {
    Rect::new(
        rectangle.grid_x.unwrap_or(0) as f32 * WORLD_SURFACE_PARTITION_W,
        rectangle.grid_y.unwrap_or(0) as f32 * WORLD_SURFACE_PARTITION_H,
        WORLD_SURFACE_PARTITION_W,
        WORLD_SURFACE_PARTITION_H,
    )
}


/// Complete-world LOD bounds. These are generated archipelago-layout units,
/// not landmass-local tile coordinates. Keeping the spaces explicit prevents
/// multiple islands whose local partition grids begin at (0,0) from rendering
/// on top of one another.
pub(crate) fn world_archipelago_overview_bounds(bake: &SemanticWorldBakeV1) -> Option<Rect> {
    if bake.span_w <= 0 || bake.span_h <= 0 {
        return None;
    }
    Some(Rect::new(
        bake.origin_x as f32,
        bake.origin_y as f32,
        bake.span_w as f32,
        bake.span_h as f32,
    ))
}

/// Legacy compatibility rectangle retained for old manifests/tools. The
/// complete-world Game Canvas must never use this to position geography.
pub(crate) fn world_scene_overview_rect(rectangle: &SceneRectangleSpec) -> Rect {
    let [x, y, width, height] = rectangle.world_rect_preview_px;
    Rect::new(x as f32, y as f32, width.max(1) as f32, height.max(1) as f32)
}

pub(crate) fn world_overview_landmass_at_point(
    manifest: &SceneRectangleManifest,
    settings: &WorldCreationSettings,
    bake: &SemanticWorldBakeV1,
    point: Vec2,
) -> Option<(usize, i32)> {
    if semantic_world_code_at_point(bake, point).is_none_or(|code| code <= 1) {
        return None;
    }
    let profile = haven_world::GeographicGenerationProfile::from_world_creation(settings);
    let skeleton = haven_world::ArchipelagoSkeleton::for_geographic_profile(settings.seed, profile);
    let mut major_id = 0_i32;
    let mut best: Option<(f32, i32)> = None;
    for landmass in skeleton.landmasses.iter().filter(|landmass| {
        matches!(landmass.class, LandmassClass::Mainland | LandmassClass::MajorIsland)
    }) {
        let dx = (point.x - landmass.center.x as f32) / landmass.radius_x_tiles.max(1) as f32;
        let dy = (point.y - landmass.center.y as f32) / landmass.radius_y_tiles.max(1) as f32;
        let distance = dx * dx + dy * dy;
        if best.map(|(current, _)| distance < current).unwrap_or(true) {
            best = Some((distance, major_id));
        }
        major_id += 1;
    }
    let (_, landmass_id) = best?;
    manifest
        .scene_rectangles
        .iter()
        .enumerate()
        .find(|(_, entry)| {
            rectangle_is_overworld_surface(entry) && entry.landmass_id == landmass_id
        })
        .map(|(index, _)| (index, landmass_id))
}

pub(crate) fn world_overview_landmass_rect(
    settings: &WorldCreationSettings,
    landmass_id: i32,
) -> Option<Rect> {
    if landmass_id < 0 {
        return None;
    }
    let profile = haven_world::GeographicGenerationProfile::from_world_creation(settings);
    let skeleton = haven_world::ArchipelagoSkeleton::for_geographic_profile(settings.seed, profile);
    let landmass = skeleton
        .landmasses
        .iter()
        .filter(|entry| matches!(entry.class, LandmassClass::Mainland | LandmassClass::MajorIsland))
        .nth(landmass_id as usize)?;
    Some(Rect::new(
        (landmass.center.x - landmass.radius_x_tiles) as f32,
        (landmass.center.y - landmass.radius_y_tiles) as f32,
        (landmass.radius_x_tiles * 2) as f32,
        (landmass.radius_y_tiles * 2) as f32,
    ))
}

fn semantic_world_code_at_point(bake: &SemanticWorldBakeV1, point: Vec2) -> Option<u8> {
    if point.x < bake.origin_x as f32
        || point.y < bake.origin_y as f32
        || point.x >= (bake.origin_x + bake.span_w) as f32
        || point.y >= (bake.origin_y + bake.span_h) as f32
    {
        return None;
    }
    let normalized_x = (point.x - bake.origin_x as f32) / bake.span_w.max(1) as f32;
    let normalized_y = (point.y - bake.origin_y as f32) / bake.span_h.max(1) as f32;
    let col = (normalized_x * bake.cols as f32).floor() as usize;
    let row = (normalized_y * bake.rows as f32).floor() as usize;
    bake.cells.get(row * bake.cols + col).copied()
}

pub(crate) fn world_scene_grid_bounds_all(manifest: &SceneRectangleManifest) -> Option<Rect> {
    let mut min_x = f32::INFINITY;
    let mut min_y = f32::INFINITY;
    let mut max_x = f32::NEG_INFINITY;
    let mut max_y = f32::NEG_INFINITY;
    for rectangle in manifest
        .scene_rectangles
        .iter()
        .filter(|entry| rectangle_is_overworld_surface(entry))
    {
        let rect = world_scene_grid_rect(manifest, rectangle);
        min_x = min_x.min(rect.x);
        min_y = min_y.min(rect.y);
        max_x = max_x.max(rect.x + rect.w);
        max_y = max_y.max(rect.y + rect.h);
    }
    if !min_x.is_finite() || !min_y.is_finite() {
        return None;
    }
    Some(Rect::new(min_x, min_y, max_x - min_x, max_y - min_y))
}

pub(crate) fn world_landmass_at_global_cell(
    manifest: &SceneRectangleManifest,
    global: haven_editor::GridPos,
) -> Option<i32> {
    manifest
        .scene_rectangles
        .iter()
        .rev()
        .filter(|entry| rectangle_is_overworld_surface(entry))
        .find(|rectangle| {
            world_scene_grid_rect(manifest, rectangle)
                .contains(vec2(global.x as f32 + 0.5, global.y as f32 + 0.5))
        })
        .map(|rectangle| rectangle.landmass_id)
}

pub(crate) fn world_scene_grid_bounds_for_landmass(
    manifest: &SceneRectangleManifest,
    landmass_id: i32,
) -> Option<Rect> {
    let mut min_x = f32::INFINITY;
    let mut min_y = f32::INFINITY;
    let mut max_x = f32::NEG_INFINITY;
    let mut max_y = f32::NEG_INFINITY;
    for rectangle in manifest
        .scene_rectangles
        .iter()
        .filter(|entry| rectangle_is_overworld_surface(entry) && entry.landmass_id == landmass_id)
    {
        let rect = world_scene_grid_rect(manifest, rectangle);
        min_x = min_x.min(rect.x);
        min_y = min_y.min(rect.y);
        max_x = max_x.max(rect.x + rect.w);
        max_y = max_y.max(rect.y + rect.h);
    }
    if !min_x.is_finite() || !min_y.is_finite() {
        return None;
    }
    Some(Rect::new(min_x, min_y, max_x - min_x, max_y - min_y))
}

pub(crate) fn rectangle_is_overworld_surface(rectangle: &SceneRectangleSpec) -> bool {
    rectangle.grid_x.is_some()
        && rectangle.grid_y.is_some()
        && !rectangle.kind.starts_with("special_")
}

fn rects_intersect(left: Rect, right: Rect) -> bool {
    left.x < right.x + right.w
        && left.x + left.w > right.x
        && left.y < right.y + right.h
        && left.y + left.h > right.y
}

fn world_preview_step(pixels_per_tile: f32) -> i32 {
    if pixels_per_tile >= 5.0 {
        1
    } else if pixels_per_tile >= 2.5 {
        2
    } else if pixels_per_tile >= 1.2 {
        4
    } else if pixels_per_tile >= 0.6 {
        8
    } else {
        16
    }
}

fn scene_visible_local_bounds(target: Rect, visible: Rect) -> (i32, i32, i32, i32) {
    let Some(bounds) = visible_grid_bounds_in_world(
        AuthoringCanvasRect::new(visible.x, visible.y, visible.w, visible.h),
        AuthoringCanvasPoint::new(target.x, target.y),
        1.0,
        MAP_W as i32,
        MAP_H as i32,
    ) else {
        return (0, 0, 0, 0);
    };
    (
        bounds.min.x,
        bounds.min.y,
        bounds.max.x + 1,
        bounds.max.y + 1,
    )
}

fn world_surface_tile_visible(
    tile: haven_core::TileKind,
    show_terrain: bool,
    show_water: bool,
    show_roads_paths: bool,
    show_structures: bool,
    show_structural_levels: bool,
) -> bool {
    match super::canvas_layers::canvas_layer_kind_for_surface_tile(tile) {
        super::canvas_layers::CanvasLayerKind::Water => show_water,
        super::canvas_layers::CanvasLayerKind::RoadsPaths => show_roads_paths,
        super::canvas_layers::CanvasLayerKind::Structures => show_structures,
        super::canvas_layers::CanvasLayerKind::StructuralLevels => show_structural_levels,
        _ => show_terrain,
    }
}

fn draw_scene_surface_into_rect(
    scene: &SceneMap,
    target: Rect,
    visible: Rect,
    pixels_per_tile: f32,
    show_terrain: bool,
    show_water: bool,
    show_roads_paths: bool,
    show_structures: bool,
    show_structural_levels: bool,
) {
    let step = world_preview_step(pixels_per_tile);
    let (min_x, min_y, max_x, max_y) = scene_visible_local_bounds(target, visible);
    if min_x >= max_x || min_y >= max_y {
        return;
    }
    let mut y = min_y;
    while y < max_y {
        let block_h = step.min(max_y - y);
        let mut x = min_x;
        while x < max_x {
            let block_w = step.min(max_x - x);
            let tile = scene.map.get(x, y);
            if world_surface_tile_visible(
                tile,
                show_terrain,
                show_water,
                show_roads_paths,
                show_structures,
                show_structural_levels,
            ) {
                draw_rectangle(
                    target.x + x as f32,
                    target.y + y as f32,
                    block_w as f32 + 0.02,
                    block_h as f32 + 0.02,
                    scene_tile_color(tile),
                );
            }
            x += step;
        }
        y += step;
    }
}

fn draw_scene_zone_overlay(scene: &SceneMap, target: Rect, visible: Rect, pixels_per_tile: f32) {
    let step = world_preview_step(pixels_per_tile).max(2);
    let (min_x, min_y, max_x, max_y) = scene_visible_local_bounds(target, visible);
    let mut y = min_y;
    while y < max_y {
        let mut x = min_x;
        while x < max_x {
            if let Some(mut color) = zone_preview_color(scene.zone_at(x, y)) {
                color.a = color.a.max(0.22);
                draw_rectangle(
                    target.x + x as f32,
                    target.y + y as f32,
                    step.min(max_x - x) as f32,
                    step.min(max_y - y) as f32,
                    color,
                );
            }
            x += step;
        }
        y += step;
    }
}

fn draw_scene_structural_level_overlay(
    scene: &SceneMap,
    target: Rect,
    visible: Rect,
    pixels_per_tile: f32,
) {
    let step = world_preview_step(pixels_per_tile).max(2);
    let (min_x, min_y, max_x, max_y) = scene_visible_local_bounds(target, visible);
    let mut y = min_y;
    while y < max_y {
        let mut x = min_x;
        while x < max_x {
            let level = scene.map.get_structural_level(x, y).unwrap_or(0);
            if level > 0 {
                let alpha = (0.10 + level as f32 * 0.09).min(0.36);
                draw_rectangle(
                    target.x + x as f32,
                    target.y + y as f32,
                    step.min(max_x - x) as f32,
                    step.min(max_y - y) as f32,
                    Color::new(0.78, 0.42, 0.18, alpha),
                );
            }
            x += step;
        }
        y += step;
    }
}

fn world_object_layer_visible(
    kind: haven_core::ObjectKind,
    show_vegetation: bool,
    show_resources: bool,
    show_structures: bool,
    show_objects_props: bool,
) -> bool {
    match super::canvas_layers::canvas_layer_kind_for_world_object(kind) {
        super::canvas_layers::CanvasLayerKind::Vegetation => show_vegetation,
        super::canvas_layers::CanvasLayerKind::Resources => show_resources,
        super::canvas_layers::CanvasLayerKind::Structures => show_structures,
        _ => show_objects_props,
    }
}

fn draw_scene_object_overlay(
    scene: &SceneMap,
    target: Rect,
    visible: Rect,
    pixels_per_tile: f32,
    show_vegetation: bool,
    show_resources: bool,
    show_structures: bool,
    show_objects_props: bool,
    show_water: bool,
    show_roads_paths: bool,
    show_structural_levels: bool,
) {
    let line = if pixels_per_tile >= 4.0 { 0.12 } else { 0.28 };
    // Stamps are semantic composite placeables too. Pond stamps follow the
    // Water layer, structural stamps follow Structures/Elevation, and normal
    // authored stamps follow Objects & Props. They never inherit Terrain just
    // because their backing data lives beside terrain content.
    for stamp in &scene.map.stamps {
        let stamp_visible = match super::canvas_layers::canvas_layer_kind_for_stamp(&stamp.stamp_key, None) {
            super::canvas_layers::CanvasLayerKind::Water => show_water,
            super::canvas_layers::CanvasLayerKind::RoadsPaths => show_roads_paths,
            super::canvas_layers::CanvasLayerKind::Structures => show_structures,
            super::canvas_layers::CanvasLayerKind::StructuralLevels => show_structural_levels,
            _ => show_objects_props,
        };
        if !stamp_visible {
            continue;
        }
        let (x, y, w, h) = stamp.visual_rect();
        let rect = Rect::new(target.x + x as f32, target.y + y as f32, w as f32, h as f32);
        if rects_intersect(rect, visible) {
            draw_rectangle(
                rect.x,
                rect.y,
                rect.w.max(1.0),
                rect.h.max(1.0),
                Color::new(0.26, 0.72, 0.94, 0.18),
            );
            draw_rectangle_lines(
                rect.x,
                rect.y,
                rect.w.max(1.0),
                rect.h.max(1.0),
                line,
                Color::new(0.42, 0.86, 1.0, 0.86),
            );
        }
    }
    for object in &scene.map.objects {
        if !world_object_layer_visible(
            object.kind,
            show_vegetation,
            show_resources,
            show_structures,
            show_objects_props,
        ) {
            continue;
        }
        let (x, y, w, h) = object.visual_rect();
        let rect = Rect::new(target.x + x as f32, target.y + y as f32, w as f32, h as f32);
        if rects_intersect(rect, visible) {
            draw_rectangle(
                rect.x,
                rect.y,
                rect.w.max(1.0),
                rect.h.max(1.0),
                Color::new(1.0, 0.78, 0.24, 0.16),
            );
            draw_rectangle_lines(
                rect.x,
                rect.y,
                rect.w.max(1.0),
                rect.h.max(1.0),
                line,
                Color::new(1.0, 0.86, 0.36, 0.90),
            );
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rectangle_intersection_rejects_offscreen_regions() {
        assert!(rects_intersect(
            Rect::new(0.0, 0.0, 10.0, 10.0),
            Rect::new(5.0, 5.0, 10.0, 10.0),
        ));
        assert!(!rects_intersect(
            Rect::new(0.0, 0.0, 10.0, 10.0),
            Rect::new(20.0, 20.0, 10.0, 10.0),
        ));
    }

    #[test]
    fn world_surface_partitions_use_true_tile_dimensions() {
        assert_eq!(WORLD_SURFACE_PARTITION_W, MAP_W as f32);
        assert_eq!(WORLD_SURFACE_PARTITION_H, MAP_H as f32);
        assert_ne!(WORLD_SURFACE_PARTITION_W, WORLD_SURFACE_PARTITION_H);
    }

    #[test]
    fn world_preview_lod_reaches_native_tiles_when_zoomed_in() {
        assert_eq!(world_preview_step(6.0), 1);
        assert_eq!(world_preview_step(3.0), 2);
        assert_eq!(world_preview_step(1.5), 4);
        assert_eq!(world_preview_step(0.8), 8);
        assert_eq!(world_preview_step(0.2), 16);
    }
}
