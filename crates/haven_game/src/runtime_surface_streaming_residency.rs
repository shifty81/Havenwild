impl Game {
    /// H21A14AB3: Development/open-world startup must never synchronously rebake
    /// every loaded exterior partition before the first interactive frame.
    /// Streamed surfaces already have bounded background hydrology/structural
    /// workers, so prime that local residency authority and let normal frame
    /// maintenance publish only the nearby caches. Legacy/non-streamed exterior
    /// scenes retain the synchronous compatibility rebuild.
    pub(super) fn prepare_initial_surface_structures(&mut self) {
        if self.active_surface_chunk_coord().is_some() {
            self.surface_chunks.structural_rebuild_needed = true;
            self.surface_chunks.last_active_chunk = None;
            self.surface_chunks.last_hydrology_signature = None;
            self.surface_chunks.next_maintenance_at = 0.0;
            self.log.event(
                "Startup surface authority queued through bounded residency workers; full-world synchronous structural bake skipped",
            );
            // This call only snapshots/queues the bounded preload neighborhood.
            // Hydrology and structural solves themselves remain worker-backed.
            self.update_surface_chunk_jobs();
        } else {
            if self.world.active().kind == SceneKind::Exterior {
                self.log.event(
                    "Bounded exterior instance active: retained scene terrain + local structural cache; continuous surface streaming disabled",
                );
            }
            self.rebuild_active_surface_structures();
        }
    }

    pub(super) fn surface_runtime_state(&self) -> haven_world::SurfaceRuntimeState {
        let local = WorldTileCoord::new(
            (self.player.x / TILE_SIZE).floor() as i32,
            (self.player.y / TILE_SIZE).floor() as i32,
        );
        haven_world::SurfaceRuntimeState::for_world(&self.world, local)
    }

    pub(super) fn surface_global_tile(&self) -> WorldTileCoord {
        self.surface_runtime_state().global_tile
    }

    pub(super) fn active_surface_chunk_coord(&self) -> Option<ChunkCoord> {
        if !haven_world::scene_is_surface_chunk(self.world.active()) {
            return None;
        }
        let active_scene_id = self.world.active_scene.project_id();
        haven_world::ContinuousSurfaceManifest::for_world(&self.world)
            .chunk_for_scene(active_scene_id)
    }

    pub(super) fn active_surface_origin_px(&self) -> Vec2 {
        let Some(chunk) = self.active_surface_chunk_coord() else {
            return Vec2::ZERO;
        };
        vec2(
            chunk.x as f32 * MAP_W as f32 * TILE_SIZE,
            chunk.y as f32 * MAP_H as f32 * TILE_SIZE,
        )
    }

    pub(super) fn surface_cell_target_at_runtime_world(
        &self,
        runtime_world: Vec2,
    ) -> Option<SurfaceCellTarget> {
        if self.active_surface_chunk_coord().is_none() {
            let local_x = (runtime_world.x / TILE_SIZE).floor() as i32;
            let local_y = (runtime_world.y / TILE_SIZE).floor() as i32;
            TavernMap::idx(local_x, local_y)?;
            return Some(SurfaceCellTarget {
                scene_id: self.world.active_scene.project_id().clone(),
                chunk: ChunkCoord::new(0, 0),
                local_x,
                local_y,
                global_x: local_x,
                global_y: local_y,
            });
        }

        let global_x = (runtime_world.x / TILE_SIZE).floor() as i32;
        let global_y = (runtime_world.y / TILE_SIZE).floor() as i32;
        let canonical = self
            .world_topology
            .canonical_tile(WorldTileCoord::new(global_x, global_y))?;
        let address = haven_world::surface_tile_address(canonical);
        let manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
        let scene_id = manifest.scene_id_for_chunk(address.chunk);
        self.world.scene_by_id(&scene_id)?;
        Some(SurfaceCellTarget {
            scene_id,
            chunk: address.chunk,
            local_x: address.local_x,
            local_y: address.local_y,
            global_x: canonical.x,
            global_y: canonical.y,
        })
    }

    pub(super) fn surface_cell_target_at_screen(&self, screen: Vec2) -> Option<SurfaceCellTarget> {
        let visible = vec2(screen_width(), screen_height());
        let runtime_world = (screen - visible * 0.5) / self.camera_zoom + self.camera_target;
        self.surface_cell_target_at_runtime_world(runtime_world)
    }

    pub(super) fn surface_cell_screen_origin(&self, target: &SurfaceCellTarget) -> Vec2 {
        if self.active_surface_chunk_coord().is_some() {
            self.runtime_world_to_screen(vec2(
                target.global_x as f32 * TILE_SIZE,
                target.global_y as f32 * TILE_SIZE,
            ))
        } else {
            self.world_to_screen(vec2(
                target.local_x as f32 * TILE_SIZE,
                target.local_y as f32 * TILE_SIZE,
            ))
        }
    }

    pub(super) fn local_world_to_runtime_world(&self, local: Vec2) -> Vec2 {
        if self.active_surface_chunk_coord().is_some() {
            self.active_surface_origin_px() + local
        } else {
            local
        }
    }

    pub(super) fn runtime_world_to_active_local(&self, runtime_world: Vec2) -> Vec2 {
        if self.active_surface_chunk_coord().is_some() {
            runtime_world - self.active_surface_origin_px()
        } else {
            runtime_world
        }
    }

    pub(super) fn active_local_camera_target(&self) -> Vec2 {
        self.runtime_world_to_active_local(self.camera_target)
    }

    pub(super) fn synchronize_surface_position(&mut self) {
        if self.active_surface_chunk_coord().is_some() {
            let _ = self.surface_global_tile();
        }
    }

    pub(super) fn update_surface_chunk_jobs(&mut self) {
        if self.active_surface_chunk_coord().is_none() {
            return;
        }
        let frame_started = get_time();

        // Completed disk writes are acknowledged without making the movement
        // frame perform filesystem I/O itself.
        for result in self.surface_chunks.persistence.drain() {
            if !result.ok { continue; }
            match result.kind {
                SurfacePersistenceKind::Baseline => self.surface_chunks.cache_writes += 1,
                SurfacePersistenceKind::Delta => self.surface_chunks.delta_writes += 1,
                SurfacePersistenceKind::Bytes => {}
            }
        }

        let mut structural_sources_changed = false;
        let publish_deadline = frame_started + SURFACE_PUBLISH_BUDGET_SECONDS;
        let mut integrated = 0usize;
        while integrated < SURFACE_MAX_PUBLISH_PER_FRAME && get_time() <= publish_deadline {
            let Some(result) = self.surface_chunks.jobs.try_receive() else { break; };
            let scene_id = result.scene.id.clone();
            if self.world.scene_by_id(&scene_id).is_none() {
                if !result.loaded_from_cache {
                    if result.baseline_persisted {
                        self.surface_chunks.cache_writes =
                            self.surface_chunks.cache_writes.saturating_add(1);
                    } else {
                        // Exceptional durability fallback only. Normal virgin
                        // exploration persists on the worker without cloning; if
                        // that write failed, retain the old async baseline path
                        // rather than silently losing the generated partition.
                        let _ = self.surface_chunks.persistence.send(
                            SurfacePersistenceRequest::Baseline {
                                root: self.save_paths.chunks_root.clone(),
                                chunk: result.request.chunk,
                                scene: result.scene.clone(),
                            },
                        );
                    }
                }
                let _ = self.world.insert_scene(result.scene);
                structural_sources_changed = true;
                self.surface_chunks.structural_rebuild_needed = true;
            }
            integrated += 1;
        }

        // Publish hydrology only if it still belongs to the newest requested
        // residency generation. Worker completion is queued first; only a small
        // number of partition maps are copied into live scenes per frame.
        if self.surface_chunks.pending_hydrology_publish.is_empty() {
            if let Some(result) = self.surface_chunks.hydrology_jobs.try_receive() {
                if result.token == self.surface_chunks.latest_hydrology_token {
                    self.surface_chunks.hydrology_reconciles += 1;
                    if result.applied_cells > 0 {
                        self.surface_chunks.pending_hydrology_publish.extend(
                            result.scene_ids.into_iter().zip(result.chunks).map(
                                |((coord, scene_id), map)| (coord, scene_id, map),
                            ),
                        );
                    }
                }
            }
        }

        let mut hydrology_published = 0usize;
        while hydrology_published < SURFACE_MAX_PUBLISH_PER_FRAME && get_time() <= publish_deadline {
            let Some((_coord, scene_id, map)) =
                self.surface_chunks.pending_hydrology_publish.pop_front()
            else {
                break;
            };
            let Some(scene) = self.world.scene_mut_by_id(&scene_id) else {
                continue;
            };
            scene.map = map;
            // AC2: hydrology is deterministic and is reconciled again whenever
            // the centered residency window changes. Do not clone the complete
            // live SceneMap on the movement thread merely to refresh a cache
            // baseline; the first baseline is already persisted by the prepare
            // worker and player deltas remain independently authoritative.
            hydrology_published += 1;
        }
        if hydrology_published > 0 && self.surface_chunks.pending_hydrology_publish.is_empty() {
            // Structural solve waits until the whole reconciled hydrology window
            // is visible, never against a half-published river/waterfall path.
            structural_sources_changed = true;
            self.surface_chunks.structural_rebuild_needed = true;
        }

        if self.surface_chunks.pending_structural_publish.is_empty() {
            if let Some(result) = self.surface_chunks.structural_jobs.try_receive() {
                if result.token == self.surface_chunks.latest_structural_token {
                    match result.bake {
                        Ok(bake) => {
                            // Publish normalized levels only as part of the same
                            // successful structural transaction as the derived
                            // cliff cache. A failed bake must never leave live
                            // maps normalized against an older cache.
                            self.surface_chunks
                                .pending_structural_levels_publish
                                .extend(result.normalized_levels);
                            self.surface_chunks.pending_structural_report = Some(bake.report);
                            self.surface_chunks.pending_structural_publish.extend(bake.chunks);
                        }
                        Err(error) => {
                            self.surface_chunks.pending_structural_report = None;
                            self.log.event(&format!(
                                "Background structural surface rebuild failed: {error}"
                            ));
                        }
                    }
                }
            }
        }

        let mut structural_levels_published = 0usize;
        if !self.surface_chunks.pending_structural_levels_publish.is_empty() {
            let manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
            while structural_levels_published < 2 && get_time() <= publish_deadline {
                let Some((chunk, levels)) =
                    self.surface_chunks.pending_structural_levels_publish.pop_front()
                else {
                    break;
                };
                let scene_id = manifest.scene_id_for_chunk(chunk);
                let Some(scene) = self.world.scene_mut_by_id(&scene_id) else {
                    continue;
                };
                if scene.map.structural_levels != levels {
                    scene.map.structural_levels = levels;
                }
                structural_levels_published += 1;
            }
        }

        let mut structural_published = 0usize;
        if !self.surface_chunks.pending_structural_publish.is_empty() {
            let manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
            while structural_published < SURFACE_MAX_PUBLISH_PER_FRAME && get_time() <= publish_deadline {
                let Some(chunk_cache) = self.surface_chunks.pending_structural_publish.pop_front()
                else {
                    break;
                };
                let chunk = ChunkCoord::new(chunk_cache.chunk_x, chunk_cache.chunk_y);
                let Some(binding) = manifest.binding_for_chunk(chunk) else {
                    continue;
                };
                let Some(report) = self.surface_chunks.pending_structural_report.as_ref() else {
                    continue;
                };
                self.surface_chunks.structural_cache.insert(
                    binding.scene_id.as_str().to_owned(),
                    haven_world::LegacyCliffBridgeResultV2 {
                        schema: haven_world::LEGACY_CLIFF_BRIDGE_V2_SCHEMA.to_owned(),
                        width: chunk_cache.width,
                        height: chunk_cache.height,
                        structural_cells: chunk_cache.cells,
                        report: report.clone(),
                    },
                );
                structural_published += 1;
            }
        }
        if (structural_published > 0 || structural_levels_published > 0)
            && self.surface_chunks.pending_structural_report.is_some()
            && self.surface_chunks.pending_structural_publish.is_empty()
            && self.surface_chunks.pending_structural_levels_publish.is_empty()
        {
            self.surface_chunks.pending_structural_report = None;
            let manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
            self.rebuild_authored_ramp_owner_cache(&manifest);
            self.surface_chunks.structural_rebuilds += 1;
        }

        let state = self.surface_runtime_state();
        let active_key = (state.active_chunk.x, state.active_chunk.y);
        let now = get_time();
        let active_changed = self.surface_chunks.last_active_chunk != Some(active_key);
        if !surface_maintenance_due(now, self.surface_chunks.next_maintenance_at, active_changed) {
            self.surface_chunks.last_stream_cost_ms = (get_time() - frame_started) * 1000.0;
            return;
        }
        self.surface_chunks.last_active_chunk = Some(active_key);
        self.surface_chunks.next_maintenance_at = now + SURFACE_MAINTENANCE_INTERVAL_SECONDS;
        if active_changed {
            self.surface_chunks.streaming_generation =
                self.surface_chunks.streaming_generation.wrapping_add(1);
        }

        if !self.surface_chunks.pins_initialized {
            self.surface_chunks.pinned_surface_scenes = self
                .world
                .scenes
                .iter()
                .filter(|scene| {
                    scene.kind == SceneKind::Exterior
                        && parse_pcg_surface_scene_id(&scene.id).is_some()
                })
                .map(|scene| scene.id.as_str().to_owned())
                .collect();
            self.surface_chunks.pins_initialized = true;
        }

        let residency = SurfaceResidencyWindow::refresh(
            state.active_chunk,
            state.manifest.active_radius_chunks,
            state.manifest.preload_radius_chunks,
            self.world_seed,
        );
        let mut valid_preload = residency
            .preload
            .iter()
            .filter_map(|(x, y)| {
                self.world_topology
                    .canonical_chunk(ChunkCoord::new(*x, *y))
                    .map(|chunk| (chunk.x, chunk.y))
            })
            .collect::<BTreeSet<_>>();
        let hydrology_preload = valid_preload.clone();

        // AC2 predictive residency: prepare a small movement-facing wedge well
        // before the player reaches the centered preload boundary. The old
        // single extra cell routinely let generation finish only as the player
        // approached virgin terrain. The centered set remains the hydrology/
        // structural authority so prediction does not multiply expensive solves.
        let movement = self.controls.movement_vector();
        let bias_x = if movement.x > 0.2 { 1 } else if movement.x < -0.2 { -1 } else { 0 };
        let bias_y = if movement.y > 0.2 { 1 } else if movement.y < -0.2 { -1 } else { 0 };
        if bias_x != 0 || bias_y != 0 {
            let base_radius = state.manifest.preload_radius_chunks as i32;
            let side_x = -bias_y;
            let side_y = bias_x;
            for lookahead in 1..=3_i32 {
                let distance = base_radius + lookahead;
                for lateral in -1..=1_i32 {
                    // Keep the farthest prediction narrow; nearer rows can
                    // prepare the likely diagonal neighbors as well.
                    if lookahead == 3 && lateral != 0 {
                        continue;
                    }
                    let predicted = ChunkCoord::new(
                        state.active_chunk.x + bias_x * distance + side_x * lateral,
                        state.active_chunk.y + bias_y * distance + side_y * lateral,
                    );
                    if let Some(chunk) = self.world_topology.canonical_chunk(predicted) {
                        valid_preload.insert((chunk.x, chunk.y));
                    }
                }
            }
        }

        let active_pcg_region = parse_pcg_surface_scene_id(self.world.active_scene.project_id())
            .map(|(region, _)| region);
        let profile = GeographicGenerationProfile::from_world_creation(&self.world_creation_settings);
        for &(x, y) in &valid_preload {
            let chunk = ChunkCoord::new(x, y);
            let scene_id = state.manifest.scene_id_for_chunk(chunk);
            if self.world.scene_by_id(&scene_id).is_some() { continue; }
            let pcg_region = active_pcg_region
                .as_deref()
                .filter(|_| state.manifest.binding_for_chunk(chunk).is_none());
            self.surface_chunks.jobs.request(
                self.world_seed,
                chunk,
                profile,
                pcg_region,
                scene_id,
                &self.save_paths.chunks_root,
            );
        }

        let refreshed_manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
        let loaded_count = hydrology_preload.iter().filter(|(x, y)| {
            let scene_id = refreshed_manifest.scene_id_for_chunk(ChunkCoord::new(*x, *y));
            self.world.scene_by_id(&scene_id).is_some()
        }).count();
        let hydrology_signature = HydrologyResidencySignature {
            active_x: state.active_chunk.x,
            active_y: state.active_chunk.y,
            preload_count: hydrology_preload.len(),
            loaded_count,
        };
        if self.surface_chunks.last_hydrology_signature != Some(hydrology_signature)
            && loaded_count == hydrology_preload.len()
            && self.request_loaded_surface_hydrology(&hydrology_preload)
        {
            self.surface_chunks.last_hydrology_signature = Some(hydrology_signature);
        }

        self.evict_distant_generated_surface_chunks(&valid_preload);
        if structural_sources_changed {
            self.surface_chunks.structural_rebuild_needed = true;
        }
        if self.surface_chunks.structural_rebuild_needed {
            if self.request_local_surface_structural_rebuild(&hydrology_preload) {
                self.surface_chunks.structural_rebuild_needed = false;
            }
        } else if active_changed && !self.surface_chunks.structural_jobs.pending() {
            let _ = self.request_local_surface_structural_rebuild(&hydrology_preload);
        }

        // Discovery calculation remains local, but the JSON write itself is
        // queued to the background persistence worker.
        self.capture_active_world_map_chunk_if_moved();
        self.surface_chunks.last_stream_cost_ms = (get_time() - frame_started) * 1000.0;
    }

    /// Reconciles the complete loaded preload rectangle as one hydrology grid.
    ///
    /// This runs only when every chunk in the requested residency window is
    /// available. Missing streamed neighbors are never treated as dry land.
    /// Player-delta snapshots remain authoritative; only unedited baseline
    /// caches are refreshed after reconciliation.
    fn request_loaded_surface_hydrology(&mut self, preload: &BTreeSet<(i32, i32)>) -> bool {
        if self.surface_chunks.hydrology_jobs.pending()
            || !self.surface_chunks.pending_hydrology_publish.is_empty()
        {
            return false;
        }
        let Some(min_x) = preload.iter().map(|(x, _)| *x).min() else { return false; };
        let Some(max_x) = preload.iter().map(|(x, _)| *x).max() else { return false; };
        let Some(min_y) = preload.iter().map(|(_, y)| *y).min() else { return false; };
        let Some(max_y) = preload.iter().map(|(_, y)| *y).max() else { return false; };
        let width_chunks = (max_x - min_x + 1) as usize;
        let height_chunks = (max_y - min_y + 1) as usize;
        if width_chunks.saturating_mul(height_chunks) != preload.len() { return false; }

        let manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
        let mut chunks = Vec::with_capacity(preload.len());
        let mut scene_ids = Vec::with_capacity(preload.len());
        for y in min_y..=max_y {
            for x in min_x..=max_x {
                let coord = ChunkCoord::new(x, y);
                let scene_id = manifest.scene_id_for_chunk(coord);
                let Some(scene) = self.world.scene_by_id(&scene_id) else { return false; };
                chunks.push(scene.map.clone());
                scene_ids.push((coord, scene_id));
            }
        }
        let token = self.surface_chunks.streaming_generation.wrapping_add(1);
        self.surface_chunks.latest_hydrology_token = token;
        self.surface_chunks.hydrology_jobs.request(HydrologyJobRequest {
            token,
            scene_ids,
            window: ChunkHydrologyWindowV2 {
                origin_chunk_x: min_x,
                origin_chunk_y: min_y,
                width_chunks,
                height_chunks,
                wraps_complete_world_width: false,
                chunks,
            },
        })
    }

    fn evict_distant_generated_surface_chunks(&mut self, preload: &BTreeSet<(i32, i32)>) {
        let active_id = self.world.active_scene.project_id().clone();
        let removable = self
            .world
            .scenes
            .iter()
            .filter_map(|scene| {
                let chunk = parse_generated_chunk_scene_id(&scene.id)
                    .or_else(|| parse_pcg_surface_scene_id(&scene.id).map(|(_, chunk)| chunk))?;
                if scene.id == active_id
                    || preload.contains(&(chunk.x, chunk.y))
                    || self
                        .surface_chunks
                        .pinned_surface_scenes
                        .contains(scene.id.as_str())
                {
                    None
                } else {
                    Some(scene.id.clone())
                }
            })
            .collect::<Vec<_>>();
        for id in removable {
            self.surface_chunks.structural_cache.remove(id.as_str());
            let _ = self.world.remove_scene(&id);
        }
    }

    fn persist_active_generated_chunk_delta(&mut self) {
        let scene_id = self.world.active_scene.project_id();
        let Some(chunk) = parse_generated_chunk_scene_id(scene_id)
            .or_else(|| parse_pcg_surface_scene_id(scene_id).map(|(_, chunk)| chunk))
        else { return; };
        let _ = self.surface_chunks.persistence.send(SurfacePersistenceRequest::Delta {
            root: self.save_paths.chunks_root.clone(),
            chunk,
            scene: self.world.active().clone(),
        });
    }

    pub(super) fn try_stream_exterior_position(&mut self, candidate: Vec2) -> Option<Vec2> {
        if self.world.active().kind != SceneKind::Exterior {
            return Some(candidate);
        }
        if self.active_surface_chunk_coord().is_none() {
            let dimensions = self.world.active().dimensions;
            let width_px = dimensions.width as f32 * TILE_SIZE;
            let height_px = dimensions.height as f32 * TILE_SIZE;
            if candidate.x < 0.0
                || candidate.y < 0.0
                || candidate.x >= width_px
                || candidate.y >= height_px
            {
                // Home Estate and other bounded exterior instances have real
                // scene edges. Leaving them requires an authored transition
                // (Estate gateway/cave), never implicit surface streaming.
                return None;
            }
            return Some(candidate);
        }
        let width_px = MAP_W as f32 * TILE_SIZE;
        let height_px = MAP_H as f32 * TILE_SIZE;
        let mut chunk_delta = ChunkCoord::new(0, 0);
        let mut local = candidate;
        if local.x < 0.0 { chunk_delta.x = -1; local.x += width_px; }
        else if local.x >= width_px { chunk_delta.x = 1; local.x -= width_px; }
        if local.y < 0.0 { chunk_delta.y = -1; local.y += height_px; }
        else if local.y >= height_px { chunk_delta.y = 1; local.y -= height_px; }
        if chunk_delta == ChunkCoord::new(0, 0) { return Some(local); }

        let state = self.surface_runtime_state();
        let requested_target_chunk = ChunkCoord::new(
            state.active_chunk.x + chunk_delta.x,
            state.active_chunk.y + chunk_delta.y,
        );
        let target_chunk = self.world_topology.canonical_chunk(requested_target_chunk)?;
        let target_scene_id = state.manifest.scene_id_for_chunk(target_chunk);
        let target_scene = SceneReference::new(target_scene_id.clone());

        // H20 fail-closed boundary: crossing never performs cache reads, PCG,
        // hydrology, structural solving, or disk writes synchronously. If the
        // partition is not ready yet, request it and keep the player on the last
        // safe cell for this frame.
        if self.world.scene_by_reference(&target_scene).is_none() {
            let active_pcg_region = parse_pcg_surface_scene_id(self.world.active_scene.project_id())
                .map(|(region, _)| region);
            let pcg_region = active_pcg_region
                .as_deref()
                .filter(|_| state.manifest.binding_for_chunk(target_chunk).is_none());
            let profile = GeographicGenerationProfile::from_world_creation(&self.world_creation_settings);
            self.surface_chunks.jobs.request(
                self.world_seed,
                target_chunk,
                profile,
                pcg_region,
                target_scene_id,
                &self.save_paths.chunks_root,
            );
            return None;
        }

        let target = self.world.scene_by_reference(&target_scene)?;
        if target.kind != SceneKind::Exterior { return None; }
        let tile_x = (local.x / TILE_SIZE).floor() as i32;
        let tile_y = (local.y / TILE_SIZE).floor() as i32;
        if !target.map.is_cell_walkable(tile_x, tile_y) { return None; }
        if self.world.set_active_scene(target_scene).is_err() { return None; }

        self.terrain_cache = LiveAutotileCache::new(self.world.active());
        self.terrain_cache.synchronize(self.world.active());
        self.refresh_world_paint_render_bindings_for_active_scene(
            "Surface chunk render binding refresh",
        );
        self.surface_chunks.last_active_chunk = None;
        let tree_count = self
            .world
            .active()
            .map
            .objects
            .iter()
            .filter(|object| object.kind == ObjectKind::Tree)
            .count();
        self.status_message = format!(
            "Crossed surface {},{} | trees {} | prepare {} | persist {} | hydro {} | structural {} | stream {:.2} ms",
            target_chunk.x,
            target_chunk.y,
            tree_count,
            self.surface_chunks.jobs.pending_count(),
            self.surface_chunks.persistence.pending_count(),
            usize::from(self.surface_chunks.hydrology_jobs.pending()),
            usize::from(self.surface_chunks.structural_jobs.pending()),
            self.surface_chunks.last_stream_cost_ms,
        );
        self.log.event(&self.status_message);
        Some(local)
    }
}

