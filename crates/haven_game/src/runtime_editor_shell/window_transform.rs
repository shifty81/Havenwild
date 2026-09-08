use super::*;

impl Game {
    pub(super) fn update_editor_window_transform(&mut self, mx: f32, my: f32) -> bool {
        let rect = self.panel_rect(UiPanelId::Editor);
        let resize_hit = mx >= rect.x + rect.w - 20.0
            && mx <= rect.x + rect.w
            && my >= rect.y + rect.h - 20.0
            && my <= rect.y + rect.h;

        if is_mouse_button_pressed(MouseButton::Left) {
            if resize_hit {
                let (grid_x, grid_y) = panel_grid_from_screen(
                    UiAnchor::TopLeft,
                    rect.x,
                    rect.y,
                    rect.w,
                    rect.h,
                    UI_GRID,
                );
                let layout = self.ui_layout.panel_mut(UiPanelId::Editor);
                layout.anchor = UiAnchor::TopLeft;
                layout.grid_x = grid_x;
                layout.grid_y = grid_y;
                self.editor_resizing = true;
                self.status_message = "Resizing World Editor".to_string();
                return true;
            }
            if rect.title_bar_contains(mx, my) {
                self.layout_drag = Some(LayoutDrag {
                    panel: UiPanelId::Editor,
                    grab_offset: vec2(mx - rect.x, my - rect.y),
                });
                self.status_message = "Moving World Editor".to_string();
                return true;
            }
        }

        if is_mouse_button_down(MouseButton::Left) {
            if self.editor_resizing {
                let current = self.panel_rect(UiPanelId::Editor);
                let layout = self.ui_layout.panel_mut(UiPanelId::Editor);
                layout.width = (mx - current.x)
                    .clamp(600.0, (screen_width() - current.x - UI_GRID).max(600.0));
                layout.height = (my - current.y)
                    .clamp(510.0, (screen_height() - current.y - UI_GRID).max(510.0));
                return true;
            }
            if let Some(drag) = self
                .layout_drag
                .filter(|drag| drag.panel == UiPanelId::Editor)
            {
                let current = self.panel_rect(UiPanelId::Editor);
                let layout = self.ui_layout.panel(UiPanelId::Editor);
                let snapped =
                    snap_panel_to_grid(mx - drag.grab_offset.x, my - drag.grab_offset.y, UI_GRID);
                let (grid_x, grid_y) = panel_grid_from_screen(
                    layout.anchor,
                    snapped.x,
                    snapped.y,
                    current.w,
                    current.h,
                    UI_GRID,
                );
                let layout = self.ui_layout.panel_mut(UiPanelId::Editor);
                layout.grid_x = grid_x;
                layout.grid_y = grid_y;
                return true;
            }
        } else if self.editor_resizing
            || self
                .layout_drag
                .is_some_and(|drag| drag.panel == UiPanelId::Editor)
        {
            self.editor_resizing = false;
            self.layout_drag = None;
            self.save_layout();
            self.status_message = "World Editor layout saved".to_string();
            return true;
        }
        false
    }
}
