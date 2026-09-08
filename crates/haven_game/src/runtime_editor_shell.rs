use super::*;

mod window_transform;
mod world_builder;

impl Game {
    pub(super) fn update_layout_editor(&mut self) {
        let (mx, my) = mouse_position();
        if is_mouse_button_pressed(MouseButton::Left) {
            for panel in [
                UiPanelId::Editor,
                UiPanelId::Inspector,
                UiPanelId::Validation,
                UiPanelId::WorldGraph,
                UiPanelId::Hud,
            ] {
                let rect = self.panel_rect(panel);
                if rect.title_bar_contains(mx, my) {
                    self.layout_drag = Some(LayoutDrag {
                        panel,
                        grab_offset: vec2(mx - rect.x, my - rect.y),
                    });
                    self.status_message = format!("Moving {}", panel.label());
                    return;
                }
            }
        }

        if is_mouse_button_down(MouseButton::Left) {
            if let Some(drag) = self.layout_drag {
                let w = self.ui_layout.panel(drag.panel).width;
                let h = self.ui_layout.panel(drag.panel).height;
                let snapped =
                    snap_panel_to_grid(mx - drag.grab_offset.x, my - drag.grab_offset.y, UI_GRID);
                let layout = self.ui_layout.panel_mut(drag.panel);
                let (grid_x, grid_y) =
                    panel_grid_from_screen(layout.anchor, snapped.x, snapped.y, w, h, UI_GRID);
                layout.grid_x = grid_x;
                layout.grid_y = grid_y;
                self.status_message = format!(
                    "{} snapped to {},{}",
                    drag.panel.label(),
                    layout.grid_x,
                    layout.grid_y
                );
            }
        } else if self.layout_drag.is_some() {
            self.layout_drag = None;
            self.save_layout();
        }
    }

    pub(super) fn panel_rect(&self, panel: UiPanelId) -> UiPanelRect {
        let layout = self.ui_layout.panel(panel);
        let mut width = layout.width;
        if panel == UiPanelId::Editor && !self.editor_minimized {
            width = width.max(600.0);
        }
        let height = if panel == UiPanelId::Editor {
            if self.editor_minimized {
                96.0
            } else {
                layout.height.max(510.0)
            }
        } else if panel == UiPanelId::Inspector {
            layout.height.max(330.0)
        } else {
            layout.height
        };
        let mut rect = resolve_panel_rect(
            layout.anchor,
            layout.grid_x,
            layout.grid_y,
            width,
            height,
            UI_GRID,
        );
        if panel == UiPanelId::Inspector
            && self.dev_mode
            && self.build_mode
            && !self.editor_minimized
        {
            let editor = self.panel_rect(UiPanelId::Editor);
            let overlaps = rect.x < editor.x + editor.w
                && rect.x + rect.w > editor.x
                && rect.y < editor.y + editor.h
                && rect.y + rect.h > editor.y;
            if overlaps {
                let below = editor.y + editor.h + UI_GRID;
                if below + rect.h <= screen_height() - UI_GRID {
                    rect.y = below;
                    rect.x = editor.x + editor.w - rect.w;
                } else {
                    rect.x = (editor.x - rect.w - UI_GRID).max(UI_GRID);
                    rect.y = editor.y;
                }
            }
        }
        rect
    }

    pub(super) fn handle_editor_overlay_click(&mut self, mx: f32, my: f32) -> bool {
        let rect = self.panel_rect(UiPanelId::Editor);
        let panel_x = rect.x;
        let panel_y = rect.y;
        if self.editor_minimized {
            let inside_toolbar = rect.contains(mx, my);
            if !inside_toolbar {
                return false;
            }
            if is_mouse_button_pressed(MouseButton::Left) {
                return self.handle_minimized_toolbar_click(mx, my, panel_x);
            }
            return true;
        }
        let inside_panel = rect.contains(mx, my);
        if !inside_panel {
            return false;
        }
        if is_mouse_button_pressed(MouseButton::Left) {
            let tab_w = 68.0;
            let tab_step = 69.0;
            for (i, tab) in EditorTab::ALL.iter().enumerate() {
                let x = panel_x + 12.0 + i as f32 * tab_step;
                if mx >= x && mx <= x + tab_w && my >= panel_y + 42.0 && my <= panel_y + 68.0 {
                    self.editor_tab = *tab;
                    self.tool_page = 0;
                    self.select_first_tool_on_page();
                    self.status_message = format!("{}: {}", tab.label(), tab.workflow_help());
                    return true;
                }
            }
            if self.editor_tab == EditorTab::World {
                return self.handle_world_tab_click(mx, my, panel_x);
            }
            if self.editor_tab == EditorTab::Objects {
                return self.handle_objects_tab_click(mx, my, panel_x);
            }
            if self.editor_tab == EditorTab::Rules {
                return self.handle_rules_tab_click(mx, my, panel_x);
            }
            if self.editor_tab == EditorTab::Map {
                return self.handle_map_tab_click(mx, my, panel_x);
            }
            if self.editor_tab == EditorTab::Paint {
                return self.handle_world_paint_tab_click(mx, my, panel_x);
            }
            if self.editor_tab == EditorTab::Transitions {
                return self.handle_transition_rules_tab_click(mx, my, panel_x);
            }
            if self.editor_tab == EditorTab::Assets {
                return self.handle_asset_reference_browser_click(mx, my, panel_x);
            }
            return self.handle_tool_tab_click(mx, my, panel_x, panel_y);
        }
        true
    }

    pub(super) fn terrain_paint_mode_button_rect(&self, index: usize) -> Rect {
        let panel = self.panel_rect(UiPanelId::Editor);
        let gap = 8.0;
        let width = ((panel.w - 52.0) / 3.0).max(96.0);
        Rect::new(
            panel.x + 18.0 + index as f32 * (width + gap),
            panel.y + 398.0,
            width,
            28.0,
        )
    }

    fn handle_tool_tab_click(&mut self, mx: f32, my: f32, panel_x: f32, panel_y: f32) -> bool {
        let rect = self.panel_rect(UiPanelId::Editor);
        if self.editor_tab == EditorTab::Tiles {
            let mouse = vec2(mx, my);
            for (index, mode) in TerrainPaintMode::ALL.into_iter().enumerate() {
                if self.terrain_paint_mode_button_rect(index).contains(mouse) {
                    self.terrain_paint_mode = mode;
                    self.status_message =
                        format!("Terrain paint mode: {} — {}", mode.label(), mode.help());
                    self.log.event(&self.status_message);
                    return true;
                }
            }
        }
        let visible_tools = self.visible_tool_indices();
        let start = self.tool_page * 10;
        let end = (start + 10).min(visible_tools.len());
        for (slot, visible_index) in (start..end).enumerate() {
            let column = slot % 2;
            let row = slot / 2;
            let gap = 14.0;
            let card_w = ((rect.w - 36.0 - gap) * 0.5).max(250.0);
            let x = panel_x + 18.0 + column as f32 * (card_w + gap);
            let y = panel_y + 84.0 + row as f32 * 62.0;
            if mx >= x && mx <= x + card_w && my >= y && my <= y + 54.0 {
                self.selected_tool = visible_tools[visible_index];
                self.status_message = format!(
                    "Selected {}",
                    self.palette.tools[self.selected_tool].label()
                );
                self.log.event(&self.status_message);
                return true;
            }
        }
        true
    }

    pub(super) fn handle_minimized_toolbar_click(
        &mut self,
        mx: f32,
        my: f32,
        panel_x: f32,
    ) -> bool {
        let panel_y = self.panel_rect(UiPanelId::Editor).y;
        for (label, x, y) in [
            ("Open", panel_x + 14.0, panel_y + 40.0),
            ("Save", panel_x + 82.0, panel_y + 40.0),
            ("Undo", panel_x + 150.0, panel_y + 40.0),
            ("Redo", panel_x + 218.0, panel_y + 40.0),
            ("Check", panel_x + 286.0, panel_y + 40.0),
        ] {
            if mx >= x && mx <= x + 58.0 && my >= y && my <= y + 26.0 {
                match label {
                    "Open" => {
                        self.editor_minimized = false;
                        self.status_message = "Editor overlay expanded".to_string();
                    }
                    "Save" => self.save_map(),
                    "Undo" => self.undo_world(),
                    "Redo" => self.redo_world(),
                    "Check" => {
                        self.validation_messages = validate_world(&self.world);
                        self.status_message = if self.validation_messages.is_empty() {
                            "World validation passed".to_string()
                        } else {
                            format!(
                                "World validation: {} warning(s)",
                                self.validation_messages.len()
                            )
                        };
                    }
                    _ => {}
                }
                self.log.event(&self.status_message);
                return true;
            }
        }
        true
    }
}

/// Apply the explicitly selected terrain-paint policy after an editor stroke.
///
/// Exact mode performs no neighboring mutation. Coastline and Hydrology are
/// deliberate authoring operations selected by the user.
fn apply_editor_terrain_paint_policy(
    map: &mut TavernMap,
    min_x: i32,
    min_y: i32,
    max_x: i32,
    max_y: i32,
    mode: TerrainPaintMode,
) -> Result<TerrainPaintModeReport, String> {
    apply_terrain_paint_mode_to_map(map, min_x, min_y, max_x, max_y, mode)
}

fn terrain_paint_policy_suffix(report: TerrainPaintModeReport) -> String {
    let mut parts = Vec::new();
    if report.total_mutations() > 0 {
        parts.push(format!(
            "{} neighboring repair(s)",
            report.total_mutations()
        ));
    }
    if report.unsupported_contacts > 0 {
        parts.push(format!(
            "{} unsupported authored contact(s)",
            report.unsupported_contacts
        ));
    }
    if parts.is_empty() {
        String::new()
    } else {
        format!("; {}", parts.join("; "))
    }
}

#[cfg(test)]
mod shore_water_tests;
