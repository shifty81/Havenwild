use super::*;
use haven_assets::{
    placeable_asset_registry::PlaceableAnimationClip,
    building_instance::{
        BuildingConnectorTraversal, BuildingInstanceDefinition, BuildingInstanceViewState,
        BuildingPlacementSpace,
    },
    building_recipe::{BuildingOpeningKind, BuildingRecipePiece, BuildingRecipePieceKind},
};

#[derive(Clone, Debug)]
pub(crate) struct RuntimeBuildingDoorAnimation {
    pub instance_id: String,
    pub opening_id: String,
    pub local_tile: [i32; 2],
    pub clip: PlaceableAnimationClip,
    pub frame_index: usize,
    pub frame_elapsed_ms: f32,
}

impl RuntimeBuildingDoorAnimation {
    fn key(instance_id: &str, opening_id: &str) -> String {
        format!("{instance_id}::{opening_id}")
    }

    fn source_rect(&self) -> Option<[f32; 4]> {
        self.clip.frames.get(self.frame_index).map(|frame| frame.source_rect)
    }

    fn draw_offset_px(&self) -> [f32; 2] {
        self.clip
            .frames
            .get(self.frame_index)
            .map(|frame| frame.draw_offset_px)
            .unwrap_or([0.0, 0.0])
    }

    fn blocks_movement(&self, persistent_blocks: bool) -> bool {
        if self
            .clip
            .blocked_from_frame
            .is_some_and(|index| self.frame_index >= index)
        {
            return true;
        }
        if self
            .clip
            .passable_from_frame
            .is_some_and(|index| self.frame_index >= index)
        {
            return false;
        }
        persistent_blocks
    }

    fn advance(&mut self, dt: f32) -> bool {
        if self.clip.frames.is_empty() {
            return true;
        }
        self.frame_elapsed_ms += dt.max(0.0) * 1000.0;
        loop {
            let duration = self
                .clip
                .frames
                .get(self.frame_index)
                .map(|frame| frame.duration_ms.max(1) as f32)
                .unwrap_or(1.0);
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

#[derive(Clone, Debug)]
pub(crate) struct RuntimeBuildingDrawPiece {
    pub instance_id: String,
    pub building_anchor_tile: [i32; 2],
    pub world_tile: [i32; 2],
    pub sort_y: f32,
    pub piece: Option<BuildingRecipePiece>,
    pub composite_override: Option<haven_core::SceneVisualOverride>,
    /// Continuous-surface pieces use global world-tile coordinates and must
    /// bypass active-partition local screen conversion.
    pub surface_global: bool,
}

impl Game {
    pub(super) fn update_building_door_animations(&mut self, dt: f32) {
        let completed = self
            .building_door_animations
            .iter_mut()
            .filter_map(|(key, animation)| {
                animation.advance(dt).then(|| {
                    (
                        key.clone(),
                        animation.instance_id.clone(),
                        animation.opening_id.clone(),
                        animation.clip.to_state.clone(),
                        animation.clip.complete_sound_event.clone(),
                    )
                })
            })
            .collect::<Vec<_>>();
        for (key, instance_id, opening_id, terminal_state, sound_event) in completed {
            self.building_door_animations.remove(&key);
            if let Some(sound_event) = sound_event {
                self.log.event(&format!("Audio hook {sound_event}"));
            }
            let Some(instance) = self.building_instance_registry.entry(&instance_id).cloned() else {
                continue;
            };
            let Some(recipe) = self.building_recipe_registry.entry(&instance.recipe_id).cloned() else {
                continue;
            };
            if let Ok(revision) = self.building_instance_registry.set_opening_state(
                &instance_id,
                &recipe,
                &opening_id,
                terminal_state.clone(),
            ) {
                self.last_replication_status = format!(
                    "Building door {opening_id} reached {terminal_state} at revision {revision}"
                );
            }
        }
    }

    fn building_door_animation_at(
        &self,
        instance_id: &str,
        local_tile: [i32; 2],
    ) -> Option<&RuntimeBuildingDoorAnimation> {
        self.building_door_animations
            .values()
            .find(|animation| animation.instance_id == instance_id && animation.local_tile == local_tile)
    }

    /// Resolves the authoritative BuildingInstance set for the active runtime partition.
    /// Exterior chunks may see a continuous-surface building whose anchor lives in a
    /// neighboring storage partition; special scenes remain scene-local.
    pub(super) fn resolved_active_building_instances(&self) -> Vec<BuildingInstanceDefinition> {
        let scene = self.world.active();
        if self.active_surface_chunk_coord().is_some() {
            let manifest = haven_world::continuous_surface::ContinuousSurfaceManifest::for_world(&self.world);
            let origin = manifest
                .chunk_for_scene(&scene.id)
                .map(|chunk| [chunk.x * haven_core::MAP_W as i32, chunk.y * haven_core::MAP_H as i32]);
            self.building_instance_registry.resolved_for_scene(
                scene.id.code(),
                manifest.pcg_region.as_deref(),
                origin,
                [haven_core::MAP_W as i32, haven_core::MAP_H as i32],
                &self.building_recipe_registry,
            )
        } else {
            self.building_instance_registry.resolved_for_scene(
                scene.id.code(),
                None,
                None,
                [haven_core::MAP_W as i32, haven_core::MAP_H as i32],
                &self.building_recipe_registry,
            )
        }
    }

    pub(super) fn refresh_building_instance_views(&mut self) {
        let player_tile = [
            (self.player.x / TILE_SIZE).floor() as i32,
            (self.player.y / TILE_SIZE).floor() as i32,
        ];
        let updates = self
            .resolved_active_building_instances()
            .into_iter()
            .filter_map(|instance| {
                let recipe = self.building_recipe_registry.entry(&instance.recipe_id)?;
                let mut state = self
                    .building_instance_views
                    .get(&instance.id)
                    .copied()
                    .unwrap_or_else(|| BuildingInstanceViewState::for_definition(&instance));
                instance.refresh_view_from_world_tile(recipe, &mut state, player_tile);
                Some((instance.id, state))
            })
            .collect::<Vec<_>>();
        for (id, state) in updates {
            self.building_instance_views.insert(id, state);
        }
    }

    pub(super) fn building_move_allowed(&self, world_tile: [i32; 2]) -> bool {
        for instance in self.resolved_active_building_instances() {
            let Some(recipe) = self.building_recipe_registry.entry(&instance.recipe_id) else {
                continue;
            };
            if !instance.footprint_contains_world_tile(recipe, world_tile) {
                continue;
            }
            let state = self
                .building_instance_views
                .get(&instance.id)
                .copied()
                .unwrap_or_else(|| BuildingInstanceViewState::for_definition(&instance));
            if instance.wall_blocks_world_tile(recipe, state.active_level, world_tile) {
                return false;
            }
            if let Some(level) = recipe.level(state.active_level) {
                let local = instance.local_tile(world_tile);
                for opening in &level.openings {
                    if opening.tile != local || opening.kind != BuildingOpeningKind::Door {
                        continue;
                    }
                    let Some(definition) = self.placeable_registry.resolve_alias(&opening.asset_id) else {
                        return false;
                    };
                    let effective_state = self
                        .building_instance_registry
                        .effective_opening_state(&instance.id, opening);
                    let persistent_blocks = definition
                        .footprint_for_state(effective_state)
                        .blocks_movement;
                    let blocks = self
                        .building_door_animation_at(&instance.id, local)
                        .map_or(persistent_blocks, |animation| {
                            animation.blocks_movement(persistent_blocks)
                        });
                    if blocks {
                        return false;
                    }
                }
            }
            if state.inside
                && !instance.navigation_allows_world_tile(recipe, state.active_level, world_tile)
            {
                return false;
            }
            if instance.furnishing_blocks_world_tile(
                recipe,
                &self.placeable_registry,
                state.active_level,
                world_tile,
                |furnishing| {
                    self.building_instance_registry
                        .effective_furnishing_state(&instance.id, furnishing)
                        .map(str::to_string)
                },
            ) {
                return false;
            }
        }
        true
    }

    pub(super) fn try_traverse_building_connector_at(
        &mut self,
        x: i32,
        y: i32,
    ) -> Option<String> {
        let scene_id = self.world.active_scene.code().to_string();
        let world_tile = [x, y];
        let traversal: Option<BuildingConnectorTraversal> = self
            .resolved_active_building_instances()
            .into_iter()
            .find_map(|instance| {
                let recipe = self.building_recipe_registry.entry(&instance.recipe_id)?;
                let state = self
                    .building_instance_views
                    .get(&instance.id)
                    .copied()
                    .unwrap_or_else(|| BuildingInstanceViewState::for_definition(&instance));
                if !state.inside {
                    return None;
                }
                instance.connector_traversal_at(recipe, state, world_tile)
            });
        let traversal = traversal?;
        if let Some(state) = self.building_instance_views.get_mut(&traversal.instance_id) {
            state.active_level = traversal.to_level;
            state.inside = true;
        }
        self.player = vec2(
            (traversal.destination_world_tile[0] as f32 + 0.5) * TILE_SIZE,
            (traversal.destination_world_tile[1] as f32 + 0.5) * TILE_SIZE,
        );
        self.camera_target = self.local_world_to_runtime_world(self.player);
        self.selected_cell = (
            traversal.destination_world_tile[0],
            traversal.destination_world_tile[1],
        );
        Some(format!(
            "Building stairs {}: level {} -> {} (same scene {})",
            traversal.connector_id, traversal.from_level, traversal.to_level, scene_id
        ))
    }

    /// Applies an interaction transition to a BuildingRecipe opening while keeping
    /// the mutation in BuildingInstance persistent state. Recipe defaults are never
    /// rewritten, and camera cutaway state is never replicated or saved.
    pub(super) fn try_interact_building_opening_at(&mut self, x: i32, y: i32) -> Option<String> {
        let world_tile = [x, y];
        let mut target = None;
        for instance in self.resolved_active_building_instances() {
            let Some(recipe) = self.building_recipe_registry.entry(&instance.recipe_id) else {
                continue;
            };
            let state = self
                .building_instance_views
                .get(&instance.id)
                .copied()
                .unwrap_or_else(|| BuildingInstanceViewState::for_definition(&instance));
            let local = instance.local_tile(world_tile);
            let Some(opening) = recipe.opening_at(state.active_level, local) else {
                continue;
            };
            if opening.kind != BuildingOpeningKind::Door {
                continue;
            }
            let effective_state = self
                .building_instance_registry
                .effective_opening_state(&instance.id, opening)
                .map(str::to_string);
            target = Some((
                instance.id,
                recipe.clone(),
                opening.clone(),
                effective_state,
            ));
            break;
        }
        let (instance_id, recipe, opening, current_state) = target?;
        let definition = self.placeable_registry.resolve_alias(&opening.asset_id)?;
        let transition = definition
            .transition_for(current_state.as_deref(), "interact")
            .cloned()?;
        let authority = haven_assets::placeable_asset_registry::PlaceableMutationContext {
            is_authoritative_host: true,
            editor_preview: false,
        };
        if !transition.authority.allows(authority) {
            return Some("Building door state transition rejected: host authority required.".to_string());
        }
        let current = current_state.as_deref().unwrap_or("closed");
        if let Some(clip) = definition
            .visual
            .as_ref()
            .and_then(|visual| visual.animation_for_transition(current, &transition.to))
            .cloned()
        {
            if let Some(sound_event) = clip.start_sound_event.as_deref() {
                self.log.event(&format!("Audio hook {sound_event}"));
            }
            let key = RuntimeBuildingDoorAnimation::key(&instance_id, &opening.id);
            if self.building_door_animations.contains_key(&key) {
                return Some(format!("Door {} is already moving.", opening.id));
            }
            self.building_door_animations.insert(
                key,
                RuntimeBuildingDoorAnimation {
                    instance_id: instance_id.clone(),
                    opening_id: opening.id.clone(),
                    local_tile: opening.tile,
                    clip,
                    frame_index: 0,
                    frame_elapsed_ms: 0.0,
                },
            );
            return Some(format!(
                "Door {} animation started: {} -> {}.",
                opening.id, current, transition.to
            ));
        }
        let revision = match self.building_instance_registry.set_opening_state(
            &instance_id,
            &recipe,
            &opening.id,
            transition.to.clone(),
        ) {
            Ok(revision) => revision,
            Err(error) => return Some(format!("Building door state mutation failed: {error}")),
        };
        let envelope = match self.host_building_instance_state_envelope(
            &instance_id,
            &format!("opening {} interact", opening.id),
        ) {
            Ok(envelope) => envelope,
            Err(error) => return Some(format!("Building replication snapshot failed: {error}")),
        };
        self.last_replication_status = format!(
            "Building state seq {} prepared for host replication",
            envelope.snapshot.sequence
        );
        self.log.event(&envelope.status_line());
        let message = if transition.message.is_empty() {
            format!(
                "Building door {} -> {} (instance revision {})",
                opening.id, transition.to, revision
            )
        } else {
            format!("{} [building revision {}]", transition.message, revision)
        };
        Some(message)
    }

    pub(super) fn try_interact_building_furnishing_at(
        &mut self,
        x: i32,
        y: i32,
    ) -> Option<String> {
        let world_tile = [x, y];
        let mut target = None;
        for instance in self.resolved_active_building_instances() {
            let Some(recipe) = self.building_recipe_registry.entry(&instance.recipe_id) else {
                continue;
            };
            let state = self
                .building_instance_views
                .get(&instance.id)
                .copied()
                .unwrap_or_else(|| BuildingInstanceViewState::for_definition(&instance));
            if !state.inside {
                continue;
            }
            let Some(furnishing) = instance.furnishing_interaction_at(
                recipe,
                &self.placeable_registry,
                state.active_level,
                world_tile,
            ) else {
                continue;
            };
            target = Some((instance.id, recipe.clone(), furnishing.clone()));
            break;
        }
        let (instance_id, recipe, furnishing) = target?;
        let Some(asset_id) = furnishing.asset_id.as_deref() else {
            let sockets = furnishing
                .interaction_sockets
                .iter()
                .map(|socket| format!("{}:{}", socket.id, socket.purpose))
                .collect::<Vec<_>>()
                .join(", ");
            return Some(format!(
                "{} is logically interactive but its exact visual is deferred. Sockets: {}",
                furnishing.id,
                if sockets.is_empty() { "none" } else { sockets.as_str() }
            ));
        };
        let definition = self.placeable_registry.resolve_alias(asset_id)?.clone();
        let current_state = self
            .building_instance_registry
            .effective_furnishing_state(&instance_id, &furnishing)
            .map(str::to_string);
        let trigger = definition.behavior.interaction_trigger.as_str();
        let transition = definition
            .transition_for(current_state.as_deref(), trigger)
            .cloned();
        let mut transition_message = None;
        if let Some(transition) = transition {
            let authority = haven_assets::placeable_asset_registry::PlaceableMutationContext {
                is_authoritative_host: true,
                editor_preview: false,
            };
            if transition.authority.allows(authority) {
                match self.building_instance_registry.set_furnishing_state(
                    &instance_id,
                    &recipe,
                    &furnishing.id,
                    transition.to.clone(),
                ) {
                    Ok(revision) => {
                        transition_message = Some(if transition.message.is_empty() {
                            format!(
                                "Building furnishing {} -> {} (instance revision {})",
                                furnishing.id, transition.to, revision
                            )
                        } else {
                            format!("{} [building revision {}]", transition.message, revision)
                        });
                        if let Ok(envelope) = self.host_building_instance_state_envelope(
                            &instance_id,
                            &format!("furnishing {} interact", furnishing.id),
                        ) {
                            self.last_replication_status = format!(
                                "Building state seq {} prepared for host replication",
                                envelope.snapshot.sequence
                            );
                            self.log.event(&envelope.status_line());
                        }
                    }
                    Err(error) => return Some(format!("Building furnishing mutation failed: {error}")),
                }
            } else {
                return Some("Building furnishing state transition rejected: host authority required.".to_string());
            }
        }

        let resulting_state = self
            .building_instance_registry
            .effective_furnishing_state(&instance_id, &furnishing)
            .map(str::to_string);
        let commands = crate::placeable_behavior_runtime::compile_placeable_behavior(
            &definition,
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
                PlaceableBehaviorCommand::ReserveAttachment { attachment_id, reservation } => {
                    action_messages.push(format!("Reserved {attachment_id} for {reservation}."));
                }
                PlaceableBehaviorCommand::ReleaseAttachments => {
                    action_messages.push("Released furnishing attachment reservations.".to_string());
                }
                PlaceableBehaviorCommand::RestUntilMorning => {
                    self.day_clock = 8.0;
                    action_messages.push("Rested until morning.".to_string());
                }
                PlaceableBehaviorCommand::GrantPlaceholderReward { amount } => {
                    self.coin += amount;
                    action_messages.push(format!("Building furnishing reward (+{amount} coin placeholder)."));
                }
                PlaceableBehaviorCommand::ToggleOpen => {
                    action_messages.push("Updated furnishing state and collision.".to_string());
                }
                PlaceableBehaviorCommand::RequestSceneTransition { target } => {
                    action_messages.push(format!(
                        "Furnishing requested transition to {}.",
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
        Some(transition_message.unwrap_or(action_message))
    }

    pub(super) fn visible_building_draw_pieces(&self) -> Vec<RuntimeBuildingDrawPiece> {
        let mut result = Vec::new();
        for instance in self.resolved_active_building_instances() {
            let Some(recipe) = self.building_recipe_registry.entry(&instance.recipe_id) else {
                continue;
            };
            let state = self
                .building_instance_views
                .get(&instance.id)
                .copied()
                .unwrap_or_else(|| BuildingInstanceViewState::for_definition(&instance));
            let building_bottom =
                (instance.anchor_tile[1] + recipe.footprint[1] as i32) as f32 * TILE_SIZE;
            if !state.inside {
                if let Some(entry) = self.world.active().visual_overrides.iter().find(|entry| {
                    entry.is_building_composite()
                        && entry.x == instance.anchor_tile[0]
                        && entry.y == instance.anchor_tile[1]
                        && entry.w == recipe.footprint[0] as i32
                        && entry.h == recipe.footprint[1] as i32
                }) {
                    result.push(RuntimeBuildingDrawPiece {
                        instance_id: instance.id.clone(),
                        building_anchor_tile: instance.anchor_tile,
                        world_tile: instance.anchor_tile,
                        sort_y: building_bottom,
                        piece: None,
                        composite_override: Some(entry.clone()),
                        surface_global: false,
                    });
                    continue;
                }
            }
            for visible in self
                .building_instance_registry
                .visible_pieces_for_instance(&instance, recipe, state)
            {
                let sort_y = if visible.piece.kind == BuildingRecipePieceKind::Roof {
                    building_bottom
                } else {
                    (visible.world_tile[1] as f32 + 1.0) * TILE_SIZE
                };
                result.push(RuntimeBuildingDrawPiece {
                    instance_id: instance.id.clone(),
                    building_anchor_tile: instance.anchor_tile,
                    world_tile: visible.world_tile,
                    sort_y,
                    piece: Some(visible.piece),
                    composite_override: None,
                    surface_global: false,
                });
            }
        }
        result
    }

    /// Resolves continuous-surface buildings in global tile space for rendering.
    ///
    /// Storage partitions are persistence/streaming units, not visibility units.
    /// A building remains renderable while its world-space footprint intersects
    /// the camera even when its anchor belongs to a neighboring active chunk.
    pub(super) fn visible_surface_building_draw_pieces(&self) -> Vec<RuntimeBuildingDrawPiece> {
        let manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
        let active_region = manifest.pcg_region.as_deref();
        let mut result = Vec::new();

        for source in self.building_instance_registry.entries() {
            if source.placement_space != BuildingPlacementSpace::ContinuousSurface
                || source.surface_region_id.as_deref() != active_region
            {
                continue;
            }
            let Some(global_anchor) = source.global_anchor_tile else {
                continue;
            };
            let Some(recipe) = self.building_recipe_registry.entry(&source.recipe_id) else {
                continue;
            };

            let mut instance = source.clone();
            instance.anchor_tile = global_anchor;
            let state = self
                .building_instance_views
                .get(&instance.id)
                .copied()
                .unwrap_or_else(|| BuildingInstanceViewState::for_definition(&instance));
            let building_bottom =
                (global_anchor[1] + recipe.footprint[1] as i32) as f32 * TILE_SIZE;

            if !state.inside {
                let address = haven_world::surface_tile_address(
                    haven_world::open_world::WorldTileCoord::new(global_anchor[0], global_anchor[1]),
                );
                let scene_id = manifest.scene_id_for_chunk(address.chunk);
                if let Some(scene) = self.world.scene_by_id(&scene_id) {
                    if let Some(entry) = scene.visual_overrides.iter().find(|entry| {
                        entry.is_building_composite()
                            && entry.x == address.local_x
                            && entry.y == address.local_y
                            && entry.w == recipe.footprint[0] as i32
                            && entry.h == recipe.footprint[1] as i32
                    }) {
                        let mut global_entry = entry.clone();
                        global_entry.x = global_anchor[0];
                        global_entry.y = global_anchor[1];
                        result.push(RuntimeBuildingDrawPiece {
                            instance_id: instance.id.clone(),
                            building_anchor_tile: global_anchor,
                            world_tile: global_anchor,
                            sort_y: building_bottom,
                            piece: None,
                            composite_override: Some(global_entry),
                            surface_global: true,
                        });
                        continue;
                    }
                }
            }

            for visible in self
                .building_instance_registry
                .visible_pieces_for_instance(&instance, recipe, state)
            {
                let sort_y = if visible.piece.kind == BuildingRecipePieceKind::Roof {
                    building_bottom
                } else {
                    (visible.world_tile[1] as f32 + 1.0) * TILE_SIZE
                };
                result.push(RuntimeBuildingDrawPiece {
                    instance_id: instance.id.clone(),
                    building_anchor_tile: global_anchor,
                    world_tile: visible.world_tile,
                    sort_y,
                    piece: Some(visible.piece),
                    composite_override: None,
                    surface_global: true,
                });
            }
        }
        result
    }

    pub(super) fn draw_building_piece(&self, piece: &RuntimeBuildingDrawPiece) -> bool {
        if let Some(entry) = piece.composite_override.as_ref() {
            let Some(texture) = self.world_visual_override_textures.get(&entry.asset_path) else {
                return false;
            };
            let world = vec2(
                entry.x as f32 * TILE_SIZE,
                entry.y as f32 * TILE_SIZE,
            );
            let top_left = if piece.surface_global {
                self.runtime_world_to_screen(world)
            } else {
                self.world_to_screen(world)
            };
            draw_texture_ex(
                texture,
                top_left.x,
                top_left.y,
                WHITE,
                DrawTextureParams {
                    dest_size: Some(vec2(
                        entry.w as f32 * TILE_SIZE,
                        entry.h as f32 * TILE_SIZE,
                    )),
                    ..Default::default()
                },
            );
            return true;
        }

        let Some(recipe_piece) = piece.piece.as_ref() else {
            return false;
        };
        let Some(definition) = self.placeable_registry.resolve_alias(&recipe_piece.asset_id) else {
            return false;
        };
        let (Some(texture), Some(visual)) = (
            self.placeable_textures.get(definition.pack_qualified_id()),
            definition.visual.as_ref(),
        ) else {
            return false;
        };
        let animation = self.building_door_animation_at(&piece.instance_id, recipe_piece.tile);
        let (source_rect, draw_offset_px) = if let Some(animation) = animation {
            let Some(source_rect) = animation.source_rect() else { return false; };
            (source_rect, animation.draw_offset_px())
        } else {
            let Some(frame) = visual.frame_for_state(recipe_piece.state.as_deref()) else { return false; };
            (frame.source_rect, frame.draw_offset_px)
        };
        let top_left_world = if let Some(origin) = recipe_piece.render_origin_px {
            vec2(
                piece.building_anchor_tile[0] as f32 * TILE_SIZE + origin[0] as f32,
                piece.building_anchor_tile[1] as f32 * TILE_SIZE + origin[1] as f32,
            )
        } else {
            let foot_world = vec2(
                (piece.world_tile[0] as f32 + 0.5) * TILE_SIZE,
                (piece.world_tile[1] as f32 + 1.0) * TILE_SIZE,
            );
            vec2(
                foot_world.x - visual.foot_anchor[0],
                foot_world.y - visual.foot_anchor[1],
            )
        };
        let top_left_world = top_left_world + vec2(draw_offset_px[0], draw_offset_px[1]);
        let top_left = if piece.surface_global {
            self.runtime_world_to_screen(top_left_world)
        } else {
            self.world_to_screen(top_left_world)
        };
        draw_texture_ex(
            texture,
            top_left.x,
            top_left.y,
            WHITE,
            DrawTextureParams {
                dest_size: Some(vec2(source_rect[2], source_rect[3])),
                source: Some(Rect::new(
                    source_rect[0],
                    source_rect[1],
                    source_rect[2],
                    source_rect[3],
                )),
                ..Default::default()
            },
        );
        true
    }
}
