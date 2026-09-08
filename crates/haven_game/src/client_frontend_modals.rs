#![allow(dead_code)]

use haven_save::{ClientSaveSlot, CURRENT_CLIENT_GENERATION_VERSION};
use macroquad::prelude::*;

use crate::client_character_frontend_draw::{draw_button, draw_text_centered};

pub(crate) fn draw_create_modal(slot: ClientSaveSlot, seed_text: &str) {
    let panel = modal_rect(520.0, 300.0);
    draw_modal_panel(panel, &format!("Create {}", slot.label()));
    draw_text(
        "World seed",
        panel.x + 28.0,
        panel.y + 92.0,
        20.0,
        Color::from_rgba(208, 218, 214, 255),
    );
    let input = Rect::new(panel.x + 28.0, panel.y + 108.0, panel.w - 56.0, 46.0);
    draw_rectangle(
        input.x,
        input.y,
        input.w,
        input.h,
        Color::from_rgba(10, 17, 21, 255),
    );
    draw_rectangle_lines(
        input.x,
        input.y,
        input.w,
        input.h,
        2.0,
        Color::from_rgba(104, 139, 128, 255),
    );
    draw_text(
        seed_text,
        input.x + 14.0,
        input.y + 31.0,
        24.0,
        Color::from_rgba(238, 232, 204, 255),
    );
    draw_text(
        "The seed controls island spacing and coastline structure for this playthrough.",
        panel.x + 28.0,
        panel.y + 186.0,
        16.0,
        Color::from_rgba(157, 176, 180, 255),
    );
    draw_button(create_randomize_rect(), "Randomize", false);
    draw_button(create_cancel_rect(), "Cancel", false);
    draw_button(create_confirm_rect(), "Create World", true);
}

pub(crate) fn draw_delete_modal(slot: ClientSaveSlot) {
    let panel = modal_rect(500.0, 220.0);
    draw_modal_panel(panel, "Delete gameplay save?");
    draw_text_centered(
        &format!(
            "{} and all of its generated world data will be removed.",
            slot.label()
        ),
        panel.x + panel.w * 0.5,
        panel.y + 104.0,
        17.0,
        Color::from_rgba(202, 207, 204, 255),
    );
    draw_button(delete_cancel_rect(), "Cancel", false);
    draw_button(delete_confirm_rect(), "Delete Save", false);
}

pub(crate) fn draw_regenerate_modal(slot: ClientSaveSlot, seed: u64) {
    let panel = modal_rect(560.0, 250.0);
    draw_modal_panel(panel, "Regenerate generated world?");
    draw_text_centered(
        &format!(
            "{} will be rebuilt from its existing seed {seed}.",
            slot.label()
        ),
        panel.x + panel.w * 0.5,
        panel.y + 100.0,
        17.0,
        Color::from_rgba(202, 211, 207, 255),
    );
    draw_text_centered(
        "This replaces the slot world, generated previews, edits, and current progress.",
        panel.x + panel.w * 0.5,
        panel.y + 130.0,
        16.0,
        Color::from_rgba(226, 160, 132, 255),
    );
    draw_text_centered(
        &format!(
            "The rebuilt slot will use coastline generation v{}.",
            CURRENT_CLIENT_GENERATION_VERSION
        ),
        panel.x + panel.w * 0.5,
        panel.y + 158.0,
        16.0,
        Color::from_rgba(157, 181, 183, 255),
    );
    draw_button(regenerate_cancel_rect(), "Cancel", false);
    draw_button(regenerate_confirm_rect(), "Regenerate", true);
}

fn draw_modal_panel(panel: Rect, title: &str) {
    draw_rectangle(
        panel.x,
        panel.y,
        panel.w,
        panel.h,
        Color::from_rgba(20, 29, 34, 255),
    );
    draw_rectangle_lines(
        panel.x,
        panel.y,
        panel.w,
        panel.h,
        2.0,
        Color::from_rgba(105, 132, 124, 255),
    );
    draw_text_centered(
        title,
        panel.x + panel.w * 0.5,
        panel.y + 52.0,
        28.0,
        Color::from_rgba(237, 228, 192, 255),
    );
}

fn modal_rect(width: f32, height: f32) -> Rect {
    Rect::new(
        (screen_width() - width) * 0.5,
        (screen_height() - height) * 0.5,
        width,
        height,
    )
}

pub(crate) fn create_randomize_rect() -> Rect {
    let panel = modal_rect(520.0, 300.0);
    Rect::new(panel.x + 28.0, panel.y + 232.0, 112.0, 40.0)
}

pub(crate) fn create_cancel_rect() -> Rect {
    let panel = modal_rect(520.0, 300.0);
    Rect::new(panel.x + panel.w - 244.0, panel.y + 232.0, 94.0, 40.0)
}

pub(crate) fn create_confirm_rect() -> Rect {
    let panel = modal_rect(520.0, 300.0);
    Rect::new(panel.x + panel.w - 140.0, panel.y + 232.0, 112.0, 40.0)
}

pub(crate) fn delete_cancel_rect() -> Rect {
    let panel = modal_rect(500.0, 220.0);
    Rect::new(panel.x + 132.0, panel.y + 154.0, 100.0, 40.0)
}

pub(crate) fn delete_confirm_rect() -> Rect {
    let panel = modal_rect(500.0, 220.0);
    Rect::new(panel.x + 246.0, panel.y + 154.0, 122.0, 40.0)
}

pub(crate) fn regenerate_cancel_rect() -> Rect {
    let panel = modal_rect(560.0, 250.0);
    Rect::new(panel.x + 160.0, panel.y + 190.0, 104.0, 40.0)
}

pub(crate) fn regenerate_confirm_rect() -> Rect {
    let panel = modal_rect(560.0, 250.0);
    Rect::new(panel.x + 278.0, panel.y + 190.0, 122.0, 40.0)
}
