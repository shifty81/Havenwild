use super::*;
impl Game {
    pub(super) fn world_paint_settings(&self) -> WorldPaintBrushSettings {
        WorldPaintBrushSettings {
            family: self.world_paint_family,
            layer: self.world_paint_layer,
            radius_tiles: self.brush_size,
            strength: self.world_paint_strength,
            subcell_mode: self.world_paint_subcell_mode,
            autotile_refresh: self.world_paint_autotile,
            mirror_horizontal: self.world_paint_mirror_horizontal,
            mirror_vertical: self.world_paint_mirror_vertical,
        }
    }
    pub(super) fn apply_world_paint_at(&mut self, tx: i32, ty: i32) {
        let scene_id = self.world.active_scene.clone();
        let biome = self.world.active().biome;
        let settings = self.world_paint_settings();
        let mut report =
            apply_world_paint_brush(&mut self.world.active_mut().map, tx, ty, biome, settings);
        if let Some(bounds) = report.changed_bounds {
            let contact_report = normalize_lpc_authored_material_contacts_region(
                &mut self.world.active_mut().map,
                bounds.min_x,
                bounds.min_y,
                bounds.max_x,
                bounds.max_y,
            );
            report.cleanup_mutations = report
                .cleanup_mutations
                .saturating_add(contact_report.total_mutations());
        }
        self.world_paint_edit_sequence = self.world_paint_edit_sequence.saturating_add(1);
        let delta_record = WorldPaintDeltaRecord::from_report(
            &scene_id,
            tx,
            ty,
            self.world_paint_edit_sequence,
            settings,
            &report,
        );
        let material_record = delta_record.clone();
        let delta_status =
            match append_world_paint_delta_record(&self.save_paths.world_paint_delta, delta_record)
            {
                Ok(delta_report) => delta_report.status_line(),
                Err(err) => format!("Paint delta persist failed: {}", err),
            };
        let material_status = match apply_world_paint_delta_record_to_material_state_path(
            &self.save_paths.world_paint_material_state,
            &material_record,
        ) {
            Ok(material_report) => material_report.status_line(),
            Err(err) => format!("Material state update failed: {}", err),
        };
        self.world_paint_delta_status = format!("{} | {}", delta_status, material_status);
        self.world_paint_last_report = report.status_line();
        self.status_message = format!(
            "{} | {}",
            self.world_paint_last_report, self.world_paint_delta_status
        );
        self.log.event(&format!(
            "World paint: {}; cleanup mutations {}; {}; {}",
            report.status_line(),
            report.cleanup_mutations,
            report.deterministic_note,
            self.world_paint_delta_status
        ));
        self.refresh_world_paint_render_bindings_for_active_scene(
            "Paint stroke render binding refresh",
        );
        self.sync_active_terrain_cache_now();
    }
    pub(super) fn replay_world_paint_deltas(&mut self, active_scene_only: bool) {
        let scene_filter = if active_scene_only {
            Some(self.world.active_scene.clone())
        } else {
            None
        };
        match load_and_replay_world_paint_deltas(
            &mut self.world,
            &self.save_paths.world_paint_delta,
            scene_filter,
        ) {
            Ok(report) => {
                self.world_paint_delta_status = report.status_line();
                self.world_paint_last_report = if report.issues.is_empty() {
                    "Replay completed without skipped paint records".to_string()
                } else {
                    format!(
                        "Replay completed with {} skipped record(s)",
                        report.issues.len()
                    )
                };
                self.status_message = format!(
                    "{} | {}",
                    self.world_paint_delta_status, self.world_paint_last_report
                );
                self.log
                    .event(&format!("World paint replay: {}", report.status_line()));
                self.refresh_world_paint_render_bindings_for_active_scene(
                    "Replay render binding refresh",
                );
                for issue in report.issues.iter().take(4) {
                    self.log.event(&format!(
                        "World paint replay issue: {}",
                        issue.status_line()
                    ));
                }
            }
            Err(err) => {
                self.world_paint_delta_status = format!("Paint delta replay failed: {}", err);
                self.status_message = self.world_paint_delta_status.clone();
                self.log.event(&self.status_message);
            }
        }
    }
    pub(super) fn inspect_selected_world_paint_material_cell(&mut self) {
        let scene_id = self.world.active_scene.clone();
        let (x, y) = self.selected_cell;
        match inspect_world_paint_material_cell_path(
            &self.save_paths.world_paint_material_state,
            scene_id.code(),
            x,
            y,
        ) {
            Ok(inspection) => {
                self.world_paint_inspector_status = inspection.status_line();
                self.world_paint_inspector = Some(inspection);
            }
            Err(err) => {
                self.world_paint_inspector_status = format!("Material inspector failed: {}", err);
                self.world_paint_inspector = None;
            }
        }
        self.status_message = self.world_paint_inspector_status.clone();
        self.log.event(&format!(
            "World paint inspector: {}",
            self.world_paint_inspector_status
        ));
    }
    pub(super) fn resolve_selected_world_paint_material_adjacency(&mut self) {
        let scene_id = self.world.active_scene.clone();
        let (x, y) = self.selected_cell;
        match resolve_world_paint_material_adjacency_path(
            &self.save_paths.world_paint_material_state,
            scene_id.code(),
            x,
            y,
        ) {
            Ok(report) => {
                self.world_paint_adjacency_status = report.status_line();
                self.world_paint_adjacency = Some(report);
            }
            Err(err) => {
                self.world_paint_adjacency_status = format!("Material adjacency failed: {}", err);
                self.world_paint_adjacency = None;
            }
        }
        self.status_message = self.world_paint_adjacency_status.clone();
        self.log.event(&format!(
            "World paint adjacency: {}",
            self.world_paint_adjacency_status
        ));
    }
    pub(super) fn resolve_active_scene_world_paint_adjacency(&mut self) {
        let scene_id = self.world.active_scene.clone();
        match resolve_world_paint_material_scene_adjacency_path(
            &self.save_paths.world_paint_material_state,
            scene_id.code(),
        ) {
            Ok(report) => {
                self.world_paint_adjacency_status = report.status_line();
                self.world_paint_adjacency = None;
            }
            Err(err) => {
                self.world_paint_adjacency_status = format!("Scene adjacency failed: {}", err);
                self.world_paint_adjacency = None;
            }
        }
        self.status_message = self.world_paint_adjacency_status.clone();
        self.log.event(&format!(
            "World paint scene adjacency: {}",
            self.world_paint_adjacency_status
        ));
    }
    pub(super) fn resolve_selected_world_paint_transition_tile(&mut self) {
        let scene_id = self.world.active_scene.clone();
        let (x, y) = self.selected_cell;
        match resolve_world_paint_transition_tile(
            runtime_root(),
            &self.save_paths.world_paint_material_state,
            scene_id.code(),
            x,
            y,
        ) {
            Ok(report) => {
                self.world_paint_tile_resolver_status = report.status_line();
                self.world_paint_tile_resolution = Some(report);
            }
            Err(err) => {
                self.world_paint_tile_resolver_status =
                    format!("Transition tile resolve failed: {}", err);
                self.world_paint_tile_resolution = None;
            }
        }
        self.status_message = self.world_paint_tile_resolver_status.clone();
        self.log.event(&format!(
            "World paint transition tile: {}",
            self.world_paint_tile_resolver_status
        ));
    }
    pub(super) fn resolve_active_scene_world_paint_transition_tiles(&mut self) {
        let scene_id = self.world.active_scene.clone();
        match resolve_world_paint_scene_transition_tiles(
            runtime_root(),
            &self.save_paths.world_paint_material_state,
            scene_id.code(),
        ) {
            Ok(report) => {
                self.world_paint_tile_resolver_status = report.status_line();
                self.world_paint_tile_resolution = None;
            }
            Err(err) => {
                self.world_paint_tile_resolver_status =
                    format!("Scene transition tile resolve failed: {}", err);
                self.world_paint_tile_resolution = None;
            }
        }
        self.status_message = self.world_paint_tile_resolver_status.clone();
        self.log.event(&format!(
            "World paint scene transition tiles: {}",
            self.world_paint_tile_resolver_status
        ));
    }
    pub(super) fn handle_world_paint_tab_click(&mut self, mx: f32, my: f32, panel_x: f32) -> bool {
        for (label, x, y, w) in [
            ("Family", panel_x + 18.0, 126.0, 92.0),
            ("Layer", panel_x + 118.0, 126.0, 82.0),
            ("Subcell", panel_x + 208.0, 126.0, 92.0),
            ("Str-", panel_x + 308.0, 126.0, 62.0),
            ("Str+", panel_x + 378.0, 126.0, 62.0),
            ("Auto", panel_x + 18.0, 164.0, 82.0),
            ("MirrorH", panel_x + 108.0, 164.0, 82.0),
            ("MirrorV", panel_x + 198.0, 164.0, 82.0),
            ("Match", panel_x + 288.0, 164.0, 82.0),
            ("Water", panel_x + 18.0, 202.0, 76.0),
            ("Sand", panel_x + 102.0, 202.0, 72.0),
            ("Cave", panel_x + 182.0, 202.0, 72.0),
            ("Brick", panel_x + 262.0, 202.0, 76.0),
            ("Wood", panel_x + 346.0, 202.0, 76.0),
            ("Replay", panel_x + 18.0, 240.0, 94.0),
            ("ReplayAll", panel_x + 120.0, 240.0, 106.0),
            ("Inspect", panel_x + 234.0, 240.0, 94.0),
            ("Adj", panel_x + 336.0, 240.0, 64.0),
            ("SceneAdj", panel_x + 408.0, 240.0, 94.0),
            ("Tile", panel_x + 18.0, 278.0, 76.0),
            ("SceneTile", panel_x + 102.0, 278.0, 104.0),
            ("Bind", panel_x + 214.0, 278.0, 76.0),
        ] {
            if mx >= x && mx <= x + w && my >= y && my <= y + 26.0 {
                match label {
                    "Family" => {
                        self.world_paint_family = self.world_paint_family.cycle(1);
                        self.world_paint_layer = self.world_paint_family.default_layer();
                    }
                    "Layer" => self.world_paint_layer = self.world_paint_layer.cycle(1),
                    "Subcell" => {
                        self.world_paint_subcell_mode = self.world_paint_subcell_mode.cycle(1)
                    }
                    "Str-" => {
                        self.world_paint_strength = (self.world_paint_strength - 0.1).max(0.1)
                    }
                    "Str+" => {
                        self.world_paint_strength = (self.world_paint_strength + 0.1).min(1.0)
                    }
                    "Auto" => self.world_paint_autotile = !self.world_paint_autotile,
                    "MirrorH" => {
                        self.world_paint_mirror_horizontal = !self.world_paint_mirror_horizontal
                    }
                    "MirrorV" => {
                        self.world_paint_mirror_vertical = !self.world_paint_mirror_vertical
                    }
                    "Match" => self.world_paint_layer = self.world_paint_family.default_layer(),
                    "Water" => {
                        self.world_paint_family = WorldPaintFamily::Water;
                        self.world_paint_layer = self.world_paint_family.default_layer();
                    }
                    "Sand" => {
                        self.world_paint_family = WorldPaintFamily::Sand;
                        self.world_paint_layer = self.world_paint_family.default_layer();
                    }
                    "Cave" => {
                        self.world_paint_family = WorldPaintFamily::Cave;
                        self.world_paint_layer = self.world_paint_family.default_layer();
                    }
                    "Brick" => {
                        self.world_paint_family = WorldPaintFamily::PavedBrick;
                        self.world_paint_layer = self.world_paint_family.default_layer();
                    }
                    "Wood" => {
                        self.world_paint_family = WorldPaintFamily::WoodPlank;
                        self.world_paint_layer = self.world_paint_family.default_layer();
                    }
                    "Replay" => {
                        self.replay_world_paint_deltas(true);
                        return true;
                    }
                    "ReplayAll" => {
                        self.replay_world_paint_deltas(false);
                        return true;
                    }
                    "Inspect" => {
                        self.inspect_selected_world_paint_material_cell();
                        return true;
                    }
                    "Adj" => {
                        self.resolve_selected_world_paint_material_adjacency();
                        return true;
                    }
                    "SceneAdj" => {
                        self.resolve_active_scene_world_paint_adjacency();
                        return true;
                    }
                    "Tile" => {
                        self.resolve_selected_world_paint_transition_tile();
                        return true;
                    }
                    "SceneTile" => {
                        self.resolve_active_scene_world_paint_transition_tiles();
                        return true;
                    }
                    "Bind" => {
                        self.refresh_world_paint_render_bindings_for_active_scene(
                            "Manual paint render binding refresh",
                        );
                        self.status_message = self.world_paint_render_status.clone();
                        return true;
                    }
                    _ => {}
                }
                self.status_message = format!(
                    "Paint {} on {} using {} subcells",
                    self.world_paint_family.label(),
                    self.world_paint_layer.code(),
                    self.world_paint_subcell_mode.code()
                );
                self.log.event(&self.status_message);
                return true;
            }
        }
        true
    }
    pub(super) fn handle_world_paint_hotkeys(&mut self) {
        if is_key_pressed(KeyCode::J) {
            self.world_paint_family = self.world_paint_family.cycle(-1);
            self.world_paint_layer = self.world_paint_family.default_layer();
        }
        if is_key_pressed(KeyCode::K) {
            self.world_paint_family = self.world_paint_family.cycle(1);
            self.world_paint_layer = self.world_paint_family.default_layer();
        }
        if is_key_pressed(KeyCode::LeftBracket) {
            self.world_paint_subcell_mode = self.world_paint_subcell_mode.cycle(-1);
        }
        if is_key_pressed(KeyCode::RightBracket) {
            self.world_paint_subcell_mode = self.world_paint_subcell_mode.cycle(1);
        }
        if is_key_pressed(KeyCode::P) {
            self.world_paint_layer = self.world_paint_layer.cycle(1);
        }
        if is_key_pressed(KeyCode::A) {
            self.world_paint_autotile = !self.world_paint_autotile;
        }
        if is_key_pressed(KeyCode::H) {
            self.world_paint_mirror_horizontal = !self.world_paint_mirror_horizontal;
        }
        if is_key_pressed(KeyCode::V) {
            self.world_paint_mirror_vertical = !self.world_paint_mirror_vertical;
        }
        if is_key_pressed(KeyCode::R) {
            self.world_paint_layer = self.world_paint_family.default_layer();
        }
        if is_key_pressed(KeyCode::T) {
            self.replay_world_paint_deltas(true);
        }
        if is_key_pressed(KeyCode::I) {
            self.inspect_selected_world_paint_material_cell();
        }
        if is_key_pressed(KeyCode::Y) {
            self.resolve_selected_world_paint_material_adjacency();
        }
        if is_key_pressed(KeyCode::U) {
            self.resolve_active_scene_world_paint_adjacency();
        }
        if is_key_pressed(KeyCode::O) {
            self.resolve_selected_world_paint_transition_tile();
        }
        if is_key_pressed(KeyCode::L) {
            self.resolve_active_scene_world_paint_transition_tiles();
        }
        if is_key_pressed(KeyCode::B) {
            self.refresh_world_paint_render_bindings_for_active_scene(
                "Hotkey paint render binding refresh",
            );
        }
        self.status_message = format!(
            "Paint {} | layer {} | subcell {} | autotile {} | mirror H:{} V:{}",
            self.world_paint_family.label(),
            self.world_paint_layer.code(),
            self.world_paint_subcell_mode.code(),
            if self.world_paint_autotile {
                "on"
            } else {
                "off"
            },
            if self.world_paint_mirror_horizontal {
                "on"
            } else {
                "off"
            },
            if self.world_paint_mirror_vertical {
                "on"
            } else {
                "off"
            }
        );
    }
}
