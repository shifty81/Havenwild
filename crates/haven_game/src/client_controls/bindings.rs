use macroquad::prelude::MouseButton;
use serde::{Deserialize, Serialize};

const DEFAULT_STICK_DEADZONE: f32 = 0.22;

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub(crate) enum PromptStyle {
    Auto,
    KeyboardMouse,
    Controller,
}

impl PromptStyle {
    pub(crate) const ALL: [Self; 3] = [Self::Auto, Self::KeyboardMouse, Self::Controller];

    pub(crate) const fn label(self) -> &'static str {
        match self {
            Self::Auto => "Auto",
            Self::KeyboardMouse => "Keyboard & Mouse",
            Self::Controller => "Controller",
        }
    }
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub(crate) enum ActivePromptDevice {
    KeyboardMouse,
    Controller,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq, Hash)]
#[serde(rename_all = "snake_case")]
pub(crate) enum ControlAction {
    MoveUp,
    MoveDown,
    MoveLeft,
    MoveRight,
    Sprint,
    Interact,
    PrimaryAction,
    SecondaryAction,
    PreviousTool,
    NextTool,
    Inventory,
    Map,
    Rest,
    Emote,
    Pause,
    Confirm,
    Cancel,
}

impl ControlAction {
    pub(crate) const SETTINGS_ROWS: [Self; 17] = [
        Self::MoveUp,
        Self::MoveDown,
        Self::MoveLeft,
        Self::MoveRight,
        Self::Sprint,
        Self::Interact,
        Self::PrimaryAction,
        Self::SecondaryAction,
        Self::PreviousTool,
        Self::NextTool,
        Self::Inventory,
        Self::Map,
        Self::Rest,
        Self::Emote,
        Self::Pause,
        Self::Confirm,
        Self::Cancel,
    ];

    pub(crate) const fn label(self) -> &'static str {
        match self {
            Self::MoveUp => "Move Up",
            Self::MoveDown => "Move Down",
            Self::MoveLeft => "Move Left",
            Self::MoveRight => "Move Right",
            Self::Sprint => "Sprint",
            Self::Interact => "Interact",
            Self::PrimaryAction => "Use Tool / Primary",
            Self::SecondaryAction => "Secondary Action",
            Self::PreviousTool => "Previous Hotbar Slot",
            Self::NextTool => "Next Hotbar Slot",
            Self::Inventory => "Inventory",
            Self::Map => "World Map",
            Self::Rest => "Rest",
            Self::Emote => "Emote",
            Self::Pause => "Pause",
            Self::Confirm => "Confirm",
            Self::Cancel => "Cancel / Back",
        }
    }

    pub(crate) const fn controller_short_label(self) -> &'static str {
        match self {
            Self::MoveUp => "Move Up",
            Self::MoveDown => "Move Down",
            Self::MoveLeft => "Move Left",
            Self::MoveRight => "Move Right",
            Self::Sprint => "Sprint",
            Self::Interact => "Interact",
            Self::PrimaryAction => "Primary",
            Self::SecondaryAction => "Secondary",
            Self::PreviousTool => "Prev Slot",
            Self::NextTool => "Next Slot",
            Self::Inventory => "Inventory",
            Self::Map => "Map",
            Self::Rest => "Rest",
            Self::Emote => "Emote",
            Self::Pause => "Pause",
            Self::Confirm => "Confirm",
            Self::Cancel => "Cancel",
        }
    }
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub(crate) enum MouseBinding {
    Left,
    Right,
    Middle,
}

impl MouseBinding {
    pub(super) fn button(self) -> MouseButton {
        match self {
            Self::Left => MouseButton::Left,
            Self::Right => MouseButton::Right,
            Self::Middle => MouseButton::Middle,
        }
    }

    pub(crate) const fn label(self) -> &'static str {
        match self {
            Self::Left => "Mouse Left",
            Self::Right => "Mouse Right",
            Self::Middle => "Mouse Middle",
        }
    }
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub(crate) enum ControllerBinding {
    South,
    East,
    West,
    North,
    LeftShoulder,
    RightShoulder,
    LeftTrigger,
    RightTrigger,
    DpadUp,
    DpadDown,
    DpadLeft,
    DpadRight,
    Start,
    Back,
    LeftThumb,
    RightThumb,
}

impl ControllerBinding {
    pub(crate) const fn label(self) -> &'static str {
        match self {
            Self::South => "A / Cross",
            Self::East => "B / Circle",
            Self::West => "X / Square",
            Self::North => "Y / Triangle",
            Self::LeftShoulder => "LB / L1",
            Self::RightShoulder => "RB / R1",
            Self::LeftTrigger => "LT / L2",
            Self::RightTrigger => "RT / R2",
            Self::DpadUp => "D-Pad Up",
            Self::DpadDown => "D-Pad Down",
            Self::DpadLeft => "D-Pad Left",
            Self::DpadRight => "D-Pad Right",
            Self::Start => "Menu / Options",
            Self::Back => "View / Create",
            Self::LeftThumb => "Left Stick Click",
            Self::RightThumb => "Right Stick Click",
        }
    }

    pub(crate) const fn short_label(self) -> &'static str {
        match self {
            Self::South => "A",
            Self::East => "B",
            Self::West => "X",
            Self::North => "Y",
            Self::LeftShoulder => "LB",
            Self::RightShoulder => "RB",
            Self::LeftTrigger => "LT",
            Self::RightTrigger => "RT",
            Self::DpadUp => "D↑",
            Self::DpadDown => "D↓",
            Self::DpadLeft => "D←",
            Self::DpadRight => "D→",
            Self::Start => "Menu",
            Self::Back => "View",
            Self::LeftThumb => "LS",
            Self::RightThumb => "RS",
        }
    }

    pub(super) fn button_mask(self) -> Option<u16> {
        match self {
            Self::DpadUp => Some(0x0001),
            Self::DpadDown => Some(0x0002),
            Self::DpadLeft => Some(0x0004),
            Self::DpadRight => Some(0x0008),
            Self::Start => Some(0x0010),
            Self::Back => Some(0x0020),
            Self::LeftThumb => Some(0x0040),
            Self::RightThumb => Some(0x0080),
            Self::LeftShoulder => Some(0x0100),
            Self::RightShoulder => Some(0x0200),
            Self::South => Some(0x1000),
            Self::East => Some(0x2000),
            Self::West => Some(0x4000),
            Self::North => Some(0x8000),
            Self::LeftTrigger | Self::RightTrigger => None,
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub(crate) struct ActionBinding {
    pub keyboard_primary: Option<String>,
    pub keyboard_secondary: Option<String>,
    pub mouse: Option<MouseBinding>,
    pub controller: Option<ControllerBinding>,
}

impl ActionBinding {
    fn keyboard(primary: &str, secondary: Option<&str>, controller: ControllerBinding) -> Self {
        Self {
            keyboard_primary: Some(primary.to_string()),
            keyboard_secondary: secondary.map(str::to_string),
            mouse: None,
            controller: Some(controller),
        }
    }

    fn mouse(mouse: MouseBinding, keyboard: Option<&str>, controller: ControllerBinding) -> Self {
        Self {
            keyboard_primary: keyboard.map(str::to_string),
            keyboard_secondary: None,
            mouse: Some(mouse),
            controller: Some(controller),
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub(crate) struct ControlSettings {
    pub schema: String,
    pub prompt_style: PromptStyle,
    pub controller_deadzone: f32,
    pub vibration_strength: f32,
    pub bindings: Vec<(ControlAction, ActionBinding)>,
}

impl Default for ControlSettings {
    fn default() -> Self {
        Self {
            schema: "havenwild.client_controls.v0_1".to_string(),
            prompt_style: PromptStyle::Auto,
            controller_deadzone: DEFAULT_STICK_DEADZONE,
            vibration_strength: 0.70,
            bindings: vec![
                (ControlAction::MoveUp, ActionBinding::keyboard("W", Some("Up"), ControllerBinding::DpadUp)),
                (ControlAction::MoveDown, ActionBinding::keyboard("S", Some("Down"), ControllerBinding::DpadDown)),
                (ControlAction::MoveLeft, ActionBinding::keyboard("A", Some("Left"), ControllerBinding::DpadLeft)),
                (ControlAction::MoveRight, ActionBinding::keyboard("D", Some("Right"), ControllerBinding::DpadRight)),
                (ControlAction::Sprint, ActionBinding::keyboard("LeftShift", Some("RightShift"), ControllerBinding::LeftTrigger)),
                (ControlAction::Interact, ActionBinding::keyboard("F", None, ControllerBinding::South)),
                (ControlAction::PrimaryAction, ActionBinding::mouse(MouseBinding::Left, Some("C"), ControllerBinding::West)),
                (ControlAction::SecondaryAction, ActionBinding::mouse(MouseBinding::Right, Some("X"), ControllerBinding::East)),
                (ControlAction::PreviousTool, ActionBinding::keyboard("LeftBracket", None, ControllerBinding::LeftShoulder)),
                (ControlAction::NextTool, ActionBinding::keyboard("RightBracket", None, ControllerBinding::RightShoulder)),
                (ControlAction::Inventory, ActionBinding::keyboard("Tab", Some("I"), ControllerBinding::North)),
                (ControlAction::Map, ActionBinding::keyboard("M", None, ControllerBinding::Back)),
                (ControlAction::Rest, ActionBinding::keyboard("R", None, ControllerBinding::RightThumb)),
                (ControlAction::Emote, ActionBinding::keyboard("Y", None, ControllerBinding::LeftThumb)),
                (ControlAction::Pause, ActionBinding::keyboard("Escape", None, ControllerBinding::Start)),
                (ControlAction::Confirm, ActionBinding::keyboard("Enter", Some("Space"), ControllerBinding::South)),
                (ControlAction::Cancel, ActionBinding::keyboard("Escape", None, ControllerBinding::East)),
            ],
        }
    }
}

impl ControlSettings {
    pub(super) fn binding(&self, action: ControlAction) -> Option<&ActionBinding> {
        self.bindings.iter().find_map(|(candidate, binding)| (*candidate == action).then_some(binding))
    }

    pub(super) fn binding_mut(&mut self, action: ControlAction) -> Option<&mut ActionBinding> {
        self.bindings.iter_mut().find_map(|(candidate, binding)| (*candidate == action).then_some(binding))
    }

    pub(crate) fn reset_defaults(&mut self) {
        *self = Self::default();
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum RebindDevice {
    KeyboardMouse,
    Controller,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct RebindCapture {
    pub action: ControlAction,
    pub device: RebindDevice,
}

