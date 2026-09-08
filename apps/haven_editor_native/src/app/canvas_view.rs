use haven_core::{SceneMap, MAP_H, MAP_W};
use macroquad::prelude::*;

use super::editor_text::{draw_editor_text, measure_editor_text};
use super::editor_theme;
use super::render_helpers::{draw_editor_widget, scene_tile_color};
use super::world_surface_editor::WorldSurfaceViewOptions;
use super::{MUTED, PANEL_EDGE, TEXT};

pub(crate) const CANVAS_RULER_THICKNESS: f32 = 24.0;

pub(crate) fn draw_canvas_rulers(viewport: Rect, visible: Rect, major_step: f32, unit_label: &str) {
    if viewport.w <= 1.0 || viewport.h <= 1.0 || visible.w <= 0.0 || visible.h <= 0.0 {
        return;
    }
    let top = Rect::new(
        viewport.x,
        viewport.y - CANVAS_RULER_THICKNESS,
        viewport.w,
        CANVAS_RULER_THICKNESS,
    );
    let left = Rect::new(
        viewport.x - CANVAS_RULER_THICKNESS,
        viewport.y,
        CANVAS_RULER_THICKNESS,
        viewport.h,
    );
    draw_rectangle(
        top.x,
        top.y,
        top.w,
        top.h,
        Color::new(0.055, 0.075, 0.085, 1.0),
    );
    draw_rectangle(
        left.x,
        left.y,
        left.w,
        left.h,
        Color::new(0.055, 0.075, 0.085, 1.0),
    );
    draw_rectangle_lines(top.x, top.y, top.w, top.h, 1.0, PANEL_EDGE);
    draw_rectangle_lines(left.x, left.y, left.w, left.h, 1.0, PANEL_EDGE);

    let step = adaptive_ruler_step(major_step.max(0.0001), visible.w / viewport.w.max(1.0));
    let start_x = (visible.x / step).floor() as i32;
    let end_x = ((visible.x + visible.w) / step).ceil() as i32;
    for index in start_x..=end_x {
        let world_x = index as f32 * step;
        let screen_x = viewport.x + (world_x - visible.x) / visible.w * viewport.w;
        if screen_x < viewport.x - 1.0 || screen_x > viewport.x + viewport.w + 1.0 {
            continue;
        }
        draw_line(screen_x, top.y + 14.0, screen_x, top.y + top.h, 1.0, MUTED);
        draw_editor_text(
            &format_ruler_value(world_x),
            screen_x + 3.0,
            top.y + 12.0,
            11.0,
            MUTED,
        );
    }
    let start_y = (visible.y / step).floor() as i32;
    let end_y = ((visible.y + visible.h) / step).ceil() as i32;
    for index in start_y..=end_y {
        let world_y = index as f32 * step;
        let screen_y = viewport.y + (world_y - visible.y) / visible.h * viewport.h;
        if screen_y < viewport.y - 1.0 || screen_y > viewport.y + viewport.h + 1.0 {
            continue;
        }
        draw_line(
            left.x + 14.0,
            screen_y,
            left.x + left.w,
            screen_y,
            1.0,
            MUTED,
        );
        draw_editor_text(
            &format_ruler_value(world_y),
            left.x + 2.0,
            screen_y - 3.0,
            10.0,
            MUTED,
        );
    }

    let mouse = vec2(mouse_position().0, mouse_position().1);
    if viewport.contains(mouse) {
        let world_x = visible.x + (mouse.x - viewport.x) / viewport.w * visible.w;
        let world_y = visible.y + (mouse.y - viewport.y) / viewport.h * visible.h;
        draw_line(
            mouse.x,
            viewport.y,
            mouse.x,
            viewport.y + viewport.h,
            1.0,
            Color::new(0.96, 0.62, 0.30, 0.58),
        );
        draw_line(
            viewport.x,
            mouse.y,
            viewport.x + viewport.w,
            mouse.y,
            1.0,
            Color::new(0.96, 0.62, 0.30, 0.58),
        );
        let readout = format!(
            "{} {}, {}",
            unit_label,
            format_ruler_value(world_x),
            format_ruler_value(world_y)
        );
        let width = measure_editor_text(&readout, None, 13, 1.0).width + 12.0;
        let x = (mouse.x + 12.0).min(viewport.x + viewport.w - width - 4.0);
        let y = (mouse.y - 10.0).max(viewport.y + 18.0);
        draw_rectangle(x, y - 16.0, width, 20.0, Color::new(0.02, 0.03, 0.04, 0.90));
        draw_editor_text(&readout, x + 6.0, y, 13.0, TEXT);
    }
}

fn adaptive_ruler_step(base: f32, world_per_pixel: f32) -> f32 {
    let target = (world_per_pixel * 90.0).max(base);
    let exponent = target.log10().floor();
    let magnitude = 10.0_f32.powf(exponent);
    let normalized = target / magnitude;
    let snapped = if normalized <= 1.0 {
        1.0
    } else if normalized <= 2.0 {
        2.0
    } else if normalized <= 5.0 {
        5.0
    } else {
        10.0
    };
    (snapped * magnitude).max(base)
}

fn format_ruler_value(value: f32) -> String {
    if value.abs() >= 1000.0 {
        format!("{:.1}k", value / 1000.0)
    } else if value.fract().abs() < 0.01 {
        format!("{}", value.round() as i32)
    } else {
        format!("{value:.1}")
    }
}


const CANVAS_VIEW_CONTROL_H: f32 = 28.0;
const CANVAS_VIEW_CONTROL_GAP: f32 = 3.0;
const CANVAS_VIEW_CONTROL_MARGIN: f32 = 8.0;

pub(crate) fn canvas_view_control_rect(viewport: Rect, index: usize) -> Rect {
    // W72D: [-] [zoom] [+] [1:1] [Frame] is the only zoom/view chrome and
    // lives directly inside the upper-right corner of the authored canvas.
    // Tool Rail and Layers remain dedicated sibling columns outside the canvas.
    const WIDTHS: [f32; 5] = [30.0, 62.0, 30.0, 42.0, 58.0];
    let total = WIDTHS.iter().sum::<f32>()
        + CANVAS_VIEW_CONTROL_GAP * (WIDTHS.len().saturating_sub(1) as f32);
    let x0 = (viewport.x + viewport.w - total - CANVAS_VIEW_CONTROL_MARGIN)
        .max(viewport.x + CANVAS_VIEW_CONTROL_MARGIN);
    let mut x = x0;
    for width in WIDTHS.iter().take(index) {
        x += *width + CANVAS_VIEW_CONTROL_GAP;
    }
    Rect::new(
        x,
        viewport.y + CANVAS_VIEW_CONTROL_MARGIN,
        WIDTHS[index.min(WIDTHS.len() - 1)],
        CANVAS_VIEW_CONTROL_H,
    )
}

pub(crate) fn draw_canvas_view_controls(viewport: Rect, zoom_percent: f32) {
    if viewport.w < 250.0 || viewport.h < 48.0 {
        return;
    }
    let first = canvas_view_control_rect(viewport, 0);
    let last = canvas_view_control_rect(viewport, 4);
    let backdrop = Rect::new(
        first.x - 4.0,
        first.y - 4.0,
        last.x + last.w - first.x + 8.0,
        CANVAS_VIEW_CONTROL_H + 8.0,
    );
    draw_rectangle(
        backdrop.x,
        backdrop.y,
        backdrop.w,
        backdrop.h,
        Color::new(0.035, 0.045, 0.055, 0.96),
    );
    draw_rectangle_lines(
        backdrop.x,
        backdrop.y,
        backdrop.w,
        backdrop.h,
        1.0,
        editor_theme::colors::BORDER_STRONG,
    );
    draw_editor_widget(canvas_view_control_rect(viewport, 0), "−", false);
    let zoom = canvas_view_control_rect(viewport, 1);
    draw_rectangle(zoom.x, zoom.y, zoom.w, zoom.h, editor_theme::colors::CONTROL_BG);
    draw_rectangle_lines(zoom.x, zoom.y, zoom.w, zoom.h, 1.0, editor_theme::colors::BORDER_SUBTLE);
    let label = format!("{:.0}%", zoom_percent);
    let width = measure_editor_text(&label, None, 11, 1.0).width;
    draw_editor_text(
        &label,
        zoom.x + (zoom.w - width) * 0.5,
        zoom.y + 18.0,
        11.0,
        TEXT,
    );
    draw_editor_widget(canvas_view_control_rect(viewport, 2), "+", false);
    draw_editor_widget(canvas_view_control_rect(viewport, 3), "1:1", false);
    draw_editor_widget(canvas_view_control_rect(viewport, 4), "Frame", false);
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum CanvasToolbarKind {
    SceneMap,
    WorldScenes,
    SceneBank,
}

pub(crate) fn draw_canvas_toolbar(
    _host: Rect,
    _mode: CanvasToolbarKind,
    _zoom_percent: f32,
    _pan_active: bool,
    _world_options: Option<WorldSurfaceViewOptions>,
) {
    // W72D: retired compatibility shim. The historical full-width canvas
    // toolbar is never rendered. View controls live in the upper-right of the
    // actual canvas; world/scene options live in Layers, Tool Rail, Properties,
    // or contextual bottom trays. Keeping the symbol avoids breakage in older
    // call sites while guaranteeing that no separator toolbar can reappear.
}

pub(crate) fn draw_infinite_grid(visible: Rect, minor_step: f32, major_every: i32, zoom: f32) {
    if minor_step <= 0.0 || major_every <= 0 {
        return;
    }
    let minor_color = Color::new(0.23, 0.30, 0.33, 0.48);
    let major_color = Color::new(0.34, 0.43, 0.46, 0.78);
    let axis_color = Color::new(0.62, 0.50, 0.34, 0.82);
    let thin = ((0.055_f32).max(minor_step * 0.010) / zoom.max(0.20)).min(minor_step * 0.08);
    let thick = ((0.11_f32).max(minor_step * 0.020) / zoom.max(0.20)).min(minor_step * 0.12);
    let mut x = (visible.x / minor_step).floor() * minor_step;
    while x <= visible.x + visible.w {
        let grid_index = (x / minor_step).round() as i32;
        let major = grid_index.rem_euclid(major_every) == 0;
        let color = if grid_index == 0 {
            axis_color
        } else if major {
            major_color
        } else {
            minor_color
        };
        draw_line(
            x,
            visible.y,
            x,
            visible.y + visible.h,
            if major { thick } else { thin },
            color,
        );
        x += minor_step;
    }
    let mut y = (visible.y / minor_step).floor() * minor_step;
    while y <= visible.y + visible.h {
        let grid_index = (y / minor_step).round() as i32;
        let major = grid_index.rem_euclid(major_every) == 0;
        let color = if grid_index == 0 {
            axis_color
        } else if major {
            major_color
        } else {
            minor_color
        };
        draw_line(
            visible.x,
            y,
            visible.x + visible.w,
            y,
            if major { thick } else { thin },
            color,
        );
        y += minor_step;
    }
}

fn preview_grid_dimensions(rect: Rect) -> (i32, i32) {
    let columns = ((rect.w / 4.0).round() as i32)
        .clamp(8, 32)
        .min(MAP_W as i32);
    let rows = ((rect.h / 4.0).round() as i32)
        .clamp(8, 24)
        .min(MAP_H as i32);
    (columns, rows)
}

pub(crate) fn draw_scene_into_rect(scene: &SceneMap, rect: Rect) {
    // Scene cards previously issued MAP_W * MAP_H draw calls for every visible
    // card. With expanded 96x64 scenes this could exceed one hundred thousand
    // rectangles per frame and make Windows dim the editor as unresponsive.
    // Downsample the preview and merge horizontal runs while the real scene
    // editor continues to draw the complete map at native tile resolution.
    let (columns, rows) = preview_grid_dimensions(rect);
    let cell_w = rect.w / columns as f32;
    let cell_h = rect.h / rows as f32;

    for preview_y in 0..rows {
        let source_y = (((preview_y as f32 + 0.5) * MAP_H as f32 / rows as f32).floor() as i32)
            .clamp(0, MAP_H as i32 - 1);
        let mut run_start = 0;
        let first_source_x =
            ((0.5 * MAP_W as f32 / columns as f32).floor() as i32).clamp(0, MAP_W as i32 - 1);
        let mut run_tile = scene.map.get(first_source_x, source_y);

        for preview_x in 1..=columns {
            let next_tile = if preview_x < columns {
                let source_x = (((preview_x as f32 + 0.5) * MAP_W as f32 / columns as f32).floor()
                    as i32)
                    .clamp(0, MAP_W as i32 - 1);
                Some(scene.map.get(source_x, source_y))
            } else {
                None
            };

            if next_tile == Some(run_tile) {
                continue;
            }

            draw_rectangle(
                rect.x + run_start as f32 * cell_w,
                rect.y + preview_y as f32 * cell_h,
                (preview_x - run_start) as f32 * cell_w + 0.2,
                cell_h + 0.2,
                scene_tile_color(run_tile),
            );
            if let Some(tile) = next_tile {
                run_start = preview_x;
                run_tile = tile;
            }
        }
    }
}

#[cfg(test)]
mod preview_tests {
    use super::*;

    #[test]
    fn scene_preview_grid_is_bounded_for_large_scene_cards() {
        let (columns, rows) = preview_grid_dimensions(Rect::new(0.0, 0.0, 96.0, 96.0));
        assert!(columns <= 32);
        assert!(rows <= 24);
        assert!(columns * rows < MAP_W as i32 * MAP_H as i32);
    }
}
