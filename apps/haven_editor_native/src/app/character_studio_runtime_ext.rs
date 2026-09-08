//! R31-R44 Character Studio production extensions.
//!
//! Kept out of the already-large core Character Studio module so later
//! wardrobe/layer/NPC workflows do not reverse the R29 decomposition rule.
use super::*;
use haven_assets::universal_lpc_npc_generation::{
    UniversalLpcNpcGenerationCatalog,
};
use haven_assets::universal_lpc_character_recipe::{UniversalLpcCharacterRecipe, UniversalLpcSelection};
use haven_assets::universal_lpc_resolver::UniversalLpcCharacterResolver;
use haven_assets::universal_lpc_equipment_catalog::UniversalLpcEquipmentItemSeedCatalog;
use haven_assets::universal_lpc_sheet_definition::DEFAULT_ULPC_SOURCE_ROOT;
use std::path::PathBuf;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum CharacterLayerViewMode {
    Composition,
    EquipmentSlots,
}

impl CharacterLayerViewMode {
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Composition => "Composition",
            Self::EquipmentSlots => "Equipment Slots",
        }
    }
}

const CHARACTER_EQUIPMENT_SLOT_CATEGORIES: [(&str, &str); 12] = [
    ("hat", "Headwear"),
    ("neck", "Neck"),
    ("torso", "Torso"),
    ("arms", "Arms / Shoulders"),
    ("hands", "Hands"),
    ("legs", "Legs"),
    ("feet", "Feet"),
    ("back", "Back"),
    ("accessory", "Accessory"),
    ("weapon", "Main Hand"),
    ("shield", "Off Hand"),
    ("tools", "Tool"),
];

#[derive(Clone, Debug)]
pub(crate) struct RuntimeCharacterAnimationSource {
    pub source_path: PathBuf,
    pub display_name: String,
    pub item_id: String,
    pub source_animation: String,
    pub frame_size: u32,
}

#[derive(Clone, Debug)]
pub(crate) struct CharacterSemanticLayerRow {
    pub label: String,
    pub slot: String,
    pub item_id: String,
    pub group: &'static str,
    pub current_action_available: bool,
    pub presentation_note: Option<String>,
    pub empty_slot: bool,
    pub preview_visible: bool,
    pub locked_order: bool,
}

fn semantic_character_group(slot: &str) -> &'static str {
    match slot {
        "body" | "head" => "Foundation",
        "eyes" | "eyebrows" | "nose" | "ears" | "hair" | "beards" | "expression"
        | "wings" | "tail" | "mobility" | "effects" => "Appearance",
        "hat" | "headwear" | "neck" | "torso" | "arms" | "hands" | "legs" | "feet"
        | "accessory" | "accessories" | "back" => "Wardrobe",
        "weapon" | "weapons" | "shield" | "shields" | "tools" | "main_hand" | "off_hand" => "Held",
        _ => "Equipment",
    }
}

impl CharacterStudioState {
    fn npc_profile_catalog(&self) -> Result<UniversalLpcNpcGenerationCatalog, String> {
        UniversalLpcNpcGenerationCatalog::load_default()
    }

    pub(crate) fn npc_profile_label(&self) -> String {
        if let Some(draft) = self.npc_profile_draft.as_ref() {
            return format!("{} *", draft.id);
        }
        self.npc_profile_catalog()
            .ok()
            .and_then(|catalog| catalog.profiles.get(self.npc_profile_index).map(|profile| profile.id.clone()))
            .unwrap_or_else(|| "NPC Profile unavailable".to_string())
    }

    pub(crate) fn npc_profile_detail_lines(&self) -> Vec<String> {
        let Ok(catalog) = self.npc_profile_catalog() else {
            return vec!["NPC profile catalog unavailable".to_string()];
        };
        let Some(raw) = catalog.profiles.get(self.npc_profile_index) else {
            return vec!["NPC profile unavailable".to_string()];
        };
        let profile = if let Some(draft) = self.npc_profile_draft.as_ref() {
            draft.clone()
        } else {
            let Ok(profile) = catalog.resolved_profile(&raw.id) else {
                return vec![format!("{} has invalid inherited rules", raw.id)];
            };
            profile
        };
        let maximum = profile
            .population
            .maximum
            .map(|value| value.to_string())
            .unwrap_or_else(|| "unbounded".to_string());
        vec![
            format!("Profile: {} · v{}", profile.id, profile.profile_version.max(1)),
            format!(
                "Inheritance: {}",
                raw.extends.as_deref().unwrap_or("root profile")
            ),
            format!(
                "Region / roles: {} · {}",
                if profile.region.is_empty() { "Any" } else { &profile.region },
                if profile.roles.is_empty() { "resident".to_string() } else { profile.roles.join(", ") }
            ),
            format!(
                "Faction / wealth: {} · {}",
                if profile.factions.is_empty() { "unrestricted".to_string() } else { profile.factions.join(", ") },
                if profile.wealth_tiers.is_empty() { "unrestricted".to_string() } else { profile.wealth_tiers.join(", ") }
            ),
            format!(
                "Required animation: {}",
                if profile.required_animations.is_empty() { "none".to_string() } else { profile.required_animations.join(", ") }
            ),
            format!(
                "Population: min {} · max {} · weight {}{}{}",
                profile.population.minimum,
                maximum,
                profile.population.weight,
                if profile.population.requires_home { " · home" } else { "" },
                if profile.population.requires_workplace { " · workplace" } else { "" },
            ),
            format!(
                "Wardrobe / gear: {} · {}",
                if profile.wardrobe_categories.is_empty() { "default wardrobe".to_string() } else { profile.wardrobe_categories.join(", ") },
                if profile.equipment_categories.is_empty() { "no required gear".to_string() } else { profile.equipment_categories.join(", ") }
            ),
        ]
    }

    pub(crate) fn npc_profile_constraint_summary(&self) -> String {
        let Ok(catalog) = self.npc_profile_catalog() else {
            return "NPC profile rules unavailable".to_string();
        };
        let Some(raw) = catalog.profiles.get(self.npc_profile_index) else {
            return "NPC profile unavailable".to_string();
        };
        let profile = if let Some(draft) = self.npc_profile_draft.as_ref() {
            draft.clone()
        } else {
            let Ok(profile) = catalog.resolved_profile(&raw.id) else {
                return "NPC profile inheritance is invalid".to_string();
            };
            profile
        };
        format!(
            "{} · {} role{} · {} required animation{} · population weight {}",
            if profile.region.is_empty() { "Any region" } else { &profile.region },
            profile.roles.len(),
            if profile.roles.len() == 1 { "" } else { "s" },
            profile.required_animations.len(),
            if profile.required_animations.len() == 1 { "" } else { "s" },
            profile.population.weight,
        )
    }

    pub(crate) fn cycle_npc_profile(&mut self, delta: i32) -> String {
        let Ok(catalog) = self.npc_profile_catalog() else {
            return "NPC generation profiles are unavailable".to_string();
        };
        if catalog.profiles.is_empty() {
            return "NPC generation profile catalog is empty".to_string();
        }
        self.npc_profile_index = cycle_index(
            self.npc_profile_index.min(catalog.profiles.len() - 1),
            catalog.profiles.len(),
            delta,
        );
        self.npc_profile_editor_open = false;
        self.npc_profile_draft = None;
        format!("NPC profile: {}", catalog.profiles[self.npc_profile_index].id)
    }

    pub(crate) fn generate_selected_npc_profile(&mut self) -> String {
        if self.mode != CharacterStudioMode::Npc {
            return "Switch Character Studio to NPC mode before generating an NPC profile".to_string();
        }
        let Some(builder) = self.builder_catalog.as_ref() else {
            return "Universal LPC definition catalog is unavailable".to_string();
        };
        let Some(authority) = self.authority.as_ref() else {
            return "Universal LPC authority is unavailable".to_string();
        };
        let Ok(mut catalog) = self.npc_profile_catalog() else {
            return "NPC generation profiles are unavailable".to_string();
        };
        let profile_id = if let Some(draft) = self.npc_profile_draft.as_ref() {
            if let Some(index) = catalog.profiles.iter().position(|profile| profile.id == draft.id) {
                catalog.profiles[index] = draft.clone();
            } else {
                catalog.profiles.push(draft.clone());
            }
            draft.id.clone()
        } else {
            let Some(profile) = catalog.profiles.get(self.npc_profile_index) else {
                return "Selected NPC profile is unavailable".to_string();
            };
            profile.id.clone()
        };
        let seed = self.npc_generation_seed;
        let generated = match catalog.generate_recipe_with_builder_report(
            &profile_id,
            seed,
            &authority.source_commit,
            builder,
        ) {
            Ok(result) => result,
            Err(error) => return format!("NPC generation failed: {error}"),
        };
        let generation_warnings = generated.warnings;
        let typed = generated.recipe;
        let sex = typed
            .identity
            .authored_traits
            .iter()
            .find_map(|value| value.strip_prefix("sex:"))
            .unwrap_or("Male");
        self.sex = if sex.eq_ignore_ascii_case("female") {
            CharacterSexFilter::Female
        } else {
            CharacterSexFilter::Male
        };
        self.age = if typed.identity.age_group.eq_ignore_ascii_case("child") {
            CharacterAgeFilter::Child
        } else if typed.identity.age_group.eq_ignore_ascii_case("teen") {
            CharacterAgeFilter::Teen
        } else if typed.identity.age_group.eq_ignore_ascii_case("elder")
            || typed.identity.age_group.eq_ignore_ascii_case("elderly")
        {
            CharacterAgeFilter::Elder
        } else {
            CharacterAgeFilter::Adult
        };
        let layers = {
            let mut layers = Vec::new();
            {
                let mut push_selection = |group: &str, selection: &UniversalLpcSelection| {
                    let slot = builder
                        .option(&selection.item_id)
                        .map(|option| option.category.clone())
                        .unwrap_or_else(|| group.to_string());
                    layers.push(CharacterRecipeDraftLayer {
                        slot,
                        source: selection.definition_source.clone(),
                        item_id: Some(selection.item_id.clone()),
                        variant: selection.variant.clone(),
                        selection_group: Some(group.to_string()),
                        selected_license: selection.selected_license.clone(),
                        share_alike_required: selection.share_alike_required,
                    });
                };
                for (group, selection) in &typed.selections {
                    push_selection(group, selection);
                }
                if let Some(selection) = typed.equipment.main_hand.as_ref() {
                    push_selection("main_hand", selection);
                }
                if let Some(selection) = typed.equipment.off_hand.as_ref() {
                    push_selection("off_hand", selection);
                }
                for (group, selection) in &typed.equipment.equipped {
                    push_selection(group, selection);
                }
            }
            layers
        };
        self.recipe = CharacterRecipeDraft {
            schema: CHARACTER_STUDIO_DRAFT_SCHEMA.to_string(),
            mode: CharacterStudioMode::Npc.label().to_string(),
            template: format!("npc_profile:{profile_id}"),
            sex: self.sex.label().to_string(),
            age: self.age.label().to_string(),
            direction: self.direction_label().to_string(),
            action: self.action_label().to_string(),
            palette_variant: self.palette_variant,
            layers,
        };
        self.locked_slots.clear();
        self.selected_recipe_layer = self.recipe.layers.len().saturating_sub(1);
        self.npc_generation_seed = self
            .npc_generation_seed
            .wrapping_add(0x9E37_79B9_7F4A_7C15);
        self.rebuild_filter();
        self.restart_preview_animation();
        self.sync_assembled_preview();
        let message = if generation_warnings.is_empty() {
            format!(
                "Generated deterministic {profile_id} NPC · seed {seed} · {} resolved recipe layers · profile constraints satisfied",
                self.recipe.layers.len()
            )
        } else {
            format!(
                "Generated deterministic {profile_id} NPC · seed {seed} · {} resolved recipe layers · {} coverage/setup warning(s): {}",
                self.recipe.layers.len(),
                generation_warnings.len(),
                generation_warnings.join(" | ")
            )
        };
        self.recipe_message = Some(message.clone());
        message
    }

    pub(crate) fn npc_profile_editor_open(&self) -> bool { self.npc_profile_editor_open }

    pub(crate) fn toggle_npc_profile_editor(&mut self) -> String {
        if self.npc_profile_editor_open {
            self.npc_profile_editor_open = false;
            self.npc_profile_draft = None;
            return "Closed NPC Profile Rules draft without changing the base profile".to_string();
        }
        let Ok(catalog) = self.npc_profile_catalog() else {
            return "NPC profile catalog unavailable".to_string();
        };
        let Some(raw) = catalog.profiles.get(self.npc_profile_index) else {
            return "Selected NPC profile unavailable".to_string();
        };
        let Ok(mut draft) = catalog.resolved_profile(&raw.id) else {
            return format!("{} has invalid inherited rules", raw.id);
        };
        let parent_id = raw.id.clone();
        draft.id = format!("{}_variant_{:04x}", parent_id, self.npc_generation_seed & 0xffff);
        draft.extends = Some(parent_id.clone());
        draft.profile_version = draft.profile_version.max(1) + 1;
        self.npc_profile_draft = Some(draft);
        self.npc_profile_editor_open = true;
        self.advanced_open = true;
        format!("Editing derived NPC profile rules from {parent_id}; base profile remains read-only")
    }

    pub(crate) fn npc_profile_draft_population_label(&self) -> String {
        let Some(draft) = self.npc_profile_draft.as_ref() else {
            return "Profile Rules".to_string();
        };
        let max = draft.population.maximum
            .map(|value| value.to_string())
            .unwrap_or_else(|| "∞".to_string());
        format!(
            "min {} · max {} · wt {}",
            draft.population.minimum, max, draft.population.weight
        )
    }

    pub(crate) fn npc_profile_draft_maximum_label(&self) -> String {
        self.npc_profile_draft
            .as_ref()
            .and_then(|draft| draft.population.maximum)
            .map(|value| format!("Max {value}"))
            .unwrap_or_else(|| "Max ∞".to_string())
    }

    pub(crate) fn npc_profile_draft_weight_label(&self) -> String {
        self.npc_profile_draft
            .as_ref()
            .map(|draft| format!("Weight {}", draft.population.weight))
            .unwrap_or_else(|| "Weight".to_string())
    }

    pub(crate) fn npc_profile_draft_requires_home(&self) -> bool {
        self.npc_profile_draft.as_ref().is_some_and(|draft| draft.population.requires_home)
    }

    pub(crate) fn npc_profile_draft_requires_workplace(&self) -> bool {
        self.npc_profile_draft.as_ref().is_some_and(|draft| draft.population.requires_workplace)
    }

    pub(crate) fn adjust_npc_profile_minimum(&mut self, delta: i32) -> String {
        let Some(draft) = self.npc_profile_draft.as_mut() else {
            return "Open Profile Rules before changing population constraints".to_string();
        };
        let next = (draft.population.minimum as i64 + delta as i64).clamp(0, 999) as u32;
        draft.population.minimum = next;
        if let Some(maximum) = draft.population.maximum {
            if maximum < next { draft.population.maximum = Some(next); }
        }
        format!("{} minimum population: {}", draft.id, next)
    }

    pub(crate) fn adjust_npc_profile_maximum(&mut self, delta: i32) -> String {
        let Some(draft) = self.npc_profile_draft.as_mut() else {
            return "Open Profile Rules before changing population constraints".to_string();
        };
        let current = draft.population.maximum.unwrap_or(draft.population.minimum.max(1));
        let next = (current as i64 + delta as i64)
            .clamp(draft.population.minimum as i64, 999) as u32;
        draft.population.maximum = Some(next);
        format!("{} maximum population: {}", draft.id, next)
    }

    pub(crate) fn toggle_npc_profile_unbounded_maximum(&mut self) -> String {
        let Some(draft) = self.npc_profile_draft.as_mut() else {
            return "Open Profile Rules before changing population constraints".to_string();
        };
        if draft.population.maximum.take().is_some() {
            format!("{} maximum population: unbounded", draft.id)
        } else {
            let value = draft.population.minimum.max(1);
            draft.population.maximum = Some(value);
            format!("{} maximum population: {}", draft.id, value)
        }
    }

    pub(crate) fn adjust_npc_profile_weight(&mut self, delta: i32) -> String {
        let Some(draft) = self.npc_profile_draft.as_mut() else {
            return "Open Profile Rules before changing population constraints".to_string();
        };
        let next = (draft.population.weight as i64 + delta as i64).clamp(0, 100) as u32;
        draft.population.weight = next;
        format!("{} population weight: {}", draft.id, next)
    }

    pub(crate) fn toggle_npc_profile_home_requirement(&mut self) -> String {
        let Some(draft) = self.npc_profile_draft.as_mut() else {
            return "Open Profile Rules before changing population constraints".to_string();
        };
        draft.population.requires_home = !draft.population.requires_home;
        format!("{} requires home: {}", draft.id, draft.population.requires_home)
    }

    pub(crate) fn toggle_npc_profile_workplace_requirement(&mut self) -> String {
        let Some(draft) = self.npc_profile_draft.as_mut() else {
            return "Open Profile Rules before changing population constraints".to_string();
        };
        draft.population.requires_workplace = !draft.population.requires_workplace;
        format!("{} requires workplace: {}", draft.id, draft.population.requires_workplace)
    }

    pub(crate) fn save_npc_profile_variant(&mut self) -> String {
        let Some(draft) = self.npc_profile_draft.clone() else {
            return "Open Profile Rules before saving a derived NPC profile".to_string();
        };
        let Ok(catalog) = self.npc_profile_catalog() else {
            return "NPC profile catalog unavailable".to_string();
        };
        if let Err(error) = catalog.validate() {
            return format!("NPC profile catalog invalid before save: {error}");
        }
        let path = match catalog.save_profile_variant_default(&draft) {
            Ok(path) => path,
            Err(error) => return format!("NPC profile variant save failed: {error}"),
        };
        match self.npc_profile_catalog() {
            Ok(reloaded) => {
                if let Some(index) = reloaded.profiles.iter().position(|profile| profile.id == draft.id) {
                    self.npc_profile_index = index;
                }
            }
            Err(error) => return format!("Saved {path}, but reload failed: {error}"),
        }
        self.npc_profile_editor_open = false;
        self.npc_profile_draft = None;
        format!("Saved derived NPC profile {} → {path}", draft.id)
    }

    /// A semantic Character Layer is a live view of the exact recipe, not a
    /// second compositor. Missing action coverage keeps the row visible so the
    /// editor can explain disappearing garments instead of pretending unequip.
    pub(crate) fn semantic_layer_rows(&self) -> Vec<CharacterSemanticLayerRow> {
        if self.layer_view_mode == CharacterLayerViewMode::EquipmentSlots {
            return CHARACTER_EQUIPMENT_SLOT_CATEGORIES
                .iter()
                .map(|(slot, slot_label)| {
                    let layer = self.recipe.layers.iter().find(|layer| {
                        layer.slot == *slot
                            || layer.selection_group.as_deref() == Some(*slot)
                    });
                    let item_id = layer
                        .and_then(|layer| layer.item_id.clone())
                        .unwrap_or_default();
                    let label = if item_id.is_empty() {
                        format!("{slot_label} — Empty")
                    } else {
                        self.builder_catalog
                            .as_ref()
                            .and_then(|builder| builder.option(&item_id))
                            .map(|option| format!("{slot_label} — {}", option.display_name))
                            .unwrap_or_else(|| format!("{slot_label} — {item_id}"))
                    };
                    let user_hidden = !item_id.is_empty() && self.preview_hidden_items.contains(&item_id);
                    let presentation_note = if item_id.is_empty() {
                        None
                    } else if user_hidden {
                        Some("Preview hidden by user; equipment remains in the recipe".to_string())
                    } else {
                        self.presentation_issues
                            .iter()
                            .find(|issue| issue.item_id == item_id)
                            .map(|issue| issue.reason.clone())
                    };
                    let current_action_available = item_id.is_empty()
                        || self
                            .assembled_preview_layers
                            .iter()
                            .any(|resolved| resolved.slot == item_id);
                    let preview_visible = layer.is_none() || (!user_hidden && presentation_note.is_none());
                    CharacterSemanticLayerRow {
                        label,
                        slot: (*slot).to_string(),
                        item_id,
                        group: "Equipment Slot",
                        current_action_available,
                        presentation_note,
                        empty_slot: layer.is_none(),
                        preview_visible,
                        locked_order: true,
                    }
                })
                .collect();
        }

        self.recipe
            .layers
            .iter()
            .map(|layer| {
                let item_id = layer.item_id.clone().unwrap_or_else(|| layer.slot.clone());
                let label = self
                    .builder_catalog
                    .as_ref()
                    .and_then(|builder| builder.option(&item_id))
                    .map(|option| option.display_name.clone())
                    .unwrap_or_else(|| {
                        item_id
                            .rsplit('/')
                            .next()
                            .unwrap_or(&item_id)
                            .replace('_', " ")
                    });
                let user_hidden = self.preview_hidden_items.contains(&item_id);
                let presentation_note = if user_hidden {
                    Some("Preview hidden by user; recipe selection is unchanged".to_string())
                } else {
                    self.presentation_issues
                        .iter()
                        .find(|issue| issue.item_id == item_id)
                        .map(|issue| issue.reason.clone())
                };
                let current_action_available = self
                    .assembled_preview_layers
                    .iter()
                    .any(|resolved| resolved.slot == item_id);
                let preview_visible = !user_hidden && presentation_note.is_none();
                CharacterSemanticLayerRow {
                    label,
                    slot: layer.slot.clone(),
                    item_id,
                    group: semantic_character_group(&layer.slot),
                    current_action_available,
                    presentation_note,
                    empty_slot: false,
                    preview_visible,
                    locked_order: true,
                }
            })
            .collect()
    }

    pub(crate) fn toggle_semantic_layer_preview(&mut self, index: usize) -> String {
        let rows = self.semantic_layer_rows();
        let Some(row) = rows.get(index) else {
            return "Character layer is unavailable".to_string();
        };
        if row.empty_slot || row.item_id.is_empty() {
            return format!("{} is empty; there is no visual layer to hide", row.label);
        }
        let item_id = row.item_id.clone();
        if self.preview_hidden_items.remove(&item_id) {
            format!("Preview restored: {} · recipe/equipment unchanged", row.label)
        } else {
            self.preview_hidden_items.insert(item_id);
            format!("Preview hidden: {} · recipe/equipment unchanged", row.label)
        }
    }

    pub(crate) fn reset_preview_visibility(&mut self) -> String {
        let count = self.preview_hidden_items.len();
        self.preview_hidden_items.clear();
        format!("Restored {count} Character preview visibility override(s)")
    }

    pub(crate) fn select_semantic_layer(&mut self, index: usize) -> String {
        if self.layer_view_mode == CharacterLayerViewMode::EquipmentSlots {
            self.selected_equipment_slot = index.min(CHARACTER_EQUIPMENT_SLOT_CATEGORIES.len().saturating_sub(1));
            let (slot, label) = CHARACTER_EQUIPMENT_SLOT_CATEGORIES[self.selected_equipment_slot];
            if let Some(category_index) = UNIVERSAL_LPC_CHARACTER_BUILDER_CATEGORIES
                .iter()
                .position(|category| category.id == slot)
            {
                self.select_slot_filter(category_index + 1);
            }
            if let Some(recipe_index) = self.recipe.layers.iter().position(|layer| {
                layer.slot == slot || layer.selection_group.as_deref() == Some(slot)
            }) {
                self.selected_recipe_layer = recipe_index;
                return format!("Equipment slot selected: {label} · Wardrobe filtered to compatible {slot} choices");
            }
            return format!("Equipment slot selected: {label} · Empty · choose a compatible item from Wardrobe & Gear");
        }
        if self.recipe.layers.is_empty() {
            return "Character recipe has no layers".to_string();
        }
        self.selected_recipe_layer = index.min(self.recipe.layers.len() - 1);
        let slot = self.recipe.layers[self.selected_recipe_layer].slot.clone();
        if let Some(category_index) = UNIVERSAL_LPC_CHARACTER_BUILDER_CATEGORIES
            .iter()
            .position(|category| category.id == slot)
        {
            self.select_slot_filter(category_index + 1);
        }
        let row = self
            .semantic_layer_rows()
            .into_iter()
            .nth(self.selected_recipe_layer);
        match row {
            Some(row) if row.presentation_note.is_some() => format!(
                "Character layer selected: {} [{}] • {}",
                row.label,
                row.slot,
                row.presentation_note.unwrap_or_default()
            ),
            Some(row) if row.current_action_available => format!(
                "Character layer selected: {} [{}] • {} coverage ready",
                row.label,
                row.slot,
                self.action_label()
            ),
            Some(row) => format!(
                "Character layer selected: {} [{}] • WARNING: no {} presentation; item remains equipped",
                row.label,
                row.slot,
                self.action_label()
            ),
            None => format!("Character layer selected: {slot}"),
        }
    }

    pub(crate) fn character_catalog_thumbnail_key(&self, visible_index: usize) -> Option<String> {
        let option_index = *self.filtered_indices.get(visible_index)?;
        let option = self.builder_catalog.as_ref()?.options.get(option_index)?;
        Some(format!(
            "character:{}:{}:{}",
            self.current_body_type().as_str(),
            option.item_id,
            option.variants.first().map(String::as_str).unwrap_or("default")
        ))
    }

    pub(crate) fn character_catalog_thumbnail_request(
        &self,
        visible_index: usize,
    ) -> Option<(String, PathBuf, Rect)> {
        let builder = self.builder_catalog.as_ref()?;
        let authority = self.authority.as_ref()?;
        let option_index = *self.filtered_indices.get(visible_index)?;
        let option = builder.options.get(option_index)?;
        let key = self.character_catalog_thumbnail_key(visible_index)?;
        let mut recipe = UniversalLpcCharacterRecipe::new(
            authority.source_commit.clone(),
            self.current_body_type(),
        );
        recipe.apply_identity_foundations(self.sex.label(), self.age.label());
        if option.category == "body" {
            recipe.selections.insert(
                "body".into(),
                UniversalLpcSelection {
                    item_id: option.item_id.clone(),
                    display_name: option.display_name.clone(),
                    locked: true,
                    ..Default::default()
                },
            );
        } else if option.category == "head" {
            recipe.selections.insert(
                "head".into(),
                UniversalLpcSelection {
                    item_id: option.item_id.clone(),
                    display_name: option.display_name.clone(),
                    locked: true,
                    ..Default::default()
                },
            );
        } else if builder
            .select_option(&mut recipe, &option.item_id, option.variants.first().cloned())
            .is_err()
        {
            return None;
        }
        let source_root = haven_assets::asset_intake::repo_root_dir().join(DEFAULT_ULPC_SOURCE_ROOT);
        let resolver = UniversalLpcCharacterResolver::with_source_root(&source_root, &builder.definitions);
        for action in ["idle", "walk", "run", "sit"] {
            let Ok(resolved) = resolver.resolve(&recipe, action) else { continue; };
            let Some(layer) = resolved.layers.iter().rev().find(|layer| layer.item_id == option.item_id) else {
                continue;
            };
            if !layer.source_path.is_file() {
                continue;
            }
            let frame_size = layer.frame_size.max(1);
            let frame = if animation_spec(&layer.source_animation).is_some() {
                frame_for_progress(&layer.source_animation, 0.0)
            } else {
                0
            };
            let row = character_direction_row(0, 4);
            return Some((
                key,
                layer.source_path.clone(),
                Rect::new(
                    (frame as u32 * frame_size) as f32,
                    (row as u32 * frame_size) as f32,
                    frame_size as f32,
                    frame_size as f32,
                ),
            ));
        }
        None
    }

    /// Resolve the visual source that the shared ULPC resolver actually selected
    /// for the runtime equipment/action pair. Gameplay item ids (`item.ulpc.*`)
    /// are first translated through the canonical item-seed catalog to the
    /// corresponding CharacterRecipe equipment source id (`ulpc.*`). This keeps
    /// F3/runtime navigation on the same source path the compositor used.
    pub(crate) fn resolve_runtime_animation_source(
        &self,
        runtime_item_id: Option<&str>,
        action_id: &str,
    ) -> Result<RuntimeCharacterAnimationSource, String> {
        let recipe = self.typed_recipe_from_draft()?;
        let builder = self
            .builder_catalog
            .as_ref()
            .ok_or_else(|| "Universal LPC sheet-definition catalog is unavailable".to_string())?;
        let source_root = haven_assets::asset_intake::repo_root_dir().join(DEFAULT_ULPC_SOURCE_ROOT);
        let resolver = UniversalLpcCharacterResolver::with_source_root(&source_root, &builder.definitions);
        let resolved = resolver.resolve(&recipe, action_id)?;

        let mapped_item_id = runtime_item_id.and_then(|item_id| {
            UniversalLpcEquipmentItemSeedCatalog::load_default()
                .ok()
                .and_then(|catalog| catalog.find(item_id).map(|item| item.equipment_source_id.clone()))
        });
        let selected_row_item_id = self
            .semantic_layer_rows()
            .get(self.selected_semantic_layer_index())
            .map(|row| row.item_id.clone())
            .filter(|value| !value.trim().is_empty());

        let matches_requested_item = |item_id: &str| {
            mapped_item_id.as_deref() == Some(item_id)
                || runtime_item_id == Some(item_id)
                || selected_row_item_id.as_deref() == Some(item_id)
        };
        let layer = if runtime_item_id.is_some() {
            resolved
                .layers
                .iter()
                .rev()
                .find(|layer| matches_requested_item(&layer.item_id))
                .ok_or_else(|| {
                    format!(
                        "Runtime equipment {} has no resolved visual for {}",
                        runtime_item_id.unwrap_or("equipment"),
                        action_id
                    )
                })?
        } else {
            resolved
                .layers
                .iter()
                .rev()
                .find(|layer| selected_row_item_id.as_deref() == Some(layer.item_id.as_str()))
                .or_else(|| resolved.layers.iter().rev().find(|layer| layer.source_path.is_file()))
                .ok_or_else(|| format!("Character action {action_id} resolved no editable visual source"))?
        };
        if !layer.source_path.is_file() {
            return Err(format!(
                "Resolved runtime source is missing: {}",
                layer.source_path.display()
            ));
        }
        let display_name = self
            .builder_catalog
            .as_ref()
            .and_then(|catalog| catalog.option(&layer.item_id))
            .map(|option| option.display_name.clone())
            .unwrap_or_else(|| layer.item_id.clone());
        Ok(RuntimeCharacterAnimationSource {
            source_path: layer.source_path.clone(),
            display_name,
            item_id: layer.item_id.clone(),
            source_animation: layer.source_animation.clone(),
            frame_size: layer.frame_size.max(1),
        })
    }

    pub(crate) fn select_runtime_equipment_slot(&mut self, runtime_slot: &str) -> bool {
        let semantic_slot = match runtime_slot {
            "main_hand" => "weapon",
            "off_hand" => "shield",
            other => other,
        };
        let Some(index) = CHARACTER_EQUIPMENT_SLOT_CATEGORIES.iter().position(|(slot, _)| {
            *slot == semantic_slot
                || (*slot == "tools" && semantic_slot == "tool")
                || (*slot == "accessory" && semantic_slot == "accessories")
        }) else {
            return false;
        };
        self.layer_view_mode = CharacterLayerViewMode::EquipmentSlots;
        self.selected_equipment_slot = index;
        true
    }

    pub(crate) fn selected_semantic_layer_index(&self) -> usize {
        if self.layer_view_mode == CharacterLayerViewMode::EquipmentSlots {
            self.selected_equipment_slot
        } else {
            self.selected_recipe_layer
        }
    }

    pub(crate) fn semantic_layer_count(&self) -> usize {
        if self.layer_view_mode == CharacterLayerViewMode::EquipmentSlots {
            CHARACTER_EQUIPMENT_SLOT_CATEGORIES.len()
        } else {
            self.recipe.layers.len()
        }
    }

    pub(crate) fn layer_view_label(&self) -> &'static str { self.layer_view_mode.label() }

    pub(crate) fn toggle_layer_view_mode(&mut self) -> String {
        self.layer_view_mode = match self.layer_view_mode {
            CharacterLayerViewMode::Composition => CharacterLayerViewMode::EquipmentSlots,
            CharacterLayerViewMode::EquipmentSlots => CharacterLayerViewMode::Composition,
        };
        format!("Character Layers: {}", self.layer_view_mode.label())
    }
}

impl EditorApp {
    pub(crate) fn load_visible_character_catalog_thumbnail(&mut self, rect: Rect) {
        let visible_cards = character_visible_cards(rect);
        for offset in 0..visible_cards {
            let visible_index = self.character_studio.list_offset + offset;
            let Some((key, path, source)) = self
                .character_studio
                .character_catalog_thumbnail_request(visible_index)
            else {
                continue;
            };
            if self.unified_asset_browser.contains_or_failed(&key) {
                continue;
            }
            if let Err(error) = self
                .unified_asset_browser
                .load_thumbnail_region(key, &path, source)
            {
                self.status_message = format!("Character thumbnail skipped: {error}");
            }
            break;
        }
    }

    pub(crate) fn draw_npc_profile_controls(&self, c: Rect) {
        if self.character_studio.mode != CharacterStudioMode::Npc {
            return;
        }
        draw_editor_widget(center_button_rect(c, 3, 0, 4), "‹ Profile", false);
        super::super::gui_controls::draw_control(
            center_button_rect(c, 3, 1, 4),
            &self.character_studio.npc_profile_label(),
            super::super::gui_controls::GuiControlClass::Toggle,
            self.character_studio.npc_profile_editor_open(),
            true,
        );
        draw_editor_widget(center_button_rect(c, 3, 2, 4), "Profile ›", false);
        super::super::gui_controls::draw_control(
            center_button_rect(c, 3, 3, 4),
            "Generate",
            super::super::gui_controls::GuiControlClass::Primary,
            false,
            true,
        );
    }

    pub(crate) fn draw_npc_profile_rule_editor(&self, c: Rect) {
        if self.character_studio.mode != CharacterStudioMode::Npc
            || !self.character_studio.advanced_open()
            || !self.character_studio.npc_profile_editor_open()
        {
            return;
        }
        draw_scissored_text(
            "NPC PROFILE RULES · derived variant",
            c.x,
            c.y + 16.0 * 32.0 - 6.0,
            c.w,
            10.5,
            MUTED,
        );
        draw_editor_widget(center_button_rect(c, 17, 0, 3), "Min -", false);
        draw_editor_widget(
            center_button_rect(c, 17, 1, 3),
            &self.character_studio.npc_profile_draft_population_label(),
            true,
        );
        draw_editor_widget(center_button_rect(c, 17, 2, 3), "Min +", false);
        draw_editor_widget(center_button_rect(c, 18, 0, 3), "Max -", false);
        draw_editor_widget(
            center_button_rect(c, 18, 1, 3),
            &self.character_studio.npc_profile_draft_maximum_label(),
            true,
        );
        draw_editor_widget(center_button_rect(c, 18, 2, 3), "Max +", false);
        draw_editor_widget(center_button_rect(c, 19, 0, 3), "Weight -", false);
        draw_editor_widget(
            center_button_rect(c, 19, 1, 3),
            &self.character_studio.npc_profile_draft_weight_label(),
            true,
        );
        draw_editor_widget(center_button_rect(c, 19, 2, 3), "Weight +", false);
        super::super::gui_controls::draw_control(
            center_button_rect(c, 20, 0, 3),
            "Requires Home",
            super::super::gui_controls::GuiControlClass::Toggle,
            self.character_studio.npc_profile_draft_requires_home(),
            true,
        );
        super::super::gui_controls::draw_control(
            center_button_rect(c, 20, 1, 3),
            "Requires Work",
            super::super::gui_controls::GuiControlClass::Toggle,
            self.character_studio.npc_profile_draft_requires_workplace(),
            true,
        );
        super::super::gui_controls::draw_control(
            center_button_rect(c, 20, 2, 3),
            "Save Variant",
            super::super::gui_controls::GuiControlClass::Primary,
            false,
            true,
        );
    }

    pub(crate) fn handle_npc_profile_controls(&mut self, mouse: Vec2, c: Rect) -> bool {
        if self.character_studio.mode != CharacterStudioMode::Npc {
            return false;
        }
        if center_button_rect(c, 3, 0, 4).contains(mouse) {
            self.status_message = self.character_studio.cycle_npc_profile(-1);
            return true;
        }
        if center_button_rect(c, 3, 1, 4).contains(mouse) {
            self.status_message = self.character_studio.toggle_npc_profile_editor();
            return true;
        }
        if center_button_rect(c, 3, 2, 4).contains(mouse) {
            self.status_message = self.character_studio.cycle_npc_profile(1);
            return true;
        }
        if center_button_rect(c, 3, 3, 4).contains(mouse) {
            self.status_message = self.character_studio.generate_selected_npc_profile();
            return true;
        }
        if self.character_studio.advanced_open() && self.character_studio.npc_profile_editor_open() {
            if center_button_rect(c, 17, 0, 3).contains(mouse) {
                self.status_message = self.character_studio.adjust_npc_profile_minimum(-1);
                return true;
            }
            if center_button_rect(c, 17, 2, 3).contains(mouse) {
                self.status_message = self.character_studio.adjust_npc_profile_minimum(1);
                return true;
            }
            if center_button_rect(c, 18, 0, 3).contains(mouse) {
                self.status_message = self.character_studio.adjust_npc_profile_maximum(-1);
                return true;
            }
            if center_button_rect(c, 18, 1, 3).contains(mouse) {
                self.status_message = self.character_studio.toggle_npc_profile_unbounded_maximum();
                return true;
            }
            if center_button_rect(c, 18, 2, 3).contains(mouse) {
                self.status_message = self.character_studio.adjust_npc_profile_maximum(1);
                return true;
            }
            if center_button_rect(c, 19, 0, 3).contains(mouse) {
                self.status_message = self.character_studio.adjust_npc_profile_weight(-1);
                return true;
            }
            if center_button_rect(c, 19, 2, 3).contains(mouse) {
                self.status_message = self.character_studio.adjust_npc_profile_weight(1);
                return true;
            }
            if center_button_rect(c, 20, 0, 3).contains(mouse) {
                self.status_message = self.character_studio.toggle_npc_profile_home_requirement();
                return true;
            }
            if center_button_rect(c, 20, 1, 3).contains(mouse) {
                self.status_message = self.character_studio.toggle_npc_profile_workplace_requirement();
                return true;
            }
            if center_button_rect(c, 20, 2, 3).contains(mouse) {
                self.status_message = self.character_studio.save_npc_profile_variant();
                return true;
            }
        }
        false
    }
}

// R31 visual Wardrobe/Create catalog rendering is intentionally kept in the
// runtime extension so the core Character Studio authority stays decomposed.
impl EditorApp {
    pub(crate) fn draw_character_catalog(&self, rect: Rect) {
        for (index, section) in [CharacterCatalogSection::Create, CharacterCatalogSection::WardrobeGear]
            .into_iter()
            .enumerate()
        {
            super::gui_controls::draw_control(
                character_catalog_section_rect(rect, index),
                section.label(),
                super::gui_controls::GuiControlClass::Segmented,
                self.character_studio.catalog_section() == section,
                true,
            );
        }
        let search = character_search_rect(rect);
        draw_rectangle(search.x, search.y, search.w, search.h, CONTROL_BG);
        draw_rectangle_lines(
            search.x, search.y, search.w, search.h, 1.0,
            if self.text_focus == EditorTextFocus::CharacterAssetFilter {
                editor_theme::colors::SELECTION_OUTLINE
            } else { PANEL_EDGE },
        );
        let text = if self.character_studio.query.is_empty() {
            CHARACTER_CATALOG_SEARCH_PLACEHOLDER
        } else { &self.character_studio.query };
        draw_scissored_text(text, search.x + 8.0, search.y + 20.0, search.w - 16.0, 13.0, MUTED);
        draw_editor_text(
            &format!("{} choices | {}", self.character_studio.filtered_count(), self.character_studio.slot_display_label()),
            rect.x, rect.y + 86.0, 13.0, MUTED,
        );

        let Some(builder) = self.character_studio.builder_catalog.as_ref() else {
            draw_wrapped(
                self.character_studio.load_error().unwrap_or("Universal LPC sheet-definition catalog is unavailable."),
                rect.x, rect.y + 112.0, rect.w, 15.0, WARN,
            );
            return;
        };

        let visible_cards = character_visible_cards(rect);
        for card in 0..visible_cards {
            let visible_index = self.character_studio.list_offset + card;
            let Some(option_index) = self.character_studio.filtered_indices.get(visible_index) else { break; };
            let Some(option) = builder.options.get(*option_index) else { continue; };
            let card_rect = character_card_rect(rect, card);
            let selected = visible_index == self.character_studio.selected_visible_index();
            draw_rectangle(
                card_rect.x, card_rect.y, card_rect.w, card_rect.h,
                if selected { editor_theme::colors::SELECTION_FILL } else { CONTROL_BG },
            );
            draw_rectangle_lines(
                card_rect.x, card_rect.y, card_rect.w, card_rect.h,
                if selected { 2.0 } else { 1.0 },
                if selected { editor_theme::colors::SELECTION_OUTLINE } else { PANEL_EDGE },
            );
            let thumb = Rect::new(card_rect.x + 5.0, card_rect.y + 5.0, card_rect.w - 10.0, 70.0);
            if let Some(key) = self.character_studio.character_catalog_thumbnail_key(visible_index) {
                if let Some(texture) = self.unified_asset_browser.texture(&key) {
                    let scale = (thumb.w / texture.width()).min(thumb.h / texture.height()).max(0.01);
                    let size = vec2(texture.width() * scale, texture.height() * scale);
                    draw_texture_ex(
                        texture,
                        thumb.x + (thumb.w - size.x) * 0.5,
                        thumb.y + (thumb.h - size.y) * 0.5,
                        WHITE,
                        DrawTextureParams { dest_size: Some(size), ..Default::default() },
                    );
                } else {
                    draw_scissored_text("loading…", thumb.x, thumb.y + 38.0, thumb.w, 10.5, MUTED);
                }
            }
            let coverage = if option.supports_animation(self.character_studio.action_id()) { "✓" } else { "⚠" };
            draw_scissored_text(
                &format!("{coverage} {}", option.display_name),
                card_rect.x + 5.0, card_rect.y + 89.0, card_rect.w - 10.0, 11.0, TEXT,
            );
            let flags = format!(
                "{}{}{}",
                if option.variants.len() > 1 { format!("{} variants", option.variants.len()) } else { option.category.clone() },
                if option.share_alike_required() { " · SA" } else { "" },
                if option.animations.iter().any(|animation| custom_animation_spec(animation).is_some()) { " · animated" } else { "" },
            );
            draw_scissored_text(&flags, card_rect.x + 5.0, card_rect.y + 105.0, card_rect.w - 10.0, 9.5, MUTED);
        }
        draw_scissored_text(
            "Mouse wheel / arrows / PageUp-PageDown browse the visual compatible catalog.",
            rect.x,
            rect.y + rect.h - 4.0,
            rect.w,
            10.5,
            MUTED,
        );
    }

}
