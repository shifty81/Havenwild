use super::*;

fn surface_actor_visible_at_zoom(kind: ObjectKind, camera_zoom: f32) -> bool {
    // At extreme world zoom these one-cell forage sprites are below useful
    // inspection scale but still cost draw calls and sort bandwidth. Trees stay
    // visible at every zoom because forest presence is a worldgen acceptance
    // signal; structures/resources with gameplay silhouettes are never culled.
    if camera_zoom <= 0.95 {
        return !matches!(kind, ObjectKind::Bush | ObjectKind::Mushroom | ObjectKind::Herb);
    }
    if camera_zoom <= 1.10 {
        return !matches!(kind, ObjectKind::Mushroom | ObjectKind::Herb);
    }
    true
}

fn structural_cliff_face_sort_y(global_y: i32, face_segments: u8) -> f32 {
    // The authored foot row is the visual base of the wall. Sort at the top of
    // that row: actors whose feet are still in the projected body rows remain
    // behind the cliff, while actors that have stepped onto/beyond the foot row
    // render in front. This also keeps an upper-plateau actor out of the face
    // replay because the character body grows north from its foot anchor.
    (global_y as f32 + f32::from(face_segments)) * TILE_SIZE - 0.5
}

impl Game {
    pub(super) fn draw(&self) {
        #[cfg(target_os = "windows")]
        crate::native_crash_windows::set_phase(crate::native_crash_windows::PHASE_DRAW_CLEAR);
        let background = if self.world.active().kind == SceneKind::Exterior {
            sky_color(night_amount(self.day_clock))
        } else {
            // Interior/cave scenes render only their authored footprint. The
            // unused backing grid is true void rather than repeated floor/wall.
            BLACK
        };
        clear_background(background);
        set_camera(&self.game_camera());
        #[cfg(target_os = "windows")]
        crate::native_crash_windows::set_phase(crate::native_crash_windows::PHASE_DRAW_MAP);
        self.draw_map();
        #[cfg(target_os = "windows")]
        crate::native_crash_windows::set_phase(
            crate::native_crash_windows::PHASE_DRAW_STRUCTURAL_CLIFFS,
        );
        self.draw_structural_cliffs();
        // Project-owned hand-painted visual overrides sit above generated terrain/cliffs
        // while semantic collision/navigation remains owned by the world model.
        #[cfg(target_os = "windows")]
        crate::native_crash_windows::set_phase(
            crate::native_crash_windows::PHASE_DRAW_VISUAL_OVERRIDES,
        );
        self.draw_scene_visual_overrides();
        #[cfg(target_os = "windows")]
        crate::native_crash_windows::set_phase(crate::native_crash_windows::PHASE_DRAW_TRANSITIONS);
        self.draw_transitions();
        #[cfg(target_os = "windows")]
        crate::native_crash_windows::set_phase(crate::native_crash_windows::PHASE_DRAW_ACTORS);
        self.draw_actors();
        // Restore the AB40-AB49 player-interaction draw lane that AC1's
        // Aug-31-based runtime_draw overwrite displaced. Projectiles and the
        // ranged targeting overlay are world-space presentation and therefore
        // must render while the gameplay camera is still active.
        self.draw_runtime_projectiles();
        self.draw_ranged_targeting_overlay();
        #[cfg(target_os = "windows")]
        crate::native_crash_windows::set_phase(crate::native_crash_windows::PHASE_DRAW_WORLD_OVERLAYS);
        self.draw_editor_footprint_overlays();
        self.draw_terrain_debug_overlay();
        self.draw_transition_rule_inspector_overlay();
        self.draw_transition_rule_preview_overlay();
        self.draw_editor_cursor();
        set_default_camera();
        #[cfg(target_os = "windows")]
        crate::native_crash_windows::set_phase(crate::native_crash_windows::PHASE_DRAW_HUD);
        self.draw_lighting_overlay();
        self.draw_player_hud_frame();
        self.draw_ui();
        self.draw_runtime_chat();
        self.draw_tile_context_menu();
        if self.dev_mode && self.build_mode && self.editor_tab != EditorTab::World {
            draw_inspector_overlay(self.panel_rect(UiPanelId::Inspector), &self.inspector);
        }
        if self.dev_mode && self.show_world_graph {
            draw_world_graph_overlay(
                self.panel_rect(UiPanelId::WorldGraph),
                &self.world.scenes,
                &self.world.active_scene,
            );
        }
        if self.dev_mode && !self.validation_messages.is_empty() {
            draw_validation_overlay(
                self.panel_rect(UiPanelId::Validation),
                &self.validation_messages,
            );
        }
        if self.layout_edit_mode {
            let mut panel_rects = Vec::new();
            for panel in UiPanelId::ALL {
                if panel == UiPanelId::Inspector
                    && (!self.dev_mode || !self.build_mode || self.editor_tab == EditorTab::World)
                {
                    continue;
                }
                if panel == UiPanelId::WorldGraph && (!self.dev_mode || !self.show_world_graph) {
                    continue;
                }
                if panel == UiPanelId::Validation
                    && (!self.dev_mode || self.validation_messages.is_empty())
                {
                    continue;
                }
                if panel == UiPanelId::Editor && (!self.dev_mode || !self.build_mode) {
                    continue;
                }
                panel_rects.push((panel, self.panel_rect(panel)));
            }
            draw_layout_guides(&panel_rects);
        }
        #[cfg(target_os = "windows")]
        crate::native_crash_windows::set_phase(crate::native_crash_windows::PHASE_DRAW_WORLD_MAP);
        self.draw_world_map_overlay();
        if self.player_inventory_ui.open {
            #[cfg(target_os = "windows")]
            crate::native_crash_windows::set_phase(crate::native_crash_windows::PHASE_DRAW_INVENTORY);
            // AC1 must preserve the AB49R1 authoritative item-icon binding.
            // The cliff closure originally started from the Aug-31 rollup and
            // accidentally restored the obsolete zero-argument draw call.
            self.player_inventory_ui
                .draw(self.item_icon_atlas.as_ref(), &self.item_icon_rects);
            // AB40-AB49 reserves the inventory/equipment presentation for a
            // live composed character rather than the obsolete head-only crop.
            // Draw it after the inventory chrome so the paper doll owns the
            // character viewport without being hidden by the panel background.
            self.draw_inventory_character_paper_doll();
            // The hotbar is part of gameplay, not the inventory modal. Keep it
            // fully visible/active above the menu so items can be dragged from
            // Inventory directly onto player-chosen shortcut slots.
            self.draw_player_hotbar();
        }
        #[cfg(target_os = "windows")]
        crate::native_crash_windows::set_phase(
            crate::native_crash_windows::PHASE_DRAW_NOTIFICATIONS,
        );
        self.player_inventory_ui.draw_processing_notifications();
    }

    /// Draw the Inventory + Equipment paper doll from the same resolved
    /// runtime character layers used by the in-world player. This deliberately
    /// uses the complete authored frame rather than `draw_portrait`, which is
    /// a head/shoulders crop intended only for the compact HUD portrait.
    pub(super) fn draw_inventory_character_paper_doll(&self) {
        let panel_w = screen_width().min(1180.0) - 48.0;
        let panel_h = screen_height().min(760.0) - 48.0;
        let panel = Rect::new(
            (screen_width() - panel_w) * 0.5,
            (screen_height() - panel_h) * 0.5,
            panel_w,
            panel_h,
        );

        // Keep the preview in the upper-right equipment workspace. The
        // inventory grid ends well before this region, while crafting owns the
        // lower half of the panel. Clamp for smaller supported windows.
        let preview_w = 156.0_f32.min((panel.w - 56.0).max(96.0));
        let preview_h = 238.0_f32.min((panel.h - 150.0).max(132.0));
        let preview = Rect::new(
            panel.x + panel.w - preview_w - 28.0,
            panel.y + 92.0,
            preview_w,
            preview_h,
        );

        draw_rectangle(
            preview.x,
            preview.y,
            preview.w,
            preview.h,
            Color::from_rgba(24, 23, 20, 232),
        );
        draw_rectangle_lines(
            preview.x,
            preview.y,
            preview.w,
            preview.h,
            2.0,
            Color::from_rgba(151, 119, 73, 230),
        );
        draw_text(
            "Character",
            preview.x + 12.0,
            preview.y + 23.0,
            18.0,
            Color::from_rgba(232, 213, 170, 255),
        );

        let body = Rect::new(
            preview.x + 10.0,
            preview.y + 32.0,
            preview.w - 20.0,
            preview.h - 42.0,
        );

        if let Some(appearance) = self.runtime_character_appearance.as_ref() {
            // The paper doll is a stable south-facing idle presentation. It
            // remains live because equipment changes rebuild this same runtime
            // appearance through the inventory/profile synchronization path.
            for layer in &appearance.layers {
                let texture = layer
                    .idle_texture
                    .as_ref()
                    .unwrap_or(&layer.walk_texture);
                let frame_h = if texture.height() >= 96.0 * 4.0
                    && (texture.height() as i32).rem_euclid(96) == 0
                {
                    96.0
                } else {
                    64.0
                };
                let columns = (texture.width() / 64.0).floor().max(1.0);
                let rows = (texture.height() / frame_h).floor().max(1.0);
                let row = 2.0_f32.min(rows - 1.0);
                let source = Rect::new(0.0, row * frame_h, 64.0_f32.min(texture.width()), frame_h);
                let scale = (body.w / source.w).min(body.h / source.h);
                let draw_w = source.w * scale;
                let draw_h = source.h * scale;
                let x = body.x + (body.w - draw_w) * 0.5;
                let y = body.y + body.h - draw_h;
                draw_texture_ex(
                    texture,
                    x,
                    y,
                    layer.tint,
                    DrawTextureParams {
                        dest_size: Some(vec2(draw_w, draw_h)),
                        source: Some(source),
                        ..Default::default()
                    },
                );
                let _ = columns; // document that column zero is the idle pose
            }
            return;
        }

        // Source-backed compatibility fallback only. This still renders the
        // complete player frame; it never falls back to the cropped HUD
        // portrait or to generated placeholder art.
        if let Some(atlas) = self.player_walk_atlas.as_ref() {
            let source = Rect::new(0.0, 2.0 * 96.0, 64.0, 96.0);
            let scale = (body.w / source.w).min(body.h / source.h);
            let draw_w = source.w * scale;
            let draw_h = source.h * scale;
            draw_texture_ex(
                atlas,
                body.x + (body.w - draw_w) * 0.5,
                body.y + body.h - draw_h,
                WHITE,
                DrawTextureParams {
                    dest_size: Some(vec2(draw_w, draw_h)),
                    source: Some(source),
                    ..Default::default()
                },
            );
        }
    }

    fn draw_tile_context_menu(&self) {
        let Some(menu) = self.tile_context_menu else {
            return;
        };
        let tile = self.world.active().map.get(menu.cell.0, menu.cell.1);
        let x = menu.screen.x;
        let y = menu.screen.y;
        draw_panel(x, y, 238.0, 282.0, "Tile actions");
        draw_text(
            &format!("{},{}  {}", menu.cell.0, menu.cell.1, tile.label()),
            x + 12.0,
            y + 52.0,
            17.0,
            Color::from_rgba(255, 246, 208, 255),
        );
        for (index, label) in [
            "Inspect tile",
            "Paint selected tile",
            "Copy tile",
            "Paste tile",
            "Erase tile contents",
            "Edit transition here",
            "Clear zone",
        ]
        .iter()
        .enumerate()
        {
            draw_editor_button(label, x + 10.0, y + 62.0 + index as f32 * 30.0, 218.0, 27.0);
        }
    }
    pub(super) fn draw_transitions(&self) {
        if !self.dev_mode || (self.build_mode && !self.show_interaction_overlay) {
            return;
        }
        for transition in &self.world.active().transitions {
            let screen = self.world_to_screen(vec2(
                transition.x as f32 * TILE_SIZE,
                transition.y as f32 * TILE_SIZE,
            ));
            draw_rectangle_lines(
                screen.x + 2.0,
                screen.y + 2.0,
                transition.w as f32 * TILE_SIZE - 4.0,
                transition.h as f32 * TILE_SIZE - 4.0,
                3.0,
                Color::from_rgba(116, 221, 255, 245),
            );
        }
    }
    pub(super) fn draw_lighting_overlay(&self) {
        let night = night_amount(self.day_clock);
        if night > 0.02 {
            draw_rectangle(
                0.0,
                0.0,
                screen_width(),
                screen_height(),
                Color::new(0.012, 0.016, 0.050, night * 0.72),
            );
        }
        if self.tavern_open {
            draw_circle(
                220.0,
                72.0,
                38.0,
                Color::new(1.0, 0.68, 0.28, 0.10 + night * 0.10),
            );
        }
    }
    pub(super) fn draw_actors(&self) {
        // Streamed-surface identity, not SceneKind::Exterior, decides which
        // actor path owns the scene. Home Estate and other bounded exteriors
        // remain exterior for sky/weather while retaining scene-local actors.
        if self.active_surface_chunk_coord().is_some() {
            self.draw_continuous_surface_actors();
            return;
        }
        self.draw_active_scene_actors();
    }

    fn draw_active_scene_actors(&self) {
        let map = &self.world.active().map;
        let visible = runtime_view_culling::visible_tile_bounds(
            self.active_local_camera_target(),
            self.camera_zoom,
            3,
            self.world.active().dimensions,
        );
        let building_pieces = self.visible_building_draw_pieces();
        let mut commands = Vec::with_capacity(
            map.stamps.len() + map.objects.len() + self.customers.len() + building_pieces.len() + 1,
        );
        for (index, stamp) in map.stamps.iter().enumerate() {
            if runtime_view_culling::tile_rect_intersects_bounds(stamp.visual_rect(), visible, 2) {
                commands.push((stamp.sort_y(), 0_u8, RenderCommand::Stamp(index)));
            }
        }
        for (index, object) in map.objects.iter().enumerate() {
            if !runtime_view_culling::tile_rect_intersects_bounds(object.visual_rect(), visible, 2)
            {
                continue;
            }
            if matches!(object.kind, ObjectKind::Mushroom | ObjectKind::Herb) {
                self.draw_object(*object, self.world_to_screen(object_origin(*object)));
                continue;
            }
            commands.push((object_sort_y(*object), 1_u8, RenderCommand::Object(index)));
        }
        for (index, piece) in building_pieces.iter().enumerate() {
            if runtime_view_culling::tile_rect_intersects_bounds(
                (piece.world_tile[0], piece.world_tile[1], 1, 1),
                visible,
                2,
            ) {
                commands.push((piece.sort_y, 2_u8, RenderCommand::BuildingPiece(index)));
            }
        }
        for (index, customer) in self.customers.iter().enumerate() {
            let tile_x = (customer.pos.x / TILE_SIZE).floor() as i32;
            let tile_y = (customer.pos.y / TILE_SIZE).floor() as i32;
            if runtime_view_culling::tile_rect_intersects_bounds((tile_x, tile_y, 1, 1), visible, 2)
            {
                commands.push((
                    customer_sort_y(customer),
                    2_u8,
                    RenderCommand::Customer(index),
                ));
            }
        }
        commands.push((player_sort_y(self.player), 3_u8, RenderCommand::Player));
        commands.sort_by(|left, right| left.0.total_cmp(&right.0).then(left.1.cmp(&right.1)));
        for (_, _, command) in commands {
            match command {
                RenderCommand::Stamp(index) => {
                    self.draw_stamp(&self.world.active().map.stamps[index]);
                }
                RenderCommand::Object(index) => {
                    let object = self.world.active().map.objects[index];
                    self.draw_object(object, self.world_to_screen(object_origin(object)));
                }
                RenderCommand::Customer(index) => self.draw_customer(&self.customers[index]),
                RenderCommand::BuildingPiece(index) => {
                    self.draw_building_piece(&building_pieces[index]);
                }
                RenderCommand::Player => self.draw_player(),
                RenderCommand::SurfaceStamp { .. }
                | RenderCommand::SurfaceObject { .. }
                | RenderCommand::SurfaceCliffFace { .. } => {}
            }
        }
    }

    fn draw_continuous_surface_actors(&self) {
        let manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
        let viewport = vec2(screen_width().max(1.0), screen_height().max(1.0));
        let half_visible = viewport / self.camera_zoom.max(0.01) * 0.5;
        let min_x = ((self.camera_target.x - half_visible.x) / TILE_SIZE).floor() as i32 - 4;
        let min_y = ((self.camera_target.y - half_visible.y) / TILE_SIZE).floor() as i32 - 6;
        let max_x = ((self.camera_target.x + half_visible.x) / TILE_SIZE).ceil() as i32 + 4;
        let max_y = ((self.camera_target.y + half_visible.y) / TILE_SIZE).ceil() as i32 + 4;
        let visible = (min_x, min_y, max_x, max_y);
        let mut commands = Vec::new();

        for binding in &manifest.exterior_bindings {
            let offset_x = binding.chunk.x * MAP_W as i32;
            let offset_y = binding.chunk.y * MAP_H as i32;
            // Storage partitions are not render units. Reject an entire chunk
            // before resolving its scene or walking its object/stamp arrays.
            // Previously every loaded PCG partition was scanned every frame,
            // even when dozens of chunks were far outside the camera.
            if !runtime_view_culling::tile_rect_intersects_bounds(
                (offset_x, offset_y, MAP_W as i32, MAP_H as i32),
                visible,
                2,
            ) {
                continue;
            }
            let Some(scene_index) = self
                .world
                .scenes
                .iter()
                .position(|scene| scene.id == binding.scene_id)
            else {
                continue;
            };
            let scene = &self.world.scenes[scene_index];
            for (stamp_index, stamp) in scene.map.stamps.iter().enumerate() {
                let (x, y, w, h) = stamp.visual_rect();
                let global_rect = (x + offset_x, y + offset_y, w, h);
                if !runtime_view_culling::tile_rect_intersects_bounds(global_rect, visible, 2) {
                    continue;
                }
                commands.push((
                    stamp.sort_y() + offset_y as f32 * TILE_SIZE,
                    0_u8,
                    RenderCommand::SurfaceStamp {
                        scene_index,
                        stamp_index,
                        chunk_x: binding.chunk.x,
                        chunk_y: binding.chunk.y,
                    },
                ));
            }
            for (object_index, object) in scene.map.objects.iter().enumerate() {
                if !surface_actor_visible_at_zoom(object.kind, self.camera_zoom) {
                    continue;
                }
                let (x, y, w, h) = object.visual_rect();
                let global_rect = (x + offset_x, y + offset_y, w, h);
                if !runtime_view_culling::tile_rect_intersects_bounds(global_rect, visible, 2) {
                    continue;
                }
                if matches!(object.kind, ObjectKind::Mushroom | ObjectKind::Herb) {
                    self.draw_surface_object(scene, *object, binding.chunk.x, binding.chunk.y);
                    continue;
                }
                commands.push((
                    object_sort_y(*object) + offset_y as f32 * TILE_SIZE,
                    1_u8,
                    RenderCommand::SurfaceObject {
                        scene_index,
                        object_index,
                        chunk_x: binding.chunk.x,
                        chunk_y: binding.chunk.y,
                    },
                ));
            }
        }

        // Structural south faces join the same Y-depth queue as actors. The
        // base terrain/cliff pass has already drawn them once; this second
        // submission is an occlusion-only replay at the face foot depth. This
        // fixes lower-ground characters drawing fully on top of a cliff while
        // preserving actors that are genuinely in front of the foot.
        for global_y in min_y..=max_y {
            for global_x in min_x..=max_x {
                let Some(cell) = self.surface_structural_at_global_in_manifest(
                    &manifest,
                    global_x,
                    global_y,
                ) else {
                    continue;
                };
                if !cell
                    .exposed_edges
                    .contains(haven_world::EdgeMaskV2::SOUTH)
                {
                    continue;
                }
                let face_segments =
                    haven_render::structural_cliff_visual::authored_south_face_segments(cell);
                if face_segments < 2 {
                    continue;
                }
                // A complete authored ramp contains walkable ground inside its
                // visual stamp. Replaying the whole ramp as foreground would
                // paint over a character standing on the ramp, so ramp-owned
                // cells remain in the ordinary structural pass.
                if self
                    .complete_directional_ramp_owner_for_cell(&manifest, global_x, global_y)
                    .is_some()
                {
                    continue;
                }
                commands.push((
                    structural_cliff_face_sort_y(global_y, face_segments),
                    2_u8,
                    RenderCommand::SurfaceCliffFace { global_x, global_y },
                ));
            }
        }

        // Continuous-surface buildings are resolved in global tile space.
        // Storage partitions are residency/persistence units, not visibility
        // units, so a building does not disappear when its anchor crosses the
        // active 64x64 partition boundary.
        let building_pieces = self.visible_surface_building_draw_pieces();
        let active_offset = self.active_surface_origin_px();
        for (index, piece) in building_pieces.iter().enumerate() {
            let global_x = piece.world_tile[0];
            let global_y = piece.world_tile[1];
            if runtime_view_culling::tile_rect_intersects_bounds((global_x, global_y, 1, 1), visible, 2) {
                commands.push((piece.sort_y, 2_u8, RenderCommand::BuildingPiece(index)));
            }
        }
        for (index, customer) in self.customers.iter().enumerate() {
            let global = customer.pos + active_offset;
            let tile_x = (global.x / TILE_SIZE).floor() as i32;
            let tile_y = (global.y / TILE_SIZE).floor() as i32;
            if runtime_view_culling::tile_rect_intersects_bounds((tile_x, tile_y, 1, 1), visible, 2)
            {
                commands.push((global.y, 2_u8, RenderCommand::Customer(index)));
            }
        }
        let player_global = self.local_world_to_runtime_world(self.player);
        commands.push((player_global.y + 20.0, 3_u8, RenderCommand::Player));
        commands.sort_by(|left, right| left.0.total_cmp(&right.0).then(left.1.cmp(&right.1)));

        for (_, _, command) in commands {
            match command {
                RenderCommand::SurfaceStamp {
                    scene_index,
                    stamp_index,
                    chunk_x,
                    chunk_y,
                } => {
                    let stamp = &self.world.scenes[scene_index].map.stamps[stamp_index];
                    self.draw_surface_stamp(stamp, chunk_x, chunk_y);
                }
                RenderCommand::SurfaceObject {
                    scene_index,
                    object_index,
                    chunk_x,
                    chunk_y,
                } => {
                    let scene = &self.world.scenes[scene_index];
                    let object = scene.map.objects[object_index];
                    self.draw_surface_object(scene, object, chunk_x, chunk_y);
                }
                RenderCommand::Customer(index) => {
                    let customer = &self.customers[index];
                    let screen = self.runtime_world_to_screen(customer.pos + active_offset);
                    draw_circle(
                        screen.x,
                        screen.y - 8.0,
                        9.0,
                        Color::from_rgba(226, 188, 128, 255),
                    );
                    draw_rectangle(
                        screen.x - 7.0,
                        screen.y,
                        14.0,
                        16.0,
                        Color::from_rgba(104, 82, 142, 255),
                    );
                }
                RenderCommand::BuildingPiece(index) => {
                    self.draw_building_piece(&building_pieces[index]);
                }
                RenderCommand::SurfaceCliffFace { global_x, global_y } => {
                    self.draw_structural_cliff_foreground_face(
                        &manifest,
                        global_x,
                        global_y,
                    );
                }
                RenderCommand::Player => self.draw_player(),
                RenderCommand::Stamp(_) | RenderCommand::Object(_) => {}
            }
        }
    }
    pub(super) fn draw_customer(&self, customer: &Customer) {
        let screen = self.world_to_screen(customer.pos);
        draw_circle(
            screen.x,
            screen.y - 8.0,
            9.0,
            Color::from_rgba(226, 188, 128, 255),
        );
        draw_rectangle(
            screen.x - 7.0,
            screen.y,
            14.0,
            16.0,
            Color::from_rgba(104, 82, 142, 255),
        );
    }
    pub(super) fn draw_player(&self) {
        let screen = self.world_to_screen(self.player);
        let character = self.player_character_state();
        let facing = vec2(character.facing[0], character.facing[1]);
        if let Some(appearance) = &self.runtime_character_appearance {
            let frame = crate::character_runtime_compositor::RuntimeCharacterAppearance::frame(
                facing,
                crate::character_ecs_runtime::compositor_animation_kind(character.locomotion),
                character.locomotion_phase,
                character
                    .action
                    .map(crate::character_ecs_runtime::compositor_animation_kind),
                character.action_progress(),
            );
            appearance.draw(vec2(screen.x, screen.y + 18.0), frame);
            return;
        }

        // Compatibility is source-backed only. If the modular appearance cannot
        // resolve, the curated character.player.base LPC atlas may keep the player
        // visible while diagnostics report the failed layered appearance. No
        // procedural character artwork is generated in production.
        if let Some(atlas) = &self.player_walk_atlas {
            let row = match crate::character_runtime_compositor::resolve_character_facing(facing) {
                crate::character_runtime_compositor::CharacterFacing::North => 0,
                crate::character_runtime_compositor::CharacterFacing::West => 1,
                crate::character_runtime_compositor::CharacterFacing::South => 2,
                crate::character_runtime_compositor::CharacterFacing::East => 3,
            };
            let column = if character.moving {
                1 + ((character.locomotion_phase * 1.25).floor() as i32).rem_euclid(8)
            } else {
                0
            };
            draw_ellipse(
                screen.x,
                screen.y + 16.0,
                12.0,
                5.0,
                0.0,
                Color::new(0.0, 0.0, 0.0, 0.22),
            );
            draw_texture_ex(
                atlas,
                screen.x - 32.0,
                screen.y - 78.0,
                WHITE,
                DrawTextureParams {
                    source: Some(Rect::new(
                        column as f32 * 64.0,
                        row as f32 * 96.0,
                        64.0,
                        96.0,
                    )),
                    dest_size: Some(vec2(64.0, 96.0)),
                    ..Default::default()
                },
            );
        }
    }
}


#[cfg(test)]
mod h20v2b4_tests {
    use super::*;

    #[test]
    fn wide_zoom_keeps_tree_acceptance_visible() {
        assert!(surface_actor_visible_at_zoom(ObjectKind::Tree, 0.84));
        assert!(!surface_actor_visible_at_zoom(ObjectKind::Herb, 0.84));
        assert!(!surface_actor_visible_at_zoom(ObjectKind::Bush, 0.84));
    }

    #[test]
    fn ordinary_zoom_keeps_all_actor_classes() {
        assert!(surface_actor_visible_at_zoom(ObjectKind::Herb, 1.34));
        assert!(surface_actor_visible_at_zoom(ObjectKind::Bush, 1.34));
    }
}


#[cfg(test)]
mod cliff_depth_sort_tests {
    use super::*;

    #[test]
    fn cliff_face_depth_key_is_at_projected_foot() {
        let key = structural_cliff_face_sort_y(10, 2);
        assert_eq!(key, 12.0 * TILE_SIZE - 0.5);
        let lower_body_actor_feet = 11.0 * TILE_SIZE + 20.0;
        let actor_in_front_of_foot = 12.0 * TILE_SIZE + 20.0;
        assert!(lower_body_actor_feet < key);
        assert!(actor_in_front_of_foot > key);
        assert!(structural_cliff_face_sort_y(10, 4) > key);
    }
}
