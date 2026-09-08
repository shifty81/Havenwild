use std::{collections::BTreeSet, sync::OnceLock};

use haven_core::{ObjectId, ObjectKind, SceneBiome};
use serde::Deserialize;

use crate::{
    character_equipment_runtime::clothing_item_catalog, player_inventory_ui::ItemStack, Game,
};

const EMBEDDED_CLOTHING_LOOT_TABLES: &str =
    include_str!("../../../content/loot/clothing_loot_tables_v0_1.json");

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ClothingLootCatalog {
    schema: String,
    tables: Vec<ClothingLootTable>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ClothingLootTable {
    id: String,
    rolls: [u8; 2],
    entries: Vec<ClothingLootEntry>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ClothingLootEntry {
    item_id: String,
    weight: u32,
}

static CLOTHING_LOOT_CATALOG: OnceLock<ClothingLootCatalog> = OnceLock::new();

fn clothing_loot_catalog() -> &'static ClothingLootCatalog {
    CLOTHING_LOOT_CATALOG.get_or_init(|| {
        let catalog: ClothingLootCatalog = serde_json::from_str(EMBEDDED_CLOTHING_LOOT_TABLES)
            .expect("embedded clothing loot tables must be valid JSON");
        catalog
            .validate()
            .expect("embedded clothing loot tables must pass validation");
        catalog
    })
}

impl ClothingLootCatalog {
    fn validate(&self) -> Result<(), String> {
        if self.schema != "havenwild.loot.clothing_tables.v0_1" {
            return Err(format!("unsupported clothing loot schema {}", self.schema));
        }
        let items = clothing_item_catalog();
        let mut table_ids = BTreeSet::new();
        for table in &self.tables {
            if !table_ids.insert(table.id.as_str()) {
                return Err(format!("duplicate clothing loot table {}", table.id));
            }
            if table.rolls[0] == 0 || table.rolls[0] > table.rolls[1] {
                return Err(format!(
                    "invalid roll range for clothing loot table {}",
                    table.id
                ));
            }
            if table.entries.is_empty() {
                return Err(format!("clothing loot table {} has no entries", table.id));
            }
            for entry in &table.entries {
                if entry.weight == 0 {
                    return Err(format!(
                        "clothing loot table {} contains a zero-weight entry",
                        table.id
                    ));
                }
                let item = items.item(&entry.item_id).ok_or_else(|| {
                    format!(
                        "clothing loot table {} references unknown item {}",
                        table.id, entry.item_id
                    )
                })?;
                if !item.runtime_ready {
                    return Err(format!(
                        "clothing loot table {} references non-runtime item {}",
                        table.id, entry.item_id
                    ));
                }
            }
        }
        Ok(())
    }

    fn table(&self, id: &str) -> Option<&ClothingLootTable> {
        self.tables.iter().find(|table| table.id == id)
    }
}

pub(crate) fn roll_clothing_loot(table_id: &str, seed: u64) -> Result<Vec<ItemStack>, String> {
    let catalog = clothing_loot_catalog();
    let table = catalog
        .table(table_id)
        .ok_or_else(|| format!("unknown clothing loot table {table_id}"))?;
    let mut rng = DeterministicLootRng::new(seed ^ stable_hash(table_id));
    let roll_span = u64::from(table.rolls[1] - table.rolls[0] + 1);
    let roll_count = usize::from(table.rolls[0]) + (rng.next_u64() % roll_span) as usize;
    let mut selected = BTreeSet::new();
    let mut output = Vec::new();
    for _ in 0..roll_count {
        let candidates = table
            .entries
            .iter()
            .filter(|entry| !selected.contains(entry.item_id.as_str()))
            .collect::<Vec<_>>();
        if candidates.is_empty() {
            break;
        }
        let total_weight = candidates
            .iter()
            .map(|entry| u64::from(entry.weight))
            .sum::<u64>();
        let mut ticket = rng.next_u64() % total_weight;
        let chosen = candidates
            .into_iter()
            .find(|entry| {
                let weight = u64::from(entry.weight);
                if ticket < weight {
                    true
                } else {
                    ticket -= weight;
                    false
                }
            })
            .expect("positive loot weights must resolve a candidate");
        selected.insert(chosen.item_id.as_str());
        let item = clothing_item_catalog()
            .item(&chosen.item_id)
            .expect("validated clothing item must still exist");
        output.push(ItemStack {
            item_id: item.item_id.clone(),
            display_name: item.display_name.clone(),
            quantity: 1,
        });
    }
    Ok(output)
}

impl Game {
    pub(super) fn loot_clothing_container(
        &mut self,
        object_id: ObjectId,
        object_kind: ObjectKind,
    ) -> String {
        if self.world.active().map.object_state(object_id) == Some("looted") {
            return format!("{} is empty", object_kind.label());
        }
        let table_id = clothing_table_for_container(self.world.active().biome, object_kind);
        let seed = self.world_seed
            ^ object_id.raw().rotate_left(17)
            ^ stable_hash(self.world.active().id.code());
        let loot = match roll_clothing_loot(table_id, seed) {
            Ok(loot) => loot,
            Err(error) => return format!("Loot table error: {error}"),
        };
        if loot.is_empty() {
            self.world
                .active_mut()
                .map
                .set_object_state(object_id, "looted");
            return format!("{} contained no clothing", object_kind.label());
        }
        if !self.player_inventory_ui.try_add_items(&loot) {
            return "Inventory is full; container remains unopened".to_string();
        }
        self.world
            .active_mut()
            .map
            .set_object_state(object_id, "looted");
        let names = loot
            .iter()
            .map(|stack| stack.display_name.as_str())
            .collect::<Vec<_>>()
            .join(", ");
        format!("Looted {names}")
    }
}

fn clothing_table_for_container(biome: SceneBiome, kind: ObjectKind) -> &'static str {
    match (biome, kind) {
        (SceneBiome::Coastal, _) => "clothing_coastal_cache",
        (SceneBiome::Cave, _) => "clothing_travel_cache",
        (_, ObjectKind::Barrel) => "clothing_travel_cache",
        (SceneBiome::Temperate, ObjectKind::Crate) => "clothing_farmstead",
        _ => "clothing_common_household",
    }
}

fn stable_hash(value: &str) -> u64 {
    let mut hash = 0xcbf29ce484222325u64;
    for byte in value.as_bytes() {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(0x100000001b3);
    }
    hash
}

#[derive(Clone, Copy, Debug)]
struct DeterministicLootRng {
    state: u64,
}

impl DeterministicLootRng {
    fn new(seed: u64) -> Self {
        Self {
            state: seed.max(0x9e3779b97f4a7c15),
        }
    }

    fn next_u64(&mut self) -> u64 {
        let mut value = self.state;
        value ^= value >> 12;
        value ^= value << 25;
        value ^= value >> 27;
        self.state = value;
        value.wrapping_mul(0x2545f4914f6cdd1d)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn clothing_loot_is_deterministic_for_container_identity() {
        let first = roll_clothing_loot("clothing_farmstead", 42).expect("loot");
        let second = roll_clothing_loot("clothing_farmstead", 42).expect("loot");
        assert_eq!(first, second);
        assert!(!first.is_empty());
    }

    #[test]
    fn clothing_loot_does_not_duplicate_within_one_roll() {
        let loot = roll_clothing_loot("clothing_common_household", 77).expect("loot");
        let ids = loot
            .iter()
            .map(|stack| stack.item_id.as_str())
            .collect::<BTreeSet<_>>();
        assert_eq!(ids.len(), loot.len());
    }
}
