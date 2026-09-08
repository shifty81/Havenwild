#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum GameplayTool {
    Axe,
    Pickaxe,
    Hoe,
    WateringCan,
    Hammer,
    FishingRod,
    Shovel,
    Scythe,
    Whip,
    Hand,
}

impl GameplayTool {
    pub(crate) const ALL: [GameplayTool; 10] = [
        GameplayTool::Axe,
        GameplayTool::Pickaxe,
        GameplayTool::Hoe,
        GameplayTool::WateringCan,
        GameplayTool::Hammer,
        GameplayTool::FishingRod,
        GameplayTool::Shovel,
        GameplayTool::Scythe,
        GameplayTool::Whip,
        GameplayTool::Hand,
    ];

    pub(crate) fn label(self) -> &'static str {
        match self {
            GameplayTool::Axe => "Axe",
            GameplayTool::Pickaxe => "Mining Pick",
            GameplayTool::Hoe => "Hoe",
            GameplayTool::WateringCan => "Watering Can",
            GameplayTool::Hammer => "Hammer",
            GameplayTool::FishingRod => "Fishing Rod",
            GameplayTool::Shovel => "Shovel",
            GameplayTool::Scythe => "Scythe",
            GameplayTool::Whip => "Whip",
            GameplayTool::Hand => "Hand",
        }
    }

    pub(crate) fn from_item_id(item_id: &str) -> Option<Self> {
        Self::ALL
            .into_iter()
            .find(|tool| tool.item_id().is_some_and(|value| value == item_id))
    }

    pub(crate) fn item_id(self) -> Option<&'static str> {
        Some(match self {
            GameplayTool::Axe => "item.ulpc.tools_tool_axe",
            GameplayTool::Pickaxe => "item.ulpc.tools_tool_pickaxe",
            GameplayTool::Hoe => "item.ulpc.tools_tool_hoe",
            GameplayTool::WateringCan => "item.ulpc.tools_tool_watering_can",
            GameplayTool::Hammer => "item.ulpc.tools_tool_hammer",
            GameplayTool::FishingRod => "item.ulpc.tools_tool_rod",
            GameplayTool::Shovel => "item.ulpc.tools_tool_shovel",
            GameplayTool::Scythe => "item.ulpc.weapons_polearm_weapon_polearm_scythe",
            GameplayTool::Whip => "item.ulpc.tools_tool_whip",
            GameplayTool::Hand => return None,
        })
    }


}

pub(crate) fn cycle_hotbar_index(current: usize, direction: i32) -> usize {
    (current as i32 + direction).rem_euclid(HOTBAR_SLOT_COUNT as i32) as usize
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn hotbar_wraps_in_both_directions() {
        assert_eq!(cycle_hotbar_index(0, -1), HOTBAR_SLOT_COUNT - 1);
        assert_eq!(cycle_hotbar_index(HOTBAR_SLOT_COUNT - 1, 1), 0);
    }

    #[test]
    fn ulpc_tools_are_addressed_by_catalog_item_id() {
        assert_eq!(GameplayTool::Shovel.item_id(), Some("item.ulpc.tools_tool_shovel"));
        assert_eq!(GameplayTool::Whip.item_id(), Some("item.ulpc.tools_tool_whip"));
        assert_eq!(GameplayTool::Hand.item_id(), None);
    }

    #[test]
    fn hotbar_layout_stays_inside_supported_safe_area() {
        let slots = hotbar_slot_rects(640.0, 480.0);
        assert_eq!(slots.len(), HOTBAR_SLOT_COUNT);
        let first = slots.first().unwrap().1;
        let last = slots.last().unwrap().1;
        assert!(first.x >= 12.0);
        assert!(last.x + last.w <= 640.0 - 12.0 + f32::EPSILON);
    }

    #[test]
    fn hotbar_layout_shrinks_without_slot_overlap() {
        let slots = hotbar_slot_rects(420.0, 320.0);
        for pair in slots.windows(2) {
            let left = pair[0].1;
            let right = pair[1].1;
            assert!(left.x + left.w < right.x);
        }
        let last = slots.last().unwrap().1;
        assert!(last.x + last.w <= 420.0 - 12.0 + f32::EPSILON);
    }
}

// H21A14AC2R3H: the gameplay hotbar is a player-authored shortcut surface.
// GameplayTool remains a taxonomy/action adapter only; its ALL array must never
// be interpreted as a hard-coded slot assignment.
pub(crate) const HOTBAR_SLOT_COUNT: usize = 10;

#[derive(Clone, Debug, serde::Serialize, serde::Deserialize, PartialEq, Eq)]
pub(crate) struct HotbarBinding {
    pub(crate) item_id: String,
    pub(crate) display_name: String,
}

#[derive(Clone, Debug, serde::Serialize, serde::Deserialize)]
struct PersistedHotbar {
    schema: String,
    #[serde(default)]
    bindings: Vec<Option<HotbarBinding>>,
}

struct HotbarRuntimeState {
    save_path: std::path::PathBuf,
    bindings: Vec<Option<HotbarBinding>>,
    drag_candidate: Option<HotbarBinding>,
    drag_origin: Option<[f32; 2]>,
}

static HOTBAR_RUNTIME: std::sync::OnceLock<std::sync::Mutex<HotbarRuntimeState>> =
    std::sync::OnceLock::new();

fn empty_bindings() -> Vec<Option<HotbarBinding>> {
    vec![None; HOTBAR_SLOT_COUNT]
}

fn load_hotbar(path: std::path::PathBuf) -> HotbarRuntimeState {
    let bindings = std::fs::read(&path)
        .ok()
        .and_then(|bytes| serde_json::from_slice::<PersistedHotbar>(&bytes).ok())
        .filter(|saved| saved.schema == "havenwild.player_hotbar.v0_1")
        .map(|mut saved| {
            saved.bindings.resize(HOTBAR_SLOT_COUNT, None);
            saved.bindings.truncate(HOTBAR_SLOT_COUNT);
            saved.bindings
        })
        .unwrap_or_else(empty_bindings);
    HotbarRuntimeState {
        save_path: path,
        bindings,
        drag_candidate: None,
        drag_origin: None,
    }
}

fn save_hotbar(state: &HotbarRuntimeState) -> Result<(), String> {
    if let Some(parent) = state.save_path.parent() {
        std::fs::create_dir_all(parent).map_err(|error| error.to_string())?;
    }
    let payload = PersistedHotbar {
        schema: "havenwild.player_hotbar.v0_1".to_string(),
        bindings: state.bindings.clone(),
    };
    let bytes = serde_json::to_vec_pretty(&payload).map_err(|error| error.to_string())?;
    std::fs::write(&state.save_path, bytes).map_err(|error| error.to_string())
}

fn hotbar_save_path(game: &crate::Game) -> std::path::PathBuf {
    // ClientSavePaths::root is intentionally serialized as a String. Convert it
    // back to a path at the filesystem boundary rather than assuming PathBuf.
    std::path::Path::new(&game.save_paths.root).join("player_hotbar.json")
}

fn with_hotbar_state<R>(game: &crate::Game, f: impl FnOnce(&mut HotbarRuntimeState) -> R) -> R {
    let requested_path = hotbar_save_path(game);
    let mutex = HOTBAR_RUNTIME.get_or_init(|| {
        std::sync::Mutex::new(load_hotbar(requested_path.clone()))
    });
    let mut state = mutex.lock().unwrap_or_else(|poisoned| poisoned.into_inner());
    if state.save_path != requested_path {
        *state = load_hotbar(requested_path);
    }
    f(&mut state)
}

pub(crate) fn hotbar_slot_rects(
    screen_w: f32,
    screen_h: f32,
) -> Vec<(usize, macroquad::prelude::Rect)> {
    use macroquad::prelude::Rect;

    // One bounded geometry authority owns frame, slot, selector, pointer hit,
    // key-label and drag/drop placement. Shrink spacing and slots together on
    // narrow viewports instead of letting the ten-slot strip leave the safe area.
    const SAFE_MARGIN: f32 = 12.0;
    const SLOT_MAX: f32 = 50.0;
    const SLOT_MIN: f32 = 32.0;
    const GAP_MAX: f32 = 6.0;
    const GAP_MIN: f32 = 2.0;
    const BOTTOM_MARGIN: f32 = 14.0;

    let count = HOTBAR_SLOT_COUNT as f32;
    let gaps = HOTBAR_SLOT_COUNT.saturating_sub(1) as f32;
    let ideal_total = count * SLOT_MAX + gaps * GAP_MAX;
    let available = (screen_w - SAFE_MARGIN * 2.0).max(count + gaps * GAP_MIN);
    let scale = (available / ideal_total).clamp(0.0, 1.0);
    let gap = (GAP_MAX * scale).clamp(GAP_MIN, GAP_MAX);
    let mut slot = (SLOT_MAX * scale).clamp(SLOT_MIN, SLOT_MAX);
    let mut total = count * slot + gaps * gap;
    if total > available {
        slot = ((available - gaps * gap) / count).max(1.0);
        total = count * slot + gaps * gap;
    }

    let max_start = (screen_w - SAFE_MARGIN - total).max(SAFE_MARGIN);
    let start_x = ((screen_w - total) * 0.5).clamp(SAFE_MARGIN, max_start);
    let y = (screen_h - slot - BOTTOM_MARGIN).max(SAFE_MARGIN);
    (0..HOTBAR_SLOT_COUNT)
        .map(|index| {
            (
                index,
                Rect::new(start_x + index as f32 * (slot + gap), y, slot, slot),
            )
        })
        .collect()
}

impl crate::Game {
    pub(crate) fn hotbar_binding(&self, slot: usize) -> Option<HotbarBinding> {
        with_hotbar_state(self, |state| state.bindings.get(slot).cloned().flatten())
    }

    pub(crate) fn selected_hotbar_binding(&self) -> Option<HotbarBinding> {
        self.hotbar_binding(self.selected_gameplay_tool.min(HOTBAR_SLOT_COUNT - 1))
    }

    pub(crate) fn hotbar_binding_is_available(&self, item_id: &str) -> bool {
        self.player_inventory_ui
            .slots
            .iter()
            .flatten()
            .any(|stack| stack.item_id == item_id)
            || self
                .player_inventory_ui
                .equipped_items()
                .values()
                .any(|stack| stack.item_id == item_id)
    }

    pub(crate) fn bind_hotbar_slot(&mut self, slot: usize, binding: HotbarBinding) {
        if slot >= HOTBAR_SLOT_COUNT {
            return;
        }
        let result = with_hotbar_state(self, |state| {
            state.bindings[slot] = Some(binding.clone());
            save_hotbar(state)
        });
        self.status_message = match result {
            Ok(()) => format!("Hotbar {} assigned to {}", slot + 1, binding.display_name),
            Err(error) => format!("Hotbar assignment saved in memory; disk save failed: {error}"),
        };
    }

    pub(crate) fn clear_hotbar_slot(&mut self, slot: usize) {
        if slot >= HOTBAR_SLOT_COUNT {
            return;
        }
        let result = with_hotbar_state(self, |state| {
            state.bindings[slot] = None;
            save_hotbar(state)
        });
        self.status_message = match result {
            Ok(()) => format!("Hotbar {} cleared", slot + 1),
            Err(error) => format!("Hotbar cleared in memory; disk save failed: {error}"),
        };
    }

    /// Inventory remains the authority. A real press-drag-release gesture from
    /// Inventory onto any hotbar slot creates a non-owning shortcut; it never
    /// moves or duplicates the stack. Right-clicking a hotbar slot while
    /// Inventory is open clears that shortcut.
    pub(crate) fn handle_inventory_hotbar_drag_drop(&mut self) {
        use macroquad::prelude::*;
        if !self.player_inventory_ui.open {
            with_hotbar_state(self, |state| {
                state.drag_candidate = None;
                state.drag_origin = None;
            });
            return;
        }

        let point = vec2(mouse_position().0, mouse_position().1);
        let hit = hotbar_slot_rects(screen_width(), screen_height())
            .into_iter()
            .find(|(_, rect)| rect.contains(point));

        if let Some((slot, _)) = hit {
            if is_mouse_button_pressed(MouseButton::Right) {
                self.clear_hotbar_slot(slot);
                return;
            }
        }

        // Capture the currently selected inventory stack only when the player
        // begins a left-button gesture while Inventory is open. This prevents a
        // mere release/click over the hotbar from silently assigning a slot.
        if is_mouse_button_pressed(MouseButton::Left) && hit.is_none() {
            let candidate = self
                .player_inventory_ui
                .slots
                .get(self.player_inventory_ui.selected_slot)
                .and_then(Option::as_ref)
                .map(|stack| HotbarBinding {
                    item_id: stack.item_id.clone(),
                    display_name: stack.display_name.clone(),
                });
            with_hotbar_state(self, |state| {
                state.drag_candidate = candidate;
                state.drag_origin = Some([point.x, point.y]);
            });
        }

        if !is_mouse_button_released(MouseButton::Left) {
            return;
        }

        let candidate = with_hotbar_state(self, |state| {
            let candidate = state.drag_candidate.take();
            let origin = state.drag_origin.take();
            match (candidate, origin) {
                (Some(binding), Some([x, y]))
                    if vec2(point.x - x, point.y - y).length_squared() >= 36.0 =>
                {
                    Some(binding)
                }
                _ => None,
            }
        });

        let (Some((slot, _)), Some(binding)) = (hit, candidate) else {
            return;
        };
        self.bind_hotbar_slot(slot, binding);
        self.selected_gameplay_tool = slot;
    }
}
