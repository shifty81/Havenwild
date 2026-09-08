use std::collections::VecDeque;

use macroquad::prelude::*;

use super::Game;
use crate::runtime_ui_theme::{fit_runtime_label, ui_brass, ui_muted, ui_panel_fill, ui_parchment, ui_teal};

const CHAT_MAX_MESSAGES: usize = 96;
const CHAT_VISIBLE_MESSAGES: usize = 6;
const CHAT_WIDTH: f32 = 390.0;
const CHAT_HEIGHT: f32 = 154.0;

#[derive(Clone, Debug)]
pub(crate) struct RuntimeChatState {
    focused: bool,
    input: String,
    messages: VecDeque<String>,
    last_activity_at: f64,
}

impl Default for RuntimeChatState {
    fn default() -> Self {
        let mut messages = VecDeque::new();
        messages.push_back("Chat ready".to_string());
        Self {
            focused: false,
            input: String::new(),
            messages,
            last_activity_at: 0.0,
        }
    }
}

impl RuntimeChatState {
    pub(crate) fn focused(&self) -> bool {
        self.focused
    }

    fn push_message_at(&mut self, message: impl Into<String>, activity_at: f64) {
        self.messages.push_back(message.into());
        while self.messages.len() > CHAT_MAX_MESSAGES {
            self.messages.pop_front();
        }
        self.last_activity_at = activity_at;
    }

    fn push_message(&mut self, message: impl Into<String>) {
        self.push_message_at(message, get_time());
    }
}

impl Game {
    /// Returns true while chat owns gameplay input for this frame.
    pub(super) fn handle_runtime_chat_input(&mut self) -> bool {
        if self.runtime_chat.focused {
            if is_key_pressed(KeyCode::Escape) {
                self.runtime_chat.focused = false;
                self.runtime_chat.input.clear();
                return true;
            }
            if is_key_pressed(KeyCode::Enter) {
                let message = self.runtime_chat.input.trim().to_string();
                self.runtime_chat.input.clear();
                self.runtime_chat.focused = false;
                if !message.is_empty() {
                    let line = format!("You: {message}");
                    self.runtime_chat.push_message(line.clone());
                    self.log.event(&format!("Chat {line}"));
                }
                return true;
            }
            if is_key_pressed(KeyCode::Backspace) {
                self.runtime_chat.input.pop();
            }
            while let Some(character) = get_char_pressed() {
                if !character.is_control() && self.runtime_chat.input.chars().count() < 120 {
                    self.runtime_chat.input.push(character);
                }
            }
            return true;
        }

        if is_key_pressed(KeyCode::Enter) {
            self.runtime_chat.focused = true;
            self.runtime_chat.last_activity_at = get_time();
            return true;
        }
        false
    }

    pub(super) fn draw_runtime_chat(&self) {
        let rect = runtime_chat_rect();
        let now = get_time();
        let active = self.runtime_chat.focused
            || now - self.runtime_chat.last_activity_at < 8.0
            || self.runtime_chat.messages.len() <= 1;
        if active {
            draw_rectangle(rect.x, rect.y, rect.w, rect.h, Color::from_rgba(6, 13, 15, 188));
            draw_rectangle(rect.x, rect.y, 3.0, rect.h, ui_brass());
            draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 1.0, ui_teal());
        }

        let visible = self
            .runtime_chat
            .messages
            .iter()
            .rev()
            .take(CHAT_VISIBLE_MESSAGES)
            .collect::<Vec<_>>();
        let mut y = rect.y + 18.0;
        for line in visible.into_iter().rev() {
            draw_text(
                &fit_runtime_label(line, rect.w - 22.0, 12),
                rect.x + 10.0,
                y,
                12.0,
                if active { ui_parchment() } else { Color::from_rgba(218, 214, 190, 175) },
            );
            y += 18.0;
        }

        let input_rect = Rect::new(rect.x + 8.0, rect.y + rect.h - 31.0, rect.w - 16.0, 23.0);
        if self.runtime_chat.focused {
            draw_rectangle(input_rect.x, input_rect.y, input_rect.w, input_rect.h, ui_panel_fill());
            draw_rectangle_lines(input_rect.x, input_rect.y, input_rect.w, input_rect.h, 1.0, ui_brass());
            let text = if self.runtime_chat.input.is_empty() {
                "Type a message…".to_string()
            } else {
                self.runtime_chat.input.clone()
            };
            draw_text(
                &fit_runtime_label(&text, input_rect.w - 14.0, 13),
                input_rect.x + 7.0,
                input_rect.y + 16.0,
                13.0,
                if self.runtime_chat.input.is_empty() { ui_muted() } else { ui_parchment() },
            );
        } else {
            draw_text("Enter · Chat", input_rect.x + 2.0, input_rect.y + 16.0, 11.0, ui_muted());
        }
    }
}

pub(crate) fn runtime_chat_rect() -> Rect {
    let width = CHAT_WIDTH.min((screen_width() * 0.36).max(260.0));
    Rect::new(14.0, screen_height() - CHAT_HEIGHT - 14.0, width, CHAT_HEIGHT)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn chat_history_is_bounded() {
        let mut chat = RuntimeChatState::default();
        for index in 0..(CHAT_MAX_MESSAGES + 25) {
            chat.push_message_at(format!("message {index}"), index as f64);
        }
        assert_eq!(chat.messages.len(), CHAT_MAX_MESSAGES);
        assert_eq!(chat.last_activity_at, (CHAT_MAX_MESSAGES + 24) as f64);
    }
}
