use std::{collections::BTreeMap, fs, path::Path};

use serde::Deserialize;

pub(crate) const PRODUCTION_CATALOG_PATH: &str =
    "content/assets/lpc/lpc_character_production_catalog_v0_1.json";

const EMBEDDED_PRODUCTION_CATALOG: &str =
    include_str!("../../../content/assets/lpc/lpc_character_production_catalog_v0_1.json");

#[derive(Clone, Debug, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub(crate) struct CharacterProductionCatalog {
    pub(crate) schema: String,
    pub(crate) source_root: String,
    pub(crate) component_count: usize,
    pub(crate) channel_counts: BTreeMap<String, usize>,
    pub(crate) components: Vec<CharacterProductionComponent>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub(crate) struct CharacterProductionComponent {
    pub(crate) id: String,
    pub(crate) display_name: String,
    pub(crate) semantic_channel: String,
    pub(crate) top_level: String,
    pub(crate) component_folder: String,
    pub(crate) body_compatibility: String,
    pub(crate) authored_variants: BTreeMap<String, BTreeMap<String, String>>,
    pub(crate) animations: Vec<String>,
    pub(crate) production_ready: bool,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub(crate) struct CreatorRepositoryOption {
    pub(crate) component_id: String,
    pub(crate) variant_id: String,
    pub(crate) display_name: String,
    pub(crate) semantic_channel: String,
    pub(crate) body_compatibility: String,
    pub(crate) idle_source: String,
    pub(crate) walk_source: String,
}

impl CharacterProductionCatalog {
    pub(crate) fn embedded() -> Result<Self, String> {
        let catalog: Self = serde_json::from_str(EMBEDDED_PRODUCTION_CATALOG).map_err(|error| {
            format!("failed to parse embedded character production catalog: {error}")
        })?;
        catalog.validate()?;
        Ok(catalog)
    }

    pub(crate) fn load(project_root: &Path) -> Result<Self, String> {
        let path = project_root.join(PRODUCTION_CATALOG_PATH);
        let bytes = fs::read(&path)
            .map_err(|error| format!("failed to read {}: {error}", path.display()))?;
        let catalog: Self = serde_json::from_slice(&bytes)
            .map_err(|error| format!("failed to parse {}: {error}", path.display()))?;
        catalog.validate()?;
        Ok(catalog)
    }

    fn validate(&self) -> Result<(), String> {
        if self.schema != "havenwild.lpc.character.production_catalog.v0_1" {
            return Err(format!(
                "unsupported character production catalog schema: {}",
                self.schema
            ));
        }
        if self.component_count != self.components.len() {
            return Err(format!(
                "character production catalog count mismatch: declared {}, loaded {}",
                self.component_count,
                self.components.len()
            ));
        }
        Ok(())
    }

    pub(crate) fn creator_components<'a>(
        &'a self,
        semantic_channel: &'a str,
        body: &'a str,
    ) -> impl Iterator<Item = &'a CharacterProductionComponent> + 'a {
        let channel_allowed = creator_channel_allowed_for_body(semantic_channel, body);
        self.components.iter().filter(move |component| {
            channel_allowed
                && component.production_ready
                && component.semantic_channel == semantic_channel
                && body_is_compatible(&component.body_compatibility, body)
        })
    }

    pub(crate) fn creator_options(
        &self,
        semantic_channel: &str,
        body: &str,
    ) -> Vec<CreatorRepositoryOption> {
        // Defense in depth: callers cannot obtain a disallowed creator channel
        // even if repository metadata marks the underlying LPC layer universal.
        if !creator_channel_allowed_for_body(semantic_channel, body) {
            return Vec::new();
        }

        let mut options = self
            .creator_components(semantic_channel, body)
            .flat_map(|component| {
                component
                    .authored_variants
                    .iter()
                    .filter_map(move |(variant, animations)| {
                        let idle = animations.get("Idle")?;
                        let walk = animations.get("Walk")?;
                        Some(CreatorRepositoryOption {
                            component_id: component.id.clone(),
                            variant_id: stable_variant_id(variant),
                            display_name: variant.clone(),
                            semantic_channel: component.semantic_channel.clone(),
                            body_compatibility: component.body_compatibility.clone(),
                            idle_source: idle.clone(),
                            walk_source: walk.clone(),
                        })
                    })
            })
            .collect::<Vec<_>>();
        options.sort_by(|left, right| {
            left.display_name
                .cmp(&right.display_name)
                .then_with(|| left.component_id.cmp(&right.component_id))
        });
        options.dedup_by(|left, right| {
            left.component_id == right.component_id && left.variant_id == right.variant_id
        });
        options
    }
}

pub(crate) fn creator_channel_allowed_for_body(semantic_channel: &str, body: &str) -> bool {
    // Universal LPC records describe source-layer geometry. Havenwild owns the
    // player/NPC eligibility policy. Clothing remains broadly available across
    // Male and Female characters, while facial hair is Male-only.
    semantic_channel != "facial_hair" || body == "male_neutral"
}

fn body_is_compatible(compatibility: &str, body: &str) -> bool {
    compatibility == "universal"
        || compatibility == body
        || (compatibility == "masculine" && body == "male_neutral")
        || (compatibility == "feminine" && body == "female_neutral")
}

pub(crate) fn stable_variant_id(display_name: &str) -> String {
    let mut output = String::with_capacity(display_name.len());
    let mut separator_pending = false;
    for character in display_name.chars().flat_map(char::to_lowercase) {
        if character.is_ascii_alphanumeric() {
            if separator_pending && !output.is_empty() {
                output.push('_');
            }
            output.push(character);
            separator_pending = false;
        } else {
            separator_pending = true;
        }
    }
    output
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn embedded_catalog_is_the_194_component_authority() {
        let catalog = CharacterProductionCatalog::embedded().expect("embedded catalog");
        assert_eq!(catalog.component_count, 194);
        assert_eq!(catalog.components.len(), 194);
    }

    #[test]
    fn creator_options_require_idle_and_walk_sources() {
        let catalog = CharacterProductionCatalog::embedded().expect("embedded catalog");
        let options = catalog.creator_options("scalp_hair", "male_neutral");
        assert!(!options.is_empty());
        assert!(options.iter().all(|entry| !entry.idle_source.is_empty()));
        assert!(options.iter().all(|entry| !entry.walk_source.is_empty()));
    }

    #[test]
    fn creator_filter_maps_game_sex_to_repository_compatibility() {
        let catalog = CharacterProductionCatalog::embedded().expect("embedded catalog");
        assert!(catalog.creator_components("body", "male_neutral").count() > 0);
        assert!(catalog.creator_components("body", "female_neutral").count() > 0);
        assert_eq!(
            catalog
                .creator_components("facial_hair", "female_neutral")
                .count(),
            0
        );
        assert!(catalog
            .creator_options("facial_hair", "female_neutral")
            .is_empty());
    }

    #[test]
    fn havenwild_channel_policy_rejects_only_female_facial_hair() {
        assert!(creator_channel_allowed_for_body(
            "facial_hair",
            "male_neutral"
        ));
        assert!(!creator_channel_allowed_for_body(
            "facial_hair",
            "female_neutral"
        ));
        assert!(creator_channel_allowed_for_body(
            "clothing_torso",
            "male_neutral"
        ));
        assert!(creator_channel_allowed_for_body(
            "clothing_torso",
            "female_neutral"
        ));
        assert!(creator_channel_allowed_for_body(
            "clothing_legs",
            "female_neutral"
        ));
        assert!(creator_channel_allowed_for_body(
            "clothing_feet",
            "female_neutral"
        ));
    }

    #[test]
    fn stable_variant_ids_are_portable() {
        assert_eq!(
            stable_variant_id("Hair 07 - Bob, Side Part"),
            "hair_07_bob_side_part"
        );
    }
}
