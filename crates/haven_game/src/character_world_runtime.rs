use super::*;
use haven_core::ProjectSceneId;
use haven_save::{save_character_world_link, CharacterWorldLink};
use std::path::Path;

impl Game {
    pub(super) fn restore_character_world_link(
        world: &mut GameWorld,
        link: &CharacterWorldLink,
    ) -> Option<String> {
        if link.world_scene.trim().is_empty() {
            return None;
        }
        let scene = SceneReference::new(link.world_scene.clone());
        if world.scene_by_reference(&scene).is_none() {
            return Some(format!(
                "character scene {} unavailable; using world spawn",
                link.world_scene
            ));
        }
        match world.set_active_scene(scene) {
            Ok(()) => Some(format!(
                "restored character {} in scene {}",
                link.character_id.0, link.world_scene
            )),
            Err(error) => Some(format!("character scene restore failed: {error}")),
        }
    }

    pub(super) fn character_world_position_or_spawn(
        link: &CharacterWorldLink,
        spawn_x: i32,
        spawn_y: i32,
    ) -> Vec2 {
        let [x, y] = link.world_position;
        let mut tile = if x == 0 && y == 0 {
            [spawn_x, spawn_y]
        } else {
            [x, y]
        };
        let manifest = haven_world::ContinuousSurfaceManifest::legacy_starter_bridge();
        let scene_id = ProjectSceneId::new(link.world_scene.clone());
        if let Some(binding) = manifest.binding_for_scene(&scene_id) {
            let already_local =
                (0..MAP_W as i32).contains(&tile[0]) && (0..MAP_H as i32).contains(&tile[1]);
            if !already_local {
                tile[0] -= binding.chunk.x * MAP_W as i32;
                tile[1] -= binding.chunk.y * MAP_H as i32;
            }
        }
        // Character links for exterior scenes may contain global surface coordinates.
        // Until a matching surface binding is available, never interpret an out-of-range
        // global coordinate as a local scene coordinate: use the authored safe spawn.
        if !(0..MAP_W as i32).contains(&tile[0]) || !(0..MAP_H as i32).contains(&tile[1]) {
            tile = [spawn_x, spawn_y];
        }
        vec2(
            tile[0] as f32 * TILE_SIZE + TILE_SIZE * 0.5,
            tile[1] as f32 * TILE_SIZE + TILE_SIZE * 0.5,
        )
    }


    /// Repair an exterior character position that resolves onto water, a blocked
    /// structural lip/face, or another non-walkable cell. Saved character links
    /// may outlive world-generation changes, so boot must validate the actual
    /// loaded surface rather than trusting the stored tile blindly.
    pub(super) fn repair_exterior_player_spawn_if_unsafe(&mut self) {
        if self.world.active().kind != SceneKind::Exterior {
            return;
        }

        let current_x = (self.player.x / TILE_SIZE).floor() as i32;
        let current_y = (self.player.y / TILE_SIZE).floor() as i32;
        let current_global = self.surface_global_tile();
        let current_safe = {
            let scene = self.world.active();
            let tile = scene.map.get(current_x, current_y);
            !tile.is_water()
                && scene.is_cell_walkable(current_x, current_y)
                && !self.structural_cliff_face_occupies_tile(current_global)
                && self
                    .surface_structural_at_global(current_global.x, current_global.y)
                    .is_none_or(|cell| cell.blocked_edges.is_empty())
        };
        if current_safe {
            return;
        }

        // Prefer a nearby dry Level-0 cell in the currently active partition.
        // This keeps startup deterministic and avoids forcing a scene transition
        // merely to recover from a stale/unsafe saved spawn.
        const MAX_SAFE_SPAWN_RADIUS: i32 = 48;
        let origin = self.active_surface_origin_px();
        let mut best: Option<(i32, i32, i32)> = None;
        let scene = self.world.active();
        for radius in 0..=MAX_SAFE_SPAWN_RADIUS {
            for dy in -radius..=radius {
                for dx in -radius..=radius {
                    if radius > 0 && dx.abs() != radius && dy.abs() != radius {
                        continue;
                    }
                    let x = current_x + dx;
                    let y = current_y + dy;
                    if TavernMap::idx(x, y).is_none() {
                        continue;
                    }
                    let tile = scene.map.get(x, y);
                    if tile.is_water() || !scene.is_cell_walkable(x, y) {
                        continue;
                    }
                    let global = haven_world::open_world::WorldTileCoord::new(
                        (origin.x / TILE_SIZE).round() as i32 + x,
                        (origin.y / TILE_SIZE).round() as i32 + y,
                    );
                    if self.structural_cliff_face_occupies_tile(global) {
                        continue;
                    }
                    let blocked_lip = self
                        .surface_structural_at_global(global.x, global.y)
                        .is_some_and(|cell| !cell.blocked_edges.is_empty());
                    if blocked_lip {
                        continue;
                    }
                    let preference = match tile {
                        TileKind::Grass | TileKind::TallGrass | TileKind::Road | TileKind::StonePath => 0,
                        TileKind::Sand | TileKind::WetSand | TileKind::MountainPath => 1,
                        _ => 2,
                    };
                    best = Some((preference, x, y));
                    break;
                }
                if best.is_some() {
                    break;
                }
            }
            if best.is_some() {
                break;
            }
        }

        if let Some((_preference, safe_x, safe_y)) = best {
            self.player = vec2(
                safe_x as f32 * TILE_SIZE + TILE_SIZE * 0.5,
                safe_y as f32 * TILE_SIZE + TILE_SIZE * 0.5,
            );
            self.camera_target = self.local_world_to_runtime_world(self.player);
            self.selected_cell = (safe_x, safe_y);
            self.inspector = inspect_scene_cell(self.world.active(), safe_x, safe_y);
            self.status_message = format!(
                "Unsafe exterior spawn repaired to dry tile {},{}",
                safe_x, safe_y
            );
            self.log.event(&self.status_message);
            if let Err(error) = self.persist_character_world_state("unsafe local spawn repair") {
                self.log.event(&format!("Spawn repair persistence failed: {error}"));
            }
            return;
        }

        // An irregular coastline can make the entire legacy harbor storage
        // partition marine water. In that case searching only the active 64x64
        // scene can never recover. Search the already-loaded partitions in the
        // same continuous PCG surface and relocate to the nearest stable dry
        // scene-local cell. This performs no disk I/O or PCG work; all candidate
        // scene maps are already resident from the saved/generated world.
        let Some((scene_id, safe_x, safe_y, safe_global)) =
            self.nearest_safe_loaded_surface_spawn(current_global)
        else {
            self.log.event(
                "Exterior spawn repair could not find dry walkable ground in the loaded surface",
            );
            return;
        };
        if self.world.active_scene.project_id() != &scene_id {
            if let Err(error) = self
                .world
                .set_active_scene(SceneReference::from(scene_id.clone()))
            {
                self.log.event(&format!(
                    "Exterior spawn repair could not activate safe scene {}: {error}",
                    scene_id
                ));
                return;
            }
        }
        self.player = vec2(
            safe_x as f32 * TILE_SIZE + TILE_SIZE * 0.5,
            safe_y as f32 * TILE_SIZE + TILE_SIZE * 0.5,
        );
        self.camera_target = self.local_world_to_runtime_world(self.player);
        self.selected_cell = (safe_x, safe_y);
        self.inspector = inspect_scene_cell(self.world.active(), safe_x, safe_y);
        self.character_world_link.world_scene = scene_id.code().to_string();
        self.character_world_link.world_position = [safe_global.x, safe_global.y];
        self.status_message = format!(
            "Unsafe marine spawn relocated to dry mainland tile {},{} in {}",
            safe_global.x, safe_global.y, scene_id
        );
        self.log.event(&self.status_message);
        if let Err(error) = self.persist_character_world_state("unsafe cross-partition spawn repair") {
            self.log.event(&format!("Spawn repair persistence failed: {error}"));
        }
    }

    fn nearest_safe_loaded_surface_spawn(
        &self,
        current_global: haven_world::open_world::WorldTileCoord,
    ) -> Option<(
        ProjectSceneId,
        i32,
        i32,
        haven_world::open_world::WorldTileCoord,
    )> {
        let manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
        let mut best: Option<(
            (i32, i32, i32),
            ProjectSceneId,
            i32,
            i32,
            haven_world::open_world::WorldTileCoord,
        )> = None;

        for binding in &manifest.exterior_bindings {
            let Some(scene) = self.world.scene_by_id(&binding.scene_id) else {
                continue;
            };
            let Some((local_x, local_y)) = haven_world::nearest_stable_walkable_cell(scene) else {
                continue;
            };
            let tile = scene.map.get(local_x, local_y);
            if tile.is_water() || !scene.is_cell_walkable(local_x, local_y) {
                continue;
            }
            let global = haven_world::surface_global_tile(binding.chunk, local_x, local_y);
            if self.structural_cliff_face_occupies_tile(global) {
                continue;
            }
            if self
                .surface_structural_at_global_in_manifest(&manifest, global.x, global.y)
                .is_some_and(|cell| !cell.blocked_edges.is_empty())
            {
                continue;
            }

            let distance = (global.x - current_global.x)
                .abs()
                .max((global.y - current_global.y).abs());
            let terrain_preference = match tile {
                TileKind::Grass | TileKind::TallGrass | TileKind::Road | TileKind::StonePath => 0,
                TileKind::Sand | TileKind::WetSand | TileKind::MountainPath => 1,
                _ => 2,
            };
            let center_preference = (local_x - MAP_W as i32 / 2)
                .abs()
                .max((local_y - MAP_H as i32 / 2).abs());
            let score = (distance, terrain_preference, center_preference);
            if best
                .as_ref()
                .is_none_or(|(best_score, ..)| score < *best_score)
            {
                best = Some((
                    score,
                    binding.scene_id.clone(),
                    local_x,
                    local_y,
                    global,
                ));
            }
        }

        best.map(|(_, scene_id, local_x, local_y, global)| {
            (scene_id, local_x, local_y, global)
        })
    }

    pub(super) fn persist_character_world_state(&mut self, reason: &str) -> Result<(), String> {
        self.character_world_link.world_id = self.world_id.clone();
        self.character_world_link.character_id = self.character_id.clone();
        self.character_world_link.world_scene = self.world.active_scene.code().to_string();
        self.synchronize_surface_position();
        self.character_world_link.world_position =
            if self.world.active().kind == SceneKind::Exterior {
                {
                    let tile = self.surface_global_tile();
                    [tile.x, tile.y]
                }
            } else {
                [
                    (self.player.x / TILE_SIZE).floor() as i32,
                    (self.player.y / TILE_SIZE).floor() as i32,
                ]
            };
        self.character_world_link
            .world_reputation
            .insert("global".to_string(), self.reputation);
        // World-local relationships and quest flags remain authoritative in this link
        // and round-trip unchanged until their gameplay systems mutate them.
        let _preserved_world_relationships = self.character_world_link.world_relationships.len();
        let _preserved_world_quest_flags = self.character_world_link.world_quest_flags.len();
        self.character_world_link.touch();
        save_character_world_link(Path::new(&self.save_paths.root), &self.character_world_link)?;
        self.log.event(&format!(
            "Character-world state saved ({reason}): {} @ {} [{}, {}]",
            self.character_id.0,
            self.character_world_link.world_scene,
            self.character_world_link.world_position[0],
            self.character_world_link.world_position[1]
        ));
        Ok(())
    }

    pub(super) fn reload_character_world_state(&mut self) {
        match haven_save::load_character_world_link(
            Path::new(&self.save_paths.root),
            &self.character_id,
        ) {
            Ok(link) => {
                self.character_world_link = link;
                if let Some(status) =
                    Self::restore_character_world_link(&mut self.world, &self.character_world_link)
                {
                    self.log.event(&status);
                }
                let spawn = self.world.active();
                self.player = Self::character_world_position_or_spawn(
                    &self.character_world_link,
                    spawn.spawn_x,
                    spawn.spawn_y,
                );
                self.camera_target = self.local_world_to_runtime_world(self.player);
                self.reputation = self
                    .character_world_link
                    .world_reputation
                    .get("global")
                    .copied()
                    .unwrap_or(1);
            }
            Err(error) => self.log.event(&format!(
                "Character-world state load skipped for {}: {error}",
                self.character_id.0
            )),
        }
    }
}
