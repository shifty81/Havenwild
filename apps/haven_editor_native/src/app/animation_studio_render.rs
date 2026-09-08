use super::render_helpers::*;
use super::sprite_workspace::*;
use super::*;
use haven_pixel::{AnimationDocument, AnimationSocketKind, PixelSelection};
use haven_ui::{UiGrid, UiRect};

pub(crate) fn draw_animation_toolbar(app: &EditorApp, rect: Rect) {
    draw_sprite_toolbar_background(rect);
    draw_editor_widget(
        animation_play_rect(rect),
        if app.animation_studio.playing {
            "Pause"
        } else {
            "Play"
        },
        app.animation_studio.playing,
    );
    draw_editor_widget(animation_prev_frame_rect(rect), "Prev", false);
    draw_editor_widget(animation_next_frame_rect(rect), "Next", false);
    draw_editor_widget(animation_add_frame_rect(rect), "+ Frame", false);
    draw_editor_widget(animation_duplicate_frame_rect(rect), "Duplicate", false);
    draw_editor_widget(animation_delete_frame_rect(rect), "Delete", false);
    draw_editor_widget(animation_move_left_rect(rect), "Move <", false);
    draw_editor_widget(animation_move_right_rect(rect), "Move >", false);
    draw_editor_widget(
        animation_onion_rect(rect),
        "Onion",
        app.animation_studio.onion_skin,
    );
    draw_editor_widget(
        animation_grid_rect(rect),
        "Grid",
        app.animation_studio.show_source_grid,
    );

    let transport_end = animation_next_frame_rect(rect).x + animation_next_frame_rect(rect).w;
    let edit_end = animation_move_right_rect(rect).x + animation_move_right_rect(rect).w;
    draw_sprite_toolbar_separator(transport_end + 4.0, rect);
    draw_sprite_toolbar_separator(edit_end + 4.0, rect);
}

pub(crate) fn draw_animation_source_sheet(
    app: &EditorApp,
    document: &AnimationDocument,
    texture: &Texture2D,
    rect: Rect,
) {
    let content = Rect::new(rect.x + 8.0, rect.y + 32.0, rect.w - 16.0, rect.h - 40.0);
    draw_animation_checkerboard(content, 12.0);
    let image_rect = fit_image_rect(
        content,
        document.metadata.image_width,
        document.metadata.image_height,
        1.0,
    );
    draw_texture_ex(
        texture,
        image_rect.x,
        image_rect.y,
        WHITE,
        DrawTextureParams {
            dest_size: Some(vec2(image_rect.w, image_rect.h)),
            ..Default::default()
        },
    );
    restore_editor_ui_render_state();
    if app.animation_studio.show_source_grid {
        draw_source_grid(document, image_rect);
    }
    if let Some(selection) = app.animation_studio.selected_source() {
        let scale_x = image_rect.w / document.metadata.image_width.max(1) as f32;
        let scale_y = image_rect.h / document.metadata.image_height.max(1) as f32;
        let selected = Rect::new(
            image_rect.x + selection.x as f32 * scale_x,
            image_rect.y + selection.y as f32 * scale_y,
            selection.width as f32 * scale_x,
            selection.height as f32 * scale_y,
        );
        draw_rectangle_lines(selected.x, selected.y, selected.w, selected.h, 3.0, GOOD);
    }
}

pub(crate) fn draw_animation_preview(
    app: &EditorApp,
    document: &AnimationDocument,
    texture: &Texture2D,
    rect: Rect,
) {
    let content = Rect::new(rect.x + 8.0, rect.y + 32.0, rect.w - 16.0, rect.h - 40.0);
    draw_animation_checkerboard(content, 14.0);
    let Some(frame) = document.frame() else {
        draw_wrapped(
            "Add a source cell to the selected clip to begin previewing.",
            content.x + 12.0,
            content.y + 32.0,
            content.w - 24.0,
            16.0,
            MUTED,
        );
        return;
    };
    if app.animation_studio.onion_skin {
        let frame_count = document.clip().map_or(0, |clip| clip.frames.len());
        if frame_count > 1 {
            let previous = if document.selected_frame == 0 {
                frame_count - 1
            } else {
                document.selected_frame - 1
            };
            if let Some(previous_frame) = document.clip().and_then(|clip| clip.frames.get(previous))
            {
                draw_frame_in_preview(
                    texture,
                    previous_frame.source,
                    content,
                    Color::new(0.25, 0.65, 1.0, 0.22),
                );
            }
        }
    }
    let destination = draw_frame_in_preview(texture, frame.source, content, WHITE);
    let scale_x = destination.w / frame.source.width.max(1) as f32;
    let scale_y = destination.h / frame.source.height.max(1) as f32;
    let pivot_x = destination.x + frame.pivot[0] as f32 * scale_x;
    let pivot_y = destination.y + frame.pivot[1] as f32 * scale_y;
    draw_line(pivot_x - 7.0, pivot_y, pivot_x + 7.0, pivot_y, 2.0, WARN);
    draw_line(pivot_x, pivot_y - 7.0, pivot_x, pivot_y + 7.0, 2.0, WARN);
    let shadow_x = pivot_x + frame.shadow_offset[0] as f32 * scale_x;
    let shadow_y = pivot_y + frame.shadow_offset[1] as f32 * scale_y;
    draw_ellipse_lines(
        shadow_x,
        shadow_y,
        14.0,
        5.0,
        0.0,
        1.0,
        Color::new(0.35, 0.40, 0.48, 0.95),
    );
    for socket in &frame.sockets {
        let x = destination.x + socket.position[0] as f32 * scale_x;
        let y = destination.y + socket.position[1] as f32 * scale_y;
        draw_circle(x, y, 5.0, socket_color(socket.kind));
        draw_circle_lines(x, y, 7.0, 1.0, TEXT);
        draw_editor_text(socket.kind.label(), x + 9.0, y + 4.0, 11.0, TEXT);
    }
    draw_animation_gameplay_guides(frame, destination);
    draw_scissored_text(
        &format!(
            "{} | {} ms | {} sockets | {} events",
            app.animation_studio.placement_mode.label(),
            frame.duration_ms,
            frame.sockets.len(),
            frame.events.len()
        ),
        content.x + 8.0,
        content.y + content.h - 8.0,
        content.w - 16.0,
        13.0,
        MUTED,
    );
}

fn draw_frame_in_preview(
    texture: &Texture2D,
    source: PixelSelection,
    content: Rect,
    tint: Color,
) -> Rect {
    let destination = fit_image_rect(content, source.width, source.height, 4.0);
    draw_texture_ex(
        texture,
        destination.x,
        destination.y,
        tint,
        DrawTextureParams {
            dest_size: Some(vec2(destination.w, destination.h)),
            source: Some(Rect::new(
                source.x as f32,
                source.y as f32,
                source.width as f32,
                source.height as f32,
            )),
            ..Default::default()
        },
    );
    restore_editor_ui_render_state();
    destination
}

pub(crate) fn draw_animation_timeline(
    _app: &EditorApp,
    document: &AnimationDocument,
    texture: &Texture2D,
    rect: Rect,
) {
    let Some(clip) = document.clip() else {
        return;
    };
    draw_section_header(
        Rect::new(rect.x + 10.0, rect.y + 2.0, rect.w - 20.0, 24.0),
        "Timeline",
        Some(&format!("{} frames", clip.frames.len())),
    );
    let start_x = rect.x + 10.0;
    let y = rect.y + 32.0;
    for (index, frame) in clip.frames.iter().take(12).enumerate() {
        let item = animation_timeline_frame_rect(rect, index);
        draw_animation_checkerboard(item, 8.0);
        draw_texture_ex(
            texture,
            item.x + 4.0,
            item.y + 4.0,
            WHITE,
            DrawTextureParams {
                dest_size: Some(vec2(item.w - 8.0, item.h - 24.0)),
                source: Some(Rect::new(
                    frame.source.x as f32,
                    frame.source.y as f32,
                    frame.source.width as f32,
                    frame.source.height as f32,
                )),
                ..Default::default()
            },
        );
        restore_editor_ui_render_state();
        draw_rectangle_lines(
            item.x,
            item.y,
            item.w,
            item.h,
            if index == document.selected_frame {
                3.0
            } else {
                1.0
            },
            if index == document.selected_frame {
                GOOD
            } else {
                PANEL_EDGE
            },
        );
        draw_editor_text(
            &format!("{} | {}ms", index + 1, frame.duration_ms),
            item.x + 4.0,
            item.y + item.h - 6.0,
            11.0,
            TEXT,
        );
        if !frame.events.is_empty() {
            draw_badge(
                Rect::new(item.x + item.w - 19.0, item.y + 4.0, 15.0, 15.0),
                "E",
                true,
            );
        }
        if !frame.sockets.is_empty() {
            draw_badge(
                Rect::new(item.x + item.w - 37.0, item.y + 4.0, 15.0, 15.0),
                "S",
                true,
            );
        }
    }
    if clip.frames.len() > 12 {
        draw_scissored_text(
            &format!("+{} more frames", clip.frames.len() - 12),
            start_x,
            y + 84.0,
            rect.w - 20.0,
            13.0,
            MUTED,
        );
    }
}

fn draw_source_grid(document: &AnimationDocument, image_rect: Rect) {
    let scale_x = image_rect.w / document.metadata.image_width.max(1) as f32;
    let scale_y = image_rect.h / document.metadata.image_height.max(1) as f32;
    let frame_width = document.metadata.frame_width.max(1) as i32;
    let frame_height = document.metadata.frame_height.max(1) as i32;
    let mut x = document.metadata.grid_offset[0];
    while x <= document.metadata.image_width as i32 {
        if x >= 0 {
            let screen_x = image_rect.x + x as f32 * scale_x;
            draw_line(
                screen_x,
                image_rect.y,
                screen_x,
                image_rect.y + image_rect.h,
                1.0,
                WARN,
            );
        }
        x += frame_width;
    }
    let mut y = document.metadata.grid_offset[1];
    while y <= document.metadata.image_height as i32 {
        if y >= 0 {
            let screen_y = image_rect.y + y as f32 * scale_y;
            draw_line(
                image_rect.x,
                screen_y,
                image_rect.x + image_rect.w,
                screen_y,
                1.0,
                WARN,
            );
        }
        y += frame_height;
    }
}

fn draw_animation_checkerboard(rect: Rect, cell: f32) {
    let columns = (rect.w / cell).ceil() as i32;
    let rows = (rect.h / cell).ceil() as i32;
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
                cell,
                cell,
                color,
            );
        }
    }
}

pub(crate) fn fit_image_rect(rect: Rect, width: u32, height: u32, padding: f32) -> Rect {
    let available_w = (rect.w - padding * 2.0).max(1.0);
    let available_h = (rect.h - padding * 2.0).max(1.0);
    let scale = (available_w / width.max(1) as f32)
        .min(available_h / height.max(1) as f32)
        .max(0.001);
    let w = width as f32 * scale;
    let h = height as f32 * scale;
    Rect::new(
        rect.x + (rect.w - w) * 0.5,
        rect.y + (rect.h - h) * 0.5,
        w,
        h,
    )
}

fn socket_color(kind: AnimationSocketKind) -> Color {
    match kind {
        AnimationSocketKind::MainHand => Color::new(1.0, 0.45, 0.30, 1.0),
        AnimationSocketKind::OffHand => Color::new(0.95, 0.75, 0.30, 1.0),
        AnimationSocketKind::Tool => Color::new(0.40, 0.85, 0.95, 1.0),
        AnimationSocketKind::Head => Color::new(0.70, 0.45, 0.95, 1.0),
        AnimationSocketKind::Back => Color::new(0.45, 0.75, 0.95, 1.0),
        AnimationSocketKind::Mouth => Color::new(0.95, 0.45, 0.65, 1.0),
        AnimationSocketKind::Ground => Color::new(0.45, 0.95, 0.55, 1.0),
        AnimationSocketKind::Interaction => Color::new(0.95, 0.95, 0.45, 1.0),
        AnimationSocketKind::Hinge => Color::new(1.00, 0.30, 0.25, 1.0),
        AnimationSocketKind::Handle => Color::new(1.00, 0.70, 0.25, 1.0),
        AnimationSocketKind::Effect => Color::new(0.65, 0.45, 1.00, 1.0),
        AnimationSocketKind::Impact => Color::new(1.00, 0.25, 0.55, 1.0),
    }
}

pub(crate) fn animation_toolbar_rect(host: Rect) -> Rect {
    Rect::new(host.x + 8.0, host.y + 8.0, host.w - 16.0, 34.0)
}
pub(crate) fn animation_source_rect(host: Rect) -> Rect {
    Rect::new(
        host.x + 8.0,
        host.y + 48.0,
        host.w * 0.57 - 12.0,
        host.h - 202.0,
    )
}
pub(crate) fn animation_preview_rect(host: Rect) -> Rect {
    Rect::new(
        host.x + host.w * 0.57,
        host.y + 48.0,
        host.w * 0.43 - 8.0,
        host.h - 202.0,
    )
}
pub(crate) fn animation_timeline_rect(host: Rect) -> Rect {
    Rect::new(host.x + 8.0, host.y + host.h - 146.0, host.w - 16.0, 138.0)
}

pub(crate) fn animation_refresh_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + 34.0, 104.0, 30.0)
}
pub(crate) fn animation_open_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + 112.0, rect.y + 34.0, 104.0, 30.0)
}
pub(crate) fn animation_library_category_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + 70.0, rect.w, 26.0)
}
pub(crate) fn animation_library_grid_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + 102.0, rect.w, (rect.h - 106.0).max(1.0))
}
pub(crate) fn animation_play_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y, 68.0, 30.0)
}
pub(crate) fn animation_prev_frame_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + 74.0, rect.y, 58.0, 30.0)
}
pub(crate) fn animation_next_frame_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + 138.0, rect.y, 58.0, 30.0)
}
pub(crate) fn animation_add_frame_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + 204.0, rect.y, 74.0, 30.0)
}
pub(crate) fn animation_duplicate_frame_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + 284.0, rect.y, 82.0, 30.0)
}
pub(crate) fn animation_delete_frame_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + 372.0, rect.y, 66.0, 30.0)
}
pub(crate) fn animation_move_left_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + 444.0, rect.y, 68.0, 30.0)
}
pub(crate) fn animation_move_right_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + 518.0, rect.y, 68.0, 30.0)
}
pub(crate) fn animation_onion_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + rect.w - 146.0, rect.y, 66.0, 30.0)
}
pub(crate) fn animation_grid_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + rect.w - 74.0, rect.y, 66.0, 30.0)
}
pub(crate) fn animation_timeline_frame_rect(rect: Rect, index: usize) -> Rect {
    Rect::new(
        rect.x + 10.0 + index as f32 * 76.0,
        rect.y + 30.0,
        70.0,
        92.0,
    )
}

fn animation_inspector_grid(rect: Rect, y: f32, columns: usize, height: f32) -> UiGrid {
    UiGrid::new(
        UiRect::new(rect.x, rect.y + y, rect.w, height),
        columns,
        6.0,
        height,
    )
}

fn animation_inspector_cell(rect: Rect, y: f32, columns: usize, index: usize, height: f32) -> Rect {
    let cell = animation_inspector_grid(rect, y, columns, height).cell(index);
    Rect::new(cell.x, cell.y, cell.width, cell.height)
}

pub(crate) fn animation_clip_prev_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 88.0, 4, 0, 30.0)
}
pub(crate) fn animation_clip_next_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 88.0, 4, 1, 30.0)
}
pub(crate) fn animation_clip_add_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 88.0, 4, 2, 30.0)
}
pub(crate) fn animation_clip_delete_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 88.0, 4, 3, 30.0)
}
pub(crate) fn animation_direction_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 160.0, 2, 0, 30.0)
}
pub(crate) fn animation_loop_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 160.0, 2, 1, 30.0)
}
pub(crate) fn animation_profile_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 198.0, 2, 0, 30.0)
}
pub(crate) fn animation_slice_row_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 198.0, 2, 1, 30.0)
}
pub(crate) fn animation_frame_width_down_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 234.0, 4, 0, 30.0)
}
pub(crate) fn animation_frame_width_up_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 234.0, 4, 1, 30.0)
}
pub(crate) fn animation_frame_height_down_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 234.0, 4, 2, 30.0)
}
pub(crate) fn animation_frame_height_up_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 234.0, 4, 3, 30.0)
}
pub(crate) fn animation_duration_down_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 306.0, 2, 0, 30.0)
}
pub(crate) fn animation_duration_up_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 306.0, 2, 1, 30.0)
}
pub(crate) fn animation_pivot_mode_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 342.0, 3, 0, 30.0)
}
pub(crate) fn animation_pivot_bottom_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 342.0, 3, 1, 30.0)
}
pub(crate) fn animation_hinge_pivot_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 342.0, 3, 2, 30.0)
}
pub(crate) fn animation_shadow_mode_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 378.0, 2, 0, 30.0)
}
pub(crate) fn animation_shadow_reset_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 378.0, 2, 1, 30.0)
}
pub(crate) fn animation_socket_prev_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 438.0, 4, 0, 30.0)
}
// W72D1: inspector label hit-targets are shared by animation input and rendering.
pub(crate) fn animation_socket_label_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 438.0, 4, 1, 30.0)
}
pub(crate) fn animation_socket_next_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 438.0, 4, 2, 30.0)
}
pub(crate) fn animation_socket_mode_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 438.0, 4, 3, 30.0)
}
pub(crate) fn animation_event_prev_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 482.0, 4, 0, 30.0)
}
pub(crate) fn animation_event_label_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 482.0, 4, 1, 30.0)
}
pub(crate) fn animation_event_next_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 482.0, 4, 2, 30.0)
}
pub(crate) fn animation_event_toggle_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 482.0, 4, 3, 30.0)
}
pub(crate) fn animation_edit_pixels_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 520.0, 1, 0, 28.0)
}
pub(crate) fn animation_save_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 564.0, 2, 0, 34.0)
}
pub(crate) fn animation_publish_rect(rect: Rect) -> Rect {
    animation_inspector_cell(rect, 564.0, 2, 1, 34.0)
}


fn draw_animation_gameplay_guides(frame: &haven_pixel::AnimationFrame, destination: Rect) {
    let sx = destination.w / frame.source.width.max(1) as f32;
    let sy = destination.h / frame.source.height.max(1) as f32;
    let foot_x = destination.x + (frame.foot_anchor[0] as f32 + 0.5) * sx;
    let foot_y = destination.y + (frame.foot_anchor[1] as f32 + 0.5) * sy;
    draw_line(foot_x - 7.0, foot_y, foot_x + 7.0, foot_y, 2.0, GOOD);
    draw_line(foot_x, foot_y - 7.0, foot_x, foot_y + 7.0, 2.0, GOOD);
    for bounds in &frame.hitboxes {
        draw_rectangle_lines(destination.x + bounds.x as f32 * sx, destination.y + bounds.y as f32 * sy, bounds.width as f32 * sx, bounds.height as f32 * sy, 2.0, WARN);
    }
    for bounds in &frame.hurtboxes {
        draw_rectangle_lines(destination.x + bounds.x as f32 * sx, destination.y + bounds.y as f32 * sy, bounds.width as f32 * sx, bounds.height as f32 * sy, 2.0, ACCENT);
    }
}
