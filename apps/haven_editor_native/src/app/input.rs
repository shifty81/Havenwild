use super::render_helpers::*;
use super::*;

impl EditorApp {
    pub(crate) fn update(&mut self) {
        self.poll_development_client();
        self.poll_resource_context();
        self.update_asset_palette_drag();

        // W79: document close confirmation and project-wide Settings are true
        // overlays. They own input before any canvas/editor interaction.
        if self.pending_document_close.is_some() {
            if is_key_pressed(KeyCode::Escape) {
                self.pending_document_close = None;
                self.status_message = "Document close cancelled".to_string();
                return;
            }
            if is_mouse_button_pressed(MouseButton::Left) {
                let point = vec2(mouse_position().0, mouse_position().1);
                let _ = self.handle_document_close_dialog_click(point);
            }
            return;
        }
        if self.editor_settings.open {
            if is_key_pressed(KeyCode::Escape) {
                self.editor_settings.open = false;
                let _ = self.editor_settings.save_default();
                return;
            }
            if is_mouse_button_pressed(MouseButton::Left) {
                let point = vec2(mouse_position().0, mouse_position().1);
                let _ = self.handle_editor_settings_click(point);
            }
            return;
        }

        if self.pixel_color_popup_open && is_key_pressed(KeyCode::Escape) {
            self.close_pixel_color_tray();
            self.status_message = "Palette color edit cancelled".to_string();
            return;
        }

        if self.world_terrain_browser_open {
            if is_key_pressed(KeyCode::Escape) {
                self.world_terrain_browser_open = false;
                return;
            }
            if is_mouse_button_pressed(MouseButton::Left) {
                let point = vec2(mouse_position().0, mouse_position().1);
                let _ = self.handle_world_terrain_material_browser_click(point);
            }
            return;
        }

        // Authoring publish is a true modal and owns the pointer until committed/cancelled.
        if self.authoring_session.is_some() {
            if is_mouse_button_pressed(MouseButton::Left) {
                let (mx, my) = mouse_position();
                let _ = self.handle_authoring_publish_click(mx, my);
            }
            return;
        }

        // Active Pixel Studio modals own input before canvas navigation.
        // The canvas navigation path reports the pointer as consumed while the
        // modal is visible, so routing this later made the dialog unclickable.
        if self.viewport_mode == EditorViewportMode::PixelStudio
            && self.pixel_studio.new_dialog.is_some()
        {
            if is_mouse_button_pressed(MouseButton::Left) {
                let mouse = vec2(mouse_position().0, mouse_position().1);
                self.handle_new_pixel_dialog_click(mouse);
            }
            self.handle_new_pixel_dialog_input();
            return;
        }
        if self.update_gui_pointer_capture() {
            return;
        }
        if self.update_pixel_layer_drag_input() {
            return;
        }
        if self.update_canvas_layer_resize_input() {
            return;
        }
        if self.update_canvas_layer_scroll_input() {
            return;
        }
        if self.update_canvas_tool_scroll_input() {
            return;
        }
        if self.update_asset_palette_scroll_input() {
            return;
        }
        if self.update_workspace_resize_input() {
            return;
        }

        // UI pointer ownership is gesture-scoped, not frame-scoped. Without this
        // latch, a context-menu press can be consumed on its first frame and the
        // still-held button can fall through to Scene Map painting on the next.
        if self.primary_pointer_owned_by_ui {
            if is_mouse_button_released(MouseButton::Left) {
                self.primary_pointer_owned_by_ui = false;
            }
            return;
        }

        if is_mouse_button_pressed(MouseButton::Right) {
            let (mx, my) = mouse_position();
            if self.handle_shared_palette_secondary_click(mx, my) {
                self.primary_pointer_owned_by_ui = true;
                return;
            }
            if self.open_pixel_layer_context_menu() {
                return;
            }
            if self.open_scene_asset_context_menu() {
                return;
            }
            if self.open_world_canvas_context_menu() {
                return;
            }
            self.world_canvas_context_menu = None;
        }
        if self.text_focus != EditorTextFocus::None {
            if is_mouse_button_pressed(MouseButton::Left) {
                let consumed = if self.help_center.open {
                    let (mx, my) = mouse_position();
                    self.handle_help_center_click(vec2(mx, my))
                } else {
                    self.handle_primary_click()
                };
                if !consumed {
                    self.text_focus = EditorTextFocus::None;
                }
            }
            self.handle_text_input();
            return;
        }
        if self.handle_workspace_shell_shortcuts() {
            return;
        }
        if is_mouse_button_pressed(MouseButton::Left) {
            let (mx, my) = mouse_position();
            if self.help_center.open {
                let _ = self.handle_help_center_click(vec2(mx, my));
                self.primary_pointer_owned_by_ui = true;
                return;
            }

            // Popups are top-most input owners. Whether the click chooses an
            // action or merely dismisses the popup, it must never reach canvas
            // authoring beneath it.
            if self.scene_asset_context_menu.is_some() {
                let _ = self.handle_scene_asset_context_click(mx, my);
                self.primary_pointer_owned_by_ui = true;
                return;
            }
            if self.world_canvas_context_menu.is_some() {
                let _ = self.handle_world_canvas_context_click(mx, my);
                self.primary_pointer_owned_by_ui = true;
                return;
            }

            if self.handle_workspace_document_tabs_click(mx, my) {
                self.primary_pointer_owned_by_ui = true;
                return;
            }
            if self.handle_scene_workspace_empty_state_click(mx, my) {
                self.primary_pointer_owned_by_ui = true;
                return;
            }
            if self.handle_shared_palette_popup_click(mx, my) {
                self.primary_pointer_owned_by_ui = true;
                return;
            }
            if self.handle_shared_palette_click(mx, my) {
                self.primary_pointer_owned_by_ui = true;
                return;
            }
            if self.handle_canvas_view_controls_click(mx, my) {
                self.primary_pointer_owned_by_ui = true;
                return;
            }
            if self.handle_canvas_tool_rack_click(mx, my) {
                self.primary_pointer_owned_by_ui = true;
                return;
            }
            if self.handle_canvas_layer_rail_click(mx, my) {
                self.primary_pointer_owned_by_ui = true;
                return;
            }
            if self.handle_workspace_chrome_click(mx, my) {
                self.primary_pointer_owned_by_ui = true;
                return;
            }
            if self.workspace_shell.right_panel_visible
                && self.shell_layout().inspector_content.contains(vec2(mx, my))
            {
                self.primary_pointer_owned_by_ui = true;
            }
        }

        let canvas_pointer_consumed = self.update_canvas_navigation();
        let pointer_consumed =
            if is_mouse_button_pressed(MouseButton::Left) && !canvas_pointer_consumed {
                self.handle_primary_click()
            } else {
                false
            };
        if is_key_pressed(KeyCode::Tab) && self.pixel_studio.new_dialog.is_none() {
            let _ = self.command_bus.commit_gesture();
            self.last_painted_cell = None;
            self.viewport_mode = match self.viewport_mode {
                EditorViewportMode::SceneRectangles | EditorViewportMode::RegionGraph | EditorViewportMode::SceneBank => EditorViewportMode::SceneMap,
                EditorViewportMode::SceneMap => EditorViewportMode::PixelStudio,
                EditorViewportMode::PixelStudio => EditorViewportMode::AnimationStudio,
                EditorViewportMode::AnimationStudio => EditorViewportMode::CharacterStudio,
                EditorViewportMode::CharacterStudio => EditorViewportMode::LogicStudio,
                EditorViewportMode::LogicStudio => EditorViewportMode::SoundStudio,
                EditorViewportMode::SoundStudio => EditorViewportMode::SceneRectangles,
            };
            self.status_message = format!("Viewport mode: {}", self.viewport_mode.label());
            self.command_bus.record_event(self.app_command(
                EditorCommandKind::SceneMutation,
                self.status_message.clone(),
            ));
        }
        let control_down = is_key_down(KeyCode::LeftControl) || is_key_down(KeyCode::RightControl);
        if (control_down && is_key_pressed(KeyCode::S)) || is_key_pressed(KeyCode::F5) {
            self.save_all_editor_documents();
        }
        if control_down && is_key_pressed(KeyCode::L) {
            self.reload_all_editor_documents();
        }
        let shift_down_global = is_key_down(KeyCode::LeftShift) || is_key_down(KeyCode::RightShift);
        if control_down && shift_down_global && is_key_pressed(KeyCode::T) {
            self.reopen_last_closed_document();
            return;
        }
        if control_down && !shift_down_global && is_key_pressed(KeyCode::W) {
            self.request_close_active_document();
            return;
        }

        // W60E5: one shortcut router owns the permanent CanvasWorkspace tool rack.
        // Each tab/layer adapter decides whether a universal tool is meaningful.
        self.handle_contextual_canvas_shortcuts();

        match self.viewport_mode {
            EditorViewportMode::RegionGraph => {
                if is_key_pressed(KeyCode::Down) || is_key_pressed(KeyCode::Right) {
                    self.cycle_landmass_selection(1);
                }
                if is_key_pressed(KeyCode::Up) || is_key_pressed(KeyCode::Left) {
                    self.cycle_landmass_selection(-1);
                }
                if is_key_pressed(KeyCode::Enter) {
                    self.frame_entire_world();
                }
            }
            EditorViewportMode::SceneRectangles => {
                let shift_down =
                    is_key_down(KeyCode::LeftShift) || is_key_down(KeyCode::RightShift);
                // Storage-partition manipulation is diagnostic-only. It cannot
                // steal ordinary world-authoring keys from the global canvas.
                if self.world_show_partitions && control_down && shift_down {
                    if is_key_pressed(KeyCode::Left) {
                        self.move_selected_scene_cell(-1, 0);
                    }
                    if is_key_pressed(KeyCode::Right) {
                        self.move_selected_scene_cell(1, 0);
                    }
                    if is_key_pressed(KeyCode::Up) {
                        self.move_selected_scene_cell(0, -1);
                    }
                    if is_key_pressed(KeyCode::Down) {
                        self.move_selected_scene_cell(0, 1);
                    }
                    if is_key_pressed(KeyCode::Backspace) {
                        self.clear_selected_rectangle_assignment();
                    }
                }
                if is_key_pressed(KeyCode::Enter) {
                    self.open_assigned_rectangle_scene();
                }
                if !self.update_direct_visual_authoring(pointer_consumed, canvas_pointer_consumed) {
                    self.update_world_editor_input(pointer_consumed, canvas_pointer_consumed);
                }
            }
            EditorViewportMode::SceneBank => {
                if is_key_pressed(KeyCode::Down) || is_key_pressed(KeyCode::Right) {
                    self.cycle_scene_bank_selection(1);
                }
                if is_key_pressed(KeyCode::Up) || is_key_pressed(KeyCode::Left) {
                    self.cycle_scene_bank_selection(-1);
                }
                if is_key_pressed(KeyCode::Enter) {
                    self.open_selected_scene_bank_scene();
                }
            }
            EditorViewportMode::SceneMap => {
                if self.game_canvas_ui_active() {
                    self.update_game_canvas_ui_input(pointer_consumed, canvas_pointer_consumed);
                    return;
                }
                if !self.scene_workspace_has_open_document() {
                    return;
                }
                let scene_undo_before = self.command_bus.undo_len();
                let shift_down =
                    is_key_down(KeyCode::LeftShift) || is_key_down(KeyCode::RightShift);
                let alt_down = is_key_down(KeyCode::LeftAlt) || is_key_down(KeyCode::RightAlt);
                let mut building_input_consumed = false;

                if is_key_pressed(KeyCode::PageUp) {
                    building_input_consumed |= self.cycle_building_preview_level(1);
                }
                if is_key_pressed(KeyCode::PageDown) {
                    building_input_consumed |= self.cycle_building_preview_level(-1);
                }
                if is_key_pressed(KeyCode::Home) {
                    building_input_consumed |= self.toggle_building_preview_cutaway();
                }
                if control_down && shift_down && is_key_pressed(KeyCode::B) {
                    building_input_consumed |= self.delete_building_instance_at_scene_cursor();
                } else if control_down && !alt_down && is_key_pressed(KeyCode::B) {
                    building_input_consumed |= self.place_building_instance_at_scene_cursor();
                }
                if control_down && alt_down {
                    if is_key_pressed(KeyCode::Right) {
                        building_input_consumed |= self.move_building_instance_at_scene_cursor(1, 0);
                    }
                    if is_key_pressed(KeyCode::Left) {
                        building_input_consumed |= self.move_building_instance_at_scene_cursor(-1, 0);
                    }
                    if is_key_pressed(KeyCode::Down) {
                        building_input_consumed |= self.move_building_instance_at_scene_cursor(0, 1);
                    }
                    if is_key_pressed(KeyCode::Up) {
                        building_input_consumed |= self.move_building_instance_at_scene_cursor(0, -1);
                    }
                }
                if !building_input_consumed
                    && !self.update_direct_visual_authoring(pointer_consumed, canvas_pointer_consumed)
                {
                    self.update_scene_map_input(pointer_consumed, canvas_pointer_consumed);
                }
                if self.command_bus.undo_len() != scene_undo_before {
                    self.mark_active_scene_document_dirty();
                }
            }
            EditorViewportMode::PixelStudio => {
                self.update_pixel_studio_input();
            }
            EditorViewportMode::AnimationStudio => {
                self.update_animation_studio_input();
            }
            EditorViewportMode::CharacterStudio => {
                self.update_character_studio_input();
            }
            EditorViewportMode::LogicStudio => {
                self.update_logic_studio_input();
            }
            EditorViewportMode::SoundStudio => {
                self.update_sound_studio_input();
            }
        }
    }

    pub(crate) fn handle_primary_click(&mut self) -> bool {
        let (mx, my) = mouse_position();

        if self.authoring_session.is_some() {
            return self.handle_authoring_publish_click(mx, my);
        }
        if self.viewport_mode == EditorViewportMode::PixelStudio
            && self.pixel_studio.new_dialog.is_some()
        {
            return self.handle_pixel_studio_click(mx, my);
        }

        if self.handle_editor_menu_click(mx, my) {
            return true;
        }
        if self.handle_workspace_chrome_click(mx, my) {
            return true;
        }
        if self.handle_right_dock_click(mx, my) {
            return true;
        }

        if self.scene_asset_context_menu.is_some() && self.handle_scene_asset_context_click(mx, my)
        {
            return true;
        }

        if self.world_canvas_context_menu.is_some()
            && self.handle_world_canvas_context_click(mx, my)
        {
            return true;
        }

        // A14X: six top-level studio buttons are persistent. Game Canvas is a
        // single studio; World/Scene/Routes/Scene Library remain contextual views.
        for (index, mode) in [
            EditorViewportMode::SceneMap,
            EditorViewportMode::PixelStudio,
            EditorViewportMode::AnimationStudio,
            EditorViewportMode::CharacterStudio,
            EditorViewportMode::LogicStudio,
            EditorViewportMode::SoundStudio,
        ]
        .into_iter()
        .enumerate()
        {
            let button = workspace_tab_rect(index);
            if button.contains(vec2(mx, my)) {
                let _ = self.command_bus.commit_gesture();
                self.last_painted_cell = None;
                self.text_focus = EditorTextFocus::None;
                self.scene_name_edit = None;
                self.scene_delete_armed = None;
                self.world_canvas_context_menu = None;
                        self.pixel_symmetry_popup_open = false;
                if mode == EditorViewportMode::SceneMap {
                    // Clicking the global Game Canvas tab while already in one of
                    // its contextual views must not throw the user back to Scene.
                    if !self.viewport_mode.is_game_canvas() {
                        self.activate_scene_workspace();
                    }
                    self.status_message = "Opened Game Canvas workspace".to_string();
                } else {
                    self.viewport_mode = mode;
                    self.reopen_workspace_document(mode);
                    self.status_message = format!("Opened {} workspace", mode.label());
                }
                return true;
            }
        }

        let list_rect = self.shell_layout().list_content;
        if self.workspace_shell.left_panel_visible
            && self.viewport_mode == EditorViewportMode::SceneMap
            && list_rect.contains(vec2(mx, my))
        {
            return self.handle_scene_outliner_click(mx, my, list_rect);
        }
        if self.workspace_shell.left_panel_visible
            && self.viewport_mode == EditorViewportMode::SceneBank
            && list_rect.contains(vec2(mx, my))
        {
            return self.handle_scene_bank_list_click(mx, my, list_rect);
        }
        if self.workspace_shell.left_panel_visible
            && matches!(
                self.viewport_mode,
                EditorViewportMode::RegionGraph | EditorViewportMode::SceneRectangles
            )
            && list_rect.contains(vec2(mx, my))
        {
            return self.handle_landmass_list_click(mx, my, list_rect);
        }
        if self.viewport_mode == EditorViewportMode::PixelStudio {
            return self.handle_pixel_studio_click(mx, my);
        }
        if self.viewport_mode == EditorViewportMode::AnimationStudio {
            return self.handle_animation_studio_click(mx, my);
        }
        if self.viewport_mode == EditorViewportMode::CharacterStudio {
            return self.handle_character_studio_click(mx, my);
        }
        if self.viewport_mode == EditorViewportMode::LogicStudio {
            return self.handle_logic_studio_click(mx, my);
        }
        if self.viewport_mode == EditorViewportMode::SoundStudio {
            return self.handle_sound_studio_click(mx, my);
        }

        if self.game_canvas_ui_active() {
            self.text_focus = EditorTextFocus::None;
            // Central UI-document selection/dragging is handled in the per-frame
            // input path. Chrome and dock clicks have already been consumed above.
            return true;
        }
        self.text_focus = EditorTextFocus::None;
        if self.handle_canvas_toolbar_click(mx, my) {
            return true;
        }
        if self.workspace_shell.right_panel_visible
            && self.viewport_mode == EditorViewportMode::SceneMap
        {
            if self.workspace_shell.right_dock_tab == RightDockTab::Properties {
                let inspector_rect = self.inspector_content_rect();
                if self.handle_scene_properties_click(mx, my, inspector_rect) {
                    return true;
                }
            }
        }
        if self.workspace_shell.right_panel_visible
            && self.viewport_mode == EditorViewportMode::SceneBank
        {
            if self.handle_scene_bank_inspector_click(mx, my) {
                return true;
            }
            if self.handle_scene_bank_canvas_click(mx, my) {
                return true;
            }
        }
        if self.viewport_mode == EditorViewportMode::SceneRectangles
            && self.workspace_shell.right_panel_visible
            && self.workspace_shell.right_dock_tab == RightDockTab::Properties
            && self.handle_world_properties_click(mx, my, self.inspector_content_rect())
        {
            return true;
        }
        // Global canvas authoring is routed after chrome/inspector input so
        // paint drags, marquees, and cross-partition gestures own the press.
        if self.viewport_mode == EditorViewportMode::RegionGraph {
            if self.workspace_shell.right_panel_visible
                && self.handle_world_routes_inspector_click(mx, my)
            {
                return true;
            }
            if self.handle_world_routes_click(mx, my) {
                return true;
            }
        }
        false
    }

}
