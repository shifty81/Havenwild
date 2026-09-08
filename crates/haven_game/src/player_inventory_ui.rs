use macroquad::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::OnceLock;
use std::time::{SystemTime, UNIX_EPOCH};

use crate::character_equipment_runtime::{
    clothing_item_catalog, equipment_slot_for_item, equipment_slot_order, universal_lpc_seed_for_item,
};
use crate::client_controls::{ControlAction, ControlRuntime};

mod crafting;
mod draw;
mod interaction;
mod station_processing;

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub(crate) struct ItemStack {
    pub(crate) item_id: String,
    pub(crate) display_name: String,
    pub(crate) quantity: u16,
}

#[derive(Clone, Debug, Deserialize)]
pub(crate) struct RecipeDefinition {
    pub(crate) id: String,
    pub(crate) display_name: String,
    pub(crate) station_id: String,
    pub(crate) ingredients: Vec<(String, u16)>,
    pub(crate) output: (String, String, u16),
    pub(crate) process_seconds: f32,
    pub(crate) fuel_cost: u16,
}

#[derive(Clone, Debug, Deserialize)]
#[allow(dead_code)]
pub(crate) struct CraftingStationDefinition {
    pub(crate) id: String,
    pub(crate) display_name: String,
    #[allow(dead_code)]
    pub(crate) input_slots: u8,
    #[allow(dead_code)]
    pub(crate) output_slots: u8,
    #[allow(dead_code)]
    pub(crate) fuel_slots: u8,
    #[allow(dead_code)]
    pub(crate) recipe_category: String,
}

#[derive(Clone, Debug, Deserialize)]
struct CraftingCatalogFile {
    schema: String,
    stations: Vec<CraftingStationDefinition>,
    recipes: Vec<RecipeDefinition>,
}

#[derive(Clone, Debug)]
struct CraftingCatalog {
    stations: Vec<CraftingStationDefinition>,
    recipes_by_station: BTreeMap<String, Vec<RecipeDefinition>>,
}

static CRAFTING_CATALOG: OnceLock<CraftingCatalog> = OnceLock::new();

fn crafting_catalog() -> &'static CraftingCatalog {
    CRAFTING_CATALOG.get_or_init(|| {
        let source = include_str!("../../../content/crafting/havenwild_crafting_catalog_v0_1.json");
        let parsed: CraftingCatalogFile = serde_json::from_str(source)
            .expect("embedded Havenwild crafting catalog must be valid JSON");
        assert_eq!(
            parsed.schema, "havenwild.crafting_catalog.v0_1",
            "unsupported embedded Havenwild crafting catalog schema"
        );
        assert!(
            !parsed.stations.is_empty(),
            "crafting catalog must define at least one station"
        );
        let station_ids = parsed
            .stations
            .iter()
            .map(|station| station.id.clone())
            .collect::<BTreeSet<_>>();
        assert_eq!(
            station_ids.len(),
            parsed.stations.len(),
            "crafting catalog station IDs must be unique"
        );
        assert!(
            station_ids.contains("hand"),
            "crafting catalog must define hand crafting"
        );
        let mut recipe_ids = BTreeSet::new();
        let mut recipes_by_station: BTreeMap<String, Vec<RecipeDefinition>> = BTreeMap::new();
        for recipe in parsed.recipes {
            assert!(
                recipe_ids.insert(recipe.id.clone()),
                "crafting catalog recipe IDs must be unique"
            );
            assert!(
                station_ids.contains(recipe.station_id.as_str()),
                "crafting recipe references an unknown station"
            );
            assert!(
                !recipe.ingredients.is_empty(),
                "crafting recipe must have ingredients"
            );
            assert!(
                recipe.output.2 > 0,
                "crafting recipe output quantity must be positive"
            );
            recipes_by_station
                .entry(recipe.station_id.clone())
                .or_default()
                .push(recipe);
        }
        CraftingCatalog {
            stations: parsed.stations,
            recipes_by_station,
        }
    })
}

fn crafting_stations() -> &'static [CraftingStationDefinition] {
    &crafting_catalog().stations
}

fn recipes_for_station(station_id: &str) -> &'static [RecipeDefinition] {
    crafting_catalog()
        .recipes_by_station
        .get(station_id)
        .map_or(&[], Vec::as_slice)
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub(crate) struct StationProcessingJob {
    pub(crate) recipe_id: String,
    pub(crate) display_name: String,
    pub(crate) output_item_id: String,
    pub(crate) output_display_name: String,
    pub(crate) output_quantity: u16,
    pub(crate) remaining_seconds: f32,
    pub(crate) total_seconds: f32,
    #[serde(default)]
    pub(crate) consumed_ingredients: Vec<ItemStack>,
    #[serde(default)]
    pub(crate) fuel_cost: u16,
    #[serde(default)]
    pub(crate) blocked_on_output: bool,
    #[serde(default)]
    pub(crate) paused: bool,
}

#[derive(Clone, Debug)]
#[allow(dead_code)]
struct StationNotification {
    #[allow(dead_code)]
    message: String,
    #[allow(dead_code)]
    created_at: f64,
}

const STATION_OUTPUT_STACK_LIMIT: usize = 4;
const MAX_STACK_QUANTITY: u16 = 99;
#[allow(dead_code)]
const STATION_NOTIFICATION_SECONDS: f64 = 5.0;
const MAX_OFFLINE_PROCESSING_SECONDS: u64 = 12 * 60 * 60;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub(crate) struct PlacedStationRecord {
    pub(crate) instance_id: String,
    pub(crate) station_id: String,
    pub(crate) world_x: f32,
    pub(crate) world_y: f32,
    #[serde(default)]
    pub(crate) scene_id: String,
    pub(crate) placement_confirmed: bool,
    #[serde(default)]
    pub(crate) fuel: u16,
    #[serde(default)]
    pub(crate) input_storage: Vec<ItemStack>,
    #[serde(default)]
    pub(crate) output_storage: Vec<ItemStack>,
    #[serde(default)]
    pub(crate) processing_queue: Vec<StationProcessingJob>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct PersistedInventory {
    schema: String,
    #[serde(default)]
    saved_at_unix_seconds: u64,
    slots: Vec<Option<ItemStack>>,
    crafting_grid: [Option<ItemStack>; 4],
    #[serde(default)]
    selected_station: usize,
    #[serde(default = "default_deployed_stations")]
    deployed_stations: Vec<String>,
    #[serde(default)]
    placed_stations: Vec<PlacedStationRecord>,
    #[serde(default)]
    equipment: BTreeMap<String, ItemStack>,
}

fn default_deployed_stations() -> Vec<String> {
    vec!["hand".to_string()]
}

#[derive(Clone, Debug)]
pub(crate) struct PlayerInventoryUi {
    pub(crate) open: bool,
    pub(crate) selected_slot: usize,
    pub(crate) selected_recipe: usize,
    pub(crate) slots: Vec<Option<ItemStack>>,
    pub(crate) crafting_grid: [Option<ItemStack>; 4],
    pub(crate) status: String,
    pub(crate) selected_station: usize,
    deployed_stations: Vec<String>,
    placed_stations: Vec<PlacedStationRecord>,
    pending_station_placement: Option<String>,
    active_station_context: Option<String>,
    active_station_instance: Option<String>,
    selected_queue_job: usize,
    processing_notifications: Vec<StationNotification>,
    equipment: BTreeMap<String, ItemStack>,
    selected_equipment_slot: usize,
    equipment_changed: bool,
    drag_source: Option<usize>,
    drag_equipment_source: Option<String>,
    authoring_document_id: String,
    save_path: Option<PathBuf>,
    loaded_from_persistence: bool,
    dirty: bool,
}

impl PlayerInventoryUi {
    pub(crate) fn starter() -> Self {
        let mut slots = vec![None; 30];
        slots[0] = Some(ItemStack {
            item_id: "stick".to_string(),
            display_name: "Stick".to_string(),
            quantity: 8,
        });
        slots[1] = Some(ItemStack {
            item_id: "stone".to_string(),
            display_name: "Stone".to_string(),
            quantity: 10,
        });
        slots[2] = Some(ItemStack {
            item_id: "fiber".to_string(),
            display_name: "Plant Fiber".to_string(),
            quantity: 6,
        });
        slots[3] = Some(ItemStack {
            item_id: "wood".to_string(),
            display_name: "Wood".to_string(),
            quantity: 8,
        });
        Self {
            open: false,
            selected_slot: 0,
            selected_recipe: 0,
            slots,
            crafting_grid: [None, None, None, None],
            status: "Tab closes inventory · drag slots · Enter crafts".to_string(),
            selected_station: 0,
            deployed_stations: default_deployed_stations(),
            placed_stations: Vec::new(),
            pending_station_placement: None,
            active_station_context: None,
            active_station_instance: None,
            selected_queue_job: 0,
            processing_notifications: Vec::new(),
            equipment: BTreeMap::new(),
            selected_equipment_slot: 0,
            equipment_changed: false,
            drag_source: None,
            drag_equipment_source: None,
            authoring_document_id: "inventory".to_string(),
            save_path: None,
            loaded_from_persistence: false,
            dirty: false,
        }
    }


    /// New-player baseline: the primitive axe is a real Universal LPC item and
    /// is equipped in Main Hand without assigning any hotbar slot. Existing
    /// persisted inventories are never modified by this bootstrap.
    pub(crate) fn ensure_fresh_character_primitive_axe(&mut self) -> usize {
        if self.loaded_from_persistence {
            return 0;
        }
        const AXE_ID: &str = "item.ulpc.tools_tool_axe";
        if self.equipment.values().any(|stack| stack.item_id == AXE_ID) {
            return 0;
        }
        if let Some(index) = self.slots.iter().position(|slot| {
            slot.as_ref().is_some_and(|stack| stack.item_id == AXE_ID)
        }) {
            if !self.equipment.contains_key("main_hand") {
                if let Some(stack) = self.slots[index].take() {
                    self.equipment.insert("main_hand".to_string(), stack);
                    self.equipment_changed = true;
                    self.dirty = true;
                    self.status = "Primitive Axe equipped in Main Hand; hotbar shortcuts remain player-authored".to_string();
                    return 1;
                }
            }
            return 0;
        }
        if self.equipment.contains_key("main_hand") {
            return 0;
        }
        self.equipment.insert(
            "main_hand".to_string(),
            ItemStack {
                item_id: AXE_ID.to_string(),
                display_name: "Primitive Axe".to_string(),
                quantity: 1,
            },
        );
        self.equipment_changed = true;
        self.dirty = true;
        self.status = "Primitive Axe equipped in Main Hand; hotbar shortcuts remain player-authored".to_string();
        1
    }

    /// Development-world provisioning exposes the real Universal LPC tool
    /// inventory without hard-coding hotbar assignments. The hotbar remains a
    /// player-authored shortcut surface; this only ensures the test character
    /// can equip/inspect the production items and their generated icons.
    pub(crate) fn ensure_development_toolkit(&mut self) -> usize {
        let mut changed = 0usize;
        for tool in crate::gameplay_hotbar::GameplayTool::ALL {
            let Some(item_id) = tool.item_id() else {
                continue;
            };
            let already_present = self
                .slots
                .iter()
                .flatten()
                .any(|stack| stack.item_id == item_id)
                || self.equipment.values().any(|stack| stack.item_id == item_id);
            if already_present {
                continue;
            }
            let Some(slot) = self.slots.iter_mut().find(|slot| slot.is_none()) else {
                break;
            };
            *slot = Some(ItemStack {
                item_id: item_id.to_string(),
                display_name: tool.label().to_string(),
                quantity: 1,
            });
            changed += 1;
        }

        // A development character should visibly prove the Main Hand pipeline
        // immediately. Equip the production Axe only when Main Hand is empty;
        // this does not create or persist any hotbar slot binding.
        if !self.equipment.contains_key("main_hand") {
            if let Some(index) = self.slots.iter().position(|slot| {
                slot.as_ref().is_some_and(|stack| {
                    stack.item_id == "item.ulpc.tools_tool_axe"
                })
            }) {
                if let Some(stack) = self.slots[index].take() {
                    self.equipment.insert("main_hand".to_string(), stack);
                    changed += 1;
                }
            }
        }

        if changed > 0 {
            self.dirty = true;
            self.equipment_changed = true;
            self.status = format!(
                "Development toolkit ready: {changed} tool/equipment change(s); drag items to author hotbar shortcuts"
            );
        }
        changed
    }

    pub(crate) fn load_or_starter(path: impl Into<PathBuf>) -> Self {
        let path = path.into();
        let mut inventory = Self::starter();
        inventory.save_path = Some(path.clone());
        if let Ok(bytes) = fs::read(&path) {
            match serde_json::from_slice::<PersistedInventory>(&bytes) {
                Ok(saved) if saved.slots.len() == 30 => {
                    inventory.slots = saved.slots;
                    inventory.crafting_grid = saved.crafting_grid;
                    inventory.selected_station =
                        saved.selected_station.min(crafting_stations().len() - 1);
                    inventory.deployed_stations = if saved.deployed_stations.is_empty() {
                        default_deployed_stations()
                    } else {
                        saved.deployed_stations
                    };
                    inventory.placed_stations = saved.placed_stations;
                    inventory.equipment = saved.equipment;
                    inventory.loaded_from_persistence = true;
                    let offline_summary =
                        inventory.apply_offline_station_progress(saved.saved_at_unix_seconds);
                    if !inventory
                        .deployed_stations
                        .iter()
                        .any(|station| station == "hand")
                    {
                        inventory.deployed_stations.push("hand".to_string());
                    }
                    inventory.status = offline_summary.unwrap_or_else(|| {
                        "Inventory and station access restored from save".to_string()
                    });
                }
                Ok(_) => {
                    inventory.status = "Inventory save had an unsupported slot layout".to_string()
                }
                Err(error) => inventory.status = format!("Inventory save ignored: {error}"),
            }
        }
        inventory
    }

    fn apply_offline_station_progress(&mut self, saved_at_unix_seconds: u64) -> Option<String> {
        if saved_at_unix_seconds == 0 {
            return None;
        }
        let now = unix_time_seconds();
        let elapsed = now
            .saturating_sub(saved_at_unix_seconds)
            .min(MAX_OFFLINE_PROCESSING_SECONDS);
        if elapsed == 0 {
            return None;
        }

        let mut completed_jobs = 0usize;
        let mut blocked_stations = 0usize;
        for station in &mut self.placed_stations {
            let (completed, blocked) = advance_station_offline(station, elapsed as f32);
            completed_jobs += completed;
            blocked_stations += usize::from(blocked);
        }
        if completed_jobs == 0 && blocked_stations == 0 {
            return None;
        }
        self.dirty = true;
        Some(format!(
            "Offline processing: {completed_jobs} job(s) completed{}",
            if blocked_stations > 0 {
                format!("; {blocked_stations} station(s) waiting on output space")
            } else {
                String::new()
            }
        ))
    }

    pub(crate) fn save(&mut self) -> Result<(), String> {
        let Some(path) = self.save_path.clone() else {
            return Ok(());
        };
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).map_err(|error| error.to_string())?;
        }
        let payload = PersistedInventory {
            schema: "havenwild.player_inventory.v0_12".to_string(),
            saved_at_unix_seconds: unix_time_seconds(),
            slots: self.slots.clone(),
            crafting_grid: self.crafting_grid.clone(),
            selected_station: self.selected_station,
            deployed_stations: self.deployed_stations.clone(),
            placed_stations: self.placed_stations.clone(),
            equipment: self.equipment.clone(),
        };
        let bytes = serde_json::to_vec_pretty(&payload).map_err(|error| error.to_string())?;
        let temporary = path.with_extension("json.tmp");
        fs::write(&temporary, bytes).map_err(|error| error.to_string())?;
        if path.exists() {
            fs::remove_file(&path).map_err(|error| error.to_string())?;
        }
        fs::rename(&temporary, &path).map_err(|error| error.to_string())?;
        self.dirty = false;
        Ok(())
    }

    pub(crate) fn inventory_save_path(character_links_root: &str, character_id: &str) -> PathBuf {
        Path::new(character_links_root)
            .join(character_id)
            .join("inventory.json")
    }

    fn mark_dirty(&mut self) {
        self.dirty = true;
    }

    pub(crate) fn authoring_ui_document_id(&self) -> &str {
        self.authoring_document_id.as_str()
    }

    pub(super) fn focus_inventory_authoring(&mut self) {
        self.authoring_document_id = "inventory".to_string();
    }

    pub(super) fn focus_crafting_authoring(&mut self) {
        self.authoring_document_id = "crafting".to_string();
    }

    pub(crate) fn toggle(&mut self) {
        self.open = !self.open;
        if self.open {
            self.focus_inventory_authoring();
            self.active_station_context = Some("hand".to_string());
            self.active_station_instance = None;
            self.selected_station = 0;
            self.selected_recipe = 0;
            self.status = "Inventory opened · hand crafting active".to_string();
        } else {
            self.active_station_context = None;
            self.active_station_instance = None;
            self.status = match self.save() {
                Ok(()) => "Inventory closed and saved".to_string(),
                Err(error) => format!("Inventory closed; save failed: {error}"),
            };
        }
    }

    pub(crate) fn open_station_instance(&mut self, station_id: &str, instance_id: &str) -> bool {
        let Some(index) = crafting_stations()
            .iter()
            .position(|station| station.id == station_id)
        else {
            return false;
        };
        self.open = true;
        self.focus_crafting_authoring();
        self.selected_station = index;
        self.selected_recipe = 0;
        self.active_station_context = Some(station_id.to_string());
        self.active_station_instance = Some(instance_id.to_string());
        self.selected_queue_job = 0;
        self.status = format!("Opened {}", crafting_stations()[index].display_name);
        true
    }
}

fn inventory_panel_rect() -> Rect {
    let width = screen_width().min(1180.0) - 48.0;
    let height = screen_height().min(760.0) - 48.0;
    Rect::new(
        (screen_width() - width) * 0.5,
        (screen_height() - height) * 0.5,
        width,
        height,
    )
}

#[allow(dead_code)]
pub(crate) fn equipment_slot_rects() -> Vec<(usize, &'static str, Rect)> {
    let panel = inventory_panel_rect();
    let x = panel.x + 30.0;
    let y = panel.y + 102.0;
    let w = 72.0;
    let h = 46.0;
    let positions = [
        ("head", x + 84.0, y),
        ("torso", x, y + 58.0),
        ("legs", x, y + 116.0),
        ("feet", x + 84.0, y + 232.0),
        ("back", x + 168.0, y + 58.0),
        ("hands", x + 168.0, y + 116.0),
        ("main_hand", x, y + 174.0),
        ("off_hand", x + 168.0, y + 174.0),
    ];
    equipment_slot_order()
        .iter()
        .enumerate()
        .filter_map(|(index, slot)| {
            positions
                .iter()
                .find(|(name, _, _)| name == slot)
                .map(|(_, px, py)| (index, *slot, Rect::new(*px, *py, w, h)))
        })
        .collect()
}

pub(crate) fn equipment_paper_doll_rect() -> Rect {
    let panel = inventory_panel_rect();
    Rect::new(panel.x + 103.0, panel.y + 151.0, 96.0, 184.0)
}

fn inventory_slot_rects() -> Vec<(usize, Rect)> {
    let panel = inventory_panel_rect();
    let mut rects = Vec::with_capacity(30);
    let start_x = panel.x + 322.0;
    let start_y = panel.y + 98.0;
    for index in 0..30 {
        let column = index % 6;
        let row = index / 6;
        rects.push((
            index,
            Rect::new(
                start_x + column as f32 * 62.0,
                start_y + row as f32 * 62.0,
                56.0,
                54.0,
            ),
        ));
    }
    rects
}

fn recipe_rects(recipe_count: usize) -> Vec<(usize, Rect)> {
    let panel = inventory_panel_rect();
    (0..recipe_count)
        .map(|index| {
            (
                index,
                Rect::new(
                    panel.x + 520.0,
                    panel.y + 466.0 + index as f32 * 58.0,
                    panel.w - 548.0,
                    50.0,
                ),
            )
        })
        .collect()
}

fn unix_time_seconds() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_or(0, |duration| duration.as_secs())
}

fn advance_station_offline(station: &mut PlacedStationRecord, mut seconds: f32) -> (usize, bool) {
    let mut completed_jobs = 0usize;
    let mut blocked_on_output = false;

    while seconds > 0.0 && !station.processing_queue.is_empty() {
        if station.processing_queue[0].paused {
            break;
        }

        let remaining = station.processing_queue[0].remaining_seconds.max(0.0);
        if remaining > seconds {
            station.processing_queue[0].remaining_seconds = remaining - seconds;
            break;
        }
        seconds = (seconds - remaining).max(0.0);
        station.processing_queue[0].remaining_seconds = 0.0;

        let output_item_id = station.processing_queue[0].output_item_id.clone();
        let output_quantity = station.processing_queue[0].output_quantity;
        if !can_accept_station_output(&station.output_storage, &output_item_id, output_quantity) {
            station.processing_queue[0].blocked_on_output = true;
            blocked_on_output = true;
            break;
        }

        let completed = station.processing_queue.remove(0);
        merge_stack(
            &mut station.output_storage,
            ItemStack {
                item_id: completed.output_item_id,
                display_name: completed.output_display_name,
                quantity: completed.output_quantity,
            },
        );
        completed_jobs += 1;
    }

    (completed_jobs, blocked_on_output)
}

fn can_accept_station_output(storage: &[ItemStack], item_id: &str, quantity: u16) -> bool {
    let stack_limit = item_stack_limit(item_id);
    let available_in_existing = storage
        .iter()
        .filter(|stack| stack.item_id == item_id)
        .map(|stack| stack_limit.saturating_sub(stack.quantity))
        .fold(0_u16, u16::saturating_add);
    if available_in_existing >= quantity {
        return true;
    }
    let remaining = quantity - available_in_existing;
    let free_slots = STATION_OUTPUT_STACK_LIMIT.saturating_sub(storage.len());
    usize::from(remaining) <= free_slots.saturating_mul(usize::from(stack_limit))
}

fn merge_stack(storage: &mut Vec<ItemStack>, mut incoming: ItemStack) {
    let stack_limit = item_stack_limit(&incoming.item_id);
    for stack in storage
        .iter_mut()
        .filter(|stack| stack.item_id == incoming.item_id)
    {
        let room = stack_limit.saturating_sub(stack.quantity);
        let moved = room.min(incoming.quantity);
        stack.quantity = stack.quantity.saturating_add(moved);
        incoming.quantity -= moved;
        if incoming.quantity == 0 {
            return;
        }
    }
    while incoming.quantity > 0 {
        let quantity = incoming.quantity.min(stack_limit);
        storage.push(ItemStack {
            item_id: incoming.item_id.clone(),
            display_name: incoming.display_name.clone(),
            quantity,
        });
        incoming.quantity -= quantity;
    }
}

fn item_stack_limit(item_id: &str) -> u16 {
    if let Some(item) = clothing_item_catalog().item(item_id) {
        return item.stack_limit;
    }
    if let Some(item) = universal_lpc_seed_for_item(item_id) {
        return item.stack_limit.min(u16::MAX as usize) as u16;
    }
    MAX_STACK_QUANTITY
}

fn item_display_name(item_id: &str) -> String {
    item_id
        .split('_')
        .map(|part| {
            let mut chars = part.chars();
            match chars.next() {
                Some(first) => first.to_uppercase().collect::<String>() + chars.as_str(),
                None => String::new(),
            }
        })
        .collect::<Vec<_>>()
        .join(" ")
}

fn station_display_name(station_id: &str) -> &str {
    crafting_stations()
        .iter()
        .find(|station| station.id == station_id)
        .map_or(station_id, |station| station.display_name.as_str())
}

#[cfg(test)]
mod development_toolkit_tests {
    use super::*;

    #[test]
    fn fresh_inventory_gets_real_primitive_axe_without_hotbar_authority() {
        let mut inventory = PlayerInventoryUi::starter();
        assert_eq!(inventory.ensure_fresh_character_primitive_axe(), 1);
        assert_eq!(
            inventory.equipment.get("main_hand").map(|stack| stack.item_id.as_str()),
            Some("item.ulpc.tools_tool_axe")
        );
        assert_eq!(inventory.ensure_fresh_character_primitive_axe(), 0);
    }

    #[test]
    fn persisted_inventory_is_never_modified_by_starter_axe_bootstrap() {
        let mut inventory = PlayerInventoryUi::starter();
        inventory.loaded_from_persistence = true;
        assert_eq!(inventory.ensure_fresh_character_primitive_axe(), 0);
        assert!(!inventory.equipment.contains_key("main_hand"));
    }

    #[test]
    fn development_toolkit_grants_real_tools_and_equips_main_hand_once() {
        let mut inventory = PlayerInventoryUi::starter();
        let first = inventory.ensure_development_toolkit();
        assert!(first > 0);
        assert_eq!(
            inventory
                .equipment
                .get("main_hand")
                .map(|stack| stack.item_id.as_str()),
            Some("item.ulpc.tools_tool_axe")
        );
        assert!(inventory.slots.iter().flatten().any(|stack| {
            stack.item_id == "item.ulpc.tools_tool_pickaxe"
        }));
        assert_eq!(inventory.ensure_development_toolkit(), 0);
    }
}
