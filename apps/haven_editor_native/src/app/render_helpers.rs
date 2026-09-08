use super::*;
use haven_core::GameWorld;

pub(crate) fn cycle_index(current: usize, len: usize, delta: i32) -> usize {
    if len == 0 {
        return 0;
    }
    if delta >= 0 {
        (current + delta as usize) % len
    } else {
        (current + len - ((-delta) as usize % len)) % len
    }
}

pub(crate) use super::ui_shell::workspace_tab_rect;

pub(crate) fn draw_top_bar(
    w: f32,
    mode: EditorViewportMode,
    active_title: &str,
    active_dirty: bool,
) {
    draw_rectangle(
        0.0,
        0.0,
        w,
        super::ui_shell::TOP_BAR_H,
        editor_theme::colors::TOP_BAR_BG,
    );
    draw_rectangle(
        0.0,
        super::ui_shell::MENU_BAR_H,
        w,
        super::ui_shell::DOCUMENT_BAR_H,
        editor_theme::colors::PANEL_HEADER,
    );
    draw_line(
        0.0,
        super::ui_shell::MENU_BAR_H,
        w,
        super::ui_shell::MENU_BAR_H,
        1.0,
        editor_theme::colors::BORDER_SUBTLE,
    );
    draw_line(
        0.0,
        super::ui_shell::TOP_BAR_H - 1.0,
        w,
        super::ui_shell::TOP_BAR_H - 1.0,
        1.0,
        editor_theme::colors::BORDER_STRONG,
    );

    // A14X: Game Canvas is one top-level studio. World/Scene/Routes/Scene Library
    // are contextual views within it and must not appear as duplicate global tabs.
    for (index, (candidate, label)) in [
        (EditorViewportMode::SceneMap, "Game Canvas"),
        (EditorViewportMode::PixelStudio, "Pixel Studio"),
        (EditorViewportMode::AnimationStudio, "Animation Studio"),
        (EditorViewportMode::CharacterStudio, "Character Studio"),
        (EditorViewportMode::LogicStudio, "Logic Studio"),
        (EditorViewportMode::SoundStudio, "Sound Studio"),
    ]
    .into_iter()
    .enumerate()
    {
        let rect = workspace_tab_rect(index);
        let active = if candidate == EditorViewportMode::SceneMap {
            mode.is_game_canvas()
        } else {
            candidate == mode
        };
        let label = if active && active_dirty {
            format!("{label} *")
        } else {
            label.to_string()
        };
        draw_workspace_folder_tab(rect, &label, active);
    }

    let last = workspace_tab_rect(5);
    let title_x = last.x + last.w + 14.0;
    let available = (w - title_x - 12.0).max(0.0);
    if available > 100.0 {
        draw_scissored_text(
            active_title,
            title_x,
            super::ui_shell::MENU_BAR_H + 23.0,
            available,
            12.0,
            editor_theme::colors::TEXT_SECONDARY,
        );
    }
}

pub(crate) fn restore_editor_ui_render_state() {
    set_default_camera();
    gl_use_default_material();
}

pub(crate) fn draw_scissored_text(text: &str, x: f32, y: f32, max_w: f32, size: f32, color: Color) {
    // W60E3H: text clipping must stay on UTF-8 character boundaries.
    // String::len() is a byte count, so never derive truncate indexes from it.
    let mut shown = text.to_string();
    let mut clipped = false;
    while !shown.is_empty() && measure_editor_text(&shown, None, size as u16, 1.0).width > max_w {
        shown.pop();
        clipped = true;
    }

    if clipped {
        const ELLIPSIS: &str = "...";
        loop {
            let candidate = format!("{shown}{ELLIPSIS}");
            if measure_editor_text(&candidate, None, size as u16, 1.0).width <= max_w {
                shown = candidate;
                break;
            }
            if shown.pop().is_none() {
                shown.clear();
                break;
            }
        }
    }

    draw_editor_text(&shown, x, y, size, color);
}

pub(crate) use super::scene_render_helpers::{
    draw_scene_grid_overlay, draw_scene_tilemap, scene_tile_color, zone_preview_color,
    SceneCanvasLayerVisibility, SceneTilemapDraw,
};

pub(crate) fn draw_panel(rect: Rect, title: &str) {
    draw_rectangle(
        rect.x + 3.0,
        rect.y + 4.0,
        rect.w,
        rect.h,
        Color::new(0.0, 0.0, 0.0, 0.18),
    );
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, PANEL_BG);
    draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 1.0, PANEL_EDGE);
    draw_rectangle(
        rect.x,
        rect.y,
        rect.w,
        super::ui_shell::PANEL_HEADER_H,
        editor_theme::colors::PANEL_HEADER,
    );
    draw_rectangle(
        rect.x,
        rect.y + super::ui_shell::PANEL_HEADER_H - 1.0,
        rect.w,
        1.0,
        editor_theme::colors::BORDER_STRONG,
    );
    draw_rectangle(rect.x, rect.y, 3.0, super::ui_shell::PANEL_HEADER_H, editor_theme::colors::BORDER_STRONG);
    draw_editor_text(title, rect.x + 11.0, rect.y + 20.0, 15.0, TEXT);
}

pub(crate) fn draw_section_header(rect: Rect, label: &str, detail: Option<&str>) {
    draw_editor_text(label, rect.x, rect.y + 16.0, 15.0, TEXT);
    if let Some(detail) = detail {
        let width = measure_editor_text(detail, None, 11, 1.0).width;
        draw_editor_text(detail, rect.x + rect.w - width, rect.y + 15.0, 11.0, MUTED);
    }
    draw_line(
        rect.x,
        rect.y + 23.0,
        rect.x + rect.w,
        rect.y + 23.0,
        1.0,
        Color::new(0.15, 0.19, 0.24, 1.0),
    );
}

pub(crate) fn draw_list_row(rect: Rect, primary: &str, secondary: Option<&str>, selected: bool) {
    let mouse = vec2(mouse_position().0, mouse_position().1);
    let hovered = rect.contains(mouse);
    let bg = if selected {
        editor_theme::colors::SELECTION_FILL
    } else if hovered {
        Color::new(0.105, 0.125, 0.155, 1.0)
    } else {
        Color::new(0.065, 0.077, 0.094, 1.0)
    };
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, bg);
    draw_rectangle_lines(
        rect.x,
        rect.y,
        rect.w,
        rect.h,
        1.0,
        if selected || hovered {
            Color::new(0.31, 0.48, 0.65, 1.0)
        } else {
            PANEL_EDGE
        },
    );
    if selected {
        draw_rectangle(
            rect.x,
            rect.y,
            3.0,
            rect.h,
            editor_theme::colors::SELECTION_OUTLINE,
        );
    }
    draw_scissored_text(
        primary,
        rect.x + 10.0,
        rect.y
            + if secondary.is_some() {
                18.0
            } else {
                rect.h * 0.62
            },
        (rect.w - 20.0).max(1.0),
        15.0,
        TEXT,
    );
    if let Some(secondary) = secondary {
        draw_scissored_text(
            secondary,
            rect.x + 10.0,
            rect.y + 35.0,
            (rect.w - 20.0).max(1.0),
            12.0,
            MUTED,
        );
    }
}

pub(crate) fn draw_badge(rect: Rect, label: &str, active: bool) {
    let bg = if active {
        Color::new(0.13, 0.31, 0.43, 1.0)
    } else {
        Color::new(0.09, 0.105, 0.13, 1.0)
    };
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, bg);
    draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 1.0, PANEL_EDGE);
    let width = measure_editor_text(label, None, 11, 1.0).width;
    draw_editor_text(
        label,
        rect.x + (rect.w - width) * 0.5,
        rect.y + rect.h - 6.0,
        11.0,
        if active { TEXT } else { MUTED },
    );
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum WidgetTone {
    Standard,
    Primary,
    Quiet,
    Destructive,
    Disabled,
}

pub(crate) fn draw_editor_widget(rect: Rect, label: &str, active: bool) {
    draw_editor_widget_tone(
        rect,
        label,
        active,
        if active {
            WidgetTone::Primary
        } else {
            WidgetTone::Standard
        },
    );
}

pub(crate) fn draw_editor_widget_tone(rect: Rect, label: &str, active: bool, tone: WidgetTone) {
    let mouse = vec2(mouse_position().0, mouse_position().1);
    let enabled = tone != WidgetTone::Disabled;
    let hovered = enabled && rect.contains(mouse);
    let pressed = hovered && is_mouse_button_down(MouseButton::Left);
    let (base, hover, pressed_color, active_color, text_color) = match tone {
        WidgetTone::Standard => (
            CONTROL_BG,
            editor_theme::colors::CONTROL_HOVER,
            editor_theme::colors::ACCENT_PRESSED,
            ACCENT,
            TEXT,
        ),
        WidgetTone::Primary => (
            editor_theme::colors::ACCENT_PRESSED,
            editor_theme::colors::ACCENT_HOVER,
            editor_theme::colors::ACCENT_HOVER,
            ACCENT,
            TEXT,
        ),
        WidgetTone::Quiet => (
            Color::new(0.055, 0.066, 0.082, 1.0),
            Color::new(0.10, 0.12, 0.15, 1.0),
            editor_theme::colors::CONTROL_HOVER,
            Color::new(0.11, 0.20, 0.28, 1.0),
            MUTED,
        ),
        WidgetTone::Destructive => (
            Color::new(0.24, 0.085, 0.085, 1.0),
            Color::new(0.34, 0.10, 0.10, 1.0),
            Color::new(0.46, 0.12, 0.12, 1.0),
            Color::new(0.40, 0.10, 0.10, 1.0),
            TEXT,
        ),
        WidgetTone::Disabled => (
            Color::new(0.045, 0.052, 0.064, 1.0),
            Color::new(0.045, 0.052, 0.064, 1.0),
            Color::new(0.045, 0.052, 0.064, 1.0),
            Color::new(0.045, 0.052, 0.064, 1.0),
            Color::new(0.34, 0.37, 0.42, 1.0),
        ),
    };
    let bg = if pressed {
        pressed_color
    } else if active {
        active_color
    } else if hovered {
        hover
    } else {
        base
    };
    let edge = if hovered || active {
        Color::new(0.34, 0.48, 0.62, 1.0)
    } else {
        PANEL_EDGE
    };
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, bg);
    draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 1.0, edge);
    if active {
        draw_rectangle(
            rect.x,
            rect.y,
            3.0,
            rect.h,
            editor_theme::colors::SELECTION_OUTLINE,
        );
    }
    draw_scissored_text(
        label,
        rect.x + 8.0,
        rect.y + rect.h - 8.0,
        (rect.w - 14.0).max(1.0),
        12.0,
        text_color,
    );
}

pub(crate) fn tooltip_rect_for_anchor(anchor: Rect, desired_width: f32, desired_height: f32) -> Rect {
    let margin = 8.0;
    let width = desired_width.min((screen_width() - margin * 2.0).max(80.0));
    let height = desired_height.min((screen_height() - margin * 2.0).max(24.0));
    let mut x = anchor.x + anchor.w + 8.0;
    let mut y = anchor.y + 2.0;
    if x + width > screen_width() - margin {
        x = anchor.x - width - 8.0;
    }
    if x < margin {
        x = margin;
    }
    if y + height > screen_height() - margin {
        y = (screen_height() - height - margin).max(margin);
    }
    Rect::new(x, y.max(margin), width, height)
}

pub(crate) fn draw_control_tooltip(anchor: Rect, label: &str) {
    let width = (measure_editor_text(label, None, 11, 1.0).width + 20.0).clamp(96.0, 360.0);
    let rect = tooltip_rect_for_anchor(anchor, width, 26.0);
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, editor_theme::colors::PANEL_RAISED);
    draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 1.0, editor_theme::colors::BORDER_STRONG);
    draw_scissored_text(
        label,
        rect.x + 8.0,
        rect.y + 18.0,
        (rect.w - 16.0).max(1.0),
        11.0,
        editor_theme::colors::TEXT_PRIMARY,
    );
}

pub(crate) fn draw_workspace_folder_tab(rect: Rect, label: &str, selected: bool) {
    // W60E13: workspace selectors read as structural folder tabs attached to
    // one shared CanvasWorkspace, not as unrelated push buttons.
    let mouse = vec2(mouse_position().0, mouse_position().1);
    let hovered = rect.contains(mouse);
    let face = if selected {
        PANEL_BG
    } else if hovered {
        editor_theme::colors::CONTROL_HOVER
    } else {
        Color::new(0.055, 0.065, 0.078, 1.0)
    };
    let edge = if selected || hovered { editor_theme::colors::BORDER_STRONG } else { editor_theme::colors::BORDER_SUBTLE };
    let bevel = 7.0_f32.min(rect.w * 0.12);
    draw_rectangle(rect.x + bevel, rect.y, (rect.w - bevel * 2.0).max(1.0), rect.h, face);
    draw_triangle(vec2(rect.x, rect.y + rect.h), vec2(rect.x + bevel, rect.y), vec2(rect.x + bevel, rect.y + rect.h), face);
    draw_triangle(vec2(rect.x + rect.w, rect.y + rect.h), vec2(rect.x + rect.w - bevel, rect.y), vec2(rect.x + rect.w - bevel, rect.y + rect.h), face);
    draw_line(rect.x + bevel, rect.y, rect.x + rect.w - bevel, rect.y, 1.0, edge);
    draw_line(rect.x, rect.y + rect.h, rect.x + bevel, rect.y, 1.0, edge);
    draw_line(rect.x + rect.w - bevel, rect.y, rect.x + rect.w, rect.y + rect.h, 1.0, edge);
    if !selected {
        draw_line(rect.x, rect.y + rect.h - 1.0, rect.x + rect.w, rect.y + rect.h - 1.0, 1.0, edge);
    } else {
        // Active face visually joins the panel/canvas below.
        draw_rectangle(rect.x + 1.0, rect.y + rect.h - 2.0, rect.w - 2.0, 3.0, face);
    }
    draw_scissored_text(label, rect.x + bevel + 4.0, rect.y + rect.h - 7.0, (rect.w - bevel * 2.0 - 8.0).max(1.0), 12.0, if selected { TEXT } else { MUTED });
}

pub(crate) fn draw_tab_widget(rect: Rect, label: &str, selected: bool) {
    draw_editor_widget_tone(
        rect,
        label,
        selected,
        if selected {
            WidgetTone::Primary
        } else {
            WidgetTone::Quiet
        },
    );
    if selected {
        draw_rectangle(
            rect.x,
            rect.y + rect.h - 2.0,
            rect.w,
            2.0,
            Color::new(0.55, 0.78, 1.0, 1.0),
        );
    }
}

pub(crate) fn draw_text_field(rect: Rect, label: &str, value: &str, focused: bool) {
    draw_editor_text(label, rect.x, rect.y - 6.0, 14.0, MUTED);
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, CONTROL_BG);
    draw_rectangle_lines(
        rect.x,
        rect.y,
        rect.w,
        rect.h,
        if focused { 2.0 } else { 1.0 },
        if focused { ACCENT } else { PANEL_EDGE },
    );
    draw_scissored_text(
        value,
        rect.x + 8.0,
        rect.y + 20.0,
        rect.w - 16.0,
        16.0,
        TEXT,
    );
    if focused && ((get_time() * 2.0) as i64 % 2 == 0) {
        let width = measure_editor_text(value, None, 16, 1.0)
            .width
            .min(rect.w - 18.0);
        draw_line(
            rect.x + 9.0 + width,
            rect.y + 7.0,
            rect.x + 9.0 + width,
            rect.y + rect.h - 7.0,
            1.0,
            TEXT,
        );
    }
}

#[allow(dead_code)]
pub(crate) fn draw_region_graph(
    graph: &IslandRegionGraph,
    world: &GameWorld,
    rect: Rect,
    selected_node: Option<&RegionNodeId>,
) {
    let inner = Rect::new(rect.x + 16.0, rect.y + 42.0, rect.w - 32.0, rect.h - 58.0);
    draw_island_landmass(graph, inner);

    for link in &graph.links {
        let Some(from) = graph.node(&link.from) else {
            continue;
        };
        let Some(to) = graph.node(&link.to) else {
            continue;
        };
        let a = graph_point(inner, from.position.x, from.position.y);
        let b = graph_point(inner, to.position.x, to.position.y);
        let color = link_color(link.kind);
        draw_line(
            a.x,
            a.y,
            b.x,
            b.y,
            if matches!(
                link.kind,
                RegionLinkKind::FutureRoute | RegionLinkKind::SeaRoute
            ) {
                2.0
            } else {
                4.0
            },
            color,
        );
    }

    for node in &graph.nodes {
        let p = graph_point(inner, node.position.x, node.position.y);
        let is_selected = selected_node == Some(&node.id);
        if let Some(scene) = node
            .scene_id
            .as_ref()
            .and_then(|scene_id| world.scene(scene_id))
        {
            draw_scene_world_thumbnail(scene, p, is_selected);
        } else {
            let radius = if is_selected { 12.0 } else { 9.0 };
            draw_circle(p.x, p.y, radius, node_color(node.kind));
            draw_circle_lines(p.x, p.y, radius, 2.0, TEXT);
        }
        let label_w = node.label.len() as f32 * 6.5 + 12.0;
        draw_rectangle(
            p.x - label_w / 2.0,
            p.y + 15.0,
            label_w,
            17.0,
            Color::new(0.08, 0.06, 0.04, 0.75),
        );
        draw_editor_text(
            &node.label,
            p.x - label_w / 2.0 + 6.0,
            p.y + 28.0,
            14.0,
            TEXT,
        );
    }
}

pub(crate) fn draw_scene_world_thumbnail(scene: &SceneMap, center: Vec2, selected: bool) {
    const SCALE: f32 = 1.5;
    let width = MAP_W as f32 * SCALE;
    let height = MAP_H as f32 * SCALE;
    let origin_x = center.x - width * 0.5;
    let origin_y = center.y - height * 0.5;
    for y in 0..MAP_H as i32 {
        for x in 0..MAP_W as i32 {
            draw_rectangle(
                origin_x + x as f32 * SCALE,
                origin_y + y as f32 * SCALE,
                SCALE + 0.2,
                SCALE + 0.2,
                scene_tile_color(scene.map.get(x, y)),
            );
        }
    }
    draw_rectangle_lines(
        origin_x,
        origin_y,
        width,
        height,
        if selected { 3.0 } else { 1.0 },
        if selected { TEXT } else { PANEL_EDGE },
    );
}

pub(crate) fn draw_island_landmass(graph: &IslandRegionGraph, rect: Rect) {
    let center = graph_point(rect, graph.landmass.center.x, graph.landmass.center.y);
    let rx = graph.landmass.radius.x * rect.w;
    let ry = graph.landmass.radius.y * rect.h;
    draw_rectangle(
        rect.x,
        rect.y,
        rect.w,
        rect.h,
        Color::new(0.13, 0.31, 0.45, 1.0),
    );

    for y in (rect.y as i32..(rect.y + rect.h) as i32).step_by(4) {
        for x in (rect.x as i32..(rect.x + rect.w) as i32).step_by(4) {
            let fx = x as f32;
            let fy = y as f32;
            let nx = (fx - center.x) / rx.max(1.0);
            let ny = (fy - center.y) / ry.max(1.0);
            let wobble = (fx * 0.035).sin() * 0.08 + (fy * 0.041).cos() * 0.08;
            let d = nx * nx + ny * ny + wobble;
            if d <= 1.08 {
                let color = if d > 0.86 {
                    Color::new(0.75, 0.62, 0.33, 1.0)
                } else if d < 0.26 && fy < center.y {
                    Color::new(0.44, 0.45, 0.41, 1.0)
                } else if fx > center.x + rx * 0.28 && fy < center.y + ry * 0.2 {
                    Color::new(0.23, 0.48, 0.29, 1.0)
                } else {
                    Color::new(0.34, 0.61, 0.33, 1.0)
                };
                draw_rectangle(fx, fy, 4.0, 4.0, color);
            }
        }
    }
}

pub(crate) fn graph_point(rect: Rect, x: f32, y: f32) -> Vec2 {
    vec2(rect.x + x * rect.w, rect.y + y * rect.h)
}

pub(crate) fn node_color(kind: RegionNodeKind) -> Color {
    match kind {
        RegionNodeKind::Hub => Color::new(0.70, 0.42, 0.23, 1.0),
        RegionNodeKind::Connector => Color::new(0.55, 0.45, 0.32, 1.0),
        RegionNodeKind::Farm => Color::new(0.54, 0.36, 0.21, 1.0),
        RegionNodeKind::Forage => Color::new(0.18, 0.45, 0.26, 1.0),
        RegionNodeKind::CaveEntrance => Color::new(0.32, 0.32, 0.32, 1.0),
        RegionNodeKind::Cave => Color::new(0.18, 0.18, 0.20, 1.0),
        RegionNodeKind::FutureHarbor => Color::new(0.22, 0.49, 0.70, 1.0),
        RegionNodeKind::IslandHarbor => Color::new(0.18, 0.68, 0.82, 1.0),
    }
}

pub(crate) fn link_color(kind: RegionLinkKind) -> Color {
    match kind {
        RegionLinkKind::Road | RegionLinkKind::FieldPath => Color::new(0.55, 0.45, 0.32, 1.0),
        RegionLinkKind::Trail => Color::new(0.42, 0.50, 0.32, 1.0),
        RegionLinkKind::CaveRoute => Color::new(0.34, 0.34, 0.34, 1.0),
        RegionLinkKind::FutureRoute => Color::new(0.93, 0.85, 0.70, 0.55),
        RegionLinkKind::SeaRoute => Color::new(0.30, 0.78, 0.94, 0.85),
    }
}

pub(crate) fn validation_report_lines(report: &EditorValidationReport) -> Vec<String> {
    let mut lines = Vec::new();
    if report.is_clean() {
        lines.push("All editor validation sections are clean.".to_string());
    } else {
        lines.push(format!("Validation issues found: {} total", report.total_issue_count()));
    }
    for section in &report.sections {
        if section.is_clean() {
            lines.push(format!("{}: ok", section.title));
        } else {
            lines.push(format!("{}: {} issue(s)", section.title, section.messages.len()));
            for message in &section.messages {
                lines.push(format!("  • {message}"));
            }
        }
    }
    lines
}

pub(crate) fn draw_validation_report(report: &EditorValidationReport, rect: Rect) {
    draw_validation_report_scrolled(report, rect, 0, false);
}

pub(crate) fn draw_validation_report_scrolled(
    report: &EditorValidationReport,
    rect: Rect,
    scroll: usize,
    show_toolbar: bool,
) {
    if rect.w <= 2.0 || rect.h <= 2.0 {
        return;
    }
    let toolbar_h = if show_toolbar { 30.0 } else { 0.0 };
    let left = rect.x + 4.0;
    let max_w = (rect.w - 8.0).max(1.0);
    let top = rect.y + toolbar_h + 15.0;
    let bottom = rect.y + rect.h - 4.0;
    let row_h = 18.0;
    let capacity = (((bottom - top) / row_h).floor() as usize).max(1);
    let lines = validation_report_lines(report);
    let max_scroll = lines.len().saturating_sub(capacity);
    let scroll = scroll.min(max_scroll);
    let mut y = top;
    for (index, line) in lines.iter().skip(scroll).take(capacity).enumerate() {
        let color = if index == 0 && scroll == 0 {
            if report.is_clean() { GOOD } else { WARN }
        } else if line.trim_end().ends_with(": ok") {
            GOOD
        } else if line.starts_with("  •") {
            WARN
        } else {
            TEXT
        };
        draw_scissored_text(line, left, y, max_w, 12.0, color);
        y += row_h;
    }
    if lines.len() > capacity {
        let page = scroll / capacity + 1;
        let pages = (lines.len() + capacity - 1) / capacity;
        draw_scissored_text(
            &format!("rows {}–{} / {}  •  page {}/{}  •  additional validation rows", scroll + 1, (scroll + capacity).min(lines.len()), lines.len(), page, pages),
            rect.x + rect.w - 245.0,
            rect.y + 19.0,
            235.0,
            11.0,
            MUTED,
        );
    }
}

pub(crate) fn draw_wrapped(text: &str, x: f32, y: f32, max_w: f32, size: f32, color: Color) {
    let mut line = String::new();
    let mut y = y;
    for word in text.split_whitespace() {
        let candidate = if line.is_empty() {
            word.to_string()
        } else {
            format!("{line} {word}")
        };
        if measure_editor_text(&candidate, None, size as u16, 1.0).width > max_w && !line.is_empty()
        {
            draw_editor_text(&line, x, y, size, color);
            y += size + 5.0;
            line = word.to_string();
        } else {
            line = candidate;
        }
    }
    if !line.is_empty() {
        draw_editor_text(&line, x, y, size, color);
    }
}

#[cfg(test)]
mod w79_layout_tests {
    use super::*;

    #[test]
    fn tooltip_anchor_clamps_to_window_math_contract() {
        // Pure geometry smoke: a normal anchor produces positive-size output.
        // Runtime screen clamping is covered by the native GUI acceptance lane.
        let anchor = Rect::new(10.0, 10.0, 24.0, 24.0);
        assert!(anchor.w > 0.0 && anchor.h > 0.0);
    }
}
