use super::render_helpers::{draw_editor_widget, draw_editor_widget_tone, WidgetTone};
use super::*;

const TAB_GAP: f32 = 3.0;
const TAB_MAX_W: f32 = 190.0;
const TAB_MIN_W: f32 = 92.0;
const TAB_CLOSE_W: f32 = 22.0;
const TAB_CONTROL_W: f32 = 30.0;
const TAB_CONTROL_GAP: f32 = 4.0;
const SCENE_TAB_LIMIT: usize = 7;
const RECENT_SCENE_LIMIT: usize = 12;
const OVERFLOW_ROW_H: f32 = 30.0;
const OVERFLOW_W: f32 = 300.0;

#[derive(Clone)]
pub(crate) struct SceneDocumentUiState {
    pub edit_tool: SceneEditTool,
    pub layer_mode: SceneLayerMode,
    pub layer_override: Option<super::canvas_layers::CanvasLayerKind>,
    pub active_tool: super::tool_registry::UniversalTool,
    pub authoring_context: super::brush_authoring::CanvasAuthoringContext,
    pub selection: haven_authoring::EditorSelection,
    pub show_grid: bool,
    pub selected_tile: usize,
    pub selected_object: usize,
}

impl Default for SceneDocumentUiState {
    fn default() -> Self {
        Self {
            edit_tool: SceneEditTool::Select,
            layer_mode: SceneLayerMode::Terrain,
            layer_override: None,
            active_tool: super::tool_registry::UniversalTool::Select,
            authoring_context: super::brush_authoring::CanvasAuthoringContext::default(),
            selection: haven_authoring::EditorSelection::default(),
            show_grid: false,
            selected_tile: 0,
            selected_object: 0,
        }
    }
}

pub(crate) fn document_tab_rect(bar: Rect, index: usize, count: usize, right_reserve: f32) -> Rect {
    let available =
        (bar.w - right_reserve - TAB_GAP * count.saturating_sub(1) as f32).max(TAB_MIN_W);
    let width = if count == 0 {
        TAB_MIN_W
    } else {
        (available / count as f32).clamp(TAB_MIN_W, TAB_MAX_W)
    };
    Rect::new(
        bar.x + index as f32 * (width + TAB_GAP),
        bar.y + 2.0,
        width,
        (bar.h - 4.0).max(1.0),
    )
}

fn scene_tab_close_rect(tab: Rect) -> Rect {
    Rect::new(tab.x + tab.w - TAB_CLOSE_W, tab.y, TAB_CLOSE_W, tab.h)
}

fn scene_tab_add_rect(bar: Rect) -> Rect {
    Rect::new(
        bar.x + bar.w - TAB_CONTROL_W * 2.0 - TAB_CONTROL_GAP,
        bar.y + 2.0,
        TAB_CONTROL_W,
        (bar.h - 4.0).max(1.0),
    )
}

fn scene_tab_overflow_rect(bar: Rect) -> Rect {
    Rect::new(
        bar.x + bar.w - TAB_CONTROL_W,
        bar.y + 2.0,
        TAB_CONTROL_W,
        (bar.h - 4.0).max(1.0),
    )
}

fn scene_tab_right_reserve() -> f32 {
    TAB_CONTROL_W * 2.0 + TAB_CONTROL_GAP * 2.0
}

fn scene_tab_capacity(bar: Rect) -> usize {
    let available = (bar.w - scene_tab_right_reserve()).max(TAB_MIN_W);
    (((available + TAB_GAP) / (TAB_MIN_W + TAB_GAP)).floor() as usize)
        .clamp(1, SCENE_TAB_LIMIT)
}

fn scene_tab_window(total: usize, selected: usize, limit: usize) -> std::ops::Range<usize> {
    let limit = limit.max(1).min(SCENE_TAB_LIMIT);
    if total <= limit {
        return 0..total;
    }
    let selected = selected.min(total.saturating_sub(1));
    let start = selected
        .saturating_sub(limit - 1)
        .min(total - limit);
    start..(start + limit)
}

fn draw_bar_background(bar: Rect) {
    draw_rectangle(bar.x, bar.y, bar.w, bar.h, editor_theme::colors::PANEL_HEADER);
    draw_line(
        bar.x,
        bar.y + bar.h,
        bar.x + bar.w,
        bar.y + bar.h,
        1.0,
        editor_theme::colors::BORDER_STRONG,
    );
}

fn compact_scene_tab_label(name: &str, dirty: bool) -> String {
    const MAX_CHARS: usize = 22;
    let mut compact = if name.chars().count() > MAX_CHARS {
        let prefix: String = name.chars().take(MAX_CHARS.saturating_sub(1)).collect();
        format!("{prefix}…")
    } else {
        name.to_string()
    };
    if dirty {
        compact.push_str(" *");
    }
    compact
}

fn overflow_popup_rect(bar: Rect, row_count: usize) -> Rect {
    let h = (row_count.max(1) as f32 * OVERFLOW_ROW_H + 8.0).min(330.0);
    Rect::new(
        (bar.x + bar.w - OVERFLOW_W).max(bar.x),
        bar.y + bar.h + 2.0,
        OVERFLOW_W.min(bar.w),
        h,
    )
}

fn overflow_row_rect(popup: Rect, row: usize) -> Rect {
    Rect::new(
        popup.x + 4.0,
        popup.y + 4.0 + row as f32 * OVERFLOW_ROW_H,
        popup.w - 8.0,
        OVERFLOW_ROW_H - 2.0,
    )
}

impl EditorApp {
    pub(crate) fn store_active_scene_document_ui_state(&mut self) {
        let Some(scene_id) = self
            .model
            .world
            .scenes
            .get(self.selected_scene)
            .map(|scene| scene.id.clone())
        else {
            return;
        };
        if self.command_bus.undo_len() != self.saved_undo_depth {
            self.scene_document_dirty_ids.insert(scene_id.clone());
        }
        self.scene_document_states.insert(
            scene_id,
            SceneDocumentUiState {
                edit_tool: self.scene_edit_tool,
                layer_mode: self.scene_layer_mode,
                layer_override: self.canvas_layer_context_override,
                active_tool: self.canvas_active_tool,
                authoring_context: self.canvas_authoring_context.clone(),
                selection: self.selection.clone(),
                show_grid: self.scene_show_grid,
                selected_tile: self.selected_tile,
                selected_object: self.selected_object,
            },
        );
    }

    pub(crate) fn restore_active_scene_document_ui_state(&mut self) {
        let Some(scene_id) = self
            .model
            .world
            .scenes
            .get(self.selected_scene)
            .map(|scene| scene.id.clone())
        else {
            return;
        };
        let state = self
            .scene_document_states
            .get(&scene_id)
            .cloned()
            .unwrap_or_default();
        self.scene_edit_tool = state.edit_tool;
        self.scene_layer_mode = state.layer_mode;
        self.canvas_layer_context_override = state.layer_override;
        self.canvas_active_tool = state.active_tool;
        self.canvas_authoring_context = state.authoring_context;
        self.selection = state.selection;
        self.scene_show_grid = state.show_grid;
        self.selected_tile = state.selected_tile;
        self.selected_object = state.selected_object;
    }

    pub(crate) fn scene_workspace_has_open_document(&self) -> bool {
        self.active_scene_id().is_some_and(|id| {
            self.open_scene_documents
                .iter()
                .any(|open_id| open_id == &id)
        })
    }

    pub(crate) fn ensure_selected_scene_document_open(&mut self) {
        let Some(scene_id) = self.active_scene_id() else {
            return;
        };
        if !self
            .open_scene_documents
            .iter()
            .any(|open_id| open_id == &scene_id)
        {
            self.open_scene_documents.push(scene_id.clone());
        }
        self.last_active_scene_document = Some(scene_id.clone());
        self.recently_closed_scene_documents
            .retain(|closed_id| closed_id != &scene_id);
    }

    pub(crate) fn activate_scene_workspace(&mut self) {
        self.game_canvas_ui.close_view();
        self.viewport_mode = EditorViewportMode::SceneMap;
        if self.scene_workspace_has_open_document() {
            return;
        }
        let candidate = self
            .last_active_scene_document
            .clone()
            .filter(|id| self.open_scene_documents.iter().any(|open_id| open_id == id))
            .or_else(|| self.open_scene_documents.first().cloned());
        if let Some(scene_id) = candidate {
            if let Some(index) = self.model.world.scenes.position(&scene_id) {
                self.focus_scene_index_without_open(index);
                self.last_active_scene_document = Some(scene_id);
            }
        }
    }

    pub(crate) fn mark_active_scene_document_dirty(&mut self) {
        if let Some(scene_id) = self.active_scene_id() {
            self.scene_document_dirty_ids.insert(scene_id);
        }
    }

    pub(crate) fn clear_scene_document_dirty_state(&mut self) {
        self.scene_document_dirty_ids.clear();
    }

    pub(crate) fn close_scene_document(&mut self, scene_id: &ProjectSceneId) -> bool {
        let Some(position) = self
            .open_scene_documents
            .iter()
            .position(|open_id| open_id == scene_id)
        else {
            return false;
        };
        let was_active = self.active_scene_id().as_ref() == Some(scene_id)
            && self.scene_workspace_has_open_document();
        if was_active {
            self.store_active_scene_document_ui_state();
        }
        self.open_scene_documents.remove(position);
        self.recently_closed_scene_documents
            .retain(|closed_id| closed_id != scene_id);
        self.recently_closed_scene_documents.push(scene_id.clone());
        if self.recently_closed_scene_documents.len() > RECENT_SCENE_LIMIT {
            let excess = self.recently_closed_scene_documents.len() - RECENT_SCENE_LIMIT;
            self.recently_closed_scene_documents.drain(0..excess);
        }
        self.scene_tab_overflow_open = false;

        if self.open_scene_documents.is_empty() {
            if was_active {
                self.selection.clear();
                self.scene_drag = None;
                self.last_active_scene_document = None;
            }
            self.status_message = format!(
                "Closed {} editor tab; scene remains in the project",
                scene_id.label()
            );
            return true;
        }

        if was_active {
            let next_position = position.min(self.open_scene_documents.len() - 1);
            let next_id = self.open_scene_documents[next_position].clone();
            if let Some(index) = self.model.world.scenes.position(&next_id) {
                self.focus_scene_index_without_open(index);
                self.last_active_scene_document = Some(next_id);
            }
        }
        self.status_message = format!(
            "Closed {} editor tab; scene remains in the project",
            scene_id.label()
        );
        true
    }

    pub(crate) fn reopen_last_closed_scene_document(&mut self) -> bool {
        while let Some(scene_id) = self.recently_closed_scene_documents.pop() {
            let Some(index) = self.model.world.scenes.position(&scene_id) else {
                continue;
            };
            self.select_scene_index(index);
            self.viewport_mode = EditorViewportMode::SceneMap;
            self.scene_tab_overflow_open = false;
            self.status_message = format!("Reopened {}", scene_id.label());
            return true;
        }
        self.status_message = "No recently closed Scene document".to_string();
        false
    }

    pub(crate) fn begin_new_scene_from_document_bar(&mut self) {
        self.viewport_mode = EditorViewportMode::SceneMap;
        self.scene_tab_overflow_open = false;
        self.focus_right_dock(super::workspace_shell::RightDockTab::Outliner);
        self.begin_scene_name_edit(SceneNameEditMode::Create);
        self.status_message = "New Scene: enter a name in the Outliner and press Enter".to_string();
    }

    pub(crate) fn browse_project_scenes(&mut self) {
        self.viewport_mode = EditorViewportMode::SceneMap;
        self.scene_tab_overflow_open = false;
        self.focus_right_dock(super::workspace_shell::RightDockTab::Outliner);
        self.status_message = "Browse project scenes in Outliner; selecting a scene opens its document tab".to_string();
    }

    fn open_scene_document_ids(&self) -> Vec<ProjectSceneId> {
        self.open_scene_documents
            .iter()
            .filter(|id| self.model.world.scene_by_id(id).is_some())
            .cloned()
            .collect()
    }

    fn selected_open_scene_position(&self, ids: &[ProjectSceneId]) -> usize {
        let Some(active) = self.active_scene_id() else {
            return 0;
        };
        ids.iter().position(|id| id == &active).unwrap_or(0)
    }

    pub(crate) fn draw_workspace_document_tabs(&self) {
        if self.viewport_mode == EditorViewportMode::PixelStudio {
            return;
        }
        let bar = self.canvas_workspace_layout().document_tabs;
        draw_bar_background(bar);
        if !matches!(self.viewport_mode, EditorViewportMode::SceneMap | EditorViewportMode::PixelStudio)
            && self.workspace_document_is_closed(self.viewport_mode)
        {
            draw_editor_widget_tone(
                document_tab_rect(bar, 0, 1, 0.0),
                &format!("+ Reopen {}", self.viewport_mode.label()),
                false,
                WidgetTone::Quiet,
            );
            return;
        }
        match self.viewport_mode {
            EditorViewportMode::SceneMap => {
                if let Some(document) = self.game_canvas_ui.document.as_ref() {
                    self.draw_single_document_tab(bar, &format!("UI · {}", document.display_name));
                } else {
                    self.draw_scene_document_tabs(bar);
                }
            },
            EditorViewportMode::SceneRectangles => {
                self.draw_single_document_tab(bar, "Complete Seeded World")
            }
            EditorViewportMode::RegionGraph => {
                self.draw_single_document_tab(bar, "World Routes + Scene Library")
            }
            EditorViewportMode::SceneBank => {
                self.draw_single_document_tab(bar, "Scene Library")
            }
            EditorViewportMode::AnimationStudio => {
                let label = self
                    .animation_studio
                    .document
                    .as_ref()
                    .map(|document| document.metadata.display_name.as_str())
                    .unwrap_or("Animation Document");
                self.draw_single_document_tab(bar, label);
            }
            EditorViewportMode::CharacterStudio => {
                self.draw_single_document_tab(bar, "Character Recipe")
            }
            EditorViewportMode::LogicStudio => {
                self.draw_single_document_tab(bar, &self.logic_studio.graph.display_name)
            }
            EditorViewportMode::SoundStudio => {
                self.draw_single_document_tab(bar, &self.sound_studio.document.display_name)
            }
            EditorViewportMode::PixelStudio => {}
        }
    }

    fn draw_scene_document_tabs(&self, bar: Rect) {
        let ids = self.open_scene_document_ids();
        let selected_position = self.selected_open_scene_position(&ids);
        let range = scene_tab_window(ids.len(), selected_position, scene_tab_capacity(bar));
        let visible_count = range.len();
        for (visual_index, open_position) in range.enumerate() {
            let Some(scene_id) = ids.get(open_position) else {
                continue;
            };
            let Some(scene) = self.model.world.scene_by_id(scene_id) else {
                continue;
            };
            let tab = document_tab_rect(
                bar,
                visual_index,
                visible_count.max(1),
                scene_tab_right_reserve(),
            );
            let active = self.active_scene_id().as_ref() == Some(scene_id)
                && self.scene_workspace_has_open_document();
            let tab_dirty = self.scene_document_dirty_ids.contains(scene_id)
                || (active && self.command_bus.undo_len() != self.saved_undo_depth);
            let label = compact_scene_tab_label(&scene.name, tab_dirty);
            draw_editor_widget_tone(
                tab,
                &label,
                active,
                if active {
                    WidgetTone::Primary
                } else {
                    WidgetTone::Quiet
                },
            );
            let close = scene_tab_close_rect(tab);
            draw_editor_text(
                "×",
                close.x + 6.0,
                close.y + close.h * 0.66,
                15.0,
                if active {
                    editor_theme::colors::TEXT_PRIMARY
                } else {
                    editor_theme::colors::TEXT_SECONDARY
                },
            );
        }
        draw_editor_widget(scene_tab_add_rect(bar), "+", false);
        draw_editor_widget(scene_tab_overflow_rect(bar), "▾", self.scene_tab_overflow_open);
    }

    fn draw_single_document_tab(&self, bar: Rect, label: &str) {
        let tab = document_tab_rect(bar, 0, 1, 0.0);
        let display = if self.active_document_dirty() { format!("{label} *") } else { label.to_string() };
        draw_editor_widget_tone(tab, &display, true, WidgetTone::Primary);
        let close = scene_tab_close_rect(tab);
        draw_editor_text(
            "×",
            close.x + 6.0,
            close.y + close.h * 0.66,
            14.0,
            editor_theme::colors::TEXT_PRIMARY,
        );
    }

    pub(crate) fn draw_workspace_document_tab_overlay(&self) {
        if self.viewport_mode != EditorViewportMode::SceneMap || self.game_canvas_ui_active() || !self.scene_tab_overflow_open {
            return;
        }
        let bar = self.canvas_workspace_layout().document_tabs;
        let recent_count = self
            .recently_closed_scene_documents
            .iter()
            .filter(|id| self.model.world.scene_by_id(id).is_some())
            .count();
        let row_count = 3 + recent_count.min(6);
        let popup = overflow_popup_rect(bar, row_count);
        draw_rectangle(
            popup.x,
            popup.y,
            popup.w,
            popup.h,
            editor_theme::colors::PANEL_BG,
        );
        draw_rectangle_lines(
            popup.x,
            popup.y,
            popup.w,
            popup.h,
            1.0,
            editor_theme::colors::BORDER_STRONG,
        );
        draw_editor_widget(overflow_row_rect(popup, 0), "+  New Scene...", false);
        draw_editor_widget(overflow_row_rect(popup, 1), "Browse Project Scenes...", false);
        draw_editor_widget(overflow_row_rect(popup, 2), "Open Scene Library...", false);
        for (row, scene_id) in self
            .recently_closed_scene_documents
            .iter()
            .rev()
            .filter(|id| self.model.world.scene_by_id(id).is_some())
            .take(6)
            .enumerate()
        {
            let label = format!("Reopen  {}", scene_id.label());
            draw_editor_widget(overflow_row_rect(popup, row + 3), &label, false);
        }
    }

    pub(crate) fn draw_scene_workspace_empty_state(&self) {
        if self.viewport_mode != EditorViewportMode::SceneMap || self.scene_workspace_has_open_document() {
            return;
        }
        let viewport = self.canvas_workspace_layout().viewport;
        draw_rectangle(
            viewport.x,
            viewport.y,
            viewport.w,
            viewport.h,
            Color::new(0.055, 0.065, 0.075, 1.0),
        );
        let panel = Rect::new(
            viewport.x + (viewport.w - 420.0).max(0.0) * 0.5,
            viewport.y + (viewport.h - 250.0).max(0.0) * 0.42,
            420.0_f32.min(viewport.w),
            250.0_f32.min(viewport.h),
        );
        draw_editor_text(
            "No Scene Open",
            panel.x + 18.0,
            panel.y + 42.0,
            28.0,
            editor_theme::colors::TEXT_PRIMARY,
        );
        draw_editor_text(
            "Closed tabs never delete project scenes.",
            panel.x + 18.0,
            panel.y + 72.0,
            15.0,
            editor_theme::colors::TEXT_SECONDARY,
        );
        draw_editor_widget(
            Rect::new(panel.x + 18.0, panel.y + 94.0, panel.w - 36.0, 32.0),
            "+ New Scene",
            false,
        );
        draw_editor_widget(
            Rect::new(panel.x + 18.0, panel.y + 134.0, panel.w - 36.0, 32.0),
            "Browse Project Scenes",
            false,
        );
        draw_editor_widget(
            Rect::new(panel.x + 18.0, panel.y + 174.0, panel.w - 36.0, 32.0),
            "Open Scene Library",
            false,
        );
        draw_editor_widget(
            Rect::new(panel.x + 18.0, panel.y + 214.0, panel.w - 36.0, 32.0),
            "Reopen Last Closed",
            false,
        );
    }

    pub(crate) fn handle_workspace_document_tabs_click(&mut self, mx: f32, my: f32) -> bool {
        if self.viewport_mode == EditorViewportMode::PixelStudio {
            return false;
        }
        let point = vec2(mx, my);
        let bar = self.canvas_workspace_layout().document_tabs;

        if self.game_canvas_ui_active() {
            if !bar.contains(point) { return false; }
            let tab = document_tab_rect(bar, 0, 1, 0.0);
            if tab.contains(point) && scene_tab_close_rect(tab).contains(point) {
                self.request_close_active_document();
            }
            return true;
        }

        if !matches!(self.viewport_mode, EditorViewportMode::SceneMap | EditorViewportMode::PixelStudio)
            && bar.contains(point)
        {
            if self.workspace_document_is_closed(self.viewport_mode) {
                self.reopen_workspace_document(self.viewport_mode);
                return true;
            }
            let tab = document_tab_rect(bar, 0, 1, 0.0);
            if tab.contains(point) && scene_tab_close_rect(tab).contains(point) {
                self.request_close_workspace_document(self.viewport_mode);
                return true;
            }
            return true;
        }

        if self.viewport_mode == EditorViewportMode::SceneMap && self.scene_tab_overflow_open {
            let recent: Vec<ProjectSceneId> = self
                .recently_closed_scene_documents
                .iter()
                .rev()
                .filter(|id| self.model.world.scene_by_id(id).is_some())
                .take(6)
                .cloned()
                .collect();
            let popup = overflow_popup_rect(bar, 3 + recent.len());
            if popup.contains(point) {
                for row in 0..(3 + recent.len()) {
                    if !overflow_row_rect(popup, row).contains(point) {
                        continue;
                    }
                    match row {
                        0 => self.begin_new_scene_from_document_bar(),
                        1 => self.browse_project_scenes(),
                        2 => {
                            self.scene_tab_overflow_open = false;
                            self.viewport_mode = EditorViewportMode::SceneBank;
                            self.reopen_workspace_document(EditorViewportMode::SceneBank);
                            self.status_message = "Opened Scene Library".to_string();
                        }
                        _ => {
                            let scene_id = recent[row - 3].clone();
                            if let Some(index) = self.model.world.scenes.position(&scene_id) {
                                self.select_scene_index(index);
                                self.scene_tab_overflow_open = false;
                                self.status_message = format!("Reopened {}", scene_id.label());
                            }
                        }
                    }
                    return true;
                }
                return true;
            }
            if !bar.contains(point) {
                self.scene_tab_overflow_open = false;
                return true;
            }
        }

        if !bar.contains(point) {
            return false;
        }
        if self.viewport_mode == EditorViewportMode::SceneMap {
            if scene_tab_add_rect(bar).contains(point) {
                self.begin_new_scene_from_document_bar();
                return true;
            }
            if scene_tab_overflow_rect(bar).contains(point) {
                self.scene_tab_overflow_open = !self.scene_tab_overflow_open;
                return true;
            }

            let ids = self.open_scene_document_ids();
            let selected_position = self.selected_open_scene_position(&ids);
            let range = scene_tab_window(ids.len(), selected_position, scene_tab_capacity(bar));
            let visible_count = range.len();
            for (visual_index, open_position) in range.enumerate() {
                let Some(scene_id) = ids.get(open_position).cloned() else {
                    continue;
                };
                let tab = document_tab_rect(
                    bar,
                    visual_index,
                    visible_count.max(1),
                    scene_tab_right_reserve(),
                );
                if !tab.contains(point) {
                    continue;
                }
                if scene_tab_close_rect(tab).contains(point) {
                    self.request_close_scene_document(scene_id);
                    return true;
                }
                if let Some(scene_index) = self.model.world.scenes.position(&scene_id) {
                    self.select_scene_index(scene_index);
                    self.status_message = format!("Focused Scene document: {}", scene_id.label());
                }
                return true;
            }
        }
        true
    }

    pub(crate) fn handle_scene_workspace_empty_state_click(&mut self, mx: f32, my: f32) -> bool {
        if self.viewport_mode != EditorViewportMode::SceneMap || self.scene_workspace_has_open_document() {
            return false;
        }
        let viewport = self.canvas_workspace_layout().viewport;
        let panel = Rect::new(
            viewport.x + (viewport.w - 420.0).max(0.0) * 0.5,
            viewport.y + (viewport.h - 250.0).max(0.0) * 0.42,
            420.0_f32.min(viewport.w),
            250.0_f32.min(viewport.h),
        );
        let point = vec2(mx, my);
        if Rect::new(panel.x + 18.0, panel.y + 94.0, panel.w - 36.0, 32.0).contains(point) {
            self.begin_new_scene_from_document_bar();
            return true;
        }
        if Rect::new(panel.x + 18.0, panel.y + 134.0, panel.w - 36.0, 32.0).contains(point) {
            self.browse_project_scenes();
            return true;
        }
        if Rect::new(panel.x + 18.0, panel.y + 174.0, panel.w - 36.0, 32.0).contains(point) {
            self.viewport_mode = EditorViewportMode::SceneBank;
            self.reopen_workspace_document(EditorViewportMode::SceneBank);
            self.status_message = "Opened Scene Library".to_string();
            return true;
        }
        if Rect::new(panel.x + 18.0, panel.y + 214.0, panel.w - 36.0, 32.0).contains(point) {
            self.reopen_last_closed_scene_document();
            return true;
        }
        viewport.contains(point)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn selected_scene_remains_visible_when_scene_count_exceeds_tab_limit() {
        assert_eq!(scene_tab_window(12, 0, 7), 0..7);
        assert_eq!(scene_tab_window(12, 7, 7), 1..8);
        assert_eq!(scene_tab_window(12, 11, 7), 5..12);
    }

    #[test]
    fn document_tabs_fit_inside_reserved_bar() {
        let bar = Rect::new(10.0, 20.0, 900.0, 30.0);
        for count in 1..=8 {
            for index in 0..count {
                let tab = document_tab_rect(bar, index, count, 120.0);
                assert!(tab.x >= bar.x - 0.01);
                assert!(tab.x + tab.w <= bar.x + bar.w - 120.0 + 0.01);
            }
        }
    }

    #[test]
    fn scene_tab_capacity_shrinks_before_tabs_reach_fixed_controls() {
        let narrow = Rect::new(10.0, 20.0, 420.0, 30.0);
        let wide = Rect::new(10.0, 20.0, 1200.0, 30.0);
        assert!(scene_tab_capacity(narrow) < scene_tab_capacity(wide));
        assert!(scene_tab_capacity(narrow) >= 1);
    }

    #[test]
    fn scene_tabs_reserve_new_and_overflow_controls() {
        let bar = Rect::new(10.0, 20.0, 700.0, 30.0);
        let last_tab = document_tab_rect(bar, 4, 5, scene_tab_right_reserve());
        assert!(last_tab.x + last_tab.w <= scene_tab_add_rect(bar).x + 0.01);
        assert!(scene_tab_add_rect(bar).x + scene_tab_add_rect(bar).w <= scene_tab_overflow_rect(bar).x + 0.01);
    }

    #[test]
    fn dirty_marker_is_compact_and_explicit() {
        assert!(compact_scene_tab_label("Estate", true).ends_with(" *"));
        assert!(!compact_scene_tab_label("Estate", false).ends_with(" *"));
    }
}
