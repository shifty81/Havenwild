use crate::asset_pack::{AssetCategory, AssetPackRegistry, StableAssetRef};
use crate::universal_lpc_animation::{HAVENWILD_CHARACTER_FRAME_SIZE, ULPC_DIRECTION_ORDER};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};
use std::fs::read_to_string;
use std::path::Path;

pub const LPC_CHARACTER_LAYER_CATALOG_SCHEMA: &str = "havenwild.lpc_character_layer_catalog.v2";

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct LpcCharacterLayerCatalog {
    pub schema: String,
    #[serde(default)]
    pub pass: String,
    pub profile_id: String,
    pub frame_cell: [u32; 2],
    pub directions: Vec<String>,
    #[serde(default)]
    pub future_direction_profile: Option<String>,
    pub layer_order: Vec<String>,
    pub slots: Vec<LpcCharacterLayerSlot>,
    #[serde(default)]
    pub body_families: Vec<String>,
    pub animation_families: Vec<LpcAnimationFamily>,
    #[serde(default)]
    pub compatibility_matrix: Option<String>,
    pub consumers: Vec<String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct LpcCharacterLayerSlot {
    pub id: String,
    pub category: AssetCategory,
    pub required: bool,
    pub multiple: bool,
    #[serde(default)]
    pub allowed_tags: BTreeSet<String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(untagged)]
pub enum LpcFramesPerDirection {
    Fixed(u32),
    SourceDefined(String),
}

impl LpcFramesPerDirection {
    pub fn is_source_defined(&self) -> bool {
        matches!(self, Self::SourceDefined(value) if value == "source_defined")
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct LpcAnimationFamily {
    pub id: String,
    pub rows: u32,
    pub frames_per_direction: LpcFramesPerDirection,
    #[serde(default)]
    pub runtime_columns: Option<u32>,
    #[serde(default)]
    pub required_baseline: bool,
    pub direction_order: Vec<String>,
    #[serde(default)]
    pub required_events: Vec<String>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CharacterLayerCandidate {
    pub slot: String,
    pub reference: StableAssetRef,
}

#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct CharacterLayerIndex {
    pub by_slot: BTreeMap<String, Vec<CharacterLayerCandidate>>,
}

impl LpcCharacterLayerCatalog {
    pub fn load(path: &Path) -> Result<Self, String> {
        let raw = read_to_string(path).map_err(|error| error.to_string())?;
        let catalog: Self = serde_json::from_str(&raw).map_err(|error| error.to_string())?;
        catalog.validate()?;
        Ok(catalog)
    }

    pub fn validate(&self) -> Result<(), String> {
        if self.schema != LPC_CHARACTER_LAYER_CATALOG_SCHEMA {
            return Err(format!("unsupported LPC character catalog schema {}", self.schema));
        }
        if self.frame_cell != HAVENWILD_CHARACTER_FRAME_SIZE {
            return Err(format!(
                "Havenwild character runtime frame cell must be {:?}, got {:?}",
                HAVENWILD_CHARACTER_FRAME_SIZE, self.frame_cell
            ));
        }
        let expected_directions: Vec<String> = ULPC_DIRECTION_ORDER.iter().map(|value| (*value).to_string()).collect();
        if self.directions != expected_directions {
            return Err(format!(
                "production LPC character profile must use four cardinal directions {:?}, got {:?}",
                expected_directions, self.directions
            ));
        }
        if !self.slots.iter().any(|slot| slot.id == "body/base" && slot.required) {
            return Err("LPC character profile requires body/base".to_string());
        }
        let unique: BTreeSet<_> = self.slots.iter().map(|slot| &slot.id).collect();
        if unique.len() != self.slots.len() {
            return Err("LPC character slots must be unique".to_string());
        }
        for required in ["male", "female", "teen", "child", "muscular", "pregnant"] {
            if !self.body_families.iter().any(|value| value == required) {
                return Err(format!("LPC character profile is missing body family {required}"));
            }
        }
        for family in &self.animation_families {
            if family.rows != 4 {
                return Err(format!("animation {} must resolve through four cardinal rows", family.id));
            }
            if family.direction_order != expected_directions {
                return Err(format!("animation {} direction order does not match runtime authority", family.id));
            }
            if let LpcFramesPerDirection::SourceDefined(value) = &family.frames_per_direction {
                if value != "source_defined" {
                    return Err(format!("animation {} has unknown frames_per_direction value {value}", family.id));
                }
            }
        }
        Ok(())
    }
}

impl CharacterLayerIndex {
    pub fn build(registry: &AssetPackRegistry, catalog: &LpcCharacterLayerCatalog) -> Self {
        let mut index = Self::default();
        for pack in registry.mounted_packs().filter(|pack| pack.production_enabled) {
            for asset in &pack.assets {
                let Some(slot) = asset.metadata.get("character_layer_slot").and_then(|value| value.as_str()) else { continue; };
                if !catalog.slots.iter().any(|definition| definition.id == slot) { continue; }
                index.by_slot.entry(slot.to_string()).or_default().push(CharacterLayerCandidate {
                    slot: slot.to_string(),
                    reference: StableAssetRef {
                        pack_id: pack.id.clone(),
                        category: asset.category.clone(),
                        asset_id: asset.id.clone(),
                        source_id: asset.source_id.clone(),
                        variant_id: None,
                    },
                });
            }
        }
        for candidates in index.by_slot.values_mut() {
            candidates.sort_by(|left, right| {
                left.reference.pack_id.cmp(&right.reference.pack_id)
                    .then_with(|| left.reference.asset_id.cmp(&right.reference.asset_id))
            });
        }
        index
    }
}

pub fn category_is_character_layer(category: &AssetCategory) -> bool {
    matches!(
        category,
        AssetCategory::Character
            | AssetCategory::Clothing
            | AssetCategory::Armor
            | AssetCategory::Tool
            | AssetCategory::Weapon
            | AssetCategory::Npc
            | AssetCategory::Animation
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn clothing_and_armor_are_character_layers() {
        assert!(category_is_character_layer(&AssetCategory::Clothing));
        assert!(category_is_character_layer(&AssetCategory::Armor));
        assert!(!category_is_character_layer(&AssetCategory::Terrain));
    }
}
