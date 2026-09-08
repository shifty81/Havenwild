use super::render_helpers::{draw_editor_widget_tone, WidgetTone};
use super::tool_registry::{self, ToolGroup, UniversalTool};
use super::workspace_shell::RightDockTab;
use super::*;

const TOOL_BUTTON_H: f32 = 40.0;
const TOOL_BUTTON_GAP: f32 = 4.0;
const TOOL_GROUP_GAP: f32 = 8.0;
const GROUP_BUTTON: f32 = 36.0;
const POPUP_ROW_H: f32 = 34.0;
const RAIL_HEADER_H: f32 = 32.0;
const BRUSH_SLIDER_H: f32 = 108.0;
const TOOL_HEADER_BUTTON_W: f32 = 24.0;
const TOOL_SHELF_BUTTON_H: f32 = 38.0;
const BRUSH_MODE_BUTTON_H: f32 = 38.0;

impl EditorApp {
    pub(crate) fn canvas_tool_rack_rect(&self) -> Rect {
        let host = self.canvas_overlay_surface_rect();
        let width = self.canvas_tool_rack_width();
        // W72D: Tool Rail is a dedicated sibling column outside the canvas and
        // shares the exact same vertical bounds as Layers and the authored canvas.
        Rect::new(host.x, host.y, width, host.h)
    }

    pub(crate) fn draw_canvas_tool_rack(&self) {
        let rect = self.canvas_tool_rack_rect();
        draw_rectangle(rect.x, rect.y, rect.w, rect.h, Color::new(0.09, 0.09, 0.09, 1.0));
        draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 1.0, editor_theme::colors::BORDER_STRONG);

        let compact = self.workspace_shell.canvas_tool_rail_collapsed;
        let collapse = tool_collapse_rect(rect);
        draw_editor_widget_tone(collapse, "", false, WidgetTone::Quiet);
        draw_chevron_icon(collapse, compact, editor_theme::colors::TEXT_SECONDARY);
        if compact {
            return;
        }
        let layer = self.active_canvas_layer_kind();
        let entries = visible_tool_entries(self.viewport_mode, layer);
        let options_top = tool_options_top(self, rect);
        let start = self.workspace_shell.canvas_tool_scroll.min(entries.len().saturating_sub(1));
        for index in start..entries.len() {
            let (group, tool) = entries[index];
            let button = visible_tool_button_rect_from(rect, &entries, start, index);
            if button.y + button.h > options_top - 3.0 {
                break;
            }
            let active = self.universal_tool_is_active(tool);
            let tone = if active { WidgetTone::Primary } else { WidgetTone::Standard };
            draw_editor_widget_tone(button, "", active, tone);
            let icon_color = if active { WHITE } else { editor_theme::colors::TEXT_PRIMARY };
            draw_tool_icon(tool, centered_icon_rect(button, 27.0), icon_color);

            if index + 1 < entries.len() && entries[index + 1].0 != group {
                let y = button.y + button.h + TOOL_GROUP_GAP * 0.5;
                draw_line(rect.x + 7.0, y, rect.x + rect.w - 7.0, y, 1.0, editor_theme::colors::BORDER_SUBTLE);
            }
        }

        // Tool-specific options are always bottom-anchored. This keeps the upper
        // rail stable while brush size/shape/symmetry change with the active tool.
        if options_top < rect.y + rect.h - 4.0 {
            draw_line(rect.x + 5.0, options_top - 5.0, rect.x + rect.w - 5.0, options_top - 5.0, 1.0, editor_theme::colors::BORDER_STRONG);
        }
        if self.viewport_mode == EditorViewportMode::PixelStudio {
            let symmetry = pixel_symmetry_tool_rect(self, rect);
            let enabled = self.pixel_studio.document.is_some();
            let active = enabled && (self.pixel_studio.symmetry_horizontal || self.pixel_studio.symmetry_vertical);
            let tone = if enabled { if active { WidgetTone::Primary } else { WidgetTone::Standard } } else { WidgetTone::Disabled };
            draw_editor_widget_tone(symmetry, "", active, tone);
            if enabled { draw_symmetry_icon(symmetry, editor_theme::colors::TEXT_PRIMARY); }
            if self.pixel_tool_uses_brush_slider() {
                let brush = pixel_brush_tool_rect(self, rect);
                draw_editor_widget_tone(brush, "", self.pixel_brush_popup_open, WidgetTone::Standard);
                draw_pixel_brush_icon(brush, self.pixel_studio.brush_kind, editor_theme::colors::TEXT_PRIMARY);
                self.draw_contextual_brush_slider(rect);
            }
        } else if self.direct_visual_tool_uses_brush_slider() {
            let brush = pixel_brush_tool_rect(self, rect);
            draw_editor_widget_tone(brush, "", self.pixel_brush_popup_open, WidgetTone::Standard);
            draw_pixel_brush_icon(brush, self.pixel_studio.brush_kind, editor_theme::colors::TEXT_PRIMARY);
            self.draw_contextual_brush_slider(rect);
        } else if self.viewport_mode == EditorViewportMode::SceneRectangles && self.world_tool_uses_brush_slider() {
            self.draw_contextual_brush_slider(rect);
        }

        // A14Y: the lower Tool Rail exposes source plus every compatible brush
        // mode directly. There is no blind mode-cycle button and no hidden
        // secondary-tool menu. The Palette remains a real reserved Canvas panel.
        let source_rect = tool_shelf_source_rect(self, rect);
        let source_enabled = self.canvas_authoring_context.source_kind != super::brush_authoring::BrushSourceKind::None;
        draw_editor_widget_tone(
            source_rect,
            "",
            false,
            if source_enabled { WidgetTone::Standard } else { WidgetTone::Disabled },
        );
        draw_brush_source_icon(
            self.canvas_authoring_context.source_kind,
            centered_icon_rect(source_rect, 25.0),
            if source_enabled { editor_theme::colors::TEXT_PRIMARY } else { editor_theme::colors::TEXT_DISABLED },
        );
        let modes = active_brush_modes(self);
        for (index, mode) in modes.iter().copied().enumerate() {
            let mode_rect = tool_shelf_mode_rect(self, rect, index);
            let active = mode == self.canvas_authoring_context.brush_mode;
            draw_editor_widget_tone(
                mode_rect,
                "",
                active,
                if active { WidgetTone::Primary } else { WidgetTone::Quiet },
            );
            draw_brush_mode_icon(
                mode,
                centered_icon_rect(mode_rect, 25.0),
                if active { WHITE } else { editor_theme::colors::TEXT_PRIMARY },
            );
        }
        let palette_rect = tool_shelf_palette_rect(self, rect);
        let palette_enabled = self.canvas_supports_shared_palette();
        draw_editor_widget_tone(
            palette_rect,
            "",
            self.workspace_shell.shared_palette_visible,
            if palette_enabled { WidgetTone::Quiet } else { WidgetTone::Disabled },
        );
        draw_palette_icon(
            centered_icon_rect(palette_rect, 25.0),
            if palette_enabled { editor_theme::colors::TEXT_PRIMARY } else { editor_theme::colors::TEXT_DISABLED },
        );
    }

    /// W80 overlay pass: Tool Rail flyouts are anchored to their control and
    /// drawn after the Layers rail so they are never displaced to a distant
    /// panel merely to avoid paint-order clipping.
    pub(crate) fn draw_canvas_tool_overlays(&self) {
        if self.pixel_symmetry_popup_open { self.draw_pixel_symmetry_popup(); }
        if self.pixel_brush_popup_open { self.draw_pixel_brush_popup(); }
    }

    pub(crate) fn canvas_tool_tooltip_request(&self) -> Option<(Rect, String)> {
        let rect = self.canvas_tool_rack_rect();
        if self.workspace_shell.canvas_tool_rail_collapsed { return None; }
        let mouse = vec2(mouse_position().0, mouse_position().1);
        let entries = visible_tool_entries(self.viewport_mode, self.active_canvas_layer_kind());
        let options_top = tool_options_top(self, rect);
        let start = self.workspace_shell.canvas_tool_scroll.min(entries.len().saturating_sub(1));
        for index in start..entries.len() {
            let (group, tool) = entries[index];
            let button = visible_tool_button_rect_from(rect, &entries, start, index);
            if button.y + button.h > options_top - 3.0 { break; }
            if button.contains(mouse) {
                let descriptor = tool_registry::descriptor(tool);
                return Some((button, format!("{} • {} • {}", group.label(), descriptor.shortcut, descriptor.help)));
            }
        }
        let collapse = tool_collapse_rect(rect);
        if collapse.contains(mouse) { return Some((collapse, "Collapse Tool Rail".to_string())); }
        let source_rect = tool_shelf_source_rect(self, rect);
        if source_rect.contains(mouse) {
            return Some((source_rect, format!("Brush source: {} • click to open the contextual Palette", self.canvas_authoring_context.compact_source_label())));
        }
        for (index, mode) in active_brush_modes(self).iter().copied().enumerate() {
            let mode_rect = tool_shelf_mode_rect(self, rect, index);
            if mode_rect.contains(mouse) {
                return Some((mode_rect, format!("Brush mode: {}", mode.label())));
            }
        }
        let palette_rect = tool_shelf_palette_rect(self, rect);
        if palette_rect.contains(mouse) {
            return Some((palette_rect, "Contextual Palette • compatible sources for the active layer and brush".to_string()));
        }
        if self.viewport_mode == EditorViewportMode::PixelStudio {
            let symmetry = pixel_symmetry_tool_rect(self, rect);
            if symmetry.contains(mouse) { return Some((symmetry, "Pixel symmetry options".to_string())); }
            let brush = pixel_brush_tool_rect(self, rect);
            if brush.contains(mouse) { return Some((brush, "Brush shape/options".to_string())); }
        }
        None
    }

    pub(crate) fn handle_canvas_tool_rack_click(&mut self, mx: f32, my: f32) -> bool {
        let point = vec2(mx, my);
        let rect = self.canvas_tool_rack_rect();
        if rect.contains(point) {
            self.pixel_layer_menu_anchor = None;
        }

        let collapse = tool_collapse_rect(rect);
        if collapse.contains(point) {
            self.workspace_shell.canvas_tool_rail_collapsed = !self.workspace_shell.canvas_tool_rail_collapsed;
            let _ = self.workspace_shell.save_default();
            self.pixel_symmetry_popup_open = false;
            self.pixel_brush_popup_open = false;
            self.status_message = if self.workspace_shell.canvas_tool_rail_collapsed { "Tool rail compact".to_string() } else { "Tool rail expanded".to_string() };
            return true;
        }
        if self.workspace_shell.canvas_tool_rail_collapsed {
            return rect.contains(point);
        }
        if tool_shelf_source_rect(self, rect).contains(point) {
            if self.canvas_supports_shared_palette() {
                self.workspace_shell.shared_palette_visible = true;
                self.brush_palette_offset = 0;
                let _ = self.workspace_shell.save_default();
                self.status_message = format!("Palette: {}", self.canvas_palette_context_title());
            }
            return true;
        }
        for (index, mode) in active_brush_modes(self).iter().copied().enumerate() {
            if tool_shelf_mode_rect(self, rect, index).contains(point) {
                let _ = self.select_canvas_brush_mode(mode);
                self.brush_palette_offset = 0;
                return true;
            }
        }
        if tool_shelf_palette_rect(self, rect).contains(point) {
            if self.canvas_supports_shared_palette() {
                self.workspace_shell.shared_palette_visible = !self.workspace_shell.shared_palette_visible;
                self.brush_palette_offset = 0;
                self.pixel_color_popup_open = false;
                let _ = self.workspace_shell.save_default();
                self.status_message = if self.workspace_shell.shared_palette_visible {
                    format!("Palette opened: {}", self.canvas_palette_context_title())
                } else {
                    "Palette hidden".to_string()
                };
            }
            return true;
        }
        if self.pixel_brush_popup_open {
            let popup = self.pixel_brush_popup_rect();
            if popup.contains(point) {
                let row = ((my - popup.y - 4.0) / POPUP_ROW_H).floor().max(0.0) as usize;
                let brush_count = haven_pixel::PixelBrushKind::ALL.len();
                if row < brush_count {
                    self.pixel_studio.brush_kind = haven_pixel::PixelBrushKind::ALL[row];
                    self.status_message = format!("Pixel brush: {}", self.pixel_studio.brush_kind.label());
                } else if row == brush_count {
                    self.pixel_studio.brush_density = match self.pixel_studio.brush_density {
                        0..=64 => 128, 65..=128 => 192, 129..=192 => 255, _ => 64,
                    };
                    self.status_message = format!("Brush density: {}%", self.pixel_studio.brush_density as u32 * 100 / 255);
                } else if row == brush_count + 1 {
                    self.pixel_studio.cycle_brush_angle(45);
                    self.status_message = format!("Brush angle: {}°", self.pixel_studio.brush_angle_degrees);
                }
                return true;
            }
            self.pixel_brush_popup_open = false;
        }
        if self.pixel_symmetry_popup_open {
            let popup = self.pixel_symmetry_popup_rect();
            if popup.contains(point) {
                let index = ((my - popup.y - 5.0) / POPUP_ROW_H).floor().clamp(0.0, 3.0) as usize;
                self.apply_pixel_symmetry_mode(index);
                self.pixel_symmetry_popup_open = false;
                return true;
            }
            self.pixel_symmetry_popup_open = false;
        }
        if !rect.contains(point) { return false; }

        if self.viewport_mode == EditorViewportMode::PixelStudio {
            let symmetry = pixel_symmetry_tool_rect(self, rect);
            if symmetry.contains(point) && self.pixel_studio.document.is_some() {
                self.pixel_symmetry_popup_open = !self.pixel_symmetry_popup_open;
                self.pixel_brush_popup_open = false;
                    return true;
            }
        }
        let brush = pixel_brush_tool_rect(self, rect);
        if brush.contains(point) && (self.pixel_tool_uses_brush_slider() || self.direct_visual_tool_uses_brush_slider()) {
            self.pixel_brush_popup_open = !self.pixel_brush_popup_open;
            self.pixel_symmetry_popup_open = false;
            return true;
        }
        let slider = contextual_brush_slider_rect(self, rect, self.viewport_mode == EditorViewportMode::PixelStudio);
        if slider.contains(point) && (self.pixel_tool_uses_brush_slider() || self.direct_visual_tool_uses_brush_slider() || self.world_tool_uses_brush_slider()) {
            self.begin_brush_slider_drag(slider);
            return true;
        }

        let layer = self.active_canvas_layer_kind();
        let entries = visible_tool_entries(self.viewport_mode, layer);
        let options_top = tool_options_top(self, rect);
        let start = self.workspace_shell.canvas_tool_scroll.min(entries.len().saturating_sub(1));
        for index in start..entries.len() {
            let (_group, tool) = entries[index];
            let button = visible_tool_button_rect_from(rect, &entries, start, index);
            if button.y + button.h > options_top - 3.0 { break; }
            if button.contains(point) {
                self.activate_universal_tool(tool);
                let descriptor = tool_registry::descriptor(tool);
                self.status_message = format!("Tool selected: {} [{}] | {}", tool.label(), descriptor.shortcut, descriptor.help);
                return true;
            }
        }
        true
    }

    pub(crate) fn update_canvas_tool_scroll_input(&mut self) -> bool {
        if self.workspace_shell.canvas_tool_rail_collapsed { return false; }
        let mouse = vec2(mouse_position().0, mouse_position().1);
        let rail = self.canvas_tool_rack_rect();
        if !rail.contains(mouse) || mouse.y >= tool_options_top(self, rail) { return false; }
        let wheel = mouse_wheel().1;
        if wheel.abs() < f32::EPSILON { return false; }
        let entries = visible_tool_entries(self.viewport_mode, self.active_canvas_layer_kind());
        let max_scroll = entries.len().saturating_sub(1);
        if wheel > 0.0 {
            self.workspace_shell.canvas_tool_scroll = self.workspace_shell.canvas_tool_scroll.saturating_sub(1);
        } else {
            self.workspace_shell.canvas_tool_scroll = (self.workspace_shell.canvas_tool_scroll + 1).min(max_scroll);
        }
        let _ = self.workspace_shell.save_default();
        true
    }

    fn pixel_tool_uses_brush_slider(&self) -> bool {
        self.viewport_mode == EditorViewportMode::PixelStudio
            && self.pixel_studio.document.is_some()
            && matches!(self.pixel_studio.tool, haven_pixel::PixelTool::Pencil | haven_pixel::PixelTool::Eraser)
    }

    fn direct_visual_tool_uses_brush_slider(&self) -> bool {
        self.direct_visual_authoring_active()
            && matches!(self.canvas_active_tool, UniversalTool::Paint | UniversalTool::Erase)
    }

    fn world_tool_uses_brush_slider(&self) -> bool {
        self.viewport_mode == EditorViewportMode::SceneRectangles
            && self.active_canvas_layer_kind() != Some(super::canvas_layers::CanvasLayerKind::AuthoredPixels)
            && matches!(self.world_edit_tool, WorldEditTool::Paint | WorldEditTool::Erase)
    }

    fn draw_contextual_brush_slider(&self, rail: Rect) {
        let slider = contextual_brush_slider_rect(self, rail, self.viewport_mode == EditorViewportMode::PixelStudio);
        let (step, max_step, label) = if self.viewport_mode == EditorViewportMode::PixelStudio || self.direct_visual_tool_uses_brush_slider() {
            let sizes = [1_u8, 2, 3, 4, 5, 8, 12, 16, 24, 32];
            let step = sizes.iter().position(|v| *v == self.pixel_studio.brush_size).unwrap_or(0) as f32;
            (step, (sizes.len() - 1) as f32, format!("{}px", self.pixel_studio.brush_size))
        } else {
            (self.world_brush_radius.clamp(0, 8) as f32, 8.0, format!("{}t", self.world_brush_radius * 2 + 1))
        };
        let t = if max_step <= 0.0 { 0.0 } else { step / max_step };
        gui_controls::draw_slider(
            gui_controls::SliderSpec {
                rect: slider,
                normalized: t,
                label: &label,
                vertical: true,
                enabled: true,
            },
            matches!(self.gui_interaction.capture, Some(gui_controls::GuiPointerCapture::BrushSlider(_))),
        );
    }

    pub(crate) fn apply_contextual_brush_slider(&mut self, mouse_y: f32, slider: Rect) {
        let usable = (slider.h - 33.0).max(1.0);
        let t = ((slider.y + slider.h - 20.0 - mouse_y) / usable).clamp(0.0, 1.0);
        if self.viewport_mode == EditorViewportMode::PixelStudio || self.direct_visual_tool_uses_brush_slider() {
            let sizes = [1_u8, 2, 3, 4, 5, 8, 12, 16, 24, 32];
            let index = (t * (sizes.len() - 1) as f32).round() as usize;
            self.pixel_studio.brush_size = sizes[index.min(sizes.len() - 1)];
            self.status_message = format!("Pixel brush size: {}px", self.pixel_studio.brush_size);
        } else if self.viewport_mode == EditorViewportMode::SceneRectangles {
            self.world_brush_radius = (t * 8.0).round() as i32;
            self.status_message = format!("World brush: {}x{} tiles", self.world_brush_radius * 2 + 1, self.world_brush_radius * 2 + 1);
        }
    }

    fn pixel_brush_popup_rect(&self) -> Rect {
        let rail = self.canvas_tool_rack_rect();
        let button = pixel_brush_tool_rect(self, rail);
        let rows = haven_pixel::PixelBrushKind::ALL.len() + 2;
        clamp_tool_popup_to_workspace(
            self.main_viewport_rect(),
            Rect::new(
                button.x + button.w + 6.0,
                button.y,
                190.0,
                8.0 + rows as f32 * POPUP_ROW_H,
            ),
        )
    }

    fn draw_pixel_brush_popup(&self) {
        if !(self.pixel_tool_uses_brush_slider() || self.direct_visual_tool_uses_brush_slider()) { return; }
        let popup = self.pixel_brush_popup_rect();
        draw_rectangle(popup.x, popup.y, popup.w, popup.h, editor_theme::colors::PANEL_RAISED);
        draw_rectangle_lines(popup.x, popup.y, popup.w, popup.h, 1.0, editor_theme::colors::BORDER_STRONG);
        let mouse = vec2(mouse_position().0, mouse_position().1);
        for (index, kind) in haven_pixel::PixelBrushKind::ALL.into_iter().enumerate() {
            let row = Rect::new(popup.x + 4.0, popup.y + 4.0 + index as f32 * POPUP_ROW_H, popup.w - 8.0, POPUP_ROW_H - 2.0);
            if row.contains(mouse) { draw_rectangle(row.x, row.y, row.w, row.h, editor_theme::colors::CONTROL_HOVER); }
            if kind == self.pixel_studio.brush_kind { draw_rectangle(row.x, row.y, 3.0, row.h, editor_theme::colors::ACCENT); }
            draw_pixel_brush_icon(Rect::new(row.x + 7.0, row.y + 5.0, 22.0, 22.0), kind, editor_theme::colors::TEXT_PRIMARY);
            draw_editor_text(kind.label(), row.x + 38.0, row.y + 21.0, 12.0, editor_theme::colors::TEXT_PRIMARY);
        }
        let base = haven_pixel::PixelBrushKind::ALL.len();
        let density_row = Rect::new(popup.x + 4.0, popup.y + 4.0 + base as f32 * POPUP_ROW_H, popup.w - 8.0, POPUP_ROW_H - 2.0);
        let density_color = if self.pixel_studio.brush_kind.uses_density() { editor_theme::colors::TEXT_PRIMARY } else { editor_theme::colors::TEXT_DISABLED };
        draw_editor_text(&format!("Density  {}%", self.pixel_studio.brush_density as u32 * 100 / 255), density_row.x + 8.0, density_row.y + 21.0, 11.5, density_color);
        let angle_row = Rect::new(popup.x + 4.0, popup.y + 4.0 + (base + 1) as f32 * POPUP_ROW_H, popup.w - 8.0, POPUP_ROW_H - 2.0);
        let angle_color = if self.pixel_studio.brush_kind.uses_angle() { editor_theme::colors::TEXT_PRIMARY } else { editor_theme::colors::TEXT_DISABLED };
        draw_editor_text(&format!("Angle  {}°", self.pixel_studio.brush_angle_degrees), angle_row.x + 8.0, angle_row.y + 21.0, 11.5, angle_color);
    }

    fn pixel_symmetry_popup_rect(&self) -> Rect {
        let rail = self.canvas_tool_rack_rect();
        let button = pixel_symmetry_tool_rect(self, rail);
        clamp_tool_popup_to_workspace(
            self.main_viewport_rect(),
            Rect::new(
                button.x + button.w + 6.0,
                button.y,
                176.0,
                8.0 + POPUP_ROW_H * 4.0,
            ),
        )
    }

    fn draw_pixel_symmetry_popup(&self) {
        if self.viewport_mode != EditorViewportMode::PixelStudio || self.pixel_studio.document.is_none() { return; }
        let popup = self.pixel_symmetry_popup_rect();
        draw_rectangle(popup.x, popup.y, popup.w, popup.h, editor_theme::colors::PANEL_RAISED);
        draw_rectangle_lines(popup.x, popup.y, popup.w, popup.h, 1.0, editor_theme::colors::BORDER_STRONG);
        let current = match (self.pixel_studio.symmetry_horizontal, self.pixel_studio.symmetry_vertical) {
            (false, false) => 0,
            (true, false) => 1,
            (false, true) => 2,
            (true, true) => 3,
        };
        for (index, label) in ["Off", "Horizontal", "Vertical", "Horizontal + Vertical"].into_iter().enumerate() {
            let row = Rect::new(popup.x + 4.0, popup.y + 4.0 + index as f32 * POPUP_ROW_H, popup.w - 8.0, POPUP_ROW_H - 2.0);
            if index == current { draw_rectangle(row.x, row.y, row.w, row.h, Color::new(0.12, 0.27, 0.42, 1.0)); }
            let center = vec2(row.x + 14.0, row.y + row.h * 0.5);
            draw_circle_lines(center.x, center.y, 6.0, 1.3, editor_theme::colors::TEXT_SECONDARY);
            if index == current { draw_circle(center.x, center.y, 3.2, editor_theme::colors::ACCENT_HOVER); }
            draw_editor_text(label, row.x + 28.0, row.y + 21.0, 12.0, editor_theme::colors::TEXT_PRIMARY);
        }
    }

    fn apply_pixel_symmetry_mode(&mut self, index: usize) {
        let (h, v) = match index {
            1 => (true, false),
            2 => (false, true),
            3 => (true, true),
            _ => (false, false),
        };
        self.pixel_studio.symmetry_horizontal = h;
        self.pixel_studio.symmetry_vertical = v;
        self.status_message = format!("Pixel symmetry: {}", self.pixel_studio.symmetry_label());
    }

    fn universal_tool_available(
        &self,
        layer: Option<super::canvas_layers::CanvasLayerKind>,
        tool: UniversalTool,
    ) -> bool {
        if self.game_canvas_ui_active() {
            return tool == UniversalTool::Select;
        }
        if !tool_registry::tool_is_applicable(self.viewport_mode, layer, tool) {
            return false;
        }
        !(self.active_canvas_layer_locked() && tool.mutates_document())
    }

    fn universal_tool_is_active(&self, tool: UniversalTool) -> bool {
        if self.game_canvas_ui_active() {
            return tool == UniversalTool::Select;
        }
        if self.active_canvas_layer_kind() == Some(super::canvas_layers::CanvasLayerKind::AuthoredPixels)
            && matches!(self.viewport_mode, EditorViewportMode::SceneMap | EditorViewportMode::SceneRectangles)
            && matches!(tool, UniversalTool::Paint | UniversalTool::Erase | UniversalTool::Pick | UniversalTool::PixelEdit)
        {
            return self.canvas_active_tool == tool;
        }
        if matches!(tool, UniversalTool::Move | UniversalTool::Link | UniversalTool::Collision | UniversalTool::PixelEdit | UniversalTool::Event)
            && self.canvas_active_tool == tool { return true; }
        match self.viewport_mode {
            EditorViewportMode::SceneMap => matches!(
                (tool, self.scene_edit_tool),
                (UniversalTool::Select, SceneEditTool::Select)
                    | (UniversalTool::Pan, SceneEditTool::Pan)
                    | (UniversalTool::Paint, SceneEditTool::Paint)
                    | (UniversalTool::Erase, SceneEditTool::Erase)
                    | (UniversalTool::Fill, SceneEditTool::Fill)
                    | (UniversalTool::Replace, SceneEditTool::Replace)
                    | (UniversalTool::Pick, SceneEditTool::Eyedropper)
                    | (UniversalTool::Rectangle, SceneEditTool::Rectangle)
                    | (UniversalTool::Place, SceneEditTool::Place)
            ),
            EditorViewportMode::SceneRectangles => matches!(
                (tool, self.world_edit_tool),
                (UniversalTool::Select, WorldEditTool::Select)
                    | (UniversalTool::Pan, WorldEditTool::Pan)
                    | (UniversalTool::Paint, WorldEditTool::Paint)
                    | (UniversalTool::Erase, WorldEditTool::Erase)
                    | (UniversalTool::Fill, WorldEditTool::Fill)
                    | (UniversalTool::Replace, WorldEditTool::Replace)
                    | (UniversalTool::Pick, WorldEditTool::Eyedropper)
                    | (UniversalTool::Rectangle, WorldEditTool::Rectangle)
                    | (UniversalTool::Place, WorldEditTool::Place)
            ),
            EditorViewportMode::PixelStudio => self.pixel_studio.document.as_ref().is_some_and(|_| match (tool, self.pixel_studio.tool) {
                (UniversalTool::Select, haven_pixel::PixelTool::Selection) => true,
                (UniversalTool::Paint, haven_pixel::PixelTool::Pencil) => true,
                (UniversalTool::Erase, haven_pixel::PixelTool::Eraser) => true,
                (UniversalTool::Fill, haven_pixel::PixelTool::Fill) => true,
                (UniversalTool::Pick, haven_pixel::PixelTool::Eyedropper) => true,
                (UniversalTool::MagicSelect, haven_pixel::PixelTool::MagicSelect) => true,
                (UniversalTool::Rectangle, haven_pixel::PixelTool::Rectangle) => true,
                (UniversalTool::Ellipse, haven_pixel::PixelTool::Ellipse) => true,
                (UniversalTool::Line, haven_pixel::PixelTool::Line) => true,
                (UniversalTool::Gradient, haven_pixel::PixelTool::Gradient) => true,
                (UniversalTool::Blur, haven_pixel::PixelTool::Blur) => true,
                (UniversalTool::Smudge, haven_pixel::PixelTool::Smudge) => true,
                (UniversalTool::Lighten, haven_pixel::PixelTool::Lighten) => true,
                (UniversalTool::Darken, haven_pixel::PixelTool::Darken) => true,
                _ => false,
            }),
            EditorViewportMode::RegionGraph => self.canvas_active_tool == tool,
            EditorViewportMode::SceneBank => self.canvas_active_tool == tool,
            EditorViewportMode::LogicStudio | EditorViewportMode::SoundStudio => self.canvas_active_tool == tool,
            EditorViewportMode::AnimationStudio => match tool {
                UniversalTool::Anchor => matches!(self.animation_studio.placement_mode, super::animation_studio::AnimationPlacementMode::Pivot | super::animation_studio::AnimationPlacementMode::HingePivot | super::animation_studio::AnimationPlacementMode::Foot | super::animation_studio::AnimationPlacementMode::Shadow),
                UniversalTool::Socket => self.animation_studio.placement_mode == super::animation_studio::AnimationPlacementMode::Socket,
                UniversalTool::Select => self.animation_studio.placement_mode == super::animation_studio::AnimationPlacementMode::None,
                _ => false,
            },
            _ => tool == UniversalTool::Select,
        }
    }

    pub(crate) fn activate_universal_tool(&mut self, tool: UniversalTool) {
        let layer = self.active_canvas_layer_kind();
        if !self.universal_tool_available(layer, tool) {
            return;
        }
        self.canvas_active_tool = tool;
        self.sync_canvas_authoring_context();
        if self.game_canvas_ui_active() {
            self.status_message = "UI control selection tool active; drag unlocked controls on the Game Canvas".to_string();
            return;
        }
        match self.viewport_mode {
            EditorViewportMode::SceneMap => match tool {
                UniversalTool::Paint | UniversalTool::Erase | UniversalTool::Pick
                    if layer == Some(super::canvas_layers::CanvasLayerKind::AuthoredPixels) => {
                        self.set_scene_edit_tool(SceneEditTool::Select);
                        self.workspace_shell.shared_palette_visible = true;
                    }
                UniversalTool::Inspect | UniversalTool::Select => self.set_scene_edit_tool(SceneEditTool::Select),
                UniversalTool::Pan => self.set_scene_edit_tool(SceneEditTool::Pan),
                UniversalTool::Paint => self.set_scene_edit_tool(SceneEditTool::Paint),
                UniversalTool::Erase => self.set_scene_edit_tool(SceneEditTool::Erase),
                UniversalTool::Fill => self.set_scene_edit_tool(SceneEditTool::Fill),
                UniversalTool::Replace => self.set_scene_edit_tool(SceneEditTool::Replace),
                UniversalTool::Pick => self.set_scene_edit_tool(SceneEditTool::Eyedropper),
                UniversalTool::Rectangle => self.set_scene_edit_tool(SceneEditTool::Rectangle),
                UniversalTool::Line => self.set_scene_edit_tool(SceneEditTool::Select),
                UniversalTool::Place => { self.set_scene_edit_tool(SceneEditTool::Place); self.focus_right_dock(RightDockTab::Assets); }
                UniversalTool::Collision => { self.canvas_layer_context_override = Some(super::canvas_layers::CanvasLayerKind::Collision); self.set_scene_edit_tool(SceneEditTool::Select); }
                UniversalTool::PixelEdit => {
                    self.set_scene_edit_tool(SceneEditTool::Select);
                    if layer == Some(super::canvas_layers::CanvasLayerKind::TerrainTransitions) {
                        if !self.open_current_terrain_transition_repair_document() {
                            self.reveal_terrain_transition_lab();
                        }
                    } else {
                        self.open_scene_selection_in_pixel_studio();
                    }
                }
                UniversalTool::Move => self.set_scene_edit_tool(SceneEditTool::Select),
                UniversalTool::Link | UniversalTool::Anchor | UniversalTool::Socket | UniversalTool::Event
                | UniversalTool::MagicSelect | UniversalTool::Ellipse | UniversalTool::Gradient
                | UniversalTool::Blur | UniversalTool::Smudge | UniversalTool::Lighten | UniversalTool::Darken
                    => self.set_scene_edit_tool(SceneEditTool::Select),
            },
            EditorViewportMode::SceneRectangles => match tool {
                UniversalTool::Paint | UniversalTool::Erase | UniversalTool::Pick
                    if layer == Some(super::canvas_layers::CanvasLayerKind::AuthoredPixels) => {
                        self.set_world_edit_tool(WorldEditTool::Select);
                        self.workspace_shell.shared_palette_visible = true;
                    }
                UniversalTool::Inspect | UniversalTool::Select => self.set_world_edit_tool(WorldEditTool::Select),
                UniversalTool::Pan => self.set_world_edit_tool(WorldEditTool::Pan),
                UniversalTool::Paint => self.set_world_edit_tool(WorldEditTool::Paint),
                UniversalTool::Erase => self.set_world_edit_tool(WorldEditTool::Erase),
                UniversalTool::Fill => self.set_world_edit_tool(WorldEditTool::Fill),
                UniversalTool::Replace => self.set_world_edit_tool(WorldEditTool::Replace),
                UniversalTool::Pick => self.set_world_edit_tool(WorldEditTool::Eyedropper),
                UniversalTool::Rectangle => self.set_world_edit_tool(WorldEditTool::Rectangle),
                UniversalTool::Line => self.set_world_edit_tool(WorldEditTool::Select),
                UniversalTool::Place => { self.set_world_edit_tool(WorldEditTool::Place); self.focus_right_dock(RightDockTab::Assets); }
                UniversalTool::Collision => { self.canvas_layer_context_override = Some(super::canvas_layers::CanvasLayerKind::Collision); self.set_world_edit_tool(WorldEditTool::Select); }
                UniversalTool::PixelEdit => {
                    self.set_world_edit_tool(WorldEditTool::Select);
                    if layer == Some(super::canvas_layers::CanvasLayerKind::TerrainTransitions) {
                        if !self.open_current_terrain_transition_repair_document() {
                            self.reveal_terrain_transition_lab();
                        }
                    } else {
                        self.open_world_selection_in_pixel_studio();
                    }
                }
                UniversalTool::Move | UniversalTool::Link | UniversalTool::Anchor | UniversalTool::Socket | UniversalTool::Event
                | UniversalTool::MagicSelect | UniversalTool::Ellipse | UniversalTool::Gradient
                | UniversalTool::Blur | UniversalTool::Smudge | UniversalTool::Lighten | UniversalTool::Darken
                    => self.set_world_edit_tool(WorldEditTool::Select),
            },
            EditorViewportMode::PixelStudio => {
                self.pixel_studio.tool = match tool {
                    UniversalTool::Paint => haven_pixel::PixelTool::Pencil,
                    UniversalTool::Erase => haven_pixel::PixelTool::Eraser,
                    UniversalTool::Fill => haven_pixel::PixelTool::Fill,
                    UniversalTool::Pick => haven_pixel::PixelTool::Eyedropper,
                    UniversalTool::MagicSelect => haven_pixel::PixelTool::MagicSelect,
                    UniversalTool::Rectangle => haven_pixel::PixelTool::Rectangle,
                    UniversalTool::Ellipse => haven_pixel::PixelTool::Ellipse,
                    UniversalTool::Line => haven_pixel::PixelTool::Line,
                    UniversalTool::Gradient => haven_pixel::PixelTool::Gradient,
                    UniversalTool::Blur => haven_pixel::PixelTool::Blur,
                    UniversalTool::Smudge => haven_pixel::PixelTool::Smudge,
                    UniversalTool::Lighten => haven_pixel::PixelTool::Lighten,
                    UniversalTool::Darken => haven_pixel::PixelTool::Darken,
                    UniversalTool::Collision => {
                        if let Some(document) = self.pixel_studio.document.as_mut() {
                            let index = document
                                .layers()
                                .iter()
                                .position(|layer| layer.metadata.name == "Collision Add")
                                .or_else(|| document.layers().iter().position(|layer| {
                                    layer.metadata.name.contains("Collision") && !layer.metadata.locked
                                }));
                            if let Some(index) = index {
                                let _ = document.select_layer(index);
                            }
                        }
                        haven_pixel::PixelTool::Pencil
                    }
                    _ => haven_pixel::PixelTool::Selection,
                };
            }
            EditorViewportMode::RegionGraph => {
                if tool == UniversalTool::Link { self.canvas_layer_context_override = Some(super::canvas_layers::CanvasLayerKind::Links); }
            }
            EditorViewportMode::SceneBank => {}
            EditorViewportMode::AnimationStudio => match tool {
                UniversalTool::Inspect | UniversalTool::Select => {
                    self.animation_studio.placement_mode = super::animation_studio::AnimationPlacementMode::None;
                }
                UniversalTool::Anchor => {
                    self.animation_studio.placement_mode = match layer {
                        Some(super::canvas_layers::CanvasLayerKind::AnimationFootAnchor) => super::animation_studio::AnimationPlacementMode::Foot,
                        Some(super::canvas_layers::CanvasLayerKind::AnimationShadowAnchor) => super::animation_studio::AnimationPlacementMode::Shadow,
                        _ => super::animation_studio::AnimationPlacementMode::Pivot,
                    };
                }
                UniversalTool::Socket => {
                    self.animation_studio.placement_mode = super::animation_studio::AnimationPlacementMode::Socket;
                    self.canvas_layer_context_override = Some(super::canvas_layers::CanvasLayerKind::AnimationSockets);
                }
                UniversalTool::Rectangle => {
                    self.animation_studio.bounds_drag_start = None;
                    self.animation_studio.placement_mode = match layer {
                        Some(super::canvas_layers::CanvasLayerKind::AnimationHitboxes) => super::animation_studio::AnimationPlacementMode::Hitbox,
                        Some(super::canvas_layers::CanvasLayerKind::AnimationHurtboxes) => super::animation_studio::AnimationPlacementMode::Hurtbox,
                        _ => super::animation_studio::AnimationPlacementMode::None,
                    };
                }
                UniversalTool::Erase => {
                    if let Some(document) = self.animation_studio.document.as_mut() {
                        if let Some(frame) = document.frame_mut() {
                            match layer {
                                Some(super::canvas_layers::CanvasLayerKind::AnimationHitboxes) => { frame.hitboxes.pop(); },
                                Some(super::canvas_layers::CanvasLayerKind::AnimationHurtboxes) => { frame.hurtboxes.pop(); },
                                _ => {}
                            }
                            document.dirty = true;
                        }
                    }
                }
                UniversalTool::Event => {
                    let event = self.animation_studio.selected_event_kind();
                    let enabled = self.animation_studio.document.as_mut().and_then(|document| document.toggle_selected_event(event));
                    self.canvas_layer_context_override = Some(super::canvas_layers::CanvasLayerKind::AnimationEvents);
                    self.status_message = match enabled {
                        Some(true) => format!("Added {} event to selected frame", event.label()),
                        Some(false) => format!("Removed {} event from selected frame", event.label()),
                        None => "No animation frame is selected".to_string(),
                    };
                }
                UniversalTool::PixelEdit => self.open_selected_animation_frame_in_pixel_studio(),
                _ => {}
            },
            EditorViewportMode::LogicStudio | EditorViewportMode::SoundStudio => {}
            _ => {}
        }
        self.sync_canvas_authoring_context();
        if matches!(tool, UniversalTool::Paint | UniversalTool::Place | UniversalTool::Fill | UniversalTool::Rectangle)
            && self.canvas_authoring_context.brush_mode != super::brush_authoring::BrushMode::None
            && self.canvas_supports_shared_palette()
        {
            self.workspace_shell.shared_palette_visible = true;
        }
    }

    pub(crate) fn handle_contextual_canvas_shortcuts(&mut self) {
        let control = is_key_down(KeyCode::LeftControl) || is_key_down(KeyCode::RightControl);
        let alt = is_key_down(KeyCode::LeftAlt) || is_key_down(KeyCode::RightAlt);
        let shift = is_key_down(KeyCode::LeftShift) || is_key_down(KeyCode::RightShift);
        if control {
            if is_key_pressed(KeyCode::E) {
                let layer = self.active_canvas_layer_kind();
                if self.universal_tool_available(layer, UniversalTool::PixelEdit) {
                    self.activate_universal_tool(UniversalTool::PixelEdit);
                }
            }
            return;
        }
        let digit_keys = [KeyCode::Key1, KeyCode::Key2, KeyCode::Key3, KeyCode::Key4, KeyCode::Key5, KeyCode::Key6, KeyCode::Key7, KeyCode::Key8, KeyCode::Key9];
        if alt {
            for (index, key) in digit_keys.into_iter().enumerate() {
                if is_key_pressed(key) {
                    let _ = self.select_canvas_layer_by_shortcut(index);
                    return;
                }
            }
            return;
        }
        // Shift-modified keys belong to the active workspace (frame editing,
        // symmetry, nudging, etc.). The universal rail only consumes plain keys.
        if shift { return; }
        let bindings = [
            (KeyCode::Key1, UniversalTool::Select),
            (KeyCode::Key2, UniversalTool::Paint),
            (KeyCode::Key3, UniversalTool::Rectangle),
            (KeyCode::Key4, UniversalTool::Fill),
            (KeyCode::Key5, UniversalTool::Move),
            (KeyCode::Key6, UniversalTool::Pick),
            (KeyCode::Key7, UniversalTool::Place),
            (KeyCode::Key8, UniversalTool::Erase),
            (KeyCode::Key9, UniversalTool::Pan),
            (KeyCode::S, UniversalTool::Select),
            (KeyCode::P, UniversalTool::Paint),
            (KeyCode::R, UniversalTool::Rectangle),
            (KeyCode::F, UniversalTool::Fill),
            (KeyCode::Q, UniversalTool::Replace),
            (KeyCode::M, UniversalTool::Move),
            (KeyCode::I, UniversalTool::Pick),
            (KeyCode::E, UniversalTool::Erase),
            (KeyCode::C, UniversalTool::Collision),
            (KeyCode::A, UniversalTool::Anchor),
            (KeyCode::K, UniversalTool::Socket),
            (KeyCode::V, UniversalTool::Event),
            (KeyCode::W, UniversalTool::MagicSelect),
            (KeyCode::O, UniversalTool::Ellipse),
            (KeyCode::G, UniversalTool::Gradient),
            (KeyCode::B, UniversalTool::Blur),
            (KeyCode::U, UniversalTool::Smudge),
            (KeyCode::J, UniversalTool::Lighten),
            (KeyCode::D, UniversalTool::Darken),
        ];
        let layer = self.active_canvas_layer_kind();
        // L is intentionally contextual: Pixel Studio owns Line while world,
        // scene and future node canvases own Link. The numeric group shortcut
        // remains stable even where letter mnemonics differ by canvas domain.
        if is_key_pressed(KeyCode::L) {
            let tool = if self.universal_tool_available(layer, UniversalTool::Line) {
                UniversalTool::Line
            } else {
                UniversalTool::Link
            };
            if self.universal_tool_available(layer, tool) {
                self.activate_universal_tool(tool);
                let descriptor = tool_registry::descriptor(tool);
                self.status_message = format!(
                    "{} | {} | {}",
                    self.viewport_mode.label(),
                    tool.label(),
                    descriptor.help
                );
            } else {
                self.status_message = format!(
                    "{} is unavailable for the active {} layer",
                    tool.label(),
                    self.viewport_mode.label()
                );
            }
            return;
        }
        for (key, tool) in bindings {
            if is_key_pressed(key) {
                if self.universal_tool_available(layer, tool) {
                    self.activate_universal_tool(tool);
                    let descriptor = tool_registry::descriptor(tool);
                    self.status_message = format!("{} | {} | {}", self.viewport_mode.label(), tool.label(), descriptor.help);
                } else {
                    self.status_message = format!("{} is unavailable for the active {} layer", tool.label(), self.viewport_mode.label());
                }
                return;
            }
        }
    }
}

fn visible_tool_entries(viewport: EditorViewportMode, layer: Option<super::canvas_layers::CanvasLayerKind>) -> Vec<(ToolGroup, UniversalTool)> {
    ToolGroup::ALL
        .into_iter()
        .flat_map(|group| group.tools().iter().copied().map(move |tool| (group, tool)))
        .filter(|(_, tool)| tool_registry::tool_is_applicable(viewport, layer, *tool))
        .collect()
}

fn visible_tool_button_rect_from(
    rect: Rect,
    entries: &[(ToolGroup, UniversalTool)],
    start: usize,
    index: usize,
) -> Rect {
    let mut y = rect.y + RAIL_HEADER_H + 5.0;
    for i in start..index {
        y += TOOL_BUTTON_H + TOOL_BUTTON_GAP;
        if i + 1 < entries.len() && entries[i].0 != entries[i + 1].0 { y += TOOL_GROUP_GAP; }
    }
    Rect::new(rect.x + 4.0, y, rect.w - 8.0, TOOL_BUTTON_H)
}

fn tool_collapse_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + 3.0, rect.y + 3.0, TOOL_HEADER_BUTTON_W, RAIL_HEADER_H - 6.0)
}

fn active_brush_modes(app: &EditorApp) -> Vec<super::brush_authoring::BrushMode> {
    super::brush_authoring::compatible_brush_modes(
        app.viewport_mode,
        app.active_canvas_layer_kind(),
        app.canvas_active_tool,
    )
    .iter()
    .copied()
    .filter(|mode| *mode != super::brush_authoring::BrushMode::None)
    .collect()
}

fn tool_shelf_height(app: &EditorApp) -> f32 {
    let mode_count = active_brush_modes(app).len();
    8.0 + TOOL_SHELF_BUTTON_H + 3.0
        + mode_count as f32 * (BRUSH_MODE_BUTTON_H + 3.0)
        + TOOL_SHELF_BUTTON_H
}

fn tool_shelf_source_rect(app: &EditorApp, rect: Rect) -> Rect {
    Rect::new(
        rect.x + 4.0,
        rect.y + rect.h - tool_shelf_height(app) + 3.0,
        rect.w - 8.0,
        TOOL_SHELF_BUTTON_H,
    )
}

fn tool_shelf_mode_rect(app: &EditorApp, rect: Rect, index: usize) -> Rect {
    let source = tool_shelf_source_rect(app, rect);
    Rect::new(
        source.x,
        source.y + TOOL_SHELF_BUTTON_H + 3.0 + index as f32 * (BRUSH_MODE_BUTTON_H + 3.0),
        source.w,
        BRUSH_MODE_BUTTON_H,
    )
}

pub(crate) fn tool_shelf_palette_rect(app: &EditorApp, rect: Rect) -> Rect {
    let mode_count = active_brush_modes(app).len();
    let source = tool_shelf_source_rect(app, rect);
    Rect::new(
        source.x,
        source.y + TOOL_SHELF_BUTTON_H + 3.0 + mode_count as f32 * (BRUSH_MODE_BUTTON_H + 3.0),
        source.w,
        TOOL_SHELF_BUTTON_H,
    )
}

fn centered_icon_rect(button: Rect, edge: f32) -> Rect {
    let edge = edge.min(button.w - 8.0).min(button.h - 8.0).max(10.0);
    Rect::new(
        button.x + (button.w - edge) * 0.5,
        button.y + (button.h - edge) * 0.5,
        edge,
        edge,
    )
}

fn draw_chevron_icon(rect: Rect, points_right: bool, color: Color) {
    let cx = rect.x + rect.w * 0.5;
    let cy = rect.y + rect.h * 0.5;
    let d = 4.0;
    if points_right {
        draw_line(cx - d, cy - d, cx + d, cy, 1.8, color);
        draw_line(cx + d, cy, cx - d, cy + d, 1.8, color);
    } else {
        draw_line(cx + d, cy - d, cx - d, cy, 1.8, color);
        draw_line(cx - d, cy, cx + d, cy + d, 1.8, color);
    }
}

fn draw_palette_icon(rect: Rect, color: Color) {
    let cx = rect.x + rect.w * 0.5;
    let cy = rect.y + rect.h * 0.5;
    draw_circle_lines(cx, cy, rect.w * 0.34, 1.6, color);
    draw_circle(cx - 5.0, cy - 4.0, 2.1, color);
    draw_circle(cx + 1.0, cy - 6.0, 2.1, color);
    draw_circle(cx + 6.0, cy - 1.0, 2.1, color);
    draw_circle_lines(cx + 4.0, cy + 6.0, 3.0, 1.4, color);
}

fn draw_brush_source_icon(kind: super::brush_authoring::BrushSourceKind, rect: Rect, color: Color) {
    use super::brush_authoring::BrushSourceKind as S;
    let x = rect.x;
    let y = rect.y;
    let w = rect.w;
    let h = rect.h;
    let cx = x + w * 0.5;
    let cy = y + h * 0.5;
    match kind {
        S::None => draw_line(x + 5.0, cy, x + w - 5.0, cy, 1.6, color),
        S::PixelColor => {
            draw_circle(cx, cy, 7.0, color);
            draw_circle(cx + 4.0, cy - 4.0, 2.0, editor_theme::colors::PANEL_BG);
        }
        S::TerrainMaterial | S::AtlasCell => {
            draw_rectangle_lines(x + 4.0, y + 4.0, w - 8.0, h - 8.0, 1.5, color);
            draw_line(cx, y + 4.0, cx, y + h - 4.0, 1.0, color);
            draw_line(x + 4.0, cy, x + w - 4.0, cy, 1.0, color);
        }
        S::Stamp | S::StructuralRecipe | S::Object => {
            draw_rectangle_lines(x + 5.0, y + 8.0, w - 10.0, h - 12.0, 1.6, color);
            draw_rectangle(x + 9.0, y + 4.0, w - 18.0, 5.0, color);
        }
        S::CollisionSemantic => {
            draw_triangle(vec2(cx, y + 3.0), vec2(x + 4.0, y + h - 4.0), vec2(x + w - 4.0, y + h - 4.0), color);
            draw_line(cx, y + 9.0, cx, y + h - 9.0, 1.5, editor_theme::colors::PANEL_BG);
        }
        S::NavigationSemantic | S::GameplaySemantic => {
            draw_circle(x + 5.0, y + h - 6.0, 2.5, color);
            draw_circle(cx, cy, 2.5, color);
            draw_circle(x + w - 5.0, y + 6.0, 2.5, color);
            draw_line(x + 7.0, y + h - 7.0, cx - 2.0, cy + 1.0, 1.5, color);
            draw_line(cx + 2.0, cy - 1.0, x + w - 7.0, y + 7.0, 1.5, color);
        }
        S::Light => {
            draw_circle_lines(cx, cy, 5.0, 1.6, color);
            for (dx, dy) in [(0.0,-10.0),(0.0,10.0),(-10.0,0.0),(10.0,0.0)] {
                draw_line(cx + dx * 0.65, cy + dy * 0.65, cx + dx, cy + dy, 1.4, color);
            }
        }
        S::AtmosphereProfile => {
            for offset in [-6.0_f32, 0.0, 6.0] {
                draw_line(x + 4.0, cy + offset, x + w - 4.0, cy + offset, 1.5, color);
            }
        }
        S::WeatherProfile => {
            draw_circle_lines(cx - 4.0, cy - 2.0, 5.0, 1.5, color);
            draw_circle_lines(cx + 3.0, cy - 3.0, 6.0, 1.5, color);
            draw_line(x + 5.0, cy + 2.0, x + w - 5.0, cy + 2.0, 1.5, color);
            draw_line(cx - 4.0, cy + 6.0, cx - 6.0, cy + 10.0, 1.3, color);
            draw_line(cx + 2.0, cy + 6.0, cx, cy + 10.0, 1.3, color);
        }
    }
}

fn draw_brush_mode_icon(mode: super::brush_authoring::BrushMode, rect: Rect, color: Color) {
    use super::brush_authoring::BrushMode as B;
    let x = rect.x;
    let y = rect.y;
    let w = rect.w;
    let h = rect.h;
    let cx = x + w * 0.5;
    let cy = y + h * 0.5;
    match mode {
        B::None => draw_line(x + 5.0, cy, x + w - 5.0, cy, 1.5, color),
        B::Pixel => {
            draw_rectangle_lines(x + 4.0, y + 4.0, w - 8.0, h - 8.0, 1.3, color);
            draw_line(cx, y + 4.0, cx, y + h - 4.0, 1.0, color);
            draw_line(x + 4.0, cy, x + w - 4.0, cy, 1.0, color);
            draw_circle(x + w - 7.0, y + 7.0, 2.3, color);
        }
        B::ExactTile => {
            draw_rectangle_lines(x + 4.0, y + 4.0, w - 8.0, h - 8.0, 1.8, color);
            draw_rectangle_lines(x + 8.0, y + 8.0, w - 16.0, h - 16.0, 1.0, color);
        }
        B::Stamp => {
            draw_rectangle(x + 8.0, y + 4.0, w - 16.0, 6.0, color);
            draw_rectangle_lines(x + 5.0, y + 10.0, w - 10.0, h - 15.0, 1.6, color);
        }
        B::SemanticTerrain => {
            draw_line(x + 3.0, y + h - 6.0, x + 9.0, cy, 1.8, color);
            draw_line(x + 9.0, cy, x + 14.0, y + h - 10.0, 1.8, color);
            draw_line(x + 14.0, y + h - 10.0, x + w - 3.0, y + h - 5.0, 1.8, color);
            draw_line(x + 4.0, y + h - 4.0, x + w - 4.0, y + h - 4.0, 1.3, color);
        }
        B::Autotile => {
            for row in 0..2 { for col in 0..2 {
                draw_rectangle_lines(x + 4.0 + col as f32 * 9.0, y + 4.0 + row as f32 * 9.0, 8.0, 8.0, 1.3, color);
            }}
        }
        B::TerrainElevation => {
            draw_rectangle_lines(x + 4.0, cy + 2.0, w - 12.0, 6.0, 1.4, color);
            draw_rectangle_lines(x + 7.0, cy - 5.0, w - 15.0, 6.0, 1.4, color);
            draw_line(x + w - 6.0, cy + 8.0, x + w - 6.0, cy - 8.0, 1.7, color);
            draw_triangle(vec2(x + w - 6.0, cy - 10.0), vec2(x + w - 9.0, cy - 5.0), vec2(x + w - 3.0, cy - 5.0), color);
        }
        B::Elevation => {
            draw_rectangle(x + 4.0, y + h - 7.0, 6.0, 4.0, color);
            draw_rectangle(x + 10.0, y + h - 12.0, 6.0, 9.0, color);
            draw_rectangle(x + 16.0, y + h - 17.0, 6.0, 14.0, color);
        }
        B::Hydrology => {
            draw_triangle(vec2(cx, y + 3.0), vec2(cx - 7.0, cy + 5.0), vec2(cx + 7.0, cy + 5.0), color);
            draw_circle(cx, cy + 5.0, 7.0, color);
        }
        B::Collision => {
            draw_rectangle_lines(x + 5.0, y + 5.0, w - 10.0, h - 10.0, 1.8, color);
            draw_line(x + 6.0, y + 6.0, x + w - 6.0, y + h - 6.0, 1.6, color);
            draw_line(x + w - 6.0, y + 6.0, x + 6.0, y + h - 6.0, 1.6, color);
        }
        B::Navigation => {
            draw_circle(x + 5.0, y + h - 6.0, 2.4, color);
            draw_circle(cx, cy, 2.4, color);
            draw_circle(x + w - 5.0, y + 6.0, 2.4, color);
            draw_line(x + 7.0, y + h - 7.0, cx - 2.0, cy + 2.0, 1.5, color);
            draw_line(cx + 2.0, cy - 2.0, x + w - 7.0, y + 7.0, 1.5, color);
        }
        B::Object => {
            draw_rectangle_lines(x + 5.0, y + 6.0, w - 10.0, h - 11.0, 1.6, color);
            draw_line(x + 5.0, y + 6.0, cx, y + 2.0, 1.3, color);
            draw_line(x + w - 5.0, y + 6.0, cx, y + 2.0, 1.3, color);
        }
        B::Scatter => {
            for (dx, dy) in [(-7.0,-5.0),(1.0,-7.0),(7.0,-1.0),(-4.0,4.0),(4.0,6.0)] { draw_circle(cx + dx, cy + dy, 2.0, color); }
        }
        B::GameplayRegion => {
            draw_rectangle_lines(x + 4.0, y + 5.0, w - 8.0, h - 10.0, 1.4, color);
            draw_triangle(vec2(cx, y + 8.0), vec2(cx - 5.0, cy + 4.0), vec2(cx + 5.0, cy + 4.0), color);
        }
        B::Lighting => draw_brush_source_icon(super::brush_authoring::BrushSourceKind::Light, rect, color),
        B::Atmosphere => draw_brush_source_icon(super::brush_authoring::BrushSourceKind::AtmosphereProfile, rect, color),
        B::Weather => draw_brush_source_icon(super::brush_authoring::BrushSourceKind::WeatherProfile, rect, color),
        B::VisualOverride => {
            draw_ellipse_lines(cx, cy, 9.0, 5.5, 0.0, 1.5, color);
            draw_circle(cx, cy, 2.5, color);
            draw_line(x + w - 7.0, y + 4.0, x + w - 3.0, y + 8.0, 1.4, color);
            draw_line(x + w - 3.0, y + 4.0, x + w - 7.0, y + 8.0, 1.4, color);
        }
    }
}

fn tool_options_top(app: &EditorApp, rect: Rect) -> f32 {
    if app.viewport_mode == EditorViewportMode::PixelStudio {
        if app.pixel_tool_uses_brush_slider() { pixel_symmetry_tool_rect(app, rect).y }
        else { rect.y + rect.h - tool_shelf_height(app) - GROUP_BUTTON - 8.0 }
    } else if app.direct_visual_tool_uses_brush_slider() {
        pixel_brush_tool_rect(app, rect).y
    } else if app.world_tool_uses_brush_slider() {
        contextual_brush_slider_rect(app, rect, false).y
    } else {
        rect.y + rect.h - tool_shelf_height(app)
    }
}

fn pixel_symmetry_tool_rect(app: &EditorApp, rect: Rect) -> Rect {
    if app.pixel_tool_uses_brush_slider() {
        let slider = contextual_brush_slider_rect(app, rect, true);
        let brush_y = slider.y - GROUP_BUTTON - 6.0;
        Rect::new(rect.x + 3.0, brush_y - GROUP_BUTTON - 6.0, rect.w - 6.0, GROUP_BUTTON)
    } else {
        Rect::new(rect.x + 3.0, rect.y + rect.h - tool_shelf_height(app) - GROUP_BUTTON - 8.0, rect.w - 6.0, GROUP_BUTTON)
    }
}

fn pixel_brush_tool_rect(app: &EditorApp, rect: Rect) -> Rect {
    let slider = contextual_brush_slider_rect(app, rect, true);
    Rect::new(rect.x + 3.0, slider.y - GROUP_BUTTON - 6.0, rect.w - 6.0, GROUP_BUTTON)
}

fn contextual_brush_slider_rect(app: &EditorApp, rect: Rect, after_symmetry: bool) -> Rect {
    // Brush slider remains immediately above the dynamic source/mode/palette shelf.
    // The shelf may grow when a layer exposes several direct brush modes.
    let bottom = rect.y + rect.h - tool_shelf_height(app) - 8.0;
    let h = if after_symmetry { BRUSH_SLIDER_H } else { BRUSH_SLIDER_H.min(rect.h * 0.28) };
    Rect::new(rect.x + 5.0, bottom - h, rect.w - 10.0, h)
}

fn clamp_tool_popup_to_workspace(host: Rect, desired: Rect) -> Rect {
    let margin = 4.0;
    let max_x = (host.x + host.w - desired.w - margin).max(host.x + margin);
    let max_y = (host.y + host.h - desired.h - margin).max(host.y + margin);
    Rect::new(
        desired.x.clamp(host.x + margin, max_x),
        desired.y.clamp(host.y + margin, max_y),
        desired.w.min((host.w - margin * 2.0).max(1.0)),
        desired.h.min((host.h - margin * 2.0).max(1.0)),
    )
}

fn draw_pixel_brush_icon(rect: Rect, kind: haven_pixel::PixelBrushKind, color: Color) {
    let cx = rect.x + rect.w * 0.5;
    let cy = rect.y + rect.h * 0.5;
    match kind {
        haven_pixel::PixelBrushKind::Square => draw_rectangle_lines(cx - 6.0, cy - 6.0, 12.0, 12.0, 1.6, color),
        haven_pixel::PixelBrushKind::Circle => draw_circle_lines(cx, cy, 6.0, 1.6, color),
        haven_pixel::PixelBrushKind::Diamond => {
            draw_line(cx, cy - 7.0, cx + 7.0, cy, 1.6, color);
            draw_line(cx + 7.0, cy, cx, cy + 7.0, 1.6, color);
            draw_line(cx, cy + 7.0, cx - 7.0, cy, 1.6, color);
            draw_line(cx - 7.0, cy, cx, cy - 7.0, 1.6, color);
        }
        haven_pixel::PixelBrushKind::Line => draw_line(cx - 7.0, cy + 6.0, cx + 7.0, cy - 6.0, 2.0, color),
        haven_pixel::PixelBrushKind::Dither => {
            for y in 0..3 { for x in 0..3 { if (x + y) % 2 == 0 { draw_rectangle(cx - 6.0 + x as f32 * 5.0, cy - 6.0 + y as f32 * 5.0, 3.0, 3.0, color); } } }
        }
        haven_pixel::PixelBrushKind::Spray => {
            for (dx, dy) in [(-5.0,-2.0),(0.0,-6.0),(5.0,-3.0),(-3.0,4.0),(3.0,5.0),(0.0,0.0)] { draw_circle(cx + dx, cy + dy, 1.5, color); }
        }
        haven_pixel::PixelBrushKind::Cross => {
            draw_line(cx - 6.0, cy, cx + 6.0, cy, 1.8, color);
            draw_line(cx, cy - 6.0, cx, cy + 6.0, 1.8, color);
        }
        haven_pixel::PixelBrushKind::Ring => draw_circle_lines(cx, cy, 6.0, 1.8, color),
        haven_pixel::PixelBrushKind::Noise => {
            for (dx, dy) in [(-5.0,-4.0),(-3.0,3.0),(0.0,-1.0),(2.0,5.0),(5.0,-5.0),(6.0,2.0)] { draw_circle(cx + dx, cy + dy, 1.0, color); }
        }
    }
}

fn draw_symmetry_icon(rect: Rect, color: Color) {
    let cx = rect.x + rect.w * 0.5;
    let cy = rect.y + rect.h * 0.5;
    draw_line(cx, rect.y + 8.0, cx, rect.y + rect.h - 8.0, 1.0, color);
    draw_line(rect.x + 9.0, cy, rect.x + rect.w - 9.0, cy, 1.0, color);
    draw_circle_lines(cx - 7.0, cy - 7.0, 3.0, 1.2, color);
    draw_circle_lines(cx + 7.0, cy - 7.0, 3.0, 1.2, color);
    draw_circle_lines(cx - 7.0, cy + 7.0, 3.0, 1.2, color);
    draw_circle_lines(cx + 7.0, cy + 7.0, 3.0, 1.2, color);
}

fn draw_tool_icon(tool: UniversalTool, rect: Rect, color: Color) {
    let x = rect.x;
    let y = rect.y;
    let w = rect.w;
    let h = rect.h;
    match tool {
        UniversalTool::Inspect => {
            draw_triangle(vec2(x + 4.0, y + 3.0), vec2(x + 4.0, y + h - 4.0), vec2(x + w - 5.0, y + h - 9.0), color);
            draw_line(x + 11.0, y + 14.0, x + 17.0, y + 21.0, 2.0, color);
        }
        UniversalTool::Select => {
            // W60E5: selection is a marquee, not a generic pointer rectangle.
            let left = x + 4.0; let top = y + 5.0; let right = x + w - 4.0; let bottom = y + h - 5.0;
            let mut px = left;
            while px < right {
                let end = (px + 4.0).min(right);
                draw_line(px, top, end, top, 1.6, color);
                draw_line(px, bottom, end, bottom, 1.6, color);
                px += 7.0;
            }
            let mut py = top;
            while py < bottom {
                let end = (py + 4.0).min(bottom);
                draw_line(left, py, left, end, 1.6, color);
                draw_line(right, py, right, end, 1.6, color);
                py += 7.0;
            }
        }
        UniversalTool::Pan => {
            draw_circle_lines(x + w * 0.5, y + h * 0.53, 7.0, 1.7, color);
            for dx in [-6.0_f32, -2.0, 2.0, 6.0] { draw_line(x + w * 0.5 + dx, y + 3.0, x + w * 0.5 + dx * 0.7, y + 12.0, 1.5, color); }
        }
        UniversalTool::Paint | UniversalTool::PixelEdit => {
            draw_line(x + 5.0, y + h - 5.0, x + w - 6.0, y + 6.0, 4.0, color);
            draw_triangle(vec2(x + 3.0, y + h - 3.0), vec2(x + 9.0, y + h - 5.0), vec2(x + 5.0, y + h - 9.0), color);
        }
        UniversalTool::Erase => {
            draw_triangle(vec2(x + 7.0, y + h - 7.0), vec2(x + 12.0, y + 6.0), vec2(x + w - 5.0, y + 12.0), color);
            draw_triangle(vec2(x + 7.0, y + h - 7.0), vec2(x + w - 5.0, y + 12.0), vec2(x + w - 10.0, y + h - 3.0), color);
        }
        UniversalTool::Fill => {
            draw_rectangle_lines(x + 6.0, y + 7.0, 11.0, 11.0, 1.7, color);
            draw_line(x + 7.0, y + 18.0, x + 19.0, y + 6.0, 2.0, color);
            draw_circle(x + 20.0, y + 19.0, 3.0, color);
        }
        UniversalTool::Replace => {
            let cy = y + h * 0.5;
            draw_line(x + 5.0, cy - 4.0, x + w - 7.0, cy - 4.0, 1.8, color);
            draw_triangle(vec2(x + w - 5.0, cy - 4.0), vec2(x + w - 10.0, cy - 7.0), vec2(x + w - 10.0, cy - 1.0), color);
            draw_line(x + w - 5.0, cy + 4.0, x + 7.0, cy + 4.0, 1.8, color);
            draw_triangle(vec2(x + 5.0, cy + 4.0), vec2(x + 10.0, cy + 1.0), vec2(x + 10.0, cy + 7.0), color);
        }
        UniversalTool::Pick => {
            draw_line(x + 7.0, y + h - 6.0, x + w - 5.0, y + 7.0, 3.0, color);
            draw_circle_lines(x + w - 6.0, y + 6.0, 4.0, 1.6, color);
        }
        UniversalTool::MagicSelect => {
            draw_rectangle_lines(x + 5.0, y + 6.0, w - 10.0, h - 12.0, 1.4, color);
            draw_line(x + 7.0, y + 9.0, x + w - 7.0, y + h - 8.0, 1.2, color);
            draw_circle(x + w - 7.0, y + 7.0, 2.3, color);
        }
        UniversalTool::Rectangle => draw_rectangle_lines(x + 5.0, y + 6.0, w - 10.0, h - 12.0, 2.0, color),
        UniversalTool::Ellipse => draw_ellipse_lines(x + w * 0.5, y + h * 0.5, w * 0.34, h * 0.30, 0.0, 2.0, color),
        UniversalTool::Line => {
            draw_line(x + 5.0, y + h - 6.0, x + w - 5.0, y + 6.0, 2.0, color);
            draw_circle(x + 5.0, y + h - 6.0, 2.2, color);
            draw_circle(x + w - 5.0, y + 6.0, 2.2, color);
        }
        UniversalTool::Gradient => {
            for i in 0..4 {
                let shade = 0.35 + i as f32 * 0.18;
                draw_rectangle(x + 5.0 + i as f32 * 4.0, y + 6.0, 4.0, h - 12.0, Color::new(color.r * shade, color.g * shade, color.b * shade, color.a));
            }
            draw_rectangle_lines(x + 5.0, y + 6.0, 16.0, h - 12.0, 1.2, color);
        }
        UniversalTool::Blur => {
            draw_circle(x + w * 0.45, y + h * 0.5, 6.0, Color::new(color.r, color.g, color.b, color.a * 0.45));
            draw_circle_lines(x + w * 0.55, y + h * 0.5, 7.0, 1.4, color);
        }
        UniversalTool::Smudge => {
            draw_line(x + 5.0, y + h - 7.0, x + 12.0, y + 9.0, 2.4, color);
            draw_line(x + 12.0, y + 9.0, x + w - 5.0, y + 13.0, 2.4, color);
            draw_line(x + 10.0, y + h - 5.0, x + w - 5.0, y + 13.0, 1.2, color);
        }
        UniversalTool::Lighten => {
            let cx = x + w * 0.5; let cy = y + h * 0.5;
            draw_circle_lines(cx, cy, 5.0, 1.8, color);
            for (dx, dy) in [(0.0,-9.0),(0.0,9.0),(-9.0,0.0),(9.0,0.0)] {
                draw_line(cx + dx * 0.65, cy + dy * 0.65, cx + dx, cy + dy, 1.5, color);
            }
        }
        UniversalTool::Darken => {
            draw_circle(x + w * 0.5, y + h * 0.5, 7.0, color);
            draw_circle(x + w * 0.56, y + h * 0.42, 6.0, editor_theme::colors::PANEL_BG);
        }
        UniversalTool::Place => {
            draw_rectangle_lines(x + 5.0, y + 7.0, w - 10.0, h - 12.0, 1.7, color);
            draw_line(x + w * 0.5, y + 10.0, x + w * 0.5, y + h - 8.0, 2.0, color);
            draw_line(x + 9.0, y + h * 0.5, x + w - 9.0, y + h * 0.5, 2.0, color);
        }
        UniversalTool::Move => {
            let cx = x + w * 0.5; let cy = y + h * 0.5;
            draw_line(cx, y + 3.0, cx, y + h - 3.0, 1.8, color); draw_line(x + 3.0, cy, x + w - 3.0, cy, 1.8, color);
            draw_triangle(vec2(cx, y + 2.0), vec2(cx - 3.0, y + 7.0), vec2(cx + 3.0, y + 7.0), color);
            draw_triangle(vec2(x + w - 2.0, cy), vec2(x + w - 7.0, cy - 3.0), vec2(x + w - 7.0, cy + 3.0), color);
        }
        UniversalTool::Link => {
            draw_circle_lines(x + 9.0, y + h * 0.5, 6.0, 1.8, color); draw_circle_lines(x + w - 9.0, y + h * 0.5, 6.0, 1.8, color); draw_line(x + 13.0, y + h * 0.5, x + w - 13.0, y + h * 0.5, 2.0, color);
        }
        UniversalTool::Collision => {
            draw_triangle(vec2(x + w * 0.5, y + 3.0), vec2(x + 5.0, y + 9.0), vec2(x + 7.0, y + h - 6.0), color);
            draw_triangle(vec2(x + w * 0.5, y + 3.0), vec2(x + w - 5.0, y + 9.0), vec2(x + w - 7.0, y + h - 6.0), color);
            draw_line(x + 7.0, y + h - 6.0, x + w - 7.0, y + h - 6.0, 2.0, color);
        }
        UniversalTool::Anchor => {
            let cx = x + w * 0.5; let cy = y + h * 0.5;
            draw_circle_lines(cx, cy, 6.5, 1.5, color);
            draw_line(cx - 10.0, cy, cx + 10.0, cy, 1.5, color);
            draw_line(cx, cy - 10.0, cx, cy + 10.0, 1.5, color);
        }
        UniversalTool::Socket => { draw_circle_lines(x + w * 0.5, y + h * 0.5, 8.0, 2.0, color); draw_circle(x + w * 0.5, y + h * 0.5, 2.5, color); }
        UniversalTool::Event => { draw_triangle(vec2(x + w * 0.5, y + 3.0), vec2(x + 4.0, y + h - 4.0), vec2(x + w - 4.0, y + h - 4.0), color); draw_line(x + w * 0.5, y + 9.0, x + w * 0.5, y + 16.0, 2.0, editor_theme::colors::PANEL_BG); }
    }
}

#[cfg(test)]
mod w81r4_popup_tests {
    use super::*;

    #[test]
    fn popup_is_clamped_above_open_bottom_dock_workspace_edge() {
        let host = Rect::new(10.0, 20.0, 500.0, 400.0);
        let popup = clamp_tool_popup_to_workspace(host, Rect::new(48.0, 360.0, 176.0, 144.0));
        assert!(popup.y >= host.y + 4.0);
        assert!(popup.y + popup.h <= host.y + host.h - 4.0 + f32::EPSILON);
    }

    #[test]
    fn popup_keeps_control_side_anchor_when_it_already_fits() {
        let host = Rect::new(10.0, 20.0, 500.0, 400.0);
        let desired = Rect::new(48.0, 80.0, 176.0, 144.0);
        let popup = clamp_tool_popup_to_workspace(host, desired);
        assert_eq!(popup.x, desired.x);
        assert_eq!(popup.y, desired.y);
    }
}
