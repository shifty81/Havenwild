use std::collections::BTreeSet;
use std::path::{Path, PathBuf};

use crate::universal_lpc_animation::UniversalLpcBodyType;
use crate::universal_lpc_character_recipe::{
    universal_lpc_foundation_head_kind, HavenwildCharacterIdentityMetadata,
    UniversalLpcCharacterRecipe, UniversalLpcSelection,
};
use crate::universal_lpc_sheet_definition::{
    UniversalLpcDefinitionCatalog, UniversalLpcDefinitionRecord, DEFAULT_ULPC_SOURCE_ROOT,
};

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct UniversalLpcBuilderOption {
    pub item_id: String,
    pub display_name: String,
    pub category: String,
    pub selection_group: String,
    pub definition_path: PathBuf,
    pub variants: Vec<String>,
    pub animations: Vec<String>,
    pub tags: BTreeSet<String>,
    pub required_tags: BTreeSet<String>,
    pub excluded_tags: BTreeSet<String>,
    pub licenses: BTreeSet<String>,
    pub source_urls: BTreeSet<String>,
    pub priority: i32,
}

impl UniversalLpcBuilderOption {
    pub fn supports_body(&self, catalog: &UniversalLpcDefinitionCatalog, body: UniversalLpcBodyType) -> bool {
        catalog.find(&self.item_id)
            .is_some_and(|record| record.definition.layers().iter().any(|(_, layer)| layer.path_for_body(body).is_some()))
    }

    pub fn supports_animation(&self, animation: &str) -> bool {
        self.animations.is_empty() || self.animations.iter().any(|value| value == animation)
    }

    pub fn preferred_license(&self) -> Option<&str> {
        self.licenses.iter()
            .find(|license| is_preferred_character_license(license))
            .map(String::as_str)
            .or_else(|| self.licenses.iter().next().map(String::as_str))
    }

    pub fn share_alike_required(&self) -> bool {
        !self.licenses.is_empty()
            && self.licenses.iter().all(|license| !is_preferred_character_license(license))
            && self.licenses.iter().any(|license| license.to_ascii_lowercase().contains("by-sa"))
    }

    pub fn is_selectable(&self, include_share_alike: bool) -> bool {
        self.licenses.is_empty()
            || self.licenses.iter().any(|license| is_preferred_character_license(license))
            || (include_share_alike && self.licenses.iter().any(|license| license.to_ascii_lowercase().contains("by-sa")))
    }
}

#[derive(Clone, Debug, Default, PartialEq)]
pub struct UniversalLpcCharacterBuilderCatalog {
    pub definitions: UniversalLpcDefinitionCatalog,
    pub options: Vec<UniversalLpcBuilderOption>,
}

impl UniversalLpcCharacterBuilderCatalog {
    pub fn load_default_source() -> Result<Self, String> {
        Self::load_source_root(Path::new(DEFAULT_ULPC_SOURCE_ROOT))
    }

    pub fn load_source_root(source_root: &Path) -> Result<Self, String> {
        let definitions = UniversalLpcDefinitionCatalog::load_source_root(source_root)?;
        Ok(Self::from_definitions(definitions))
    }

    pub fn from_definitions(definitions: UniversalLpcDefinitionCatalog) -> Self {
        let mut options = definitions.records.iter()
            .filter_map(builder_option_from_record)
            .collect::<Vec<_>>();
        options.sort_by(|left, right| {
            left.category.cmp(&right.category)
                .then_with(|| right.priority.cmp(&left.priority))
                .then_with(|| left.display_name.cmp(&right.display_name))
                .then_with(|| left.item_id.cmp(&right.item_id))
        });
        Self { definitions, options }
    }

    pub fn option(&self, item_id: &str) -> Option<&UniversalLpcBuilderOption> {
        self.options.iter().find(|option| option.item_id == item_id)
    }

    pub fn options_for<'a>(
        &'a self,
        category: &'a str,
        body: UniversalLpcBodyType,
    ) -> impl Iterator<Item = &'a UniversalLpcBuilderOption> + 'a {
        self.options.iter().filter(move |option| {
            (category == "all" || option.category == category)
                && option.supports_body(&self.definitions, body)
        })
    }

    pub fn definition_for_source(
        &self,
        relative_source: &str,
        body: UniversalLpcBodyType,
    ) -> Option<&UniversalLpcDefinitionRecord> {
        let source = normalize_source(relative_source);
        self.definitions.records.iter()
            .filter_map(|record| {
                let longest = record.definition.layers().iter()
                    .filter_map(|(_, layer)| layer.path_for_body(body))
                    .map(normalize_source)
                    .filter(|prefix| source.starts_with(prefix))
                    .map(|prefix| prefix.len())
                    .max()?;
                Some((longest, record))
            })
            .max_by_key(|(length, _)| *length)
            .map(|(_, record)| record)
    }

    pub fn foundation_recipe(
        &self,
        source_commit: impl Into<String>,
        sex: &str,
        age_group: &str,
    ) -> Result<UniversalLpcCharacterRecipe, String> {
        let body = crate::universal_lpc_character_recipe::universal_lpc_body_type_for_identity(sex, age_group);
        let mut recipe = UniversalLpcCharacterRecipe::new(source_commit, body);
        recipe.identity = HavenwildCharacterIdentityMetadata {
            age_group: normalize_age(age_group).to_string(),
            ..Default::default()
        };
        let body_id = "body_body";
        let head_id = foundation_head_item_id(sex, age_group);
        if self.definitions.find(body_id).is_none() {
            return Err(format!("ULPC character catalog is missing foundation body definition {body_id}"));
        }
        if self.definitions.find(&head_id).is_none() {
            return Err(format!("ULPC character catalog is missing foundation head definition {head_id}"));
        }
        let mut body_selection = self.selection_for_option(body_id, None)?;
        body_selection.locked = true;
        let mut head_selection = self.selection_for_option(&head_id, None)?;
        head_selection.locked = true;
        recipe.selections.insert("body".into(), body_selection);
        recipe.selections.insert("head".into(), head_selection);
        recipe.validate()?;
        Ok(recipe)
    }

    pub fn compatible_option<'a>(
        &'a self,
        recipe: &UniversalLpcCharacterRecipe,
        option: &'a UniversalLpcBuilderOption,
    ) -> bool {
        if !option.supports_body(&self.definitions, recipe.body_type) {
            return false;
        }
        let active = active_recipe_tags(recipe, self);
        option.required_tags.iter().all(|tag| active.contains(tag))
            && option.excluded_tags.iter().all(|tag| !active.contains(tag))
    }

    pub fn selection_for_option(
        &self,
        item_id: &str,
        variant: Option<String>,
    ) -> Result<UniversalLpcSelection, String> {
        let option = self.option(item_id)
            .ok_or_else(|| format!("unknown ULPC character builder item {item_id}"))?;
        if let Some(variant) = variant.as_deref() {
            if !option.variants.is_empty() && !option.variants.iter().any(|value| value == variant) {
                return Err(format!("unknown variant {variant} for {}", option.display_name));
            }
        }
        Ok(UniversalLpcSelection {
            item_id: option.item_id.clone(),
            display_name: option.display_name.clone(),
            variant,
            definition_source: option.definition_path.to_string_lossy().replace('\\', "/"),
            selected_license: option.preferred_license().map(str::to_string),
            licenses: option.licenses.clone(),
            source_urls: option.source_urls.clone(),
            share_alike_required: option.share_alike_required(),
            ..Default::default()
        })
    }

    pub fn select_option(
        &self,
        recipe: &mut UniversalLpcCharacterRecipe,
        item_id: &str,
        variant: Option<String>,
    ) -> Result<String, String> {
        let option = self.option(item_id)
            .ok_or_else(|| format!("unknown ULPC character builder item {item_id}"))?;
        if !self.compatible_option(recipe, option) {
            return Err(format!("{} is incompatible with the current character recipe", option.display_name));
        }
        if let Some(variant) = variant.as_deref() {
            if !option.variants.is_empty() && !option.variants.iter().any(|value| value == variant) {
                return Err(format!("unknown variant {variant} for {}", option.display_name));
            }
        }
        let selection = self.selection_for_option(item_id, variant)?;
        if option.category == "weapon" {
            recipe.equipment.main_hand = Some(selection);
        } else if option.category == "shield" {
            recipe.equipment.off_hand = Some(selection);
        } else if matches!(option.category.as_str(), "tools" | "accessory") {
            recipe.equipment.equipped.insert(option.selection_group.clone(), selection);
        } else {
            recipe.selections.insert(option.selection_group.clone(), selection);
        }
        recipe.validate()?;
        Ok(option.selection_group.clone())
    }
}

pub fn stable_definition_item_id(definition_path: &Path) -> String {
    definition_path.with_extension("").to_string_lossy()
        .replace('\\', "/")
        .replace('/', "_")
}

pub fn foundation_head_item_id(sex: &str, age_group: &str) -> String {
    let kind = universal_lpc_foundation_head_kind(sex, age_group);
    format!("head_heads_human_heads_human_{kind}")
}

pub fn normalize_age(age_group: &str) -> &'static str {
    match age_group.to_ascii_lowercase().as_str() {
        "child" => "Child",
        "teen" => "Teen",
        "elder" | "elderly" => "Elder",
        _ => "Adult",
    }
}

fn builder_option_from_record(record: &UniversalLpcDefinitionRecord) -> Option<UniversalLpcBuilderOption> {
    let definition = &record.definition;
    let display_name = definition.name.as_deref()?.trim();
    if display_name.is_empty() || definition.layer_1.is_none() {
        return None;
    }
    let definition_path = record.definition_path.to_string_lossy().replace('\\', "/");
    let type_name = definition.type_name.as_deref().unwrap_or("");
    let category = builder_category(&definition_path, type_name, &definition.tags).to_string();
    let selection_group = selection_group(&category, type_name, &record.item_id);
    let mut licenses = BTreeSet::new();
    let mut source_urls = BTreeSet::new();
    for credit in &definition.credits {
        licenses.extend(credit.licenses.iter().filter(|value| !value.trim().is_empty()).cloned());
        source_urls.extend(credit.urls.iter().filter(|value| !value.trim().is_empty()).cloned());
    }
    Some(UniversalLpcBuilderOption {
        item_id: record.item_id.clone(),
        display_name: display_name.to_string(),
        category,
        selection_group,
        definition_path: record.definition_path.clone(),
        variants: definition.variants.clone(),
        animations: definition.animations.clone(),
        tags: definition.tags.iter().map(|value| value.to_ascii_lowercase()).collect(),
        required_tags: definition.required_tags.iter().map(|value| value.to_ascii_lowercase()).collect(),
        excluded_tags: definition.excluded_tags.iter().map(|value| value.to_ascii_lowercase()).collect(),
        licenses,
        source_urls,
        priority: definition.priority.unwrap_or(0),
    })
}

fn builder_category(path: &str, type_name: &str, tags: &[String]) -> &'static str {
    let type_low = type_name.to_ascii_lowercase();
    let low = format!("{} {} {}", path, type_name, tags.join(" ")).to_ascii_lowercase();
    if type_low == "body" || low.starts_with("sheet_definitions/body/") { return "body"; }
    if type_low == "head" || low.starts_with("sheet_definitions/head/heads/") { return "head"; }

    if matches!(type_low.as_str(), "hair" | "hairextl" | "hairextr" | "ponytail" | "updo") || low.contains("/hair/") { return "hair"; }
    if type_low == "eyebrows" || low.contains("eyebrow") { return "eyebrows"; }
    if matches!(type_low.as_str(), "eyes" | "facial_eyes") || low.contains("/eyes/") { return "eyes"; }
    if type_low == "nose" || low.contains("/nose/") { return "nose"; }
    if matches!(type_low.as_str(), "ears" | "ears_inner" | "furry_ears" | "furry_ears_skin") || low.contains("/ears/") { return "ears"; }
    if matches!(type_low.as_str(), "beard" | "mustache") || low.contains("beard") || low.contains("moustache") { return "beards"; }
    if matches!(type_low.as_str(), "expression" | "expression_crying" | "wrinkles" | "facial_mask" | "facial_left" | "facial_left_trim" | "facial_right" | "facial_right_trim") { return "expression"; }

    if matches!(type_low.as_str(), "clothes" | "torso" | "shirt" | "jacket" | "jacket_trim" | "jacket_collar" | "jacket_pockets" | "vest" | "dress" | "dress_trim" | "apron" | "overalls" | "armour" | "chainmail" | "bandages") || low.contains("/torso/") { return "torso"; }
    if matches!(type_low.as_str(), "arms" | "sleeves" | "dress_sleeves" | "dress_sleeves_trim" | "shoulders" | "bauldron" | "bracers") { return "arms"; }
    if matches!(type_low.as_str(), "hands" | "gloves" | "wrists" | "ring") { return "hands"; }
    if matches!(type_low.as_str(), "legs" | "cargo" | "sash") || low.contains("/legs/") { return "legs"; }
    if matches!(type_low.as_str(), "shoes" | "feet" | "socks" | "shoes_toe" | "fins") || low.contains("/feet/") { return "feet"; }
    if matches!(type_low.as_str(), "hat" | "visor" | "hat_trim" | "hat_overlay" | "hat_accessory" | "hat_buckle" | "bandana" | "bandana_overlay" | "headcover" | "headcover_rune" | "horns") || low.contains("headwear") { return "hat"; }
    if matches!(type_low.as_str(), "neck" | "necklace") { return "neck"; }
    if matches!(type_low.as_str(), "backpack" | "backpack_straps" | "cape" | "cape_trim" | "quiver") || low.contains("/back/") { return "back"; }

    if type_low.starts_with("shield") || low.contains("shield") { return "shield"; }
    if matches!(type_low.as_str(), "weapon" | "weapon_magic_crystal" | "ammo") || low.contains("weapons/") { return "weapon"; }
    if low.contains("tools/") || type_low == "tool" { return "tools"; }
    if type_low.starts_with("wings") || low.contains("wings") { return "wings"; }
    if type_low == "tail" || low.contains("/tail/") { return "tail"; }
    if matches!(type_low.as_str(), "wheelchair" | "prosthesis_hand" | "prosthesis_leg") { return "mobility"; }
    if type_low == "shadow" || type_low.starts_with("wound_") { return "effects"; }

    "accessory"
}

fn selection_group(category: &str, type_name: &str, item_id: &str) -> String {
    if matches!(category, "body" | "head") {
        return category.to_string();
    }
    let normalized_type = type_name.trim().to_ascii_lowercase().replace(' ', "_").replace('-', "_");
    if !normalized_type.is_empty() {
        return normalized_type;
    }
    item_id.split('_').take(3).collect::<Vec<_>>().join("_")
}

fn active_recipe_tags(
    recipe: &UniversalLpcCharacterRecipe,
    catalog: &UniversalLpcCharacterBuilderCatalog,
) -> BTreeSet<String> {
    let mut tags = BTreeSet::new();
    for selection in recipe.selections.values().chain(recipe.equipped_visuals()) {
        if let Some(option) = catalog.option(&selection.item_id) {
            tags.extend(option.tags.iter().cloned());
            tags.insert(option.selection_group.clone());
            tags.insert(option.item_id.clone());
        }
    }
    tags.extend(recipe.identity.authored_traits.iter().map(|value| value.to_ascii_lowercase()));
    tags
}

fn normalize_source(value: &str) -> String {
    value.trim_start_matches("spritesheets/").trim_start_matches('/').replace('\\', "/").to_ascii_lowercase()
}

fn is_preferred_character_license(value: &str) -> bool {
    let low = value.to_ascii_lowercase().replace('-', " ");
    (low.contains("oga by") || low.contains("cc by")) && !low.contains("by sa")
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::universal_lpc_sheet_definition::{UniversalLpcLayerDefinition, UniversalLpcSheetDefinition};

    fn record(item_id: &str, path: &str, type_name: &str, z: i32) -> UniversalLpcDefinitionRecord {
        let mut body_paths = std::collections::BTreeMap::new();
        body_paths.insert("male".to_string(), serde_json::Value::String(path.to_string()));
        UniversalLpcDefinitionRecord {
            item_id: item_id.to_string(),
            definition_path: PathBuf::from(format!("sheet_definitions/{item_id}.json")),
            definition: UniversalLpcSheetDefinition {
                name: Some(item_id.to_string()),
                type_name: Some(type_name.to_string()),
                layer_1: Some(UniversalLpcLayerDefinition { z_pos: Some(z), custom_animation: None, body_paths }),
                animations: vec!["idle".into(), "walk".into()],
                ..Default::default()
            },
        }
    }

    #[test]
    fn stable_definition_ids_match_normalized_catalog_contract() {
        assert_eq!(stable_definition_item_id(Path::new("head/heads/human/heads_human_male.json")), "head_heads_human_heads_human_male");
    }

    #[test]
    fn headwear_and_head_remain_distinct_categories() {
        assert_eq!(builder_category("sheet_definitions/head/heads/human/male.json", "head", &[]), "head");
        assert_eq!(builder_category("sheet_definitions/headwear/helmets/armet.json", "hat", &[]), "hat");
    }

    #[test]
    fn source_lookup_prefers_longest_definition_prefix() {
        let definitions = UniversalLpcDefinitionCatalog { records: vec![
            record("body_body", "body/bodies/male/", "body", 0),
            record("body_detail", "body/bodies/male/detail/", "accessory", 5),
        ]};
        let catalog = UniversalLpcCharacterBuilderCatalog::from_definitions(definitions);
        assert_eq!(catalog.definition_for_source("body/bodies/male/detail/walk.png", UniversalLpcBodyType::Male).unwrap().item_id, "body_detail");
    }
}
