impl Game {
    /// Reveal the actual live surface around the player. Discovery is cell based,
    /// not partition based: crossing a 96x96 storage boundary must never reveal a
    /// giant rectangular map block. The same baked structural cache used by the
    /// cliff renderer supplies map cliff marks, so M cannot advertise a cliff
    /// that the runtime structural renderer does not currently know about.
    pub(super) fn capture_active_world_map_chunk(&mut self) {
        self.capture_active_world_map_chunk_impl(true);
    }

    /// Movement-time discovery capture. The reveal radius is much larger than
    /// one tile, so recomputing and serializing the same neighborhood every
    /// maintenance tick only creates frame spikes. Refresh when the player
    /// crosses the world-map sampling grid instead; explicit map-open rebuilds
    /// still force a capture through `capture_active_world_map_chunk`.
    pub(super) fn capture_active_world_map_chunk_if_moved(&mut self) {
        self.capture_active_world_map_chunk_impl(false);
    }

    fn capture_active_world_map_chunk_impl(&mut self, force: bool) {
        if self.world.active().kind != SceneKind::Exterior {
            return;
        }
        let center = self.surface_global_tile();
        let sample = (
            center.x.div_euclid(WORLD_MAP_SAMPLE_STEP),
            center.y.div_euclid(WORLD_MAP_SAMPLE_STEP),
        );
        if !force && self.world_map.last_capture_sample == Some(sample) {
            return;
        }
        self.world_map.last_capture_sample = Some(sample);

        let manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
        let radius = WORLD_MAP_REVEAL_RADIUS_TILES;
        let min_x = (center.x - radius).div_euclid(WORLD_MAP_SAMPLE_STEP) * WORLD_MAP_SAMPLE_STEP;
        let max_x = (center.x + radius).div_euclid(WORLD_MAP_SAMPLE_STEP) * WORLD_MAP_SAMPLE_STEP;
        let min_y = (center.y - radius).div_euclid(WORLD_MAP_SAMPLE_STEP) * WORLD_MAP_SAMPLE_STEP;
        let max_y = (center.y + radius).div_euclid(WORLD_MAP_SAMPLE_STEP) * WORLD_MAP_SAMPLE_STEP;
        let radius_sq = i64::from(radius) * i64::from(radius);
        let mut updates = Vec::new();

        let mut base_y = min_y;
        while base_y <= max_y {
            let mut base_x = min_x;
            while base_x <= max_x {
                let sample_center_x = base_x + WORLD_MAP_SAMPLE_STEP / 2;
                let sample_center_y = base_y + WORLD_MAP_SAMPLE_STEP / 2;
                let dx = i64::from(sample_center_x - center.x);
                let dy = i64::from(sample_center_y - center.y);
                if dx * dx + dy * dy <= radius_sq {
                    let address = haven_world::surface_tile_address(WorldTileCoord::new(base_x, base_y));
                    let col = (address.local_x / WORLD_MAP_SAMPLE_STEP) as usize;
                    let row = (address.local_y / WORLD_MAP_SAMPLE_STEP) as usize;
                    let index = row * WORLD_MAP_CHUNK_COLS + col;
                    let already_explored = self
                        .world_map
                        .explored_chunks
                        .get(&(address.chunk.x, address.chunk.y))
                        .and_then(|snapshot| snapshot.cells.get(index))
                        .is_some_and(|code| *code != WORLD_MAP_UNEXPLORED);
                    // Normal movement only resolves the newly exposed rim.
                    // Opening/rebuilding the map forces a resample so authored
                    // terrain edits can still refresh already-explored cells.
                    if force || !already_explored {
                        if let Some(code) = self.world_map_sample_code_global(&manifest, base_x, base_y) {
                            updates.push((address.chunk, col, row, code));
                        }
                    }
                }
                base_x += WORLD_MAP_SAMPLE_STEP;
            }
            base_y += WORLD_MAP_SAMPLE_STEP;
        }

        let mut changed = false;
        for (chunk, col, row, code) in updates {
            let snapshot = self
                .world_map
                .explored_chunks
                .entry((chunk.x, chunk.y))
                .or_insert_with(|| empty_world_map_chunk_snapshot(chunk));
            let index = row * snapshot.cols + col;
            if snapshot.cells.get(index).copied() != Some(code) {
                if let Some(cell) = snapshot.cells.get_mut(index) {
                    *cell = code;
                    changed = true;
                }
            }
        }
        if changed {
            // H21A14AB4: never perform filesystem writes on the movement frame.
            // Serialization remains bounded to the compact exploration cache;
            // directory creation and disk I/O are owned by the existing surface
            // persistence worker. This is especially important for development
            // worlds with a large explored-map history.
            if let Ok(bytes) = world_map_exploration_bytes(&self.world_map.explored_chunks) {
                let path = self.world_map.exploration_path.clone();
                let _ = self.queue_surface_background_bytes(path, bytes);
            }
        }
    }

    fn world_map_sample_code_global(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        base_x: i32,
        base_y: i32,
    ) -> Option<u8> {
        let mut selected = None;
        let mut selected_priority = 0_u8;
        for offset_y in 0..WORLD_MAP_SAMPLE_STEP {
            for offset_x in 0..WORLD_MAP_SAMPLE_STEP {
                let code = self.world_map_cell_code_global(
                    manifest,
                    base_x + offset_x,
                    base_y + offset_y,
                )?;
                let priority = world_map_code_priority(code);
                if priority >= selected_priority {
                    selected = Some(code);
                    selected_priority = priority;
                }
            }
        }
        selected
    }

    fn world_map_cell_code_global(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        global_x: i32,
        global_y: i32,
    ) -> Option<u8> {
        let address = haven_world::surface_tile_address(WorldTileCoord::new(global_x, global_y));
        let scene_id = manifest.scene_id_for_chunk(address.chunk);
        // Map/minimap semantics now consume the same canonical terrain recipe
        // that wraps semantic tile + persisted structural level + baked cliff
        // topology. Existing numeric exploration codes remain unchanged.
        if let Some(recipe) =
            self.surface_terrain_recipe_cell(&scene_id, address.local_x, address.local_y)
        {
            return Some(recipe.map_code());
        }
        self.world_map.development_reveal_all.then(|| {
            let profile = haven_world::GeographicGenerationProfile::from_world_creation(
                &self.world_creation_settings,
            );
            haven_world::sample_generated_surface_map_code(
                self.world_seed,
                global_x,
                global_y,
                profile,
            )
        })
    }

    pub(super) fn handle_world_map_input(&mut self) -> bool {
        if !self.world_map.open {
            if !self.controls.action_pressed(ControlAction::Map) {
                return false;
            }
            self.world_map.open = true;
            self.world_map.drag_last = None;
            self.tile_context_menu = None;
            self.rebuild_world_map_geographic_overview();
            self.fit_world_map_to_view();
            self.status_message =
                "World map opened: drag or WASD to pan, wheel to zoom, Home to fit".to_string();
            return true;
        }

        if self.controls.action_pressed(ControlAction::Map)
            || self.controls.action_pressed(ControlAction::Cancel)
            || self.controls.action_pressed(ControlAction::Pause)
        {
            self.world_map.open = false;
            self.world_map.drag_last = None;
            self.status_message = "World map closed".to_string();
            return true;
        }

        let viewport = world_map_viewport_rect();
        let mouse = vec2(mouse_position().0, mouse_position().1);
        let wheel = mouse_wheel().1;
        if wheel.abs() > f32::EPSILON && viewport.contains(mouse) {
            let before = self.world_map_screen_to_canvas(mouse, viewport);
            let factor = 1.18_f32.powf(wheel.clamp(-4.0, 4.0));
            self.world_map.zoom = (self.world_map.zoom * factor).clamp(0.005, 12.0);
            let center_screen = vec2(viewport.x + viewport.w * 0.5, viewport.y + viewport.h * 0.5);
            self.world_map.center = before - (mouse - center_screen) / self.world_map.zoom;
        }

        if is_mouse_button_pressed(MouseButton::Left) && viewport.contains(mouse) {
            self.world_map.drag_last = Some(mouse);
        }
        if is_mouse_button_down(MouseButton::Left) {
            if let Some(previous) = self.world_map.drag_last {
                let delta = mouse - previous;
                self.world_map.center -= delta / self.world_map.zoom.max(0.01);
                self.world_map.drag_last = Some(mouse);
            }
        } else {
            self.world_map.drag_last = None;
        }

        let pan_speed = 460.0 * get_frame_time() / self.world_map.zoom.max(0.005);
        let pan = self.controls.movement_vector();
        self.world_map.center += pan * pan_speed;
        if is_key_pressed(KeyCode::Home) {
            self.fit_world_map_to_view();
        }
        if is_key_pressed(KeyCode::R) {
            if let Some(player) = self.world_map_player_canvas_position() {
                self.world_map.center = player;
            }
        }
        true
    }

    pub(super) fn draw_world_map_overlay(&self) {
        if !self.world_map.open {
            return;
        }
        use crate::runtime_ui_theme::{draw_runtime_panel, ui_muted, ui_teal};
        draw_rectangle(0.0, 0.0, screen_width(), screen_height(), crate::runtime_ui_theme::ui_backdrop());
        let panel = world_map_panel_rect();
        let controls = format!(
            "{} / {} close · Drag/WASD pan · Wheel zoom · Home fit · R center player",
            self.controls.prompt_label(ControlAction::Map),
            self.controls.prompt_label(ControlAction::Cancel),
        );
        draw_runtime_panel(panel, "WORLD MAP", Some(&controls));

        let viewport = world_map_viewport_rect();
        draw_rectangle(
            viewport.x,
            viewport.y,
            viewport.w,
            viewport.h,
            Color::from_rgba(6, 13, 18, 255),
        );
        self.draw_archipelago_world_map(viewport);
        draw_rectangle_lines(
            viewport.x,
            viewport.y,
            viewport.w,
            viewport.h,
            1.0,
            ui_teal(),
        );

        let footer_y = panel.y + panel.h - 14.0;
        let player_tile = self.surface_global_tile();
        draw_text(
            &format!(
                "Player tile {},{}  |  map zoom {:.2}x  |  explored partitions {}  |  {}",
                player_tile.x,
                player_tile.y,
                self.world_map.zoom,
                self.world_map.explored_chunks.len(),
                if self.world_map.development_reveal_all {
                    "DEVELOPMENT LIVE WORLD LOD"
                } else {
                    "map expands as you explore"
                }
            ),
            panel.x + 22.0,
            footer_y,
            14.0,
            ui_muted(),
        );
    }

    pub(super) fn draw_player_centered_minimap(&self, rect: Rect) {
        let center_screen = vec2(rect.x + rect.w * 0.5, rect.y + rect.h * 0.5);
        let radius = (rect.w.min(rect.h) * 0.5).max(1.0);
        draw_circle(
            center_screen.x,
            center_screen.y,
            radius,
            Color::from_rgba(5, 12, 16, 255),
        );
        let cell_px = 3.0_f32;
        let cols = ((rect.w / cell_px).floor() as i32).max(5) | 1;
        let rows = ((rect.h / cell_px).floor() as i32).max(5) | 1;
        let half_cols = cols / 2;
        let half_rows = rows / 2;
        let grid_origin = vec2(
            rect.x + (rect.w - cols as f32 * cell_px) * 0.5,
            rect.y + (rect.h - rows as f32 * cell_px) * 0.5,
        );
        let clip_radius = (radius - cell_px * 0.70).max(1.0);
        let clip_radius_sq = clip_radius * clip_radius;
        let inside_circle = |col: i32, row: i32| {
            let px = grid_origin.x + (col as f32 + 0.5) * cell_px;
            let py = grid_origin.y + (row as f32 + 0.5) * cell_px;
            let dx = px - center_screen.x;
            let dy = py - center_screen.y;
            dx * dx + dy * dy <= clip_radius_sq
        };

        if self.active_surface_chunk_coord().is_some() {
            let center = self.surface_global_tile();
            let manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
            let scenes = loaded_surface_scene_map(&self.world, &manifest);
            for row in 0..rows {
                let global_y = center.y + row - half_rows;
                for col in 0..cols {
                    if !inside_circle(col, row) {
                        continue;
                    }
                    let global_x = center.x + col - half_cols;
                    let color = self
                        .world_map_cell_code_global(&manifest, global_x, global_y)
                        .map(explored_world_map_color)
                        .or_else(|| surface_tile_at(&scenes, global_x, global_y).map(world_map_tile_color))
                        .unwrap_or(Color::from_rgba(7, 18, 28, 255));
                    draw_rectangle(
                        grid_origin.x + col as f32 * cell_px,
                        grid_origin.y + row as f32 * cell_px,
                        cell_px.ceil(),
                        cell_px.ceil(),
                        color,
                    );
                }
            }
            draw_minimap_natural_objects(
                &scenes,
                center,
                half_cols,
                half_rows,
                grid_origin,
                cell_px,
                center_screen,
                clip_radius,
            );
        } else {
            let center_x = (self.player.x / TILE_SIZE).floor() as i32;
            let center_y = (self.player.y / TILE_SIZE).floor() as i32;
            let map = &self.world.active().map;
            for row in 0..rows {
                let local_y = center_y + row - half_rows;
                for col in 0..cols {
                    if !inside_circle(col, row) {
                        continue;
                    }
                    let local_x = center_x + col - half_cols;
                    let color = TavernMap::idx(local_x, local_y)
                        .map(|_| world_map_tile_color(map.get(local_x, local_y)))
                        .unwrap_or(Color::from_rgba(4, 8, 10, 255));
                    draw_rectangle(
                        grid_origin.x + col as f32 * cell_px,
                        grid_origin.y + row as f32 * cell_px,
                        cell_px.ceil(),
                        cell_px.ceil(),
                        color,
                    );
                }
            }
        }

        let marker = center_screen;
        draw_circle(
            marker.x,
            marker.y,
            3.5,
            Color::from_rgba(255, 231, 126, 255),
        );
        draw_circle_lines(
            marker.x,
            marker.y,
            5.5,
            1.0,
            Color::from_rgba(35, 29, 18, 255),
        );
        draw_circle_lines(
            center_screen.x,
            center_screen.y,
            radius,
            1.0,
            Color::from_rgba(91, 113, 105, 255),
        );
        // The production minimap frame owns the north marker. Keeping the
        // map renderer free of duplicate chrome lets the same circular map be
        // reused behind alternate HUD skins.
    }

    fn fit_world_map_to_view(&mut self) {
        let viewport = world_map_viewport_rect();
        if !self.world_map.development_reveal_all {
            if let Some((min_x, min_y, max_x, max_y)) =
                explored_world_map_bounds(&self.world_map.explored_chunks)
            {
                let width = (max_x - min_x).max(1) as f32;
                let height = (max_y - min_y).max(1) as f32;
                self.world_map.center =
                    vec2(min_x as f32 + width * 0.5, min_y as f32 + height * 0.5);
                self.world_map.zoom = ((viewport.w / width).min(viewport.h / height) * 0.92)
                    .clamp(0.005, 12.0);
                return;
            }
        }
        if let Some(overview) = &self.world_map.overview {
            self.world_map.center = vec2(
                overview.origin_x as f32 + overview.span_w as f32 * 0.5,
                overview.origin_y as f32 + overview.span_h as f32 * 0.5,
            );
            self.world_map.zoom = ((viewport.w / overview.span_w.max(1) as f32)
                .min(viewport.h / overview.span_h.max(1) as f32)
                * 0.92)
                .clamp(0.005, 12.0);
            return;
        }
        if let Some(manifest) = &self.world_map.manifest {
            let width = manifest.archipelago_generation.canvas_size_px[0].max(1) as f32;
            let height = manifest.archipelago_generation.canvas_size_px[1].max(1) as f32;
            self.world_map.center = vec2(width * 0.5, height * 0.5);
            self.world_map.zoom =
                ((viewport.w / width).min(viewport.h / height) * 0.92).clamp(0.005, 12.0);
            return;
        }
        let player = self.surface_global_tile();
        self.world_map.center = vec2(player.x as f32, player.y as f32);
        self.world_map.zoom = 4.0;
    }

    fn world_map_screen_to_canvas(&self, screen: Vec2, viewport: Rect) -> Vec2 {
        let center_screen = vec2(viewport.x + viewport.w * 0.5, viewport.y + viewport.h * 0.5);
        self.world_map.center + (screen - center_screen) / self.world_map.zoom.max(0.01)
    }

    fn world_map_canvas_to_screen(&self, canvas: Vec2, viewport: Rect) -> Vec2 {
        let center_screen = vec2(viewport.x + viewport.w * 0.5, viewport.y + viewport.h * 0.5);
        center_screen + (canvas - self.world_map.center) * self.world_map.zoom
    }

    fn draw_archipelago_world_map(&self, viewport: Rect) {
        if !self.world_map.development_reveal_all && !self.world_map.explored_chunks.is_empty() {
            self.draw_explored_world_map(viewport);
            if let Some(player) = self.world_map_player_canvas_position() {
                let screen = self.world_map_canvas_to_screen(player, viewport);
                if viewport.contains(screen) {
                    draw_circle(screen.x, screen.y, 6.0, Color::from_rgba(255, 230, 119, 255));
                    draw_circle_lines(screen.x, screen.y, 8.0, 2.0, Color::from_rgba(35, 27, 15, 255));
                }
            }
            return;
        }
        if let Some(overview) = &self.world_map.overview {
            self.draw_geographic_world_map(overview, viewport);
            // Exact discovered/live cells refine the production LOD cache.
            // This keeps roads, edited terrain, bridges and baked cliff roles
            // faithful where the runtime has authoritative SurfaceTerrainRecipe
            // data instead of replacing them with coarse world-scale samples.
            if !self.world_map.explored_chunks.is_empty() {
                self.draw_explored_world_map(viewport);
            }
            if let Some(player) = self.world_map_player_canvas_position() {
                let screen = self.world_map_canvas_to_screen(player, viewport);
                if viewport.contains(screen) {
                    draw_circle(screen.x, screen.y, 6.0, Color::from_rgba(255, 230, 119, 255));
                    draw_circle_lines(screen.x, screen.y, 8.0, 2.0, Color::from_rgba(35, 27, 15, 255));
                }
            }
            return;
        }
        let Some(manifest) = &self.world_map.manifest else {
            self.draw_active_surface_world_map(viewport);
            return;
        };

        let canvas_size = vec2(
            manifest.archipelago_generation.canvas_size_px[0].max(1) as f32,
            manifest.archipelago_generation.canvas_size_px[1].max(1) as f32,
        );
        let canvas_origin = self.world_map_canvas_to_screen(Vec2::ZERO, viewport);
        let canvas_rect = Rect::new(
            canvas_origin.x,
            canvas_origin.y,
            canvas_size.x * self.world_map.zoom,
            canvas_size.y * self.world_map.zoom,
        );
        if let Some(clipped) = rect_intersection(canvas_rect, viewport) {
            draw_rectangle(
                clipped.x,
                clipped.y,
                clipped.w,
                clipped.h,
                Color::from_rgba(8, 27, 42, 255),
            );
        }

        for scene in &self.world.scenes {
            if scene.kind != SceneKind::Exterior {
                continue;
            }
            let Some((region, chunk)) = haven_world::parse_pcg_surface_scene_id(&scene.id) else {
                continue;
            };
            let Some(spec) = find_rectangle_spec(manifest, &region, chunk) else {
                continue;
            };
            self.draw_scene_on_archipelago_map(scene, spec, viewport);
        }

        if let Some(player) = self.world_map_player_canvas_position() {
            let screen = self.world_map_canvas_to_screen(player, viewport);
            if viewport.contains(screen) {
                draw_circle(
                    screen.x,
                    screen.y,
                    6.0,
                    Color::from_rgba(255, 230, 119, 255),
                );
                draw_circle_lines(
                    screen.x,
                    screen.y,
                    8.0,
                    2.0,
                    Color::from_rgba(35, 27, 15, 255),
                );
            }
        }
    }

    fn draw_explored_world_map(&self, viewport: Rect) {
        let cell_world = WORLD_MAP_SAMPLE_STEP as f32;
        for snapshot in self.world_map.explored_chunks.values() {
            let chunk_origin_x = snapshot.chunk_x * MAP_W as i32;
            let chunk_origin_y = snapshot.chunk_y * MAP_H as i32;
            for row in 0..snapshot.rows {
                let mut col = 0usize;
                while col < snapshot.cols {
                    let code = snapshot.cells[row * snapshot.cols + col];
                    let mut run_end = col + 1;
                    while run_end < snapshot.cols
                        && snapshot.cells[row * snapshot.cols + run_end] == code
                    {
                        run_end += 1;
                    }
                    if code != WORLD_MAP_UNEXPLORED {
                        let world_x = chunk_origin_x as f32 + col as f32 * cell_world;
                        let world_y = chunk_origin_y as f32 + row as f32 * cell_world;
                        let top_left = self.world_map_canvas_to_screen(vec2(world_x, world_y), viewport);
                        let run_rect = Rect::new(
                            top_left.x,
                            top_left.y,
                            (run_end - col) as f32 * cell_world * self.world_map.zoom + 0.75,
                            cell_world * self.world_map.zoom + 0.75,
                        );
                        if let Some(clipped) = rect_intersection(run_rect, viewport) {
                            draw_rectangle(
                                clipped.x,
                                clipped.y,
                                clipped.w,
                                clipped.h,
                                explored_world_map_color(code),
                            );
                        }
                    }
                    col = run_end;
                }
            }
        }
    }

    fn draw_geographic_world_map(&self, overview: &WorldMapOverview, viewport: Rect) {
        let cell_w = overview.span_w as f32 / overview.cols.max(1) as f32;
        let cell_h = overview.span_h as f32 / overview.rows.max(1) as f32;
        for row in 0..overview.rows {
            let mut col = 0usize;
            while col < overview.cols {
                let code = overview.cells[row * overview.cols + col];
                let mut run_end = col + 1;
                while run_end < overview.cols
                    && overview.cells[row * overview.cols + run_end] == code
                {
                    run_end += 1;
                }
                let world_x = overview.origin_x as f32 + col as f32 * cell_w;
                let world_y = overview.origin_y as f32 + row as f32 * cell_h;
                let top_left = self.world_map_canvas_to_screen(vec2(world_x, world_y), viewport);
                let run_rect = Rect::new(
                    top_left.x,
                    top_left.y,
                    (run_end - col) as f32 * cell_w * self.world_map.zoom + 0.75,
                    cell_h * self.world_map.zoom + 0.75,
                );
                if let Some(clipped) = rect_intersection(run_rect, viewport) {
                    draw_rectangle(
                        clipped.x,
                        clipped.y,
                        clipped.w,
                        clipped.h,
                        geographic_overview_color(code),
                    );
                }
                col = run_end;
            }
        }
    }

    fn draw_scene_on_archipelago_map(
        &self,
        scene: &SceneMap,
        spec: &SceneRectangleSpec,
        viewport: Rect,
    ) {
        let [preview_x, preview_y, preview_w, preview_h] = spec.world_rect_preview_px;
        let top_left =
            self.world_map_canvas_to_screen(vec2(preview_x as f32, preview_y as f32), viewport);
        let cell_w = preview_w as f32 / MAP_W as f32 * self.world_map.zoom;
        let cell_h = preview_h as f32 / MAP_H as f32 * self.world_map.zoom;
        if cell_w <= 0.0 || cell_h <= 0.0 {
            return;
        }
        let scene_rect = Rect::new(
            top_left.x,
            top_left.y,
            preview_w as f32 * self.world_map.zoom,
            preview_h as f32 * self.world_map.zoom,
        );
        if !rects_intersect(scene_rect, viewport) {
            return;
        }

        let x_step = (0.8 / cell_w).ceil().max(1.0) as i32;
        let y_step = (0.8 / cell_h).ceil().max(1.0) as i32;
        let mut y = 0_i32;
        while y < MAP_H as i32 {
            let screen_y = top_left.y + y as f32 * cell_h;
            let mut x = 0_i32;
            while x < MAP_W as i32 {
                let tile = scene.map.get(x, y);
                let color = world_map_tile_color(tile);
                let mut run_end = x + x_step;
                while run_end < MAP_W as i32
                    && scene.map.get(run_end, y) == tile
                    && run_end - x < 24
                {
                    run_end += x_step;
                }
                run_end = run_end.min(MAP_W as i32);
                let run_rect = Rect::new(
                    top_left.x + x as f32 * cell_w,
                    screen_y,
                    (run_end - x) as f32 * cell_w,
                    y_step as f32 * cell_h,
                );
                if let Some(clipped) = rect_intersection(run_rect, viewport) {
                    draw_rectangle(
                        clipped.x,
                        clipped.y,
                        clipped.w.ceil(),
                        clipped.h.ceil(),
                        color,
                    );
                }
                x = run_end;
            }
            y += y_step;
        }

        if cell_w.max(cell_h) >= 0.8 {
            for object in &scene.map.objects {
                if !matches!(
                    object.kind,
                    ObjectKind::Tree | ObjectKind::Bush | ObjectKind::Mushroom | ObjectKind::Herb
                ) {
                    continue;
                }
                let object_screen = vec2(
                    top_left.x + (object.x as f32 + 0.5) * cell_w,
                    top_left.y + (object.y as f32 + 0.5) * cell_h,
                );
                if !viewport.contains(object_screen) {
                    continue;
                }
                let Some(color) = natural_object_map_color(object.kind) else {
                    continue;
                };
                draw_circle(
                    object_screen.x,
                    object_screen.y,
                    1.5_f32.max(cell_w * 0.35),
                    color,
                );
            }
        }
    }

    fn world_map_player_canvas_position(&self) -> Option<Vec2> {
        if !self.world_map.explored_chunks.is_empty() {
            let player = self.surface_global_tile();
            return Some(vec2(player.x as f32 + 0.5, player.y as f32 + 0.5));
        }
        if self.world_map.overview.is_some() {
            let player = self.surface_global_tile();
            return Some(vec2(player.x as f32 + 0.5, player.y as f32 + 0.5));
        }
        let manifest = self.world_map.manifest.as_ref()?;
        let (region, chunk) =
            haven_world::parse_pcg_surface_scene_id(self.world.active_scene.project_id())?;
        let spec = find_rectangle_spec(manifest, &region, chunk)?;
        let [x, y, w, h] = spec.world_rect_preview_px;
        Some(vec2(
            x as f32 + (self.player.x / (MAP_W as f32 * TILE_SIZE)) * w as f32,
            y as f32 + (self.player.y / (MAP_H as f32 * TILE_SIZE)) * h as f32,
        ))
    }

    fn draw_active_surface_world_map(&self, viewport: Rect) {
        let manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
        let scenes = loaded_surface_scene_map(&self.world, &manifest);
        let center = WorldTileCoord::new(
            self.world_map.center.x.floor() as i32,
            self.world_map.center.y.floor() as i32,
        );
        let cell_px = self.world_map.zoom.max(0.5);
        let half_cols = (viewport.w / cell_px * 0.5).ceil() as i32;
        let half_rows = (viewport.h / cell_px * 0.5).ceil() as i32;
        for y in center.y - half_rows..=center.y + half_rows {
            for x in center.x - half_cols..=center.x + half_cols {
                let Some(tile) = surface_tile_at(&scenes, x, y) else {
                    continue;
                };
                let screen = vec2(
                    viewport.x + viewport.w * 0.5 + (x - center.x) as f32 * cell_px,
                    viewport.y + viewport.h * 0.5 + (y - center.y) as f32 * cell_px,
                );
                draw_rectangle(
                    screen.x,
                    screen.y,
                    cell_px.ceil(),
                    cell_px.ceil(),
                    world_map_tile_color(tile),
                );
            }
        }
        let player = self.surface_global_tile();
        let player_screen = vec2(
            viewport.x + viewport.w * 0.5 + (player.x - center.x) as f32 * cell_px,
            viewport.y + viewport.h * 0.5 + (player.y - center.y) as f32 * cell_px,
        );
        if viewport.contains(player_screen) {
            draw_circle(
                player_screen.x,
                player_screen.y,
                5.0,
                Color::from_rgba(255, 230, 119, 255),
            );
        }
    }
}
