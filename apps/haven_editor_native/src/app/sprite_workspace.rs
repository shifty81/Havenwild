use super::render_helpers::*;
use super::*;

pub(crate) const SPRITE_BOTTOM_DOCK_HEIGHT: f32 = 78.0;
pub(crate) const SPRITE_SWATCH_SIZE: f32 = 24.0;
pub(crate) const SPRITE_SWATCH_GAP: f32 = 5.0;
pub(crate) const SPRITE_BOTTOM_RIGHT_RESERVE: f32 = 220.0;
pub(crate) const SPRITE_PALETTE_SCROLL_RESERVE: f32 = 62.0;

pub(crate) fn draw_sprite_toolbar_background(rect: Rect) {
    draw_rectangle(
        rect.x,
        rect.y,
        rect.w,
        rect.h,
        editor_theme::colors::PANEL_RAISED,
    );
    draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 1.0, PANEL_EDGE);
}

pub(crate) fn draw_sprite_toolbar_separator(x: f32, rect: Rect) {
    draw_line(x, rect.y + 6.0, x, rect.y + rect.h - 6.0, 1.0, PANEL_EDGE);
}

pub(crate) fn draw_sprite_panel(rect: Rect, title: &str, context: Option<&str>) {
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, PANEL_BG);
    draw_rectangle(
        rect.x,
        rect.y,
        rect.w,
        30.0,
        editor_theme::colors::PANEL_RAISED,
    );
    draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 1.0, PANEL_EDGE);
    draw_editor_text(title, rect.x + 10.0, rect.y + 21.0, 15.0, TEXT);
    if let Some(context) = context {
        let measured = measure_editor_text(context, None, 12, 1.0).width;
        draw_scissored_text(
            context,
            (rect.x + rect.w - measured - 10.0).max(rect.x + 92.0),
            rect.y + 20.0,
            (rect.w - 104.0).max(24.0),
            12.0,
            MUTED,
        );
    }
    draw_line(
        rect.x,
        rect.y + 30.0,
        rect.x + rect.w,
        rect.y + 30.0,
        1.0,
        PANEL_EDGE,
    );
}

pub(crate) fn draw_sprite_bottom_dock(
    rect: Rect,
    active_tab: &str,
    secondary_tab: &str,
    colors: &[[u8; 4]],
    foreground: [u8; 4],
    background: [u8; 4],
    scroll_offset: usize,
) {
    draw_sprite_panel(rect, active_tab, Some(secondary_tab));
    let y = rect.y + 38.0;
    let palette_width = (rect.w - SPRITE_BOTTOM_RIGHT_RESERVE).max(86.0);
    let available = (palette_width - 20.0 - SPRITE_PALETTE_SCROLL_RESERVE).max(0.0);
    let swatch = SPRITE_SWATCH_SIZE;
    let gap = SPRITE_SWATCH_GAP;
    let slots = ((available + gap) / (swatch + gap)).floor().max(0.0) as usize;
    let visible = colors.len().saturating_sub(scroll_offset).min(slots.saturating_sub(1));
    for (visual_index, rgba) in colors.iter().skip(scroll_offset).take(visible).enumerate() {
        let swatch_rect = sprite_bottom_swatch_rect(rect, visual_index);
        let x = swatch_rect.x;
        let color = Color::new(
            rgba[0] as f32 / 255.0,
            rgba[1] as f32 / 255.0,
            rgba[2] as f32 / 255.0,
            rgba[3] as f32 / 255.0,
        );
        if rgba[3] < 255 {
            draw_sprite_checkerboard(Rect::new(x, y, swatch, swatch), 6.0);
        }
        draw_rectangle(x, y, swatch, swatch, color);
        let is_foreground = *rgba == foreground;
        let is_background = *rgba == background;
        draw_rectangle_lines(
            x - if is_foreground || is_background { 2.0 } else { 0.0 },
            y - if is_foreground || is_background { 2.0 } else { 0.0 },
            swatch + if is_foreground || is_background { 4.0 } else { 0.0 },
            swatch + if is_foreground || is_background { 4.0 } else { 0.0 },
            if is_foreground || is_background { 2.0 } else { 1.0 },
            if is_foreground { ACCENT } else if is_background { WARN } else { PANEL_EDGE },
        );
    }
    if slots > 0 {
        let add = sprite_bottom_add_swatch_rect(rect, visible);
        draw_rectangle(add.x, add.y, add.w, add.h, editor_theme::colors::PANEL_RAISED);
        draw_rectangle_lines(add.x, add.y, add.w, add.h, 1.0, ACCENT);
        draw_editor_text("+", add.x + 7.0, add.y + 19.0, 20.0, TEXT);
    }
    draw_editor_widget_tone(sprite_bottom_scroll_left_rect(rect), "‹", false, if scroll_offset > 0 { WidgetTone::Quiet } else { WidgetTone::Disabled });
    draw_editor_widget_tone(
        sprite_bottom_scroll_right_rect(rect),
        "›",
        false,
        if scroll_offset + visible < colors.len() { WidgetTone::Quiet } else { WidgetTone::Disabled },
    );
    let separator_x = rect.x + rect.w - SPRITE_BOTTOM_RIGHT_RESERVE;
    draw_line(separator_x, rect.y + 34.0, separator_x, rect.y + rect.h - 6.0, 1.0, editor_theme::colors::BORDER_STRONG);

    // Foreground/background are first-class mouse-button colors and live beside
    // the bottom palette instead of occupying the right Inspector.
    let bg = sprite_bottom_background_color_rect(rect);
    let fg = sprite_bottom_foreground_color_rect(rect);
    draw_sprite_checkerboard(bg, 6.0);
    draw_rectangle(bg.x, bg.y, bg.w, bg.h, rgba_color(background));
    draw_rectangle_lines(bg.x, bg.y, bg.w, bg.h, 2.0, WARN);
    draw_sprite_checkerboard(fg, 6.0);
    draw_rectangle(fg.x, fg.y, fg.w, fg.h, rgba_color(foreground));
    draw_rectangle_lines(fg.x, fg.y, fg.w, fg.h, 2.0, ACCENT);
    draw_editor_text("FG", fg.x + 5.0, fg.y - 4.0, 9.0, TEXT);
    draw_editor_text("BG", bg.x + 5.0, bg.y - 4.0, 9.0, MUTED);
}

fn rgba_color(rgba: [u8; 4]) -> Color {
    Color::new(
        rgba[0] as f32 / 255.0,
        rgba[1] as f32 / 255.0,
        rgba[2] as f32 / 255.0,
        rgba[3] as f32 / 255.0,
    )
}

fn draw_sprite_checkerboard(rect: Rect, cell: f32) {
    let cols = (rect.w / cell).ceil() as usize;
    let rows = (rect.h / cell).ceil() as usize;
    for row in 0..rows {
        for col in 0..cols {
            let x = rect.x + col as f32 * cell;
            let y = rect.y + row as f32 * cell;
            let w = cell.min(rect.x + rect.w - x);
            let h = cell.min(rect.y + rect.h - y);
            let color = if (row + col) % 2 == 0 {
                editor_theme::colors::CHECKER_LIGHT
            } else {
                editor_theme::colors::CHECKER_DARK
            };
            draw_rectangle(x, y, w, h, color);
        }
    }
}

pub(crate) fn sprite_bottom_swatch_rect(rect: Rect, index: usize) -> Rect {
    Rect::new(
        rect.x + 10.0 + index as f32 * (SPRITE_SWATCH_SIZE + SPRITE_SWATCH_GAP),
        rect.y + 38.0,
        SPRITE_SWATCH_SIZE,
        SPRITE_SWATCH_SIZE,
    )
}

pub(crate) fn sprite_bottom_visible_color_count(rect: Rect, color_count: usize) -> usize {
    let palette_width = (rect.w - SPRITE_BOTTOM_RIGHT_RESERVE).max(86.0);
    let available = (palette_width - 20.0 - SPRITE_PALETTE_SCROLL_RESERVE).max(0.0);
    let slots = ((available + SPRITE_SWATCH_GAP)
        / (SPRITE_SWATCH_SIZE + SPRITE_SWATCH_GAP))
        .floor()
        .max(0.0) as usize;
    color_count.min(slots.saturating_sub(1))
}

/// `visible_count` is the number of visible swatches, not the total palette length.
pub(crate) fn sprite_bottom_add_swatch_rect(rect: Rect, visible_count: usize) -> Rect {
    sprite_bottom_swatch_rect(rect, visible_count)
}

pub(crate) fn sprite_bottom_scroll_left_rect(rect: Rect) -> Rect {
    let separator = rect.x + rect.w - SPRITE_BOTTOM_RIGHT_RESERVE;
    Rect::new(separator - 58.0, rect.y + 40.0, 26.0, 28.0)
}

pub(crate) fn sprite_bottom_scroll_right_rect(rect: Rect) -> Rect {
    let separator = rect.x + rect.w - SPRITE_BOTTOM_RIGHT_RESERVE;
    Rect::new(separator - 28.0, rect.y + 40.0, 26.0, 28.0)
}

pub(crate) fn sprite_bottom_foreground_color_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + rect.w - 204.0, rect.y + 40.0, 30.0, 30.0)
}

pub(crate) fn sprite_bottom_background_color_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + rect.w - 168.0, rect.y + 40.0, 30.0, 30.0)
}

pub(crate) fn sprite_bottom_swap_color_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + rect.w - 132.0, rect.y + 40.0, 58.0, 28.0)
}

pub(crate) fn sprite_bottom_reset_color_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + rect.w - 68.0, rect.y + 40.0, 60.0, 28.0)
}

#[cfg(test)]
mod w76_palette_geometry_tests {
    use super::*;

    fn overlaps(a: Rect, b: Rect) -> bool {
        a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y
    }

    #[test]
    fn palette_swatches_never_enter_fixed_fg_bg_swap_reset_cluster() {
        for width in [320.0, 640.0, 1280.0] {
            let rect = Rect::new(0.0, 0.0, width, SPRITE_BOTTOM_DOCK_HEIGHT);
            let visible = sprite_bottom_visible_color_count(rect, 128);
            let fixed = [
                sprite_bottom_foreground_color_rect(rect),
                sprite_bottom_background_color_rect(rect),
                sprite_bottom_swap_color_rect(rect),
                sprite_bottom_reset_color_rect(rect),
            ];
            for index in 0..=visible {
                let swatch = sprite_bottom_swatch_rect(rect, index);
                assert!(fixed.iter().all(|control| !overlaps(swatch, *control)));
            }
        }
    }
}
