use super::*;
use crate::universal_lpc_gameplay_equipment::GameplayEquipmentAction;

const RANGED_FULL_CHARGE_SECONDS: f64 = 0.90;
const RANGED_MIN_SPEED: f32 = 300.0;
const RANGED_MAX_SPEED: f32 = 560.0;
const RANGED_MAX_DISTANCE: f32 = TILE_SIZE * 14.0;
const RUNTIME_PROJECTILE_LIMIT: usize = 64;

#[derive(Clone, Debug)]
pub(crate) struct PendingGameplayToolAction {
    tool: Option<GameplayTool>,
    item_id: String,
    display_name: String,
    action: GameplayEquipmentAction,
    x: i32,
    y: i32,
    contact_progress: f32,
}

// Compatibility state retained by the post-AB40 Game struct. H21A14AC2R3H
// deliberately replaced gameplay_tool_runtime.rs for player-authored hotbar
// authority, but that overwrite also removed these later ranged-runtime types.
// Keep their data representation small and self-contained so the existing Game
// fields remain valid without reintroducing any hard-coded hotbar ownership.
#[derive(Clone, Debug)]
pub(crate) struct RangedAimState {
    pub(crate) origin: Vec2,
    pub(crate) target: Vec2,
    pub(crate) item_id: String,
    pub(crate) display_name: String,
    pub(crate) started_at: f64,
}

#[derive(Clone, Debug)]
pub(crate) struct RuntimeProjectile {
    pub(crate) position: Vec2,
    pub(crate) previous_position: Vec2,
    pub(crate) velocity: Vec2,
    pub(crate) radius: f32,
    pub(crate) remaining_seconds: f32,
    pub(crate) damage: f32,
}

impl Game {
    pub(super) fn handle_gameplay_tool_use_input(&mut self) {
        // Charge/draw weapons own PrimaryAction from press through release.
        // While held, the pointer remains a real world-space target rather than
        // collapsing to the adjacent facing tile used by ordinary hand tools.
        if self.ranged_aim.is_some() {
            if self.dev_mode || self.pause_menu_open {
                self.ranged_aim = None;
                return;
            }
            self.update_ranged_aim_target();
            if !self.controls.action_down(ControlAction::PrimaryAction) {
                self.release_ranged_aim();
            }
            return;
        }

        if self.dev_mode
            || self.pause_menu_open
            || !self.controls.action_pressed(ControlAction::PrimaryAction)
            || pointer_over_gameplay_hud()
            || self.player_character_state().action_locks_movement()
        {
            return;
        }
        self.use_selected_gameplay_tool();
    }

    fn use_selected_gameplay_tool(&mut self) {
        // Hotbar slots are player-authored shortcuts. The GameplayTool enum is
        // now only an action adapter for recognized tool item definitions.
        let selected_binding = self.selected_hotbar_binding();
        let (tool, item_id, display_name, action) = if let Some(binding) = selected_binding {
            if !self.hotbar_binding_is_available(&binding.item_id) {
                self.status_message = format!(
                    "{} is no longer available; reassign hotbar slot {}",
                    binding.display_name,
                    self.selected_gameplay_tool + 1
                );
                return;
            }

            if let Some(equipment) = self.universal_lpc_gameplay_equipment.find(&binding.item_id) {
                (
                    GameplayTool::from_item_id(&binding.item_id),
                    binding.item_id,
                    binding.display_name,
                    equipment.action,
                )
            } else if let Some(tool) = GameplayTool::from_item_id(&binding.item_id) {
                let item_id = binding.item_id;
                let display_name = binding.display_name;
                (Some(tool), item_id, display_name, fallback_gameplay_action(tool))
            } else {
                self.status_message = format!(
                    "{} is assigned to the hotbar but has no direct-use action yet",
                    binding.display_name
                );
                return;
            }
        } else {
            // Empty hotbar means unarmed/hand interaction, not a hidden tool
            // assignment. No slot is ever pre-populated with a tool.
            let tool = GameplayTool::Hand;
            (
                Some(tool),
                "hand".to_string(),
                tool.label().to_string(),
                fallback_gameplay_action(tool),
            )
        };
        // The hotbar is a shortcut surface, not a second equipment authority.
        // Direct-use equipment must equip the matching item in Main Hand before use;
        // equipment whose canonical slot is not Main Hand (for example shields) uses
        // that declared slot instead.
        if item_id != "hand" && !self.ensure_hotbar_item_equipped_for_use(&item_id, &display_name) {
            return;
        }

        if action == GameplayEquipmentAction::Shoot {
            self.begin_ranged_aim(item_id, display_name);
            return;
        }

        let cost = tool.map(tool_stamina_cost).unwrap_or_else(|| action_stamina_cost(action));
        if !self.try_spend_character_stamina(cost) {
            self.status_message = format!("Too exhausted to use {display_name}");
            self.log.event(&self.status_message);
            return;
        }

        let current_facing = self.player_facing_vec();
        let facing = if current_facing.length_squared() > f32::EPSILON {
            current_facing.normalize()
        } else {
            vec2(0.0, 1.0)
        };
        let target = self.player + facing * TILE_SIZE * 0.85;
        let x = (target.x / TILE_SIZE).floor() as i32;
        let y = (target.y / TILE_SIZE).floor() as i32;
        self.selected_cell = (x, y);

        if tool == Some(GameplayTool::Hand) {
            self.interact_with_tile_at(x, y);
            self.inspector = inspect_scene_cell(self.world.active(), x, y);
            self.log.event(&self.status_message);
            return;
        }

        let contact = haven_assets::universal_lpc_animation::contact_progress(action.ulpc_animation())
            .unwrap_or(0.5);
        self.begin_character_equipment_animation(action);
        self.pending_gameplay_tool_action = Some(PendingGameplayToolAction {
            tool,
            item_id,
            display_name: display_name.clone(),
            action,
            x,
            y,
            contact_progress: contact,
        });
        self.status_message = format!("{display_name}...");
        self.log.event(&self.status_message);
    }

    pub(super) fn update_character_action_animation(&mut self, dt: f32) {
        let mut character = self.player_character_state();
        let before_progress = character.action_progress();
        let remaining_before = character.action_remaining;
        character.advance_action(dt);
        let after_progress = if remaining_before > 0.0 && dt.max(0.0) >= remaining_before {
            1.0
        } else {
            character.action_progress()
        };
        self.set_player_character_state(character);

        let should_commit = self
            .pending_gameplay_tool_action
            .as_ref()
            .is_some_and(|pending| {
                before_progress < pending.contact_progress
                    && after_progress >= pending.contact_progress
            });
        if should_commit {
            self.commit_pending_gameplay_tool_action();
        }
    }


    fn begin_character_equipment_animation(&mut self, action: GameplayEquipmentAction) {
        let mut character = self.player_character_state();
        character.begin_action(action.animation(), action.duration_seconds());
        character.moving = false;
        character.locomotion = CharacterAnimationIntent::Idle;
        character.locomotion_phase *= 0.35;
        self.set_player_character_state(character);
    }

    fn commit_pending_gameplay_tool_action(&mut self) {
        let Some(pending) = self.pending_gameplay_tool_action.take() else { return; };
        match pending.tool {
            Some(GameplayTool::Hand) => self.interact_with_tile_at(pending.x, pending.y),
            Some(GameplayTool::Hoe) => self.use_hoe_at(pending.x, pending.y),
            Some(GameplayTool::WateringCan) => self.use_watering_can_at(pending.x, pending.y),
            Some(GameplayTool::Scythe) => self.use_scythe_at(pending.x, pending.y),
            Some(GameplayTool::FishingRod) => self.use_fishing_rod_at(pending.x, pending.y),
            Some(GameplayTool::Shovel) => self.use_shovel_at(pending.x, pending.y),
            Some(GameplayTool::Whip) => self.use_weapon_interaction_at(GameplayTool::Whip, pending.x, pending.y),
            Some(GameplayTool::Axe) => self.use_resource_tool_at(GameplayTool::Axe, pending.x, pending.y),
            Some(GameplayTool::Pickaxe) => self.use_resource_tool_at(GameplayTool::Pickaxe, pending.x, pending.y),
            Some(GameplayTool::Hammer) => {
                self.interact_with_tile_at(pending.x, pending.y);
                if self.status_message.trim().is_empty() {
                    self.status_message = format!("Used {} at {},{}", pending.display_name, pending.x, pending.y);
                }
            }
            None => self.use_generic_equipment_action_at(
                pending.action,
                &pending.item_id,
                &pending.display_name,
                pending.x,
                pending.y,
            ),
        }
        self.inspector = inspect_scene_cell(self.world.active(), pending.x, pending.y);
        self.log.event(&self.status_message);
    }

    fn use_hoe_at(&mut self, x: i32, y: i32) {
        let tile = self.world.active().map.get(x, y);
        if matches!(tile, TileKind::Grass | TileKind::Dirt | TileKind::TallGrass) {
            self.world.active_mut().map.set(x, y, TileKind::TilledSoil);
            self.sync_active_terrain_cache_now();
            self.status_message = format!("Tilled soil at {},{}", x, y);
        } else {
            self.status_message = format!("The hoe cannot work {}", tile.label());
        }
    }

    fn use_watering_can_at(&mut self, x: i32, y: i32) {
        let tile = self.world.active().map.get(x, y);
        if tile == TileKind::TilledSoil {
            self.world.active_mut().map.set(x, y, TileKind::WateredSoil);
            self.sync_active_terrain_cache_now();
            self.status_message = format!("Watered soil at {},{}", x, y);
            return;
        }
        self.status_message = match water_source_class(tile) {
            WaterSourceClass::Fresh => format!("Filled watering can from fresh {}", tile.label()),
            WaterSourceClass::Salt => "Ocean water is salt water and cannot fill the watering can".to_string(),
            WaterSourceClass::Brackish => "River-mouth water is brackish and cannot fill the watering can".to_string(),
            WaterSourceClass::None => "Watering requires tilled soil or fresh water".to_string(),
        };
    }

    fn use_scythe_at(&mut self, x: i32, y: i32) {
        let tile = self.world.active().map.get(x, y);
        if tile == TileKind::Crop {
            // Crop harvesting uses the crop growth/harvest state through the
            // canonical tile interaction instead of flattening a crop directly
            // into generic grass from the tool adapter.
            self.interact_with_tile_at(x, y);
        } else if tile == TileKind::TallGrass {
            self.world.active_mut().map.set(x, y, TileKind::Grass);
            self.sync_active_terrain_cache_now();
            self.status_message = format!("Cut growth at {},{}", x, y);
        } else {
            self.use_weapon_interaction_at(GameplayTool::Scythe, x, y);
        }
    }

    fn use_shovel_at(&mut self, x: i32, y: i32) {
        let tile = self.world.active().map.get(x, y);
        if matches!(tile, TileKind::Grass | TileKind::TallGrass | TileKind::TilledSoil | TileKind::WateredSoil) {
            self.world.active_mut().map.set(x, y, TileKind::Dirt);
            self.sync_active_terrain_cache_now();
            self.status_message = format!("Cleared topsoil at {},{}", x, y);
        } else {
            self.status_message = format!("The shovel cannot dig {} here", tile.label());
        }
    }

    fn ensure_hotbar_item_equipped_for_use(&mut self, item_id: &str, display_name: &str) -> bool {
        let Some(expected_slot) = crate::character_equipment_runtime::equipment_slot_for_item(item_id) else {
            self.status_message = format!("{display_name} is not registered as equippable");
            self.log.event(&self.status_message);
            return false;
        };

        if self
            .player_inventory_ui
            .equipped_items()
            .get(&expected_slot)
            .is_some_and(|stack| stack.item_id == item_id)
        {
            return true;
        }

        let Some(inventory_slot) = self
            .player_inventory_ui
            .slots
            .iter()
            .position(|slot| slot.as_ref().is_some_and(|stack| stack.item_id == item_id))
        else {
            self.status_message = format!("{display_name} is no longer available to equip");
            self.log.event(&self.status_message);
            return false;
        };

        let previous_selection = self.player_inventory_ui.selected_slot;
        self.player_inventory_ui.selected_slot = inventory_slot;
        self.player_inventory_ui.equip_selected_item();
        self.player_inventory_ui.selected_slot = previous_selection
            .min(self.player_inventory_ui.slots.len().saturating_sub(1));

        let equipped = self
            .player_inventory_ui
            .equipped_items()
            .get(&expected_slot)
            .is_some_and(|stack| stack.item_id == item_id);
        if !equipped {
            self.status_message = format!(
                "{display_name} could not be equipped in {expected_slot}: {}",
                self.player_inventory_ui.status
            );
            self.log.event(&self.status_message);
            return false;
        }

        self.synchronize_inventory_equipment_with_profile();
        true
    }

    fn use_resource_tool_at(&mut self, tool: GameplayTool, x: i32, y: i32) {
        let Some(resource) = resource_target_for_tool(tool) else {
            self.status_message = format!("{} has no resource-harvest contract", tool.label());
            return;
        };
        let Some(object_index) = self.world.active().map.interaction_object_at(x, y) else {
            self.status_message = format!("{} needs a {} target", tool.label(), resource.target_label);
            return;
        };
        let object = self.world.active().map.objects[object_index];
        if object.kind != resource.kind {
            self.status_message = format!(
                "{} cannot harvest {} with the {} resource contract",
                tool.label(),
                object.kind.label(),
                resource.target_label
            );
            return;
        }

        let resource_hits: u16 = self
            .world
            .active()
            .map
            .object_state(object.id)
            .and_then(|state| state.strip_prefix("resource_hits:"))
            .and_then(|value| value.parse::<u16>().ok())
            .unwrap_or(0);
        let next_hits = resource_hits.saturating_add(1);
        if next_hits < resource.required_hits {
            self.world
                .active_mut()
                .map
                .set_object_state(object.id, format!("resource_hits:{next_hits}"));
            self.status_message = format!(
                "{} {} hit {}/{}",
                tool.label(),
                resource.target_label,
                next_hits,
                resource.required_hits
            );
            return;
        }

        let drop = crate::player_inventory_ui::ItemStack {
            item_id: resource.drop_item_id.to_string(),
            display_name: resource.drop_display_name.to_string(),
            quantity: resource.drop_quantity,
        };
        if !self.player_inventory_ui.try_add_items(&[drop]) {
            self.status_message = format!(
                "Inventory full; {} remains until its {} can be collected",
                resource.target_label,
                resource.drop_display_name
            );
            return;
        }

        let _ = self.world.active_mut().map.remove_object(object.id);
        self.status_message = format!(
            "Harvested {} with {} (+{} {})",
            resource.target_label,
            tool.label(),
            resource.drop_quantity,
            resource.drop_display_name
        );
    }

    fn use_weapon_interaction_at(&mut self, tool: GameplayTool, x: i32, y: i32) {
        self.interact_with_tile_at(x, y);
        if self.status_message.trim().is_empty() {
            self.status_message = format!("{} attack at {},{}", tool.label(), x, y);
        }
    }

    fn use_generic_equipment_action_at(
        &mut self,
        action: GameplayEquipmentAction,
        item_id: &str,
        display_name: &str,
        x: i32,
        y: i32,
    ) {
        match action {
            GameplayEquipmentAction::Block => {
                self.status_message = format!("Blocked with {display_name}");
            }
            GameplayEquipmentAction::Equip => {
                self.status_message = format!("Readied {display_name}");
            }
            GameplayEquipmentAction::Shoot => {
                self.status_message = format!("Fired {display_name} toward {},{}", x, y);
            }
            GameplayEquipmentAction::Spellcast => {
                self.status_message = format!("Cast with {display_name} toward {},{}", x, y);
            }
            _ => {
                self.interact_with_tile_at(x, y);
                if self.status_message.trim().is_empty() {
                    self.status_message = format!("Used {display_name} ({item_id}) at {},{}", x, y);
                }
            }
        }
    }

    fn use_fishing_rod_at(&mut self, x: i32, y: i32) {
        let tile = self.world.active().map.get(x, y);
        if tile.is_water() {
            self.status_message = format!("Cast fishing line into {}", tile.label());
        } else {
            self.status_message = "Fishing requires a water target".to_string();
        }
    }

    fn begin_ranged_aim(&mut self, item_id: String, display_name: String) {
        let origin = self.player;
        let target = self.ranged_pointer_target(origin);
        self.ranged_aim = Some(RangedAimState {
            origin,
            target,
            item_id,
            display_name: display_name.clone(),
            started_at: get_time(),
        });
        self.status_message = format!("Drawing {display_name}...");
        self.log.event(&self.status_message);
    }

    fn update_ranged_aim_target(&mut self) {
        let origin = self.player;
        let target = self.ranged_pointer_target(origin);
        if let Some(aim) = self.ranged_aim.as_mut() {
            aim.origin = origin;
            aim.target = target;
        }
    }

    fn ranged_pointer_target(&self, origin: Vec2) -> Vec2 {
        let pointer = self.screen_to_world(vec2(mouse_position().0, mouse_position().1));
        let mut delta = pointer - origin;
        if delta.length_squared() <= 1.0 {
            delta = self.player_facing_vec();
            if delta.length_squared() <= f32::EPSILON {
                delta = vec2(0.0, 1.0);
            }
            delta = delta.normalize() * TILE_SIZE * 4.0;
        }
        let distance = delta.length();
        if distance > RANGED_MAX_DISTANCE && distance > f32::EPSILON {
            origin + delta / distance * RANGED_MAX_DISTANCE
        } else {
            origin + delta
        }
    }

    fn ranged_charge_progress(&self) -> f32 {
        self.ranged_aim
            .as_ref()
            .map(|aim| ranged_charge_progress_for_elapsed(get_time() - aim.started_at))
            .unwrap_or(0.0)
    }

    fn release_ranged_aim(&mut self) {
        let charge = self.ranged_charge_progress();
        let Some(aim) = self.ranged_aim.take() else {
            return;
        };

        let stamina_cost = action_stamina_cost(GameplayEquipmentAction::Shoot);
        if !self.try_spend_character_stamina(stamina_cost) {
            self.status_message = format!("Too exhausted to fire {}", aim.display_name);
            self.log.event(&self.status_message);
            return;
        }

        self.begin_character_equipment_animation(GameplayEquipmentAction::Shoot);
        self.spawn_runtime_projectile(aim.origin, aim.target, charge);
        self.status_message = format!(
            "Fired {} · draw {:.0}%",
            aim.display_name,
            charge * 100.0
        );
        self.log.event(&format!(
            "{} ({})",
            self.status_message, aim.item_id
        ));
    }

    fn spawn_runtime_projectile(&mut self, origin: Vec2, target: Vec2, charge: f32) {
        let mut direction = target - origin;
        if direction.length_squared() <= f32::EPSILON {
            direction = self.player_facing_vec();
        }
        if direction.length_squared() <= f32::EPSILON {
            direction = vec2(0.0, 1.0);
        }
        direction = direction.normalize();

        let charge = charge.clamp(0.0, 1.0);
        let speed = RANGED_MIN_SPEED + (RANGED_MAX_SPEED - RANGED_MIN_SPEED) * charge;
        let lifetime = 0.75 + 0.65 * charge;
        let damage = 6.0 + 12.0 * charge;
        let muzzle = origin + direction * (TILE_SIZE * 0.35);

        if self.runtime_projectiles.len() >= RUNTIME_PROJECTILE_LIMIT {
            let overflow = self.runtime_projectiles.len() + 1 - RUNTIME_PROJECTILE_LIMIT;
            self.runtime_projectiles.drain(0..overflow);
        }
        self.runtime_projectiles.push(RuntimeProjectile {
            position: muzzle,
            previous_position: muzzle,
            velocity: direction * speed,
            radius: 3.5 + charge * 1.5,
            remaining_seconds: lifetime,
            damage,
        });
    }

    pub(super) fn update_runtime_projectiles(&mut self, dt: f32) {
        let dt = dt.max(0.0);
        for projectile in &mut self.runtime_projectiles {
            projectile.previous_position = projectile.position;
            projectile.position += projectile.velocity * dt;
            projectile.remaining_seconds -= dt;
        }

        // This lane is intentionally world-space and target-agnostic: animal,
        // mob, NPC, destructible-object, and future combat-health adapters can
        // consume the same projectile position/damage authority without
        // changing mouse aiming or charge/release behavior.
        self.runtime_projectiles.retain(|projectile| {
            projectile.remaining_seconds > 0.0
                && projectile.position.x.is_finite()
                && projectile.position.y.is_finite()
        });
    }

    /// World-space projectile presentation retained from the AB40-AB49 player
    /// interaction lane. Projectiles are drawn while the gameplay camera is
    /// still active; runtime_draw.rs owns the call site/order.
    pub(super) fn draw_runtime_projectiles(&self) {
        let projectile_color = Color {
            r: 1.0,
            g: 0.78,
            b: 0.24,
            a: 1.0,
        };
        for projectile in &self.runtime_projectiles {
            if (projectile.position - projectile.previous_position).length_squared() > 0.01 {
                let trail_width = (1.4 + projectile.damage * 0.04).clamp(1.4, 2.2);
                draw_line(
                    projectile.previous_position.x,
                    projectile.previous_position.y,
                    projectile.position.x,
                    projectile.position.y,
                    trail_width,
                    projectile_color,
                );
            }
            draw_circle(
                projectile.position.x,
                projectile.position.y,
                projectile.radius.max(2.0),
                projectile_color,
            );
        }
    }

    /// Ranged targeting overlay retained as a read-only presentation of the
    /// authoritative aim state. It intentionally does not own input or hotbar
    /// assignment; those remain separate gameplay authorities.
    pub(super) fn draw_ranged_targeting_overlay(&self) {
        let Some(aim) = self.ranged_aim.as_ref() else {
            return;
        };
        let charge = self.ranged_charge_progress();
        let line_color = Color {
            r: 1.0,
            g: 0.88,
            b: 0.42,
            a: 0.80,
        };
        draw_line(
            aim.origin.x,
            aim.origin.y,
            aim.target.x,
            aim.target.y,
            1.5 + charge * 1.5,
            line_color,
        );
        draw_circle_lines(
            aim.target.x,
            aim.target.y,
            8.0 + charge * 5.0,
            1.5,
            line_color,
        );
    }
}

fn ranged_charge_progress_for_elapsed(elapsed_seconds: f64) -> f32 {
    (elapsed_seconds.max(0.0) / RANGED_FULL_CHARGE_SECONDS)
        .clamp(0.0, 1.0) as f32
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct ResourceToolTarget {
    kind: ObjectKind,
    target_label: &'static str,
    required_hits: u16,
    drop_item_id: &'static str,
    drop_display_name: &'static str,
    drop_quantity: u16,
}

fn resource_target_for_tool(tool: GameplayTool) -> Option<ResourceToolTarget> {
    match tool {
        GameplayTool::Axe => Some(ResourceToolTarget {
            kind: ObjectKind::Tree,
            target_label: "Tree",
            required_hits: 3,
            drop_item_id: "resource.wood",
            drop_display_name: "Wood",
            drop_quantity: 3,
        }),
        GameplayTool::Pickaxe => Some(ResourceToolTarget {
            kind: ObjectKind::OreNode,
            target_label: "Ore Node",
            required_hits: 4,
            drop_item_id: "resource.ore.copper",
            drop_display_name: "Copper Ore",
            drop_quantity: 2,
        }),
        _ => None,
    }
}

fn fallback_gameplay_action(tool: GameplayTool) -> GameplayEquipmentAction {
    match tool {
        GameplayTool::Axe => GameplayEquipmentAction::Chop,
        GameplayTool::Pickaxe => GameplayEquipmentAction::Mine,
        GameplayTool::Hoe => GameplayEquipmentAction::Till,
        GameplayTool::WateringCan => GameplayEquipmentAction::Water,
        GameplayTool::Hammer => GameplayEquipmentAction::Build,
        GameplayTool::FishingRod => GameplayEquipmentAction::Fish,
        GameplayTool::Shovel => GameplayEquipmentAction::Dig,
        GameplayTool::Scythe | GameplayTool::Whip => GameplayEquipmentAction::Slash,
        GameplayTool::Hand => GameplayEquipmentAction::Equip,
    }
}

fn action_stamina_cost(action: GameplayEquipmentAction) -> f32 {
    match action {
        GameplayEquipmentAction::Block | GameplayEquipmentAction::Equip => 1.0,
        GameplayEquipmentAction::Water => 2.0,
        GameplayEquipmentAction::Fish => 3.0,
        GameplayEquipmentAction::Till | GameplayEquipmentAction::Slash | GameplayEquipmentAction::Thrust => 4.0,
        GameplayEquipmentAction::Chop | GameplayEquipmentAction::Build | GameplayEquipmentAction::Dig => 5.0,
        GameplayEquipmentAction::Mine | GameplayEquipmentAction::Shoot | GameplayEquipmentAction::Spellcast => 6.0,
    }
}

fn tool_stamina_cost(tool: GameplayTool) -> f32 {
    match tool {
        GameplayTool::Axe => 6.0,
        GameplayTool::Pickaxe => 7.0,
        GameplayTool::Hoe => 4.0,
        GameplayTool::WateringCan => 2.0,
        GameplayTool::Hammer => 5.0,
        GameplayTool::FishingRod => 3.0,
        GameplayTool::Shovel => 5.0,
        GameplayTool::Scythe => 4.0,
        GameplayTool::Whip => 4.0,
        GameplayTool::Hand => 0.0,
    }
}

fn pointer_over_gameplay_hud() -> bool {
    let (x, y) = mouse_position();
    let over_hotbar = gameplay_hotbar::hotbar_slot_rects(screen_width(), screen_height())
        .into_iter()
        .any(|(_, rect)| rect.contains(vec2(x, y)));
    over_hotbar
        || (x <= 360.0 && y <= 154.0)
        || (x >= screen_width() - 310.0 && y <= 310.0)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn hand_interaction_is_free_and_work_tools_cost_stamina() {
        assert_eq!(tool_stamina_cost(GameplayTool::Hand), 0.0);
        assert!(tool_stamina_cost(GameplayTool::Pickaxe) > 0.0);
        assert!(tool_stamina_cost(GameplayTool::Shovel) > 0.0);
    }

    #[test]
    fn action_timer_exclusively_owns_movement_until_animation_finishes() {
        let mut state = CharacterRuntimeState::player_default(EntityId::from_raw(1));
        state.begin_action(CharacterAnimationIntent::OneHandSlash, 0.58);
        assert!(state.action_locks_movement());
        state.advance_action(0.60);
        assert!(!state.action_locks_movement());
    }

    #[test]
    fn ranged_charge_progress_clamps_from_zero_to_full_draw() {
        assert_eq!(ranged_charge_progress_for_elapsed(-1.0), 0.0);
        assert!(ranged_charge_progress_for_elapsed(RANGED_FULL_CHARGE_SECONDS * 0.5) > 0.45);
        assert_eq!(ranged_charge_progress_for_elapsed(RANGED_FULL_CHARGE_SECONDS * 2.0), 1.0);
    }

    #[test]
    fn axe_and_pickaxe_keep_distinct_resource_targets() {
        let axe = resource_target_for_tool(GameplayTool::Axe).expect("axe target");
        let pickaxe = resource_target_for_tool(GameplayTool::Pickaxe).expect("pickaxe target");
        assert_eq!(axe.kind, ObjectKind::Tree);
        assert_eq!(pickaxe.kind, ObjectKind::OreNode);
        assert_eq!(pickaxe.drop_display_name, "Copper Ore");
        assert!(axe.required_hits > 1);
        assert!(pickaxe.required_hits > 1);
    }
}
