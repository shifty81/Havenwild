fn title_screen_rect() -> Rect {
    let scale = (screen_width() / TITLE_SOURCE_W)
        .min(screen_height() / TITLE_SOURCE_H)
        .max(0.01);
    let width = TITLE_SOURCE_W * scale;
    let height = TITLE_SOURCE_H * scale;
    Rect::new(
        (screen_width() - width) * 0.5,
        (screen_height() - height) * 0.5,
        width,
        height,
    )
}

fn title_source_to_screen(rect: Rect) -> Rect {
    let screen = title_screen_rect();
    let scale = screen.w / TITLE_SOURCE_W;
    Rect::new(
        screen.x + rect.x * scale,
        screen.y + rect.y * scale,
        rect.w * scale,
        rect.h * scale,
    )
}

pub(crate) fn draw_title_menu_background(texture: Option<&Texture2D>) {
    clear_background(BLACK);
    let destination = title_screen_rect();
    if let Some(texture) = texture {
        draw_texture_ex(
            texture,
            destination.x,
            destination.y,
            WHITE,
            DrawTextureParams {
                dest_size: Some(vec2(destination.w, destination.h)),
                ..Default::default()
            },
        );
    } else {
        draw_ocean_background();
        draw_title("HAVENWILD");
    }
}

pub(crate) fn draw_frontend_backdrop(texture: Option<&Texture2D>) {
    draw_title_menu_background(texture);
    draw_rectangle(
        0.0,
        0.0,
        screen_width(),
        screen_height(),
        Color::from_rgba(8, 19, 22, 216),
    );
}

pub(crate) fn draw_title_menu_hover(
    texture: Option<&Texture2D>,
    source_rect: Rect,
    hit_rect: Rect,
    enabled: bool,
) {
    let hovered = enabled && hit_rect.contains(mouse_vec());
    let pressed = hovered && is_mouse_button_down(MouseButton::Left);
    if enabled && !hovered {
        return;
    }

    let Some(texture) = texture else {
        // The accepted scenic title already contains complete normal-state
        // artwork. Never fall back to a rectangular hover frame over it.
        return;
    };

    let mut destination = title_source_to_screen(source_rect);
    if pressed {
        destination.y += 2.0;
    }
    let tint = if enabled {
        WHITE
    } else {
        Color::from_rgba(0, 0, 0, 150)
    };
    draw_texture_ex(
        texture,
        destination.x,
        destination.y,
        tint,
        DrawTextureParams {
            dest_size: Some(vec2(destination.w, destination.h)),
            source: Some(source_rect),
            ..Default::default()
        },
    );
}

pub(crate) fn title_continue_visual_source() -> Rect {
    Rect::new(140.0, 310.0, 390.0, 115.0)
}

pub(crate) fn title_new_visual_source() -> Rect {
    Rect::new(140.0, 405.0, 390.0, 120.0)
}

pub(crate) fn title_load_visual_source() -> Rect {
    Rect::new(140.0, 500.0, 390.0, 115.0)
}

pub(crate) fn title_settings_visual_source() -> Rect {
    Rect::new(140.0, 595.0, 390.0, 115.0)
}

pub(crate) fn title_multiplayer_visual_source() -> Rect {
    Rect::new(140.0, 690.0, 390.0, 115.0)
}

pub(crate) fn title_quit_visual_source() -> Rect {
    Rect::new(140.0, 785.0, 390.0, 115.0)
}

pub(crate) fn main_continue_rect() -> Rect {
    title_source_to_screen(Rect::new(154.0, 320.0, 356.0, 92.0))
}

pub(crate) fn main_new_rect() -> Rect {
    title_source_to_screen(Rect::new(154.0, 416.0, 356.0, 92.0))
}

pub(crate) fn main_load_rect() -> Rect {
    title_source_to_screen(Rect::new(154.0, 513.0, 356.0, 90.0))
}

pub(crate) fn main_settings_rect() -> Rect {
    title_source_to_screen(Rect::new(154.0, 608.0, 356.0, 91.0))
}

pub(crate) fn main_multiplayer_rect() -> Rect {
    title_source_to_screen(Rect::new(154.0, 704.0, 356.0, 91.0))
}

pub(crate) fn main_quit_rect() -> Rect {
    title_source_to_screen(Rect::new(154.0, 799.0, 356.0, 92.0))
}

pub(crate) fn frontend_back_rect() -> Rect {
    Rect::new(
        screen_width() * 0.5 - 92.0,
        screen_height() - 78.0,
        184.0,
        44.0,
    )
}

pub(crate) fn character_card_rect(index: usize) -> Rect {
    let gap = 14.0;
    let width = ((screen_width() - 80.0) - gap * 4.0) / 5.0;
    Rect::new(40.0 + index as f32 * (width + gap), 150.0, width, 390.0)
}
pub(crate) fn character_edit_rect(card: Rect) -> Rect {
    Rect::new(card.x + 12.0, card.y + card.h - 30.0, card.w * 0.45, 24.0)
}
pub(crate) fn character_delete_rect(card: Rect) -> Rect {
    Rect::new(
        card.x + card.w * 0.53,
        card.y + card.h - 30.0,
        card.w * 0.39,
        24.0,
    )
}

#[derive(Clone, Copy)]
pub(crate) struct CreatorLayout {
    pub(crate) preview_panel: Rect,
    pub(crate) form_panel: Rect,
    pub(crate) identity_panel: Rect,
    pub(crate) appearance_panel: Rect,
    pub(crate) clothing_panel: Rect,
    pub(crate) actions_y: f32,
}

pub(crate) fn creator_layout() -> CreatorLayout {
    let margin = 28.0;
    let top = 94.0;
    let actions_h = 48.0;
    let actions_y = (screen_height() - actions_h - 24.0).max(704.0);
    let content_h = (actions_y - top - 16.0).max(520.0);
    let total_w = (screen_width() - margin * 2.0).min(1180.0);
    let left_w = (total_w * 0.36).clamp(350.0, 430.0);
    let gap = 16.0;
    let right_w = total_w - left_w - gap;
    let origin_x = (screen_width() - total_w) * 0.5;
    let preview_panel = Rect::new(origin_x, top, left_w, content_h);
    let form_panel = Rect::new(origin_x + left_w + gap, top, right_w, content_h);
    let inner = 14.0;
    let identity_h = 92.0;
    let identity_panel = Rect::new(
        form_panel.x + inner,
        form_panel.y + inner,
        form_panel.w - inner * 2.0,
        identity_h,
    );
    let section_y = identity_panel.y + identity_panel.h + 12.0;
    let section_h = form_panel.y + form_panel.h - inner - section_y;
    let section_gap = 12.0;
    let section_w = (form_panel.w - inner * 2.0 - section_gap) * 0.5;
    let appearance_panel = Rect::new(form_panel.x + inner, section_y, section_w, section_h);
    let clothing_panel = Rect::new(
        appearance_panel.x + section_w + section_gap,
        section_y,
        section_w,
        section_h,
    );
    CreatorLayout {
        preview_panel,
        form_panel,
        identity_panel,
        appearance_panel,
        clothing_panel,
        actions_y,
    }
}

pub(crate) fn creator_name_rect() -> Rect {
    let panel = creator_layout().identity_panel;
    Rect::new(panel.x + 96.0, panel.y + 42.0, panel.w - 112.0, 36.0)
}

fn option_slot(row: usize) -> (Rect, usize) {
    let layout = creator_layout();
    let (panel, local_row) = match row {
        0 => (layout.appearance_panel, 0),
        1 => (layout.appearance_panel, 1),
        6 => (layout.appearance_panel, 2),
        5 => (layout.appearance_panel, 3),
        2 => (layout.clothing_panel, 0),
        3 => (layout.clothing_panel, 1),
        4 => (layout.clothing_panel, 2),
        7 | 8 => (layout.preview_panel, row - 7),
        _ => (layout.appearance_panel, 0),
    };
    (panel, local_row)
}

pub(crate) fn creator_option_rect(row: usize) -> Rect {
    if row >= 7 {
        return if row == 7 {
            creator_preview_direction_rect()
        } else {
            creator_preview_animation_rect()
        };
    }
    let (panel, local_row) = option_slot(row);
    Rect::new(
        panel.x + 12.0,
        panel.y + 43.0 + local_row as f32 * 42.0,
        panel.w - 24.0,
        34.0,
    )
}

fn color_slot(row: usize) -> (Rect, usize) {
    let layout = creator_layout();
    match row {
        0 => (layout.appearance_panel, 4),
        1 => (layout.appearance_panel, 5),
        5 => (layout.appearance_panel, 6),
        2 => (layout.clothing_panel, 3),
        3 => (layout.clothing_panel, 4),
        4 => (layout.clothing_panel, 5),
        _ => (layout.appearance_panel, 4),
    }
}

pub(crate) fn creator_color_rect(row: usize) -> (Rect, Rect) {
    let (panel, local_row) = color_slot(row);
    let y = panel.y + 43.0 + local_row as f32 * 42.0;
    (
        Rect::new(panel.x + panel.w - 92.0, y + 2.0, 32.0, 30.0),
        Rect::new(panel.x + panel.w - 46.0, y + 2.0, 32.0, 30.0),
    )
}

pub(crate) fn draw_color_selector(row: usize, label: &str, palette: (&str, [u8; 4])) {
    let (panel, local_row) = color_slot(row);
    let y = panel.y + 43.0 + local_row as f32 * 42.0;
    draw_text(
        label,
        panel.x + 14.0,
        y + 23.0,
        15.0,
        Color::from_rgba(225, 216, 191, 255),
    );
    let (left, right) = creator_color_rect(row);
    let swatch = Rect::new(panel.x + panel.w - 174.0, y + 4.0, 70.0, 26.0);
    let color = Color::from_rgba(palette.1[0], palette.1[1], palette.1[2], palette.1[3]);
    draw_rectangle(swatch.x, swatch.y, swatch.w, swatch.h, color);
    draw_rectangle_lines(
        swatch.x,
        swatch.y,
        swatch.w,
        swatch.h,
        1.0,
        Color::from_rgba(228, 211, 170, 255),
    );
    draw_button(left, "<", false);
    draw_button(right, ">", false);
    let name_x = panel.x + 14.0;
    let name_y = y + 39.0;
    draw_text(
        palette.0,
        name_x,
        name_y,
        12.0,
        Color::from_rgba(168, 161, 145, 255),
    );
}

pub(crate) fn creator_preview_direction_rect() -> Rect {
    let panel = creator_layout().preview_panel;
    let width = (panel.w - 42.0) * 0.5;
    Rect::new(panel.x + 14.0, panel.y + panel.h - 58.0, width, 36.0)
}
pub(crate) fn creator_preview_animation_rect() -> Rect {
    let panel = creator_layout().preview_panel;
    let width = (panel.w - 42.0) * 0.5;
    Rect::new(
        panel.x + 28.0 + width,
        panel.y + panel.h - 58.0,
        width,
        36.0,
    )
}
pub(crate) fn creator_cancel_rect() -> Rect {
    let layout = creator_layout();
    Rect::new(screen_width() * 0.5 - 190.0, layout.actions_y, 170.0, 44.0)
}
pub(crate) fn creator_confirm_rect() -> Rect {
    let layout = creator_layout();
    Rect::new(screen_width() * 0.5 + 20.0, layout.actions_y, 210.0, 44.0)
}

pub(crate) fn world_card_rect(index: usize) -> Rect {
    Rect::new(
        90.0,
        155.0 + index as f32 * 132.0,
        screen_width() - 180.0,
        112.0,
    )
}
pub(crate) fn world_play_rect(card: Rect) -> Rect {
    Rect::new(card.x + card.w - 330.0, card.y + 38.0, 92.0, 38.0)
}
pub(crate) fn world_create_rect(card: Rect) -> Rect {
    Rect::new(card.x + card.w - 330.0, card.y + 38.0, 142.0, 38.0)
}
pub(crate) fn world_folder_rect(card: Rect) -> Rect {
    Rect::new(card.x + card.w - 226.0, card.y + 38.0, 92.0, 38.0)
}
pub(crate) fn world_delete_rect(card: Rect) -> Rect {
    Rect::new(card.x + card.w - 122.0, card.y + 38.0, 92.0, 38.0)
}

pub(crate) fn open_folder(path: &str, status: &mut String) {
    #[cfg(target_os = "windows")]
    let result = Command::new("explorer").arg(path).spawn();
    #[cfg(target_os = "macos")]
    let result = Command::new("open").arg(path).spawn();
    #[cfg(all(unix, not(target_os = "macos")))]
    let result = Command::new("xdg-open").arg(path).spawn();
    if let Err(error) = result {
        *status = format!("Could not open world folder: {error}");
    }
}
