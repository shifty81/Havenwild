use super::*;

pub(super) fn visible_tile_bounds(
    camera_target: Vec2,
    zoom: f32,
    padding_tiles: i32,
    dimensions: haven_core::SceneDimensions,
) -> (i32, i32, i32, i32) {
    visible_tile_bounds_for_viewport(
        camera_target,
        vec2(screen_width(), screen_height()),
        zoom,
        padding_tiles,
        dimensions,
    )
}

fn visible_tile_bounds_for_viewport(
    camera_target: Vec2,
    viewport_size: Vec2,
    zoom: f32,
    padding_tiles: i32,
    dimensions: haven_core::SceneDimensions,
) -> (i32, i32, i32, i32) {
    let half_visible = viewport_size / zoom.max(0.01) * 0.5;
    let min_x = (((camera_target.x - half_visible.x) / TILE_SIZE).floor() as i32 - padding_tiles)
        .clamp(0, dimensions.width as i32 - 1);
    let min_y = (((camera_target.y - half_visible.y) / TILE_SIZE).floor() as i32 - padding_tiles)
        .clamp(0, dimensions.height as i32 - 1);
    let max_x = (((camera_target.x + half_visible.x) / TILE_SIZE).ceil() as i32 + padding_tiles)
        .clamp(0, dimensions.width as i32 - 1);
    let max_y = (((camera_target.y + half_visible.y) / TILE_SIZE).ceil() as i32 + padding_tiles)
        .clamp(0, dimensions.height as i32 - 1);
    (min_x, min_y, max_x, max_y)
}

pub(super) fn tile_rect_intersects_bounds(
    rect: (i32, i32, i32, i32),
    bounds: (i32, i32, i32, i32),
    padding_tiles: i32,
) -> bool {
    let (x, y, width, height) = rect;
    let (min_x, min_y, max_x, max_y) = bounds;
    let rect_max_x = x + width.max(1) - 1;
    let rect_max_y = y + height.max(1) - 1;
    rect_max_x >= min_x - padding_tiles
        && x <= max_x + padding_tiles
        && rect_max_y >= min_y - padding_tiles
        && y <= max_y + padding_tiles
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bounds_are_clamped_to_expanded_scene_without_runtime_context() {
        let (min_x, min_y, max_x, max_y) = visible_tile_bounds_for_viewport(
            vec2(MAP_W as f32 * TILE_SIZE, MAP_H as f32 * TILE_SIZE),
            vec2(1920.0, 1080.0),
            1.15,
            2,
            haven_core::SceneDimensions::legacy_canvas(),
        );
        assert!(min_x >= 0 && min_y >= 0);
        assert_eq!(max_x, MAP_W as i32 - 1);
        assert_eq!(max_y, MAP_H as i32 - 1);
    }
}
