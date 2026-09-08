use macroquad::prelude::*;
use std::path::{Path, PathBuf};

use crate::runtime_config::runtime_path;

mod bindings;

pub(crate) use bindings::{
    ControlAction, ControlSettings, ControllerBinding, PromptStyle, RebindCapture, RebindDevice,
};
use bindings::{ActivePromptDevice, MouseBinding};

const CONTROL_SETTINGS_PATH: &str = "WORKSPACE/client/control_settings.json";
const TRIGGER_THRESHOLD: f32 = 0.35;

#[derive(Clone, Copy, Debug, Default)]
struct ControllerSnapshot {
    connected: bool,
    buttons: u16,
    left_trigger: f32,
    right_trigger: f32,
    left_stick: Vec2,
    right_stick: Vec2,
}

pub(crate) struct ControlRuntime {
    pub settings: ControlSettings,
    pub active_prompt_device: ActivePromptDevice,
    settings_path: PathBuf,
    controller: ControllerSnapshot,
    previous_controller: ControllerSnapshot,
    capture: Option<RebindCapture>,
    capture_message: String,
    capture_input_consumed: bool,
    last_mouse_position: Vec2,
}

impl ControlRuntime {
    pub(crate) fn load() -> Self {
        let settings_path = PathBuf::from(runtime_path(CONTROL_SETTINGS_PATH));
        let settings = std::fs::read_to_string(&settings_path)
            .ok()
            .and_then(|source| serde_json::from_str::<ControlSettings>(&source).ok())
            .filter(valid_settings)
            .unwrap_or_default();
        let mouse = mouse_position();
        Self {
            settings,
            active_prompt_device: ActivePromptDevice::KeyboardMouse,
            settings_path,
            controller: ControllerSnapshot::default(),
            previous_controller: ControllerSnapshot::default(),
            capture: None,
            capture_message: String::new(),
            capture_input_consumed: false,
            last_mouse_position: vec2(mouse.0, mouse.1),
        }
    }

    pub(crate) fn save(&self) -> Result<(), String> {
        let parent = self
            .settings_path
            .parent()
            .ok_or_else(|| "control settings path has no parent".to_string())?;
        std::fs::create_dir_all(parent)
            .map_err(|error| format!("failed to create {}: {error}", parent.display()))?;
        let payload = serde_json::to_string_pretty(&self.settings).map_err(|error| error.to_string())?;
        atomic_write(&self.settings_path, payload.as_bytes())
    }

    pub(crate) fn poll(&mut self) {
        self.capture_input_consumed = false;
        self.previous_controller = self.controller;
        self.controller = poll_controller();

        let current_mouse = vec2(mouse_position().0, mouse_position().1);
        let mouse_moved = (current_mouse - self.last_mouse_position).length_squared() > 0.25;
        self.last_mouse_position = current_mouse;
        let keyboard_or_mouse_used = !get_keys_pressed().is_empty()
            || is_mouse_button_down(MouseButton::Left)
            || is_mouse_button_down(MouseButton::Right)
            || mouse_moved
            || mouse_wheel().1.abs() > f32::EPSILON;
        let controller_used = self.controller_activity();

        if controller_used {
            self.active_prompt_device = ActivePromptDevice::Controller;
        } else if keyboard_or_mouse_used {
            self.active_prompt_device = ActivePromptDevice::KeyboardMouse;
        }

        if self.capture.is_some() {
            self.poll_rebind_capture();
        }
    }

    pub(crate) fn controller_connected(&self) -> bool {
        self.controller.connected
    }

    pub(crate) fn prompt_device(&self) -> ActivePromptDevice {
        match self.settings.prompt_style {
            PromptStyle::Auto => self.active_prompt_device,
            PromptStyle::KeyboardMouse => ActivePromptDevice::KeyboardMouse,
            PromptStyle::Controller => ActivePromptDevice::Controller,
        }
    }

    pub(crate) fn cycle_prompt_style(&mut self, direction: i32) {
        let index = PromptStyle::ALL
            .iter()
            .position(|value| *value == self.settings.prompt_style)
            .unwrap_or(0);
        let next = (index as i32 + direction).rem_euclid(PromptStyle::ALL.len() as i32) as usize;
        self.settings.prompt_style = PromptStyle::ALL[next];
        let _ = self.save();
    }

    pub(crate) fn movement_vector(&self) -> Vec2 {
        let mut value = Vec2::ZERO;
        if self.keyboard_down(ControlAction::MoveLeft) {
            value.x -= 1.0;
        }
        if self.keyboard_down(ControlAction::MoveRight) {
            value.x += 1.0;
        }
        if self.keyboard_down(ControlAction::MoveUp) {
            value.y -= 1.0;
        }
        if self.keyboard_down(ControlAction::MoveDown) {
            value.y += 1.0;
        }

        if self.controller.connected {
            let stick = apply_deadzone(self.controller.left_stick, self.settings.controller_deadzone);
            value += vec2(stick.x, -stick.y);
            if self.controller_down(ControllerBinding::DpadLeft) {
                value.x -= 1.0;
            }
            if self.controller_down(ControllerBinding::DpadRight) {
                value.x += 1.0;
            }
            if self.controller_down(ControllerBinding::DpadUp) {
                value.y -= 1.0;
            }
            if self.controller_down(ControllerBinding::DpadDown) {
                value.y += 1.0;
            }
        }
        if value.length_squared() > 1.0 {
            value.normalize()
        } else {
            value
        }
    }

    pub(crate) fn action_down(&self, action: ControlAction) -> bool {
        self.keyboard_down(action)
            || self.mouse_down(action)
            || self
                .settings
                .binding(action)
                .and_then(|binding| binding.controller)
                .is_some_and(|binding| self.controller_down(binding))
    }

    pub(crate) fn action_pressed(&self, action: ControlAction) -> bool {
        self.keyboard_pressed(action)
            || self.mouse_pressed(action)
            || self
                .settings
                .binding(action)
                .and_then(|binding| binding.controller)
                .is_some_and(|binding| self.controller_pressed(binding))
    }

    pub(crate) fn menu_vertical_delta(&self) -> i32 {
        if self.action_pressed(ControlAction::MoveUp) || self.left_stick_direction_pressed(0.0, 1.0) {
            -1
        } else if self.action_pressed(ControlAction::MoveDown) || self.left_stick_direction_pressed(0.0, -1.0) {
            1
        } else {
            0
        }
    }

    pub(crate) fn menu_horizontal_delta(&self) -> i32 {
        if self.action_pressed(ControlAction::MoveLeft) || self.left_stick_direction_pressed(-1.0, 0.0) {
            -1
        } else if self.action_pressed(ControlAction::MoveRight) || self.left_stick_direction_pressed(1.0, 0.0) {
            1
        } else {
            0
        }
    }

    pub(crate) fn hotbar_delta(&self) -> i32 {
        let wheel = mouse_wheel().1;
        if wheel > f32::EPSILON || self.action_pressed(ControlAction::PreviousTool) {
            -1
        } else if wheel < -f32::EPSILON || self.action_pressed(ControlAction::NextTool) {
            1
        } else {
            0
        }
    }

    pub(crate) fn begin_rebind(&mut self, action: ControlAction, device: RebindDevice) {
        self.capture = Some(RebindCapture { action, device });
        self.capture_message = match device {
            RebindDevice::KeyboardMouse => format!("Press a key or mouse button for {}", action.label()),
            RebindDevice::Controller => format!("Press a controller button for {}", action.label()),
        };
    }

    pub(crate) fn rebind_capture(&self) -> Option<RebindCapture> {
        self.capture
    }

    pub(crate) fn capture_message(&self) -> &str {
        &self.capture_message
    }

    pub(crate) fn rebind_input_consumed(&self) -> bool {
        self.capture_input_consumed
    }

    pub(crate) fn cancel_rebind(&mut self) {
        self.capture = None;
        self.capture_message.clear();
        self.capture_input_consumed = true;
    }

    pub(crate) fn reset_defaults(&mut self) {
        self.settings.reset_defaults();
        let _ = self.save();
    }

    pub(crate) fn keyboard_binding_label(&self, action: ControlAction) -> String {
        let Some(binding) = self.settings.binding(action) else {
            return "Unbound".to_string();
        };
        let mut parts = Vec::new();
        if let Some(primary) = binding.keyboard_primary.as_deref() {
            parts.push(key_label(primary));
        }
        if let Some(secondary) = binding.keyboard_secondary.as_deref() {
            parts.push(key_label(secondary));
        }
        if let Some(mouse) = binding.mouse {
            parts.push(mouse.label().to_string());
        }
        if parts.is_empty() {
            "Unbound".to_string()
        } else {
            parts.join(" / ")
        }
    }

    pub(crate) fn controller_binding_label(&self, action: ControlAction) -> String {
        self.settings
            .binding(action)
            .and_then(|binding| binding.controller)
            .map(ControllerBinding::label)
            .unwrap_or("Unbound")
            .to_string()
    }

    pub(crate) fn controller_actions_label(&self, binding: ControllerBinding) -> String {
        let mut labels = self
            .settings
            .bindings
            .iter()
            .filter_map(|(action, candidate)| {
                (candidate.controller == Some(binding)).then_some(action.controller_short_label())
            })
            .collect::<Vec<_>>();
        labels.dedup();
        if labels.is_empty() {
            "Unbound".to_string()
        } else {
            labels.join(" / ")
        }
    }

    pub(crate) fn action_uses_controller_binding(
        &self,
        action: ControlAction,
        binding: ControllerBinding,
    ) -> bool {
        self.settings
            .binding(action)
            .and_then(|candidate| candidate.controller)
            == Some(binding)
    }

    pub(crate) fn prompt_label(&self, action: ControlAction) -> String {
        match self.prompt_device() {
            ActivePromptDevice::KeyboardMouse => self.keyboard_binding_label(action),
            ActivePromptDevice::Controller => self.controller_binding_label(action),
        }
    }

    pub(crate) fn adjust_deadzone(&mut self, delta: f32) {
        self.settings.controller_deadzone = (self.settings.controller_deadzone + delta).clamp(0.05, 0.55);
        let _ = self.save();
    }

    fn keyboard_down(&self, action: ControlAction) -> bool {
        self.settings.binding(action).is_some_and(|binding| {
            binding
                .keyboard_primary
                .as_deref()
                .and_then(key_code_from_name)
                .is_some_and(is_key_down)
                || binding
                    .keyboard_secondary
                    .as_deref()
                    .and_then(key_code_from_name)
                    .is_some_and(is_key_down)
        })
    }

    fn keyboard_pressed(&self, action: ControlAction) -> bool {
        self.settings.binding(action).is_some_and(|binding| {
            binding
                .keyboard_primary
                .as_deref()
                .and_then(key_code_from_name)
                .is_some_and(is_key_pressed)
                || binding
                    .keyboard_secondary
                    .as_deref()
                    .and_then(key_code_from_name)
                    .is_some_and(is_key_pressed)
        })
    }

    fn mouse_down(&self, action: ControlAction) -> bool {
        self.settings
            .binding(action)
            .and_then(|binding| binding.mouse)
            .is_some_and(|binding| is_mouse_button_down(binding.button()))
    }

    fn mouse_pressed(&self, action: ControlAction) -> bool {
        self.settings
            .binding(action)
            .and_then(|binding| binding.mouse)
            .is_some_and(|binding| is_mouse_button_pressed(binding.button()))
    }

    fn controller_down(&self, binding: ControllerBinding) -> bool {
        if !self.controller.connected {
            return false;
        }
        match binding {
            ControllerBinding::LeftTrigger => self.controller.left_trigger >= TRIGGER_THRESHOLD,
            ControllerBinding::RightTrigger => self.controller.right_trigger >= TRIGGER_THRESHOLD,
            _ => binding
                .button_mask()
                .is_some_and(|mask| self.controller.buttons & mask != 0),
        }
    }

    fn controller_pressed(&self, binding: ControllerBinding) -> bool {
        if !self.controller.connected {
            return false;
        }
        match binding {
            ControllerBinding::LeftTrigger => {
                self.controller.left_trigger >= TRIGGER_THRESHOLD
                    && self.previous_controller.left_trigger < TRIGGER_THRESHOLD
            }
            ControllerBinding::RightTrigger => {
                self.controller.right_trigger >= TRIGGER_THRESHOLD
                    && self.previous_controller.right_trigger < TRIGGER_THRESHOLD
            }
            _ => binding.button_mask().is_some_and(|mask| {
                self.controller.buttons & mask != 0 && self.previous_controller.buttons & mask == 0
            }),
        }
    }

    fn left_stick_direction_pressed(&self, x: f32, y: f32) -> bool {
        if !self.controller.connected {
            return false;
        }
        const MENU_AXIS_THRESHOLD: f32 = 0.62;
        let current = self.controller.left_stick.x * x + self.controller.left_stick.y * y;
        let previous = self.previous_controller.left_stick.x * x
            + self.previous_controller.left_stick.y * y;
        current >= MENU_AXIS_THRESHOLD && previous < MENU_AXIS_THRESHOLD
    }

    fn controller_activity(&self) -> bool {
        self.controller.connected
            && (self.controller.buttons != self.previous_controller.buttons
                || (self.controller.left_stick - self.previous_controller.left_stick).length_squared() > 0.0025
                || (self.controller.right_stick - self.previous_controller.right_stick).length_squared() > 0.0025
                || (self.controller.left_trigger - self.previous_controller.left_trigger).abs() > 0.04
                || (self.controller.right_trigger - self.previous_controller.right_trigger).abs() > 0.04)
    }

    fn poll_rebind_capture(&mut self) {
        let Some(capture) = self.capture else {
            return;
        };
        let mut completed = false;
        match capture.device {
            RebindDevice::KeyboardMouse => {
                if is_mouse_button_pressed(MouseButton::Left) {
                    if let Some(binding) = self.settings.binding_mut(capture.action) {
                        binding.mouse = Some(MouseBinding::Left);
                        binding.keyboard_primary = None;
                    }
                    completed = true;
                } else if is_mouse_button_pressed(MouseButton::Right) {
                    if let Some(binding) = self.settings.binding_mut(capture.action) {
                        binding.mouse = Some(MouseBinding::Right);
                        binding.keyboard_primary = None;
                    }
                    completed = true;
                } else if is_mouse_button_pressed(MouseButton::Middle) {
                    if let Some(binding) = self.settings.binding_mut(capture.action) {
                        binding.mouse = Some(MouseBinding::Middle);
                        binding.keyboard_primary = None;
                    }
                    completed = true;
                } else if let Some(key) = get_last_key_pressed() {
                    if key == KeyCode::Escape {
                        self.cancel_rebind();
                        return;
                    }
                    let name = format!("{key:?}");
                    if key_code_from_name(&name).is_some() {
                        if let Some(binding) = self.settings.binding_mut(capture.action) {
                            binding.keyboard_primary = Some(name);
                            binding.mouse = None;
                        }
                        completed = true;
                    } else {
                        self.capture_message = format!("That key is not bindable yet; press another key for {}", capture.action.label());
                    }
                }
            }
            RebindDevice::Controller => {
                for candidate in CONTROLLER_CAPTURE_ORDER {
                    if self.controller_pressed(candidate) {
                        if let Some(binding) = self.settings.binding_mut(capture.action) {
                            binding.controller = Some(candidate);
                        }
                        completed = true;
                        break;
                    }
                }
            }
        }
        if completed {
            let _ = self.save();
            self.capture = None;
            self.capture_message.clear();
            self.capture_input_consumed = true;
        }
    }
}

const CONTROLLER_CAPTURE_ORDER: [ControllerBinding; 16] = [
    ControllerBinding::South,
    ControllerBinding::East,
    ControllerBinding::West,
    ControllerBinding::North,
    ControllerBinding::LeftShoulder,
    ControllerBinding::RightShoulder,
    ControllerBinding::LeftTrigger,
    ControllerBinding::RightTrigger,
    ControllerBinding::DpadUp,
    ControllerBinding::DpadDown,
    ControllerBinding::DpadLeft,
    ControllerBinding::DpadRight,
    ControllerBinding::Start,
    ControllerBinding::Back,
    ControllerBinding::LeftThumb,
    ControllerBinding::RightThumb,
];

fn valid_settings(settings: &ControlSettings) -> bool {
    settings.schema == "havenwild.client_controls.v0_1"
        && (0.05..=0.55).contains(&settings.controller_deadzone)
        && ControlAction::SETTINGS_ROWS
            .iter()
            .all(|action| settings.binding(*action).is_some())
}

fn atomic_write(path: &Path, payload: &[u8]) -> Result<(), String> {
    let temp = path.with_extension("tmp");
    std::fs::write(&temp, payload)
        .map_err(|error| format!("failed to write {}: {error}", temp.display()))?;
    if path.exists() {
        std::fs::remove_file(path)
            .map_err(|error| format!("failed to replace {}: {error}", path.display()))?;
    }
    std::fs::rename(&temp, path)
        .map_err(|error| format!("failed to publish {}: {error}", path.display()))
}

fn apply_deadzone(value: Vec2, deadzone: f32) -> Vec2 {
    let magnitude = value.length();
    if magnitude <= deadzone {
        return Vec2::ZERO;
    }
    let normalized = ((magnitude - deadzone) / (1.0 - deadzone)).clamp(0.0, 1.0);
    if magnitude <= f32::EPSILON {
        Vec2::ZERO
    } else {
        value / magnitude * normalized
    }
}

fn key_label(name: &str) -> String {
    match name {
        "LeftShift" => "Left Shift".to_string(),
        "RightShift" => "Right Shift".to_string(),
        "LeftControl" => "Left Ctrl".to_string(),
        "RightControl" => "Right Ctrl".to_string(),
        "LeftAlt" => "Left Alt".to_string(),
        "RightAlt" => "Right Alt".to_string(),
        "LeftBracket" => "[".to_string(),
        "RightBracket" => "]".to_string(),
        value => value.to_string(),
    }
}

fn key_code_from_name(name: &str) -> Option<KeyCode> {
    Some(match name {
        "Space" => KeyCode::Space,
        "Apostrophe" => KeyCode::Apostrophe,
        "Comma" => KeyCode::Comma,
        "Minus" => KeyCode::Minus,
        "Period" => KeyCode::Period,
        "Slash" => KeyCode::Slash,
        "Key0" => KeyCode::Key0,
        "Key1" => KeyCode::Key1,
        "Key2" => KeyCode::Key2,
        "Key3" => KeyCode::Key3,
        "Key4" => KeyCode::Key4,
        "Key5" => KeyCode::Key5,
        "Key6" => KeyCode::Key6,
        "Key7" => KeyCode::Key7,
        "Key8" => KeyCode::Key8,
        "Key9" => KeyCode::Key9,
        "Semicolon" => KeyCode::Semicolon,
        "Equal" => KeyCode::Equal,
        "A" => KeyCode::A,
        "B" => KeyCode::B,
        "C" => KeyCode::C,
        "D" => KeyCode::D,
        "E" => KeyCode::E,
        "F" => KeyCode::F,
        "G" => KeyCode::G,
        "H" => KeyCode::H,
        "I" => KeyCode::I,
        "J" => KeyCode::J,
        "K" => KeyCode::K,
        "L" => KeyCode::L,
        "M" => KeyCode::M,
        "N" => KeyCode::N,
        "O" => KeyCode::O,
        "P" => KeyCode::P,
        "Q" => KeyCode::Q,
        "R" => KeyCode::R,
        "S" => KeyCode::S,
        "T" => KeyCode::T,
        "U" => KeyCode::U,
        "V" => KeyCode::V,
        "W" => KeyCode::W,
        "X" => KeyCode::X,
        "Y" => KeyCode::Y,
        "Z" => KeyCode::Z,
        "LeftBracket" => KeyCode::LeftBracket,
        "Backslash" => KeyCode::Backslash,
        "RightBracket" => KeyCode::RightBracket,
        "GraveAccent" => KeyCode::GraveAccent,
        "Escape" => KeyCode::Escape,
        "Enter" => KeyCode::Enter,
        "Tab" => KeyCode::Tab,
        "Backspace" => KeyCode::Backspace,
        "Insert" => KeyCode::Insert,
        "Delete" => KeyCode::Delete,
        "Right" => KeyCode::Right,
        "Left" => KeyCode::Left,
        "Down" => KeyCode::Down,
        "Up" => KeyCode::Up,
        "PageUp" => KeyCode::PageUp,
        "PageDown" => KeyCode::PageDown,
        "Home" => KeyCode::Home,
        "End" => KeyCode::End,
        "F1" => KeyCode::F1,
        "F2" => KeyCode::F2,
        "F3" => KeyCode::F3,
        "F4" => KeyCode::F4,
        "F5" => KeyCode::F5,
        "F6" => KeyCode::F6,
        "F7" => KeyCode::F7,
        "F8" => KeyCode::F8,
        "F9" => KeyCode::F9,
        "F10" => KeyCode::F10,
        "F11" => KeyCode::F11,
        "F12" => KeyCode::F12,
        "LeftShift" => KeyCode::LeftShift,
        "LeftControl" => KeyCode::LeftControl,
        "LeftAlt" => KeyCode::LeftAlt,
        "RightShift" => KeyCode::RightShift,
        "RightControl" => KeyCode::RightControl,
        "RightAlt" => KeyCode::RightAlt,
        _ => return None,
    })
}

#[cfg(target_os = "windows")]
fn poll_controller() -> ControllerSnapshot {
    xinput::poll_first_connected().unwrap_or_default()
}

#[cfg(not(target_os = "windows"))]
fn poll_controller() -> ControllerSnapshot {
    ControllerSnapshot::default()
}

#[cfg(target_os = "windows")]
mod xinput {
    use super::ControllerSnapshot;
    use macroquad::prelude::{vec2, Vec2};

    #[repr(C)]
    #[derive(Clone, Copy, Default)]
    struct XInputGamepad {
        buttons: u16,
        left_trigger: u8,
        right_trigger: u8,
        thumb_lx: i16,
        thumb_ly: i16,
        thumb_rx: i16,
        thumb_ry: i16,
    }

    #[repr(C)]
    #[derive(Clone, Copy, Default)]
    struct XInputState {
        packet_number: u32,
        gamepad: XInputGamepad,
    }

    #[link(name = "xinput9_1_0")]
    extern "system" {
        fn XInputGetState(user_index: u32, state: *mut XInputState) -> u32;
    }

    pub(super) fn poll_first_connected() -> Option<ControllerSnapshot> {
        for user_index in 0..4 {
            let mut state = XInputState::default();
            let result = unsafe { XInputGetState(user_index, &mut state as *mut XInputState) };
            if result == 0 {
                return Some(ControllerSnapshot {
                    connected: true,
                    buttons: state.gamepad.buttons,
                    left_trigger: state.gamepad.left_trigger as f32 / 255.0,
                    right_trigger: state.gamepad.right_trigger as f32 / 255.0,
                    left_stick: normalize_stick(state.gamepad.thumb_lx, state.gamepad.thumb_ly),
                    right_stick: normalize_stick(state.gamepad.thumb_rx, state.gamepad.thumb_ry),
                });
            }
        }
        None
    }

    fn normalize_stick(x: i16, y: i16) -> Vec2 {
        let normalize = |value: i16| {
            if value >= 0 {
                value as f32 / i16::MAX as f32
            } else {
                value as f32 / -(i16::MIN as f32)
            }
        };
        vec2(normalize(x), normalize(y))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn defaults_cover_every_settings_action() {
        let settings = ControlSettings::default();
        assert!(ControlAction::SETTINGS_ROWS
            .iter()
            .all(|action| settings.binding(*action).is_some()));
    }

    #[test]
    fn deadzone_preserves_full_scale_and_rejects_center_noise() {
        assert_eq!(apply_deadzone(Vec2::ZERO, 0.22), Vec2::ZERO);
        assert_eq!(apply_deadzone(vec2(0.1, 0.0), 0.22), Vec2::ZERO);
        let full = apply_deadzone(vec2(1.0, 0.0), 0.22);
        assert!((full.x - 1.0).abs() < 0.001);
    }
}
