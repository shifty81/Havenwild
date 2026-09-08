use std::{collections::{BTreeMap, BTreeSet}, fs, path::Path};

use serde::Deserialize;

use crate::character_repository_catalog::{
    CharacterProductionCatalog, CharacterProductionComponent,
};

pub(crate) const GAMEPLAY_EQUIPMENT_POLICY_PATH: &str =
    "content/characters/gameplay_character_equipment_policy_v0_1.json";

#[derive(Clone, Debug, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub(crate) struct GameplayEquipmentPolicy {
    pub(crate) schema: String,
    pub(crate) creator_policy: String,
    pub(crate) principles: Vec<String>,
    pub(crate) slots: Vec<EquipmentSlotPolicy>,
    pub(crate) acquisition_kinds: Vec<String>,
    pub(crate) required_animation_states: Vec<String>,
    pub(crate) optional_animation_states: Vec<String>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub(crate) struct EquipmentSlotPolicy {
    pub(crate) id: String,
    pub(crate) channels: Vec<String>,
    pub(crate) allow_at_creation: bool,
    #[serde(default)]
    pub(crate) creator_channels: Vec<String>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub(crate) struct GameplayEquipmentEntry<'a> {
    pub(crate) component: &'a CharacterProductionComponent,
    pub(crate) slot_id: &'a str,
    pub(crate) missing_required_animations: Vec<String>,
}

impl GameplayEquipmentPolicy {
    pub(crate) fn load(project_root: &Path) -> Result<Self, String> {
        let path = project_root.join(GAMEPLAY_EQUIPMENT_POLICY_PATH);
        let bytes = fs::read(&path)
            .map_err(|error| format!("failed to read {}: {error}", path.display()))?;
        let policy: Self = serde_json::from_slice(&bytes)
            .map_err(|error| format!("failed to parse {}: {error}", path.display()))?;
        if policy.schema != "havenwild.character.gameplay_equipment_policy.v0_1" {
            return Err(format!("unsupported gameplay equipment policy schema: {}", policy.schema));
        }
        let mut slot_ids = BTreeSet::new();
        for slot in &policy.slots {
            if !slot_ids.insert(slot.id.as_str()) {
                return Err(format!("duplicate gameplay equipment slot {}", slot.id));
            }
            if slot.channels.is_empty() {
                return Err(format!("gameplay equipment slot {} has no channels", slot.id));
            }
            if !slot.allow_at_creation && !slot.creator_channels.is_empty() {
                return Err(format!(
                    "gameplay-only slot {} cannot expose creator channels",
                    slot.id
                ));
            }
            for channel in &slot.creator_channels {
                if !slot.channels.iter().any(|candidate| candidate == channel) {
                    return Err(format!(
                        "creator channel {channel} is not owned by equipment slot {}",
                        slot.id
                    ));
                }
            }
        }
        for channel in policy
            .slots
            .iter()
            .flat_map(|slot| slot.creator_channels.iter())
        {
            if !policy.channel_allowed_at_creation(channel) {
                return Err(format!(
                    "creator channel {channel} failed gameplay equipment policy validation"
                ));
            }
        }
        Ok(policy)
    }

    pub(crate) fn slot_for_channel(&self, channel: &str) -> Option<&EquipmentSlotPolicy> {
        self.slots
            .iter()
            .find(|slot| slot.channels.iter().any(|candidate| candidate == channel))
    }

    pub(crate) fn channel_allowed_at_creation(&self, channel: &str) -> bool {
        self.slot_for_channel(channel).is_some_and(|slot| {
            slot.allow_at_creation
                && slot
                    .creator_channels
                    .iter()
                    .any(|candidate| candidate == channel)
        })
    }

    pub(crate) fn gameplay_entries<'a>(
        &'a self,
        catalog: &'a CharacterProductionCatalog,
    ) -> Vec<GameplayEquipmentEntry<'a>> {
        catalog
            .components
            .iter()
            .filter(|component| component.production_ready)
            .filter_map(|component| {
                let slot = self.slot_for_channel(&component.semantic_channel)?;
                let normalized = component
                    .animations
                    .iter()
                    .map(|animation| animation.to_ascii_lowercase())
                    .collect::<BTreeSet<_>>();
                let missing_required_animations = self
                    .required_animation_states
                    .iter()
                    .filter(|animation| !normalized.contains(&animation.to_ascii_lowercase()))
                    .cloned()
                    .collect::<Vec<_>>();
                Some(GameplayEquipmentEntry {
                    component,
                    slot_id: &slot.id,
                    missing_required_animations,
                })
            })
            .collect()
    }

    pub(crate) fn animation_coverage_summary(
        &self,
        catalog: &CharacterProductionCatalog,
    ) -> BTreeMap<String, usize> {
        let mut summary = BTreeMap::new();
        for entry in self.gameplay_entries(catalog) {
            let key = if entry.missing_required_animations.is_empty() {
                "ready"
            } else {
                "missing_required_animation"
            };
            *summary.entry(key.to_string()).or_insert(0) += 1;
        }
        summary
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn armor_never_enters_creator_but_remains_gameplay_visible() {
        let policy = test_policy();
        let catalog = CharacterProductionCatalog {
            schema: "havenwild.lpc.character.production_catalog.v0_1".to_string(),
            source_root: "Characters".to_string(),
            component_count: 1,
            channel_counts: BTreeMap::new(),
            components: vec![component("iron_helm", "armor_head", &["Idle", "Walk"])],
        };
        let entries = policy.gameplay_entries(&catalog);
        assert_eq!(entries.len(), 1);
        assert_eq!(entries[0].slot_id, "head");
        assert!(!policy.channel_allowed_at_creation("armor_head"));
    }

    #[test]
    fn ordinary_clothing_can_enter_creator_while_armor_remains_gameplay_only() {
        let policy = test_policy();
        assert!(policy.channel_allowed_at_creation("clothing_torso"));
        assert!(!policy.channel_allowed_at_creation("armor_torso"));
    }

    #[test]
    fn missing_idle_is_reported_instead_of_substituted() {
        let policy = test_policy();
        let catalog = CharacterProductionCatalog {
            schema: "havenwild.lpc.character.production_catalog.v0_1".to_string(),
            source_root: "Characters".to_string(),
            component_count: 1,
            channel_counts: BTreeMap::new(),
            components: vec![component("boots", "footwear", &["Walk"])],
        };
        let entries = policy.gameplay_entries(&catalog);
        assert_eq!(entries[0].missing_required_animations, vec!["idle"]);
    }

    fn test_policy() -> GameplayEquipmentPolicy {
        GameplayEquipmentPolicy {
            schema: "havenwild.character.gameplay_equipment_policy.v0_1".to_string(),
            creator_policy: String::new(),
            principles: Vec::new(),
            slots: vec![
                EquipmentSlotPolicy {
                    id: "head".to_string(),
                    channels: vec!["headwear".to_string(), "armor_head".to_string()],
                    allow_at_creation: false,
                    creator_channels: Vec::new(),
                },
                EquipmentSlotPolicy {
                    id: "torso".to_string(),
                    channels: vec!["clothing_torso".to_string(), "armor_torso".to_string()],
                    allow_at_creation: true,
                    creator_channels: vec!["clothing_torso".to_string()],
                },
                EquipmentSlotPolicy {
                    id: "feet".to_string(),
                    channels: vec!["footwear".to_string()],
                    allow_at_creation: true,
                    creator_channels: vec!["footwear".to_string()],
                },
            ],
            acquisition_kinds: Vec::new(),
            required_animation_states: vec!["idle".to_string(), "walk".to_string()],
            optional_animation_states: Vec::new(),
        }
    }

    fn component(
        id: &str,
        semantic_channel: &str,
        animations: &[&str],
    ) -> CharacterProductionComponent {
        CharacterProductionComponent {
            id: id.to_string(),
            display_name: id.to_string(),
            semantic_channel: semantic_channel.to_string(),
            top_level: String::new(),
            component_folder: String::new(),
            body_compatibility: "universal".to_string(),
            authored_variants: BTreeMap::new(),
            animations: animations.iter().map(|value| (*value).to_string()).collect(),
            production_ready: true,
        }
    }
}
