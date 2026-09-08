use std::{
    collections::{BTreeMap, BTreeSet},
    path::Path,
    sync::OnceLock,
};

use haven_save::{
    load_character_profile, CharacterAppearance, CharacterAppearanceLayer, CharacterProfileStore,
    PortableAssetRef,
};
use serde::Deserialize;
use haven_assets::universal_lpc_equipment_catalog::{
    UniversalLpcEquipmentItemSeed, UniversalLpcEquipmentItemSeedCatalog,
};

use crate::{
    character_runtime_compositor::RuntimeCharacterAppearance,
    player_inventory_ui::{ItemStack, PlayerInventoryUi},
    runtime_config::runtime_save_root,
    Game,
};

const EMBEDDED_CLOTHING_ITEM_CATALOG: &str =
    include_str!("../../../content/characters/gameplay_clothing_item_catalog_v0_1.json");

const EQUIPMENT_SLOT_ORDER: &[&str] =
    &["head", "torso", "legs", "feet", "back", "hands", "main_hand", "off_hand"];

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub(crate) struct GameplayClothingItemCatalog {
    schema: String,
    items: Vec<GameplayClothingItemDefinition>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub(crate) struct GameplayClothingItemDefinition {
    pub(crate) item_id: String,
    pub(crate) display_name: String,
    pub(crate) equipment_slot: String,
    pub(crate) appearance_slot: String,
    pub(crate) variant_id: String,
    pub(crate) asset_ref: PortableAssetRef,
    pub(crate) acquisition_kinds: Vec<String>,
    pub(crate) rarity: String,
    pub(crate) stack_limit: u16,
    pub(crate) tags: Vec<String>,
    pub(crate) runtime_ready: bool,
}

static CLOTHING_ITEM_CATALOG: OnceLock<GameplayClothingItemCatalog> = OnceLock::new();
static UNIVERSAL_LPC_ITEM_SEEDS: OnceLock<UniversalLpcEquipmentItemSeedCatalog> = OnceLock::new();

pub(crate) fn clothing_item_catalog() -> &'static GameplayClothingItemCatalog {
    CLOTHING_ITEM_CATALOG.get_or_init(|| {
        let catalog: GameplayClothingItemCatalog =
            serde_json::from_str(EMBEDDED_CLOTHING_ITEM_CATALOG)
                .expect("embedded Havenwild clothing item catalog must be valid JSON");
        catalog
            .validate()
            .expect("embedded Havenwild clothing item catalog must pass validation");
        catalog
    })
}

impl GameplayClothingItemCatalog {
    fn validate(&self) -> Result<(), String> {
        if self.schema != "havenwild.character.gameplay_clothing_item_catalog.v0_1" {
            return Err(format!("unsupported clothing item schema {}", self.schema));
        }
        let mut item_ids = BTreeSet::new();
        for item in &self.items {
            if !item_ids.insert(item.item_id.as_str()) {
                return Err(format!("duplicate clothing item {}", item.item_id));
            }
            if !EQUIPMENT_SLOT_ORDER.contains(&item.equipment_slot.as_str()) {
                return Err(format!(
                    "clothing item {} uses unknown equipment slot {}",
                    item.item_id, item.equipment_slot
                ));
            }
            if item.stack_limit != 1 {
                return Err(format!(
                    "clothing item {} must use stack limit 1",
                    item.item_id
                ));
            }
            if item.asset_ref.variant_id.as_deref() != Some(item.variant_id.as_str()) {
                return Err(format!(
                    "clothing item {} asset variant does not match {}",
                    item.item_id, item.variant_id
                ));
            }
            if item.display_name.trim().is_empty() {
                return Err(format!(
                    "clothing item {} has no display name",
                    item.item_id
                ));
            }
            if item.rarity.trim().is_empty() {
                return Err(format!("clothing item {} has no rarity", item.item_id));
            }
            if item.tags.is_empty() {
                return Err(format!(
                    "clothing item {} has no gameplay tags",
                    item.item_id
                ));
            }
            if item.acquisition_kinds.is_empty() {
                return Err(format!(
                    "clothing item {} has no acquisition route",
                    item.item_id
                ));
            }
        }
        Ok(())
    }

    pub(crate) fn item(&self, item_id: &str) -> Option<&GameplayClothingItemDefinition> {
        self.items.iter().find(|item| item.item_id == item_id)
    }

    fn equipment_appearance_slots(&self) -> BTreeSet<&str> {
        self.items
            .iter()
            .map(|item| item.appearance_slot.as_str())
            .collect()
    }
}

pub(crate) fn equipment_slot_order() -> &'static [&'static str] {
    EQUIPMENT_SLOT_ORDER
}

pub(crate) fn universal_lpc_item_seed_catalog() -> &'static UniversalLpcEquipmentItemSeedCatalog {
    UNIVERSAL_LPC_ITEM_SEEDS.get_or_init(|| {
        UniversalLpcEquipmentItemSeedCatalog::load_default()
            .expect("generated Universal LPC equipment seed catalog must be valid")
    })
}

pub(crate) fn equipment_slot_for_item(item_id: &str) -> Option<String> {
    if let Some(item) = clothing_item_catalog().item(item_id) {
        return item.runtime_ready.then(|| item.equipment_slot.clone());
    }
    universal_lpc_item_seed_catalog().find(item_id).map(|item| {
        if item.gameplay_action.eq_ignore_ascii_case("block") {
            "off_hand".to_string()
        } else {
            "main_hand".to_string()
        }
    })
}

pub(crate) fn universal_lpc_seed_for_item(item_id: &str) -> Option<&'static UniversalLpcEquipmentItemSeed> {
    universal_lpc_item_seed_catalog().find(item_id)
}

pub(crate) fn equipment_stack_for_variant(
    appearance_slot: &str,
    variant_id: &str,
) -> Option<(String, ItemStack)> {
    clothing_item_catalog()
        .items
        .iter()
        .find(|item| {
            item.runtime_ready
                && item.appearance_slot == appearance_slot
                && item.variant_id == variant_id
        })
        .map(|item| {
            (
                item.equipment_slot.clone(),
                ItemStack {
                    item_id: item.item_id.clone(),
                    display_name: item.display_name.clone(),
                    quantity: 1,
                },
            )
        })
}

pub(crate) fn equipment_stacks_from_appearance(
    appearance: &CharacterAppearance,
) -> BTreeMap<String, ItemStack> {
    appearance
        .layers
        .iter()
        .filter(|layer| layer.enabled)
        .filter_map(|layer| {
            let variant = layer.asset.variant_id.as_deref()?;
            equipment_stack_for_variant(&layer.slot, variant)
        })
        .collect()
}

fn appearance_layer(item: &GameplayClothingItemDefinition) -> CharacterAppearanceLayer {
    CharacterAppearanceLayer {
        slot: item.appearance_slot.clone(),
        asset: item.asset_ref.clone(),
        palette_id: None,
        tint_rgba: None,
        enabled: true,
    }
}

pub(crate) fn appearance_from_equipment(
    base: &CharacterAppearance,
    equipped: &BTreeMap<String, ItemStack>,
) -> Result<(CharacterAppearance, Vec<PortableAssetRef>), String> {
    let catalog = clothing_item_catalog();
    let owned_slots = catalog.equipment_appearance_slots();
    let mut appearance = base.clone();
    appearance
        .layers
        .retain(|layer| !owned_slots.contains(layer.slot.as_str()));

    let mut equipment = Vec::new();
    for slot in EQUIPMENT_SLOT_ORDER {
        let Some(stack) = equipped.get(*slot) else {
            continue;
        };
        if let Some(item) = catalog.item(&stack.item_id) {
            if item.equipment_slot != *slot {
                return Err(format!(
                    "equipped item {} belongs in {}, not {}",
                    item.item_id, item.equipment_slot, slot
                ));
            }
            if !item.runtime_ready {
                return Err(format!(
                    "equipped item {} is not runtime-ready",
                    item.item_id
                ));
            }
            appearance.layers.push(appearance_layer(item));
            equipment.push(item.asset_ref.clone());
            continue;
        }
        if let Some(item) = universal_lpc_seed_for_item(&stack.item_id) {
            let expected = if item.gameplay_action.eq_ignore_ascii_case("block") {
                "off_hand"
            } else {
                "main_hand"
            };
            if *slot != expected {
                return Err(format!(
                    "Universal LPC item {} belongs in {}, not {}",
                    item.item_id, expected, slot
                ));
            }
            equipment.push(PortableAssetRef {
                pack_id: "universal_lpc_generator".to_string(),
                category: item.category.clone(),
                asset_id: item.equipment_source_id.clone(),
                source_id: item.equipment_source_id.clone(),
                variant_id: None,
            });
            continue;
        }
        return Err(format!("unknown equipped item {}", stack.item_id));
    }
    Ok((appearance, equipment))
}

impl Game {
    pub(crate) fn synchronize_inventory_equipment_with_profile(&mut self) {
        if !self.player_inventory_ui.take_equipment_changed() {
            return;
        }

        match self.persist_inventory_equipment_to_profile() {
            Ok(()) => {
                self.character_appearance_reload_requested = true;
                self.status_message =
                    "Equipment saved; refreshing character appearance".to_string();
                self.log.event(&self.status_message);
            }
            Err(error) => {
                self.status_message = format!("Equipment change could not be saved: {error}");
                self.log.event(&self.status_message);
            }
        }
    }

    fn persist_inventory_equipment_to_profile(&mut self) -> Result<(), String> {
        let save_root = runtime_save_root();
        let profile_root = Path::new(&save_root)
            .parent()
            .unwrap_or(Path::new(&save_root))
            .join("profiles")
            .join("characters");
        let profile_path = profile_root.join(&self.character_id.0).join("profile.json");
        let mut profile = load_character_profile(&profile_path)?;
        let (appearance, equipment) = appearance_from_equipment(
            &profile.appearance,
            self.player_inventory_ui.equipped_items(),
        )?;
        profile.appearance = appearance;
        profile.equipment = equipment;
        CharacterProfileStore::new(profile_root).update(&profile)?;
        self.player_inventory_ui.save()?;
        Ok(())
    }

    pub(super) fn take_character_appearance_reload_request(&mut self) -> bool {
        std::mem::take(&mut self.character_appearance_reload_requested)
    }

    pub(super) async fn reload_character_appearance(&mut self) {
        match RuntimeCharacterAppearance::load(
            Path::new(&runtime_save_root()),
            &self.character_id,
            self.asset_session.as_ref(),
            &mut self._texture_cache,
        )
        .await
        {
            Ok(appearance) => {
                let layer_count = appearance.layers.len();
                let overlay_count = appearance.equipment_overlays.len();
                self.runtime_character_appearance = Some(appearance);
                self.status_message = format!(
                    "Character equipment refreshed ({layer_count} base layers, {overlay_count} custom equipment overlays)"
                );
                self.log.event(&self.status_message);
            }
            Err(error) => {
                self.status_message = format!("Character equipment refresh failed: {error}");
                self.log.event(&self.status_message);
            }
        }
    }
}

pub(crate) fn bootstrap_inventory_equipment(
    inventory: &mut PlayerInventoryUi,
    appearance: &CharacterAppearance,
) {
    inventory.bootstrap_equipment(equipment_stacks_from_appearance(appearance));
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn gameplay_catalog_keeps_headwear_out_of_starter_creation_but_available_in_game() {
        let catalog = clothing_item_catalog();
        let hat = catalog.item("headwear_felt_hat").expect("felt hat");
        assert_eq!(hat.equipment_slot, "head");
        assert!(hat.acquisition_kinds.iter().any(|kind| kind == "crafted"));
        assert!(!hat.acquisition_kinds.iter().any(|kind| kind == "starter"));
    }

    #[test]
    fn equipped_item_replaces_the_matching_appearance_slot() {
        let base = crate::character_creator_model::StarterCreatorSelection::default().appearance();
        let mut equipped = equipment_stacks_from_appearance(&base);
        equipped.insert(
            "torso".to_string(),
            ItemStack {
                item_id: "clothing_traveler_tunic".to_string(),
                display_name: "Traveler Tunic".to_string(),
                quantity: 1,
            },
        );
        let (appearance, _) = appearance_from_equipment(&base, &equipped).expect("appearance");
        assert_eq!(
            appearance
                .layers
                .iter()
                .find(|layer| layer.slot == "clothing/torso")
                .and_then(|layer| layer.asset.variant_id.as_deref()),
            Some("starter_tunic")
        );
    }

    #[test]
    fn equipment_bootstrap_recovers_creator_clothing_as_inventory_equipment() {
        let appearance: CharacterAppearance =
            crate::character_creator_model::StarterCreatorSelection::default().appearance();
        let equipped = equipment_stacks_from_appearance(&appearance);
        assert!(equipped.contains_key("torso"));
        assert!(equipped.contains_key("legs"));
        assert!(equipped.contains_key("feet"));
        assert!(!equipped.contains_key("head"));
    }
}
