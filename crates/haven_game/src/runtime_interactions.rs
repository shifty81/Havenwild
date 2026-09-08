use super::*;

#[derive(Clone, Debug)]
pub(crate) struct RuntimeSceneDoorAnimation {
    pub scene_id: haven_core::ProjectSceneId,
    pub object_id: haven_core::ObjectId,
    pub clip: haven_assets::placeable_asset_registry::PlaceableAnimationClip,
    pub from_footprint: haven_core::ObjectFootprint,
    pub to_footprint: haven_core::ObjectFootprint,
    pub frame_index: usize,
    pub frame_elapsed_ms: f32,
}

impl RuntimeSceneDoorAnimation {
    fn key(scene_id: &haven_core::ProjectSceneId, object_id: haven_core::ObjectId) -> String {
        format!("{}::{object_id}", scene_id.code())
    }

    pub(crate) fn source_rect(&self) -> Option<[f32; 4]> {
        self.clip.frames.get(self.frame_index).map(|frame| frame.source_rect)
    }

    pub(crate) fn draw_offset_px(&self) -> [f32; 2] {
        self.clip
            .frames
            .get(self.frame_index)
            .map(|frame| frame.draw_offset_px)
            .unwrap_or([0.0, 0.0])
    }

    fn passable(&self) -> bool {
        if self
            .clip
            .blocked_from_frame
            .is_some_and(|index| self.frame_index >= index)
        {
            return false;
        }
        if self
            .clip
            .passable_from_frame
            .is_some_and(|index| self.frame_index >= index)
        {
            return true;
        }
        !self.from_footprint.blocks_movement
    }

    fn advance(&mut self, dt: f32) -> bool {
        if self.clip.frames.is_empty() {
            return true;
        }
        self.frame_elapsed_ms += dt.max(0.0) * 1000.0;
        loop {
            let duration = self.clip.frames[self.frame_index].duration_ms.max(1) as f32;
            if self.frame_elapsed_ms < duration {
                return false;
            }
            self.frame_elapsed_ms -= duration;
            if self.frame_index + 1 >= self.clip.frames.len() {
                return true;
            }
            self.frame_index += 1;
        }
    }
}


impl Game {
    pub(super) fn update_scene_door_animations(&mut self, dt: f32) {
        let mut updates = Vec::new();
        let completed = self
            .scene_door_animations
            .iter_mut()
            .filter_map(|(key, animation)| {
                let done = animation.advance(dt);
                updates.push((
                    animation.scene_id.clone(),
                    animation.object_id,
                    animation.passable(),
                    animation.from_footprint,
                    animation.to_footprint,
                ));
                done.then(|| (
                    key.clone(),
                    animation.scene_id.clone(),
                    animation.object_id,
                    animation.clip.to_state.clone(),
                    animation.to_footprint,
                    animation.clip.complete_sound_event.clone(),
                ))
            })
            .collect::<Vec<_>>();

        for (scene_id, object_id, passable, from_footprint, to_footprint) in updates {
            if let Some(scene) = self.world.scene_mut_by_id(&scene_id) {
                if let Some(object) = scene.map.object_mut(object_id) {
                    object.footprint = if passable { to_footprint } else { from_footprint };
                }
            }
        }
        for (key, scene_id, object_id, terminal_state, terminal_footprint, sound_event) in completed {
            self.scene_door_animations.remove(&key);
            if let Some(sound_event) = sound_event {
                self.log.event(&format!("Audio hook {sound_event}"));
            }
            if let Some(scene) = self.world.scene_mut_by_id(&scene_id) {
                scene.map.set_object_state(object_id, terminal_state);
                if let Some(object) = scene.map.object_mut(object_id) {
                    object.footprint = terminal_footprint;
                }
            }
        }
    }

    pub(super) fn active_scene_door_animation(
        &self,
        scene_id: &haven_core::ProjectSceneId,
        object_id: haven_core::ObjectId,
    ) -> Option<&RuntimeSceneDoorAnimation> {
        let key = RuntimeSceneDoorAnimation::key(scene_id, object_id);
        self.scene_door_animations.get(&key)
    }

    pub(super) fn interact_with_current_tile(&mut self) {
        let x = (self.player.x / TILE_SIZE).floor() as i32;
        let y = (self.player.y / TILE_SIZE).floor() as i32;
        self.selected_cell = (x, y);
        self.interact_with_tile_at(x, y);
    }

    pub(super) fn interact_with_selected_cell(&mut self) {
        let (x, y) = self.selected_cell;
        self.interact_with_tile_at(x, y);
    }

    pub(super) fn interact_with_tile_at(&mut self, x: i32, y: i32) {
        if let Some(message) = self.try_traverse_building_connector_at(x, y) {
            self.status_message = message;
            self.log.event(&self.status_message);
            return;
        }
        if let Some(message) = self.try_interact_building_opening_at(x, y) {
            self.status_message = message;
            self.log.event(&self.status_message);
            return;
        }
        if let Some(message) = self.try_interact_building_furnishing_at(x, y) {
            self.status_message = message;
            self.log.event(&self.status_message);
            return;
        }
        if let Some(object_index) = self.world.active().map.interaction_object_at(x, y) {
            let object = self.world.active().map.objects[object_index];
            let stable_dispatch = self
                .world
                .active()
                .map
                .object_asset_ref(object.id)
                .and_then(|asset_ref| self.placeable_registry.resolve_persistent_ref(asset_ref))
                .cloned();
            if let Some(definition) = stable_dispatch {
                self.status_message = self.dispatch_placeable_interaction(object.id, &definition);
                self.log.event(&self.status_message);
                return;
            }
            self.status_message = match object.kind {
                ObjectKind::Table => {
                    "Table selected: seating attachment/meal service placeholder".to_string()
                }
                ObjectKind::Chair => "Chair selected: seat attachment placeholder".to_string(),
                ObjectKind::Bar => {
                    "Bar selected: service counter/tap management placeholder".to_string()
                }
                ObjectKind::Keg => "Keg selected: brewing/aging storage placeholder".to_string(),
                ObjectKind::Bed => "Guest bed selected: inn room service placeholder".to_string(),
                ObjectKind::Fireplace => {
                    "Cooking station selected: recipe/minigame placeholder".to_string()
                }
                ObjectKind::GreenhouseMarker => {
                    "Greenhouse marker selected: expansion entrance placeholder".to_string()
                }
                ObjectKind::Tree => "Tree · equip an Axe to chop it".to_string(),
                ObjectKind::Bush => self.forage_loose_object(object, "wild_berries", "Wild Berries", 2, false),
                ObjectKind::Boulder => "Boulder · equip a Mining Pick to quarry it".to_string(),
                ObjectKind::OreNode => "Ore node · equip a Mining Pick to mine it".to_string(),
                ObjectKind::Mushroom => self.forage_loose_object(object, "wild_mushroom", "Wild Mushroom", 1, true),
                ObjectKind::Herb => self.forage_loose_object(object, "wild_herb", "Wild Herb", 1, true),
                ObjectKind::Crate | ObjectKind::Barrel => {
                    self.loot_clothing_container(object.id, object.kind)
                }
                ObjectKind::Well => "Well selected: water interaction placeholder".to_string(),
                ObjectKind::Scarecrow => {
                    "Scarecrow selected: crop protection placeholder".to_string()
                }
                ObjectKind::Fence => {
                    "Fence selected: boundary construction placeholder".to_string()
                }
                ObjectKind::Lamp => "Lamp selected: lighting interaction placeholder".to_string(),
                ObjectKind::Bench => "Bench selected: rest interaction placeholder".to_string(),
                ObjectKind::Stump => "Tree stump · equip an Axe to clear it".to_string(),
                ObjectKind::Log => "Fallen log · equip an Axe to split it".to_string(),
                ObjectKind::Sign => "Sign selected: message interaction placeholder".to_string(),
                ObjectKind::Door => {
                    "Door selected: transition/interior entrance placeholder".to_string()
                }
                ObjectKind::Stairs => {
                    let before = self.world.active_scene.project_id().clone();
                    self.update_transitions();
                    if self.world.active_scene.project_id() != &before {
                        "Traversed structural stairs/ladder connector".to_string()
                    } else {
                        "Structural stairs/ladder connector ready".to_string()
                    }
                }
                ObjectKind::CaveEntrance => {
                    let before = self.world.active_scene.project_id().clone();
                    self.update_transitions();
                    if self.world.active_scene.project_id() != &before {
                        "Entered cave through structural cliff mouth".to_string()
                    } else {
                        "Structural cave mouth ready; no transition overlaps this interaction cell"
                            .to_string()
                    }
                }
            };
            self.log.event(&self.status_message);
            return;
        }

        let tile = self.world.active().map.get(x, y);
        let interaction = self.world.tile_rule(tile);
        match interaction {
            TileInteraction::None => {
                self.status_message = format!("{} has no interaction", tile.label());
            }
            TileInteraction::Forage => {
                self.status_message = format!(
                    "Search {} · gather visible forage plants/objects directly",
                    tile.label()
                );
            }
            TileInteraction::Hoe => {
                self.status_message = format!("{} · equip a Hoe to cultivate this tile", tile.label());
            }
            TileInteraction::Water => {
                self.status_message = format!(
                    "{} · equip a Watering Can for farming/water interaction",
                    tile.label()
                );
            }
            TileInteraction::Harvest => {
                self.status_message =
                    "Crop harvest requires its authored crop growth/harvest state".to_string();
            }
            TileInteraction::Rest => {
                self.day_clock = 8.0;
                self.status_message = format!("Rested on {}", tile.label());
            }
            TileInteraction::Blocked => {
                self.status_message = format!("{} blocks interaction", tile.label());
            }
            TileInteraction::Enter => {
                self.update_transitions();
                self.status_message = format!("Triggered enter behavior on {}", tile.label());
            }
        }
        self.log.event(&self.status_message);
    }

    fn forage_loose_object(
        &mut self,
        object: PlacedObject,
        item_id: &str,
        display_name: &str,
        quantity: u16,
        remove_after_pick: bool,
    ) -> String {
        if !remove_after_pick && self.world.active().map.object_state(object.id) == Some("foraged") {
            return format!("{} has already been gathered; wait for regrowth", object.kind.label());
        }
        let reward = crate::player_inventory_ui::ItemStack {
            item_id: item_id.to_string(),
            display_name: display_name.to_string(),
            quantity,
        };
        if !self.player_inventory_ui.try_add_items(&[reward]) {
            return format!("Inventory full — cannot collect {display_name}");
        }
        if remove_after_pick {
            let _ = self.world.active_mut().map.remove_object(object.id);
        } else {
            self.world.active_mut().map.set_object_state(object.id, "foraged");
        }
        format!("Gathered {} ×{}", display_name, quantity)
    }

    fn dispatch_placeable_interaction(
        &mut self,
        object_id: ObjectId,
        definition: &haven_assets::placeable_asset_registry::PublishedWorldAssetDefinition,
    ) -> String {
        use haven_assets::placeable_asset_registry::PlaceableMutationContext;

        let current_state = self
            .world
            .active()
            .map
            .object_state(object_id)
            .map(str::to_string);
        let trigger = definition.behavior.interaction_trigger.as_str();
        let transition = definition
            .transition_for(current_state.as_deref(), trigger)
            .cloned();
        let mut transition_message = None;
        if let Some(transition) = transition {
            let authority = PlaceableMutationContext {
                is_authoritative_host: true,
                editor_preview: false,
            };
            if transition.authority.allows(authority) {
                let next_state = transition.to.clone();
                let next_footprint = definition.footprint_for_state(Some(&next_state));
                let current = current_state
                    .as_deref()
                    .or_else(|| definition.initial_state())
                    .unwrap_or("closed");
                let animation = definition
                    .visual
                    .as_ref()
                    .and_then(|visual| visual.animation_for_transition(current, &next_state))
                    .cloned();
                if let Some(clip) = animation {
                    if let Some(sound_event) = clip.start_sound_event.as_deref() {
                        self.log.event(&format!("Audio hook {sound_event}"));
                    }
                    let scene_id = self.world.active().id.clone();
                    let key = RuntimeSceneDoorAnimation::key(&scene_id, object_id);
                    if self.scene_door_animations.contains_key(&key) {
                        return "Door is already moving.".to_string();
                    }
                    let from_footprint = definition.footprint_for_state(Some(current));
                    self.scene_door_animations.insert(
                        key,
                        RuntimeSceneDoorAnimation {
                            scene_id,
                            object_id,
                            clip,
                            from_footprint,
                            to_footprint: next_footprint,
                            frame_index: 0,
                            frame_elapsed_ms: 0.0,
                        },
                    );
                    transition_message = Some(if transition.message.is_empty() {
                        format!("Door started {} -> {}.", current, next_state)
                    } else {
                        transition.message
                    });
                } else {
                    let map = &mut self.world.active_mut().map;
                    map.set_object_state(object_id, next_state.clone());
                    if let Some(object) = map.object_mut(object_id) {
                        object.footprint = next_footprint;
                    }
                    transition_message = (!transition.message.is_empty()).then_some(transition.message);
                }
            } else {
                transition_message = Some(
                    "State transition rejected because this client is not authoritative."
                        .to_string(),
                );
            }
        }

        let resulting_state = self
            .world
            .active()
            .map
            .object_state(object_id)
            .map(str::to_string);
        let commands = crate::placeable_behavior_runtime::compile_placeable_behavior(
            definition,
            resulting_state.as_deref(),
        );
        let mut action_messages = Vec::new();
        for command in commands {
            use crate::placeable_behavior_runtime::PlaceableBehaviorCommand;
            match command {
                PlaceableBehaviorCommand::Inspect => {
                    if !definition.interaction.message.is_empty() {
                        action_messages.push(definition.interaction.message.clone());
                    }
                }
                PlaceableBehaviorCommand::ReserveAttachment {
                    attachment_id,
                    reservation,
                } => {
                    action_messages.push(format!("Reserved {attachment_id} for {reservation}."));
                }
                PlaceableBehaviorCommand::ReleaseAttachments => {
                    action_messages.push("Released placeable attachment reservations.".to_string());
                }
                PlaceableBehaviorCommand::RestUntilMorning => {
                    self.day_clock = 8.0;
                    action_messages.push("Rested until morning.".to_string());
                }
                PlaceableBehaviorCommand::GrantPlaceholderReward { amount } => {
                    self.coin += amount;
                    action_messages
                        .push(format!("Harvested resource (+{amount} coin placeholder)."));
                }
                PlaceableBehaviorCommand::ToggleOpen => {
                    action_messages.push("Updated door state and collision.".to_string());
                }
                PlaceableBehaviorCommand::RequestSceneTransition { target } => {
                    self.update_transitions();
                    action_messages.push(format!(
                        "Requested scene transition to {}.",
                        target.as_deref().unwrap_or("configured target")
                    ));
                }
            }
        }
        let action_message = if action_messages.is_empty() {
            definition.interaction.message.clone()
        } else {
            action_messages.join(" ")
        };
        let mut message = transition_message.unwrap_or(action_message);
        if let Some(node_id) = definition.behavior.node_id.as_deref() {
            message.push_str(&format!(" [executed behavior: {node_id}]"));
        }
        message
    }
}
