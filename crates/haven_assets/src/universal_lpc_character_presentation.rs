use std::collections::BTreeSet;

use crate::universal_lpc_character_recipe::UniversalLpcCharacterRecipe;
use crate::universal_lpc_sheet_definition::{
    UniversalLpcDefinitionCatalog, UniversalLpcDefinitionRecord,
};

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum CharacterPresentationIssueKind {
    Occluded,
    EquipmentConflict,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CharacterPresentationIssue {
    pub kind: CharacterPresentationIssueKind,
    pub item_id: String,
    pub caused_by_item_id: String,
    pub reason: String,
}

#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct CharacterPresentationResolution {
    /// Items remain present in the CharacterRecipe but are intentionally not
    /// emitted as render layers while an active equipment presentation occludes
    /// them. Removing the equipment restores them without recipe mutation.
    pub hidden_item_ids: BTreeSet<String>,
    pub issues: Vec<CharacterPresentationIssue>,
}

pub fn resolve_character_presentation(
    recipe: &UniversalLpcCharacterRecipe,
    catalog: &UniversalLpcDefinitionCatalog,
) -> CharacterPresentationResolution {
    let mut out = CharacterPresentationResolution::default();

    let headwear = recipe
        .equipment
        .equipped
        .iter()
        .filter(|(slot, _)| matches!(slot.as_str(), "head" | "hat" | "headwear"))
        .map(|(_, selection)| selection)
        .chain(recipe.selections.get("hat"));

    for selection in headwear {
        let Some(record) = catalog.find(&selection.item_id) else { continue; };
        let profile = headwear_profile(record);
        if profile == HeadwearOcclusionProfile::None {
            continue;
        }
        if let Some(hair) = recipe.selections.get("hair") {
            out.hidden_item_ids.insert(hair.item_id.clone());
            out.issues.push(CharacterPresentationIssue {
                kind: CharacterPresentationIssueKind::Occluded,
                item_id: hair.item_id.clone(),
                caused_by_item_id: selection.item_id.clone(),
                reason: match profile {
                    HeadwearOcclusionProfile::Top => "headwear covers the hair-top region; the chosen hair remains equipped and will return when headwear is removed",
                    HeadwearOcclusionProfile::TopAndSides => "helmet covers hair top/sides; the chosen hair remains equipped",
                    HeadwearOcclusionProfile::Full => "full headwear/hood occludes the current hair presentation; the chosen hair remains equipped",
                    HeadwearOcclusionProfile::None => unreachable!(),
                }
                .to_string(),
            });
        }
        if profile == HeadwearOcclusionProfile::Full {
            if let Some(ears) = recipe.selections.get("ears") {
                out.hidden_item_ids.insert(ears.item_id.clone());
                out.issues.push(CharacterPresentationIssue {
                    kind: CharacterPresentationIssueKind::Occluded,
                    item_id: ears.item_id.clone(),
                    caused_by_item_id: selection.item_id.clone(),
                    reason: "full headwear occludes external ear presentation; ear identity remains selected".to_string(),
                });
            }
        }
    }

    if let (Some(main_hand), Some(off_hand)) = (
        recipe.equipment.main_hand.as_ref(),
        recipe.equipment.off_hand.as_ref(),
    ) {
        if catalog
            .find(&main_hand.item_id)
            .is_some_and(definition_is_two_handed)
        {
            out.hidden_item_ids.insert(off_hand.item_id.clone());
            out.issues.push(CharacterPresentationIssue {
                kind: CharacterPresentationIssueKind::EquipmentConflict,
                item_id: off_hand.item_id.clone(),
                caused_by_item_id: main_hand.item_id.clone(),
                reason: "two-handed main-hand equipment conflicts with the off-hand presentation".to_string(),
            });
        }
    }

    let back_items = recipe
        .equipment
        .equipped
        .iter()
        .filter(|(slot, _)| slot.as_str() == "back")
        .map(|(_, selection)| selection)
        .chain(recipe.selections.get("back"));
    let back = back_items.collect::<Vec<_>>();
    if back.len() > 1 {
        for pair in back.windows(2) {
            let left = pair[0];
            let right = pair[1];
            if is_large_back_item(catalog.find(&left.item_id)) && is_large_back_item(catalog.find(&right.item_id)) {
                out.issues.push(CharacterPresentationIssue {
                    kind: CharacterPresentationIssueKind::EquipmentConflict,
                    item_id: right.item_id.clone(),
                    caused_by_item_id: left.item_id.clone(),
                    reason: "large back equipment overlaps another large back presentation; choose a certified compatible variant".to_string(),
                });
            }
        }
    }

    out
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum HeadwearOcclusionProfile {
    None,
    Top,
    TopAndSides,
    Full,
}

fn headwear_profile(record: &UniversalLpcDefinitionRecord) -> HeadwearOcclusionProfile {
    let haystack = definition_haystack(record);
    if contains_any(&haystack, &["fullhelm", "full_helm", "closed_helm", "hood", "coif", "greathelm", "great_helm"]) {
        HeadwearOcclusionProfile::Full
    } else if contains_any(&haystack, &["helmet", "helm", "armet", "sallet", "bascinet"]) {
        HeadwearOcclusionProfile::TopAndSides
    } else if contains_any(&haystack, &["hat", "cap", "crown", "tiara", "circlet"]) {
        HeadwearOcclusionProfile::Top
    } else {
        HeadwearOcclusionProfile::None
    }
}

fn definition_is_two_handed(record: &UniversalLpcDefinitionRecord) -> bool {
    let haystack = definition_haystack(record);
    contains_any(
        &haystack,
        &[
            "two_handed",
            "two-handed",
            "2h_",
            "2hand",
            "greatsword",
            "longbow",
            "polearm",
            "halberd",
        ],
    )
}

fn is_large_back_item(record: Option<&UniversalLpcDefinitionRecord>) -> bool {
    let Some(record) = record else { return false; };
    let haystack = definition_haystack(record);
    contains_any(&haystack, &["backpack", "rucksack", "large_pack", "cape", "cloak", "wings"])
}

fn definition_haystack(record: &UniversalLpcDefinitionRecord) -> String {
    let mut values = Vec::new();
    values.push(record.item_id.to_ascii_lowercase());
    values.push(record.definition_path.to_string_lossy().to_ascii_lowercase());
    if let Some(name) = record.definition.name.as_deref() {
        values.push(name.to_ascii_lowercase());
    }
    if let Some(type_name) = record.definition.type_name.as_deref() {
        values.push(type_name.to_ascii_lowercase());
    }
    values.extend(record.definition.tags.iter().map(|tag| tag.to_ascii_lowercase()));
    values.join(" ")
}

fn contains_any(haystack: &str, needles: &[&str]) -> bool {
    needles.iter().any(|needle| haystack.contains(needle))
}
