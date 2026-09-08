use super::*;
use crate::base_terrain_cache::BASE_TERRAIN_CHUNK_SIZE;
use crate::runtime_terrain_base_draw::TerrainBaseDrawRequest;
use crate::terrain_render::structural_cliff_top_presentation_tile;

use crate::runtime_terrain_plan::{
    color_span_lod_enabled, pixel_snapped_screen_origin, screen_position,
    world_paint_layers_active, VisibleTerrainCell,
};
pub(crate) use crate::runtime_terrain_plan::{SceneBackdropHeightCache, VisibleTerrainPlanCache};

impl Game {
    /// Render terrain from a retained per-view submission plan. Static terrain
    /// classification and water-span construction are rebuilt only when the
    /// visible tile bounds, scene, terrain revision, or paint revision change.
    pub(super) fn draw_map(&self) {
        if self.active_surface_chunk_coord().is_some() {
            self.draw_continuous_surface_terrain();
            return;
        }
        let preparation_started_at = get_time();
        let scene = self.world.active();
        let map = &scene.map;
        let mut base_terrain_cache = self.base_terrain_cache.borrow_mut();
        let base_cache_report =
            base_terrain_cache.synchronize(map, &self.terrain_cache, self.world.active().biome);
        let dirty_chunks = base_terrain_cache.last_dirty_chunks().to_vec();
        let retained_chunk_count = base_terrain_cache.retained_chunk_count();
        let retained_requested = self
            .chunk_surface_cache
            .borrow()
            .retained_execution_requested();
        if retained_requested {
            self.chunk_surface_cache.borrow_mut().synchronize(
                &dirty_chunks,
                BASE_TERRAIN_CHUNK_SIZE,
                MAP_W,
                MAP_H,
                &base_terrain_cache,
            );
        }

        self.draw_scene_backdrop();
        let local_camera_target = self.active_local_camera_target();
        let bounds =
            runtime_view_culling::visible_tile_bounds(local_camera_target, self.camera_zoom, 2, self.world.active().dimensions);
        let screen_origin = pixel_snapped_screen_origin(
            self.camera_target,
            vec2(screen_width(), screen_height()),
            self.camera_zoom,
        ) + self.active_surface_origin_px();
        let scene_id = self.world.active_scene.code();
        // Machine-local world-paint bindings are an editor/development overlay.
        // They must never override the committed semantic terrain in normal
        // gameplay, where stale paint caches previously produced square grass,
        // sand, and shallow-water blocks and disabled the retained terrain
        // surface. F3/build mode keeps the live editable overlay path.
        let paint_active = world_paint_layers_active(
            self.dev_mode,
            self.editor_tab,
            self.world_paint_render_bindings
                .has_drawable_scene_layers(scene_id),
        );
        let terrain_revision = self.terrain_cache.revision();

        // Normal gameplay uses one retained native-resolution terrain surface.
        // Editor/debug and world-paint modes keep the live per-cell path.
        let live_cell_editor_required = self.dev_mode
            && (paint_active
                || self.show_terrain_debug_overlay
                || matches!(self.editor_tab, EditorTab::Map | EditorTab::Zones));
        if self.draw_retained_terrain_scene_surface(
            map,
            &base_terrain_cache,
            scene_id,
            terrain_revision,
            screen_origin,
            live_cell_editor_required,
        ) {
            return;
        }

        let (min_x, min_y, max_x, max_y) = bounds;
        let width = (max_x - min_x + 1).max(0) as usize;
        let height = (max_y - min_y + 1).max(0) as usize;
        let desired_capacity = width.saturating_mul(height);

        let mut plan = self.visible_terrain_plan.borrow_mut();
        if plan.needs_rebuild(
            bounds,
            scene_id,
            terrain_revision,
            self.world_paint_edit_sequence,
            paint_active,
        ) {
            plan.begin_rebuild(
                bounds,
                scene_id,
                terrain_revision,
                self.world_paint_edit_sequence,
                paint_active,
                desired_capacity,
            );
            let visible_chunk_count =
                base_terrain_cache.for_each_visible_record(bounds, |x, y, cached| {
                    if !scene.is_renderable_cell(x, y) {
                        return;
                    }
                    let paint_owned = paint_active
                        && self
                            .world_paint_render_bindings
                            .has_drawable_layers(scene_id, x, y);
                    plan.cells.push(VisibleTerrainCell {
                        x,
                        y,
                        tile: cached.tile,
                        paint_owned,
                        resolved_group: cached.resolved_group,
                        resolved_mask: cached.resolved_mask,
                        has_transitions: cached
                            .transitions
                            .as_ref()
                            .is_some_and(ResolvedTerrainTransitions::has_any),
                        mapped_entry: cached.mapped_entry,
                        mapped_transition_entry: cached.mapped_transition_entry,
                    });
                });
            plan.finish_rebuild(visible_chunk_count);
        } else {
            plan.record_hit();
        }

        // Solid-color spans remain an emergency no-atlas fallback. The normal
        // production path always uses texture-backed mapped terrain.
        let wide_surface_lod = color_span_lod_enabled(
            self.camera_zoom,
            self.terrain_atlas.is_some()
                || self.lpc_terrain_source.is_some()
                || self.lpc_terrain_v7_source.is_some(),
            self.lpc_mapped_terrain_atlas.is_some(),
        );
        if wide_surface_lod {
            let mut index = 0usize;
            while index < plan.cells.len() {
                let cell = plan.cells[index];
                let flat_grass =
                    cell.tile == TileKind::Grass && !cell.paint_owned && !cell.has_transitions;
                if !flat_grass {
                    index += 1;
                    continue;
                }
                let mut span_end = index + 1;
                while span_end < plan.cells.len() {
                    let next = plan.cells[span_end];
                    if next.y != cell.y
                        || next.x != cell.x + (span_end - index) as i32
                        || next.tile != TileKind::Grass
                        || next.paint_owned
                        || next.has_transitions
                    {
                        break;
                    }
                    span_end += 1;
                }
                let screen = screen_position(cell, screen_origin);
                draw_rectangle(
                    screen.x,
                    screen.y,
                    TILE_SIZE * (span_end - index) as f32 + 0.20,
                    TILE_SIZE + 0.20,
                    tile_color(TileKind::Grass, cell.x, cell.y),
                );
                index = span_end;
            }
        }

        // The descriptor-retained lane is isolated behind an explicit
        // experimental variable. Normal gameplay uses the sorted frame plan.
        let retained_active = if retained_requested {
            let expected_visible_coordinates = plan
                .cells
                .iter()
                .map(|cell| (cell.x, cell.y))
                .collect::<Vec<_>>();
            let mut surfaces = self.chunk_surface_cache.borrow_mut();
            surfaces
                .for_each_visible_command(
                    bounds,
                    BASE_TERRAIN_CHUNK_SIZE,
                    &expected_visible_coordinates,
                    |command| {
                        let paint_owned = paint_active
                            && self.world_paint_render_bindings.has_drawable_layers(
                                scene_id,
                                command.world_x,
                                command.world_y,
                            );
                        let terrain = &command.terrain;
                        if paint_owned {
                            return;
                        }
                        if wide_surface_lod
                            && terrain.tile == TileKind::Grass
                            && terrain
                                .transitions
                                .as_ref()
                                .is_none_or(|transitions| !transitions.has_any())
                        {
                            return;
                        }
                        let screen = vec2(
                            command.world_x as f32 * TILE_SIZE + screen_origin.x,
                            command.world_y as f32 * TILE_SIZE + screen_origin.y,
                        );
                        self.draw_tile_base(TerrainBaseDrawRequest {
                            map,
                            tile: terrain.tile,
                            x: command.world_x,
                            y: command.world_y,
                            screen,
                            resolved_base: terrain
                                .resolved_group
                                .map(|group| (group, terrain.resolved_mask)),
                            mapped_entry: terrain.mapped_entry,
                            global: None,
                        });
                        if self.lpc_terrain_source.is_none()
                            && self.lpc_terrain_v7_source.is_none()
                            && self.terrain_atlas.is_none()
                            && !terrain.tile.is_water()
                        {
                            draw_tile_detail(
                                map,
                                terrain.tile,
                                command.world_x,
                                command.world_y,
                                screen.x,
                                screen.y,
                            );
                        }
                    },
                )
                .active
        } else {
            false
        };

        if !retained_active {
            for &index in &plan.base_indices {
                let cell = plan.cells[index];
                if wide_surface_lod && cell.tile == TileKind::Grass && !cell.has_transitions {
                    continue;
                }
                let screen = screen_position(cell, screen_origin);
                self.draw_tile_base(TerrainBaseDrawRequest {
                    map,
                    tile: cell.tile,
                    x: cell.x,
                    y: cell.y,
                    screen,
                    resolved_base: cell.resolved_group.map(|group| (group, cell.resolved_mask)),
                    mapped_entry: cell.mapped_entry,
                    global: None,
                });
                if self.lpc_terrain_source.is_none()
                    && self.lpc_terrain_v7_source.is_none()
                    && self.terrain_atlas.is_none()
                    && !cell.tile.is_water()
                {
                    draw_tile_detail(map, cell.tile, cell.x, cell.y, screen.x, screen.y);
                }
            }
        }

        for &index in &plan.paint_indices {
            let cell = plan.cells[index];
            let screen = screen_position(cell, screen_origin);
            self.draw_world_paint_atlas_layers_if_bound(
                scene_id, cell.x, cell.y, screen.x, screen.y,
            );
        }

        // Pure water cells are rendered from the same direct LPC source sheet
        // as land whenever that source is mounted. The shader/span backend is
        // retained only for compatibility mode. Both paths consume one bounded
        // animation budget so water motion degrades gracefully under pressure.
        let water_budget = self
            .terrain_render_telemetry
            .water_budget(self.camera_zoom, get_time() as f32);
        if self.lpc_terrain_source.is_some() || self.lpc_terrain_v7_source.is_some() {
            for cell in plan
                .cells
                .iter()
                .copied()
                .filter(|cell| cell.tile.is_water() && !cell.paint_owned)
            {
                let screen = screen_position(cell, screen_origin);
                self.draw_tile_base(TerrainBaseDrawRequest {
                    map,
                    tile: cell.tile,
                    x: cell.x,
                    y: cell.y,
                    screen,
                    resolved_base: cell.resolved_group.map(|group| (group, cell.resolved_mask)),
                    mapped_entry: cell.mapped_entry,
                    global: None,
                });
                self.water_material.draw_animation_overlay_tile(
                    cell.tile,
                    cell.x,
                    cell.y,
                    screen.x,
                    screen.y,
                    water_budget.animation_time,
                    haven_world::water_render_mask::resolve_water_render_mask(map, cell.x, cell.y),
                    water_budget.blend_layers(),
                );
            }
        }

        let mut water_shader_tiles = 0usize;
        let mut water_fallback_tiles = 0usize;
        let mut water_shader_submissions = 0usize;
        if self.lpc_terrain_source.is_none() && self.lpc_terrain_v7_source.is_none() {
            for span in &plan.water_spans {
                let cell = plan.cells[span.first_cell];
                let screen = screen_position(cell, screen_origin);
                if self.water_material.draw_interior_span(
                    span.render_kind,
                    cell.x,
                    cell.y,
                    screen.x,
                    screen.y,
                    span.tile_count,
                    water_budget.animation_time,
                ) {
                    water_shader_tiles += span.tile_count;
                    water_shader_submissions += 1;
                } else {
                    // Fail-safe compatibility lane: shader creation can fail on
                    // older/unsupported GPUs. Draw the semantic owner fill first,
                    // then layer the same bounded CPU water animation used by the
                    // normal LPC path. Never leave water blank and never paint a
                    // flat fallback over the animation afterward.
                    draw_rectangle(
                        screen.x,
                        screen.y,
                        TILE_SIZE * span.tile_count as f32 + 0.20,
                        TILE_SIZE + 0.20,
                        tile_color(span.render_kind, cell.x, cell.y),
                    );
                    for offset in 0..span.tile_count {
                        let water_x = cell.x + offset as i32;
                        self.water_material.draw_animation_overlay_tile(
                            span.render_kind,
                            water_x,
                            cell.y,
                            screen.x + TILE_SIZE * offset as f32,
                            screen.y,
                            water_budget.animation_time,
                            haven_world::water_render_mask::resolve_water_render_mask(
                                map, water_x, cell.y,
                            ),
                            water_budget.blend_layers(),
                        );
                    }
                    water_fallback_tiles += span.tile_count;
                }
            }
        }
        let _water_material_counts = (
            water_shader_tiles,
            water_fallback_tiles,
            water_shader_submissions,
        );

        // Authored V7 corner tuples are intersection graphics. Draw them only
        // after every semantic owner fill is present, shifted half a tile down
        // and right to the exact four-cell intersection.
        for &index in &plan.mapped_tuple_indices {
            let cell = plan.cells[index];
            // Elevated MountainRock is presented through the grass-capped
            // ElizaWy structural family. Do not redraw its original V7 rock
            // tuple afterward or the incompatible gray/green seam returns.
            if self.runtime_terrain_presentation_tile(map, cell.tile, cell.x, cell.y, None) != cell.tile {
                continue;
            }
            let Some(entry) = cell.mapped_transition_entry else {
                continue;
            };
            let screen = screen_position(cell, screen_origin);
            self.draw_mapped_terrain_tuple_overlay(entry, screen);
        }

        // No generic or cross-style transition overlay is permitted in the
        // V7 certification lane. Exact tuples win; reviewed V7-only connector
        // tuples may bridge Gravel, Rock Ground and Mud without changing their
        // semantic owner fills. Other unsupported contacts remain diagnostic.
        let transition_cell_count = plan.transition_indices.len();
        // Keep the lower-level base-cache traversal diagnostics available for
        // development snapshots even though the frame plan now avoids calling
        // that traversal on every rendered frame.
        let _base_visible_index_cache = (
            base_terrain_cache.visible_cache_hits(),
            base_terrain_cache.visible_cache_rebuilds(),
            base_terrain_cache.visible_cached_cells(),
            base_terrain_cache.visible_cache_last_reason(),
        );

        self.terrain_render_telemetry.record(
            plan.cells.len(),
            plan.visible_chunk_count,
            retained_chunk_count,
            base_cache_report.rebuilt_chunks,
            base_cache_report.rebuilt_cells,
            plan.hits,
            plan.rebuilds,
            plan.cells.len(),
            plan.last_reason,
            transition_cell_count,
            water_shader_tiles,
            water_shader_submissions,
            get_time() - preparation_started_at,
        );

        for &index in &plan.greenhouse_indices {
            let cell = plan.cells[index];
            let screen = screen_position(cell, screen_origin);
            draw_rectangle_lines(
                screen.x + 3.0,
                screen.y + 3.0,
                TILE_SIZE - 6.0,
                TILE_SIZE - 6.0,
                2.0,
                Color::from_rgba(143, 239, 132, 220),
            );
        }

        // Do not scan all visible cells for debug overlays during normal play.
        if self.dev_mode {
            for cell in plan.cells.iter().copied() {
                let screen = screen_position(cell, screen_origin);
                if self.show_terrain_debug_overlay {
                    draw_tile_border(map, cell.tile, cell.x, cell.y, screen.x, screen.y);
                }
                if self.editor_tab == EditorTab::Zones {
                    let zone = self.world.active().zone_at(cell.x, cell.y);
                    if zone != ZoneKind::None {
                        draw_rectangle(
                            screen.x + 4.0,
                            screen.y + 4.0,
                            TILE_SIZE - 8.0,
                            TILE_SIZE - 8.0,
                            zone_color(zone),
                        );
                    }
                }
                if self.editor_tab == EditorTab::Map {
                    let contour_alpha = (map.get_height(cell.x, cell.y) as f32 / 100.0) * 0.22;
                    draw_rectangle(
                        screen.x + 2.0,
                        screen.y + 2.0,
                        TILE_SIZE - 4.0,
                        TILE_SIZE - 4.0,
                        Color::new(1.0, 1.0, 1.0, contour_alpha * 0.25),
                    );
                }
            }
        }
    }

    /// Draws the visible exterior as one global terrain grid.
    ///
    /// PCG scene maps are storage partitions only. Every visible tile is routed
    /// through global surface coordinates, and V7 tuple sampling can read the
    /// four semantic cells that meet at a partition boundary. This removes the
    /// active-scene/neighbor split that previously produced hard seams and
    /// made the surface appear to change rooms while crossing a chunk edge.
    fn draw_continuous_surface_terrain(&self) {
        let manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
        let viewport = vec2(screen_width().max(1.0), screen_height().max(1.0));
        let half_visible = viewport / self.camera_zoom.max(0.01) * 0.5;
        let min_x = ((self.camera_target.x - half_visible.x) / TILE_SIZE).floor() as i32 - 2;
        let min_y = ((self.camera_target.y - half_visible.y) / TILE_SIZE).floor() as i32 - 2;
        let max_x = ((self.camera_target.x + half_visible.x) / TILE_SIZE).ceil() as i32 + 2;
        let max_y = ((self.camera_target.y + half_visible.y) / TILE_SIZE).ceil() as i32 + 2;

        let water_budget = self
            .terrain_render_telemetry
            .water_budget(self.camera_zoom, get_time() as f32);
        // H20V2B4: the continuous-surface path previously ignored the wide
        // camera LOD used by the older local terrain path. At maximum zoom-out
        // that made every visible cell pay the full LPC tuple/transition cost.
        // Keep authored base tiles, routes, water, cliffs and actors visible,
        // but defer tuple overlays and use one animated water layer when their
        // detail is below the useful screen scale.
        let wide_surface_lod = self.camera_zoom <= 0.95;
        let water_blend_layers = if wide_surface_lod {
            1
        } else {
            water_budget.blend_layers()
        };
        let scenes_by_chunk = manifest
            .exterior_bindings
            .iter()
            .filter_map(|binding| {
                self.world
                    .scene_by_id(&binding.scene_id)
                    .map(|scene| (binding.chunk, scene))
            })
            .collect::<std::collections::BTreeMap<_, _>>();
        let tile_at = |global_x: i32, global_y: i32| {
            let address = haven_world::surface_tile_address(
                haven_world::open_world::WorldTileCoord::new(global_x, global_y),
            );
            scenes_by_chunk.get(&address.chunk).map(|scene| {
                let tile = scene.map.get(address.local_x, address.local_y);
                let structural = structural_cliff_top_presentation_tile(
                    &scene.map,
                    tile,
                    address.local_x,
                    address.local_y,
                );
                if tile == TileKind::MountainPath
                    && self.surface_authored_ramp_owner(global_x, global_y).is_some()
                {
                    TileKind::Grass
                } else {
                    structural
                }
            })
        };

        let mut tuple_overlays = Vec::new();
        for global_y in min_y..=max_y {
            for global_x in min_x..=max_x {
                let address = haven_world::surface_tile_address(
                    haven_world::open_world::WorldTileCoord::new(global_x, global_y),
                );
                let Some(scene) = scenes_by_chunk.get(&address.chunk).copied() else {
                    continue;
                };
                if scene.kind != SceneKind::Exterior {
                    continue;
                }
                let tile = scene.map.get(address.local_x, address.local_y);
                let screen = self.runtime_world_to_screen(vec2(
                    global_x as f32 * TILE_SIZE,
                    global_y as f32 * TILE_SIZE,
                ));
                let mapped_entry = if wide_surface_lod {
                    None
                } else {
                    lpc_mapped_terrain_runtime_entry_for_tile_sampler(
                        &tile_at,
                        global_x,
                        global_y,
                    )
                };
                self.draw_tile_base(TerrainBaseDrawRequest {
                    map: &scene.map,
                    tile,
                    x: address.local_x,
                    y: address.local_y,
                    screen,
                    resolved_base: None,
                    mapped_entry,
                    global: Some((global_x, global_y)),
                });
                if tile.is_water() {
                    // Compatibility owner fill must be underneath the animation.
                    // draw_tile_base intentionally leaves no-atlas water to this
                    // lane, so paint the semantic fallback before adding glints.
                    if mapped_entry.is_none()
                        && self.lpc_terrain_source.is_none()
                        && self.lpc_terrain_v7_source.is_none()
                        && self.terrain_atlas.is_none()
                    {
                        draw_rectangle(
                            screen.x,
                            screen.y,
                            TILE_SIZE,
                            TILE_SIZE,
                            tile_color(tile, global_x, global_y),
                        );
                    }
                    let mut mask = haven_world::water_render_mask::WaterRenderMask::default();
                    for (dx, dy, bit) in [
                        (0, -1, haven_world::water_render_mask::WATER_MASK_NORTH),
                        (1, 0, haven_world::water_render_mask::WATER_MASK_EAST),
                        (0, 1, haven_world::water_render_mask::WATER_MASK_SOUTH),
                        (-1, 0, haven_world::water_render_mask::WATER_MASK_WEST),
                    ] {
                        if tile_at(global_x + dx, global_y + dy).is_some_and(|neighbor| !neighbor.is_water()) {
                            mask.shoreline_edges |= bit;
                        }
                    }
                    self.water_material.draw_animation_overlay_tile(
                        tile,
                        global_x,
                        global_y,
                        screen.x,
                        screen.y,
                        water_budget.animation_time,
                        mask,
                        water_blend_layers,
                    );
                }
                if self.dev_mode && self.editor_tab == EditorTab::Paint {
                    self.draw_world_paint_atlas_layers_if_bound(
                        scene.id.code(),
                        address.local_x,
                        address.local_y,
                        screen.x,
                        screen.y,
                    );
                }
                if self.lpc_terrain_source.is_none()
                    && self.lpc_terrain_v7_source.is_none()
                    && self.terrain_atlas.is_none()
                    && !tile.is_water()
                {
                    draw_tile_detail(
                        &scene.map,
                        tile,
                        address.local_x,
                        address.local_y,
                        screen.x,
                        screen.y,
                    );
                }
                if !wide_surface_lod
                    && self.runtime_terrain_presentation_tile(
                        &scene.map,
                        tile,
                        address.local_x,
                        address.local_y,
                        Some((global_x, global_y)),
                    ) == tile
                {
                    if let Some(entry) = lpc_mapped_terrain_transition_entry_for_tile_sampler(
                        &tile_at, global_x, global_y,
                    ) {
                        tuple_overlays.push((entry, screen));
                    }
                }

                if self.dev_mode {
                    if self.show_terrain_debug_overlay {
                        draw_tile_border(
                            &scene.map,
                            tile,
                            address.local_x,
                            address.local_y,
                            screen.x,
                            screen.y,
                        );
                    }
                    if self.editor_tab == EditorTab::Zones {
                        let zone = scene.zone_at(address.local_x, address.local_y);
                        if zone != ZoneKind::None {
                            draw_rectangle(
                                screen.x + 4.0,
                                screen.y + 4.0,
                                TILE_SIZE - 8.0,
                                TILE_SIZE - 8.0,
                                zone_color(zone),
                            );
                        }
                    }
                    if self.editor_tab == EditorTab::Map {
                        let contour_alpha =
                            (scene.map.get_height(address.local_x, address.local_y) as f32 / 100.0)
                                * 0.22;
                        draw_rectangle(
                            screen.x + 2.0,
                            screen.y + 2.0,
                            TILE_SIZE - 4.0,
                            TILE_SIZE - 4.0,
                            Color::new(1.0, 1.0, 1.0, contour_alpha * 0.25),
                        );
                    }
                }
            }
        }

        for (entry, screen) in tuple_overlays {
            self.draw_mapped_terrain_tuple_overlay(entry, screen);
        }
    }

    pub(super) fn draw_scene_backdrop(&self) {
        let scene = self.world.active();
        if scene.kind != SceneKind::Exterior {
            return;
        }
        let map = &scene.map;
        let base = self.world_to_screen(Vec2::ZERO);
        let horizon_y = base.y + 110.0;
        let backdrop_color = match scene.biome {
            SceneBiome::Coastal => Color::from_rgba(108, 148, 188, 104),
            SceneBiome::Highlands => Color::from_rgba(104, 115, 138, 110),
            _ => Color::from_rgba(98, 128, 112, 88),
        };
        let (min_x, _, max_x, _) = runtime_view_culling::visible_tile_bounds(
            self.active_local_camera_target(),
            self.camera_zoom,
            4,
            self.world.active().dimensions,
        );
        let now = get_time();
        let scene_code = self.world.active_scene.code();
        let mut height_cache = self.scene_backdrop_height_cache.borrow_mut();
        if height_cache.scene_code != scene_code
            || height_cache.max_heights.len() != MAP_W
            || now >= height_cache.next_refresh_at
        {
            height_cache.scene_code.clear();
            height_cache.scene_code.push_str(scene_code);
            height_cache.max_heights.clear();
            height_cache.max_heights.reserve(MAP_W);
            for x in 0..MAP_W as i32 {
                height_cache.max_heights.push(
                    (0..MAP_H as i32)
                        .map(|y| map.get_height(x, y))
                        .max()
                        .unwrap_or_default(),
                );
            }
            height_cache.next_refresh_at = now + 1.0;
        }
        for x in (min_x.max(0)..=max_x.min(MAP_W as i32 - 1)).step_by(2) {
            let max_height = height_cache.max_heights[x as usize];
            if max_height < self.map_mountain_level.saturating_sub(10) as u8 {
                continue;
            }
            let column = self.world_to_screen(vec2(x as f32 * TILE_SIZE, 0.0));
            let peak_y =
                horizon_y - (max_height as f32 - self.map_mountain_level as f32 + 18.0) * 3.6;
            draw_triangle(
                vec2(column.x - 36.0, horizon_y + 34.0),
                vec2(column.x + 36.0, horizon_y + 34.0),
                vec2(column.x, peak_y),
                backdrop_color,
            );
        }
    }
}
