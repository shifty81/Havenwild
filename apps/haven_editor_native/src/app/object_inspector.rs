use super::render_helpers::*;
use super::stamp_inspector_panel::*;
use super::*;
use haven_assets::user_asset_registry::authored_object_footprint;

#[path = "object_inspector_geometry.rs"]
mod object_inspector_geometry;
use object_inspector_geometry::*;

fn transition_action_rect(rect: Rect, index: usize) -> Rect {
    let gap = 5.0;
    let width = ((rect.w - gap) / 2.0).max(80.0);
    Rect::new(rect.x + (index % 2) as f32 * (width + gap), rect.y + 204.0 + (index / 2) as f32 * 36.0, width, 30.0)
}

fn travel_object_destination_kind(kind: ObjectKind) -> Option<SceneKind> {
    match kind {
        ObjectKind::Door | ObjectKind::Stairs => Some(SceneKind::Interior),
        ObjectKind::CaveEntrance => Some(SceneKind::Cave),
        _ => None,
    }
}

fn travel_object_create_label(kind: ObjectKind) -> Option<&'static str> {
    match kind {
        ObjectKind::Door => Some("Create Interior"),
        ObjectKind::Stairs => Some("Create Floor"),
        ObjectKind::CaveEntrance => Some("Create Cave"),
        _ => None,
    }
}

impl EditorApp {
    /// W63 canonical right-dock Properties surface. This bypasses the retired
    /// Scene Assets/Intake/Library sub-tabs; those workflows now live under the
    /// single project-wide Assets tab.
    pub(crate) fn draw_scene_properties(&self, rect: Rect) {
        self.draw_object_inspector(rect);
    }

    pub(crate) fn handle_scene_properties_click(&mut self, mx: f32, my: f32, rect: Rect) -> bool {
        self.handle_object_inspector_click(mx, my, rect)
    }


    fn draw_terrain_tuple_inspector(&self, rect: Rect, scene: &haven_core::SceneMap) {
        draw_section_header(
            Rect::new(rect.x, rect.y, rect.w, 28.0),
            "Terrain Tuple Inspector",
            Some("Havenwild Standard v1"),
        );
        draw_scissored_text(
            &format!("Cursor {}, {}", self.scene_cursor_x, self.scene_cursor_y),
            rect.x,
            rect.y + 48.0,
            rect.w,
            15.0,
            MUTED,
        );

        let tuple =
            haven_world::semantic_tuple_at(&scene.map, self.scene_cursor_x, self.scene_cursor_y);
        let corners = [
            ("Top Left", tuple.top_left),
            ("Top Right", tuple.top_right),
            ("Bottom Left", tuple.bottom_left),
            ("Bottom Right", tuple.bottom_right),
        ];
        let resolver = haven_world::embedded_terrain_tuple_resolver().ok();
        let gap = 5.0;
        let cell_w = (rect.w - gap) * 0.5;
        for (index, (label, ordinal)) in corners.into_iter().enumerate() {
            let col = (index % 2) as f32;
            let row = (index / 2) as f32;
            let x = rect.x + col * (cell_w + gap);
            let y = rect.y + 68.0 + row * 50.0;
            let terrain_code = ordinal
                .and_then(|value| resolver.and_then(|catalog| catalog.terrain_code(value)))
                .unwrap_or("Unknown");
            draw_rectangle(x, y, cell_w, 44.0, PANEL_BG);
            draw_rectangle_lines(x, y, cell_w, 44.0, 1.0, PANEL_EDGE);
            draw_scissored_text(label, x + 6.0, y + 14.0, cell_w - 12.0, 12.0, MUTED);
            draw_scissored_text(terrain_code, x + 6.0, y + 31.0, cell_w - 42.0, 14.0, TEXT);
            if let Some(ordinal) = ordinal {
                draw_badge(Rect::new(x + cell_w - 36.0, y + 17.0, 30.0, 20.0), &ordinal.to_string(), false);
            }
        }

        let compatibility = haven_world::terrain_tuple_compatibility(tuple);
        draw_scissored_text(
            match compatibility {
                haven_world::TerrainTupleCompatibility::Compatible => {
                    "Compatibility: supported contacts"
                }
                haven_world::TerrainTupleCompatibility::UnlistedCombination => {
                    "Compatibility: unsupported contact set"
                }
            },
            rect.x,
            rect.y + 178.0,
            rect.w,
            14.0,
            if matches!(
                compatibility,
                haven_world::TerrainTupleCompatibility::Compatible
            ) {
                GOOD
            } else {
                WARN
            },
        );
        draw_section_header(
            Rect::new(rect.x, rect.y + 194.0, rect.w, 26.0),
            "Tuple Presentation",
            Some("Exact + Contact Support"),
        );
        match self.terrain_tuple_resolution_at_cursor() {
            Ok(resolution) => {
                let (label, active) = match resolution.status {
                    haven_world::TerrainTupleResolutionStatus::Exact => ("Exact", true),
                    haven_world::TerrainTupleResolutionStatus::ExactDuplicateCanonical => {
                        ("Canonical Duplicate", false)
                    }
                    haven_world::TerrainTupleResolutionStatus::Unresolved if matches!(compatibility, haven_world::TerrainTupleCompatibility::Compatible) => ("Supported Junction", true),
                    haven_world::TerrainTupleResolutionStatus::Unresolved => ("Unsupported", false),
                };
                draw_badge(
                    Rect::new(rect.x, rect.y + 226.0, rect.w.min(180.0), 22.0),
                    label,
                    active,
                );
                draw_scissored_text(
                    &format!("Signature: {}", resolution.signature),
                    rect.x,
                    rect.y + 270.0,
                    rect.w,
                    15.0,
                    TEXT,
                );
                draw_scissored_text(
                    &format!(
                        "Exact tuple tile: {}",
                        resolution
                            .selected_tile_id
                            .map_or_else(|| "None".to_string(), |id| id.to_string())
                    ),
                    rect.x,
                    rect.y + 292.0,
                    rect.w,
                    15.0,
                    TEXT,
                );
                if !resolution.duplicate_alternatives.is_empty() {
                    draw_wrapped(
                        &format!("Alternatives: {:?}", resolution.duplicate_alternatives),
                        rect.x,
                        rect.y + 314.0,
                        rect.w,
                        14.0,
                        WARN,
                    );
                }
            }
            Err(error) => {
                draw_badge(
                    Rect::new(rect.x, rect.y + 226.0, rect.w.min(180.0), 22.0),
                    "Catalog Error",
                    false,
                );
                draw_wrapped(&error, rect.x, rect.y + 294.0, rect.w, 14.0, WARN);
            }
        }

        let repair_available = self.terrain_transition_repair_document_path().is_some();
        draw_editor_widget(terrain_transition_workbench::terrain_repair_button_rect(rect), "Open Repair Document", repair_available);
        draw_editor_widget(terrain_transition_workbench::terrain_lab_button_rect(rect), "Lab", true);

        let tile = scene.map.get(self.scene_cursor_x, self.scene_cursor_y);
        let gameplay = haven_core::terrain_gameplay_profile(tile);
        draw_section_header(
            Rect::new(rect.x, rect.y + 404.0, rect.w, 26.0),
            "Gameplay Profile",
            Some("Semantic Authority"),
        );
        draw_scissored_text(
            &format!("TileKind: {}", tile.label()),
            rect.x,
            rect.y + 456.0,
            rect.w,
            15.0,
            TEXT,
        );
        draw_scissored_text(
            &format!(
                "Collision: {:?}  Move: {}",
                gameplay.collision, gameplay.movement_cost
            ),
            rect.x,
            rect.y + 480.0,
            rect.w,
            15.0,
            TEXT,
        );
        draw_scissored_text(
            &format!(
                "Water: {}  Farming: {}",
                gameplay.water_depth.label(),
                gameplay.farming.label()
            ),
            rect.x,
            rect.y + 504.0,
            rect.w,
            15.0,
            TEXT,
        );
        draw_scissored_text(
            &format!(
                "Build: {}  Footstep: {}",
                gameplay.building.label(),
                gameplay.footstep.label()
            ),
            rect.x,
            rect.y + 528.0,
            rect.w,
            15.0,
            TEXT,
        );
        draw_wrapped(
            "Tuple artwork and shaders remain presentation-only; gameplay consumers use this semantic profile.",
            rect.x,
            rect.y + 552.0,
            rect.w,
            14.0,
            MUTED,
        );
    }


    pub(crate) fn draw_object_inspector(&self, rect: Rect) {
        let Some(scene) = self.model.world.scenes.get(self.selected_scene) else {
            draw_editor_text("No scene loaded", rect.x, rect.y + 22.0, 20.0, WARN);
            return;
        };
        if let Some(transition_id) = self.selected_transition_id() {
            if let Some(transition) = scene.transition(transition_id) {
                self.draw_transition_inspector(rect, transition);
                return;
            }
        }
        if let Some(stamp) = self
            .selected_stamp_instance_id()
            .and_then(|id| scene.map.stamp(id))
        {
            self.draw_stamp_inspector(rect, stamp);
            return;
        }
        let Some(object) = self
            .selected_object_id()
            .and_then(|id| scene.map.object(id))
            .copied()
        else {
            if let Some(instance) = self.building_at_scene_cursor() {
                self.draw_building_authoring_inspector(rect, &instance);
                return;
            }
            if scene.kind != SceneKind::Exterior {
                self.draw_enclosed_scene_inspector(rect, scene);
                return;
            }
            self.draw_terrain_tuple_inspector(rect, scene);
            return;
        };

        draw_editor_text("Object Inspector", rect.x, rect.y + 22.0, 24.0, TEXT);
        draw_editor_text(
            &format!("{}  {}", object.kind.label(), object.id),
            rect.x,
            rect.y + 48.0,
            17.0,
            GOOD,
        );
        for (line, offset) in [
            (format!("Anchor: {}, {}", object.x, object.y), 72.0),
            (format!("Asset key: object/{}", object.kind.code()), 92.0),
            (
                "Provenance: project-generated/runtime catalog".to_string(),
                112.0,
            ),
        ] {
            draw_scissored_text(&line, rect.x, rect.y + offset, rect.w, 15.0, MUTED);
        }

        draw_section_header(
            Rect::new(rect.x, rect.y + 124.0, rect.w, 24.0),
            "Footprint Target",
            Some(self.footprint_edit_target.label()),
        );
        for (index, target) in [
            FootprintEditTarget::Visual,
            FootprintEditTarget::Collision,
            FootprintEditTarget::Interaction,
        ]
        .into_iter()
        .enumerate()
        {
            draw_editor_widget(
                footprint_target_rect(rect, index),
                target.label(),
                target == self.footprint_edit_target,
            );
        }

        let (offset_x, offset_y, width, height) =
            footprint_values(object, self.footprint_edit_target);
        draw_property_row(rect, 0, "Offset X", offset_x);
        draw_property_row(rect, 1, "Offset Y", offset_y);
        draw_property_row(rect, 2, "Width", width);
        draw_property_row(rect, 3, "Height", height);

        draw_section_header(
            Rect::new(rect.x, rect.y + 362.0, rect.w, 24.0),
            "Behavior",
            Some("Runtime Flags"),
        );
        draw_editor_widget(
            behavior_button_rect(rect, 0),
            if object.footprint.blocks_movement {
                "Blocks: Yes"
            } else {
                "Blocks: No"
            },
            object.footprint.blocks_movement,
        );
        draw_editor_widget(
            behavior_button_rect(rect, 1),
            if object.footprint.occludes_player {
                "Occludes: Yes"
            } else {
                "Occludes: No"
            },
            object.footprint.occludes_player,
        );
        draw_editor_widget(
            behavior_button_rect(rect, 2),
            if object.footprint.fade_when_player_behind {
                "Fade: Yes"
            } else {
                "Fade: No"
            },
            object.footprint.fade_when_player_behind,
        );

        draw_section_header(
            Rect::new(rect.x, rect.y + 452.0, rect.w, 24.0),
            "Object Actions",
            Some("Selection"),
        );
        for (index, label) in [
            "Focus",
            "Duplicate",
            "Delete",
            "Reset Target",
            "Default All",
        ]
        .into_iter()
        .enumerate()
        {
            let tone = match index {
                0 => WidgetTone::Primary,
                2 => WidgetTone::Destructive,
                3 | 4 => WidgetTone::Quiet,
                _ => WidgetTone::Standard,
            };
            draw_editor_widget_tone(object_action_rect(rect, index), label, false, tone);
        }
        if let Some(label) = travel_object_create_label(object.kind) {
            draw_editor_widget_tone(
                object_action_rect(rect, 5),
                label,
                false,
                WidgetTone::Primary,
            );
        }
        draw_editor_text(
            "Blue visual | green collision | gold interaction",
            rect.x,
            rect.y + 592.0,
            14.0,
            MUTED,
        );
        draw_wrapped(
            &object.footprint_label(),
            rect.x,
            rect.y + 614.0,
            rect.w,
            14.0,
            TEXT,
        );
    }

    pub(crate) fn handle_object_inspector_click(&mut self, mx: f32, my: f32, rect: Rect) -> bool {
        let point = vec2(mx, my);
        if let Some(transition_id) = self.selected_transition_id() {
            if (0..6).any(|index| transition_action_rect(rect, index).contains(point)) {
                let action = (0..6).find(|index| transition_action_rect(rect, *index).contains(point)).unwrap_or(0);
                match action {
                    0 => { self.selected_transition_target = cycle_index(self.selected_transition_target, self.model.world.scenes.len(), -1); self.status_message = format!("Transition target: {}", self.selected_transition_target_scene().label()); }
                    1 => { self.selected_transition_target = cycle_index(self.selected_transition_target, self.model.world.scenes.len(), 1); self.status_message = format!("Transition target: {}", self.selected_transition_target_scene().label()); }
                    2 => {
                        let Some(scene_id) = self.active_scene_id() else { return true; };
                        let target = self.selected_transition_target_scene();
                        let spawn = self.model.world.scene_by_id(&target).map(|scene| (scene.spawn_x, scene.spawn_y)).unwrap_or((0, 0));
                        self.status_message = update_scene_transition_destination(&mut self.model.world, &mut self.command_bus, &self.model.project.project_id, EditorCommandSource::MainEditor, scene_id, transition_id, target, spawn.0, spawn.1).map(|outcome| outcome.message).unwrap_or_else(|error| error);
                    }
                    3 => {
                        let target = self.model.world.scenes.get(self.selected_scene).and_then(|scene| scene.transition(transition_id)).map(|transition| (transition.target.project_id().clone(), transition.spawn_x, transition.spawn_y));
                        if let Some((target_id, spawn_x, spawn_y)) = target {
                            if let Some(index) = self.model.world.scenes.position(&target_id) {
                                self.select_scene_index(index); self.model.world.set_active_scene(target_id.clone()).ok(); self.scene_cursor_x = spawn_x; self.scene_cursor_y = spawn_y; self.viewport_mode = EditorViewportMode::SceneMap; self.status_message = format!("Opened {} at arrival {}, {}", target_id.label(), spawn_x, spawn_y);
                            } else { self.status_message = format!("Destination {} is not loaded", target_id.label()); }
                        }
                    }
                    4 => self.create_linked_destination_for_transition(transition_id, SceneKind::Interior),
                    5 => self.create_linked_destination_for_transition(transition_id, SceneKind::Cave),
                    _ => {}
                }
                return true;
            }
        }

        let mouse = vec2(mx, my);
        if !rect.contains(mouse) {
            return false;
        }
        if self.selected_object_id().is_none() && self.selected_stamp_instance_id().is_none() {
            if self.model.world.scenes.get(self.selected_scene).is_some_and(|scene| scene.kind == SceneKind::Exterior) {
                if terrain_transition_workbench::terrain_repair_button_rect(rect).contains(mouse) {
                    self.open_current_terrain_transition_repair_document();
                    return true;
                }
                if terrain_transition_workbench::terrain_lab_button_rect(rect).contains(mouse) {
                    self.reveal_terrain_transition_lab();
                    return true;
                }
            }
            if self.building_at_scene_cursor().is_some() {
                return self.handle_building_authoring_inspector_click(mx, my, rect);
            }
            if self
                .model
                .world
                .scenes
                .get(self.selected_scene)
                .is_some_and(|scene| scene.kind != SceneKind::Exterior)
            {
                return self.handle_enclosed_scene_inspector_click(mx, my, rect);
            }
        }
        if self.selected_stamp_instance_id().is_some() {
            for index in 0..4 {
                if stamp_resize_rect(rect, index).contains(mouse) {
                    match index {
                        0 => self.resize_selected_stamp(-1, 0),
                        1 => self.resize_selected_stamp(1, 0),
                        2 => self.resize_selected_stamp(0, -1),
                        3 => self.resize_selected_stamp(0, 1),
                        _ => {}
                    }
                    return true;
                }
            }
            if stamp_reset_size_rect(rect).contains(mouse) {
                self.reset_selected_stamp_size();
            } else if stamp_action_rect(rect, 0).contains(mouse) {
                self.frame_current_selection();
            } else if stamp_action_rect(rect, 1).contains(mouse) {
                self.delete_current_selection();
            }
            return true;
        }
        for (index, target) in [
            FootprintEditTarget::Visual,
            FootprintEditTarget::Collision,
            FootprintEditTarget::Interaction,
        ]
        .into_iter()
        .enumerate()
        {
            if footprint_target_rect(rect, index).contains(mouse) {
                self.footprint_edit_target = target;
                self.status_message = format!("Footprint target: {}", target.label());
                return true;
            }
        }
        for row in 0..4 {
            if property_minus_rect(rect, row).contains(mouse) {
                self.adjust_selected_object_property(row, -1);
                return true;
            }
            if property_plus_rect(rect, row).contains(mouse) {
                self.adjust_selected_object_property(row, 1);
                return true;
            }
        }
        for index in 0..3 {
            if behavior_button_rect(rect, index).contains(mouse) {
                self.toggle_selected_object_behavior(index);
                return true;
            }
        }
        for index in 0..6 {
            if !object_action_rect(rect, index).contains(mouse) {
                continue;
            }
            match index {
                0 => self.frame_current_selection(),
                1 => self.duplicate_current_selection(),
                2 => self.delete_current_selection(),
                3 => self.reset_selected_object_target(),
                4 => self.reset_selected_object_all(),
                5 => {
                    let selected = self
                        .model
                        .world
                        .scenes
                        .get(self.selected_scene)
                        .and_then(|scene| self.selected_object_id().and_then(|id| scene.map.object(id)))
                        .copied();
                    if let Some(object) = selected {
                        if let Some(kind) = travel_object_destination_kind(object.kind) {
                            self.create_linked_destination_for_object(object, kind);
                        }
                    }
                }
                _ => {}
            }
            return true;
        }
        true
    }

    pub(crate) fn draw_selected_object_footprints(&self) {
        if !self.workspace_shell.right_panel_visible
            || self.workspace_shell.right_dock_tab != super::workspace_shell::RightDockTab::Properties
        {
            return;
        }
        let Some(scene) = self.model.world.scenes.get(self.selected_scene) else {
            return;
        };
        if let Some(stamp) = self
            .selected_stamp_instance_id()
            .and_then(|id| scene.map.stamp(id))
        {
            let category = self
                .stamp_registry
                .entry(&stamp.stamp_key)
                .map(|definition| definition.category.as_str());
            let layer = super::canvas_layers::canvas_layer_kind_for_stamp(&stamp.stamp_key, category);
            if !self.canvas_layer_kind_visible(layer) {
                return;
            }
            draw_footprint_rect(stamp.visual_rect(), Color::new(0.40, 0.66, 1.0, 0.95));
            draw_footprint_rect(stamp.collision_rect(), Color::new(0.36, 0.92, 0.48, 0.95));
            draw_footprint_rect(stamp.interaction_rect(), Color::new(1.0, 0.82, 0.30, 0.95));
            let foot = haven_render::stamp_foot_tiles(stamp);
            draw_line(foot.x - 0.22, foot.y, foot.x + 0.22, foot.y, 0.08, TEXT);
            draw_line(foot.x, foot.y - 0.22, foot.x, foot.y + 0.22, 0.08, TEXT);
            draw_circle_lines(foot.x, foot.y, 0.18, 0.07, TEXT);
            return;
        }
        let Some(object) = self
            .selected_object_id()
            .and_then(|id| scene.map.object(id))
            .copied()
        else {
            return;
        };
        let layer = if matches!(
            object.kind,
            ObjectKind::Door | ObjectKind::Stairs | ObjectKind::Fence | ObjectKind::CaveEntrance
        ) {
            super::canvas_layers::CanvasLayerKind::Structures
        } else {
            super::canvas_layers::CanvasLayerKind::Objects
        };
        if !self.canvas_layer_kind_visible(layer) {
            return;
        }
        draw_footprint_rect(object.visual_rect(), Color::new(0.40, 0.66, 1.0, 0.95));
        draw_footprint_rect(object.collision_rect(), Color::new(0.36, 0.92, 0.48, 0.95));
        draw_footprint_rect(object.interaction_rect(), Color::new(1.0, 0.82, 0.30, 0.95));
        let foot = haven_render::object_foot_tiles(object);
        draw_line(foot.x - 0.22, foot.y, foot.x + 0.22, foot.y, 0.08, TEXT);
        draw_line(foot.x, foot.y - 0.22, foot.x, foot.y + 0.22, 0.08, TEXT);
        draw_circle_lines(foot.x, foot.y, 0.18, 0.07, TEXT);
    }

    fn draw_transition_inspector(&self, rect: Rect, transition: &haven_core::Transition) {
        draw_editor_text("Transition Inspector", rect.x, rect.y + 22.0, 24.0, TEXT);
        draw_scissored_text(&transition.label, rect.x, rect.y + 50.0, rect.w, 16.0, GOOD);
        for (line, y) in [
            (format!("ID: {}", transition.id), 76.0),
            (format!("Area: {},{} {}x{}", transition.x, transition.y, transition.w, transition.h), 98.0),
            (format!("Target: {}", transition.target.label()), 120.0),
            (format!("Arrival: {}, {}", transition.spawn_x, transition.spawn_y), 142.0),
        ] { draw_scissored_text(&line, rect.x, rect.y + y, rect.w, 14.0, MUTED); }
        draw_section_header(Rect::new(rect.x, rect.y + 170.0, rect.w, 24.0), "Destination", Some("Visual scene link"));
        draw_editor_widget(transition_action_rect(rect, 0), "Previous Target", false);
        draw_editor_widget(transition_action_rect(rect, 1), "Next Target", false);
        draw_editor_widget(transition_action_rect(rect, 2), "Apply Target + Spawn", false);
        draw_editor_widget(transition_action_rect(rect, 3), "Open Destination", false);
        draw_editor_widget(transition_action_rect(rect, 4), "Create Interior + Link", false);
        draw_editor_widget(transition_action_rect(rect, 5), "Create Cave + Link", false);
        draw_wrapped(
            "Choose a destination with Previous/Next, then Apply, or create a new linked Interior/Cave in one step. New destinations receive a usable floor, perimeter walls, spawn marker, and automatic return transition, then open immediately for authoring.",
            rect.x, rect.y + 316.0, rect.w, 13.0, MUTED,
        );
    }

    fn create_linked_destination_for_transition(
        &mut self,
        transition_id: haven_editor::TransitionId,
        kind: SceneKind,
    ) {
        let Some(source_scene) = self.model.world.scenes.get(self.selected_scene) else {
            self.status_message = "No source scene is selected".to_string();
            return;
        };
        let source_id = source_scene.id.clone();
        let source_name = source_scene.name.clone();
        let source_dimensions = source_scene.dimensions;
        let source_biome = source_scene.biome;
        let Some(source_transition) = source_scene.transition(transition_id).cloned() else {
            self.status_message = format!("Transition {transition_id} is no longer available");
            return;
        };
        self.create_linked_destination(
            source_id,
            source_name,
            source_dimensions,
            source_biome,
            (
                source_transition.x,
                source_transition.y,
                source_transition.w,
                source_transition.h,
            ),
            Some(transition_id),
            kind,
        );
    }

    fn create_linked_destination_for_object(&mut self, object: PlacedObject, kind: SceneKind) {
        let Some(source_scene) = self.model.world.scenes.get(self.selected_scene) else {
            self.status_message = "No source scene is selected".to_string();
            return;
        };
        let (x, y, w, h) = object.interaction_rect();
        if w <= 0 || h <= 0 {
            self.status_message = format!(
                "{} has no interaction footprint for travel",
                object.kind.label()
            );
            return;
        }
        if let Some(existing) = source_scene.transition_id_at(x, y) {
            self.create_linked_destination_for_transition(existing, kind);
            return;
        }
        let source_id = source_scene.id.clone();
        let source_name = source_scene.name.clone();
        let source_dimensions = source_scene.dimensions;
        let source_biome = source_scene.biome;
        self.create_linked_destination(
            source_id,
            source_name,
            source_dimensions,
            source_biome,
            (x, y, w.max(1), h.max(1)),
            None,
            kind,
        );
    }

    #[allow(clippy::too_many_arguments)]
    pub(crate) fn create_linked_destination(
        &mut self,
        source_id: ProjectSceneId,
        source_name: String,
        source_dimensions: haven_core::SceneDimensions,
        source_biome: SceneBiome,
        source_rect: (i32, i32, i32, i32),
        source_transition_id: Option<haven_editor::TransitionId>,
        kind: SceneKind,
    ) {
        let (source_x, source_y, source_w, source_h) = source_rect;
        let suffix = match kind {
            SceneKind::Interior => "interior",
            SceneKind::Cave => "cave",
            SceneKind::Exterior => "scene",
        };
        let base_code = format!(
            "{}_{}_{}_{}",
            source_id.code(), suffix, source_x, source_y
        );
        let mut candidate = ProjectSceneId::new(base_code.clone());
        let mut ordinal = 2usize;
        while self.model.world.scene_by_id(&candidate).is_some() {
            candidate = ProjectSceneId::new(format!("{base_code}_{ordinal}"));
            ordinal += 1;
        }
        let display_name = match kind {
            SceneKind::Interior => format!("{source_name} Interior"),
            SceneKind::Cave => format!("{source_name} Cave"),
            SceneKind::Exterior => format!("{source_name} Scene"),
        };
        let (interior_width, interior_height, skin) = match kind {
            SceneKind::Interior => (22usize, 16usize, haven_core::EnclosedSceneSkin::House),
            SceneKind::Cave => (30usize, 22usize, haven_core::EnclosedSceneSkin::Cave),
            SceneKind::Exterior => {
                self.status_message = "Linked exterior generation is not an enclosed-scene operation".to_string();
                return;
            }
        };
        let entry_x = interior_width / 2;
        let spec = match haven_core::EnclosedSceneSpec::rectangular(
            candidate.clone(),
            display_name.clone(),
            skin,
            interior_width,
            interior_height,
            entry_x,
        ) {
            Ok(spec) => spec,
            Err(error) => {
                self.status_message = format!("Unable to define linked scene: {error}");
                return;
            }
        };
        let doorway_x = spec.entry_threshold[0];
        let doorway_y = spec.entry_threshold[1];
        let mut destination = match spec.build() {
            Ok(scene) => scene,
            Err(error) => {
                self.status_message = format!("Unable to create linked scene: {error}");
                return;
            }
        };
        if kind == SceneKind::Interior {
            destination.biome = source_biome;
        }
        let destination_spawn = (destination.spawn_x, destination.spawn_y);

        if let Err(error) = create_project_scene(
            &mut self.model.world,
            &mut self.command_bus,
            &self.model.project.project_id,
            EditorCommandSource::MainEditor,
            destination,
        ) {
            self.status_message = format!("Unable to create linked scene: {error}");
            return;
        }

        let source_link = if let Some(transition_id) = source_transition_id {
            update_scene_transition_destination(
                &mut self.model.world,
                &mut self.command_bus,
                &self.model.project.project_id,
                EditorCommandSource::MainEditor,
                source_id.clone(),
                transition_id,
                candidate.clone(),
                destination_spawn.0,
                destination_spawn.1,
            )
        } else {
            create_scene_transition(
                &mut self.model.world,
                &mut self.command_bus,
                &self.model.project.project_id,
                EditorCommandSource::MainEditor,
                source_id.clone(),
                source_x,
                source_y,
                source_w.max(1),
                source_h.max(1),
                candidate.clone(),
                destination_spawn.0,
                destination_spawn.1,
                format!("To {display_name}"),
            )
        };
        if let Err(error) = source_link {
            self.status_message = format!("Created {display_name}, but linking failed: {error}");
            return;
        }

        let return_x = source_x.clamp(0, source_dimensions.width as i32 - 1);
        let return_y = (source_y + source_h).clamp(0, source_dimensions.height as i32 - 1);
        if let Err(error) = create_scene_transition(
            &mut self.model.world,
            &mut self.command_bus,
            &self.model.project.project_id,
            EditorCommandSource::MainEditor,
            candidate.clone(),
            doorway_x,
            doorway_y,
            1,
            1,
            source_id.clone(),
            return_x,
            return_y,
            format!("Return to {source_name}"),
        ) {
            self.status_message = format!(
                "Created and linked {display_name}, but automatic return link needs repair: {error}"
            );
            return;
        }

        if let Some(index) = self.model.world.scenes.position(&candidate) {
            self.select_scene_index(index);
            let _ = self.model.world.set_active_scene(candidate.clone());
            self.scene_cursor_x = destination_spawn.0;
            self.scene_cursor_y = destination_spawn.1;
            self.viewport_mode = EditorViewportMode::SceneMap;
            self.focus_right_dock(super::workspace_shell::RightDockTab::Assets);
            self.selection.clear();
            self.scene_canvas = CanvasCameraState::default();
        }
        self.status_message = format!(
            "Created {display_name}, linked both directions, and opened it for authoring"
        );
    }

    fn draw_stamp_inspector(&self, rect: Rect, stamp: &PlacedStamp) {
        let definition = self.stamp_registry.entry(&stamp.stamp_key);
        let expandable = definition.and_then(|entry| entry.expandable);
        draw_editor_text("Multi-Tile Stamp", rect.x, rect.y + 22.0, 24.0, TEXT);
        draw_scissored_text(
            &format!(
                "{}  {}",
                definition.map_or(stamp.stamp_key.as_str(), |entry| entry.label.as_str()),
                stamp.id
            ),
            rect.x,
            rect.y + 48.0,
            rect.w,
            17.0,
            GOOD,
        );
        for (line, offset) in [
            (format!("Stable asset: stamp/{}", stamp.stamp_key), 74.0),
            (format!("Anchor: {}, {}", stamp.x, stamp.y), 96.0),
            (
                format!(
                    "Category: {}",
                    definition.map_or("unresolved", |entry| entry.category.as_str())
                ),
                118.0,
            ),
            (
                if let Some(expandable) = expandable {
                    format!(
                        "Expandable LPC 9-slice | minimum {}x{} | freeform {}",
                        expandable.minimum_w,
                        expandable.minimum_h,
                        if expandable.supports_freeform {
                            "mapped"
                        } else {
                            "no"
                        }
                    )
                } else {
                    "Fixed authored stamp".to_string()
                },
                140.0,
            ),
        ] {
            draw_scissored_text(&line, rect.x, rect.y + offset, rect.w, 15.0, MUTED);
        }

        draw_section_header(
            Rect::new(rect.x, rect.y + 160.0, rect.w, 24.0),
            "Placed Footprint",
            Some("Visual / Collision / Interaction"),
        );
        draw_wrapped(
            &stamp_footprint_label(stamp),
            rect.x,
            rect.y + 206.0,
            rect.w,
            14.0,
            TEXT,
        );

        if expandable.is_some() {
            draw_section_header(
                Rect::new(rect.x, rect.y + 262.0, rect.w, 24.0),
                "Resize Stamp",
                Some("LPC 9-Slice"),
            );
            for (index, label) in ["Width -", "Width +", "Height -", "Height +"]
                .into_iter()
                .enumerate()
            {
                draw_editor_widget(stamp_resize_rect(rect, index), label, false);
            }
            draw_editor_widget(stamp_reset_size_rect(rect), "Reset 3x3 Source Size", false);
            draw_wrapped(
                "Expansion repeats LPC edge and center cells without scaling pixels. The mapped 2x2 inner-corner block is reserved for the freeform/blob boundary editor pass.",
                rect.x,
                rect.y + 372.0,
                rect.w,
                13.0,
                MUTED,
            );
        } else {
            draw_wrapped(
                "This stamp uses its authored fixed footprint. Edit the reusable definition through Asset Intake.",
                rect.x,
                rect.y + 286.0,
                rect.w,
                14.0,
                MUTED,
            );
        }

        draw_section_header(
            Rect::new(rect.x, rect.y + 430.0, rect.w, 24.0),
            "Stamp Actions",
            Some("Selection"),
        );
        draw_editor_widget_tone(
            stamp_action_rect(rect, 0),
            "Focus",
            false,
            WidgetTone::Primary,
        );
        draw_editor_widget_tone(
            stamp_action_rect(rect, 1),
            "Delete",
            false,
            WidgetTone::Destructive,
        );
        draw_wrapped(
            definition.map_or(
                "Registry entry missing; fallback rendering will be used.",
                |entry| entry.license.as_str(),
            ),
            rect.x,
            rect.y + 532.0,
            rect.w,
            14.0,
            MUTED,
        );
    }

    fn selected_stamp_value(&self) -> Option<PlacedStamp> {
        let scene = self.model.world.scenes.get(self.selected_scene)?;
        self.selected_stamp_instance_id()
            .and_then(|id| scene.map.stamp(id))
            .cloned()
    }

    fn resize_selected_stamp(&mut self, delta_w: i32, delta_h: i32) {
        let Some(mut stamp) = self.selected_stamp_value() else {
            self.status_message = "No stamp selected".to_string();
            return;
        };
        let Some(definition) = self.stamp_registry.entry(&stamp.stamp_key) else {
            self.status_message = "Selected stamp is missing from the registry".to_string();
            return;
        };
        let Some(expandable) = definition.expandable else {
            self.status_message = "Selected stamp has a fixed authored size".to_string();
            return;
        };
        let width = (stamp.footprint.visual_w + delta_w).max(expandable.minimum_w);
        let height = (stamp.footprint.visual_h + delta_h).max(expandable.minimum_h);
        set_rectangular_stamp_size(&mut stamp, width, height);
        self.apply_stamp_candidate(
            stamp,
            format!("Resize expandable pond to {}x{}", width, height),
            (expandable.minimum_w, expandable.minimum_h),
        );
    }

    fn reset_selected_stamp_size(&mut self) {
        let Some(mut stamp) = self.selected_stamp_value() else {
            self.status_message = "No stamp selected".to_string();
            return;
        };
        let Some(definition) = self.stamp_registry.entry(&stamp.stamp_key) else {
            self.status_message = "Selected stamp is missing from the registry".to_string();
            return;
        };
        let minimum = definition.minimum_visual_size();
        set_rectangular_stamp_size(&mut stamp, minimum.0, minimum.1);
        self.apply_stamp_candidate(stamp, "Reset expandable pond size".to_string(), minimum);
    }

    fn apply_stamp_candidate(
        &mut self,
        candidate: PlacedStamp,
        action: String,
        minimum: (i32, i32),
    ) {
        let Some(scene_id) = self.active_scene_id() else {
            return;
        };
        let request = StampUpdateRequest::new(
            EditorCommandSource::MainEditor,
            scene_id,
            candidate,
            minimum,
            action,
        );
        match update_scene_stamp(
            &mut self.model.world,
            &mut self.command_bus,
            &self.model.project.project_id,
            request,
        ) {
            Ok(outcome) => {
                self.status_message = outcome.message;
                self.refresh_scene_selection_bounds();
            }
            Err(error) => self.status_message = error,
        }
    }

    fn selected_object_value(&self) -> Option<PlacedObject> {
        let scene = self.model.world.scenes.get(self.selected_scene)?;
        self.selected_object_id()
            .and_then(|id| scene.map.object(id))
            .copied()
    }

    fn adjust_selected_object_property(&mut self, row: usize, delta: i32) {
        let Some(mut object) = self.selected_object_value() else {
            self.status_message = "No object selected".to_string();
            return;
        };
        let fp = &mut object.footprint;
        match (self.footprint_edit_target, row) {
            (FootprintEditTarget::Visual, 0) => fp.visual_offset_x += delta,
            (FootprintEditTarget::Visual, 1) => fp.visual_offset_y += delta,
            (FootprintEditTarget::Visual, 2) => fp.visual_w = (fp.visual_w + delta).max(1),
            (FootprintEditTarget::Visual, 3) => fp.visual_h = (fp.visual_h + delta).max(1),
            (FootprintEditTarget::Collision, 0) => fp.collision_offset_x += delta,
            (FootprintEditTarget::Collision, 1) => fp.collision_offset_y += delta,
            (FootprintEditTarget::Collision, 2) => fp.collision_w = (fp.collision_w + delta).max(0),
            (FootprintEditTarget::Collision, 3) => fp.collision_h = (fp.collision_h + delta).max(0),
            (FootprintEditTarget::Interaction, 0) => fp.interaction_offset_x += delta,
            (FootprintEditTarget::Interaction, 1) => fp.interaction_offset_y += delta,
            (FootprintEditTarget::Interaction, 2) => {
                fp.interaction_w = (fp.interaction_w + delta).max(0)
            }
            (FootprintEditTarget::Interaction, 3) => {
                fp.interaction_h = (fp.interaction_h + delta).max(0)
            }
            _ => return,
        }
        self.apply_object_candidate(
            object,
            format!("Edited {} footprint", self.footprint_edit_target.label()),
        );
    }

    fn toggle_selected_object_behavior(&mut self, index: usize) {
        let Some(mut object) = self.selected_object_value() else {
            self.status_message = "No object selected".to_string();
            return;
        };
        match index {
            0 => object.footprint.blocks_movement = !object.footprint.blocks_movement,
            1 => {
                object.footprint.occludes_player = !object.footprint.occludes_player;
                if !object.footprint.occludes_player {
                    object.footprint.fade_when_player_behind = false;
                }
            }
            2 => {
                object.footprint.fade_when_player_behind =
                    !object.footprint.fade_when_player_behind;
                if object.footprint.fade_when_player_behind {
                    object.footprint.occludes_player = true;
                }
            }
            _ => return,
        }
        self.apply_object_candidate(object, "Edited object behavior".to_string());
    }

    fn reset_selected_object_target(&mut self) {
        let Some(mut object) = self.selected_object_value() else {
            self.status_message = "No object selected".to_string();
            return;
        };
        let default = authored_object_footprint(object.kind);
        match self.footprint_edit_target {
            FootprintEditTarget::Visual => {
                object.footprint.visual_offset_x = default.visual_offset_x;
                object.footprint.visual_offset_y = default.visual_offset_y;
                object.footprint.visual_w = default.visual_w;
                object.footprint.visual_h = default.visual_h;
            }
            FootprintEditTarget::Collision => {
                object.footprint.collision_offset_x = default.collision_offset_x;
                object.footprint.collision_offset_y = default.collision_offset_y;
                object.footprint.collision_w = default.collision_w;
                object.footprint.collision_h = default.collision_h;
                object.footprint.blocks_movement = default.blocks_movement;
            }
            FootprintEditTarget::Interaction => {
                object.footprint.interaction_offset_x = default.interaction_offset_x;
                object.footprint.interaction_offset_y = default.interaction_offset_y;
                object.footprint.interaction_w = default.interaction_w;
                object.footprint.interaction_h = default.interaction_h;
            }
        }
        self.apply_object_candidate(
            object,
            format!("Reset {} footprint", self.footprint_edit_target.label()),
        );
    }

    fn reset_selected_object_all(&mut self) {
        let Some(mut object) = self.selected_object_value() else {
            self.status_message = "No object selected".to_string();
            return;
        };
        object.footprint = authored_object_footprint(object.kind);
        self.apply_object_candidate(object, "Reset full object footprint".to_string());
    }

    fn apply_object_candidate(&mut self, candidate: PlacedObject, action: String) {
        let Some(scene_id) = self.active_scene_id() else {
            return;
        };
        match update_scene_object(
            &mut self.model.world,
            &mut self.command_bus,
            &self.model.project.project_id,
            EditorCommandSource::MainEditor,
            scene_id,
            candidate,
            action,
        ) {
            Ok(outcome) => {
                self.status_message = outcome.message;
                self.refresh_scene_selection_bounds();
            }
            Err(error) => self.status_message = error,
        }
    }
}
