use super::render_helpers::{draw_editor_widget_tone, WidgetTone};
use super::*;

const PIXEL_LAYER_FOOTER_H: f32 = 96.0;
const PIXEL_LAYER_ACTION_GAP: f32 = 3.0;
const PIXEL_LAYER_MENU_ROW_H: f32 = 28.0;
const PIXEL_LAYER_MENU_W: f32 = 164.0;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct PixelLayerDragState {
    pub(crate) source_display_index: usize,
    pub(crate) target_display_index: usize,
}

impl EditorApp {
    pub(crate) fn pixel_layer_footer_reserved(&self) -> f32 {
        if self.viewport_mode == EditorViewportMode::PixelStudio
            && self.pixel_studio.document.is_some()
            && !self.workspace_shell.canvas_layer_rail_collapsed
        {
            PIXEL_LAYER_FOOTER_H
        } else {
            0.0
        }
    }

    pub(crate) fn draw_pixel_layer_footer(&self, rect: Rect) {
        if self.viewport_mode != EditorViewportMode::PixelStudio {
            return;
        }
        let Some(document) = self.pixel_studio.document.as_ref() else {
            return;
        };
        let footer = pixel_layer_footer_rect(rect);
        draw_line(
            footer.x + 3.0,
            footer.y,
            footer.x + footer.w - 3.0,
            footer.y,
            1.0,
            editor_theme::colors::BORDER_STRONG,
        );

        // W80: keep the permanent action row compact. Reorder/merge/rename live
        // in one anchored More/context menu instead of consuming six buttons.
        let actions = ["+", "Dup", "Del", "⋯"];
        for (index, label) in actions.into_iter().enumerate() {
            let enabled = match index {
                2 => document.layer_count() > 1,
                _ => true,
            };
            draw_editor_widget_tone(
                pixel_layer_action_rect(rect, index),
                label,
                false,
                if enabled { WidgetTone::Quiet } else { WidgetTone::Disabled },
            );
        }

        let layer = document.active_layer();
        let rename = pixel_layer_rename_field_rect(rect);
        draw_rectangle(rename.x, rename.y, rename.w, rename.h, editor_theme::colors::CONTROL_BG);
        draw_rectangle_lines(
            rename.x,
            rename.y,
            rename.w,
            rename.h,
            if self.pixel_studio.layer_rename_buffer.is_some() { 2.0 } else { 1.0 },
            if self.pixel_studio.layer_rename_buffer.is_some() {
                editor_theme::colors::ACCENT
            } else {
                editor_theme::colors::BORDER_SUBTLE
            },
        );
        let name = self
            .pixel_studio
            .layer_rename_buffer
            .as_deref()
            .unwrap_or(&layer.metadata.name);
        draw_scissored_text(
            name,
            rename.x + 5.0,
            rename.y + 18.0,
            rename.w - 10.0,
            10.5,
            editor_theme::colors::TEXT_PRIMARY,
        );

        let blend = pixel_layer_blend_rect(rect);
        draw_editor_widget_tone(
            blend,
            layer.metadata.blend_mode.label(),
            false,
            WidgetTone::Quiet,
        );

        let opacity = pixel_layer_opacity_slider_rect(rect);
        gui_controls::draw_slider(
            gui_controls::SliderSpec {
                rect: opacity,
                normalized: layer.metadata.opacity as f32 / 255.0,
                label: &format!("Opacity {}%", layer.metadata.opacity as u32 * 100 / 255),
                vertical: false,
                enabled: true,
            },
            matches!(
                self.gui_interaction.capture,
                Some(gui_controls::GuiPointerCapture::LayerOpacity(_))
            ),
        );

        if self.pixel_layer_menu_anchor.is_some() {
            self.draw_pixel_layer_menu();
        }
    }

    fn draw_pixel_layer_menu(&self) {
        let Some(document) = self.pixel_studio.document.as_ref() else { return; };
        let Some(anchor) = self.pixel_layer_menu_anchor else { return; };
        let popup = pixel_layer_menu_rect(anchor);
        draw_rectangle(popup.x, popup.y, popup.w, popup.h, editor_theme::colors::PANEL_RAISED);
        draw_rectangle_lines(popup.x, popup.y, popup.w, popup.h, 1.0, editor_theme::colors::BORDER_STRONG);
        let mouse = vec2(mouse_position().0, mouse_position().1);
        for (index, label) in pixel_layer_menu_labels().into_iter().enumerate() {
            let row = pixel_layer_menu_row_rect(popup, index);
            let enabled = pixel_layer_menu_action_enabled(document, index);
            if enabled && row.contains(mouse) {
                draw_rectangle(row.x, row.y, row.w, row.h, editor_theme::colors::CONTROL_HOVER);
            }
            draw_scissored_text(
                label,
                row.x + 9.0,
                row.y + 19.0,
                row.w - 18.0,
                10.5,
                if enabled { editor_theme::colors::TEXT_PRIMARY } else { editor_theme::colors::TEXT_DISABLED },
            );
        }
    }

    pub(crate) fn handle_pixel_layer_footer_click(&mut self, point: Vec2, rect: Rect) -> bool {
        if self.viewport_mode != EditorViewportMode::PixelStudio || self.pixel_studio.document.is_none() {
            self.pixel_layer_menu_anchor = None;
            return false;
        }

        // The More/context menu is an overlay and can extend into the canvas.
        if let Some(anchor) = self.pixel_layer_menu_anchor {
            let popup = pixel_layer_menu_rect(anchor);
            if popup.contains(point) {
                let index = ((point.y - popup.y - 4.0) / PIXEL_LAYER_MENU_ROW_H).floor() as usize;
                self.execute_pixel_layer_menu_action(index);
                self.pixel_layer_menu_anchor = None;
                return true;
            }
            self.pixel_layer_menu_anchor = None;
            return true;
        }

        if !pixel_layer_footer_rect(rect).contains(point) {
            return false;
        }

        for index in 0..4 {
            if !pixel_layer_action_rect(rect, index).contains(point) {
                continue;
            }
            match index {
                0 => {
                    if let Some(document) = self.pixel_studio.document.as_mut() {
                        let number = document.layer_count() + 1;
                        document.add_layer(format!("Layer {number}"));
                    }
                    self.pixel_studio.refresh_texture();
                    self.status_message = "Added pixel layer".to_string();
                }
                1 => {
                    if let Some(document) = self.pixel_studio.document.as_mut() {
                        document.duplicate_active_layer();
                    }
                    self.pixel_studio.refresh_texture();
                    self.status_message = "Duplicated active layer".to_string();
                }
                2 => {
                    let changed = self
                        .pixel_studio
                        .document
                        .as_mut()
                        .is_some_and(|document| document.delete_active_layer());
                    if changed {
                        self.pixel_studio.refresh_texture();
                        self.status_message = "Deleted active layer".to_string();
                    } else {
                        self.status_message = "A pixel document must keep at least one layer".to_string();
                    }
                }
                3 => {
                    let button = pixel_layer_action_rect(rect, index);
                    self.pixel_layer_menu_anchor = Some(vec2(button.x + button.w + 5.0, button.y));
                }
                _ => {}
            }
            return true;
        }

        if pixel_layer_rename_field_rect(rect).contains(point) {
            self.begin_pixel_layer_rename();
            return true;
        }
        if pixel_layer_blend_rect(rect).contains(point) {
            if let Some(document) = self.pixel_studio.document.as_mut() {
                document.cycle_active_layer_blend_mode();
                self.status_message = format!("Layer blend: {}", document.active_layer().metadata.blend_mode.label());
            }
            self.pixel_studio.refresh_texture();
            return true;
        }
        let opacity = pixel_layer_opacity_slider_rect(rect);
        if opacity.contains(point) {
            self.begin_layer_opacity_drag(opacity);
            return true;
        }
        true
    }

    fn begin_pixel_layer_rename(&mut self) {
        self.pixel_studio.layer_rename_buffer = self
            .pixel_studio
            .document
            .as_ref()
            .map(|document| document.active_layer().metadata.name.clone());
        self.status_message = "Rename active layer: type a name, then press Enter".to_string();
    }

    fn execute_pixel_layer_menu_action(&mut self, index: usize) {
        let enabled = self
            .pixel_studio
            .document
            .as_ref()
            .is_some_and(|document| pixel_layer_menu_action_enabled(document, index));
        if !enabled {
            self.status_message = "Layer action is unavailable for the active layer".to_string();
            return;
        }
        let mut refresh = false;
        match index {
            0 => {
                if let Some(document) = self.pixel_studio.document.as_mut() {
                    refresh = document.move_active_layer(1);
                }
                self.status_message = "Moved active layer up".to_string();
            }
            1 => {
                if let Some(document) = self.pixel_studio.document.as_mut() {
                    refresh = document.move_active_layer(-1);
                }
                self.status_message = "Moved active layer down".to_string();
            }
            2 => {
                if let Some(document) = self.pixel_studio.document.as_mut() {
                    refresh = document.merge_active_down();
                }
                self.status_message = "Merged active layer down".to_string();
            }
            3 => self.begin_pixel_layer_rename(),
            4 => {
                if let Some(document) = self.pixel_studio.document.as_mut() {
                    document.duplicate_active_layer();
                    refresh = true;
                }
                self.status_message = "Duplicated active layer".to_string();
            }
            5 => {
                if let Some(document) = self.pixel_studio.document.as_mut() {
                    refresh = document.delete_active_layer();
                }
                self.status_message = if refresh { "Deleted active layer" } else { "A pixel document must keep at least one layer" }.to_string();
            }
            _ => {}
        }
        if refresh {
            self.pixel_studio.refresh_texture();
        }
    }

    pub(crate) fn apply_pixel_layer_opacity_slider(&mut self, mouse_x: f32, slider: Rect) {
        if self.viewport_mode != EditorViewportMode::PixelStudio {
            return;
        }
        let track_left = slider.x + 12.0;
        let track_width = (slider.w - 24.0).max(1.0);
        let normalized = ((mouse_x - track_left) / track_width).clamp(0.0, 1.0);
        let opacity = (normalized * 255.0).round() as u8;
        let changed = self
            .pixel_studio
            .document
            .as_mut()
            .is_some_and(|document| document.set_active_layer_opacity(opacity));
        if changed {
            self.pixel_studio.refresh_texture();
            self.status_message = format!("Layer opacity: {}%", opacity as u32 * 100 / 255);
        }
    }

    pub(crate) fn begin_pixel_layer_drag(&mut self, display_index: usize) {
        self.pixel_layer_drag = Some(PixelLayerDragState {
            source_display_index: display_index,
            target_display_index: display_index,
        });
    }

    /// Gesture-scoped drag-to-reorder. Locked/reference layers are structural
    /// boundaries: an editable layer cannot be dragged through them.
    pub(crate) fn update_pixel_layer_drag_input(&mut self) -> bool {
        let Some(mut drag) = self.pixel_layer_drag else { return false; };
        if self.viewport_mode != EditorViewportMode::PixelStudio || self.pixel_studio.document.is_none() {
            self.pixel_layer_drag = None;
            return false;
        }
        let rows = self.active_canvas_layer_descriptors();
        let rail = self.canvas_layer_rail_rect();
        let layout = super::canvas_layers::canvas_layer_row_layout(
            &rows,
            rail,
            self.pixel_layer_footer_reserved(),
            self.workspace_shell.canvas_layer_scroll,
        );
        let mouse = vec2(mouse_position().0, mouse_position().1);

        if is_mouse_button_down(MouseButton::Left) {
            if let Some((target, _)) = layout.iter().find(|(_, row_rect)| row_rect.contains(mouse)) {
                if pixel_layer_reorder_allowed(&rows, drag.source_display_index, *target) {
                    drag.target_display_index = *target;
                    self.pixel_layer_drag = Some(drag);
                }
            }
            self.primary_pointer_owned_by_ui = true;
            return true;
        }

        if is_mouse_button_released(MouseButton::Left) || !is_mouse_button_down(MouseButton::Left) {
            self.pixel_layer_drag = None;
            self.primary_pointer_owned_by_ui = false;
            if drag.source_display_index != drag.target_display_index
                && pixel_layer_reorder_allowed(&rows, drag.source_display_index, drag.target_display_index)
            {
                if let Some(document) = self.pixel_studio.document.as_mut() {
                    let count = document.layer_count();
                    let source = pixel_layer_actual_index(count, drag.source_display_index).unwrap_or(0);
                    let target = pixel_layer_actual_index(count, drag.target_display_index).unwrap_or(source);
                    if document.select_layer(source) && document.move_active_layer_to(target) {
                        self.pixel_studio.refresh_texture();
                        self.status_message = "Reordered pixel layer".to_string();
                    }
                }
            }
            return true;
        }
        true
    }

    pub(crate) fn open_pixel_layer_context_menu(&mut self) -> bool {
        if self.viewport_mode != EditorViewportMode::PixelStudio
            || self.pixel_studio.document.is_none()
            || self.workspace_shell.canvas_layer_rail_collapsed
        {
            return false;
        }
        let mouse = vec2(mouse_position().0, mouse_position().1);
        let rail = self.canvas_layer_rail_rect();
        if !rail.contains(mouse) {
            return false;
        }
        let rows = self.active_canvas_layer_descriptors();
        let layout = super::canvas_layers::canvas_layer_row_layout(
            &rows,
            rail,
            self.pixel_layer_footer_reserved(),
            self.workspace_shell.canvas_layer_scroll,
        );
        let Some((display_index, _)) = layout.into_iter().find(|(_, row_rect)| row_rect.contains(mouse)) else {
            return false;
        };
        if let Some(document) = self.pixel_studio.document.as_mut() {
            let actual = pixel_layer_actual_index(document.layer_count(), display_index).unwrap_or(0);
            let _ = document.select_layer(actual);
        }
        self.pixel_brush_popup_open = false;
        self.pixel_symmetry_popup_open = false;
        self.pixel_layer_menu_anchor = Some(mouse + vec2(5.0, 5.0));
        self.status_message = "Pixel layer actions".to_string();
        true
    }
}

pub(crate) fn pixel_layer_actual_index(layer_count: usize, display_index: usize) -> Option<usize> {
    layer_count.checked_sub(display_index.checked_add(1)?)
}

fn pixel_layer_reorder_allowed(
    rows: &[super::canvas_layers::CanvasLayerDescriptor],
    source: usize,
    target: usize,
) -> bool {
    if source >= rows.len() || target >= rows.len() {
        return false;
    }
    let (start, end) = if source <= target { (source, target) } else { (target, source) };
    rows[start..=end].iter().all(|row| !row.locked)
}

fn pixel_layer_footer_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + 3.0, rect.y + rect.h - PIXEL_LAYER_FOOTER_H, rect.w - 6.0, PIXEL_LAYER_FOOTER_H)
}

fn pixel_layer_action_rect(rect: Rect, index: usize) -> Rect {
    let footer = pixel_layer_footer_rect(rect);
    let width = ((footer.w - PIXEL_LAYER_ACTION_GAP * 3.0) / 4.0).max(22.0);
    Rect::new(
        footer.x + index as f32 * (width + PIXEL_LAYER_ACTION_GAP),
        footer.y + 5.0,
        width,
        24.0,
    )
}

fn pixel_layer_rename_field_rect(rect: Rect) -> Rect {
    let footer = pixel_layer_footer_rect(rect);
    let blend_w = (footer.w * 0.38).clamp(56.0, 92.0);
    Rect::new(footer.x, footer.y + 34.0, (footer.w - blend_w - 3.0).max(52.0), 24.0)
}

fn pixel_layer_blend_rect(rect: Rect) -> Rect {
    let rename = pixel_layer_rename_field_rect(rect);
    let footer = pixel_layer_footer_rect(rect);
    Rect::new(rename.x + rename.w + 3.0, rename.y, (footer.x + footer.w - rename.x - rename.w - 3.0).max(48.0), rename.h)
}

fn pixel_layer_opacity_slider_rect(rect: Rect) -> Rect {
    let footer = pixel_layer_footer_rect(rect);
    Rect::new(footer.x, footer.y + 62.0, footer.w, 29.0)
}

fn pixel_layer_menu_labels() -> [&'static str; 6] {
    ["Move Up", "Move Down", "Merge Down", "Rename", "Duplicate", "Delete"]
}

fn pixel_layer_menu_action_enabled(document: &haven_pixel::PixelDocument, index: usize) -> bool {
    match index {
        0 => document.active_layer_index() + 1 < document.layer_count(),
        1 | 2 => document.active_layer_index() > 0,
        5 => document.layer_count() > 1,
        3 | 4 => true,
        _ => false,
    }
}

fn pixel_layer_menu_rect(anchor: Vec2) -> Rect {
    let h = 8.0 + PIXEL_LAYER_MENU_ROW_H * pixel_layer_menu_labels().len() as f32;
    let x = anchor.x.clamp(4.0, (screen_width() - PIXEL_LAYER_MENU_W - 4.0).max(4.0));
    let y = anchor.y.clamp(4.0, (screen_height() - h - 4.0).max(4.0));
    Rect::new(x, y, PIXEL_LAYER_MENU_W, h)
}

fn pixel_layer_menu_row_rect(popup: Rect, index: usize) -> Rect {
    Rect::new(
        popup.x + 4.0,
        popup.y + 4.0 + index as f32 * PIXEL_LAYER_MENU_ROW_H,
        popup.w - 8.0,
        PIXEL_LAYER_MENU_ROW_H - 1.0,
    )
}

#[cfg(test)]
mod tests {
    use super::{pixel_layer_actual_index, pixel_layer_reorder_allowed};
    use crate::app::canvas_layers::{CanvasLayerDescriptor, CanvasLayerGroup, CanvasLayerKind};

    fn row(label: &str, locked: bool) -> CanvasLayerDescriptor {
        CanvasLayerDescriptor {
            label: label.into(),
            kind: CanvasLayerKind::PixelLayer,
            group: CanvasLayerGroup::Visual,
            visible: true,
            locked,
            active: false,
            dirty: false,
        }
    }

    #[test]
    fn canonical_layer_rail_maps_top_row_to_topmost_pixel_layer() {
        assert_eq!(pixel_layer_actual_index(3, 0), Some(2));
        assert_eq!(pixel_layer_actual_index(3, 2), Some(0));
    }

    #[test]
    fn canonical_layer_rail_rejects_rows_outside_pixel_stack() {
        assert_eq!(pixel_layer_actual_index(2, 2), None);
        assert_eq!(pixel_layer_actual_index(0, 0), None);
    }

    #[test]
    fn drag_reorder_cannot_cross_locked_reference_layers() {
        let rows = vec![row("Paint", false), row("Reference", true), row("Base", false)];
        assert!(pixel_layer_reorder_allowed(&rows, 0, 0));
        assert!(!pixel_layer_reorder_allowed(&rows, 0, 2));
        assert!(!pixel_layer_reorder_allowed(&rows, 2, 0));
    }
}
