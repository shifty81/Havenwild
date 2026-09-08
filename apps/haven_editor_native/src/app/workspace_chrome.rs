use super::render_helpers::*;
use super::workspace_shell::BottomDockTab;
use super::*;

impl EditorApp {
    pub(crate) fn shell_layout(&self) -> ui_shell::EditorShellLayout {
        ui_shell::EditorShellLayout::calculate(
            screen_width(),
            screen_height(),
            &self.workspace_shell,
        )
    }

    pub(crate) fn active_document_dirty(&self) -> bool {
        let world_dirty = self.command_bus.undo_len() != self.saved_undo_depth;
        let pixel_dirty = self.pixel_studio.any_document_dirty();
        let animation_dirty = self
            .animation_studio
            .document
            .as_ref()
            .is_some_and(|document| document.dirty);
        match self.viewport_mode {
            EditorViewportMode::SceneMap => {
                if self.game_canvas_ui_active() {
                    self.game_canvas_ui.dirty
                } else {
                    self.active_scene_id().is_some_and(|id| self.scene_workspace_has_open_document() && self.scene_document_dirty_ids.contains(&id))
                }
            },
            EditorViewportMode::PixelStudio => pixel_dirty,
            EditorViewportMode::AnimationStudio => animation_dirty,
            EditorViewportMode::CharacterStudio => false,
            EditorViewportMode::LogicStudio => self.logic_studio.dirty,
            EditorViewportMode::SoundStudio => self.sound_studio.dirty,
            _ => world_dirty,
        }
    }

    pub(crate) fn any_document_dirty(&self) -> bool {
        self.command_bus.undo_len() != self.saved_undo_depth
            || self.pixel_studio.any_document_dirty()
            || self
                .animation_studio
                .document
                .as_ref()
                .is_some_and(|document| document.dirty)
            || self.logic_studio.dirty
            || self.sound_studio.dirty
            || self.game_canvas_ui.dirty
    }

    pub(crate) fn active_document_title(&self) -> String {
        match self.viewport_mode {
            EditorViewportMode::RegionGraph => "Havenwild World Routes".to_string(),
            EditorViewportMode::SceneRectangles => "Alderreach Global World Editor".to_string(),
            EditorViewportMode::SceneBank => "Interior and Instance Scenes".to_string(),
            EditorViewportMode::SceneMap => {
                if let Some(document) = self.game_canvas_ui.document.as_ref() {
                    format!("Game Canvas UI: {}", document.display_name)
                } else if !self.scene_workspace_has_open_document() {
                    "Game Canvas — No Spatial Document".to_string()
                } else {
                    self.model
                        .world
                        .scenes
                        .get(self.selected_scene)
                        .map(|scene| format!("Scene: {}", scene.id.label()))
                        .unwrap_or_else(|| "Scene Editor".to_string())
                }
            }
            EditorViewportMode::PixelStudio => self
                .pixel_studio
                .document
                .as_ref()
                .map(|document| format!("Sprite/Pixel: {}", document.metadata.display_name))
                .unwrap_or_else(|| "Sprite/Pixel Studio".to_string()),
            EditorViewportMode::AnimationStudio => self
                .animation_studio
                .document
                .as_ref()
                .map(|document| format!("Animation: {}", document.metadata.display_name))
                .unwrap_or_else(|| "Animation Studio".to_string()),
            EditorViewportMode::CharacterStudio => "Character Studio".to_string(),
            EditorViewportMode::LogicStudio => format!("Logic: {}", self.logic_studio.graph.display_name),
            EditorViewportMode::SoundStudio => format!("Sound: {}", self.sound_studio.document.display_name),
        }
    }

    pub(crate) fn draw_workspace_status_bar(
        &self,
        layout: &ui_shell::EditorShellLayout,
        validation: &EditorValidationReport,
    ) {
        let rect = layout.status_bar;
        draw_rectangle(
            rect.x,
            rect.y,
            rect.w,
            rect.h,
            editor_theme::colors::TOP_BAR_BG,
        );
        draw_rectangle_lines(
            rect.x,
            rect.y,
            rect.w,
            rect.h,
            1.0,
            editor_theme::colors::BORDER_SUBTLE,
        );

        let dirty = self.any_document_dirty();
        let status_color = if !validation.is_clean() {
            editor_theme::colors::WARN
        } else if dirty {
            editor_theme::colors::ACCENT
        } else {
            editor_theme::colors::GOOD
        };
        draw_circle(rect.x + 12.0, rect.y + rect.h * 0.5, 4.0, status_color);

        let toggle = ui_shell::bottom_dock_toggle_rect(layout);
        let history_w = 178.0;
        let message_w = (toggle.x - history_w - rect.x - 28.0).max(80.0);
        draw_scissored_text(
            &self.status_message,
            rect.x + 22.0,
            rect.y + 19.0,
            message_w,
            12.0,
            editor_theme::colors::TEXT_SECONDARY,
        );
        draw_editor_text(
            &format!(
                "{} | Undo {}  Redo {}",
                if dirty { "Modified" } else { "Saved" },
                self.command_bus.undo_len(),
                self.command_bus.redo_len()
            ),
            toggle.x - history_w,
            rect.y + 19.0,
            12.0,
            if dirty {
                editor_theme::colors::ACCENT_HOVER
            } else {
                editor_theme::colors::TEXT_SECONDARY
            },
        );
        draw_editor_widget_tone(
            toggle,
            if self.workspace_shell.bottom_dock_open {
                "Hide Bottom"
            } else {
                "Bottom Panels"
            },
            self.workspace_shell.bottom_dock_open,
            WidgetTone::Quiet,
        );
    }

    pub(crate) fn draw_workspace_bottom_dock(
        &self,
        layout: &ui_shell::EditorShellLayout,
        validation: &EditorValidationReport,
    ) {
        if !self.workspace_shell.bottom_dock_open {
            return;
        }
        let dock = layout.bottom_dock;
        draw_rectangle(
            dock.x,
            dock.y,
            dock.w,
            dock.h,
            Color::new(0.045, 0.045, 0.045, 0.992),
        );
        draw_rectangle_lines(
            dock.x,
            dock.y,
            dock.w,
            dock.h,
            1.0,
            editor_theme::colors::BORDER_STRONG,
        );
        draw_rectangle(
            layout.bottom_tab_bar.x,
            layout.bottom_tab_bar.y,
            layout.bottom_tab_bar.w,
            layout.bottom_tab_bar.h,
            editor_theme::colors::PANEL_HEADER,
        );
        for (index, tab) in BottomDockTab::ALL.into_iter().enumerate() {
            draw_tab_widget(
                ui_shell::bottom_tab_rect(layout, index),
                tab.label(),
                self.workspace_shell.bottom_dock_tab == tab,
            );
        }

        let rect = layout.bottom_content;
        match self.workspace_shell.bottom_dock_tab {
            BottomDockTab::Console => self.draw_workspace_console(rect),
            // Legacy persisted Validation values normalize to Activity. Keep the
            // match exhaustive without rendering a second validation workflow.
            BottomDockTab::Validation | BottomDockTab::Tasks => self.draw_workspace_tasks(rect),
            BottomDockTab::Imports => self.draw_workspace_imports(rect),
            BottomDockTab::Build => self.draw_workspace_build(rect, validation),
        }
    }

    fn draw_workspace_console(&self, rect: Rect) {
        draw_editor_text("Editor command history", rect.x, rect.y + 17.0, 16.0, TEXT);
        let mut y = rect.y + 40.0;
        let commands = self.command_bus.recent_commands();
        if commands.is_empty() {
            draw_editor_text(
                "No editor commands recorded this session.",
                rect.x,
                y,
                14.0,
                MUTED,
            );
            return;
        }
        for command in commands.iter().rev().take(5) {
            let scene = command.target.scene_id.as_deref().unwrap_or("workspace");
            draw_scissored_text(
                &format!(
                    "{} | {} | {}",
                    command.label(),
                    scene,
                    command.payload.description
                ),
                rect.x,
                y,
                rect.w,
                13.0,
                TEXT,
            );
            y += 21.0;
        }
        if y + 42.0 < rect.y + rect.h {
            y += 8.0;
            draw_editor_text("Structured diagnostics", rect.x, y, 14.0, MUTED);
            y += 20.0;
            for event in self.diagnostics.recent().rev().take(3) {
                draw_scissored_text(
                    &format!("{:?} | {} | {}", event.level, event.category, event.message),
                    rect.x,
                    y,
                    rect.w,
                    12.0,
                    TEXT,
                );
                y += 19.0;
            }
        }
    }

    fn draw_workspace_imports(&self, rect: Rect) {
        let runtime_ready = self
            .asset_catalog
            .entries()
            .iter()
            .filter(|entry| entry.runtime_ready())
            .count();
        let lines = [
            format!("Asset Browser: {}", self.asset_browser.summary()),
            format!(
                "Production packs: {} mounted | {} diagnostic failure{} | {} stable source bindings",
                self.asset_pack_mounted_count,
                self.asset_pack_failure_count,
                if self.asset_pack_failure_count == 1 { "" } else { "s" },
                self.asset_pack_source_count
            ),
            format!(
                "Editor palette: {} entries | {} runtime ready",
                self.asset_catalog.entries().len(),
                runtime_ready
            ),
            format!(
                "Import recipes: {} | promoted-output reload {}",
                self.asset_intake_catalog.recipes.len(),
                yes_no(self.asset_hot_reload_requested)
            ),
            "Valid built-in packs remain mounted when an optional user/mod pack is invalid; raw LPC sources remain read-only."
                .to_string(),
        ];
        draw_editor_text("Asset and source intake", rect.x, rect.y + 17.0, 16.0, TEXT);
        let mut y = rect.y + 42.0;
        for line in lines {
            draw_scissored_text(&line, rect.x, y, rect.w, 14.0, TEXT);
            y += 23.0;
        }
    }

    fn draw_workspace_build(&self, rect: Rect, validation: &EditorValidationReport) {
        draw_editor_text("Build readiness", rect.x, rect.y + 17.0, 16.0, TEXT);
        let state = if validation.is_clean() {
            "Editor model validation is clean"
        } else {
            "Editor model has validation issues"
        };
        let lines = [
            state.to_string(),
            "Windows build authority: HavenwildTools.cmd -> 2. Build all".to_string(),
            "Build All runs format, Cargo check, strict Clippy, workspace tests, and packaging checks."
                .to_string(),
            "The native editor does not require a network connection.".to_string(),
            "Development play uses Play / Play From Here; live object edits use the active development session.".to_string(),
        ];
        let mut y = rect.y + 42.0;
        for line in lines {
            draw_scissored_text(&line, rect.x, y, rect.w, 14.0, TEXT);
            y += 23.0;
        }
    }

    fn draw_workspace_tasks(&self, rect: Rect) {
        draw_editor_text("Background jobs / modernization lane", rect.x, rect.y + 17.0, 16.0, TEXT);
        let mut y = rect.y + 42.0;
        if self.background_jobs.is_empty() {
            draw_editor_text("No background jobs queued.", rect.x, y, 14.0, MUTED);
            y += 23.0;
        } else {
            for job in self.background_jobs.iter().rev().take(4) {
                draw_scissored_text(
                    &format!("{:?} | {:.0}% | {}", job.state, job.progress.clamp(0.0, 1.0) * 100.0, job.label),
                    rect.x,
                    y,
                    rect.w,
                    13.0,
                    TEXT,
                );
                y += 21.0;
            }
        }
        let metrics = self.diagnostics.metrics();
        draw_scissored_text(
            &format!("Foundation metrics | assets={} | jobs queued={} active={} | diagnostic errors={}", metrics.asset_count, metrics.background_jobs_queued, metrics.background_jobs_active, self.diagnostics.error_count()),
            rect.x,
            y + 5.0,
            rect.w,
            13.0,
            MUTED,
        );
    }

    pub(crate) fn draw_workspace_splitters(&self, layout: &ui_shell::EditorShellLayout) {
        let pointer = vec2(mouse_position().0, mouse_position().1);
        for (rect, drag) in [
            (layout.left_splitter, WorkspaceResizeDrag::LeftPanel),
            (layout.right_splitter, WorkspaceResizeDrag::RightPanel),
            (layout.bottom_splitter, WorkspaceResizeDrag::BottomDock),
        ] {
            if rect.w <= 0.0 || rect.h <= 0.0 {
                continue;
            }
            let active = self.workspace_resize_drag == Some(drag);
            let hovered = rect.contains(pointer);
            let color = if active {
                editor_theme::colors::ACCENT_HOVER
            } else if hovered {
                editor_theme::colors::BORDER_STRONG
            } else {
                editor_theme::colors::BORDER_SUBTLE
            };
            if drag == WorkspaceResizeDrag::BottomDock {
                draw_line(
                    rect.x,
                    rect.y + rect.h * 0.5,
                    rect.x + rect.w,
                    rect.y + rect.h * 0.5,
                    2.0,
                    color,
                );
            } else {
                draw_line(
                    rect.x + rect.w * 0.5,
                    rect.y,
                    rect.x + rect.w * 0.5,
                    rect.y + rect.h,
                    2.0,
                    color,
                );
                let cx = rect.x + rect.w * 0.5;
                let cy = rect.y + rect.h * 0.5;
                for offset in [-5.0_f32, 0.0, 5.0] {
                    draw_line(cx - 4.0, cy + offset + 4.0, cx + 4.0, cy + offset - 4.0, 1.0, color);
                }
            }
        }
    }

    pub(crate) fn update_workspace_resize_input(&mut self) -> bool {
        let point = vec2(mouse_position().0, mouse_position().1);
        let layout = self.shell_layout();
        if self.workspace_resize_drag.is_none() && is_mouse_button_pressed(MouseButton::Left) {
            self.workspace_resize_drag = if layout.left_splitter.contains(point) {
                Some(WorkspaceResizeDrag::LeftPanel)
            } else if layout.right_splitter.contains(point) {
                Some(WorkspaceResizeDrag::RightPanel)
            } else if layout.bottom_splitter.contains(point) {
                Some(WorkspaceResizeDrag::BottomDock)
            } else {
                None
            };
        }

        let Some(drag) = self.workspace_resize_drag else {
            return false;
        };
        if is_mouse_button_down(MouseButton::Left) {
            match drag {
                WorkspaceResizeDrag::LeftPanel => {
                    self.workspace_shell.left_panel_width = point.x - ui_shell::OUTER_GAP;
                }
                WorkspaceResizeDrag::RightPanel => {
                    self.workspace_shell.right_panel_width =
                        screen_width() - ui_shell::OUTER_GAP - point.x;
                }
                WorkspaceResizeDrag::BottomDock => {
                    self.workspace_shell.bottom_dock_height =
                        layout.center_panel.y + layout.center_panel.h - point.y;
                }
            }
            self.workspace_shell.normalize_in_place();
            return true;
        }

        self.workspace_resize_drag = None;
        self.persist_workspace_shell("Workspace panel size changed");
        true
    }

    pub(crate) fn handle_workspace_chrome_click(&mut self, mx: f32, my: f32) -> bool {
        let point = vec2(mx, my);
        let layout = self.shell_layout();
        if ui_shell::bottom_dock_toggle_rect(&layout).contains(point) {
            self.workspace_shell.bottom_dock_open = !self.workspace_shell.bottom_dock_open;
            self.persist_workspace_shell("Bottom panel visibility changed");
            return true;
        }
        if !self.workspace_shell.bottom_dock_open || !layout.bottom_dock.contains(point) {
            return false;
        }
        for (index, tab) in BottomDockTab::ALL.into_iter().enumerate() {
            if ui_shell::bottom_tab_rect(&layout, index).contains(point) {
                self.workspace_shell.bottom_dock_tab = tab;
                self.persist_workspace_shell(&format!("Opened {} panel", tab.label()));
                return true;
            }
        }
        true
    }

    pub(crate) fn handle_workspace_shell_shortcuts(&mut self) -> bool {

        if is_key_pressed(KeyCode::F1) {
            if self.help_center.open {
                self.help_center.open = false;
                if self.text_focus == EditorTextFocus::HelpSearch { self.text_focus = EditorTextFocus::None; }
            } else {
                let page = self.contextual_help_page();
                self.open_help_center(page);
            }
            return true;
        }
        let control = is_key_down(KeyCode::LeftControl) || is_key_down(KeyCode::RightControl);
        let shift = is_key_down(KeyCode::LeftShift) || is_key_down(KeyCode::RightShift);
        if control && shift && is_key_pressed(KeyCode::P) {
            self.save_all_editor_documents();
            return true;
        }
        if control && is_key_pressed(KeyCode::J) {
            self.workspace_shell.bottom_dock_open = !self.workspace_shell.bottom_dock_open;
            self.persist_workspace_shell("Bottom panel visibility changed");
            return true;
        }
        if control && shift && is_key_pressed(KeyCode::L) {
            self.focus_right_dock(RightDockTab::Outliner);
            return true;
        }
        if control && shift && is_key_pressed(KeyCode::I) {
            self.workspace_shell.right_panel_visible = !self.workspace_shell.right_panel_visible;
            self.persist_workspace_shell("Workspace dock visibility changed");
            return true;
        }
        false
    }

    pub(crate) fn toggle_right_workspace_panel(&mut self) {
        self.workspace_shell.right_panel_visible = !self.workspace_shell.right_panel_visible;
        self.persist_workspace_shell("Workspace dock visibility changed");
    }

    pub(crate) fn toggle_bottom_workspace_panel(&mut self) {
        self.workspace_shell.bottom_dock_open = !self.workspace_shell.bottom_dock_open;
        self.persist_workspace_shell("Bottom panel visibility changed");
    }

    pub(crate) fn reset_workspace_layout(&mut self) {
        self.workspace_shell.reset();
        self.persist_workspace_shell("Workspace layout reset");
    }

    pub(crate) fn persist_workspace_shell(&mut self, action: &str) {
        self.status_message = match self.workspace_shell.save_default() {
            Ok(()) => format!("{action} | layout saved"),
            Err(error) => format!("{action} | layout save failed: {error}"),
        };
    }
}

fn yes_no(value: bool) -> &'static str {
    if value {
        "pending"
    } else {
        "idle"
    }
}
