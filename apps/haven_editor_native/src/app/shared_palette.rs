use super::pixel_color_panel::{
    handle_pixel_color_controls, pixel_color_popup_close_rect, pixel_color_popup_content,
    pixel_color_popup_panel,
};
use super::render_helpers::draw_editor_widget;
use super::sprite_workspace::*;
use super::*;

const CONTEXTUAL_PALETTE_HEIGHT: f32 = 200.0;

pub(crate) fn shared_palette_height(app: &EditorApp) -> f32 {
    if !app.canvas_supports_shared_palette() || !app.workspace_shell.shared_palette_visible {
        return 0.0;
    }
    if app.viewport_mode == EditorViewportMode::PixelStudio
        || app.canvas_authoring_context.brush_mode == super::brush_authoring::BrushMode::Pixel
    {
        SPRITE_BOTTOM_DOCK_HEIGHT
    } else {
        CONTEXTUAL_PALETTE_HEIGHT
    }
}

pub(crate) fn shared_palette_rect(app: &EditorApp) -> Rect {
    // H21-A14Y: Palette is a reserved sibling surface at the bottom of Canvas.
    // The CanvasWorkspace owns the reservation, so this panel never floats over
    // the authored viewport or steals pointer input from content below it.
    app.canvas_workspace_layout().palette_reserved
}

pub(crate) fn shared_palette_hide_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + rect.w - 72.0, rect.y + 3.0, 64.0, 24.0)
}

impl EditorApp {
    pub(crate) fn canvas_supports_shared_palette(&self) -> bool {
        matches!(
            self.viewport_mode,
            EditorViewportMode::SceneMap | EditorViewportMode::SceneRectangles | EditorViewportMode::PixelStudio
        )
    }

    pub(crate) fn draw_shared_palette_overlay(&mut self) {
        if !self.canvas_supports_shared_palette() || !self.workspace_shell.shared_palette_visible {
            return;
        }
        let rect = shared_palette_rect(self);
        if rect.h <= 1.0 { return; }
        if self.viewport_mode == EditorViewportMode::PixelStudio
            || self.canvas_authoring_context.brush_mode == super::brush_authoring::BrushMode::Pixel
        {
            let colors = self.pixel_studio.active_palette();
            draw_sprite_bottom_dock(
                rect,
                "Palette",
                "Left = FG | Right = BG | + = add color",
                &colors,
                self.pixel_studio.selected_color,
                self.pixel_studio.background_color,
                self.workspace_shell.shared_palette_scroll,
            );
            draw_editor_widget(sprite_bottom_swap_color_rect(rect), "Swap", false);
            draw_editor_widget(sprite_bottom_reset_color_rect(rect), "Reset", false);
        } else {
            // H21-A14Y: contextual resource choices use this same reserved panel;
            // the full Project Asset Browser remains solely in Workspace Dock.
            self.draw_canvas_brush_palette(rect);
        }
        draw_editor_widget(shared_palette_hide_rect(rect), "Hide", false);
    }

    pub(crate) fn handle_shared_palette_click(&mut self, mx: f32, my: f32) -> bool {
        if !self.canvas_supports_shared_palette() || !self.workspace_shell.shared_palette_visible {
            return false;
        }
        let mouse = vec2(mx, my);
        let rect = shared_palette_rect(self);
        if !rect.contains(mouse) { return false; }
        if shared_palette_hide_rect(rect).contains(mouse) {
            self.workspace_shell.shared_palette_visible = false;
            self.close_pixel_color_tray();
            let _ = self.workspace_shell.save_default();
            return true;
        }
        if self.viewport_mode != EditorViewportMode::PixelStudio
            && self.canvas_authoring_context.brush_mode != super::brush_authoring::BrushMode::Pixel
        {
            return self.handle_canvas_brush_palette_click(mx, my, rect);
        }
        if sprite_bottom_foreground_color_rect(rect).contains(mouse) {
            self.open_pixel_color_foreground_tray();
            return true;
        }
        if sprite_bottom_background_color_rect(rect).contains(mouse) {
            self.open_pixel_color_background_tray();
            return true;
        }
        if sprite_bottom_swap_color_rect(rect).contains(mouse) {
            std::mem::swap(&mut self.pixel_studio.selected_color, &mut self.pixel_studio.background_color);
            self.status_message = "Swapped palette foreground/background colors".to_string();
            return true;
        }
        if sprite_bottom_reset_color_rect(rect).contains(mouse) {
            self.pixel_studio.selected_color = [0, 0, 0, 255];
            self.pixel_studio.background_color = [255, 255, 255, 255];
            self.status_message = "Reset palette foreground/background colors".to_string();
            return true;
        }
        let colors = self.pixel_studio.active_palette();
        let visible = sprite_bottom_visible_color_count(
            rect,
            colors.len().saturating_sub(self.workspace_shell.shared_palette_scroll),
        );
        if sprite_bottom_scroll_left_rect(rect).contains(mouse) {
            self.workspace_shell.shared_palette_scroll = self.workspace_shell.shared_palette_scroll.saturating_sub(1);
            let _ = self.workspace_shell.save_default();
            return true;
        }
        if sprite_bottom_scroll_right_rect(rect).contains(mouse) {
            let max = colors.len().saturating_sub(visible.max(1));
            self.workspace_shell.shared_palette_scroll = (self.workspace_shell.shared_palette_scroll + 1).min(max);
            let _ = self.workspace_shell.save_default();
            return true;
        }
        for (visual_index, color) in colors
            .iter()
            .copied()
            .skip(self.workspace_shell.shared_palette_scroll)
            .take(visible)
            .enumerate()
        {
            if sprite_bottom_swatch_rect(rect, visual_index).contains(mouse) {
                self.pixel_studio.selected_color = color;
                self.open_pixel_color_foreground_tray();
                return true;
            }
        }
        if sprite_bottom_add_swatch_rect(rect, visible).contains(mouse) {
            self.open_pixel_color_add_tray();
            return true;
        }
        true
    }

    pub(crate) fn handle_shared_palette_secondary_click(&mut self, mx: f32, my: f32) -> bool {
        if !self.canvas_supports_shared_palette() || !self.workspace_shell.shared_palette_visible {
            return false;
        }
        if self.viewport_mode != EditorViewportMode::PixelStudio
            && self.canvas_authoring_context.brush_mode != super::brush_authoring::BrushMode::Pixel
        {
            return false;
        }
        let mouse = vec2(mx, my);
        let rect = shared_palette_rect(self);
        if !rect.contains(mouse) { return false; }
        if sprite_bottom_background_color_rect(rect).contains(mouse) {
            self.open_pixel_color_background_tray();
            return true;
        }
        let colors = self.pixel_studio.active_palette();
        let visible = sprite_bottom_visible_color_count(
            rect,
            colors.len().saturating_sub(self.workspace_shell.shared_palette_scroll),
        );
        for (visual_index, color) in colors
            .iter()
            .copied()
            .skip(self.workspace_shell.shared_palette_scroll)
            .take(visible)
            .enumerate()
        {
            if sprite_bottom_swatch_rect(rect, visual_index).contains(mouse) {
                self.pixel_studio.background_color = color;
                self.open_pixel_color_background_tray();
                return true;
            }
        }
        // The Palette owns its rectangle. Right-clicking empty Palette chrome must
        // never leak through to a world/object context menu behind it.
        true
    }

    pub(crate) fn handle_shared_palette_popup_click(&mut self, mx: f32, my: f32) -> bool {
        if !self.canvas_supports_shared_palette() || !self.pixel_color_popup_open { return false; }
        let mouse = vec2(mx, my);
        let panel = pixel_color_popup_panel(self);
        if pixel_color_popup_close_rect(panel).contains(mouse) {
            self.close_pixel_color_tray();
            return true;
        }
        let content = pixel_color_popup_content(panel);
        if content.contains(mouse) {
            if super::pixel_color_panel::update_color_from_pointer(self, mouse, content) {
                self.begin_color_picker_drag(content);
                return true;
            }
            let _ = handle_pixel_color_controls(self, mouse, content);
            return true;
        }
        self.close_pixel_color_tray();
        true
    }
}
