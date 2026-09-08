use super::*;

impl Game {
    pub(super) fn reset_active_scene(&mut self) {
        self.selected_object_index = None;
        self.object_list_offset = 0;
        let current = self.world.active();
        let Some(legacy_id) = current.id.legacy_scene_id() else {
            self.status_message = format!(
                "Reset is unavailable for project scene {} until scene templates are generalized",
                current.id
            );
            self.log.event(&self.status_message);
            return;
        };
        let mut replacement =
            SceneMap::starter(legacy_id, current.kind, current.spawn_x, current.spawn_y);
        let cleanup_report = if replacement.kind != SceneKind::Interior {
            Some(apply_coastline_tile_pass(
                &mut replacement.map,
                replacement.biome,
            ))
        } else {
            None
        };
        let scene_name = replacement.name.clone();
        if let Some(scene) = self.world.scene_mut(&replacement.id) {
            *scene = replacement;
        }
        if let Some(report) = cleanup_report {
            if report.total_mutations() > 0 {
                self.log
                    .event(&format!("{scene_name} {}", report.status_line()));
            }
        }
        self.set_player_to_active_spawn();
        self.status_message = format!("Reset {scene_name} from starter template");
        self.log.event(&self.status_message);
    }

    pub(super) fn regenerate_active_scene(&mut self) {
        self.selected_object_index = None;
        self.object_list_offset = 0;
        self.world_seed = self.world_seed.wrapping_add(1);
        let current = self.world.active();
        let Some(legacy_id) = current.id.legacy_scene_id() else {
            self.status_message = format!(
                "Regeneration is unavailable for project scene {} until scene templates are generalized",
                current.id
            );
            self.log.event(&self.status_message);
            return;
        };
        let seed = self
            .world_seed
            .wrapping_add((legacy_id as u64).wrapping_mul(97));
        // SceneMap::starter_seeded is a legacy u32 compatibility API. Preserve the
        // full u64 world-seed identity above, then fold both halves at this boundary
        // instead of silently discarding the high 32 bits.
        let legacy_seed = (seed as u32) ^ ((seed >> 32) as u32);
        let mut replacement = SceneMap::starter_seeded(
            legacy_id,
            current.kind,
            current.spawn_x,
            current.spawn_y,
            legacy_seed,
        );
        let cleanup_report = if replacement.kind != SceneKind::Interior {
            Some(apply_coastline_tile_pass(
                &mut replacement.map,
                replacement.biome,
            ))
        } else {
            None
        };
        let scene_name = replacement.name.clone();
        if let Some(scene) = self.world.scene_mut(&replacement.id) {
            *scene = replacement;
        }
        if let Some(report) = cleanup_report {
            if report.total_mutations() > 0 {
                self.log
                    .event(&format!("{scene_name} {}", report.status_line()));
            }
        }
        self.set_player_to_active_spawn();
        self.status_message = format!("Regenerated {scene_name} with seed {seed}");
        self.log.event(&self.status_message);
    }

    pub(super) fn clone_active_scene_to_target(&mut self) {
        let source = match self.world.scene_by_reference(&self.world.active_scene) {
            Some(scene) => scene.clone(),
            None => {
                self.status_message = "Clone failed: active scene missing".to_string();
                self.log.event(&self.status_message);
                return;
            }
        };
        let source_id = source.id.clone();
        let source_name = source.name.clone();
        let target = SceneId::ALL[self.selected_transition_target];
        if target == source_id {
            self.status_message = "Clone target must differ from active scene".to_string();
            self.log.event(&self.status_message);
            return;
        }

        let mut replacement = source;
        replacement.id = target.into();
        replacement.name = format!("{source_name} Copy");
        for transition in &mut replacement.transitions {
            if transition.target == source_id {
                transition.target = target.into();
            }
        }

        if let Some(scene) = self.world.scene_mut(target) {
            *scene = replacement;
        }
        self.status_message = format!("Cloned {source_name} into {}", target.label());
        self.log.event(&self.status_message);
    }

    pub(super) fn set_player_to_active_spawn(&mut self) {
        let scene = self.world.active();
        self.player = vec2(
            scene.spawn_x as f32 * TILE_SIZE + TILE_SIZE * 0.5,
            scene.spawn_y as f32 * TILE_SIZE + TILE_SIZE * 0.5,
        );
        self.camera_target = self.local_world_to_runtime_world(self.player);
        self.selected_cell = (scene.spawn_x, scene.spawn_y);
        self.inspector = inspect_scene_cell(scene, scene.spawn_x, scene.spawn_y);
    }


    fn player_ladder_climb_for_movement(&self, movement: Vec2) -> bool {
        use haven_world::CardinalDirectionV2;
        use haven_world::open_world::WorldTileCoord;

        if self.world.active().kind != SceneKind::Exterior
            || movement.y.abs() <= movement.x.abs()
            || movement.y.abs() < f32::EPSILON
        {
            return false;
        }
        let global = self.local_world_to_runtime_world(self.player);
        let from = WorldTileCoord::new(
            (global.x / TILE_SIZE).floor() as i32,
            (global.y / TILE_SIZE).floor() as i32,
        );
        let (direction, to) = if movement.y > 0.0 {
            (
                CardinalDirectionV2::South,
                WorldTileCoord::new(from.x, from.y + 1),
            )
        } else {
            (
                CardinalDirectionV2::North,
                WorldTileCoord::new(from.x, from.y - 1),
            )
        };
        // A constructed ladder visually projects below its structural host.
        // Climb presentation must begin at the authored foot and continue over
        // the full ladder column, not only on the final logical host edge. This
        // makes the ladder behave where the player actually sees it on screen.
        if self.surface_ladder_projection_contains_tile(from)
            || self.surface_ladder_projection_contains_tile(to)
        {
            return true;
        }

        self.structural_connector_for_edge(from, to, direction)
            == Some(crate::runtime_structural_connectors::StructuralConnectorKind::Ladder)
    }

    fn surface_ladder_projection_contains_tile(
        &self,
        tile: haven_world::open_world::WorldTileCoord,
    ) -> bool {
        use haven_world::{CardinalDirectionV2, EdgeMaskV2};

        let manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
        const MAX_LADDER_SCAN_ROWS: i32 = 12;
        for host_y in (tile.y - MAX_LADDER_SCAN_ROWS)..tile.y {
            let Some(host) = self.surface_structural_at_global_in_manifest(
                &manifest,
                tile.x,
                host_y,
            ) else {
                continue;
            };
            if !host.exposed_edges.contains(EdgeMaskV2::SOUTH) {
                continue;
            }
            if self.structural_connector_from_host_edge_in_manifest(
                &manifest,
                tile.x,
                host_y,
                CardinalDirectionV2::South,
            ) != Some(crate::runtime_structural_connectors::StructuralConnectorKind::Ladder)
            {
                continue;
            }
            let face_segments = crate::runtime_structural_cliff_shapes::authored_south_face_segments(host)
                .max(1);
            if tile_within_ladder_projection(host_y, tile.y, face_segments) {
                return true;
            }
        }
        false
    }

    pub(super) fn update_player(&mut self, dt: f32) {
        let mut character = self.player_character_state();
        if character.action_locks_movement() {
            character.moving = false;
            character.locomotion = CharacterAnimationIntent::Idle;
            character.locomotion_phase *= (1.0 - dt * 12.0).max(0.0);
            self.set_player_character_state(character);
            return;
        }

        let input = self.controls.movement_vector();
        if input.length_squared() > 0.0 {
            character.moving = true;
            let movement_amount = input.length().clamp(0.0, 1.0);
            let movement = input.normalize();
            character.facing = [movement.x, movement.y];
            let climbing_ladder = self.player_ladder_climb_for_movement(movement);
            let sprinting = !climbing_ladder && self.character_is_sprinting();
            character.locomotion = if climbing_ladder {
                CharacterAnimationIntent::Climb
            } else if sprinting {
                CharacterAnimationIntent::Run
            } else {
                CharacterAnimationIntent::Walk
            };
            character.locomotion_phase += dt
                * if climbing_ladder {
                    7.5
                } else if sprinting {
                    13.5
                } else {
                    9.5
                }
                * movement_amount.max(0.35);
            let movement_speed = if climbing_ladder {
                // A ladder is an explicit climb connector, not a hidden slope.
                // Keep auto-climb responsive while making its cadence visibly
                // distinct from ordinary walking/running.
                PLAYER_SPEED * 0.58
            } else if sprinting {
                PLAYER_SPEED * 1.55
            } else {
                PLAYER_SPEED
            };
            let delta = movement * movement_speed * movement_amount * dt;
            // Resolve each axis independently so diagonal movement slides along
            // walls instead of alternating between moving and stopping.
            let before_x_global = self.local_world_to_runtime_world(self.player);
            let next_x_global = before_x_global + vec2(delta.x, 0.0);
            let from_x_tile = haven_world::open_world::WorldTileCoord::new(
                (before_x_global.x / TILE_SIZE).floor() as i32,
                (before_x_global.y / TILE_SIZE).floor() as i32,
            );
            let to_x_tile = haven_world::open_world::WorldTileCoord::new(
                (next_x_global.x / TILE_SIZE).floor() as i32,
                (next_x_global.y / TILE_SIZE).floor() as i32,
            );
            let next_x = vec2(self.player.x + delta.x, self.player.y);
            if self.structural_surface_move_allowed(from_x_tile, to_x_tile) {
                if let Some(next_x) = self.try_stream_exterior_position(next_x) {
                    let tx = (next_x.x / TILE_SIZE).floor() as i32;
                    let ty = (next_x.y / TILE_SIZE).floor() as i32;
                    let base_allowed = self.building_move_allowed([tx, ty])
                        && self.world.active().map.is_cell_walkable(tx, ty);
                    if self.collision_override_registry.allows_position(
                        self.world.active().id.code(),
                        next_x.x,
                        next_x.y,
                        base_allowed,
                    ) {
                        self.player.x = next_x.x;
                        self.player.y = next_x.y;
                    }
                }
            }
            let before_y_global = self.local_world_to_runtime_world(self.player);
            let next_y_global = before_y_global + vec2(0.0, delta.y);
            let from_y_tile = haven_world::open_world::WorldTileCoord::new(
                (before_y_global.x / TILE_SIZE).floor() as i32,
                (before_y_global.y / TILE_SIZE).floor() as i32,
            );
            let to_y_tile = haven_world::open_world::WorldTileCoord::new(
                (next_y_global.x / TILE_SIZE).floor() as i32,
                (next_y_global.y / TILE_SIZE).floor() as i32,
            );
            let next_y = vec2(self.player.x, self.player.y + delta.y);
            if self.structural_surface_move_allowed(from_y_tile, to_y_tile) {
                if let Some(next_y) = self.try_stream_exterior_position(next_y) {
                    let tx = (next_y.x / TILE_SIZE).floor() as i32;
                    let ty = (next_y.y / TILE_SIZE).floor() as i32;
                    let base_allowed = self.building_move_allowed([tx, ty])
                        && self.world.active().map.is_cell_walkable(tx, ty);
                    if self.collision_override_registry.allows_position(
                        self.world.active().id.code(),
                        next_y.x,
                        next_y.y,
                        base_allowed,
                    ) {
                        self.player = next_y;
                    }
                }
            }
            self.synchronize_surface_position();
        } else {
            character.moving = false;
            character.locomotion = CharacterAnimationIntent::Idle;
            character.locomotion_phase *= (1.0 - dt * 8.0).max(0.0);
        }
        let moved_or_moving = character.moving;
        self.set_player_character_state(character);
        // Threshold transitions are traversal authority. Buildings, caves, and
        // authored scene links trigger when the player actually walks onto the
        // threshold cell; exterior storage-partition links remain inert inside
        // update_transitions(). This restores door -> linked interior travel
        // without requiring a second interaction after the door opens.
        if moved_or_moving {
            self.update_transitions();
        }
    }

    pub(super) fn update_transitions(&mut self) {
        let tx = (self.player.x / TILE_SIZE).floor() as i32;
        let ty = (self.player.y / TILE_SIZE).floor() as i32;
        if let Some(transition) = self.world.active().transition_at(tx, ty).cloned() {
            let surface_streaming = self.active_surface_chunk_coord().is_some()
                && (haven_world::scene_id_is_surface_partition(transition.target.project_id())
                    || self
                        .world
                        .scene_by_reference(&transition.target)
                        .is_some_and(|target| {
                            haven_world::transition_uses_surface_streaming(
                                self.world.active(),
                                target,
                            )
                        }));
            if surface_streaming {
                // Exterior partitions are storage only. Historical edge triggers
                // remain inert even when the target has not streamed in yet.
                return;
            }
            if let Err(error) = self.world.set_active_scene(transition.target.clone()) {
                self.status_message = format!("Transition blocked: {error}");
                self.log.event(&self.status_message);
                return;
            }
            self.player = vec2(
                transition.spawn_x as f32 * TILE_SIZE + TILE_SIZE * 0.5,
                transition.spawn_y as f32 * TILE_SIZE + TILE_SIZE * 0.5,
            );
            self.camera_target = self.local_world_to_runtime_world(self.player);
            self.status_message = format!("Entered {}", transition.target.label());
            self.log.event(&format!(
                "Scene transition {} to {}",
                transition.label,
                transition.target.label()
            ));
            self.refresh_world_paint_render_bindings_for_active_scene(
                "Transition paint render binding refresh",
            );
            self.persist_scene_transition_state("scene transition");
        }
    }

    pub(super) fn jump_scene(&mut self, direction: i32) {
        let (x, y) = self.world.cycle_scene(direction);
        self.selected_object_index = None;
        self.object_list_offset = 0;
        self.set_player_to_cell(x, y);
        self.status_message = format!("Dev jumped to {}", self.world.active().name);
        self.refresh_world_paint_render_bindings_for_active_scene(
            "Scene jump paint render binding refresh",
        );
        self.log.event(&self.status_message);
        self.persist_scene_transition_state("developer scene jump");
    }

    pub(super) fn jump_to_scene(&mut self, scene_id: SceneId) {
        self.world
            .set_active_scene(scene_id)
            .expect("jump target must be a loaded legacy scene");
        self.selected_transition_index = 0;
        self.selected_object_index = None;
        self.object_list_offset = 0;
        let (spawn_x, spawn_y, scene_name) = {
            let scene = self.world.active();
            (scene.spawn_x, scene.spawn_y, scene.name.clone())
        };
        self.set_player_to_cell(spawn_x, spawn_y);
        self.status_message = format!("Dev jumped to {scene_name}");
        self.refresh_world_paint_render_bindings_for_active_scene(
            "Scene jump paint render binding refresh",
        );
        self.log.event(&self.status_message);
    }

    pub(super) fn set_player_to_cell(&mut self, x: i32, y: i32) {
        self.player = vec2(
            x as f32 * TILE_SIZE + TILE_SIZE * 0.5,
            y as f32 * TILE_SIZE + TILE_SIZE * 0.5,
        );
        self.camera_target = self.local_world_to_runtime_world(self.player);
        self.selected_cell = (x, y);
        self.inspector = inspect_scene_cell(self.world.active(), x, y);
    }

    pub(super) fn update_customers(&mut self, dt: f32) {
        let result = update_tavern_customers(
            &mut self.customers,
            &mut self.customer_timer,
            dt,
            self.tavern_open,
            &self.world.active_scene,
        );
        self.coin += result.coin_delta;
        self.reputation += result.reputation_delta;
        if result.entered {
            self.log.event("Customer entered from road");
        }
    }

    pub(super) fn update_camera(&mut self, dt: f32) {
        let viewport = vec2(screen_width().max(1.0), screen_height().max(1.0));
        let dimensions = self.world.active().dimensions;
        let scene_size = vec2(dimensions.width as f32 * TILE_SIZE, dimensions.height as f32 * TILE_SIZE);
        let desired = if self.active_surface_chunk_coord().is_some() {
            // Streamed overworld traversal uses one global surface coordinate
            // system. Bounded exterior instances such as the Home Estate stay
            // scene-local and clamp to their authored map bounds.
            self.local_world_to_runtime_world(self.player)
        } else {
            clamp_camera_center_to_scene(self.player, viewport, self.camera_zoom, scene_size)
        };
        let t = 1.0 - (-9.0 * dt).exp();
        let smoothed = self.camera_target.lerp(desired, t);
        self.camera_target = if self.active_surface_chunk_coord().is_some() {
            smoothed
        } else {
            clamp_camera_center_to_scene(smoothed, viewport, self.camera_zoom, scene_size)
        };
    }

    pub(super) fn screen_to_world(&self, screen: Vec2) -> Vec2 {
        let visible = vec2(screen_width(), screen_height());
        let runtime_world = (screen - visible * 0.5) / self.camera_zoom + self.camera_target;
        self.runtime_world_to_active_local(runtime_world)
    }

    pub(super) fn runtime_world_to_screen(&self, runtime_world: Vec2) -> Vec2 {
        let visible = vec2(screen_width(), screen_height());
        runtime_world - self.camera_target + visible * 0.5
    }

    pub(super) fn world_to_screen(&self, world: Vec2) -> Vec2 {
        self.runtime_world_to_screen(self.local_world_to_runtime_world(world))
    }

    pub(super) fn game_camera(&self) -> Camera2D {
        let visible = vec2(screen_width().max(1.0), screen_height().max(1.0));
        Camera2D {
            target: visible * 0.5,
            // Runtime drawing uses screen-style coordinates where +Y points down.
            // A positive camera Y zoom preserves that orientation in Macroquad.
            zoom: vec2(
                2.0 * self.camera_zoom / visible.x,
                2.0 * self.camera_zoom / visible.y,
            ),
            ..Default::default()
        }
    }
}

fn clamp_camera_center_to_scene(
    target: Vec2,
    viewport_pixels: Vec2,
    zoom: f32,
    scene_pixels: Vec2,
) -> Vec2 {
    let zoom = zoom.max(0.01);
    let half_visible = viewport_pixels / zoom * 0.5;
    vec2(
        clamp_camera_axis(target.x, half_visible.x, scene_pixels.x),
        clamp_camera_axis(target.y, half_visible.y, scene_pixels.y),
    )
}

fn clamp_camera_axis(target: f32, half_visible: f32, scene_extent: f32) -> f32 {
    if scene_extent <= half_visible * 2.0 {
        scene_extent * 0.5
    } else {
        target.clamp(half_visible, scene_extent - half_visible)
    }
}

#[cfg(test)]
mod camera_tests {
    use super::clamp_camera_center_to_scene;
    use macroquad::prelude::vec2;

    #[test]
    fn camera_recenters_when_scene_is_smaller_than_viewport() {
        let center = clamp_camera_center_to_scene(
            vec2(10.0, 10.0),
            vec2(1280.0, 720.0),
            1.15,
            vec2(640.0, 480.0),
        );
        assert_eq!(center, vec2(320.0, 240.0));
    }

    #[test]
    fn camera_stops_at_scene_edges_instead_of_following_player_off_center() {
        let center = clamp_camera_center_to_scene(
            vec2(20.0, 2020.0),
            vec2(1280.0, 720.0),
            1.15,
            vec2(3072.0, 2048.0),
        );
        let half_visible = vec2(1280.0, 720.0) / 1.15 * 0.5;
        assert!((center.x - half_visible.x).abs() < 0.01);
        assert!((center.y - (2048.0 - half_visible.y)).abs() < 0.01);
    }

    #[test]
    fn camera_keeps_player_centered_away_from_scene_edges() {
        let target = vec2(1500.0, 1000.0);
        let center =
            clamp_camera_center_to_scene(target, vec2(1280.0, 720.0), 1.15, vec2(3072.0, 2048.0));
        assert_eq!(center, target);
    }
}

fn tile_within_ladder_projection(host_y: i32, tile_y: i32, face_segments: u8) -> bool {
    // AC3R4E: connector presentation and climb ownership terminate on the
    // exact receiver row of the structural face. An N-tier cliff therefore
    // owns exactly N ladder rows below the host, never N+1.
    let depth = i32::from(face_segments.max(1));
    tile_y > host_y && tile_y <= host_y + depth
}

#[cfg(test)]
mod ladder_projection_tests {
    use super::*;

    #[test]
    fn two_tier_ladder_reaches_the_lower_walkable_receiver_row() {
        assert!(tile_within_ladder_projection(10, 11, 2));
        assert!(tile_within_ladder_projection(10, 12, 2));
        assert!(!tile_within_ladder_projection(10, 13, 2));
    }
}
