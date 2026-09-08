use super::*;
use haven_assets::{
    lpc_cliff_ramp_provider::{LpcCliffContourStampRole, LPC_CLIFF_RAMP_GRASS_SOURCE_PATH},
    lpc_mapped_terrain::{
        lpc_mapped_terrain_atlas_path, lpc_mapped_terrain_owner_fill_entry_for_map,
        lpc_mapped_terrain_transition_entry_for_map,
    },
};
use haven_render::structural_cliff_visual::{
    authored_body_rows, resolve_cliff_visual_recipe_v1, CliffVisualShape,
    EAST_EDGE_CELL, ELIZAWY_SUMMER_CLIFF_SOURCE_PATH, NORTH_EAST_CORNER_CELL,
    NORTH_LIP_CELL, NORTH_WEST_CORNER_CELL, SOUTH_EAST_DIAGONAL_FACE,
    SOUTH_STRAIGHT_FACE, SOUTH_TERMINAL_BODY_ROW, SOUTH_TERMINAL_CREST_ROW,
    SOUTH_TERMINAL_FOOT_ROW, SOUTH_WEST_DIAGONAL_FACE, WEST_EDGE_CELL,
};
use haven_world::{
    resolve_tavern_map_elevation_cliffs_v2, terrain_tuple_render_origin_tiles,
    ElevationCliffSettingsV2,
};
use image::{imageops::FilterType, DynamicImage, Rgba, RgbaImage};
use std::{collections::HashMap, path::PathBuf};

pub(crate) struct PreparedCanvasLayer {
    pub name: String,
    pub image: RgbaImage,
    pub locked: bool,
}

pub(crate) struct PreparedCanvasComposition {
    pub layers: Vec<PreparedCanvasLayer>,
    pub building_count: usize,
    pub object_count: usize,
    pub stamp_count: usize,
}

impl EditorApp {
    /// W60E1: one prepared scene presentation is shared by Scene Editor -> Pixel Studio
    /// selection round trips. It deliberately reconstructs the same semantic layers instead
    /// of exporting only the base terrain cells.
    pub(crate) fn prepare_scene_canvas_composition(
        &self,
        scene_id: &ProjectSceneId,
        local_rect: GridRect,
    ) -> Result<PreparedCanvasComposition, String> {
        let scene = self
            .model
            .world
            .scene_by_id(scene_id)
            .ok_or_else(|| format!("Scene {} is not loaded", scene_id.code()))?;
        let width_px = (local_rect.width().max(1) as u32).saturating_mul(32);
        let height_px = (local_rect.height().max(1) as u32).saturating_mul(32);
        let mut sources: HashMap<PathBuf, DynamicImage> = HashMap::new();
        let mut layers = Vec::new();

        let mut terrain = RgbaImage::new(width_px, height_px);
        let mapped_path = lpc_mapped_terrain_atlas_path()
            .ok()
            .map(resolve_project_path);
        if let Some(path) = mapped_path.as_ref() {
            if let Ok(image) = image::open(path) {
                sources.insert(path.clone(), image);
            }
        }
        for local in local_rect.cells() {
            let target_x = (local.x - local_rect.min.x) * 32;
            let target_y = (local.y - local_rect.min.y) * 32;
            let mut drew = false;
            if let Some(path) = mapped_path.as_ref() {
                if let (Some(source), Some(entry)) = (
                    sources.get(path),
                    lpc_mapped_terrain_owner_fill_entry_for_map(&scene.map, local.x, local.y),
                ) {
                    drew = blit_atlas_rect(
                        &mut terrain,
                        source,
                        entry.rect,
                        target_x,
                        target_y,
                        32,
                        32,
                    );
                }
            }
            if !drew {
                // Fail closed to transparent rather than inventing a second terrain binding table.
                // The authored V7 mapped atlas is the scene/runtime authority for production terrain.
            }
        }
        layers.push(PreparedCanvasLayer {
            name: "Generated Terrain".to_string(),
            image: terrain,
            locked: true,
        });

        let mut transitions = RgbaImage::new(width_px, height_px);
        if let Some(path) = mapped_path.as_ref() {
            if let Some(source) = sources.get(path) {
                for local in local_rect.cells() {
                    let Some(entry) = lpc_mapped_terrain_transition_entry_for_map(&scene.map, local.x, local.y) else { continue; };
                    let (draw_x, draw_y) = terrain_tuple_render_origin_tiles(local.x, local.y);
                    let target_x = ((draw_x - local_rect.min.x as f32) * 32.0).round() as i32;
                    let target_y = ((draw_y - local_rect.min.y as f32) * 32.0).round() as i32;
                    let _ = blit_atlas_rect(&mut transitions, source, entry.rect, target_x, target_y, 32, 32);
                }
            }
        }
        layers.push(PreparedCanvasLayer {
            name: "Terrain Transitions".to_string(),
            image: transitions,
            locked: true,
        });

        // W60E7: structural elevation/cliff presentation is part of the shared
        // canvas truth. Scene Editor/runtime draw this pass after terrain
        // transitions and before authored overrides; selected-region Pixel
        // Studio must reconstruct the same cliff recipes instead of silently
        // dropping them.
        let structural_cliffs = rasterize_structural_cliffs(
            scene,
            local_rect,
            width_px,
            height_px,
            &mut sources,
        );
        layers.push(PreparedCanvasLayer {
            name: "Structural Terrain / Cliffs".to_string(),
            image: structural_cliffs,
            locked: true,
        });

        let mut existing_overrides = RgbaImage::new(width_px, height_px);
        for entry in &scene.visual_overrides {
            if entry.is_building_composite() {
                continue;
            }
            let entry_rect = GridRect::from_points(
                GridPos { x: entry.x, y: entry.y },
                GridPos { x: entry.x + entry.w - 1, y: entry.y + entry.h - 1 },
            );
            if !rects_intersect(local_rect, entry_rect) { continue; }
            let path = resolve_project_path(&entry.asset_path);
            ensure_source(&mut sources, &path);
            let Some(source) = sources.get(&path) else { continue; };
            let resized = source.resize_exact((entry.w.max(1) as u32) * 32, (entry.h.max(1) as u32) * 32, FilterType::Nearest).to_rgba8();
            let dx = (entry.x - local_rect.min.x) * 32;
            let dy = (entry.y - local_rect.min.y) * 32;
            alpha_blit(&mut existing_overrides, &resized, dx, dy);
        }
        layers.push(PreparedCanvasLayer {
            name: "Existing Visual Overrides".to_string(),
            image: existing_overrides,
            locked: true,
        });

        let mut buildings = RgbaImage::new(width_px, height_px);
        let mut building_count = 0usize;
        for instance in self.resolved_building_instances_for_scene(scene) {
            let Some(recipe) = self.building_recipe_registry.entry(&instance.recipe_id) else { continue; };
            let footprint = GridRect::from_points(
                GridPos { x: instance.anchor_tile[0], y: instance.anchor_tile[1] },
                GridPos {
                    x: instance.anchor_tile[0] + recipe.footprint[0] as i32 - 1,
                    y: instance.anchor_tile[1] + recipe.footprint[1] as i32 - 1,
                },
            );
            if !rects_intersect(local_rect, footprint) { continue; }
            building_count += 1;
            let state = self
                .building_preview_views
                .get(&instance.id)
                .copied()
                .unwrap_or_else(|| super::building_instance_preview::building_preview_state_for_recipe(&instance, recipe));
            if !state.inside {
                if let Some(entry) = scene.visual_overrides.iter().find(|entry| {
                    entry.is_building_composite()
                        && entry.x == instance.anchor_tile[0]
                        && entry.y == instance.anchor_tile[1]
                        && entry.w == recipe.footprint[0] as i32
                        && entry.h == recipe.footprint[1] as i32
                }) {
                    let path = resolve_project_path(&entry.asset_path);
                    ensure_source(&mut sources, &path);
                    if let Some(source) = sources.get(&path) {
                        let resized = source
                            .resize_exact(
                                (entry.w.max(1) as u32) * 32,
                                (entry.h.max(1) as u32) * 32,
                                FilterType::Nearest,
                            )
                            .to_rgba8();
                        let dx = (entry.x - local_rect.min.x) * 32;
                        let dy = (entry.y - local_rect.min.y) * 32;
                        alpha_blit(&mut buildings, &resized, dx, dy);
                    }
                    continue;
                }
            }
            for visible in self
                .building_instance_registry
                .visible_pieces_for_instance(&instance, recipe, state)
            {
                let Some(definition) = self.placeable_registry.resolve_alias(&visible.piece.asset_id) else { continue; };
                let Some(visual) = definition.visual.as_ref() else { continue; };
                let Some(frame) = visual.frame_for_state(visible.piece.state.as_deref()) else { continue; };
                // Authoring reconstruction must consume the same resolved runtime source
                // that Scene Editor texture loading uses. Provenance paths document where
                // an asset came from, but they are not guaranteed to be the published
                // runtime sheet that frame.source_rect addresses.
                let Some(path) = resolved_published_source_path(definition) else { continue; };
                ensure_source(&mut sources, &path);
                let Some(source) = sources.get(&path) else { continue; };
                let [sx, sy, sw, sh] = frame.source_rect;
                let rect = haven_assets::asset_registry::AtlasRect { x: sx, y: sy, w: sw, h: sh };
                let (dx, dy) = if let Some(origin) = visible.piece.render_origin_px {
                    (
                        (instance.anchor_tile[0] - local_rect.min.x) * 32 + origin[0] + frame.draw_offset_px[0] as i32,
                        (instance.anchor_tile[1] - local_rect.min.y) * 32 + origin[1] + frame.draw_offset_px[1] as i32,
                    )
                } else {
                    (
                        (visible.world_tile[0] - local_rect.min.x) * 32 + 16 - visual.foot_anchor[0] as i32 + frame.draw_offset_px[0] as i32,
                        (visible.world_tile[1] - local_rect.min.y) * 32 + 32 - visual.foot_anchor[1] as i32 + frame.draw_offset_px[1] as i32,
                    )
                };
                let _ = blit_atlas_rect(&mut buildings, source, rect, dx, dy, sw.max(1.0) as u32, sh.max(1.0) as u32);
            }
        }
        layers.push(PreparedCanvasLayer {
            name: "Buildings".to_string(),
            image: buildings,
            locked: true,
        });

        let mut objects = RgbaImage::new(width_px, height_px);
        let mut object_count = 0usize;
        for object in &scene.map.objects {
            let (vx, vy, vw, vh) = object.visual_rect();
            let visual_rect = GridRect::from_points(
                GridPos { x: vx, y: vy },
                GridPos { x: vx + vw - 1, y: vy + vh - 1 },
            );
            if !rects_intersect(local_rect, visual_rect) { continue; }
            let published = scene
                .map
                .object_asset_ref(object.id)
                .and_then(|asset_ref| self.placeable_registry.resolve_persistent_ref(asset_ref))
                .or_else(|| self.placeable_registry.for_legacy_object(object.kind));
            let Some(definition) = published else { continue; };
            let Some(visual) = definition.visual.as_ref() else { continue; };
            let state = scene.map.object_state(object.id);
            let Some(frame) = visual.frame_for_state(state) else { continue; };
            // Match Scene Editor/runtime publication authority exactly.
            let Some(path) = resolved_published_source_path(definition) else { continue; };
            ensure_source(&mut sources, &path);
            let Some(source) = sources.get(&path) else { continue; };
            let foot = haven_render::object_foot_tiles(*object);
            let dx = ((foot.x - local_rect.min.x as f32) * 32.0 - visual.foot_anchor[0] + frame.draw_offset_px[0]) as i32;
            let dy = ((foot.y - local_rect.min.y as f32) * 32.0 - visual.foot_anchor[1] + frame.draw_offset_px[1]) as i32;
            let [sx, sy, sw, sh] = frame.source_rect;
            let rect = haven_assets::asset_registry::AtlasRect { x: sx, y: sy, w: sw, h: sh };
            if blit_atlas_rect(&mut objects, source, rect, dx, dy, sw.max(1.0) as u32, sh.max(1.0) as u32) {
                object_count += 1;
            }
        }

        let mut stamp_count = 0usize;
        for stamp in &scene.map.stamps {
            let (vx, vy, vw, vh) = stamp.visual_rect();
            let visual_rect = GridRect::from_points(
                GridPos { x: vx, y: vy },
                GridPos { x: vx + vw - 1, y: vy + vh - 1 },
            );
            if !rects_intersect(local_rect, visual_rect) { continue; }
            let Some(definition) = self.stamp_registry.entry(&stamp.stamp_key) else { continue; };
            let path = resolve_project_path(&definition.sheet);
            ensure_source(&mut sources, &path);
            let Some(source) = sources.get(&path) else { continue; };
            if let Some(expandable) = definition.expandable {
                let width = stamp.footprint.visual_w.max(1);
                let height = stamp.footprint.visual_h.max(1);
                for cy in 0..height {
                    for cx in 0..width {
                        let rect = expandable.source_rect_for_rect_cell(cx, cy, width, height);
                        let dx = (stamp.x + stamp.footprint.visual_offset_x + cx - local_rect.min.x) * 32;
                        let dy = (stamp.y + stamp.footprint.visual_offset_y + cy - local_rect.min.y) * 32;
                        let _ = blit_atlas_rect(&mut objects, source, rect, dx, dy, 32, 32);
                    }
                }
            } else {
                let dx = (vx - local_rect.min.x) * 32;
                let dy = (vy - local_rect.min.y) * 32;
                let _ = blit_atlas_rect(
                    &mut objects,
                    source,
                    definition.rect,
                    dx,
                    dy,
                    (vw.max(1) as u32) * 32,
                    (vh.max(1) as u32) * 32,
                );
            }
            stamp_count += 1;
        }
        layers.push(PreparedCanvasLayer {
            name: "Objects & Stamps".to_string(),
            image: objects,
            locked: true,
        });

        Ok(PreparedCanvasComposition {
            layers,
            building_count,
            object_count,
            stamp_count,
        })
    }

    /// W60E3I: Building Composite authoring is reconstructed from published
    /// component sources only. Terrain, objects, editor overlays, collision,
    /// selection state, and scene framebuffer state are deliberately absent.
    pub(crate) fn prepare_building_canvas_composition(
        &self,
        scene_id: &ProjectSceneId,
        local_rect: GridRect,
        instance: &haven_assets::building_instance::BuildingInstanceDefinition,
    ) -> Result<PreparedCanvasComposition, String> {
        let scene = self
            .model
            .world
            .scene_by_id(scene_id)
            .ok_or_else(|| format!("Scene {} is not loaded", scene_id.code()))?;
        let recipe = self
            .building_recipe_registry
            .entry(&instance.recipe_id)
            .ok_or_else(|| format!("Building recipe {} is unavailable", instance.recipe_id))?;
        if !self
            .resolved_building_instances_for_scene(scene)
            .iter()
            .any(|candidate| candidate.id == instance.id)
        {
            return Err(format!("Building instance {} is not present in {}", instance.id, scene_id.code()));
        }

        let width_px = (local_rect.width().max(1) as u32).saturating_mul(32);
        let height_px = (local_rect.height().max(1) as u32).saturating_mul(32);
        let mut sources: HashMap<PathBuf, DynamicImage> = HashMap::new();
        // Clean composite authority is independent of Scene Editor cutaway/inside
        // preview state. Always reconstruct the authored exterior baseline.
        let state = haven_assets::building_instance::BuildingInstanceViewState::for_definition(instance);
        let building_bottom = (instance.anchor_tile[1] + recipe.footprint[1] as i32) as f32;
        let mut pieces = self
            .building_instance_registry
            .visible_pieces_for_instance(instance, recipe, state);
        pieces.sort_by(|left, right| {
            let left_y = if left.piece.kind == haven_assets::building_recipe::BuildingRecipePieceKind::Roof {
                building_bottom
            } else {
                left.world_tile[1] as f32 + 1.0
            };
            let right_y = if right.piece.kind == haven_assets::building_recipe::BuildingRecipePieceKind::Roof {
                building_bottom
            } else {
                right.world_tile[1] as f32 + 1.0
            };
            left_y.total_cmp(&right_y)
        });

        let mut layers = Vec::new();
        for visible in pieces {
            let Some(definition) = self.placeable_registry.resolve_alias(&visible.piece.asset_id) else {
                continue;
            };
            let Some(visual) = definition.visual.as_ref() else { continue; };
            let Some(frame) = visual.frame_for_state(visible.piece.state.as_deref()) else { continue; };
            let Some(path) = resolved_published_source_path(definition) else { continue; };
            ensure_source(&mut sources, &path);
            let Some(source) = sources.get(&path) else { continue; };
            let [sx, sy, sw, sh] = frame.source_rect;
            let source_rect = haven_assets::asset_registry::AtlasRect { x: sx, y: sy, w: sw, h: sh };
            let (dx, dy) = if let Some(origin) = visible.piece.render_origin_px {
                (
                    (instance.anchor_tile[0] - local_rect.min.x) * 32 + origin[0] + frame.draw_offset_px[0] as i32,
                    (instance.anchor_tile[1] - local_rect.min.y) * 32 + origin[1] + frame.draw_offset_px[1] as i32,
                )
            } else {
                (
                    (visible.world_tile[0] - local_rect.min.x) * 32 + 16 - visual.foot_anchor[0] as i32 + frame.draw_offset_px[0] as i32,
                    (visible.world_tile[1] - local_rect.min.y) * 32 + 32 - visual.foot_anchor[1] as i32 + frame.draw_offset_px[1] as i32,
                )
            };
            let mut image = RgbaImage::new(width_px, height_px);
            if !blit_atlas_rect(&mut image, source, source_rect, dx, dy, sw.max(1.0) as u32, sh.max(1.0) as u32) {
                continue;
            }
            layers.push(PreparedCanvasLayer {
                name: format!("{} • {}", visible.piece.id, visible.piece.asset_id),
                image,
                locked: true,
            });
        }

        // W60E4: a previously published whole-building composite sits above
        // the immutable component reference stack and below the new authoring
        // draft. Reopening the building therefore starts from the visual truth
        // currently used by Scene Editor/runtime rather than reverting to recipe art.
        if let Some(entry) = scene.visual_overrides.iter().find(|entry| {
            entry.is_building_composite()
                && entry.x == instance.anchor_tile[0]
                && entry.y == instance.anchor_tile[1]
                && entry.w == recipe.footprint[0] as i32
                && entry.h == recipe.footprint[1] as i32
        }) {
            let path = resolve_project_path(&entry.asset_path);
            ensure_source(&mut sources, &path);
            if let Some(source) = sources.get(&path) {
                layers.push(PreparedCanvasLayer {
                    name: "Published Building Composite Override".to_string(),
                    image: source
                        .resize_exact(width_px, height_px, FilterType::Nearest)
                        .to_rgba8(),
                    locked: true,
                });
            }
        }

        if layers.is_empty() {
            return Err(format!(
                "Building {} resolved no clean authoring component pixels",
                instance.id
            ));
        }

        Ok(PreparedCanvasComposition {
            layers,
            building_count: 1,
            object_count: 0,
            stamp_count: 0,
        })
    }
}


fn rasterize_structural_cliffs(
    scene: &SceneMap,
    local_rect: GridRect,
    width_px: u32,
    height_px: u32,
    sources: &mut HashMap<PathBuf, DynamicImage>,
) -> RgbaImage {
    let mut target = RgbaImage::new(width_px, height_px);
    let Ok(structural) = resolve_tavern_map_elevation_cliffs_v2(
        &scene.map,
        ElevationCliffSettingsV2::default(),
    ) else {
        return target;
    };

    let cliff_path = resolve_project_path(ELIZAWY_SUMMER_CLIFF_SOURCE_PATH);
    ensure_source(sources, &cliff_path);
    let Some(cliff_source) = sources.get(&cliff_path).cloned() else {
        return target;
    };

    let ramp_path = resolve_project_path(LPC_CLIFF_RAMP_GRASS_SOURCE_PATH);
    ensure_source(sources, &ramp_path);
    let ramp_source = sources.get(&ramp_path).cloned();

    let min_x = (local_rect.min.x - 2).max(0);
    let max_x = (local_rect.max.x + 2).min(MAP_W as i32 - 1);
    let min_y = (local_rect.min.y - 4).max(0);
    let max_y = (local_rect.max.y + 1).min(MAP_H as i32 - 1);

    let level_at = |x: i32, y: i32| -> Option<u8> {
        if x < 0 || y < 0 || x >= MAP_W as i32 || y >= MAP_H as i32 {
            return None;
        }
        Some(haven_world::structural_level_for_surface_recipe_v1(
            &scene.map,
            x,
            y,
        ))
    };

    for y in min_y..=max_y {
        for x in min_x..=max_x {
            if !scene.is_renderable_cell(x, y) {
                continue;
            }
            let Some(center) = structural.structural_at(x, y) else {
                continue;
            };
            let Some(recipe) = resolve_cliff_visual_recipe_v1(center, |dx, dy| {
                structural.structural_at(x + dx, y + dy)
            }) else {
                continue;
            };
            let host_level =
                haven_world::structural_level_for_surface_recipe_v1(&scene.map, x, y);
            let projection_visible = |target_x: i32, target_y: i32| {
                level_at(target_x, target_y).is_none_or(|level| level < host_level)
            };

            if !recipe.south_exposed {
                match (
                    recipe.north_exposed,
                    recipe.east_exposed,
                    recipe.west_exposed,
                ) {
                    (false, false, false) => {}
                    (true, false, false) => blit_structural_cell(
                        &mut target,
                        &cliff_source,
                        NORTH_LIP_CELL,
                        x,
                        y,
                        local_rect,
                    ),
                    (false, true, false) => blit_structural_cell(
                        &mut target,
                        &cliff_source,
                        EAST_EDGE_CELL,
                        x,
                        y,
                        local_rect,
                    ),
                    (false, false, true) => blit_structural_cell(
                        &mut target,
                        &cliff_source,
                        WEST_EDGE_CELL,
                        x,
                        y,
                        local_rect,
                    ),
                    (true, true, false) => blit_structural_cell(
                        &mut target,
                        &cliff_source,
                        NORTH_EAST_CORNER_CELL,
                        x,
                        y,
                        local_rect,
                    ),
                    (true, false, true) => blit_structural_cell(
                        &mut target,
                        &cliff_source,
                        NORTH_WEST_CORNER_CELL,
                        x,
                        y,
                        local_rect,
                    ),
                    (false, true, true) => {
                        if let Some(ridge_source) = ramp_source.as_ref() {
                            let role = LpcCliffContourStampRole::VerticalRidgeMiddle;
                            let stamp = role.source_stamp();
                            let (anchor_x, anchor_y) = role.host_anchor_offset();
                            let rect = haven_assets::asset_registry::AtlasRect {
                                x: stamp.column as f32 * 32.0,
                                y: stamp.row as f32 * 32.0,
                                w: stamp.width_cells as f32 * 32.0,
                                h: stamp.height_cells as f32 * 32.0,
                            };
                            let dx =
                                (x + i32::from(anchor_x) - local_rect.min.x) * 32;
                            let dy =
                                (y + i32::from(anchor_y) - local_rect.min.y) * 32;
                            let _ = blit_atlas_rect(
                                &mut target,
                                ridge_source,
                                rect,
                                dx,
                                dy,
                                u32::from(stamp.width_cells) * 32,
                                u32::from(stamp.height_cells) * 32,
                            );
                        }
                    }
                    (true, true, true) => {}
                }
                continue;
            }

            if recipe.north_exposed {
                blit_structural_cell(
                    &mut target,
                    &cliff_source,
                    NORTH_LIP_CELL,
                    x,
                    y,
                    local_rect,
                );
            }

            let body_rows = authored_body_rows(recipe.south_face_segments.max(1));
            match recipe.visual_shape {
                CliffVisualShape::SouthWestDiagonal if recipe.west_exposed => {
                    blit_structural_cell(
                        &mut target,
                        &cliff_source,
                        SOUTH_WEST_DIAGONAL_FACE.crest,
                        x,
                        y,
                        local_rect,
                    );
                    for row in 0..body_rows {
                        let target_y = y + 1 + row as i32;
                        if projection_visible(x - 1, target_y) {
                            blit_structural_cell(
                                &mut target,
                                &cliff_source,
                                SOUTH_WEST_DIAGONAL_FACE.body,
                                x,
                                target_y,
                                local_rect,
                            );
                        }
                    }
                    let foot_y = y + 1 + body_rows as i32;
                    if projection_visible(x - 1, foot_y) {
                        blit_structural_cell(
                            &mut target,
                            &cliff_source,
                            SOUTH_WEST_DIAGONAL_FACE.foot,
                            x,
                            foot_y,
                            local_rect,
                        );
                    }
                }
                CliffVisualShape::SouthEastDiagonal if recipe.east_exposed => {
                    blit_structural_cell(
                        &mut target,
                        &cliff_source,
                        SOUTH_EAST_DIAGONAL_FACE.crest,
                        x,
                        y,
                        local_rect,
                    );
                    for row in 0..body_rows {
                        let target_y = y + 1 + row as i32;
                        if projection_visible(x + 1, target_y) {
                            blit_structural_cell(
                                &mut target,
                                &cliff_source,
                                SOUTH_EAST_DIAGONAL_FACE.body,
                                x,
                                target_y,
                                local_rect,
                            );
                        }
                    }
                    let foot_y = y + 1 + body_rows as i32;
                    if projection_visible(x + 1, foot_y) {
                        blit_structural_cell(
                            &mut target,
                            &cliff_source,
                            SOUTH_EAST_DIAGONAL_FACE.foot,
                            x,
                            foot_y,
                            local_rect,
                        );
                    }
                }
                CliffVisualShape::SouthAuthoredTerminal
                    if recipe.east_exposed && recipe.west_exposed =>
                {
                    let mut draw_row = |row: &[Rect; 3], target_y: i32| {
                        for (column, source_rect) in row.iter().copied().enumerate() {
                            let target_x = x + column as i32 - 1;
                            if target_y == y || projection_visible(target_x, target_y) {
                                blit_structural_cell(
                                    &mut target,
                                    &cliff_source,
                                    source_rect,
                                    target_x,
                                    target_y,
                                    local_rect,
                                );
                            }
                        }
                    };
                    draw_row(&SOUTH_TERMINAL_CREST_ROW, y);
                    for row in 0..body_rows {
                        draw_row(&SOUTH_TERMINAL_BODY_ROW, y + 1 + row as i32);
                    }
                    draw_row(&SOUTH_TERMINAL_FOOT_ROW, y + 1 + body_rows as i32);
                }
                _ => {
                    if let Some(crest) = SOUTH_STRAIGHT_FACE.leading {
                        blit_structural_cell(
                            &mut target,
                            &cliff_source,
                            crest,
                            x,
                            y,
                            local_rect,
                        );
                    }
                    for row in 0..body_rows {
                        let target_y = y + 1 + row as i32;
                        if projection_visible(x, target_y) {
                            blit_structural_cell(
                                &mut target,
                                &cliff_source,
                                SOUTH_STRAIGHT_FACE.body,
                                x,
                                target_y,
                                local_rect,
                            );
                        }
                    }
                    let foot_y = y + 1 + body_rows as i32;
                    if projection_visible(x, foot_y) {
                        blit_structural_cell(
                            &mut target,
                            &cliff_source,
                            SOUTH_STRAIGHT_FACE.foot,
                            x,
                            foot_y,
                            local_rect,
                        );
                    }
                }
            }
        }
    }
    target
}

fn blit_structural_cell(
    target: &mut RgbaImage,
    source: &DynamicImage,
    rect: Rect,
    world_x: i32,
    world_y: i32,
    local_rect: GridRect,
) {
    let atlas_rect = haven_assets::asset_registry::AtlasRect {
        x: rect.x,
        y: rect.y,
        w: rect.w,
        h: rect.h,
    };
    let dx = (world_x - local_rect.min.x) * 32;
    let dy = (world_y - local_rect.min.y) * 32;
    let _ = blit_atlas_rect(target, source, atlas_rect, dx, dy, 32, 32);
}

fn resolved_published_source_path(
    definition: &haven_assets::placeable_asset_registry::PublishedWorldAssetDefinition,
) -> Option<PathBuf> {
    definition.source_path.clone().or_else(|| {
        definition
            .provenance
            .source_path
            .as_deref()
            .map(resolve_project_path)
    })
}

fn resolve_project_path(path: &str) -> PathBuf {
    let candidate = std::path::Path::new(path);
    if candidate.is_absolute() {
        candidate.to_path_buf()
    } else {
        haven_assets::asset_intake::repo_root_dir().join(candidate)
    }
}

fn ensure_source(cache: &mut HashMap<PathBuf, DynamicImage>, path: &PathBuf) {
    if !cache.contains_key(path) {
        if let Ok(image) = image::open(path) {
            cache.insert(path.clone(), image);
        }
    }
}

fn rects_intersect(a: GridRect, b: GridRect) -> bool {
    a.min.x <= b.max.x && a.max.x >= b.min.x && a.min.y <= b.max.y && a.max.y >= b.min.y
}

fn blit_atlas_rect(
    target: &mut RgbaImage,
    source: &DynamicImage,
    rect: haven_assets::asset_registry::AtlasRect,
    dx: i32,
    dy: i32,
    dw: u32,
    dh: u32,
) -> bool {
    let sx = rect.x.max(0.0) as u32;
    let sy = rect.y.max(0.0) as u32;
    let sw = rect.w.max(0.0) as u32;
    let sh = rect.h.max(0.0) as u32;
    if sw == 0 || sh == 0 || sx + sw > source.width() || sy + sh > source.height() {
        return false;
    }
    let cropped = source.crop_imm(sx, sy, sw, sh).resize_exact(dw, dh, FilterType::Nearest).to_rgba8();
    alpha_blit(target, &cropped, dx, dy);
    true
}

fn alpha_blit(target: &mut RgbaImage, source: &RgbaImage, dx: i32, dy: i32) {
    for sy in 0..source.height() {
        for sx in 0..source.width() {
            let tx = dx + sx as i32;
            let ty = dy + sy as i32;
            if tx < 0 || ty < 0 || tx >= target.width() as i32 || ty >= target.height() as i32 {
                continue;
            }
            let src = source.get_pixel(sx, sy).0;
            if src[3] == 0 { continue; }
            let dst = target.get_pixel(tx as u32, ty as u32).0;
            let sa = src[3] as u32;
            let inv = 255 - sa;
            let out_a = sa + (dst[3] as u32 * inv + 127) / 255;
            let blend = |s: u8, d: u8| -> u8 {
                ((s as u32 * sa + d as u32 * inv + 127) / 255).min(255) as u8
            };
            target.put_pixel(tx as u32, ty as u32, Rgba([blend(src[0], dst[0]), blend(src[1], dst[1]), blend(src[2], dst[2]), out_a.min(255) as u8]));
        }
    }
}
