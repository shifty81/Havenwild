use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

use crate::universal_lpc_animation::{animation_spec, custom_animation_spec, UniversalLpcBodyType};

pub const UNIVERSAL_LPC_CHARACTER_RECIPE_SCHEMA: &str =
    "havenwild.universal_lpc_character_recipe.v1";

/// Pinned Universal LPC source generation certified by the project source lock.
/// The validator cross-checks this constant against the JSON source lock so a
/// dependency upgrade cannot silently desynchronize persisted character recipes.
pub const UNIVERSAL_LPC_ACTIVE_SOURCE_COMMIT: &str =
    "0f898bb675a1abe16ce430e82e3bf9daed278690";

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct UniversalLpcCharacterBuilderCategory {
    pub id: &'static str,
    pub label: &'static str,
    pub required_foundation: bool,
}

pub const UNIVERSAL_LPC_CHARACTER_BUILDER_CATEGORIES: [UniversalLpcCharacterBuilderCategory; 25] = [
    UniversalLpcCharacterBuilderCategory { id: "body", label: "Body", required_foundation: true },
    UniversalLpcCharacterBuilderCategory { id: "head", label: "Head", required_foundation: true },
    UniversalLpcCharacterBuilderCategory { id: "hair", label: "Hair", required_foundation: false },
    UniversalLpcCharacterBuilderCategory { id: "eyebrows", label: "Brows", required_foundation: false },
    UniversalLpcCharacterBuilderCategory { id: "eyes", label: "Eyes", required_foundation: false },
    UniversalLpcCharacterBuilderCategory { id: "nose", label: "Nose", required_foundation: false },
    UniversalLpcCharacterBuilderCategory { id: "ears", label: "Ears", required_foundation: false },
    UniversalLpcCharacterBuilderCategory { id: "beards", label: "Facial Hair", required_foundation: false },
    UniversalLpcCharacterBuilderCategory { id: "expression", label: "Face Details", required_foundation: false },
    UniversalLpcCharacterBuilderCategory { id: "torso", label: "Tops / Torso", required_foundation: false },
    UniversalLpcCharacterBuilderCategory { id: "arms", label: "Arms / Shoulders", required_foundation: false },
    UniversalLpcCharacterBuilderCategory { id: "hands", label: "Hands / Gloves", required_foundation: false },
    UniversalLpcCharacterBuilderCategory { id: "legs", label: "Bottoms / Legs", required_foundation: false },
    UniversalLpcCharacterBuilderCategory { id: "feet", label: "Footwear", required_foundation: false },
    UniversalLpcCharacterBuilderCategory { id: "hat", label: "Headwear", required_foundation: false },
    UniversalLpcCharacterBuilderCategory { id: "neck", label: "Neck", required_foundation: false },
    UniversalLpcCharacterBuilderCategory { id: "back", label: "Back / Capes", required_foundation: false },
    UniversalLpcCharacterBuilderCategory { id: "accessory", label: "Accessories", required_foundation: false },
    UniversalLpcCharacterBuilderCategory { id: "weapon", label: "Weapon", required_foundation: false },
    UniversalLpcCharacterBuilderCategory { id: "shield", label: "Off Hand / Shield", required_foundation: false },
    UniversalLpcCharacterBuilderCategory { id: "tools", label: "Tools", required_foundation: false },
    UniversalLpcCharacterBuilderCategory { id: "wings", label: "Wings", required_foundation: false },
    UniversalLpcCharacterBuilderCategory { id: "tail", label: "Tail", required_foundation: false },
    UniversalLpcCharacterBuilderCategory { id: "mobility", label: "Mobility / Prosthetics", required_foundation: false },
    UniversalLpcCharacterBuilderCategory { id: "effects", label: "Scars / Effects", required_foundation: false },
];

pub const UNIVERSAL_LPC_REQUIRED_FOUNDATION_SLOTS: [&str; 2] = ["body", "head"];

pub const UNIVERSAL_LPC_FOUNDATION_BODY_ITEM_ID: &str = "body_body";

pub fn universal_lpc_foundation_head_item_id(sex: &str, age_group: &str) -> String {
    format!(
        "head_heads_human_heads_human_{}",
        universal_lpc_foundation_head_kind(sex, age_group)
    )
}

pub fn universal_lpc_body_type_for_identity(sex: &str, age_group: &str) -> UniversalLpcBodyType {
    match age_group.to_ascii_lowercase().as_str() {
        "child" => UniversalLpcBodyType::Child,
        "teen" => UniversalLpcBodyType::Teen,
        _ if sex.eq_ignore_ascii_case("female") => UniversalLpcBodyType::Female,
        _ => UniversalLpcBodyType::Male,
    }
}

pub fn universal_lpc_foundation_head_kind(sex: &str, age_group: &str) -> &'static str {
    if age_group.eq_ignore_ascii_case("child") {
        "child"
    } else if age_group.eq_ignore_ascii_case("elder") || age_group.eq_ignore_ascii_case("elderly") {
        if sex.eq_ignore_ascii_case("female") { "female_elderly" } else { "male_elderly" }
    } else if sex.eq_ignore_ascii_case("female") {
        "female"
    } else {
        "male"
    }
}


pub fn universal_lpc_builder_category_id<'a>(
    source: &str,
    category: &str,
    tags: impl IntoIterator<Item = &'a str>,
) -> Option<&'static str> {
    let low = source.to_ascii_lowercase().replace('\\', "/");
    let category_low = category.to_ascii_lowercase().replace(' ', "_").replace('-', "_");
    let tags = tags
        .into_iter()
        .map(|tag| tag.to_ascii_lowercase().replace(' ', "_").replace('-', "_"))
        .collect::<Vec<_>>();
    let tagged = |needle: &str| tags.iter().any(|tag| tag == needle);

    // Foundation paths are exact and must win before fuzzy `head` matching.
    if low.starts_with("body/bodies/") { return Some("body"); }
    if low.starts_with("head/heads/") { return Some("head"); }
    if low.starts_with("hair/") || low.contains("/hair/") { return Some("hair"); }
    if low.contains("eyebrow") { return Some("eyebrows"); }
    if low.starts_with("eyes/") || low.contains("/eyes/") { return Some("eyes"); }
    if low.starts_with("head/nose/") || low.contains("/nose/") { return Some("nose"); }
    if low.starts_with("head/ears/") || low.contains("/ears/") { return Some("ears"); }
    if low.starts_with("beards/") || low.contains("beard") || low.contains("moustache") || low.contains("mustache") { return Some("beards"); }
    if low.contains("helmet") || low.contains("headwear") || low.contains("/hat/") || low.starts_with("hat/") || low.contains("/hood/") || low.contains("/crown/") || tagged("headwear") { return Some("hat"); }
    if low.contains("shield") || low.contains("off_hand") || low.contains("offhand") { return Some("shield"); }
    if low.contains("weapon") || low.contains("sword") || low.contains("bow/") || low.contains("spear") { return Some("weapon"); }
    if low.contains("tool") { return Some("tools"); }
    if low.contains("wings") { return Some("wings"); }
    if low.contains("tail") { return Some("tail"); }
    if low.contains("backpack") || low.contains("cape") || low.contains("cloak") || low.starts_with("back/") { return Some("back"); }
    if low.contains("boots") || low.contains("shoes") || low.contains("sandals") || low.starts_with("feet/") { return Some("feet"); }
    if low.contains("pants") || low.contains("trousers") || low.contains("skirt") || low.starts_with("legs/") { return Some("legs"); }
    if low.contains("shirt") || low.contains("tunic") || low.contains("torso") || low.contains("robe") || low.contains("armor") || low.contains("armour") { return Some("torso"); }

    UNIVERSAL_LPC_CHARACTER_BUILDER_CATEGORIES
        .iter()
        .find(|entry| category_low == entry.id || tagged(entry.id))
        .map(|entry| entry.id)
}

pub fn universal_lpc_identity_compatible<'a>(
    source: &str,
    tags: impl IntoIterator<Item = &'a str>,
    sex: &str,
    age_group: &str,
) -> bool {
    let low = source.to_ascii_lowercase().replace('\\', "/");
    let tags = tags.into_iter().map(|tag| tag.to_ascii_lowercase()).collect::<Vec<_>>();
    let tagged = |needle: &str| tags.iter().any(|tag| tag == needle);
    let child = tagged("child") || low.contains("/child/");
    let teen = tagged("teen") || low.contains("/teen/");
    let elder = tagged("elderly") || low.contains("elderly");
    let is_body = low.starts_with("body/bodies/");
    let is_head = low.starts_with("head/heads/");

    let source_male = tagged("male") || low.contains("/male/") || low.contains("/male_elderly/");
    let source_female = tagged("female") || low.contains("/female/") || low.contains("/female_elderly/");
    // Child bodies/heads and teen bodies are sex-neutral in the upstream contract.
    let sex_neutral_foundation = child || (teen && is_body);
    if !sex_neutral_foundation && (source_male || source_female) {
        if sex.eq_ignore_ascii_case("female") && !source_female { return false; }
        if !sex.eq_ignore_ascii_case("female") && !source_male { return false; }
    }

    match age_group.to_ascii_lowercase().as_str() {
        "child" => {
            if is_body || is_head { child } else { !teen && !elder && (child || (!tagged("adult"))) }
        }
        "teen" => {
            if is_body { teen }
            else if is_head { !child && !elder && !teen }
            else { !child && !elder }
        }
        "elder" | "elderly" => {
            if is_body { !child && !teen }
            else if is_head { elder }
            else { !child && !teen }
        }
        _ => !child && !teen && !elder,
    }
}

#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UniversalLpcSelection {
    pub item_id: String,
    #[serde(default)]
    pub display_name: String,
    #[serde(default)]
    pub variant: Option<String>,
    #[serde(default)]
    pub recolors: BTreeMap<String, String>,
    #[serde(default)]
    pub locked: bool,
    /// Relative upstream sheet-definition source, retained for provenance/debugging.
    #[serde(default)]
    pub definition_source: String,
    /// License selected for this recipe instance when multiple upstream choices exist.
    #[serde(default)]
    pub selected_license: Option<String>,
    /// Complete upstream license set for attribution generation.
    #[serde(default)]
    pub licenses: BTreeSet<String>,
    /// Complete upstream source URL set for attribution generation.
    #[serde(default)]
    pub source_urls: BTreeSet<String>,
    /// True when the selected source requires ShareAlike propagation.
    #[serde(default)]
    pub share_alike_required: bool,
}

#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UniversalLpcEquipmentRecipe {
    #[serde(default)]
    pub main_hand: Option<UniversalLpcSelection>,
    #[serde(default)]
    pub off_hand: Option<UniversalLpcSelection>,
    #[serde(default)]
    pub equipped: BTreeMap<String, UniversalLpcSelection>,
}

#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct HavenwildCharacterIdentityMetadata {
    #[serde(default)]
    pub character_id: Option<String>,
    #[serde(default)]
    pub species: String,
    #[serde(default)]
    pub age_group: String,
    #[serde(default)]
    pub role: String,
    #[serde(default)]
    pub profession: String,
    #[serde(default)]
    pub class_id: String,
    #[serde(default)]
    pub authored_traits: BTreeSet<String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UniversalLpcCharacterRecipe {
    pub schema: String,
    pub source_commit: String,
    pub body_type: UniversalLpcBodyType,
    #[serde(default)]
    pub selections: BTreeMap<String, UniversalLpcSelection>,
    #[serde(default)]
    pub equipment: UniversalLpcEquipmentRecipe,
    #[serde(default)]
    pub identity: HavenwildCharacterIdentityMetadata,
}

impl UniversalLpcCharacterRecipe {
    pub fn new(source_commit: impl Into<String>, body_type: UniversalLpcBodyType) -> Self {
        Self {
            schema: UNIVERSAL_LPC_CHARACTER_RECIPE_SCHEMA.to_string(),
            source_commit: source_commit.into(),
            body_type,
            selections: BTreeMap::new(),
            equipment: UniversalLpcEquipmentRecipe::default(),
            identity: HavenwildCharacterIdentityMetadata::default(),
        }
    }

    pub fn validate(&self) -> Result<(), String> {
        if self.schema != UNIVERSAL_LPC_CHARACTER_RECIPE_SCHEMA {
            return Err(format!("unsupported character recipe schema {}", self.schema));
        }
        if self.source_commit.trim().is_empty() {
            return Err("character recipe must retain the ULPC source commit".to_string());
        }
        let body = self.selections.get("body").or_else(|| self.selections.get("body/base"));
        if body.is_none() {
            return Err("character recipe must contain a body selection".to_string());
        }
        if self.selections.get("head").is_none() {
            return Err("character recipe must contain a head selection".to_string());
        }
        for (group, selection) in &self.selections {
            if group.trim().is_empty() || selection.item_id.trim().is_empty() {
                return Err("character selection groups and item ids must not be empty".to_string());
            }
        }
        Ok(())
    }

    pub fn selection(&self, group: &str) -> Option<&UniversalLpcSelection> {
        self.selections.get(group)
    }

    pub fn equipped_visuals(&self) -> impl Iterator<Item = &UniversalLpcSelection> {
        self.equipment
            .main_hand
            .iter()
            .chain(self.equipment.off_hand.iter())
            .chain(self.equipment.equipped.values())
    }

    pub fn to_json_value(&self) -> Result<serde_json::Value, String> {
        serde_json::to_value(self).map_err(|error| error.to_string())
    }

    pub fn from_json_value(value: serde_json::Value) -> Result<Self, String> {
        let recipe: Self = serde_json::from_value(value).map_err(|error| error.to_string())?;
        recipe.validate()?;
        Ok(recipe)
    }

    pub fn supports_animation(&self, animation: &str) -> bool {
        animation_spec(animation).is_some() || custom_animation_spec(animation).is_some()
    }

    pub fn apply_identity_foundations(&mut self, sex: &str, age_group: &str) {
        self.body_type = universal_lpc_body_type_for_identity(sex, age_group);
        self.identity.age_group = match age_group.to_ascii_lowercase().as_str() {
            "child" => "Child",
            "teen" => "Teen",
            "elder" | "elderly" => "Elder",
            _ => "Adult",
        }.to_string();
        self.selections.insert("body".into(), UniversalLpcSelection {
            item_id: UNIVERSAL_LPC_FOUNDATION_BODY_ITEM_ID.into(),
            display_name: "Body Color".into(),
            locked: true,
            ..Default::default()
        });
        self.selections.insert("head".into(), UniversalLpcSelection {
            item_id: universal_lpc_foundation_head_item_id(sex, age_group),
            display_name: format!("{} Head", universal_lpc_foundation_head_kind(sex, age_group)),
            locked: true,
            ..Default::default()
        });
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shared_builder_identity_maps_age_to_real_ulpc_body_contract() {
        assert_eq!(universal_lpc_body_type_for_identity("Male", "Child"), UniversalLpcBodyType::Child);
        assert_eq!(universal_lpc_body_type_for_identity("Female", "Teen"), UniversalLpcBodyType::Teen);
        assert_eq!(universal_lpc_body_type_for_identity("Female", "Adult"), UniversalLpcBodyType::Female);
        assert_eq!(universal_lpc_body_type_for_identity("Male", "Elder"), UniversalLpcBodyType::Male);
        assert_eq!(universal_lpc_foundation_head_kind("Female", "Elder"), "female_elderly");
        assert_eq!(universal_lpc_foundation_head_kind("Male", "Child"), "child");
    }

    #[test]
    fn builder_categories_keep_body_and_head_as_mandatory_foundation() {
        assert!(UNIVERSAL_LPC_CHARACTER_BUILDER_CATEGORIES.iter().any(|entry| entry.id == "body" && entry.required_foundation));
        assert!(UNIVERSAL_LPC_CHARACTER_BUILDER_CATEGORIES.iter().any(|entry| entry.id == "head" && entry.required_foundation));
    }


    #[test]
    fn headwear_never_classifies_as_the_mandatory_head_foundation() {
        assert_eq!(
            universal_lpc_builder_category_id(
                "head/heads/human/male/idle.png",
                "head",
                ["male"],
            ),
            Some("head")
        );
        assert_eq!(
            universal_lpc_builder_category_id(
                "headwear/helmet/steel/idle.png",
                "clothing",
                ["headwear", "male"],
            ),
            Some("hat")
        );
    }

    #[test]
    fn identity_compatibility_makes_age_a_real_foundation_dimension() {
        assert!(universal_lpc_identity_compatible(
            "body/bodies/child/idle.png",
            std::iter::empty::<&str>(),
            "Male",
            "Child",
        ));
        assert!(!universal_lpc_identity_compatible(
            "body/bodies/male/idle.png",
            ["male"],
            "Male",
            "Child",
        ));
        assert!(universal_lpc_identity_compatible(
            "body/bodies/teen/idle.png",
            std::iter::empty::<&str>(),
            "Female",
            "Teen",
        ));
        assert!(universal_lpc_identity_compatible(
            "head/heads/human/female/idle.png",
            ["female"],
            "Female",
            "Teen",
        ));
        assert!(universal_lpc_identity_compatible(
            "head/heads/human/male_elderly/idle.png",
            ["male", "elderly"],
            "Male",
            "Elder",
        ));
        assert!(!universal_lpc_identity_compatible(
            "head/heads/human/male/idle.png",
            ["male"],
            "Male",
            "Elder",
        ));
    }

    #[test]
    fn identity_foundations_use_stable_definition_ids() {
        let mut recipe = UniversalLpcCharacterRecipe::new("abc", UniversalLpcBodyType::Male);
        recipe.apply_identity_foundations("Female", "Elder");
        assert_eq!(recipe.selection("body").unwrap().item_id, "body_body");
        assert_eq!(recipe.selection("head").unwrap().item_id, "head_heads_human_heads_human_female_elderly");
        assert_eq!(recipe.body_type, UniversalLpcBodyType::Female);
    }

    #[test]
    fn typed_recipe_round_trips_without_flattening_selection_metadata() {
        let mut recipe = UniversalLpcCharacterRecipe::new("abc", UniversalLpcBodyType::Male);
        recipe.selections.insert("body".into(), UniversalLpcSelection { item_id: "body".into(), ..Default::default() });
        recipe.selections.insert("head".into(), UniversalLpcSelection { item_id: "head".into(), ..Default::default() });
        let value = recipe.to_json_value().unwrap();
        let decoded = UniversalLpcCharacterRecipe::from_json_value(value).unwrap();
        assert_eq!(decoded, recipe);
    }
}
