use super::render_helpers::*;
use super::*;
use std::f32::consts::TAU;

fn active_edit_color(app: &EditorApp) -> [u8; 4] {
    if app.pixel_color_add_mode {
        app.pixel_color_draft
    } else if app.pixel_color_edit_background {
        app.pixel_studio.background_color
    } else {
        app.pixel_studio.selected_color
    }
}

fn set_active_edit_color(app: &mut EditorApp, color: [u8; 4]) {
    if app.pixel_color_add_mode {
        app.pixel_color_draft = color;
    } else if app.pixel_color_edit_background {
        app.pixel_studio.background_color = color;
    } else {
        app.pixel_studio.selected_color = color;
    }
}

impl EditorApp {
    pub(crate) fn open_pixel_color_foreground_tray(&mut self) {
        self.pixel_color_add_mode = false;
        self.pixel_color_edit_background = false;
        self.pixel_color_popup_open = true;
        self.status_message = "Editing palette foreground color".to_string();
    }

    pub(crate) fn open_pixel_color_background_tray(&mut self) {
        self.pixel_color_add_mode = false;
        self.pixel_color_edit_background = true;
        self.pixel_color_popup_open = true;
        self.status_message = "Editing palette background color".to_string();
    }

    pub(crate) fn open_pixel_color_add_tray(&mut self) {
        self.pixel_color_add_mode = true;
        self.pixel_color_edit_background = false;
        self.pixel_color_draft = self.pixel_studio.selected_color;
        self.pixel_color_popup_open = true;
        self.status_message = "Choose a new document palette color".to_string();
    }

    pub(crate) fn close_pixel_color_tray(&mut self) {
        self.pixel_color_popup_open = false;
        self.pixel_color_add_mode = false;
    }
}

pub(crate) fn color_wheel_center(rect: Rect) -> Vec2 {
    vec2(rect.x + rect.w * 0.38, rect.y + 104.0)
}

pub(crate) fn color_wheel_outer_radius(rect: Rect) -> f32 {
    (rect.w * 0.20).clamp(42.0, 54.0)
}

pub(crate) fn color_value_rect(rect: Rect) -> Rect {
    let radius = color_wheel_outer_radius(rect);
    let center = color_wheel_center(rect);
    Rect::new(
        center.x + radius + 14.0,
        center.y - radius,
        22.0,
        radius * 2.0,
    )
}

pub(crate) fn color_foreground_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + 174.0, 74.0, 46.0)
}

pub(crate) fn color_background_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + 84.0, rect.y + 174.0, 74.0, 46.0)
}

pub(crate) fn color_swap_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + 170.0, rect.y + 180.0, 54.0, 28.0)
}

pub(crate) fn color_reset_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + 230.0, rect.y + 180.0, 60.0, 28.0)
}

pub(crate) fn color_channel_minus_rect(rect: Rect, channel: usize) -> Rect {
    Rect::new(
        rect.x + 116.0,
        rect.y + 258.0 + channel as f32 * 28.0,
        30.0,
        26.0,
    )
}

pub(crate) fn color_channel_plus_rect(rect: Rect, channel: usize) -> Rect {
    Rect::new(
        rect.x + 222.0,
        rect.y + 258.0 + channel as f32 * 28.0,
        30.0,
        26.0,
    )
}

pub(crate) fn color_add_palette_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + rect.h - 32.0, rect.w.min(196.0), 28.0)
}

pub(crate) fn draw_pixel_color_panel(app: &EditorApp, rect: Rect) {
    // Color-wheel primitives are one of the heaviest immediate-mode UI surfaces in
    // the editor. Flush/normalize the screen-space UI boundary before and after the
    // wheel so primitive batching cannot leak a stale tint/material into editor text.
    set_default_camera();
    gl_use_default_material();
    let fg = app.pixel_studio.selected_color;
    let bg = app.pixel_studio.background_color;
    let active_color = active_edit_color(app);
    let (hue, saturation, value) = rgba_to_hsv(active_color);
    let center = color_wheel_center(rect);
    let outer = color_wheel_outer_radius(rect);
    let inner = outer * 0.70;

    let mode_label = if app.pixel_color_add_mode {
        "New Palette Color"
    } else if app.pixel_color_edit_background {
        "Background"
    } else {
        "Foreground"
    };
    draw_editor_text(mode_label, rect.x, rect.y + 20.0, 17.0, TEXT);

    let segments = 72;
    for segment in 0..segments {
        let a0 = segment as f32 / segments as f32 * TAU;
        let a1 = (segment + 1) as f32 / segments as f32 * TAU;
        let color = hsv_to_color(segment as f32 / segments as f32, 1.0, 1.0, 1.0);
        draw_triangle(
            center + vec2(a0.cos(), a0.sin()) * inner,
            center + vec2(a0.cos(), a0.sin()) * outer,
            center + vec2(a1.cos(), a1.sin()) * outer,
            color,
        );
        draw_triangle(
            center + vec2(a0.cos(), a0.sin()) * inner,
            center + vec2(a1.cos(), a1.sin()) * outer,
            center + vec2(a1.cos(), a1.sin()) * inner,
            color,
        );
    }

    // Saturation disc for the active hue. It is deliberately stepped so the
    // editor stays dependency-free and pixel-art friendly.
    for ring in (1..=18).rev() {
        let s = ring as f32 / 18.0;
        draw_circle(
            center.x,
            center.y,
            inner * s,
            hsv_to_color(hue, s, value, 1.0),
        );
    }
    draw_circle(center.x, center.y, 2.0, hsv_to_color(hue, 0.0, value, 1.0));

    let hue_angle = hue * TAU;
    let hue_marker = center + vec2(hue_angle.cos(), hue_angle.sin()) * ((inner + outer) * 0.5);
    draw_circle_lines(hue_marker.x, hue_marker.y, 5.0, 2.0, WHITE);
    let sat_marker = center + vec2(1.0, 0.0) * inner * saturation;
    draw_circle_lines(sat_marker.x, sat_marker.y, 5.0, 2.0, WHITE);

    let value_rect = color_value_rect(rect);
    let steps = 32;
    for step in 0..steps {
        let t0 = step as f32 / steps as f32;
        let t1 = (step + 1) as f32 / steps as f32;
        draw_rectangle(
            value_rect.x,
            value_rect.y + t0 * value_rect.h,
            value_rect.w,
            (t1 - t0) * value_rect.h + 1.0,
            hsv_to_color(hue, saturation, 1.0 - t0, 1.0),
        );
    }
    draw_rectangle_lines(
        value_rect.x,
        value_rect.y,
        value_rect.w,
        value_rect.h,
        1.0,
        PANEL_EDGE,
    );
    let value_y = value_rect.y + (1.0 - value) * value_rect.h;
    draw_line(
        value_rect.x - 3.0,
        value_y,
        value_rect.x + value_rect.w + 3.0,
        value_y,
        2.0,
        WHITE,
    );

    // Re-establish the canonical UI state after the procedural wheel/value geometry
    // before any glyphs are queued. This closes the recurring black-text regression.
    set_default_camera();
    gl_use_default_material();

    draw_color_swatch(color_background_rect(rect), bg, !app.pixel_color_add_mode && app.pixel_color_edit_background, "BG");
    draw_color_swatch(
        color_foreground_rect(rect),
        if app.pixel_color_add_mode { app.pixel_color_draft } else { fg },
        app.pixel_color_add_mode || !app.pixel_color_edit_background,
        if app.pixel_color_add_mode { "NEW" } else { "FG" },
    );
    draw_editor_widget(color_swap_rect(rect), "Swap", false);
    draw_editor_widget(color_reset_rect(rect), "Reset", false);

    draw_editor_text(
        &format!("#{:02X}{:02X}{:02X}{:02X}", active_color[0], active_color[1], active_color[2], active_color[3]),
        rect.x,
        rect.y + 238.0,
        18.0,
        TEXT,
    );
    for (channel, label) in ["R", "G", "B", "A"].into_iter().enumerate() {
        draw_editor_text(
            label,
            rect.x,
            rect.y + 260.0 + channel as f32 * 28.0,
            15.0,
            MUTED,
        );
        draw_editor_widget(color_channel_minus_rect(rect, channel), "-", false);
        draw_scissored_text(
            &active_color[channel].to_string(),
            rect.x + 158.0,
            rect.y + 260.0 + channel as f32 * 28.0,
            52.0,
            15.0,
            TEXT,
        );
        draw_editor_widget(color_channel_plus_rect(rect, channel), "+", false);
    }

    draw_editor_widget(color_add_palette_rect(rect), if app.pixel_color_add_mode { "Add Color to Palette" } else { "Add Current to Palette" }, false);
    set_default_camera();
    gl_use_default_material();
}

fn draw_color_checkerboard(rect: Rect, cell: f32) {
    let columns = (rect.w / cell).ceil() as i32;
    let rows = (rect.h / cell).ceil() as i32;
    for y in 0..rows {
        for x in 0..columns {
            let color = if (x + y) % 2 == 0 {
                editor_theme::colors::CHECKER_LIGHT
            } else {
                editor_theme::colors::CHECKER_DARK
            };
            draw_rectangle(
                rect.x + x as f32 * cell,
                rect.y + y as f32 * cell,
                cell.min(rect.x + rect.w - (rect.x + x as f32 * cell)),
                cell.min(rect.y + rect.h - (rect.y + y as f32 * cell)),
                color,
            );
        }
    }
}

fn draw_color_swatch(rect: Rect, color: [u8; 4], active: bool, label: &str) {
    draw_color_checkerboard(rect, 8.0);
    draw_rectangle(
        rect.x,
        rect.y,
        rect.w,
        rect.h,
        Color::from_rgba(color[0], color[1], color[2], color[3]),
    );
    draw_rectangle_lines(
        rect.x,
        rect.y,
        rect.w,
        rect.h,
        if active { 3.0 } else { 1.0 },
        if active { ACCENT } else { PANEL_EDGE },
    );
    draw_editor_text(label, rect.x + 5.0, rect.y + rect.h - 6.0, 14.0, TEXT);
}

pub(crate) fn update_color_from_pointer(app: &mut EditorApp, mouse: Vec2, rect: Rect) -> bool {
    let center = color_wheel_center(rect);
    let outer = color_wheel_outer_radius(rect);
    let inner = outer * 0.70;
    let delta = mouse - center;
    let distance = delta.length();
    let current = active_edit_color(app);
    let (mut hue, mut saturation, mut value) = rgba_to_hsv(current);
    if distance >= inner && distance <= outer {
        hue = delta.y.atan2(delta.x).rem_euclid(TAU) / TAU;
    } else if distance < inner {
        saturation = (distance / inner).clamp(0.0, 1.0);
    } else if color_value_rect(rect).contains(mouse) {
        let value_rect = color_value_rect(rect);
        value = 1.0 - ((mouse.y - value_rect.y) / value_rect.h).clamp(0.0, 1.0);
    } else {
        return false;
    }
    let alpha = current[3];
    let color = hsv_to_rgba(hue, saturation, value, alpha);
    set_active_edit_color(app, color);
    true
}

pub(crate) fn rgba_to_hsv(color: [u8; 4]) -> (f32, f32, f32) {
    let r = color[0] as f32 / 255.0;
    let g = color[1] as f32 / 255.0;
    let b = color[2] as f32 / 255.0;
    let max = r.max(g).max(b);
    let min = r.min(g).min(b);
    let delta = max - min;
    let hue = if delta <= f32::EPSILON {
        0.0
    } else if max == r {
        ((g - b) / delta).rem_euclid(6.0) / 6.0
    } else if max == g {
        (((b - r) / delta) + 2.0) / 6.0
    } else {
        (((r - g) / delta) + 4.0) / 6.0
    };
    let saturation = if max <= f32::EPSILON {
        0.0
    } else {
        delta / max
    };
    (hue, saturation, max)
}

fn hsv_to_color(h: f32, s: f32, v: f32, a: f32) -> Color {
    let rgba = hsv_to_rgba(h, s, v, (a * 255.0).round() as u8);
    Color::from_rgba(rgba[0], rgba[1], rgba[2], rgba[3])
}

fn hsv_to_rgba(h: f32, s: f32, v: f32, alpha: u8) -> [u8; 4] {
    let h6 = h.rem_euclid(1.0) * 6.0;
    let i = h6.floor() as i32;
    let f = h6 - i as f32;
    let p = v * (1.0 - s);
    let q = v * (1.0 - f * s);
    let t = v * (1.0 - (1.0 - f) * s);
    let (r, g, b) = match i.rem_euclid(6) {
        0 => (v, t, p),
        1 => (q, v, p),
        2 => (p, v, t),
        3 => (p, q, v),
        4 => (t, p, v),
        _ => (v, p, q),
    };
    [
        (r * 255.0).round() as u8,
        (g * 255.0).round() as u8,
        (b * 255.0).round() as u8,
        alpha,
    ]
}

pub(crate) fn pixel_color_popup_panel(app: &EditorApp) -> Rect {
    let bottom = super::shared_palette::shared_palette_rect(app);
    let colors = app.pixel_studio.active_palette();
    let visible = super::sprite_workspace::sprite_bottom_visible_color_count(
        bottom,
        colors.len().saturating_sub(app.workspace_shell.shared_palette_scroll),
    );
    let anchor = if app.pixel_color_add_mode {
        super::sprite_workspace::sprite_bottom_add_swatch_rect(bottom, visible)
    } else if app.pixel_color_edit_background {
        super::sprite_workspace::sprite_bottom_background_color_rect(bottom)
    } else {
        super::sprite_workspace::sprite_bottom_foreground_color_rect(bottom)
    };
    let width = 340.0_f32.min((screen_width() - 24.0).max(240.0));
    let height = 470.0_f32.min((screen_height() - 90.0).max(330.0));
    let x = (anchor.x + anchor.w * 0.5 - width * 0.5)
        .clamp(12.0, (screen_width() - width - 12.0).max(12.0));
    let y = (anchor.y - height - 8.0).max(48.0);
    Rect::new(x, y, width, height)
}

pub(crate) fn pixel_color_popup_content(panel: Rect) -> Rect {
    Rect::new(panel.x + 16.0, panel.y + 38.0, panel.w - 32.0, panel.h - 52.0)
}

pub(crate) fn pixel_color_popup_close_rect(panel: Rect) -> Rect {
    Rect::new(panel.x + panel.w - 32.0, panel.y + 5.0, 24.0, 24.0)
}

pub(crate) fn draw_pixel_color_popup(app: &EditorApp) {
    if !app.pixel_color_popup_open { return; }
    let panel = pixel_color_popup_panel(app);
    draw_rectangle(panel.x, panel.y, panel.w, panel.h, Color::new(0.055, 0.06, 0.075, 0.995));
    draw_rectangle_lines(panel.x, panel.y, panel.w, panel.h, 1.0, editor_theme::colors::BORDER_STRONG);
    let title = if app.pixel_color_add_mode {
        "Add Palette Color"
    } else if app.pixel_color_edit_background {
        "Background Color"
    } else {
        "Foreground Color"
    };
    draw_editor_text(title, panel.x + 12.0, panel.y + 21.0, 14.0, editor_theme::colors::TEXT_PRIMARY);
    draw_editor_widget(pixel_color_popup_close_rect(panel), "×", false);
    draw_pixel_color_panel(app, pixel_color_popup_content(panel));
}

pub(crate) fn handle_pixel_color_controls(app: &mut EditorApp, mouse: Vec2, rect: Rect) -> bool {
    if update_color_from_pointer(app, mouse, rect) { return true; }
    if color_foreground_rect(rect).contains(mouse) {
        if app.pixel_color_add_mode {
            app.pixel_color_add_mode = false;
        }
        app.pixel_color_edit_background = false;
        return true;
    }
    if color_background_rect(rect).contains(mouse) {
        if app.pixel_color_add_mode {
            app.pixel_color_add_mode = false;
        }
        app.pixel_color_edit_background = true;
        return true;
    }
    if color_swap_rect(rect).contains(mouse) {
        if !app.pixel_color_add_mode {
            std::mem::swap(&mut app.pixel_studio.selected_color, &mut app.pixel_studio.background_color);
        }
        return true;
    }
    if color_reset_rect(rect).contains(mouse) {
        if app.pixel_color_add_mode {
            app.pixel_color_draft = [0, 0, 0, 255];
        } else {
            app.pixel_studio.selected_color = [0, 0, 0, 255];
            app.pixel_studio.background_color = [255, 255, 255, 255];
        }
        return true;
    }
    for channel in 0..4 {
        if color_channel_minus_rect(rect, channel).contains(mouse) {
            let mut color = active_edit_color(app);
            color[channel] = color[channel].saturating_sub(1);
            set_active_edit_color(app, color);
            return true;
        }
        if color_channel_plus_rect(rect, channel).contains(mouse) {
            let mut color = active_edit_color(app);
            color[channel] = color[channel].saturating_add(1);
            set_active_edit_color(app, color);
            return true;
        }
    }
    if color_add_palette_rect(rect).contains(mouse) {
        let color = active_edit_color(app);
        match app.pixel_studio.add_color_to_palette(color) {
            Ok(true) => {
                app.status_message = "Added color to the active document palette".to_string();
                if app.pixel_color_add_mode {
                    app.close_pixel_color_tray();
                }
            }
            Ok(false) => app.status_message = "That color is already in the active document palette".to_string(),
            Err(error) => app.status_message = error,
        }
        return true;
    }
    false
}
