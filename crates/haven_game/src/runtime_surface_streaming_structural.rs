impl Game {
    /// Rebuilds the active exterior region as one structural elevation grid.
    /// PCG partitions are storage only, so cliff edges at partition borders
    /// must resolve against the neighboring partition before rendering or
    /// movement queries consume them.
    pub(super) fn rebuild_active_surface_structures(&mut self) {
        if self.world.active().kind != SceneKind::Exterior {
            return;
        }
        let manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
        let mut partitions = if self.active_surface_chunk_coord().is_none() {
            // H21A14AB8: the Home Estate is a bounded exterior world instance,
            // not chunk 0,0 of the shared overworld. Keep the historical
            // Farmstead binding only as a structural-coordinate compatibility
            // adapter, but never pull NorthRoad/SouthField/EastWoods into an
            // Estate startup bake.
            vec![(ChunkCoord::new(0, 0), self.world.active().map.clone())]
        } else {
            manifest
                .exterior_bindings
                .iter()
                .filter_map(|binding| {
                    self.world
                        .scene_by_id(&binding.scene_id)
                        .map(|scene| (binding.chunk, scene.map.clone()))
                })
                .collect::<Vec<_>>()
        };
        if partitions.is_empty() {
            return;
        }
        let normalization = haven_world::normalize_partitioned_structural_elevation_v1(
            &mut partitions,
        );
        self.publish_normalized_structural_levels(&manifest, &partitions);
        match haven_world::bake_partitioned_surface_structural_terrain_v2(
            &partitions,
            false,
            haven_world::ElevationCliffSettingsV2::default(),
        ) {
            Ok(bake) => {
                self.surface_chunks.structural_cache.clear();
                for chunk_cache in bake.chunks {
                    let chunk = ChunkCoord::new(chunk_cache.chunk_x, chunk_cache.chunk_y);
                    let Some(binding) = manifest.binding_for_chunk(chunk) else {
                        continue;
                    };
                    self.surface_chunks.structural_cache.insert(
                        binding.scene_id.as_str().to_owned(),
                        haven_world::LegacyCliffBridgeResultV2 {
                            schema: haven_world::LEGACY_CLIFF_BRIDGE_V2_SCHEMA.to_owned(),
                            width: chunk_cache.width,
                            height: chunk_cache.height,
                            structural_cells: chunk_cache.cells,
                            report: bake.report.clone(),
                        },
                    );
                }
                self.rebuild_authored_ramp_owner_cache(&manifest);
                self.surface_chunks.structural_rebuilds += 1;
                self.log.event(&format!(
                    "Structural surface rebuilt: {} partition cache(s), {} cliff edge(s), {} gentle ramp(s), {} authored connector ramp footprint cell(s) | H20S promote {} legacy rock + {} Level-1 cell(s), collapse {} relief cell(s), certify {} ramp(s)",
                    self.surface_chunks.structural_cache.len(),
                    bake.report.cliff_edges,
                    bake.report.ramps,
                    self.surface_chunks.authored_ramp_owner_by_cell.len(),
                    normalization.promoted_legacy_mountainrock,
                    normalization.promoted_level_one_cells,
                    normalization.collapsed_level_one_cells,
                    normalization.certified_ramps,
                ));
            }
            Err(error) => self
                .log
                .event(&format!("Structural surface rebuild failed: {error}")),
        }
    }

    /// Mirror only normalized structural-level metadata back into the live
    /// scenes. Terrain tiles, objects, authored overrides, and hydrology are
    /// untouched. This makes legacy-save migration persistent and keeps
    /// renderer/collision/map/editor consumers on the same structural levels.
    fn publish_normalized_structural_levels(
        &mut self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        partitions: &[(ChunkCoord, haven_core::TavernMap)],
    ) {
        for (chunk, map) in partitions {
            let Some(binding) = manifest.binding_for_chunk(*chunk) else {
                continue;
            };
            let Some(scene) = self.world.scene_mut_by_id(&binding.scene_id) else {
                continue;
            };
            if scene.map.structural_levels != map.structural_levels {
                scene.map.structural_levels.clone_from(&map.structural_levels);
            }
        }
    }

    /// Rebuild the world-space semantic traversal footprint for authored LPC
    /// 3x4 connector ramps. The artwork is wider than its walkable MountainPath
    /// corridor; only the six certified 2->1->0 path cells suppress ordinary
    /// cliff ownership. Claiming the full art rectangle creates the hard vertical
    /// cliff cutoffs seen beside ramps.
    fn rebuild_authored_ramp_owner_cache(
        &mut self,
        manifest: &haven_world::ContinuousSurfaceManifest,
    ) {
        use haven_world::CardinalDirectionV2;

        let mut owner_by_cell = BTreeMap::new();
        for binding in &manifest.exterior_bindings {
            // H21A14AB4: the structural worker only bakes the bounded residency
            // window, so ramp ownership must be rebuilt from that same cache.
            // Scanning every materialized exterior partition here can freeze a
            // large development world immediately after the first frame.
            if !self
                .surface_chunks
                .structural_cache
                .contains_key(binding.scene_id.as_str())
            {
                continue;
            }
            let Some(scene) = self.world.scene_by_id(&binding.scene_id) else {
                continue;
            };
            let origin_x = binding.chunk.x * MAP_W as i32;
            let origin_y = binding.chunk.y * MAP_H as i32;
            for local_y in 0..MAP_H as i32 {
                for local_x in 0..MAP_W as i32 {
                    if scene.map.get(local_x, local_y) != TileKind::MountainPath {
                        continue;
                    }
                    let global_x = origin_x + local_x;
                    let global_y = origin_y + local_y;
                    let Some(role) = self.complete_directional_ramp_role_for_host(
                        manifest, global_x, global_y,
                    ) else {
                        continue;
                    };
                    if self.structural_connector_from_host_edge_in_manifest(
                        manifest,
                        global_x,
                        global_y,
                        CardinalDirectionV2::South,
                    ) != Some(crate::runtime_structural_connectors::StructuralConnectorKind::Ramp)
                    {
                        continue;
                    }

                    let corridor: &[(i32, i32)] = match role {
                        haven_assets::lpc_cliff_ramp_provider::LpcDirectionalCliffRampRole::RiseRight => {
                            &[(1, -1), (1, 0), (0, 0), (0, 1), (-1, 1), (-1, 2)]
                        }
                        haven_assets::lpc_cliff_ramp_provider::LpcDirectionalCliffRampRole::RiseLeft => {
                            &[(-1, -1), (-1, 0), (0, 0), (0, 1), (1, 1), (1, 2)]
                        }
                    };
                    for (dx, dy) in corridor {
                        owner_by_cell
                            .entry((global_x + dx, global_y + dy))
                            .or_insert((global_x, global_y));
                    }

                }
            }
        }
        self.surface_chunks.authored_ramp_owner_by_cell = owner_by_cell;
    }

    pub(super) fn surface_authored_ramp_owner(
        &self,
        global_x: i32,
        global_y: i32,
    ) -> Option<(i32, i32)> {
        self.surface_chunks
            .authored_ramp_owner_by_cell
            .get(&(global_x, global_y))
            .copied()
    }

    pub(super) fn surface_structural_cell(
        &self,
        scene_id: &haven_core::ProjectSceneId,
        local_x: i32,
        local_y: i32,
    ) -> Option<haven_world::StructuralCellV2> {
        self.surface_chunks
            .structural_cache
            .get(scene_id.as_str())
            .and_then(|cache| cache.structural_at(local_x, local_y))
    }

    /// Canonical semantic/structural recipe for one loaded surface cell.
    /// Rendering/map/editor consumers may use this bridge without inferring
    /// structural level or map semantics from raw visual tiles.
    pub(super) fn surface_terrain_recipe_cell(
        &self,
        scene_id: &haven_core::ProjectSceneId,
        local_x: i32,
        local_y: i32,
    ) -> Option<haven_world::SurfaceTerrainRecipeV1> {
        let scene = self.world.scene_by_id(scene_id)?;
        let structural = self.surface_structural_cell(scene_id, local_x, local_y);
        haven_world::resolve_surface_terrain_recipe_v1(
            &scene.map,
            scene.biome,
            local_x,
            local_y,
            structural,
        )
    }

    pub(super) fn surface_structural_at_global(
        &self,
        global_x: i32,
        global_y: i32,
    ) -> Option<haven_world::StructuralCellV2> {
        let manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
        self.surface_structural_at_global_in_manifest(&manifest, global_x, global_y)
    }

    pub(super) fn surface_structural_at_global_in_manifest(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        global_x: i32,
        global_y: i32,
    ) -> Option<haven_world::StructuralCellV2> {
        let address = haven_world::surface_tile_address(WorldTileCoord::new(global_x, global_y));
        let scene_id = manifest.scene_id_for_chunk(address.chunk);
        self.surface_structural_cell(&scene_id, address.local_x, address.local_y)
    }

    /// Effective persisted structural level at a global surface tile. Fresh PCG
    /// worlds persist Level 0/1/2 explicitly; legacy AUTO cells retain the
    /// MountainRock=Level1 compatibility rule used by the structural resolver.
    pub(super) fn surface_structural_level_at_global_in_manifest(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        global_x: i32,
        global_y: i32,
    ) -> Option<u8> {
        let address = haven_world::surface_tile_address(WorldTileCoord::new(global_x, global_y));
        let scene_id = manifest.scene_id_for_chunk(address.chunk);
        let scene = self.world.scene_by_id(&scene_id)?;
        scene
            .map
            .get_structural_level(address.local_x, address.local_y)
            .or_else(|| {
                Some(if scene.map.get(address.local_x, address.local_y) == TileKind::MountainRock {
                    2
                } else {
                    0
                })
            })
    }

    pub(super) fn structural_surface_move_allowed(
        &self,
        from: WorldTileCoord,
        to: WorldTileCoord,
    ) -> bool {
        let direction = match (to.x - from.x, to.y - from.y) {
            (-1, 0) => haven_world::CardinalDirectionV2::West,
            (1, 0) => haven_world::CardinalDirectionV2::East,
            (0, -1) => haven_world::CardinalDirectionV2::North,
            (0, 1) => haven_world::CardinalDirectionV2::South,
            (0, 0) => return true,
            _ => return false,
        };

        // A visible south-facing cliff is a projected vertical wall extending
        // into screen-space cells below the structural lip. Those cells are not
        // walkable ground. Previous passes only blocked the lip edge itself,
        // which allowed the player to stand inside the rendered rock face.
        //
        // Keep this derived from structural face depth rather than image pixels:
        // gameplay/editor collision remains deterministic and independent of the
        // selected seasonal cliff texture. Explicit ramp/stair/ladder/bridge
        // corridors carve a matching opening through the projected wall.
        if self.structural_cliff_face_occupies_tile(to) {
            return false;
        }

        if self.structural_attachment_opens_edge(from, to, direction) {
            return true;
        }
        let source = self.surface_structural_at_global(from.x, from.y);
        let destination = self.surface_structural_at_global(to.x, to.y);
        let derived_blocked =
            haven_world::surface_structural_move_blocked_v1(source, destination, direction);
        // Structural levels are collision authority. Artwork is a projection of
        // this exact edge state and never decides whether traversal is blocked.
        // A level boundary blocks in both directions unless an explicit
        // ramp/stair/ladder/bridge attachment opens that exact edge. Waterfalls
        // and cave mouths remain blocking faces; cave entry is an interaction/
        // transition, not free movement.
        !derived_blocked
    }

    pub(super) fn structural_cliff_face_occupies_tile(&self, tile: WorldTileCoord) -> bool {
        use haven_world::{CardinalDirectionV2, EdgeMaskV2};

        // The six-cell LPC MountainPath corridor is real walkable ground. The
        // surrounding cliff is a perspective projection and must never re-block
        // a cell already certified as part of that connector. Level-change edges
        // inside the corridor remain governed by structural_connector_for_edge.
        if self.surface_authored_ramp_owner(tile.x, tile.y).is_some() {
            return false;
        }

        let manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
        let target_level = self
            .surface_structural_level_at_global_in_manifest(&manifest, tile.x, tile.y)
            .unwrap_or(0);

        // Current structural levels are intentionally shallow, but scan enough
        // rows to cover the largest supported face without putting an arbitrary
        // texture-sized collision box into gameplay logic. W3 additionally
        // checks adjacent host columns because ElizaWy's authored rounded south
        // terminal is a natural-scale three-column stamp (host x-1..x+1).
        const MAX_FACE_SCAN_ROWS: i32 = 12;

        for host_y in (tile.y - MAX_FACE_SCAN_ROWS)..tile.y {
            for host_x in (tile.x - 1)..=(tile.x + 1) {
                let Some(host) =
                    self.surface_structural_at_global_in_manifest(&manifest, host_x, host_y)
                else {
                    continue;
                };
                if !host.exposed_edges.contains(EdgeMaskV2::SOUTH)
                    || !structural_south_face_covers_column(host_x, tile.x, host)
                {
                    continue;
                }

                let chain_role = host
                    .cliff_shape_15()
                    .map(|shape| {
                        crate::runtime_structural_cliff_shapes::diagonal_chain_role_from_lookup(
                            shape,
                            |dx, dy| {
                                self.surface_structural_at_global_in_manifest(
                                    &manifest,
                                    host_x + dx,
                                    host_y + dy,
                                )
                                .and_then(|cell| cell.cliff_shape_15())
                            },
                        )
                    })
                    .unwrap_or(crate::runtime_structural_cliff_shapes::DiagonalChainRole::Isolated);
                let face_depth = structural_south_face_projection_depth(host, chain_role);
                if !tile_within_south_face_projection(host_y, tile.y, face_depth) {
                    continue;
                }

                // Perspective wall pixels may project over another equal/higher
                // platform in a concave/notched contour. That platform occludes
                // the wall and must remain real walkable ground.
                let host_level = self
                    .surface_structural_level_at_global_in_manifest(&manifest, host_x, host_y)
                    .unwrap_or(0);
                if target_level >= host_level {
                    continue;
                }

                // A certified connector owns the traversal corridor through its
                // host edge. The widened authored terminal does not fabricate
                // additional connector lanes in its neighboring visual columns.
                if host_x == tile.x
                    && self
                        .structural_connector_from_host_edge_in_manifest(
                            &manifest,
                            host_x,
                            host_y,
                            CardinalDirectionV2::South,
                        )
                        .is_some_and(
                            crate::runtime_structural_connectors::connector_opens_walk_corridor,
                        )
                {
                    continue;
                }

                return true;
            }
        }

        false
    }

    fn structural_attachment_opens_edge(
        &self,
        from: WorldTileCoord,
        to: WorldTileCoord,
        direction: haven_world::CardinalDirectionV2,
    ) -> bool {
        self.structural_connector_for_edge(from, to, direction)
            .is_some_and(crate::runtime_structural_connectors::connector_opens_walk_corridor)
    }
}


fn structural_south_face_covers_column(
    host_x: i32,
    target_x: i32,
    host: haven_world::StructuralCellV2,
) -> bool {
    host.cliff_shape_15()
        .is_some_and(crate::runtime_structural_cliff_shapes::is_south_authored_terminal)
        .then_some((target_x - host_x).abs() <= 1)
        .unwrap_or(target_x == host_x)
}


fn structural_south_face_projection_depth(
    host: haven_world::StructuralCellV2,
    chain_role: crate::runtime_structural_cliff_shapes::DiagonalChainRole,
) -> i32 {
    // W14: collision follows the literal receiver-facing visual depth.
    // Crest/rim presentation stays on the upper host row and does not consume
    // collision depth. A 1/2/3/4-tier south cliff therefore blocks exactly
    // 1/2/3/4 receiver rows regardless of straight/diagonal/terminal shape.
    let _ = chain_role;
    let south_segments = crate::runtime_structural_cliff_shapes::authored_south_face_segments(host)
        .max(1);
    i32::try_from(
        crate::runtime_structural_cliff_shapes::uniform_south_face_receiver_rows(south_segments),
    )
    .unwrap_or(i32::MAX)
}

fn tile_within_south_face_projection(host_y: i32, tile_y: i32, face_depth: i32) -> bool {
    tile_y > host_y && tile_y <= host_y + face_depth.max(0)
}



impl Game {
    /// Queue a structural solve for only the currently relevant residency
    /// neighborhood. The previous path cloned and rebaked every loaded exterior
    /// binding whenever one streamed neighbor changed.
    fn request_local_surface_structural_rebuild(
        &mut self,
        preload: &BTreeSet<(i32, i32)>,
    ) -> bool {
        if self.surface_chunks.structural_jobs.pending()
            || !self.surface_chunks.pending_structural_publish.is_empty()
            || !self.surface_chunks.pending_structural_levels_publish.is_empty()
            || self.surface_chunks.hydrology_jobs.pending()
            || !self.surface_chunks.pending_hydrology_publish.is_empty()
        {
            return false;
        }
        let manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
        let partitions = preload.iter().filter_map(|(x, y)| {
            let chunk = ChunkCoord::new(*x, *y);
            let scene_id = manifest.scene_id_for_chunk(chunk);
            self.world.scene_by_id(&scene_id).map(|scene| (chunk, scene.map.clone()))
        }).collect::<Vec<_>>();
        if partitions.is_empty() { return false; }
        // AC2: cloning the compact residency snapshot remains a read-only handoff,
        // but normalization and the structural solve now both run on the worker.
        let token = self.surface_chunks.streaming_generation.wrapping_add(1);
        self.surface_chunks.latest_structural_token = token;
        self.surface_chunks.structural_jobs.request(StructuralJobRequest { token, partitions })
    }

    /// Generic background byte persistence used by discovery-map snapshots.
    pub(super) fn queue_surface_background_bytes(
        &mut self,
        path: std::path::PathBuf,
        bytes: Vec<u8>,
    ) -> bool {
        self.surface_chunks.persistence.send(SurfacePersistenceRequest::Bytes { path, bytes })
    }
}

impl Game {
    pub(super) fn surface_streaming_telemetry(&self) -> String {
        format!(
            "Streaming | prepare {} | persist {} | hydro {}+{}q | structural {}+{}levelq+{}cacheq | cache {} | delta {} | hydro-pub {} | struct-pub {} | frame {:.2} ms",
            self.surface_chunks.jobs.pending_count(),
            self.surface_chunks.persistence.pending_count(),
            if self.surface_chunks.hydrology_jobs.pending() { "working" } else { "ready" },
            self.surface_chunks.pending_hydrology_publish.len(),
            if self.surface_chunks.structural_jobs.pending() { "working" } else { "ready" },
            self.surface_chunks.pending_structural_levels_publish.len(),
            self.surface_chunks.pending_structural_publish.len(),
            self.surface_chunks.cache_writes,
            self.surface_chunks.delta_writes,
            self.surface_chunks.hydrology_reconciles,
            self.surface_chunks.structural_rebuilds,
            self.surface_chunks.last_stream_cost_ms,
        )
    }
}
