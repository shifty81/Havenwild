use super::render_helpers::restore_editor_ui_render_state;
use super::editor_text::{draw_editor_text, measure_editor_text};
use super::*;

pub(crate) const BROWSER_CARD_H: f32 = 104.0;
pub(crate) const BROWSER_GAP: f32 = 6.0;

pub(crate) fn browser_columns(width: f32) -> usize {
    if width >= 430.0 { 4 } else if width >= 320.0 { 3 } else if width >= 205.0 { 2 } else { 1 }
}


pub(crate) fn fit_preview_rect(source_w: f32, source_h: f32, bounds: Rect) -> Rect {
    let source_w = source_w.max(1.0);
    let source_h = source_h.max(1.0);
    let inner = Rect::new(
        bounds.x + 4.0,
        bounds.y + 4.0,
        (bounds.w - 8.0).max(1.0),
        (bounds.h - 8.0).max(1.0),
    );
    let scale = (inner.w / source_w).min(inner.h / source_h);
    let w = (source_w * scale).max(1.0);
    let h = (source_h * scale).max(1.0);
    Rect::new(
        inner.x + (inner.w - w) * 0.5,
        inner.y + (inner.h - h) * 0.5,
        w,
        h,
    )
}

pub(crate) fn browser_card_width(width: f32, columns: usize) -> f32 {
    let gaps = BROWSER_GAP * columns.saturating_sub(1) as f32;
    ((width - gaps) / columns.max(1) as f32).max(72.0)
}

pub(crate) fn browser_card_rect(area: Rect, slot: usize) -> Rect {
    let columns = browser_columns(area.w);
    let width = browser_card_width(area.w, columns);
    let column = slot % columns;
    let row = slot / columns;
    Rect::new(
        area.x + column as f32 * (width + BROWSER_GAP),
        area.y + row as f32 * (BROWSER_CARD_H + BROWSER_GAP),
        width,
        BROWSER_CARD_H,
    )
}

pub(crate) fn browser_visible_capacity(area: Rect) -> usize {
    let columns = browser_columns(area.w);
    let rows = ((area.h + BROWSER_GAP) / (BROWSER_CARD_H + BROWSER_GAP)).floor().max(1.0) as usize;
    columns * rows
}

pub(crate) fn browser_thumbnail_rect(card: Rect) -> Rect {
    Rect::new(card.x + 5.0, card.y + 5.0, card.w - 10.0, (card.h - 38.0).max(42.0))
}

pub(crate) fn draw_browser_card_surface(card: Rect, selected: bool) {
    let background = if selected {
        Color::new(0.11, 0.24, 0.36, 1.0)
    } else {
        editor_theme::colors::CONTROL_BG
    };
    draw_rectangle(card.x, card.y, card.w, card.h, background);
    draw_rectangle_lines(
        card.x,
        card.y,
        card.w,
        card.h,
        if selected { 2.0 } else { 1.0 },
        if selected { editor_theme::colors::ACCENT } else { editor_theme::colors::BORDER_SUBTLE },
    );
}

pub(crate) fn draw_browser_card_labels(card: Rect, title: &str, subtitle: Option<&str>) {
    // Labels are deliberately drawn after any thumbnail texture. This makes the
    // font atlas the final texture/material owner for each card and closes a
    // long-standing Macroquad batching edge case where browser image sampling
    // could contaminate queued UI glyphs.
    restore_editor_ui_render_state();
    let label_y = card.y + card.h - 23.0;
    draw_scissored_text(title, card.x + 6.0, label_y, (card.w - 12.0).max(1.0), 12.5, editor_theme::colors::TEXT_PRIMARY);
    if let Some(subtitle) = subtitle {
        draw_scissored_text(subtitle, card.x + 6.0, card.y + card.h - 7.0, (card.w - 12.0).max(1.0), 9.5, editor_theme::colors::TEXT_SECONDARY);
    }
}

pub(crate) fn draw_browser_texture(texture: &Texture2D, rect: Rect) {
    // Browser cards are UI, never canvas render state. Keep texture previews
    // fenced from the dedicated editor font atlas/material lifetime.
    restore_editor_ui_render_state();
    let tw = texture.width().max(1.0);
    let th = texture.height().max(1.0);
    let scale = (rect.w / tw).min(rect.h / th);
    let size = vec2(tw * scale, th * scale);
    draw_texture_ex(
        texture,
        rect.x + (rect.w - size.x) * 0.5,
        rect.y + (rect.h - size.y) * 0.5,
        WHITE,
        DrawTextureParams { dest_size: Some(size), ..Default::default() },
    );
    restore_editor_ui_render_state();
}

pub(crate) fn draw_thumbnail_placeholder(rect: Rect, label: &str) {
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, editor_theme::colors::CANVAS_SURROUND);
    draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 1.0, editor_theme::colors::BORDER_SUBTLE);
    let short = label.chars().next().map(|c| c.to_ascii_uppercase().to_string()).unwrap_or_else(|| "?".to_string());
    let size = 18.0;
    let width = measure_editor_text(&short, None, size as u16, 1.0).width;
    draw_editor_text(&short, rect.x + (rect.w - width) * 0.5, rect.y + rect.h * 0.5 + size * 0.35, size, editor_theme::colors::TEXT_SECONDARY);
}

pub(crate) fn draw_browser_checkerboard(rect: Rect, cell: f32) {
    let cell = cell.max(2.0);
    let columns = (rect.w / cell).ceil().max(1.0) as i32;
    let rows = (rect.h / cell).ceil().max(1.0) as i32;
    for row in 0..rows {
        for column in 0..columns {
            let color = if (row + column) % 2 == 0 {
                Color::new(0.16, 0.17, 0.19, 1.0)
            } else {
                Color::new(0.11, 0.12, 0.14, 1.0)
            };
            draw_rectangle(
                rect.x + column as f32 * cell,
                rect.y + row as f32 * cell,
                cell.min(rect.x + rect.w - (rect.x + column as f32 * cell)).max(0.0),
                cell.min(rect.y + rect.h - (rect.y + row as f32 * cell)).max(0.0),
                color,
            );
        }
    }
}


#[cfg(test)]
mod a14z_preview_fit_tests {
    use super::*;

    #[test]
    fn square_atlas_cell_stays_square_in_wide_palette_card() {
        let fitted = fit_preview_rect(32.0, 32.0, Rect::new(0.0, 0.0, 300.0, 70.0));
        assert!((fitted.w - fitted.h).abs() < 0.001);
        assert!(fitted.w <= 62.1);
        assert!(fitted.x > 100.0);
    }

    #[test]
    fn wide_atlas_slice_preserves_source_aspect_ratio() {
        let fitted = fit_preview_rect(96.0, 32.0, Rect::new(0.0, 0.0, 220.0, 80.0));
        assert!(((fitted.w / fitted.h) - 3.0).abs() < 0.001);
        assert!(fitted.w <= 212.1);
        assert!(fitted.h <= 72.1);
    }
}
