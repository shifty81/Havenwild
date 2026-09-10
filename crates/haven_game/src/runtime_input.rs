use super::*;

impl Game {
    pub(super) fn handle_global_input(&mut self) {
        let frame_time = get_frame_time();
        self.update_character_vitals_runtime(frame_time);
        self.update_character_action_animation(frame_time);
        self.handle_client_camera_zoom_input();
        self.handle_gameplay_hotbar_input();
        self.handle_gameplay_tool_use_input();
        let f3_down = is_key_down(KeyCode::F3);
        if !f3_down {
            self.dev_toggle_armed = true;
        }
        if f3_down && self.dev_toggle_armed {
            self.dev_toggle_armed = false;
            if self.dev_mode {
                self.save_map();
                self.dev_mode = false;
                self.build_mode = false;
            } else {
                self.dev_mode = true;
                self.build_mode = true;
                self.editor_minimized = false;
            }
            self.status_message = if self.dev_mode {
                "Dev mode enabled: lightweight overlays; H/C/I/T enable diagnostics".to_string()
            } else {
                format!("Editor closed; edits saved to {}", self.save_paths.world)
            };
            self.log.event(&self.status_message);
        }
        if is_key_pressed(KeyCode::B) {
            if self.dev_mode {
                self.build_mode = !self.build_mode;
            }
            self.log.event(if self.build_mode {
                "Build mode enabled"
            } else {
                "Build mode disabled"
            });
        }
        if self.dev_mode && is_key_pressed(KeyCode::L) {
            self.layout_edit_mode = !self.layout_edit_mode;
            self.layout_drag = None;
            if !self.layout_edit_mode {
                self.save_layout();
            }
            self.status_message = if self.layout_edit_mode {
                "Layout edit enabled: drag panels on the 16px grid".to_string()
            } else {
                "Layout edit disabled".to_string()
            };
            self.log.event(&self.status_message);
        }
        if is_key_pressed(KeyCode::O) {
            self.tavern_open = !self.tavern_open;
            self.log.event(if self.tavern_open {
                "Tavern opened"
            } else {
                "Tavern closed"
            });
        }
        if self.controls.action_pressed(ControlAction::Interact)
            && !(self.dev_mode && self.editor_tab == EditorTab::Assets)
        {
            self.interact_with_current_tile();
        }
        if !self.dev_mode && self.controls.action_pressed(ControlAction::Rest) {
            self.try_begin_character_rest();
        }
        if is_key_pressed(KeyCode::F5) {
            self.save_map();
        }
        if is_key_pressed(KeyCode::F9) {
            self.load_map();
        }
        if self.dev_mode && is_key_pressed(KeyCode::F10) {
            self.load_worldgen_pack();
        }
        if self.dev_mode && is_key_pressed(KeyCode::F11) {
            self.export_worldgen_json();
        }
        if self.dev_mode && is_key_pressed(KeyCode::PageDown) {
            self.jump_scene(1);
        }
        if self.dev_mode && is_key_pressed(KeyCode::PageUp) {
            self.jump_scene(-1);
        }
        if self.dev_mode
            && self.editor_tab != EditorTab::Paint
            && is_key_pressed(KeyCode::RightBracket)
        {
            self.selected_transition_target =
                (self.selected_transition_target + 1) % SceneId::ALL.len();
        }
        if self.dev_mode
            && self.editor_tab != EditorTab::Paint
            && is_key_pressed(KeyCode::LeftBracket)
        {
            self.selected_transition_target =
                (self.selected_transition_target + SceneId::ALL.len() - 1) % SceneId::ALL.len();
        }
        if self.dev_mode && is_key_pressed(KeyCode::G) {
            self.show_world_graph = !self.show_world_graph;
        }
        if self.dev_mode && self.editor_tab != EditorTab::Paint && is_key_pressed(KeyCode::H) {
            self.show_footprint_overlay = !self.show_footprint_overlay;
            self.status_message = if self.show_footprint_overlay {
                "Footprint overlay enabled".to_string()
            } else {
                "Footprint overlay hidden".to_string()
            };
        }
        if self.dev_mode && is_key_pressed(KeyCode::C) {
            self.show_collision_overlay = !self.show_collision_overlay;
            self.status_message = if self.show_collision_overlay {
                "Collision/blocked overlay enabled".to_string()
            } else {
                "Collision/blocked overlay hidden".to_string()
            };
        }
        if self.dev_mode && is_key_pressed(KeyCode::I) {
            self.show_interaction_overlay = !self.show_interaction_overlay;
            self.status_message = if self.show_interaction_overlay {
                "Interaction overlay enabled".to_string()
            } else {
                "Interaction overlay hidden".to_string()
            };
        }
        if self.dev_mode && self.editor_tab != EditorTab::Paint && is_key_pressed(KeyCode::T) {
            self.show_terrain_debug_overlay = !self.show_terrain_debug_overlay;
            self.status_message = if self.show_terrain_debug_overlay {
                "Terrain family/transition debug overlay enabled".to_string()
            } else {
                "Terrain family/transition debug overlay hidden".to_string()
            };
            self.log.event(&self.status_message);
        }
        if self.dev_mode && is_key_pressed(KeyCode::Y) {
            self.show_transition_rule_inspector = !self.show_transition_rule_inspector;
            self.status_message = if self.show_transition_rule_inspector {
                "Terrain transition rule inspector enabled".to_string()
            } else {
                "Terrain transition rule inspector hidden".to_string()
            };
            self.log.event(&self.status_message);
        }
        if self.dev_mode && is_key_pressed(KeyCode::U) {
            self.show_transition_rule_preview = !self.show_transition_rule_preview;
            self.status_message = if self.show_transition_rule_preview {
                "Terrain transition rule preview grid enabled".to_string()
            } else {
                "Terrain transition rule preview grid hidden".to_string()
            };
            self.log.event(&self.status_message);
        }
        if self.dev_mode
            && self.show_transition_rule_preview
            && self.editor_tab != EditorTab::Assets
            && self.editor_tab != EditorTab::Paint
            && is_key_pressed(KeyCode::J)
        {
            self.cycle_transition_rule_preview(-1);
        }
        if self.dev_mode
            && self.show_transition_rule_preview
            && self.editor_tab != EditorTab::Assets
            && self.editor_tab != EditorTab::Paint
            && is_key_pressed(KeyCode::K)
        {
            self.cycle_transition_rule_preview(1);
        }
        if self.dev_mode
            && self.editor_tab != EditorTab::Transitions
            && self.editor_tab != EditorTab::Assets
            && self.editor_tab != EditorTab::Paint
            && is_key_pressed(KeyCode::V)
        {
            self.validation_messages = validate_world(&self.world);
            self.status_message = if self.validation_messages.is_empty() {
                "World validation passed".to_string()
            } else {
                format!(
                    "World validation: {} warning(s)",
                    self.validation_messages.len()
                )
            };
            self.log.event(&self.status_message);
        }
        if self.dev_mode
            && self.editor_tab != EditorTab::Assets
            && self.editor_tab != EditorTab::Paint
            && is_key_pressed(KeyCode::P)
        {
            self.set_active_scene_player_start(GridPos {
                x: self.selected_cell.0,
                y: self.selected_cell.1,
            });
        }
        if self.dev_mode
            && is_key_pressed(KeyCode::R)
            && self.editor_tab != EditorTab::Transitions
            && self.editor_tab != EditorTab::Assets
            && self.editor_tab != EditorTab::Paint
        {
            self.push_undo_snapshot();
            self.reset_active_scene();
        }
        if self.dev_mode && is_key_pressed(KeyCode::N) {
            self.push_undo_snapshot();
            self.regenerate_active_scene();
        }
        if self.dev_mode && is_key_pressed(KeyCode::Minus) {
            self.brush_size = (self.brush_size - 2).max(1);
            self.status_message = format!("Brush size: {}", self.brush_size);
        }
        if self.dev_mode && is_key_pressed(KeyCode::Equal) {
            self.brush_size = (self.brush_size + 2).min(9);
            self.status_message = format!("Brush size: {}", self.brush_size);
        }
        if self.dev_mode {
            if self.editor_tab != EditorTab::Transitions
                && self.editor_tab != EditorTab::Assets
                && is_key_down(KeyCode::LeftControl)
                && is_key_pressed(KeyCode::Z)
            {
                self.undo_world();
                return;
            }
            if self.editor_tab != EditorTab::Transitions
                && self.editor_tab != EditorTab::Assets
                && is_key_down(KeyCode::LeftControl)
                && is_key_pressed(KeyCode::Y)
            {
                self.redo_world();
                return;
            }
            if is_key_pressed(KeyCode::Q) {
                self.cycle_editor_tab(-1);
            }
            if is_key_pressed(KeyCode::E) {
                self.cycle_editor_tab(1);
            }
            if self.editor_tab == EditorTab::Objects {
                self.handle_selected_object_hotkeys();
            } else if self.editor_tab == EditorTab::Transitions {
                self.handle_transition_rule_editor_hotkeys();
            } else if self.editor_tab == EditorTab::Assets {
                self.handle_asset_reference_browser_hotkeys();
            } else if self.editor_tab == EditorTab::Paint {
                self.handle_world_paint_hotkeys();
            } else {
                self.adjust_selected_transition();
            }
        }
        if self.dev_mode && is_key_pressed(KeyCode::Z) {
            self.tool_page = self.tool_page.saturating_sub(1);
            self.select_first_tool_on_page();
            self.status_message = format!("Tool page {}", self.tool_page + 1);
        }
        if self.dev_mode && is_key_pressed(KeyCode::X) {
            self.tool_page = (self.tool_page + 1).min(self.max_tool_page());
            self.select_first_tool_on_page();
            self.status_message = format!("Tool page {}", self.tool_page + 1);
        }
        let number_keys = [
            KeyCode::Key1,
            KeyCode::Key2,
            KeyCode::Key3,
            KeyCode::Key4,
            KeyCode::Key5,
            KeyCode::Key6,
            KeyCode::Key7,
            KeyCode::Key8,
            KeyCode::Key9,
            KeyCode::Key0,
        ];
        let control_down = is_key_down(KeyCode::LeftControl) || is_key_down(KeyCode::RightControl);

        // Normal 1-0 always belong to the player-facing gameplay hotbar.
        // Editor palette shortcuts are intentionally moved behind Ctrl+number
        // so opening the developer overlay cannot replace the player's tools.
        if !(self.dev_mode && control_down) {
            for (slot, key) in number_keys.iter().take(gameplay_hotbar::HOTBAR_SLOT_COUNT).enumerate() {
                if is_key_pressed(*key) {
                    self.selected_gameplay_tool = slot;
                    self.status_message = self
                        .hotbar_binding(slot)
                        .map(|binding| format!("Selected {}", binding.display_name))
                        .unwrap_or_else(|| format!("Selected empty hotbar slot {}", slot + 1));
                }
            }
        } else {
            let visible_tools = self.visible_tool_indices();
            for (i, key) in number_keys.iter().enumerate() {
                let visible_index = self.tool_page * 10 + i;
                if is_key_pressed(*key) && visible_index < visible_tools.len() {
                    self.selected_tool = visible_tools[visible_index];
                }
            }
        }

        if self.dev_mode && self.editor_tab == EditorTab::Objects {
            let count = self.placeable_registry.entries().len();
            if count > 0 && is_key_pressed(KeyCode::PageDown) {
                self.selected_placeable_index = (self.selected_placeable_index + 1) % count;
                let entry = &self.placeable_registry.entries()[self.selected_placeable_index];
                self.status_message = format!("Selected pack placeable {}", entry.label);
            }
            if count > 0 && is_key_pressed(KeyCode::PageUp) {
                self.selected_placeable_index = (self.selected_placeable_index + count - 1) % count;
                let entry = &self.placeable_registry.entries()[self.selected_placeable_index];
                self.status_message = format!("Selected pack placeable {}", entry.label);
            }
        }
    }

    fn handle_gameplay_hotbar_input(&mut self) {
        let alt_down = is_key_down(KeyCode::LeftAlt) || is_key_down(KeyCode::RightAlt);
        if alt_down {
            return;
        }

        // Mouse selection and wheel/bumper cycling select shortcut positions,
        // never hard-coded tool identities.
        if is_mouse_button_pressed(MouseButton::Left) {
            let point = vec2(mouse_position().0, mouse_position().1);
            if let Some((slot, _)) = gameplay_hotbar::hotbar_slot_rects(screen_width(), screen_height())
                .into_iter()
                .find(|(_, rect)| rect.contains(point))
            {
                self.selected_gameplay_tool = slot;
                self.status_message = self
                    .hotbar_binding(slot)
                    .map(|binding| format!("Selected {}", binding.display_name))
                    .unwrap_or_else(|| format!("Selected empty hotbar slot {}", slot + 1));
                return;
            }
        }

        let direction = self.controls.hotbar_delta();
        if direction == 0 {
            return;
        }
        self.selected_gameplay_tool =
            gameplay_hotbar::cycle_hotbar_index(self.selected_gameplay_tool, direction);
        self.status_message = self
            .hotbar_binding(self.selected_gameplay_tool)
            .map(|binding| format!("Selected {}", binding.display_name))
            .unwrap_or_else(|| format!("Selected empty hotbar slot {}", self.selected_gameplay_tool + 1));
    }

    fn handle_client_camera_zoom_input(&mut self) {
        let alt_down = is_key_down(KeyCode::LeftAlt) || is_key_down(KeyCode::RightAlt);
        if !alt_down {
            return;
        }

        let wheel = mouse_wheel().1;
        if wheel.abs() <= f32::EPSILON {
            return;
        }

        // Alt+wheel is reserved for the client camera. It must not be forwarded
        // to gameplay/editor hotbar selection when those wheel bindings exist.
        let next = camera_zoom_after_wheel(self.camera_zoom, wheel);
        if (next - self.camera_zoom).abs() <= f32::EPSILON {
            return;
        }
        self.camera_zoom = next;
        self.status_message = format!("Camera zoom {:.0}%", self.camera_zoom * 100.0);
    }

    pub(super) fn max_tool_page(&self) -> usize {
        self.visible_tool_indices().len().saturating_sub(1) / 10
    }

    pub(super) fn visible_tool_indices(&self) -> Vec<usize> {
        self.palette
            .tools
            .iter()
            .enumerate()
            .filter_map(|(index, tool)| self.editor_tab.contains(*tool).then_some(index))
            .collect()
    }

    pub(super) fn select_first_tool_on_page(&mut self) {
        let visible_tools = self.visible_tool_indices();
        if let Some(tool_index) = visible_tools.get(self.tool_page * 10) {
            self.selected_tool = *tool_index;
        }
    }

    pub(super) fn cycle_editor_tab(&mut self, direction: i32) {
        let index = EditorTab::ALL
            .iter()
            .position(|tab| *tab == self.editor_tab)
            .unwrap_or(0);
        let next = (index as i32 + direction).rem_euclid(EditorTab::ALL.len() as i32) as usize;
        self.editor_tab = EditorTab::ALL[next];
        self.tool_page = 0;
        self.select_first_tool_on_page();
        self.status_message = format!(
            "{}: {}",
            self.editor_tab.label(),
            self.editor_tab.workflow_help()
        );
    }
}

fn camera_zoom_after_wheel(current: f32, raw_wheel: f32) -> f32 {
    let wheel = raw_wheel.clamp(-4.0, 4.0);
    pixel_perfect_camera_zoom(current * RUNTIME_CAMERA_ZOOM_STEP.powf(wheel))
}

fn pixel_perfect_camera_zoom(raw: f32) -> f32 {
    const TILE_PIXELS: f32 = 32.0;
    let bounded = raw.clamp(RUNTIME_CAMERA_MIN_ZOOM, RUNTIME_CAMERA_MAX_ZOOM);
    (bounded * TILE_PIXELS).round() / TILE_PIXELS
}

#[cfg(test)]
mod camera_zoom_tests {
    use super::{camera_zoom_after_wheel, pixel_perfect_camera_zoom};
    use crate::runtime_config::{
        RUNTIME_CAMERA_DEFAULT_ZOOM, RUNTIME_CAMERA_MAX_ZOOM, RUNTIME_CAMERA_MIN_ZOOM,
    };

    #[test]
    fn wheel_up_zooms_in_from_closer_default() {
        let zoomed = camera_zoom_after_wheel(RUNTIME_CAMERA_DEFAULT_ZOOM, 1.0);
        assert!(zoomed > RUNTIME_CAMERA_DEFAULT_ZOOM);
        assert!(zoomed > 1.15);
    }

    #[test]
    fn client_camera_zoom_is_bounded() {
        assert_eq!(
            camera_zoom_after_wheel(RUNTIME_CAMERA_MAX_ZOOM, 40.0),
            RUNTIME_CAMERA_MAX_ZOOM
        );
        assert_eq!(
            camera_zoom_after_wheel(RUNTIME_CAMERA_MIN_ZOOM, -40.0),
            RUNTIME_CAMERA_MIN_ZOOM
        );
    }

    #[test]
    fn camera_zoom_preserves_integer_output_tile_width() {
        for zoom in [
            RUNTIME_CAMERA_MIN_ZOOM,
            RUNTIME_CAMERA_DEFAULT_ZOOM,
            RUNTIME_CAMERA_MAX_ZOOM,
            pixel_perfect_camera_zoom(1.73),
        ] {
            assert!(((zoom * 32.0).round() - zoom * 32.0).abs() < f32::EPSILON);
        }
    }
}
