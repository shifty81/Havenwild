use super::*;

impl Game {
    pub(crate) fn update_editor(&mut self) {
        let (mx, my) = mouse_position();
        if self.update_editor_window_transform(mx, my) {
            return;
        }
        if self.handle_tile_context_menu_input(mx, my) {
            return;
        }
        if self.handle_editor_overlay_click(mx, my) {
            return;
        }
        let Some(target) = self.surface_cell_target_at_screen(vec2(mx, my)) else {
            return;
        };
        let tx = target.local_x;
        let ty = target.local_y;
        if is_mouse_button_pressed(MouseButton::Right) {
            self.selected_cell = (tx, ty);
            let Some(scene) = self.world.scene_by_id(&target.scene_id) else {
                return;
            };
            self.inspector = inspect_scene_cell(scene, tx, ty);
            if &target.scene_id != self.world.active_scene.project_id() {
                self.status_message = format!(
                    "Inspecting global tile {},{} in surface partition {},{}",
                    target.global_x, target.global_y, target.chunk.x, target.chunk.y
                );
                return;
            }
            let menu_w = 238.0;
            let menu_h = 292.0;
            self.tile_context_menu = Some(TileContextMenu {
                cell: (tx, ty),
                screen: vec2(
                    mx.min(screen_width() - menu_w - 8.0).max(8.0),
                    my.min(screen_height() - menu_h - 8.0).max(8.0),
                ),
            });
            return;
        }
        if !is_mouse_button_down(MouseButton::Left) {
            return;
        }
        self.selected_cell = (tx, ty);
        if let Some(scene) = self.world.scene_by_id(&target.scene_id) {
            self.inspector = inspect_scene_cell(scene, tx, ty);
        }
        if is_mouse_button_pressed(MouseButton::Left) {
            self.push_undo_snapshot();
        }

        if &target.scene_id != self.world.active_scene.project_id()
            && !matches!(self.editor_tab, EditorTab::Tiles)
        {
            self.status_message = format!(
                "Global surface editing currently routes terrain tiles across partitions; switch to Ground for {},{}",
                target.global_x, target.global_y
            );
            return;
        }

        if self.editor_tab == EditorTab::Map {
            self.apply_map_brush(tx, ty);
            self.sync_active_terrain_cache_now();
            self.inspector = inspect_scene_cell(self.world.active(), tx, ty);
            return;
        }

        if self.editor_tab == EditorTab::Paint {
            self.apply_world_paint_at(tx, ty);
            self.inspector = inspect_scene_cell(self.world.active(), tx, ty);
            return;
        }

        let tool = self.palette.tools[self.selected_tool];
        match tool {
            BuildTool::Inspect => {}
            BuildTool::Floor(tile) => {
                if self.world.active().kind == SceneKind::Exterior {
                    self.paint_global_surface_brush(&target, tile, false);
                } else {
                    let min_y = self.brush_min(ty);
                    let max_y = self.brush_max(ty, self.world.active().dimensions.height as i32);
                    let min_x = self.brush_min(tx);
                    let max_x = self.brush_max(tx, self.world.active().dimensions.width as i32);
                    for y in min_y..=max_y {
                        for x in min_x..=max_x {
                            self.world.active_mut().map.set(x, y, tile);
                        }
                    }
                    let mode = self.terrain_paint_mode;
                    let repair = apply_editor_terrain_paint_policy(
                        &mut self.world.active_mut().map,
                        min_x,
                        min_y,
                        max_x,
                        max_y,
                        mode,
                    );
                    self.status_message = match repair {
                        Ok(report) => format!(
                            "Painted {} [{}{}]",
                            tile.label(),
                            mode.label(),
                            terrain_paint_policy_suffix(report)
                        ),
                        Err(error) => format!(
                            "Painted {} [{}]; terrain repair failed: {}",
                            tile.label(),
                            mode.label(),
                            error
                        ),
                    };
                }
            }
            BuildTool::Object(kind) => {
                let selected = self
                    .placeable_registry
                    .entries()
                    .get(self.selected_placeable_index)
                    .cloned();
                let preview = if let Some(definition) = selected.as_ref() {
                    PlacedObject::with_footprint(
                        definition.compatibility_kind(),
                        tx,
                        ty,
                        definition.footprint,
                    )
                } else {
                    let mut preview = PlacedObject::new(kind, tx, ty);
                    preview.footprint = audited_object_footprint_for_cell(kind, tx, ty);
                    preview
                };
                let issues = self.world.active().map.placement_issues_for_object(preview);
                if issues.is_empty() {
                    let placed = if let Some(definition) = selected.as_ref() {
                        self.world
                            .active_mut()
                            .map
                            .place_pack_defined_object_with_state(
                                preview,
                                definition.persistent_ref(),
                                definition.states.first().map(String::as_str),
                            )
                    } else {
                        self.world.active_mut().map.place_custom_object(preview)
                    };
                    if placed.is_some() {
                        self.selected_object_index =
                            self.world.active().map.object_anchor_at(tx, ty);
                        self.clamp_selected_object();
                    }
                    let label = selected
                        .as_ref()
                        .map_or(kind.label(), |definition| definition.label.as_str());
                    self.status_message = format!("Placed {} at {},{}", label, tx, ty);
                } else {
                    let first_issue = issues
                        .first()
                        .map(|issue| issue.label())
                        .unwrap_or_else(|| "unknown placement issue".to_string());
                    let label = selected
                        .as_ref()
                        .map_or(kind.label(), |definition| definition.label.as_str());
                    self.status_message = format!("Cannot place {}: {}", label, first_issue);
                }
            }
            BuildTool::Erase => {
                let scene_kind = self.world.active().kind;
                let fill = match scene_kind {
                    SceneKind::Exterior => TileKind::Grass,
                    SceneKind::Interior => TileKind::WoodFloor,
                    SceneKind::Cave => TileKind::CaveFloor,
                };
                if scene_kind == SceneKind::Exterior {
                    self.paint_global_surface_brush(&target, fill, true);
                } else {
                    let min_y = self.brush_min(ty);
                    let max_y = self.brush_max(ty, self.world.active().dimensions.height as i32);
                    let min_x = self.brush_min(tx);
                    let max_x = self.brush_max(tx, self.world.active().dimensions.width as i32);
                    for y in min_y..=max_y {
                        for x in min_x..=max_x {
                            let scene = self.world.active_mut();
                            scene.map.set(x, y, fill);
                            scene.map.remove_object_at(x, y);
                            scene
                                .transitions
                                .retain(|transition| !transition.contains(x, y));
                            scene.set_zone(x, y, ZoneKind::None);
                        }
                    }
                    let mode = self.terrain_paint_mode;
                    let _ = apply_editor_terrain_paint_policy(
                        &mut self.world.active_mut().map,
                        min_x,
                        min_y,
                        max_x,
                        max_y,
                        mode,
                    );
                }
            }
            BuildTool::Hoe => {
                for y in self.brush_min(ty)..=self.brush_max(ty, self.world.active().dimensions.height as i32) {
                    for x in self.brush_min(tx)..=self.brush_max(tx, self.world.active().dimensions.width as i32) {
                        self.world.active_mut().map.set(x, y, TileKind::TilledSoil);
                    }
                }
            }
            BuildTool::GreenhouseZone => {
                for y in ty - 1..=ty + 1 {
                    for x in tx - 2..=tx + 2 {
                        self.world
                            .active_mut()
                            .map
                            .set(x, y, TileKind::GreenhouseZone);
                    }
                }
                let _ =
                    self.world
                        .active_mut()
                        .map
                        .place_object(ObjectKind::GreenhouseMarker, tx, ty);
            }
            BuildTool::Zone(zone) => {
                for y in self.brush_min(ty)..=self.brush_max(ty, self.world.active().dimensions.height as i32) {
                    for x in self.brush_min(tx)..=self.brush_max(tx, self.world.active().dimensions.width as i32) {
                        self.world.active_mut().set_zone(x, y, zone);
                    }
                }
            }
            BuildTool::Transition => {
                let target = SceneId::ALL[self.selected_transition_target];
                let (spawn_x, spawn_y) = self
                    .world
                    .scene(target)
                    .map(|scene| (scene.spawn_x, scene.spawn_y))
                    .unwrap_or((23, 13));
                let scene = self.world.active_mut();
                if let Some(existing_id) = scene.transition_id_at(tx, ty) {
                    let _ = scene.remove_transition(existing_id);
                }
                let _ = scene.insert_transition(Transition {
                    id: haven_core::TransitionId::from_raw(0),
                    x: tx,
                    y: ty,
                    w: 1,
                    h: 1,
                    target: target.into(),
                    spawn_x,
                    spawn_y,
                    label: format!("To {}", target.label()),
                });
            }
        }
        self.clamp_selected_object();
        self.sync_active_terrain_cache_now();
        if let Some(scene) = self.world.scene_by_id(&target.scene_id) {
            self.inspector = inspect_scene_cell(scene, tx, ty);
        }
    }

    fn paint_global_surface_brush(
        &mut self,
        center: &crate::runtime_surface_streaming::SurfaceCellTarget,
        tile: TileKind,
        erase_contents: bool,
    ) {
        let half = self.brush_size / 2;
        let min_global_x = center.global_x - half;
        let max_global_x = center.global_x + half;
        let min_global_y = center.global_y - half;
        let max_global_y = center.global_y + half;
        let manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
        let mut targets = Vec::new();
        for global_y in min_global_y..=max_global_y {
            for global_x in min_global_x..=max_global_x {
                let address = haven_world::surface_tile_address(
                    haven_world::open_world::WorldTileCoord::new(global_x, global_y),
                );
                let scene_id = manifest.scene_id_for_chunk(address.chunk);
                if self.world.scene_by_id(&scene_id).is_none() {
                    continue;
                }
                targets.push((scene_id, address.local_x, address.local_y));
            }
        }

        let mut touched_scenes =
            std::collections::BTreeMap::<haven_core::ProjectSceneId, (i32, i32, i32, i32)>::new();
        for (scene_id, local_x, local_y) in targets {
            let Some(scene) = self.world.scene_mut_by_id(&scene_id) else {
                continue;
            };
            scene.map.set(local_x, local_y, tile);
            if erase_contents {
                scene.map.remove_object_at(local_x, local_y);
                scene.set_zone(local_x, local_y, ZoneKind::None);
                scene
                    .transitions
                    .retain(|transition| !transition.contains(local_x, local_y));
            }
            touched_scenes
                .entry(scene_id)
                .and_modify(|bounds| {
                    bounds.0 = bounds.0.min(local_x);
                    bounds.1 = bounds.1.min(local_y);
                    bounds.2 = bounds.2.max(local_x);
                    bounds.3 = bounds.3.max(local_y);
                })
                .or_insert((local_x, local_y, local_x, local_y));
        }

        let mode = self.terrain_paint_mode;
        let mut repairs = 0usize;
        let mut unsupported = 0usize;
        for (scene_id, (min_x, min_y, max_x, max_y)) in &touched_scenes {
            let Some(scene) = self.world.scene_mut_by_id(scene_id) else {
                continue;
            };
            match apply_editor_terrain_paint_policy(
                &mut scene.map,
                *min_x,
                *min_y,
                *max_x,
                *max_y,
                mode,
            ) {
                Ok(report) => {
                    repairs += report.total_mutations();
                    unsupported += report.unsupported_contacts;
                }
                Err(error) => {
                    self.status_message = format!(
                        "Painted {} at global {},{}; terrain repair failed: {}",
                        tile.label(),
                        center.global_x,
                        center.global_y,
                        error
                    );
                    return;
                }
            }
        }

        if touched_scenes.contains_key(self.world.active_scene.project_id()) {
            self.sync_active_terrain_cache_now();
        }
        self.status_message = format!(
            "Painted {} at global {},{} across {} partition(s) [{}; {} repair(s); {} unsupported contact(s)]",
            tile.label(),
            center.global_x,
            center.global_y,
            touched_scenes.len(),
            mode.label(),
            repairs,
            unsupported
        );
    }

    fn handle_tile_context_menu_input(&mut self, mx: f32, my: f32) -> bool {
        let Some(menu) = self.tile_context_menu else {
            return false;
        };
        if is_key_pressed(KeyCode::Escape) || is_mouse_button_pressed(MouseButton::Right) {
            self.tile_context_menu = None;
            return true;
        }
        if !is_mouse_button_pressed(MouseButton::Left) {
            return true;
        }
        let row_x = menu.screen.x + 10.0;
        let row_y = menu.screen.y + 62.0;
        let row_w = 218.0;
        let row_h = 30.0;
        if mx < row_x || mx > row_x + row_w || my < row_y || my > row_y + row_h * 7.0 {
            self.tile_context_menu = None;
            return true;
        }
        let action = ((my - row_y) / row_h).floor() as usize;
        let (x, y) = menu.cell;
        self.selected_cell = menu.cell;
        match action {
            0 => {
                self.inspector = inspect_scene_cell(self.world.active(), x, y);
                self.status_message = format!("Inspecting tile {},{}", x, y);
            }
            1 => {
                if let BuildTool::Floor(tile) = self.palette.tools[self.selected_tool] {
                    self.push_undo_snapshot();
                    self.world.active_mut().map.set(x, y, tile);
                    let mode = self.terrain_paint_mode;
                    let repair = apply_editor_terrain_paint_policy(
                        &mut self.world.active_mut().map,
                        x,
                        y,
                        x,
                        y,
                        mode,
                    );
                    self.sync_active_terrain_cache_now();
                    self.status_message = match repair {
                        Ok(report) => format!(
                            "Painted {} at {},{} [{}{}]",
                            tile.label(),
                            x,
                            y,
                            mode.label(),
                            terrain_paint_policy_suffix(report)
                        ),
                        Err(error) => format!(
                            "Painted {} at {},{} [{}]; terrain repair failed: {}",
                            tile.label(),
                            x,
                            y,
                            mode.label(),
                            error
                        ),
                    };
                } else {
                    self.editor_tab = EditorTab::Tiles;
                    self.select_first_tool_on_page();
                    self.status_message =
                        "Choose a tile, then right-click and select Paint selected tile"
                            .to_string();
                }
            }
            2 => {
                let tile = self.world.active().map.get(x, y);
                self.copied_tile = Some(tile);
                self.status_message = format!("Copied {} from {},{}", tile.label(), x, y);
            }
            3 => {
                if let Some(tile) = self.copied_tile {
                    self.push_undo_snapshot();
                    self.world.active_mut().map.set(x, y, tile);
                    let mode = self.terrain_paint_mode;
                    let repair = apply_editor_terrain_paint_policy(
                        &mut self.world.active_mut().map,
                        x,
                        y,
                        x,
                        y,
                        mode,
                    );
                    self.sync_active_terrain_cache_now();
                    self.status_message = match repair {
                        Ok(report) => format!(
                            "Pasted {} at {},{} [{}{}]",
                            tile.label(),
                            x,
                            y,
                            mode.label(),
                            terrain_paint_policy_suffix(report)
                        ),
                        Err(error) => format!(
                            "Pasted {} at {},{} [{}]; terrain repair failed: {}",
                            tile.label(),
                            x,
                            y,
                            mode.label(),
                            error
                        ),
                    };
                } else {
                    self.status_message = "Copy a tile before pasting".to_string();
                }
            }
            4 => {
                self.push_undo_snapshot();
                let fill = match self.world.active().kind {
                    SceneKind::Exterior => TileKind::Grass,
                    SceneKind::Interior => TileKind::WoodFloor,
                    SceneKind::Cave => TileKind::CaveFloor,
                };
                {
                    let scene = self.world.active_mut();
                    scene.map.set(x, y, fill);
                    scene.map.remove_object_at(x, y);
                    scene.set_zone(x, y, ZoneKind::None);
                    scene
                        .transitions
                        .retain(|transition| !transition.contains(x, y));
                }
                let mode = self.terrain_paint_mode;
                let _ = apply_editor_terrain_paint_policy(
                    &mut self.world.active_mut().map,
                    x,
                    y,
                    x,
                    y,
                    mode,
                );
                self.sync_active_terrain_cache_now();
                self.status_message = format!("Erased tile {},{}", x, y);
            }
            5 => {
                self.editor_tab = EditorTab::World;
                self.select_first_tool_on_page();
                self.status_message = format!(
                    "Tile {},{} selected; use the Links tab to add or edit a transition",
                    x, y
                );
            }
            6 => {
                self.push_undo_snapshot();
                self.world.active_mut().set_zone(x, y, ZoneKind::None);
                self.sync_active_terrain_cache_now();
                self.status_message = format!("Cleared zone at {},{}", x, y);
            }
            _ => {}
        }
        self.inspector = inspect_scene_cell(self.world.active(), x, y);
        self.log.event(&self.status_message);
        self.tile_context_menu = None;
        true
    }
}
