fn layer_color(appearance: &CharacterAppearance, slot: &str, fallback: Color) -> Color {
    appearance
        .layers
        .iter()
        .find(|layer| layer.enabled && layer.slot == slot)
        .and_then(|layer| layer.tint_rgba)
        .map(|rgba| Color::from_rgba(rgba[0], rgba[1], rgba[2], rgba[3]))
        .unwrap_or(fallback)
}
pub(crate) fn draw_ocean_background() {
    clear_background(Color::from_rgba(12, 27, 35, 255));
    for index in 0..12 {
        let y = 70.0 + index as f32 * 54.0;
        draw_line(
            0.0,
            y,
            screen_width(),
            y + 18.0,
            1.0,
            Color::from_rgba(36, 69, 79, 110),
        );
    }
}

pub(crate) fn draw_title(text: &str) {
    let metrics = measure_text(text, None, 36, 1.0);
    let plaque = Rect::new(
        screen_width() * 0.5 - metrics.width * 0.5 - 34.0,
        24.0,
        metrics.width + 68.0,
        52.0,
    );
    draw_rectangle(
        plaque.x + 4.0,
        plaque.y + 5.0,
        plaque.w,
        plaque.h,
        Color::from_rgba(5, 9, 10, 150),
    );
    draw_rectangle(
        plaque.x,
        plaque.y,
        plaque.w,
        plaque.h,
        Color::from_rgba(76, 52, 34, 255),
    );
    draw_rectangle_lines(
        plaque.x,
        plaque.y,
        plaque.w,
        plaque.h,
        3.0,
        Color::from_rgba(177, 130, 72, 255),
    );
    draw_rectangle_lines(
        plaque.x + 6.0,
        plaque.y + 6.0,
        plaque.w - 12.0,
        plaque.h - 12.0,
        1.0,
        Color::from_rgba(31, 25, 20, 255),
    );
    draw_text_centered(
        text,
        screen_width() * 0.5,
        61.0,
        36.0,
        Color::from_rgba(250, 232, 187, 255),
    );
}

pub(crate) fn draw_panel(rect: Rect, selected: bool) {
    let shadow = Color::from_rgba(6, 12, 14, 150);
    draw_rectangle(rect.x + 5.0, rect.y + 6.0, rect.w, rect.h, shadow);
    let outer = if selected {
        Color::from_rgba(91, 63, 39, 255)
    } else {
        Color::from_rgba(69, 48, 33, 255)
    };
    let inner = if selected {
        Color::from_rgba(41, 61, 57, 248)
    } else {
        Color::from_rgba(31, 47, 45, 244)
    };
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, outer);
    draw_rectangle(
        rect.x + 5.0,
        rect.y + 5.0,
        rect.w - 10.0,
        rect.h - 10.0,
        inner,
    );
    draw_rectangle_lines(
        rect.x + 2.0,
        rect.y + 2.0,
        rect.w - 4.0,
        rect.h - 4.0,
        2.0,
        Color::from_rgba(159, 118, 67, 255),
    );
    draw_rectangle_lines(
        rect.x + 7.0,
        rect.y + 7.0,
        rect.w - 14.0,
        rect.h - 14.0,
        1.0,
        Color::from_rgba(27, 30, 25, 255),
    );
}

pub(crate) fn draw_section_panel(rect: Rect, title: &str) {
    draw_rectangle(
        rect.x,
        rect.y,
        rect.w,
        rect.h,
        Color::from_rgba(24, 38, 37, 238),
    );
    draw_rectangle_lines(
        rect.x,
        rect.y,
        rect.w,
        rect.h,
        2.0,
        Color::from_rgba(126, 88, 52, 255),
    );
    let header = Rect::new(rect.x + 5.0, rect.y + 5.0, rect.w - 10.0, 30.0);
    draw_rectangle(
        header.x,
        header.y,
        header.w,
        header.h,
        Color::from_rgba(76, 52, 35, 255),
    );
    draw_rectangle_lines(
        header.x,
        header.y,
        header.w,
        header.h,
        1.0,
        Color::from_rgba(181, 135, 76, 255),
    );
    draw_text(
        title,
        header.x + 12.0,
        header.y + 21.0,
        18.0,
        Color::from_rgba(244, 225, 178, 255),
    );
}

pub(crate) fn draw_button(rect: Rect, label: &str, primary: bool) {
    let hovered = rect.contains(mouse_vec());
    let fill = match (primary, hovered) {
        (true, true) => Color::from_rgba(79, 123, 65, 255),
        (true, false) => Color::from_rgba(58, 96, 51, 255),
        (false, true) => Color::from_rgba(105, 76, 48, 255),
        (false, false) => Color::from_rgba(74, 53, 38, 255),
    };
    draw_rectangle(
        rect.x + 2.0,
        rect.y + 3.0,
        rect.w,
        rect.h,
        Color::from_rgba(8, 12, 12, 150),
    );
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, fill);
    draw_rectangle_lines(
        rect.x,
        rect.y,
        rect.w,
        rect.h,
        2.0,
        Color::from_rgba(170, 126, 72, 255),
    );
    draw_rectangle_lines(
        rect.x + 4.0,
        rect.y + 4.0,
        rect.w - 8.0,
        rect.h - 8.0,
        1.0,
        Color::from_rgba(33, 28, 22, 255),
    );
    draw_text_centered(
        label,
        rect.x + rect.w * 0.5,
        rect.y + rect.h * 0.67,
        17.0,
        Color::from_rgba(250, 239, 211, 255),
    );
}

pub(crate) fn draw_text_centered(text: &str, x: f32, y: f32, size: f32, color: Color) {
    let metrics = measure_text(text, None, size as u16, 1.0);
    draw_text(text, x - metrics.width * 0.5, y, size, color);
}

pub(crate) fn mouse_vec() -> Vec2 {
    let (x, y) = mouse_position();
    vec2(x, y)
}

const TITLE_SOURCE_W: f32 = 1672.0;
const TITLE_SOURCE_H: f32 = 941.0;

