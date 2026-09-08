use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};

pub const RESOURCE_CONTEXT_SCHEMA_V1: &str = "havenwild.resource_context.v1";
pub const RESOURCE_CONTEXT_RELATIVE_PATH: &str = "WORKSPACE/dev_bridge/resource_context.json";

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ResourceContextKind {
    World,
    Scene,
    Character,
    Equipment,
    Animation,
    Frame,
    Socket,
    Ui,
    Sound,
    Behavior,
    Visual,
    Source,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ResourceContextNode {
    pub kind: ResourceContextKind,
    pub resource_id: String,
    pub label: String,
    #[serde(default)]
    pub instance_id: Option<String>,
    #[serde(default)]
    pub variant_id: Option<String>,
}

impl ResourceContextNode {
    pub fn new(
        kind: ResourceContextKind,
        resource_id: impl Into<String>,
        label: impl Into<String>,
    ) -> Self {
        Self {
            kind,
            resource_id: resource_id.into(),
            label: label.into(),
            instance_id: None,
            variant_id: None,
        }
    }
}

#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct CharacterAnimationResourceContext {
    pub character_id: String,
    #[serde(default)]
    pub equipment_slot: Option<String>,
    #[serde(default)]
    pub equipment_item_id: Option<String>,
    #[serde(default)]
    pub equipment_label: Option<String>,
    pub action_id: String,
    pub direction: String,
    pub frame_index: usize,
    #[serde(default)]
    pub socket_ids: Vec<String>,
    #[serde(default)]
    pub active_socket_id: Option<String>,
}


#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct UiResourceContext {
    pub document_id: String,
    #[serde(default)]
    pub related_document_ids: Vec<String>,
    #[serde(default)]
    pub selected_control_id: Option<String>,
    #[serde(default)]
    pub developer_focus_requested: bool,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ResourceContext {
    pub schema: String,
    pub revision: u64,
    #[serde(default)]
    pub world_id: Option<String>,
    #[serde(default)]
    pub scene_id: Option<String>,
    #[serde(default)]
    pub chain: Vec<ResourceContextNode>,
    #[serde(default)]
    pub character_animation: Option<CharacterAnimationResourceContext>,
    #[serde(default)]
    pub ui: Option<UiResourceContext>,
}

impl ResourceContext {
    pub fn new(revision: u64) -> Self {
        Self {
            schema: RESOURCE_CONTEXT_SCHEMA_V1.to_string(),
            revision,
            world_id: None,
            scene_id: None,
            chain: Vec::new(),
            character_animation: None,
            ui: None,
        }
    }

    pub fn validate(&self) -> Result<(), String> {
        if self.schema != RESOURCE_CONTEXT_SCHEMA_V1 {
            return Err(format!("unsupported resource context schema {}", self.schema));
        }
        for node in &self.chain {
            if node.resource_id.trim().is_empty() {
                return Err(format!("{:?} resource context node has an empty resource id", node.kind));
            }
            if node.label.trim().is_empty() {
                return Err(format!("{} resource context node has an empty label", node.resource_id));
            }
        }
        if let Some(ui) = &self.ui {
            if ui.document_id.trim().is_empty() {
                return Err("UI resource context requires a document id".to_string());
            }
            if ui.related_document_ids.iter().any(|id| id.trim().is_empty()) {
                return Err("UI resource context contains an empty related document id".to_string());
            }
        }
        if let Some(character) = &self.character_animation {
            if character.character_id.trim().is_empty() {
                return Err("character animation context requires a character id".to_string());
            }
            if character.action_id.trim().is_empty() {
                return Err("character animation context requires an action id".to_string());
            }
            if character.direction.trim().is_empty() {
                return Err("character animation context requires a direction".to_string());
            }
        }
        Ok(())
    }

    pub fn breadcrumb(&self) -> String {
        self.chain
            .iter()
            .map(|node| node.label.as_str())
            .collect::<Vec<_>>()
            .join(" → ")
    }
}

pub fn resource_context_path(repo_root: &Path) -> PathBuf {
    repo_root.join(RESOURCE_CONTEXT_RELATIVE_PATH)
}

pub fn write_resource_context(repo_root: &Path, context: &ResourceContext) -> Result<(), String> {
    context.validate()?;
    let path = resource_context_path(repo_root);
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .map_err(|error| format!("create resource context directory: {error}"))?;
    }
    let bytes = serde_json::to_vec_pretty(context)
        .map_err(|error| format!("serialize resource context: {error}"))?;
    let temp = path.with_extension("json.tmp");
    fs::write(&temp, bytes)
        .map_err(|error| format!("write temporary resource context {}: {error}", temp.display()))?;
    if path.exists() {
        fs::remove_file(&path)
            .map_err(|error| format!("replace resource context {}: {error}", path.display()))?;
    }
    fs::rename(&temp, &path)
        .map_err(|error| format!("commit resource context {}: {error}", path.display()))
}

pub fn read_resource_context(repo_root: &Path) -> Result<Option<ResourceContext>, String> {
    let path = resource_context_path(repo_root);
    if !path.is_file() {
        return Ok(None);
    }
    let bytes = fs::read(&path)
        .map_err(|error| format!("read resource context {}: {error}", path.display()))?;
    let context: ResourceContext = serde_json::from_slice(&bytes)
        .map_err(|error| format!("parse resource context {}: {error}", path.display()))?;
    context.validate()?;
    Ok(Some(context))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn character_equipment_animation_chain_round_trips() {
        let mut context = ResourceContext::new(17);
        context.world_id = Some("world_dev".to_string());
        context.scene_id = Some("overworld".to_string());
        context.chain = vec![
            ResourceContextNode::new(ResourceContextKind::Character, "character_dev", "Development Character"),
            ResourceContextNode::new(ResourceContextKind::Equipment, "axe_iron", "Iron Axe"),
            ResourceContextNode::new(ResourceContextKind::Animation, "1h_backslash", "1H Backslash"),
            ResourceContextNode::new(ResourceContextKind::Frame, "1h_backslash:3", "Frame 3"),
        ];
        context.character_animation = Some(CharacterAnimationResourceContext {
            character_id: "character_dev".to_string(),
            equipment_slot: Some("main_hand".to_string()),
            equipment_item_id: Some("axe_iron".to_string()),
            equipment_label: Some("Iron Axe".to_string()),
            action_id: "1h_backslash".to_string(),
            direction: "south".to_string(),
            frame_index: 3,
            socket_ids: vec!["hand_main".to_string()],
            active_socket_id: Some("hand_main".to_string()),
        });
        context.validate().unwrap();
        assert_eq!(
            context.breadcrumb(),
            "Development Character → Iron Axe → 1H Backslash → Frame 3"
        );
        let json = serde_json::to_string(&context).unwrap();
        let decoded: ResourceContext = serde_json::from_str(&json).unwrap();
        assert_eq!(decoded, context);
    }
}
