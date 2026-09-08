use super::*;

fn pixel_context_tabs_y(rect: Rect) -> f32 {
    rect.y + 34.0
}

pub(crate) fn pixel_asset_tab_rect(rect: Rect) -> Rect {
    let width = (rect.w - 12.0) / 3.0;
    Rect::new(rect.x, pixel_context_tabs_y(rect), width, 30.0)
}

pub(crate) fn pixel_animation_tab_rect(rect: Rect) -> Rect {
    let width = (rect.w - 12.0) / 3.0;
    Rect::new(rect.x + width + 6.0, pixel_context_tabs_y(rect), width, 30.0)
}

pub(crate) fn pixel_animation_onion_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + 228.0, 136.0, 30.0)
}

pub(crate) fn pixel_animation_focus_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + 144.0, rect.y + 228.0, 142.0, 30.0)
}

pub(crate) fn pixel_animation_save_return_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + 284.0, 286.0, 34.0)
}

pub(crate) fn pixel_animation_cancel_return_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + 324.0, 286.0, 34.0)
}
