use super::sprite_canvas_authority::SpriteCanvasTransform;
use super::*;
use haven_pixel::PixelSelection;

const HANDLE_SIZE: f32 = 8.0;
const ROTATE_OFFSET: f32 = 15.0;
const PIVOT_RADIUS: f32 = 6.0;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum TransformGizmoHandle {
    Move,
    Left,
    Right,
    Top,
    Bottom,
    TopLeft,
    TopRight,
    BottomLeft,
    BottomRight,
    RotateTopLeft,
    RotateTopRight,
    RotateBottomLeft,
    RotateBottomRight,
    Pivot,
}

impl TransformGizmoHandle {
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Move => "Move",
            Self::Left | Self::Right | Self::Top | Self::Bottom => "Stretch",
            Self::TopLeft | Self::TopRight | Self::BottomLeft | Self::BottomRight => "Scale",
            Self::RotateTopLeft
            | Self::RotateTopRight
            | Self::RotateBottomLeft
            | Self::RotateBottomRight => "Rotate",
            Self::Pivot => "Pivot",
        }
    }

    fn is_rotation(self) -> bool {
        matches!(
            self,
            Self::RotateTopLeft
                | Self::RotateTopRight
                | Self::RotateBottomLeft
                | Self::RotateBottomRight
        )
    }
}

#[derive(Clone, Copy, Debug)]
pub(crate) struct TransformGizmoDrag {
    pub handle: TransformGizmoHandle,
    pub start_mouse: Vec2,
    pub start_selection: PixelSelection,
    pub preview_selection: PixelSelection,
    pub start_pivot: [f32; 2],
    pub preview_pivot: [f32; 2],
    pub pivot_screen: Vec2,
    pub preview_rotation_degrees: f32,
}

pub(crate) fn selection_screen_rect(
    selection: PixelSelection,
    transform: SpriteCanvasTransform,
) -> Rect {
    transform.pixel_rect_to_screen(Rect::new(
        selection.x as f32,
        selection.y as f32,
        selection.width as f32,
        selection.height as f32,
    ))
}

pub(crate) fn pivot_screen_point(
    pivot: [f32; 2],
    transform: SpriteCanvasTransform,
) -> Vec2 {
    vec2(
        transform.image.x + pivot[0] * transform.zoom,
        transform.image.y + pivot[1] * transform.zoom,
    )
}

pub(crate) fn hit_test_transform_gizmo(
    bounds: Rect,
    pivot: Vec2,
    point: Vec2,
) -> Option<TransformGizmoHandle> {
    if point.distance(pivot) <= PIVOT_RADIUS + 3.0 {
        return Some(TransformGizmoHandle::Pivot);
    }
    for (handle, rect) in handle_rects(bounds) {
        if rect.contains(point) {
            return Some(handle);
        }
    }
    for (handle, center) in rotation_centers(bounds) {
        if point.distance(center) <= HANDLE_SIZE + 3.0 {
            return Some(handle);
        }
    }
    if bounds.contains(point) {
        return Some(TransformGizmoHandle::Move);
    }
    None
}

pub(crate) fn begin_pixel_transform_drag(
    selection: PixelSelection,
    pivot_document: [f32; 2],
    transform: SpriteCanvasTransform,
    point: Vec2,
) -> Option<TransformGizmoDrag> {
    if !transform.canvas.contains(point) {
        return None;
    }
    let bounds = selection_screen_rect(selection, transform);
    let pivot_screen = pivot_screen_point(pivot_document, transform);
    let handle = hit_test_transform_gizmo(bounds, pivot_screen, point)?;
    Some(TransformGizmoDrag {
        handle,
        start_mouse: point,
        start_selection: selection,
        preview_selection: selection,
        start_pivot: pivot_document,
        preview_pivot: pivot_document,
        pivot_screen,
        preview_rotation_degrees: 0.0,
    })
}

pub(crate) fn update_pixel_transform_drag(
    drag: &mut TransformGizmoDrag,
    point: Vec2,
    zoom: f32,
    document_size: [u32; 2],
    preserve_aspect: bool,
) {
    let zoom = zoom.max(0.001);
    if drag.handle == TransformGizmoHandle::Pivot {
        let delta = (point - drag.start_mouse) / zoom;
        drag.preview_pivot = [drag.start_pivot[0] + delta.x, drag.start_pivot[1] + delta.y];
        drag.preview_pivot[0] = drag.preview_pivot[0].clamp(0.0, document_size[0].saturating_sub(1) as f32);
        drag.preview_pivot[1] = drag.preview_pivot[1].clamp(0.0, document_size[1].saturating_sub(1) as f32);
        return;
    }
    if drag.handle.is_rotation() {
        let start = drag.start_mouse - drag.pivot_screen;
        let current = point - drag.pivot_screen;
        if start.length_squared() > 0.001 && current.length_squared() > 0.001 {
            let start_angle = start.y.atan2(start.x).to_degrees();
            let current_angle = current.y.atan2(current.x).to_degrees();
            let mut delta = current_angle - start_angle;
            while delta > 180.0 {
                delta -= 360.0;
            }
            while delta < -180.0 {
                delta += 360.0;
            }
            drag.preview_rotation_degrees = delta;
        }
        return;
    }

    let delta = (point - drag.start_mouse) / zoom;
    let dx = delta.x.round() as i32;
    let dy = delta.y.round() as i32;
    let source = drag.start_selection;
    let mut left = source.x as i32;
    let mut top = source.y as i32;
    let mut right = source.x as i32 + source.width as i32;
    let mut bottom = source.y as i32 + source.height as i32;
    match drag.handle {
        TransformGizmoHandle::Move => {
            left += dx;
            right += dx;
            top += dy;
            bottom += dy;
        }
        TransformGizmoHandle::Left => left += dx,
        TransformGizmoHandle::Right => right += dx,
        TransformGizmoHandle::Top => top += dy,
        TransformGizmoHandle::Bottom => bottom += dy,
        TransformGizmoHandle::TopLeft => {
            left += dx;
            top += dy;
        }
        TransformGizmoHandle::TopRight => {
            right += dx;
            top += dy;
        }
        TransformGizmoHandle::BottomLeft => {
            left += dx;
            bottom += dy;
        }
        TransformGizmoHandle::BottomRight => {
            right += dx;
            bottom += dy;
        }
        _ => {}
    }

    if preserve_aspect && matches!(drag.handle, TransformGizmoHandle::TopLeft | TransformGizmoHandle::TopRight | TransformGizmoHandle::BottomLeft | TransformGizmoHandle::BottomRight) {
        let aspect = source.width as f32 / source.height.max(1) as f32;
        let width = (right - left).abs().max(1) as f32;
        let height = (bottom - top).abs().max(1) as f32;
        if width / height > aspect {
            let desired_height = (width / aspect).round() as i32;
            if matches!(drag.handle, TransformGizmoHandle::TopLeft | TransformGizmoHandle::TopRight) {
                top = bottom - desired_height;
            } else {
                bottom = top + desired_height;
            }
        } else {
            let desired_width = (height * aspect).round() as i32;
            if matches!(drag.handle, TransformGizmoHandle::TopLeft | TransformGizmoHandle::BottomLeft) {
                left = right - desired_width;
            } else {
                right = left + desired_width;
            }
        }
    }

    if left > right {
        std::mem::swap(&mut left, &mut right);
    }
    if top > bottom {
        std::mem::swap(&mut top, &mut bottom);
    }
    let width = (right - left).max(1);
    let height = (bottom - top).max(1);
    let max_x = document_size[0].saturating_sub(1) as i32;
    let max_y = document_size[1].saturating_sub(1) as i32;
    left = left.clamp(0, max_x);
    top = top.clamp(0, max_y);
    let width = width.min(document_size[0].saturating_sub(left as u32) as i32).max(1);
    let height = height.min(document_size[1].saturating_sub(top as u32) as i32).max(1);
    drag.preview_selection = PixelSelection {
        x: left as u32,
        y: top as u32,
        width: width as u32,
        height: height as u32,
    };
}

pub(crate) fn draw_transform_gizmo(bounds: Rect, pivot: Vec2, active: bool, clip: Rect) {
    let line_color = if active { editor_theme::colors::ACCENT_HOVER } else { editor_theme::colors::ACCENT };
    if let Some(rect) = clipped_rect(bounds, clip) {
        draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 1.5, line_color);
    }
    for (_handle, rect) in handle_rects(bounds) {
        if let Some(rect) = clipped_rect(rect, clip) {
            draw_rectangle(rect.x, rect.y, rect.w, rect.h, editor_theme::colors::PANEL_RAISED);
            draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 1.0, line_color);
        }
    }
    for (_handle, center) in rotation_centers(bounds) {
        if clip.contains(center) {
            draw_circle_lines(center.x, center.y, HANDLE_SIZE * 0.72, 1.25, line_color);
        }
    }
    if clip.contains(pivot) {
        draw_circle(pivot.x, pivot.y, PIVOT_RADIUS, editor_theme::colors::PANEL_RAISED);
        draw_circle_lines(pivot.x, pivot.y, PIVOT_RADIUS, 1.5, editor_theme::colors::WARN);
        draw_line((pivot.x - 8.0).max(clip.x), pivot.y, (pivot.x + 8.0).min(clip.x + clip.w), pivot.y, 1.0, editor_theme::colors::WARN);
        draw_line(pivot.x, (pivot.y - 8.0).max(clip.y), pivot.x, (pivot.y + 8.0).min(clip.y + clip.h), 1.0, editor_theme::colors::WARN);
    }
}

fn clipped_rect(left: Rect, right: Rect) -> Option<Rect> {
    let x = left.x.max(right.x);
    let y = left.y.max(right.y);
    let edge_x = (left.x + left.w).min(right.x + right.w);
    let edge_y = (left.y + left.h).min(right.y + right.h);
    (edge_x > x && edge_y > y).then_some(Rect::new(x, y, edge_x - x, edge_y - y))
}

fn handle_rects(bounds: Rect) -> [(TransformGizmoHandle, Rect); 8] {
    let half = HANDLE_SIZE * 0.5;
    let cx = bounds.x + bounds.w * 0.5;
    let cy = bounds.y + bounds.h * 0.5;
    let point_rect = |x: f32, y: f32| Rect::new(x - half, y - half, HANDLE_SIZE, HANDLE_SIZE);
    [
        (TransformGizmoHandle::TopLeft, point_rect(bounds.x, bounds.y)),
        (TransformGizmoHandle::Top, point_rect(cx, bounds.y)),
        (TransformGizmoHandle::TopRight, point_rect(bounds.x + bounds.w, bounds.y)),
        (TransformGizmoHandle::Right, point_rect(bounds.x + bounds.w, cy)),
        (TransformGizmoHandle::BottomRight, point_rect(bounds.x + bounds.w, bounds.y + bounds.h)),
        (TransformGizmoHandle::Bottom, point_rect(cx, bounds.y + bounds.h)),
        (TransformGizmoHandle::BottomLeft, point_rect(bounds.x, bounds.y + bounds.h)),
        (TransformGizmoHandle::Left, point_rect(bounds.x, cy)),
    ]
}

fn rotation_centers(bounds: Rect) -> [(TransformGizmoHandle, Vec2); 4] {
    [
        (
            TransformGizmoHandle::RotateTopLeft,
            vec2(bounds.x - ROTATE_OFFSET, bounds.y - ROTATE_OFFSET),
        ),
        (
            TransformGizmoHandle::RotateTopRight,
            vec2(bounds.x + bounds.w + ROTATE_OFFSET, bounds.y - ROTATE_OFFSET),
        ),
        (
            TransformGizmoHandle::RotateBottomLeft,
            vec2(bounds.x - ROTATE_OFFSET, bounds.y + bounds.h + ROTATE_OFFSET),
        ),
        (
            TransformGizmoHandle::RotateBottomRight,
            vec2(bounds.x + bounds.w + ROTATE_OFFSET, bounds.y + bounds.h + ROTATE_OFFSET),
        ),
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pivot_wins_over_move_hit_testing() {
        let bounds = Rect::new(10.0, 10.0, 40.0, 30.0);
        let pivot = vec2(30.0, 25.0);
        assert_eq!(
            hit_test_transform_gizmo(bounds, pivot, pivot),
            Some(TransformGizmoHandle::Pivot)
        );
    }

    #[test]
    fn right_handle_is_detectable() {
        let bounds = Rect::new(10.0, 10.0, 40.0, 30.0);
        let hit = hit_test_transform_gizmo(bounds, vec2(30.0, 25.0), vec2(50.0, 25.0));
        assert_eq!(hit, Some(TransformGizmoHandle::Right));
    }

    #[test]
    fn clipped_rect_never_escapes_canvas() {
        let clip = Rect::new(20.0, 20.0, 30.0, 30.0);
        let clipped = clipped_rect(Rect::new(10.0, 10.0, 30.0, 30.0), clip).unwrap();
        assert_eq!(clipped.x, 20.0);
        assert_eq!(clipped.y, 20.0);
        assert_eq!(clipped.w, 20.0);
        assert_eq!(clipped.h, 20.0);
    }
}
