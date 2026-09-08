use super::render_helpers::*;
use super::workspace_shell::{AssetBrowserScope, RightDockTab};
use super::*;
use haven_ui::{UiColumn, UiRect, UiTabStripLayout};

const RIGHT_DOCK_TAB_H: f32 = 30.0;
const RIGHT_DOCK_TAB_GAP: f32 = 4.0;
const RIGHT_DOCK_CONTENT_GAP: f32 = 8.0;

fn right_dock_layout(rect: Rect) -> UiTabStripLayout {
    UiTabStripLayout::new(
        UiRect::new(rect.x, rect.y, rect.w, rect.h),
        RIGHT_DOCK_TAB_H,
        RIGHT_DOCK_TAB_GAP,
        RIGHT_DOCK_CONTENT_GAP,
    )
}

fn macroquad_rect(rect: UiRect) -> Rect {
    Rect::new(rect.x, rect.y, rect.width, rect.height)
}

pub(crate) fn right_dock_tab_rect(rect: Rect, index: usize) -> Rect {
    macroquad_rect(right_dock_layout(rect).tab_rect(index, RightDockTab::ALL.len()))
}

pub(crate) fn right_dock_content_rect(rect: Rect) -> Rect {
    macroquad_rect(right_dock_layout(rect).content_rect())
}

pub(crate) fn right_dock_inner_content_rect(rect: Rect) -> Rect {
    let content = right_dock_content_rect(rect);
    Rect::new(
        content.x + 8.0,
        content.y + 8.0,
        (content.w - 16.0).max(1.0),
        (content.h - 16.0).max(1.0),
    )
}

const ASSET_SCOPE_H: f32 = 30.0;
const ASSET_SCOPE_GAP: f32 = 6.0;

fn asset_scope_button_rect(rect: Rect, index: usize) -> Rect {
    let width = ((rect.w - ASSET_SCOPE_GAP) * 0.5).max(1.0);
    Rect::new(rect.x + index as f32 * (width + ASSET_SCOPE_GAP), rect.y, width, ASSET_SCOPE_H)
}

pub(crate) fn asset_scope_content_rect(rect: Rect) -> Rect {
    Rect::new(
        rect.x,
        rect.y + ASSET_SCOPE_H + ASSET_SCOPE_GAP,
        rect.w,
        (rect.h - ASSET_SCOPE_H - ASSET_SCOPE_GAP).max(1.0),
    )
}

impl EditorApp {
    pub(crate) fn contextual_asset_browser_rect(&self) -> Rect {
        if !self.workspace_shell.right_panel_visible
            || self.workspace_shell.right_dock_tab != RightDockTab::Assets
        {
            let rect = self.shell_layout().inspector_content;
            return Rect::new(rect.x, rect.y, 0.0, 0.0);
        }
        right_dock_inner_content_rect(self.shell_layout().inspector_content)
    }

    pub(crate) fn active_asset_browser_body_rect(&self) -> Option<Rect> {
        if !self.workspace_shell.right_panel_visible
            || self.workspace_shell.right_dock_tab != RightDockTab::Assets
        {
            return None;
        }
        let content = right_dock_inner_content_rect(self.shell_layout().inspector_content);
        Some(asset_scope_content_rect(content))
    }

    pub(crate) fn focus_right_dock(&mut self, tab: RightDockTab) {
        self.workspace_shell.right_panel_visible = true;
        self.workspace_shell.right_dock_tab = tab;
        self.workspace_shell.left_panel_visible = false;
        self.persist_workspace_shell(&format!("Opened {} dock", tab.label()));
    }

    pub(crate) fn draw_right_dock(&mut self, validation: &EditorValidationReport) {
        if !self.workspace_shell.right_panel_visible {
            return;
        }
        let host = self.shell_layout().inspector_content;
        for (index, tab) in RightDockTab::ALL.into_iter().enumerate() {
            draw_tab_widget(
                right_dock_tab_rect(host, index),
                tab.label(),
                self.workspace_shell.right_dock_tab == tab,
            );
        }
        let content = right_dock_content_rect(host);
        // W72: every right-dock tab owns one bounded widget surface. Individual
        // inspectors draw into this rect instead of competing for outer-shell
        // coordinates, which keeps Properties/Assets/Outliner/Validation aligned.
        draw_rectangle(
            content.x,
            content.y,
            content.w,
            content.h,
            editor_theme::colors::PANEL_BG,
        );
        draw_rectangle_lines(
            content.x,
            content.y,
            content.w,
            content.h,
            1.0,
            editor_theme::colors::BORDER_SUBTLE,
        );
        let content = Rect::new(
            content.x + 8.0,
            content.y + 8.0,
            (content.w - 16.0).max(1.0),
            (content.h - 16.0).max(1.0),
        );
        match self.workspace_shell.right_dock_tab {
            RightDockTab::Properties => self.draw_right_dock_properties(content),
            RightDockTab::Assets => self.draw_right_dock_assets(content),
            RightDockTab::Outliner => self.draw_right_dock_outliner(content),
            RightDockTab::Validation => draw_validation_report(validation, content),
        }
    }

    fn draw_right_dock_properties(&self, rect: Rect) {
        match self.viewport_mode {
            EditorViewportMode::RegionGraph => self.draw_world_routes_inspector(rect),
            EditorViewportMode::SceneRectangles => self.draw_world_properties(rect),
            EditorViewportMode::SceneBank => self.draw_scene_bank_inspector(rect),
            EditorViewportMode::SceneMap => { if self.game_canvas_ui_active() { self.draw_game_canvas_ui_properties(rect) } else { self.draw_scene_properties(rect) } },
            EditorViewportMode::PixelStudio => self.draw_pixel_inspector(rect),
            EditorViewportMode::AnimationStudio => self.draw_animation_inspector(rect),
            EditorViewportMode::CharacterStudio => self.draw_character_studio_inspector(rect),
            EditorViewportMode::LogicStudio => self.draw_logic_inspector(rect),
            EditorViewportMode::SoundStudio => self.draw_sound_inspector(rect),
        }
    }

    fn draw_right_dock_assets(&mut self, rect: Rect) {
        for (index, scope) in AssetBrowserScope::ALL.into_iter().enumerate() {
            draw_tab_widget(
                asset_scope_button_rect(rect, index),
                scope.label(),
                self.workspace_shell.asset_browser_scope == scope,
            );
        }
        let body = asset_scope_content_rect(rect);
        if self.workspace_shell.asset_browser_scope == AssetBrowserScope::AllProject {
            self.draw_asset_palette(body);
            return;
        }
        match self.viewport_mode {
            EditorViewportMode::PixelStudio => self.draw_pixel_library(body),
            EditorViewportMode::AnimationStudio => self.draw_animation_library(body),
            EditorViewportMode::CharacterStudio => self.draw_character_catalog(body),
            EditorViewportMode::LogicStudio => self.draw_logic_library(body),
            EditorViewportMode::SoundStudio => self.draw_sound_library(body),
            _ => self.draw_asset_palette(body),
        }
    }

    fn draw_right_dock_outliner(&self, rect: Rect) {
        match self.viewport_mode {
            EditorViewportMode::SceneMap => { if self.game_canvas_ui_active() { self.draw_game_canvas_ui_outliner(rect) } else { self.draw_scene_outliner(rect) } },
            EditorViewportMode::SceneBank => self.draw_scene_bank_list(rect),
            EditorViewportMode::RegionGraph | EditorViewportMode::SceneRectangles => {
                self.draw_landmass_list(rect)
            }
            EditorViewportMode::PixelStudio => {
                let mut column = UiColumn::new(
                    UiRect::new(rect.x, rect.y, rect.w, rect.h),
                    0.0,
                    4.0,
                    0.0,
                );
                let header = macroquad_rect(column.take(26.0));
                draw_section_header(header, "Open Documents", Some("Pixel Studio"));
                for tab in self.pixel_studio.document_tab_info().into_iter().take(12) {
                    let row_rect = macroquad_rect(column.take(28.0));
                    draw_list_row(
                        row_rect,
                        &tab.label,
                        tab.dirty.then_some("modified"),
                        tab.active,
                    );
                }
            }
            _ => draw_wrapped(
                "This workspace has no separate hierarchy. Assets and Properties remain available in the same canonical right dock.",
                rect.x,
                rect.y + 12.0,
                rect.w,
                15.0,
                MUTED,
            ),
        }
    }

    pub(crate) fn handle_right_dock_click(&mut self, mx: f32, my: f32) -> bool {
        if !self.workspace_shell.right_panel_visible {
            return false;
        }
        let point = vec2(mx, my);
        let host = self.shell_layout().inspector_content;
        if !host.contains(point) {
            return false;
        }
        for (index, tab) in RightDockTab::ALL.into_iter().enumerate() {
            if right_dock_tab_rect(host, index).contains(point) {
                self.workspace_shell.right_dock_tab = tab;
                self.workspace_shell.left_panel_visible = false;
                        self.persist_workspace_shell(&format!("Opened {} dock", tab.label()));
                return true;
            }
        }
        let content = right_dock_inner_content_rect(host);
        if !content.contains(point) {
            return true;
        }
        match self.workspace_shell.right_dock_tab {
            RightDockTab::Assets => {
                for (index, scope) in AssetBrowserScope::ALL.into_iter().enumerate() {
                    if asset_scope_button_rect(content, index).contains(point) {
                        self.workspace_shell.asset_browser_scope = scope;
                        let _ = self.workspace_shell.save_default();
                        self.status_message = format!("Asset browser scope: {}", scope.label());
                        return true;
                    }
                }
                let body = asset_scope_content_rect(content);
                if self.workspace_shell.asset_browser_scope == AssetBrowserScope::AllProject {
                    self.handle_asset_palette_click(mx, my, body)
                } else {
                    match self.viewport_mode {
                        EditorViewportMode::PixelStudio => self.handle_pixel_library_click(point, body),
                        EditorViewportMode::AnimationStudio => self.handle_animation_library_click_in_rect(point, body),
                        EditorViewportMode::CharacterStudio => self.handle_character_catalog_click_in_rect(point, body),
                        EditorViewportMode::LogicStudio => self.handle_logic_palette_click_in_rect(mx, my, body),
                        EditorViewportMode::SoundStudio => self.handle_sound_palette_click_in_rect(mx, my, body),
                        _ => self.handle_asset_palette_click(mx, my, body),
                    }
                }
            },
            RightDockTab::Outliner => match self.viewport_mode {
                EditorViewportMode::SceneMap => { if self.game_canvas_ui_active() { self.handle_game_canvas_ui_outliner_click(mx, my, content) } else { self.handle_scene_outliner_click(mx, my, content) } },
                EditorViewportMode::SceneBank => self.handle_scene_bank_list_click(mx, my, content),
                EditorViewportMode::RegionGraph | EditorViewportMode::SceneRectangles => {
                    self.handle_landmass_list_click(mx, my, content)
                }
                EditorViewportMode::PixelStudio => {
                    let tabs = self.pixel_studio.document_tab_info();
                    let mut column = UiColumn::new(
                        UiRect::new(content.x, content.y, content.w, content.h),
                        0.0,
                        4.0,
                        0.0,
                    );
                    let _ = column.take(26.0);
                    for tab in tabs.into_iter().take(12) {
                        let row_rect = macroquad_rect(column.take(28.0));
                        if row_rect.contains(point) {
                            let label = tab.label.clone();
                            if self.pixel_studio.activate_document_tab(tab.index) {
                                self.status_message = format!("Focused Pixel document: {label}");
                            }
                            return true;
                        }
                    }
                    true
                }
                _ => true,
            },
            // Scene/world inspectors retain their existing detailed handlers; UI
            // documents own their typed lane/property controls directly here.
            RightDockTab::Properties => {
                if self.game_canvas_ui_active() { self.handle_game_canvas_ui_properties_click(mx, my, content) } else { false }
            },
            RightDockTab::Validation => true,
        }
    }
}
