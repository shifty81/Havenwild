use serde::{Deserialize, Serialize};
use std::{collections::BTreeMap, fs, path::Path};

pub const UI_DOCUMENT_SCHEMA_V1: &str = "havenwild.ui_document.v1";
pub const TRANSITION_RESOURCE_SCHEMA_V1: &str = "havenwild.transition_resource.v1";

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum UiDocumentKind {
    Hud,
    Inventory,
    Crafting,
    Dialogue,
    Shop,
    Map,
    Settings,
    CharacterCreation,
    WorldCreation,
    Loading,
    Title,
    Pause,
    SaveSlots,
    MultiplayerLobby,
    Error,
    DeathRespawn,
    Travel,
    Custom,
}

impl UiDocumentKind {
    pub fn label(self) -> &'static str {
        match self {
            Self::Hud => "Gameplay HUD",
            Self::Inventory => "Inventory",
            Self::Crafting => "Crafting",
            Self::Dialogue => "Dialogue",
            Self::Shop => "Shop",
            Self::Map => "World Map",
            Self::Settings => "Settings",
            Self::CharacterCreation => "Character Creation",
            Self::WorldCreation => "World Creation",
            Self::Loading => "Loading Screen",
            Self::Title => "Title Screen",
            Self::Pause => "Pause",
            Self::SaveSlots => "Save Slots",
            Self::MultiplayerLobby => "Multiplayer Lobby",
            Self::Error => "Error",
            Self::DeathRespawn => "Death / Respawn",
            Self::Travel => "Travel",
            Self::Custom => "Custom UI",
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum UiAuthoringLane {
    Layout,
    Controls,
    Data,
    Behavior,
    Presentation,
    Overrides,
}

impl UiAuthoringLane {
    pub const ALL: [Self; 6] = [
        Self::Layout,
        Self::Controls,
        Self::Data,
        Self::Behavior,
        Self::Presentation,
        Self::Overrides,
    ];

    pub fn label(self) -> &'static str {
        match self {
            Self::Layout => "Layout",
            Self::Controls => "Controls",
            Self::Data => "Data",
            Self::Behavior => "Behavior",
            Self::Presentation => "Presentation",
            Self::Overrides => "Overrides",
        }
    }
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Serialize, Deserialize)]
pub struct UiRect {
    pub x: f32,
    pub y: f32,
    pub width: f32,
    pub height: f32,
}

impl UiRect {
    pub fn is_valid(self) -> bool {
        self.x.is_finite()
            && self.y.is_finite()
            && self.width.is_finite()
            && self.height.is_finite()
            && self.width > 0.0
            && self.height > 0.0
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum UiWidgetKind {
    Panel,
    NineSlice,
    Button,
    Tab,
    Slot,
    BarFrame,
    PortraitFrame,
    MinimapFrame,
    Label,
    Image,
    ScrollArea,
    Progress,
    TextInput,
    Toggle,
    List,
    Custom,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct UiDataBinding {
    pub property: String,
    pub source: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub format: Option<String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct UiBehaviorBinding {
    pub event: String,
    pub action: String,
    #[serde(default)]
    pub arguments: BTreeMap<String, String>,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct UiWidget {
    pub id: String,
    pub kind: UiWidgetKind,
    pub rect: UiRect,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub label: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub parent: Option<String>,
    #[serde(default)]
    pub data_bindings: Vec<UiDataBinding>,
    #[serde(default)]
    pub behavior_bindings: Vec<UiBehaviorBinding>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub presentation_resource: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub animation_resource: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub behavior_resource: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub sound_event_id: Option<String>,
    #[serde(default)]
    pub locked: bool,
    #[serde(default = "default_true")]
    pub visible: bool,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct UiDocument {
    pub schema: String,
    pub id: String,
    pub display_name: String,
    pub kind: UiDocumentKind,
    #[serde(default = "default_reference_size")]
    pub reference_size: [u32; 2],
    #[serde(default = "default_snap_px")]
    pub snap_px: u32,
    #[serde(default = "default_safe_area")]
    pub safe_area: [u32; 4],
    #[serde(default)]
    pub widgets: Vec<UiWidget>,
    #[serde(default)]
    pub metadata: BTreeMap<String, String>,
}

impl UiDocument {
    pub fn new(id: impl Into<String>, display_name: impl Into<String>, kind: UiDocumentKind) -> Self {
        Self {
            schema: UI_DOCUMENT_SCHEMA_V1.to_string(),
            id: id.into(),
            display_name: display_name.into(),
            kind,
            reference_size: default_reference_size(),
            snap_px: default_snap_px(),
            safe_area: default_safe_area(),
            widgets: Vec::new(),
            metadata: BTreeMap::new(),
        }
    }

    pub fn load(path: &Path) -> Result<Self, String> {
        let text = fs::read_to_string(path)
            .map_err(|error| format!("failed to read {}: {error}", path.display()))?;
        let document: Self = serde_json::from_str(&text)
            .map_err(|error| format!("failed to parse {}: {error}", path.display()))?;
        document.validate()?;
        Ok(document)
    }

    pub fn save(&self, path: &Path) -> Result<(), String> {
        self.validate()?;
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)
                .map_err(|error| format!("failed to create {}: {error}", parent.display()))?;
        }
        let text = serde_json::to_string_pretty(self)
            .map_err(|error| format!("failed to serialize UI document: {error}"))?;
        fs::write(path, format!("{text}\n"))
            .map_err(|error| format!("failed to write {}: {error}", path.display()))
    }

    pub fn validate(&self) -> Result<(), String> {
        if self.schema != UI_DOCUMENT_SCHEMA_V1 {
            return Err(format!("unsupported UI document schema {}", self.schema));
        }
        if self.id.trim().is_empty() || self.display_name.trim().is_empty() {
            return Err("UI document id/display_name must not be empty".to_string());
        }
        if self.reference_size[0] == 0 || self.reference_size[1] == 0 {
            return Err("UI document reference_size must be non-zero".to_string());
        }
        if self.snap_px == 0 {
            return Err("UI document snap_px must be non-zero".to_string());
        }
        let mut ids = std::collections::BTreeSet::new();
        for widget in &self.widgets {
            if widget.id.trim().is_empty() || !ids.insert(widget.id.as_str()) {
                return Err(format!("UI document has empty/duplicate widget id {}", widget.id));
            }
            if !widget.rect.is_valid() {
                return Err(format!("UI widget {} has invalid rectangle", widget.id));
            }
        }
        for widget in &self.widgets {
            if let Some(parent) = widget.parent.as_deref() {
                if !ids.contains(parent) {
                    return Err(format!("UI widget {} references missing parent {parent}", widget.id));
                }
            }
            for binding in &widget.data_bindings {
                if binding.property.trim().is_empty() || binding.source.trim().is_empty() {
                    return Err(format!("UI widget {} has an incomplete data binding", widget.id));
                }
            }
            for binding in &widget.behavior_bindings {
                if binding.event.trim().is_empty() || binding.action.trim().is_empty() {
                    return Err(format!("UI widget {} has an incomplete behavior binding", widget.id));
                }
            }
            for (label, resource) in [
                ("presentation", widget.presentation_resource.as_deref()),
                ("animation", widget.animation_resource.as_deref()),
                ("behavior", widget.behavior_resource.as_deref()),
                ("sound event", widget.sound_event_id.as_deref()),
            ] {
                if resource.is_some_and(|value| value.trim().is_empty()) {
                    return Err(format!("UI widget {} has an empty {label} resource reference", widget.id));
                }
            }
        }
        Ok(())
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct TransitionResource {
    pub schema: String,
    pub id: String,
    pub destination_scene_id: String,
    pub spawn_id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub loading_ui_document_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub loading_sound_event_id: Option<String>,
    #[serde(default)]
    pub metadata: BTreeMap<String, String>,
}

impl TransitionResource {
    pub fn validate(&self) -> Result<(), String> {
        if self.schema != TRANSITION_RESOURCE_SCHEMA_V1 {
            return Err(format!("unsupported transition resource schema {}", self.schema));
        }
        if self.id.trim().is_empty() || self.destination_scene_id.trim().is_empty() || self.spawn_id.trim().is_empty() {
            return Err("transition resource id/destination_scene_id/spawn_id must not be empty".to_string());
        }
        Ok(())
    }
}

fn default_true() -> bool { true }
fn default_reference_size() -> [u32; 2] { [1920, 1080] }
fn default_snap_px() -> u32 { 8 }
fn default_safe_area() -> [u32; 4] { [48, 48, 48, 48] }

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ui_document_validates_typed_data_and_behavior_bindings() {
        let mut document = UiDocument::new("crafting", "Crafting", UiDocumentKind::Crafting);
        document.widgets.push(UiWidget {
            id: "craft_button".to_string(),
            kind: UiWidgetKind::Button,
            rect: UiRect { x: 24.0, y: 24.0, width: 180.0, height: 48.0 },
            label: Some("Craft".to_string()),
            parent: None,
            data_bindings: vec![UiDataBinding { property: "enabled".to_string(), source: "crafting.can_craft_selected".to_string(), format: None }],
            behavior_bindings: vec![UiBehaviorBinding { event: "on_click".to_string(), action: "crafting.craft_selected".to_string(), arguments: BTreeMap::new() }],
            presentation_resource: None,
            animation_resource: None,
            behavior_resource: None,
            sound_event_id: None,
            locked: false,
            visible: true,
        });
        assert!(document.validate().is_ok());
    }

    #[test]
    fn transition_can_reference_loading_ui_document() {
        let resource = TransitionResource {
            schema: TRANSITION_RESOURCE_SCHEMA_V1.to_string(),
            id: "enter_cave".to_string(),
            destination_scene_id: "cave_001".to_string(),
            spawn_id: "entry".to_string(),
            loading_ui_document_id: Some("loading_default".to_string()),
            loading_sound_event_id: None,
            metadata: BTreeMap::new(),
        };
        assert!(resource.validate().is_ok());
    }
}
