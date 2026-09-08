//! Shared production runtime UI vocabulary for the player-facing game shell.
//!
//! The title/main-menu artwork keeps its own established frontend authority.
//! Everything after entering the game uses this compact wood/brass/parchment
//! vocabulary so HUD, inventory, crafting, map and pause surfaces no longer
//! drift into separate prototype palettes.

use macroquad::prelude::*;

pub(crate) fn ui_backdrop() -> Color { Color::from_rgba(5, 10, 12, 214) }
pub(crate) fn ui_panel_fill() -> Color { Color::from_rgba(25, 25, 22, 248) }
pub(crate) fn ui_panel_inner() -> Color { Color::from_rgba(38, 35, 28, 246) }
pub(crate) fn ui_slot_fill() -> Color { Color::from_rgba(45, 43, 35, 248) }
pub(crate) fn ui_slot_hover() -> Color { Color::from_rgba(59, 58, 46, 250) }
pub(crate) fn ui_brass() -> Color { Color::from_rgba(196, 157, 80, 255) }
pub(crate) fn ui_brass_bright() -> Color { Color::from_rgba(238, 207, 119, 255) }
pub(crate) fn ui_parchment() -> Color { Color::from_rgba(238, 229, 197, 255) }
pub(crate) fn ui_muted() -> Color { Color::from_rgba(164, 171, 157, 255) }
pub(crate) fn ui_teal() -> Color { Color::from_rgba(116, 157, 151, 255) }
pub(crate) fn ui_good() -> Color { Color::from_rgba(165, 196, 137, 255) }
pub(crate) fn ui_bad() -> Color { Color::from_rgba(207, 132, 117, 255) }

pub(crate) fn draw_runtime_panel(rect: Rect, title: &str, subtitle: Option<&str>) {
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, ui_panel_fill());
    draw_rectangle(rect.x + 4.0, rect.y + 4.0, rect.w - 8.0, 3.0, ui_brass());
    draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 2.0, ui_brass());
    draw_rectangle_lines(
        rect.x + 5.0,
        rect.y + 5.0,
        (rect.w - 10.0).max(0.0),
        (rect.h - 10.0).max(0.0),
        1.0,
        Color::from_rgba(83, 99, 86, 180),
    );
    draw_text(title, rect.x + 18.0, rect.y + 31.0, 23.0, ui_parchment());
    if let Some(subtitle) = subtitle {
        draw_text(
            &fit_runtime_label(subtitle, (rect.w - 36.0).max(40.0), 13),
            rect.x + 18.0,
            rect.y + 52.0,
            13.0,
            ui_muted(),
        );
    }
}

pub(crate) fn draw_runtime_section(rect: Rect, title: &str) {
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, ui_panel_inner());
    draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 1.0, Color::from_rgba(100, 91, 65, 230));
    draw_text(title, rect.x + 10.0, rect.y + 21.0, 16.0, ui_brass_bright());
    draw_line(rect.x + 10.0, rect.y + 28.0, rect.x + rect.w - 10.0, rect.y + 28.0, 1.0, Color::from_rgba(111, 92, 57, 190));
}

pub(crate) fn draw_runtime_slot(rect: Rect, selected: bool, available: bool) {
    let mouse = vec2(mouse_position().0, mouse_position().1);
    let hovered = rect.contains(mouse);
    draw_rectangle(
        rect.x,
        rect.y,
        rect.w,
        rect.h,
        if hovered { ui_slot_hover() } else { ui_slot_fill() },
    );
    let border = if selected {
        ui_brass_bright()
    } else if available {
        Color::from_rgba(126, 131, 96, 235)
    } else {
        Color::from_rgba(102, 79, 67, 220)
    };
    draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, if selected { 2.0 } else { 1.0 }, border);
}

pub(crate) fn draw_runtime_progress(rect: Rect, progress: f32, fill: Color) {
    let progress = progress.clamp(0.0, 1.0);
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, Color::from_rgba(9, 14, 14, 235));
    if progress > 0.0 {
        draw_rectangle(rect.x + 1.0, rect.y + 1.0, (rect.w - 2.0) * progress, (rect.h - 2.0).max(0.0), fill);
    }
    draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 1.0, Color::from_rgba(92, 105, 91, 230));
}

pub(crate) fn draw_runtime_key_hint(x: f32, y: f32, key: &str, label: &str) -> f32 {
    let key_w = measure_text(key, None, 12, 1.0).width + 14.0;
    let label_w = measure_text(label, None, 12, 1.0).width;
    let h = 22.0;
    draw_rectangle(x, y, key_w, h, Color::from_rgba(45, 49, 42, 250));
    draw_rectangle_lines(x, y, key_w, h, 1.0, ui_brass());
    draw_text(key, x + 7.0, y + 15.0, 12.0, ui_parchment());
    draw_text(label, x + key_w + 6.0, y + 15.0, 12.0, ui_muted());
    key_w + 6.0 + label_w + 16.0
}

pub(crate) fn fit_runtime_label(text: &str, max_width: f32, font_size: u16) -> String {
    if measure_text(text, None, font_size, 1.0).width <= max_width {
        return text.to_string();
    }
    let ellipsis = "…";
    let ellipsis_w = measure_text(ellipsis, None, font_size, 1.0).width;
    let mut candidate = String::new();
    for ch in text.chars() {
        candidate.push(ch);
        if measure_text(&candidate, None, font_size, 1.0).width + ellipsis_w > max_width {
            candidate.pop();
            break;
        }
    }
    candidate.push_str(ellipsis);
    candidate
}
