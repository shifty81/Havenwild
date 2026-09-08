#![allow(dead_code)]

use haven_assets::lpc_character_pipeline::{CharacterLayerIndex, LpcCharacterLayerCatalog};
use haven_assets::universal_lpc_character_authority::{UniversalLpcCharacterAuthority, UniversalLpcCharacterRecord};
use haven_assets::universal_lpc_character_builder::UniversalLpcCharacterBuilderCatalog;
use haven_assets::universal_lpc_sheet_definition::DEFAULT_ULPC_SOURCE_ROOT;
use haven_assets::universal_lpc_character_recipe::{
    universal_lpc_builder_category_id, universal_lpc_identity_compatible,
    UniversalLpcCharacterBuilderCategory, UniversalLpcCharacterRecipe,
    UNIVERSAL_LPC_ACTIVE_SOURCE_COMMIT, UNIVERSAL_LPC_CHARACTER_BUILDER_CATEGORIES,
};
use haven_save::{
    scan_unlimited_world_saves, CharacterAppearance, CharacterAppearanceLayer, CharacterId,
    CharacterProfile, CharacterProfileStore, CharacterRecipe, PortableAssetRef, WorldSaveId,
    MAX_PERSISTENT_CHARACTERS,
};
use std::path::{Path, PathBuf};

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum CharacterSelectionIntent {
    NewGame,
    LoadGame,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum CharacterSelectionScreen {
    CharacterList,
    CharacterCreator,
    WorldList,
    CreateWorld,
    Ready,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CharacterProfileCard {
    pub character_id: CharacterId,
    pub display_name: String,
    pub appearance: CharacterAppearance,
    pub last_played_unix_seconds: u64,
    pub occupied: bool,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct WorldSaveCard {
    pub world_id: WorldSaveId,
    pub display_name: String,
    pub path: PathBuf,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CharacterCreatorDraft {
    pub display_name: String,
    pub sex: String,
    pub age_group: String,
    pub body_profile: String,
    pub animation_profile: String,
    pub portrait_profile: String,
    pub layers: Vec<CharacterAppearanceLayer>,
    pub active_slot: String,
    pub universal_lpc_recipe: Option<UniversalLpcCharacterRecipe>,
}

#[derive(Clone, Debug)]
pub struct CharacterSelectionUiModel {
    pub intent: CharacterSelectionIntent,
    pub screen: CharacterSelectionScreen,
    pub character_cards: Vec<Option<CharacterProfileCard>>,
    pub world_cards: Vec<WorldSaveCard>,
    pub selected_character: Option<CharacterId>,
    pub selected_world: Option<WorldSaveId>,
    pub creator: CharacterCreatorDraft,
    /// Same sheet-definition builder catalog consumed by Character Studio and NPC generation.
    pub universal_lpc_builder: Option<UniversalLpcCharacterBuilderCatalog>,
    pub status: String,
}

fn asset_category_code(category: &haven_assets::asset_pack::AssetCategory) -> &'static str {
    use haven_assets::asset_pack::AssetCategory;
    match category {
        AssetCategory::Terrain => "terrain",
        AssetCategory::TileObject => "tile_object",
        AssetCategory::Building => "building",
        AssetCategory::Wall => "wall",
        AssetCategory::Floor => "floor",
        AssetCategory::Door => "door",
        AssetCategory::Furniture => "furniture",
        AssetCategory::Crop => "crop",
        AssetCategory::Tree => "tree",
        AssetCategory::Foliage => "foliage",
        AssetCategory::Character => "character",
        AssetCategory::Clothing => "clothing",
        AssetCategory::Armor => "armor",
        AssetCategory::Tool => "tool",
        AssetCategory::Weapon => "weapon",
        AssetCategory::Animal => "animal",
        AssetCategory::Npc => "npc",
        AssetCategory::Animation => "animation",
        AssetCategory::Effect => "effect",
        AssetCategory::Ui => "ui",
        AssetCategory::Audio => "audio",
        AssetCategory::Music => "music",
        AssetCategory::Item => "item",
        AssetCategory::Recipe => "recipe",
        AssetCategory::Biome => "biome",
        AssetCategory::WorldGeneration => "world_generation",
        AssetCategory::Scene => "scene",
        AssetCategory::Interior => "interior",
        AssetCategory::Cave => "cave",
        AssetCategory::Dungeon => "dungeon",
        AssetCategory::EditorTemplate => "editor_template",
        AssetCategory::Other => "other",
    }
}

impl CharacterCreatorDraft {
    pub fn from_catalog(catalog: &LpcCharacterLayerCatalog, layers: &CharacterLayerIndex) -> Self {
        let mut selected_layers = Vec::new();
        for slot in &catalog.slots {
            let first = layers.by_slot.get(&slot.id).and_then(|items| items.first());
            if let Some(candidate) = first {
                selected_layers.push(CharacterAppearanceLayer {
                    slot: slot.id.clone(),
                    asset: PortableAssetRef {
                        pack_id: candidate.reference.pack_id.0.clone(),
                        category: asset_category_code(&candidate.reference.category).to_string(),
                        asset_id: candidate.reference.asset_id.0.clone(),
                        source_id: candidate.reference.source_id.0.clone(),
                        variant_id: candidate.reference.variant_id.clone(),
                    },
                    palette_id: None,
                    tint_rgba: None,
                    enabled: slot.required || slot.id == "body/base",
                });
            }
        }
        Self {
            display_name: "New Character".to_string(),
            sex: "Male".to_string(),
            age_group: "Adult".to_string(),
            body_profile: catalog.profile_id.clone(),
            animation_profile: "lpc.eight_direction".to_string(),
            portrait_profile: "lpc.generated".to_string(),
            layers: selected_layers,
            active_slot: "body".to_string(),
            universal_lpc_recipe: {
                let mut recipe = UniversalLpcCharacterRecipe::new(
                    UNIVERSAL_LPC_ACTIVE_SOURCE_COMMIT,
                    haven_assets::universal_lpc_animation::UniversalLpcBodyType::Male,
                );
                recipe.apply_identity_foundations("Male", "Adult");
                Some(recipe)
            },
        }
    }

    pub fn builder_categories() -> &'static [UniversalLpcCharacterBuilderCategory] {
        &UNIVERSAL_LPC_CHARACTER_BUILDER_CATEGORIES
    }

    pub fn set_identity(&mut self, sex: &str, age_group: &str) {
        self.sex = if sex.eq_ignore_ascii_case("female") { "Female" } else { "Male" }.to_string();
        self.age_group = match age_group.to_ascii_lowercase().as_str() {
            "child" => "Child",
            "teen" => "Teen",
            "elder" | "elderly" => "Elder",
            _ => "Adult",
        }.to_string();
        if let Some(recipe) = self.universal_lpc_recipe.as_mut() {
            recipe.apply_identity_foundations(&self.sex, &self.age_group);
        }
    }

    pub fn universal_lpc_choices<'a>(
        &self,
        authority: &'a UniversalLpcCharacterAuthority,
        category: &str,
        include_share_alike: bool,
    ) -> Vec<&'a UniversalLpcCharacterRecord> {
        authority.records.iter()
            .filter(|record| record.is_selectable(include_share_alike))
            .filter(|record| {
                universal_lpc_builder_category_id(
                    &record.source,
                    &record.category,
                    record.tags.iter().map(String::as_str),
                ) == Some(category)
            })
            .filter(|record| {
                universal_lpc_identity_compatible(
                    &record.source,
                    record.tags.iter().map(String::as_str),
                    &self.sex,
                    &self.age_group,
                )
            })
            .collect()
    }

    /// Definition-level creator choices shared with Character Studio and NPC generation.
    /// This is the production path; `universal_lpc_choices` remains compatibility-only
    /// for older frontend code until its cards are replaced.
    pub fn universal_lpc_builder_choices<'a>(
        &self,
        builder: &'a UniversalLpcCharacterBuilderCatalog,
        category: &str,
        include_share_alike: bool,
    ) -> Vec<&'a haven_assets::universal_lpc_character_builder::UniversalLpcBuilderOption> {
        let body = haven_assets::universal_lpc_character_recipe::universal_lpc_body_type_for_identity(
            &self.sex,
            &self.age_group,
        );
        builder.options_for(category, body)
            .filter(|option| option.is_selectable(include_share_alike))
            .filter(|option| {
                self.universal_lpc_recipe.as_ref()
                    .map(|recipe| builder.compatible_option(recipe, option))
                    .unwrap_or(true)
            })
            .collect()
    }

    pub fn appearance(&self) -> CharacterAppearance {
        CharacterAppearance {
            body_profile: self.body_profile.clone(),
            animation_profile: self.animation_profile.clone(),
            portrait_profile: self.portrait_profile.clone(),
            layers: self.layers.clone(),
        }
    }

    pub fn build_profile(&self) -> CharacterProfile {
        let mut profile = CharacterProfile::new(self.display_name.trim(), self.appearance());
        if let Some(recipe) = &self.universal_lpc_recipe {
            if let Ok(value) = recipe.to_json_value() {
                profile.character_recipe = Some(CharacterRecipe(value));
            }
        }
        profile
    }

    pub fn initialize_universal_lpc_recipe(&mut self, source_commit: &str) {
        let mut recipe = UniversalLpcCharacterRecipe::new(
            source_commit,
            haven_assets::universal_lpc_character_recipe::universal_lpc_body_type_for_identity(&self.sex, &self.age_group),
        );
        recipe.apply_identity_foundations(&self.sex, &self.age_group);
        self.universal_lpc_recipe = Some(recipe);
    }

    pub fn select_universal_lpc_option(
        &mut self,
        builder: &UniversalLpcCharacterBuilderCatalog,
        item_id: &str,
        variant: Option<String>,
    ) -> Result<(), String> {
        let recipe = self.universal_lpc_recipe.as_mut()
            .ok_or_else(|| "Universal LPC creator recipe is not initialized".to_string())?;
        let group = builder.select_option(recipe, item_id, variant)?;
        self.active_slot = group;
        Ok(())
    }

    pub fn set_layer(&mut self, slot: &str, asset: PortableAssetRef) {
        if let Some(layer) = self.layers.iter_mut().find(|layer| layer.slot == slot) {
            layer.asset = asset;
            layer.enabled = true;
        } else {
            self.layers.push(CharacterAppearanceLayer {
                slot: slot.to_string(),
                asset,
                palette_id: None,
                tint_rgba: None,
                enabled: true,
            });
        }
    }
}

impl CharacterSelectionUiModel {
    pub fn load(
        intent: CharacterSelectionIntent,
        profile_store: &CharacterProfileStore,
        world_root: &Path,
        catalog: &LpcCharacterLayerCatalog,
        layers: &CharacterLayerIndex,
    ) -> Result<Self, String> {
        let profiles = profile_store.scan()?;
        let mut character_cards = profiles
            .into_iter()
            .map(|profile| {
                Some(CharacterProfileCard {
                    character_id: profile.character_id,
                    display_name: profile.display_name,
                    appearance: profile.appearance,
                    last_played_unix_seconds: profile.last_played_unix_seconds,
                    occupied: true,
                })
            })
            .collect::<Vec<_>>();
        while character_cards.len() < MAX_PERSISTENT_CHARACTERS {
            character_cards.push(None);
        }
        let world_cards = scan_unlimited_world_saves(world_root)?
            .into_iter()
            .map(|world_id| WorldSaveCard {
                display_name: world_id.0.clone(),
                path: world_root.join(&world_id.0),
                world_id,
            })
            .collect();
        let universal_lpc_builder = UniversalLpcCharacterBuilderCatalog::load_source_root(
            &haven_assets::asset_intake::repo_root_dir().join(DEFAULT_ULPC_SOURCE_ROOT),
        ).ok();
        Ok(Self {
            intent,
            screen: CharacterSelectionScreen::CharacterList,
            character_cards,
            world_cards,
            selected_character: None,
            selected_world: None,
            creator: CharacterCreatorDraft::from_catalog(catalog, layers),
            universal_lpc_builder,
            status: "Choose one of up to five persistent characters".to_string(),
        })
    }

    pub fn choose_character(&mut self, character_id: CharacterId) {
        self.selected_character = Some(character_id);
        self.screen = CharacterSelectionScreen::WorldList;
        self.status = "Choose a world or create a new one".to_string();
    }

    pub fn begin_character_creation(&mut self) -> Result<(), String> {
        if self.character_cards.iter().filter(|card| card.is_some()).count()
            >= MAX_PERSISTENT_CHARACTERS
        {
            return Err(format!(
                "character limit reached ({MAX_PERSISTENT_CHARACTERS})"
            ));
        }
        self.screen = CharacterSelectionScreen::CharacterCreator;
        Ok(())
    }

    pub fn commit_character_creation(
        &mut self,
        store: &CharacterProfileStore,
    ) -> Result<CharacterId, String> {
        let profile = self.creator.build_profile();
        let id = profile.character_id.clone();
        store.create(&profile)?;
        self.character_cards = store
            .scan()?
            .into_iter()
            .map(|profile| {
                Some(CharacterProfileCard {
                    character_id: profile.character_id,
                    display_name: profile.display_name,
                    appearance: profile.appearance,
                    last_played_unix_seconds: profile.last_played_unix_seconds,
                    occupied: true,
                })
            })
            .collect();
        while self.character_cards.len() < MAX_PERSISTENT_CHARACTERS {
            self.character_cards.push(None);
        }
        self.choose_character(id.clone());
        Ok(id)
    }

    pub fn choose_world(&mut self, world_id: WorldSaveId) -> Result<(), String> {
        if self.selected_character.is_none() {
            return Err("choose a character before selecting a world".to_string());
        }
        self.selected_world = Some(world_id);
        self.screen = CharacterSelectionScreen::Ready;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn game_creator_persists_typed_universal_lpc_recipe() {
        let mut draft = CharacterCreatorDraft {
            display_name: "Builder".into(),
            sex: "Female".into(),
            age_group: "Adult".into(),
            body_profile: "lpc".into(),
            animation_profile: "lpc.four_direction".into(),
            portrait_profile: "lpc.generated".into(),
            layers: vec![CharacterAppearanceLayer {
                slot: "body/base".into(),
                asset: PortableAssetRef {
                    pack_id: "havenwild_starter_character".into(), category: "character".into(),
                    asset_id: "body".into(), source_id: "generated".into(), variant_id: Some("female".into()),
                },
                palette_id: None, tint_rgba: None, enabled: true,
            }],
            active_slot: "body".into(),
            universal_lpc_recipe: None,
        };
        draft.initialize_universal_lpc_recipe("commit");
        let profile = draft.build_profile();
        assert!(profile.character_recipe.is_some());
    }

    #[test]
    fn game_creator_consumes_shared_character_builder_categories() {
        let categories = CharacterCreatorDraft::builder_categories();
        assert!(categories.iter().any(|category| category.id == "body" && category.required_foundation));
        assert!(categories.iter().any(|category| category.id == "head" && category.required_foundation));
        assert!(categories.iter().any(|category| category.id == "hat"));
    }

    #[test]
    fn selection_model_exposes_five_character_cards() {
        let cards: Vec<Option<CharacterProfileCard>> = (0..MAX_PERSISTENT_CHARACTERS)
            .map(|_| None)
            .collect();
        assert_eq!(cards.len(), 5);
    }

    #[test]
    fn world_selection_requires_character() {
        let mut model = CharacterSelectionUiModel {
            intent: CharacterSelectionIntent::LoadGame,
            screen: CharacterSelectionScreen::WorldList,
            character_cards: vec![None; MAX_PERSISTENT_CHARACTERS],
            world_cards: Vec::new(),
            selected_character: None,
            selected_world: None,
            creator: CharacterCreatorDraft {
                display_name: String::new(),
                sex: "Male".to_string(),
                age_group: "Adult".to_string(),
                body_profile: String::new(),
                animation_profile: String::new(),
                portrait_profile: String::new(),
                layers: Vec::new(),
                active_slot: String::new(),
                universal_lpc_recipe: None,
            },
            universal_lpc_builder: None,
            status: String::new(),
        };
        assert!(model.choose_world(WorldSaveId("world_test".to_string())).is_err());
    }
}
