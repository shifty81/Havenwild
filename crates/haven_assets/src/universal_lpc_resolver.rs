use std::collections::BTreeSet;
use std::path::{Path, PathBuf};

use crate::universal_lpc_animation::{
    animation_spec, custom_animation_spec, UniversalLpcBodyType, ULPC_SOURCE_FRAME_SIZE,
};
use crate::universal_lpc_character_recipe::{UniversalLpcCharacterRecipe, UniversalLpcSelection};
use crate::universal_lpc_character_presentation::{
    resolve_character_presentation, CharacterPresentationIssue,
};
use crate::universal_lpc_sheet_definition::{
    UniversalLpcDefinitionCatalog, UniversalLpcDefinitionRecord, UniversalLpcLayerDefinition,
    DEFAULT_ULPC_SOURCE_ROOT,
};

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ResolvedUniversalLpcLayer {
    pub item_id: String,
    pub layer_number: usize,
    pub z_pos: i32,
    pub source_path: PathBuf,
    /// Requested whole-character action.
    pub animation: String,
    /// Source animation used by this layer. Custom equipment actions can use a
    /// 128/192px custom sheet while the body/clothing use a compatible 64px
    /// standard action in the same resolved character.
    pub source_animation: String,
    pub custom_animation: Option<String>,
    pub frame_size: u32,
    pub body_type: UniversalLpcBodyType,
    pub variant: Option<String>,
}

#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct ResolvedUniversalLpcCharacter {
    pub layers: Vec<ResolvedUniversalLpcLayer>,
    pub unsupported_items: Vec<String>,
    pub dependency_rejections: Vec<String>,
    pub presentation_issues: Vec<CharacterPresentationIssue>,
}

pub struct UniversalLpcCharacterResolver<'a> {
    pub source_root: &'a Path,
    pub catalog: &'a UniversalLpcDefinitionCatalog,
}

impl<'a> UniversalLpcCharacterResolver<'a> {
    pub fn new(catalog: &'a UniversalLpcDefinitionCatalog) -> Self {
        Self { source_root: Path::new(DEFAULT_ULPC_SOURCE_ROOT), catalog }
    }

    pub fn with_source_root(source_root: &'a Path, catalog: &'a UniversalLpcDefinitionCatalog) -> Self {
        Self { source_root, catalog }
    }

    pub fn resolve(
        &self,
        recipe: &UniversalLpcCharacterRecipe,
        animation: &str,
    ) -> Result<ResolvedUniversalLpcCharacter, String> {
        recipe.validate()?;
        let standard = animation_spec(animation).is_some();
        let custom = custom_animation_spec(animation);
        if !standard && custom.is_none() {
            return Err(format!("unknown ULPC animation {animation}"));
        }
        let base_animation = custom_base_animation(animation).unwrap_or(animation);
        let active_tags = self.active_recipe_tags(recipe);
        let presentation = resolve_character_presentation(recipe, self.catalog);
        let mut resolved = ResolvedUniversalLpcCharacter::default();
        resolved.presentation_issues = presentation.issues.clone();
        for selection in recipe.selections.values().chain(recipe.equipped_visuals()) {
            if presentation.hidden_item_ids.contains(&selection.item_id) {
                continue;
            }
            let Some(record) = self.catalog.find(&selection.item_id) else {
                resolved.unsupported_items.push(selection.item_id.clone());
                continue;
            };
            if !definition_dependencies_satisfied(record, &active_tags) {
                resolved.dependency_rejections.push(selection.item_id.clone());
                continue;
            }
            let owns_requested_custom = custom.is_some() && record.definition.layers().iter()
                .any(|(_, layer)| layer.custom_animation.as_deref() == Some(animation));

            if standard {
                if !definition_supports_animation(record, animation) {
                    continue;
                }
                self.resolve_standard_item(record, selection, recipe, recipe.body_type, animation, animation, &mut resolved.layers)?;
            } else if owns_requested_custom {
                self.resolve_custom_item(record, selection, recipe, recipe.body_type, animation, &mut resolved.layers)?;
            } else if definition_supports_animation(record, base_animation) {
                // Whole-character custom actions retain an aligned body/clothing motion.
                self.resolve_standard_item(record, selection, recipe, recipe.body_type, animation, base_animation, &mut resolved.layers)?;
            }
        }
        resolved.layers.sort_by(|left, right| {
            left.z_pos.cmp(&right.z_pos)
                .then_with(|| left.item_id.cmp(&right.item_id))
                .then_with(|| left.layer_number.cmp(&right.layer_number))
        });
        resolved.unsupported_items.sort();
        resolved.unsupported_items.dedup();
        resolved.dependency_rejections.sort();
        resolved.dependency_rejections.dedup();
        Ok(resolved)
    }

    fn resolve_standard_item(
        &self,
        record: &UniversalLpcDefinitionRecord,
        selection: &UniversalLpcSelection,
        recipe: &UniversalLpcCharacterRecipe,
        body_type: UniversalLpcBodyType,
        requested_animation: &str,
        source_animation: &str,
        output: &mut Vec<ResolvedUniversalLpcLayer>,
    ) -> Result<(), String> {
        for (layer_number, layer) in record.definition.layers() {
            // Custom foreground/background sheets must never leak into Idle/Walk/etc.
            if layer.custom_animation.is_some() { continue; }
            let Some(base_path) = layer.path_for_body(body_type) else { continue; };
            let base_path = replace_path_templates(base_path, record, recipe);
            let relative = source_path_for_standard_layer(&base_path, selection, source_animation);
            output.push(ResolvedUniversalLpcLayer {
                item_id: record.item_id.clone(),
                layer_number,
                z_pos: layer.z_pos.unwrap_or(100),
                source_path: self.source_root.join("spritesheets").join(relative),
                animation: requested_animation.to_string(),
                source_animation: source_animation.to_string(),
                custom_animation: None,
                frame_size: ULPC_SOURCE_FRAME_SIZE[0],
                body_type,
                variant: selection.variant.clone(),
            });
        }
        Ok(())
    }

    fn resolve_custom_item(
        &self,
        record: &UniversalLpcDefinitionRecord,
        selection: &UniversalLpcSelection,
        recipe: &UniversalLpcCharacterRecipe,
        body_type: UniversalLpcBodyType,
        requested_animation: &str,
        output: &mut Vec<ResolvedUniversalLpcLayer>,
    ) -> Result<(), String> {
        let frame_size = custom_animation_spec(requested_animation)
            .map(|spec| spec.frame_size)
            .unwrap_or(ULPC_SOURCE_FRAME_SIZE[0]);
        for (layer_number, layer) in record.definition.layers() {
            if layer.custom_animation.as_deref() != Some(requested_animation) { continue; }
            let Some(base_path) = layer.path_for_body(body_type) else { continue; };
            let base_path = replace_path_templates(base_path, record, recipe);
            let relative = source_path_for_custom_layer(layer, &base_path, selection);
            output.push(ResolvedUniversalLpcLayer {
                item_id: record.item_id.clone(),
                layer_number,
                z_pos: layer.z_pos.unwrap_or(100),
                source_path: self.source_root.join("spritesheets").join(relative),
                animation: requested_animation.to_string(),
                source_animation: requested_animation.to_string(),
                custom_animation: layer.custom_animation.clone(),
                frame_size,
                body_type,
                variant: selection.variant.clone(),
            });
        }
        Ok(())
    }

    fn active_recipe_tags(&self, recipe: &UniversalLpcCharacterRecipe) -> BTreeSet<String> {
        let mut tags = recipe.identity.authored_traits.iter()
            .map(|value| value.to_ascii_lowercase())
            .collect::<BTreeSet<_>>();
        for selection in recipe.selections.values().chain(recipe.equipped_visuals()) {
            tags.insert(selection.item_id.to_ascii_lowercase());
            if let Some(record) = self.catalog.find(&selection.item_id) {
                tags.extend(record.definition.tags.iter().map(|value| value.to_ascii_lowercase()));
                if let Some(type_name) = record.definition.type_name.as_deref() {
                    tags.insert(type_name.to_ascii_lowercase());
                }
            }
        }
        tags
    }
}

fn definition_dependencies_satisfied(record: &UniversalLpcDefinitionRecord, active_tags: &BTreeSet<String>) -> bool {
    record.definition.required_tags.iter()
        .all(|tag| active_tags.contains(&tag.to_ascii_lowercase()))
        && record.definition.excluded_tags.iter()
            .all(|tag| !active_tags.contains(&tag.to_ascii_lowercase()))
}

fn definition_supports_animation(record: &UniversalLpcDefinitionRecord, requested: &str) -> bool {
    record.definition.animations.is_empty()
        || record.definition.animations.iter().any(|value| animation_compatible(value, requested))
}

pub fn custom_base_animation(animation: &str) -> Option<&'static str> {
    Some(match animation {
        "tool_axe" | "tool_hammer" | "tool_whip" | "slash_128" | "slash_oversize" => "slash",
        "slash_reverse_oversize" | "backslash_128" => "1h_backslash",
        "halfslash_128" => "1h_halfslash",
        "tool_rod" | "thrust_128" | "thrust_oversize" => "thrust",
        "walk_128" | "wheelchair" => "walk",
        _ => return None,
    })
}

fn source_path_for_standard_layer(
    base_path: &str,
    selection: &UniversalLpcSelection,
    animation: &str,
) -> PathBuf {
    let mut path = PathBuf::from(base_path.trim_start_matches('/'));
    path.push(source_folder_for_animation(animation));
    if selection.recolors.is_empty() {
        if let Some(variant) = selection.variant.as_deref().filter(|value| !value.is_empty()) {
            path.push(format!("{}.png", variant_to_filename(variant)));
            return path;
        }
    }
    if path.extension().is_none() { path.set_extension("png"); }
    path
}

fn source_path_for_custom_layer(
    _layer: &UniversalLpcLayerDefinition,
    base_path: &str,
    selection: &UniversalLpcSelection,
) -> PathBuf {
    let mut path = PathBuf::from(base_path.trim_start_matches('/'));
    if let Some(variant) = selection.variant.as_deref().filter(|value| !value.is_empty()) {
        path.push(format!("{}.png", variant_to_filename(variant)));
    } else if path.extension().is_none() {
        path.set_extension("png");
    }
    path
}

fn source_folder_for_animation(animation: &str) -> &str {
    match animation {
        "combat" => "combat_idle",
        "1h_slash" | "1h_backslash" => "backslash",
        "1h_halfslash" => "halfslash",
        "watering" => "thrust",
        value => value,
    }
}

fn animation_compatible(supported: &str, requested: &str) -> bool {
    supported == requested
        || (requested == "watering" && supported == "thrust")
        || (requested == "1h_slash" && supported == "1h_backslash")
}

fn variant_to_filename(value: &str) -> String {
    value.trim().to_ascii_lowercase().replace(' ', "_")
}

fn replace_path_templates(
    source: &str,
    record: &UniversalLpcDefinitionRecord,
    recipe: &UniversalLpcCharacterRecipe,
) -> String {
    let mut output = source.to_string();
    for (type_name, replacements) in &record.definition.replace_in_path {
        let token = format!("${{{type_name}}}");
        if !output.contains(&token) { continue; }
        let selected = recipe.selections.get(type_name).or_else(|| {
            recipe.selections.values().find(|selection| {
                self_describing_selection_group(&selection.item_id) == type_name.as_str()
            })
        });
        if let Some(replacement) = selected.and_then(|selection| replacement_for_selection(replacements, selection)) {
            output = output.replace(&token, replacement);
        }
    }
    output
}

fn replacement_for_selection<'a>(
    replacements: &'a std::collections::BTreeMap<String, String>,
    selection: &UniversalLpcSelection,
) -> Option<&'a String> {
    let item_stem = selection.item_id.rsplit('/').next().unwrap_or(&selection.item_id);
    let item_stem = item_stem.rsplit('.').next().unwrap_or(item_stem);
    let mut candidates = Vec::new();
    if let Some(variant) = selection.variant.as_deref().filter(|value| !value.is_empty()) {
        candidates.push(format!("{}_{}", item_stem, variant_to_filename(variant)));
        candidates.push(variant.to_string());
    }
    candidates.push(item_stem.to_string());
    candidates.push(selection.item_id.clone());
    if !selection.display_name.trim().is_empty() { candidates.push(selection.display_name.clone()); }
    for candidate in candidates {
        if let Some(value) = replacements.get(&candidate) { return Some(value); }
        if let Some((_, value)) = replacements.iter().find(|(key, _)| key.eq_ignore_ascii_case(&candidate)) {
            return Some(value);
        }
    }
    None
}

fn self_describing_selection_group(item_id: &str) -> &str {
    item_id.split(|ch: char| matches!(ch, '.' | '/' | '_')).next().unwrap_or(item_id)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn animation_folder_aliases_match_ulpc_layout() {
        assert_eq!(source_folder_for_animation("combat"), "combat_idle");
        assert_eq!(source_folder_for_animation("1h_backslash"), "backslash");
        assert_eq!(source_folder_for_animation("watering"), "thrust");
    }

    #[test]
    fn oversized_equipment_actions_have_explicit_whole_character_companions() {
        assert_eq!(custom_base_animation("tool_axe"), Some("slash"));
        assert_eq!(custom_base_animation("tool_rod"), Some("thrust"));
        assert_eq!(custom_base_animation("walk_128"), Some("walk"));
        assert_eq!(custom_base_animation("slash_reverse_oversize"), Some("1h_backslash"));
    }
}
