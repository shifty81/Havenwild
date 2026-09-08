use super::render_helpers::*;
use super::sprite_canvas_authority::*;
use super::*;

pub(crate) fn draw_selection_outline(
    selection: haven_pixel::PixelSelection,
    transform: SpriteCanvasTransform,
    color: Color,
) {
    if selection.is_empty() {
        return;
    }
    let rect = transform.pixel_rect_to_screen(Rect::new(
        selection.x as f32,
        selection.y as f32,
        selection.width as f32,
        selection.height as f32,
    ));
    if let Some(clipped) = intersect_rect(rect, transform.canvas) {
        let width = SpriteOverlayKind::Selection.style().line_width;
        draw_marquee_rect(clipped, width, color);
    }
}

fn draw_marquee_rect(rect: Rect, width: f32, color: Color) {
    let dash = 6.0;
    let gap = 4.0;
    let mut x = rect.x;
    while x < rect.x + rect.w {
        let end = (x + dash).min(rect.x + rect.w);
        draw_line(x, rect.y, end, rect.y, width, color);
        draw_line(x, rect.y + rect.h, end, rect.y + rect.h, width, color);
        x += dash + gap;
    }
    let mut y = rect.y;
    while y < rect.y + rect.h {
        let end = (y + dash).min(rect.y + rect.h);
        draw_line(rect.x, y, rect.x, end, width, color);
        draw_line(rect.x + rect.w, y, rect.x + rect.w, end, width, color);
        y += dash + gap;
    }
}

pub(crate) fn intersect_rect(left: Rect, right: Rect) -> Option<Rect> {
    let x = left.x.max(right.x);
    let y = left.y.max(right.y);
    let right_edge = (left.x + left.w).min(right.x + right.w);
    let bottom_edge = (left.y + left.h).min(right.y + right.h);
    (right_edge > x && bottom_edge > y).then_some(Rect::new(x, y, right_edge - x, bottom_edge - y))
}

pub(crate) fn draw_value_stepper(rect: Rect, y: f32, label: &str, value: i32, row: usize) {
    draw_editor_text(label, rect.x, y + 20.0, 15.0, TEXT);
    draw_editor_widget(pixel_value_minus_rect(rect, row), "-", false);
    draw_editor_widget(pixel_value_plus_rect(rect, row), "+", false);
    draw_scissored_text(
        &value.to_string(),
        rect.x + 178.0,
        y + 20.0,
        48.0,
        15.0,
        TEXT,
    );
}

pub(crate) fn pixel_refresh_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + 34.0, 104.0, 30.0)
}
pub(crate) fn pixel_library_search_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + 70.0, (rect.w - 30.0).max(40.0), 24.0)
}

pub(crate) fn pixel_library_clear_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + rect.w - 24.0, rect.y + 70.0, 24.0, 24.0)
}

pub(crate) fn pixel_library_category_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + 100.0, rect.w, 26.0)
}

pub(crate) fn pixel_library_grid_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + 132.0, rect.w, (rect.h - 136.0).max(64.0))
}

pub(crate) fn pixel_document_tabs_area_rect(bar: Rect) -> Rect {
    Rect::new(bar.x, bar.y, (bar.w - 190.0).max(96.0), bar.h)
}

pub(crate) fn pixel_document_tab_rect(bar: Rect, index: usize, count: usize) -> Rect {
    let bar = pixel_document_tabs_area_rect(bar);
    let gap = 3.0;
    let max_width = 168.0;
    let min_width = 84.0;
    let available = (bar.w - gap * count.saturating_sub(1) as f32).max(min_width);
    let width = if count == 0 { min_width } else { (available / count as f32).clamp(min_width, max_width) };
    Rect::new(bar.x + index as f32 * (width + gap), bar.y, width, bar.h)
}


pub(crate) fn pixel_document_tab_close_rect(tab: Rect) -> Rect {
    Rect::new(tab.x + tab.w - 22.0, tab.y, 22.0, tab.h)
}

pub(crate) fn pixel_document_new_rect(bar: Rect) -> Rect {
    Rect::new(bar.x + bar.w - 186.0, bar.y, 28.0, bar.h)
}

pub(crate) fn pixel_document_split_rect(bar: Rect, mode: DocumentSplitMode) -> Rect {
    let index = match mode {
        DocumentSplitMode::Single => 0,
        DocumentSplitMode::Vertical => 1,
        DocumentSplitMode::Horizontal => 2,
    };
    Rect::new(bar.x + bar.w - 152.0 + index as f32 * 50.0, bar.y, 46.0, bar.h)
}

pub(crate) fn pixel_selection_mode_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + 4.0, rect.y + 2.0, 72.0, 24.0)
}
pub(crate) fn pixel_grid_toggle_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + 232.0, 136.0, 30.0)
}
pub(crate) fn pixel_realign_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + 144.0, rect.y + 232.0, 142.0, 30.0)
}
pub(crate) fn pixel_value_minus_rect(rect: Rect, row: usize) -> Rect {
    Rect::new(
        rect.x + 132.0,
        rect.y + 270.0 + row as f32 * 34.0,
        34.0,
        28.0,
    )
}
pub(crate) fn pixel_value_plus_rect(rect: Rect, row: usize) -> Rect {
    Rect::new(
        rect.x + 232.0,
        rect.y + 270.0 + row as f32 * 34.0,
        34.0,
        28.0,
    )
}
pub(crate) fn pixel_flip_h_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + 570.0, 136.0, 30.0)
}
pub(crate) fn pixel_flip_v_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + 144.0, rect.y + 570.0, 142.0, 30.0)
}
pub(crate) fn pixel_pivot_bottom_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + 606.0, 136.0, 30.0)
}
pub(crate) fn pixel_fit_visual_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + 144.0, rect.y + 606.0, 142.0, 30.0)
}
pub(crate) fn pixel_target_kind_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + 674.0, 78.0, 30.0)
}
pub(crate) fn pixel_target_prev_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + 84.0, rect.y + 674.0, 34.0, 30.0)
}
pub(crate) fn pixel_target_next_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + rect.w - 34.0, rect.y + 674.0, 34.0, 30.0)
}
pub(crate) fn pixel_save_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + 714.0, 136.0, 32.0)
}
pub(crate) fn pixel_publish_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + 144.0, rect.y + 714.0, 142.0, 32.0)
}
