impl Game {
    fn new(
        world_id: WorldSaveId,
        character_id: CharacterId,
        assets: RuntimeAssets,
        content_mode: runtime_content_authority::RuntimeContentMode,
    ) -> Self {
        let RuntimeAssets {
            asset_session,
            terrain: terrain_atlas,
            lpc_terrain_source,
            lpc_terrain_v7_source,
            lpc_bridge_source,
            lpc_cliff_source,
            lpc_waterfall_source,
            oga_cliff_source,
            terrain_transition: terrain_transition_atlas,
            lpc_mapped_terrain: lpc_mapped_terrain_atlas,
            live_autotile: live_autotile_atlas,
            objects: object_atlas,
            world_tiles: world_tile_atlas,
            player_walk: player_walk_atlas,
            hud_vitals_frame,
            hud_hotbar_frame,
            hud_minimap_frame,
            stamp_registry,
            placeable_registry,
            stamp_textures,
            placeable_textures,
            world_visual_override_textures,
            texture_cache,
            render_bindings,
            resource_bindings,
            character_appearance: runtime_character_appearance,
            item_icon_atlas,
            item_icon_rects,
        } = assets;
        let mut log = GameLog::new();
        log.event("Havenwild standalone prototype booted");
        log.event(&format!("Runtime root: {}", runtime_root().display()));
        log.event(&format!("Runtime save root: {}", runtime_save_root()));
        if let Some(session) = &asset_session {
            log.event(&format!(
                "Mounted {} production asset packs with {} stable source bindings",
                session.registry.mounted_pack_count(),
                session.sources.len()
            ));
        } else {
            log.event("Universal asset-pack startup unavailable; explicit legacy fallbacks active");
        }
        log.event(&format!(
            "Stable texture cache: {} source texture(s), {} stable binding(s)",
            texture_cache.loaded_source_count(),
            texture_cache.stable_binding_count()
        ));
        let building_recipe_registry =
            haven_assets::building_recipe::BuildingRecipeRegistry::load_from_project_root(runtime_root())
                .unwrap_or_else(|error| {
                    log.event(&format!("BuildingRecipe authority unavailable: {error}"));
                    haven_assets::building_recipe::BuildingRecipeRegistry::default()
                });
        let mut building_instance_registry =
            haven_assets::building_instance::BuildingInstanceRegistry::load_from_project_root(
                runtime_root(),
                &building_recipe_registry,
            )
            .unwrap_or_else(|error| {
                log.event(&format!("BuildingInstance authority unavailable: {error}"));
                haven_assets::building_instance::BuildingInstanceRegistry::default()
            });
        log.event(&format!(
            "Building authority ready: {} recipe(s), {} authored instance placement(s)",
            building_recipe_registry.entries().len(),
            building_instance_registry.entries().len()
        ));
        let collision_override_registry =
            runtime_collision_overrides::RuntimeCollisionOverrideRegistry::load(runtime_root())
                .unwrap_or_else(|error| {
                    log.event(&format!("Collision override authority unavailable: {error}"));
                    runtime_collision_overrides::RuntimeCollisionOverrideRegistry::default()
                });
        log.event(&format!(
            "Authored collision overrides ready: {} region(s)",
            collision_override_registry.len()
        ));
        log.event(&runtime_cache_contract::runtime_cache_ownership_summary());
        for fallback in texture_cache.legacy_fallbacks() {
            log.event(&format!(
                "Legacy texture fallback: {} -> {}",
                fallback.semantic_id,
                fallback.fallback_path.display()
            ));
        }
        log.event(if terrain_atlas.is_some() {
            "Loaded prototype terrain atlas"
        } else {
            "Using procedural terrain fallback"
        });
        log.event(if lpc_terrain_source.is_some() && lpc_terrain_v7_source.is_some() {
            "Licensed LPC terrain source sheets loaded for supplemental families and inspection"
        } else {
            "Complete licensed LPC terrain source sheets unavailable; packaged authored atlas remains active"
        });
        log.event(if oga_cliff_source.is_some() {
            "Loaded authored LPC directional cliff-ramp sheet; exact left/right 3x4 ramp stamps are active"
        } else {
            "Directional cliff-ramp source unavailable; ramp visuals are omitted while structural traversal remains authoritative"
        });
        log.event(if lpc_cliff_source.is_some() {
            "Generated ElizaWy cliff runtime projection loaded; V7-owned plateau fill, contextual diagonals, and connector-aware structural collision are active"
        } else {
            "Generated ElizaWy cliff runtime projection unavailable; structural cliff visuals disabled and collision fails open"
        });
        log.event(if lpc_waterfall_source.is_some() {
            "Pinned ElizaWy Waterfall.png loaded; certified multi-cell waterfall connector frames are active"
        } else {
            "Pinned ElizaWy waterfall source unavailable; waterfall visuals disabled while cliff collision remains authoritative"
        });
        log.event(if terrain_transition_atlas.is_some() {
            "Loaded compatibility terrain transition atlas"
        } else {
            "Using direct LPC transition blocks"
        });
        log.event(if lpc_mapped_terrain_atlas.is_some() {
            "Loaded authored LPC terrain-map-v7 tuple atlas"
        } else {
            "ERROR: authored LPC terrain-map-v7 tuple atlas unavailable; semantic fill fallback active"
        });
        log.event(if live_autotile_atlas.is_some() {
            "Loaded compatibility same-family autotile atlas"
        } else {
            "Generated same-family autotile atlas disabled"
        });
        log.event(if object_atlas.is_some() {
            "Loaded reviewed LPC terrain-object atlas"
        } else {
            "ElizaWy object atlas unavailable; catalogued objects will be omitted instead of procedurally substituted"
        });
        log.event(&format!(
            "Loaded {} with {} atlas sheet{}",
            stamp_registry.coverage_summary(),
            stamp_textures.len(),
            if stamp_textures.len() == 1 { "" } else { "s" }
        ));
        log.event(if world_tile_atlas.is_some() {
            "Loaded optional editor world-paint compatibility atlas"
        } else {
            "Optional editor world-paint compatibility atlas is not packaged; normal gameplay uses authored terrain"
        });
        if item_icon_atlas.is_some() && !item_icon_rects.is_empty() {
            log.event(&format!(
                "Universal LPC gameplay item icons active: {} item binding(s)",
                item_icon_rects.len()
            ));
        } else {
            log.event(
                "Universal LPC gameplay item icons unavailable; inventory/hotbar will use text fallback",
            );
        }
        let water_material = water_material::WaterMaterialRuntime::load();
        log.event(&format!("Water material backend: {}", water_material.status()));
        let save_root = runtime_save_root();
        let save_paths = world_save_paths(&save_root, &world_id).unwrap_or_else(|error| {
            panic!("invalid world launch request {}: {error}", world_id.0)
        });
        if let Err(error) = save_paths.ensure_directories() {
            log.event(&format!("Save directory preparation failed: {error}"));
        }
        let load_startup_world_started = std::time::Instant::now();
        let (mut world, mut startup_status) = Self::load_startup_world(&save_paths, &mut log);
        log.event(&format!(
            "Runtime bootstrap timing: load startup world = {:.1} ms",
            load_startup_world_started.elapsed().as_secs_f64() * 1000.0
        ));

        let content_authority_started = std::time::Instant::now();
        let content_authority = runtime_content_authority::converge_runtime_content_authority(
            &mut world,
            &save_paths,
            &mut log,
            content_mode,
        );
        log.event(&format!(
            "Runtime bootstrap timing: content authority = {:.1} ms",
            content_authority_started.elapsed().as_secs_f64() * 1000.0
        ));
        if let Some(status) = content_authority.status.as_deref() {
            startup_status = format!("{startup_status}; {status}");
        }
        let building_authority_started = std::time::Instant::now();
        let canonicalized_world_assets = placeable_registry.canonicalize_world_aliases(&mut world);
        // W46C converges worldgen placement and save-backed deltas into the same
        // BuildingInstanceRegistry before any local camera/view state is created.
        // The W53B visual test intentionally skips production-pack placements and
        // persistent building deltas so its screenshot target is deterministic.
        if !content_authority.visual_test_active {
            let worldgen_pack_path = runtime_worldgen_pack_path();
            match building_instance_registry.merge_worldgen_pack_placements(
                &worldgen_pack_path,
                &building_recipe_registry,
            ) {
                Ok(count) if count > 0 => log.event(&format!(
                    "Building authority merged {count} worldgen/PCG BuildingInstance placement(s) from {worldgen_pack_path}"
                )),
                Ok(_) => {}
                Err(error) => log.event(&format!(
                    "Building worldgen placement merge skipped: {error}"
                )),
            }
            let building_instance_state_path = building_instance_save_path(&save_paths.root);
            match building_instance_registry.apply_world_state_from_path(
                &building_instance_state_path,
                &world_id.0,
                &building_recipe_registry,
            ) {
                Ok(true) => log.event(&format!(
                    "Restored BuildingInstance placement/state deltas from {}",
                    building_instance_state_path.display()
                )),
                Ok(false) => {}
                Err(error) => log.event(&format!(
                    "BuildingInstance save state unavailable; content authority remains active: {error}"
                )),
            }
        } else {
            log.event(
                "W54D2 Estate visual test: persistent BuildingInstance deltas and production PCG pack placements bypassed; authored instance catalog retained",
            );
        }
        match ensure_linked_building_interior_scenes(
            &mut world,
            &building_instance_registry,
            &building_recipe_registry,
            &placeable_registry,
        ) {
            Ok(count) if count > 0 => log.event(&format!(
                "Linked building interior authority ensured {count} exterior/interior doorway pair(s)"
            )),
            Ok(_) => {}
            Err(errors) => {
                for error in errors {
                    log.event(&format!("Linked building interior repair skipped: {error}"));
                }
            }
        }
        let building_instance_views = building_instance_registry.initial_view_states();
        log.event(&format!(
            "Runtime bootstrap timing: building placement/interior authority = {:.1} ms",
            building_authority_started.elapsed().as_secs_f64() * 1000.0
        ));
        if canonicalized_world_assets > 0 {
            log.event(&format!(
                "Published world asset authority canonicalized {canonicalized_world_assets} authored scene alias reference(s)"
            ));
        }
        let mut character_world_link = load_character_world_link(std::path::Path::new(&save_paths.root), &character_id)
            .unwrap_or_else(|_| CharacterWorldLink::new(character_id.clone(), world_id.clone()));
        if content_authority.visual_test_active {
            let active = world.active();
            character_world_link.world_scene = active.id.code().to_string();
            character_world_link.world_position = [active.spawn_x, active.spawn_y];
        } else if content_authority.rebased_saved_world
            && (runtime_content_authority::is_authored_scene(&character_world_link.world_scene)
                || runtime_content_authority::is_retired_parallel_interior(
                    &character_world_link.world_scene,
                ))
        {
            let requested = SceneReference::new(character_world_link.world_scene.clone());
            let canonical = world
                .scene_by_reference(&requested)
                .unwrap_or_else(|| world.active());
            log.event(&format!(
                "W53B content rebase relocated character from stale {} coordinates to current {} spawn",
                character_world_link.world_scene, canonical.id
            ));
            character_world_link.world_scene = canonical.id.code().to_string();
            character_world_link.world_position = [canonical.spawn_x, canonical.spawn_y];
        }
        if !character_world_link.world_scene.trim().is_empty() {
            let linked_scene = SceneReference::new(character_world_link.world_scene.clone());
            if world.scene_by_reference(&linked_scene).is_none() {
                let active = world.active();
                log.event(&format!(
                    "Character scene {} is retired/unavailable under current content authority; relocating to {} spawn",
                    character_world_link.world_scene,
                    active.id
                ));
                character_world_link.world_scene = active.id.code().to_string();
                character_world_link.world_position = [active.spawn_x, active.spawn_y];
            }
        }
        if let Some(restored) = Self::restore_character_world_link(&mut world, &character_world_link) {
            startup_status = format!("{startup_status}; {restored}");
        }
        let ui_layout = Self::load_saved_layout(&mut log);
        let world_paint_edit_sequence =
            Self::world_paint_delta_last_sequence(&mut log, &save_paths.world_paint_delta);
        let (spawn_x, spawn_y) = (world.active().spawn_x, world.active().spawn_y);
        let inspector = inspect_scene_cell(world.active(), spawn_x, spawn_y);
        let active_scene_autotile_started = std::time::Instant::now();
        let mut terrain_cache = LiveAutotileCache::new(world.active());
        terrain_cache.synchronize(world.active());
        log.event(&format!(
            "Runtime bootstrap timing: active-scene autotile cache = {:.1} ms",
            active_scene_autotile_started.elapsed().as_secs_f64() * 1000.0
        ));
        // World generation and streamed partition generation share the exact
        // persisted 64-bit seed. Truncating this to u32 makes neighboring
        // streamed chunks sample a different geographic field and produces
        // ruler-straight coast/terrain seams at partition boundaries.
        let world_seed = load_world_save_metadata(&save_paths.metadata)
            .map(|metadata| metadata.world_seed)
            .unwrap_or(1_337_u64);
        let world_creation_settings =
            haven_world::load_world_creation_settings_from_path(&save_paths.world_creation_settings)
                .unwrap_or_else(|error| {
                    log.event(&format!(
                        "World creation settings unavailable; using deterministic defaults: {error}"
                    ));
                    let mut settings = haven_world::WorldCreationSettings::default();
                    settings.seed = world_seed;
                    settings
                });
        log.event(&format!(
            "World generation profile: extent={} difficulty={} landform={} seed={}",
            world_creation_settings.extent_mode.label(),
            world_creation_settings.difficulty.label(),
            world_creation_settings.landform.label(),
            world_creation_settings.seed
        ));
        let world_topology = load_world_topology_from_path(&save_paths.world_topology)
            .unwrap_or_else(|error| {
                log.event(&format!(
                    "World topology unavailable; deriving from saved creation settings: {error}"
                ));
                let [width, height] = world_creation_settings.world_dimensions_tiles();
                haven_world::WorldTopologyConfig {
                    schema: haven_world::WORLD_TOPOLOGY_SCHEMA.to_string(),
                    extent: if world_creation_settings.is_endless() {
                        haven_world::WorldTopologyExtent::Endless
                    } else {
                        haven_world::WorldTopologyExtent::Finite
                    },
                    width_tiles: width as i32,
                    height_tiles: height as i32,
                    origin_x_tiles: if world_creation_settings.is_endless() {
                        0
                    } else {
                        -(width as i32) / 2
                    },
                    origin_y_tiles: if world_creation_settings.is_endless() {
                        0
                    } else {
                        512 - height as i32
                    },
                    chunk_size_tiles: world_creation_settings.chunk_size_tiles as i32,
                    horizontal_wrap: haven_world::HorizontalWrapMode::Disabled,
                    vertical_boundary: haven_world::VerticalBoundaryMode::Clamped,
                }
            });
        log.event(&format!(
            "World topology: {:?} origin=({}, {}) span={}x{}",
            world_topology.extent,
            world_topology.origin_x_tiles,
            world_topology.origin_y_tiles,
            world_topology.width_tiles,
            world_topology.height_tiles
        ));
        let player_spawn = Self::character_world_position_or_spawn(
            &character_world_link, spawn_x, spawn_y
        );
        log.event(&format!(
            "Player spawn resolved: character={} scene={} world=({:.1}, {:.1}) tile=({}, {}) appearance_layers={} equipment_overlays={}",
            character_id.0,
            world.active_scene.code(),
            player_spawn.x,
            player_spawn.y,
            (player_spawn.x / TILE_SIZE).floor() as i32,
            (player_spawn.y / TILE_SIZE).floor() as i32,
            runtime_character_appearance.as_ref().map_or(0, |appearance| appearance.layers.len()),
            runtime_character_appearance.as_ref().map_or(0, |appearance| appearance.equipment_overlays.len())
        ));
        log.event(if runtime_character_appearance.is_some() {
            "Runtime player compositor attached"
        } else if player_walk_atlas.is_some() {
            "Runtime player compositor unavailable; generated LPC base atlas fallback attached"
        } else {
            "Runtime player visual unavailable; procedural emergency fallback active"
        });
        let inventory_path = player_inventory_ui::PlayerInventoryUi::inventory_save_path(
            &save_paths.character_links,
            &character_id.0,
        );
        let mut player_inventory_ui =
            player_inventory_ui::PlayerInventoryUi::load_or_starter(inventory_path);
        if let Some(appearance) = runtime_character_appearance.as_ref() {
            character_equipment_runtime::bootstrap_inventory_equipment(
                &mut player_inventory_ui,
                &appearance.appearance,
            );
        }
        let character_vitals =
            character_runtime_compositor::RuntimeCharacterAppearance::load_profile_vitals(
                std::path::Path::new(&runtime_save_root()),
                &character_id,
            )
            .unwrap_or_else(|error| {
                log.event(&format!("Character vitals load failed; using defaults: {error}"));
                CharacterVitalsState::default()
            });
        let world_map = runtime_world_map::WorldMapState::load(&save_paths.scene_manifest);
        let mut ecs_world = EntityWorld::new();
        let player_entity = ecs_world.spawn();
        ecs_world
            .insert(
                player_entity,
                RuntimeEntityIdentity::player(character_id.0.clone()),
            )
            .expect("fresh player entity must accept runtime identity");
        ecs_world
            .insert(
                player_entity,
                CharacterRuntimeState::player_default(player_entity),
            )
            .expect("fresh player entity must accept character runtime state");
        log.event(&format!(
            "Runtime ECS player entity initialized: {}",
            player_entity
        ));

        Self {
            world_id,
            character_id,
            character_world_link: character_world_link.clone(),
            save_paths,
            world,
            building_recipe_registry,
            building_instance_registry,
            building_instance_views,
            building_door_animations: std::collections::BTreeMap::new(),
            scene_door_animations: std::collections::BTreeMap::new(),
            world_creation_settings,
            world_topology,
            palette: AuthoringPalette::default(),
            selected_tool: 0,
            selected_gameplay_tool: 0,
            universal_lpc_gameplay_equipment: universal_lpc_gameplay_equipment::UniversalLpcGameplayEquipmentRuntime::load_default().unwrap_or_default(),
            pending_gameplay_tool_action: None,
            ranged_aim: None,
            runtime_projectiles: Vec::new(),
            runtime_chat: runtime_chat::RuntimeChatState::default(),
            editor_tab: EditorTab::Tiles,
            terrain_paint_mode: TerrainPaintMode::Exact,
            tool_page: 0,
            selected_transition_target: 1,
            selected_transition_index: 0,
            selected_object_index: None,
            selected_placeable_index: 0,
            object_list_offset: 0,
            footprint_edit_target: FootprintEditTarget::Visual,
            selected_rule_tile: 0,
            player: player_spawn,
            ecs_world,
            player_entity,
            camera_target: player_spawn,
            camera_zoom: RUNTIME_CAMERA_DEFAULT_ZOOM,
            _runtime_content_mode: content_mode,
            dev_mode: false,
            dev_toggle_armed: true,
            build_mode: true,
            editor_minimized: false,
            tavern_open: false,
            pause_menu_open: false,
            pause_menu_page: PauseMenuPage::Main,
            pause_menu_selection: 0,
            controls: ControlRuntime::load(),
            player_inventory_ui,
            character_vitals,
            day_clock: 8.0,
            reputation: character_world_link.world_reputation.get("global").copied().unwrap_or(1),
            coin: 120,
            customers: Vec::new(),
            customer_timer: 0.0,
            selected_cell: (spawn_x, spawn_y),
            tile_context_menu: None,
            copied_tile: None,
            brush_size: 1,
            world_seed,
            map_water_level: 34,
            map_mountain_level: 76,
            map_brush: MapBrushMode::Raise,
            world_paint_family: WorldPaintFamily::Water,
            world_paint_layer: WorldPaintLayer::WaterBase,
            world_paint_subcell_mode: WorldPaintSubcellMode::Cell8,
            world_paint_strength: 1.0,
            world_paint_autotile: true,
            world_paint_mirror_horizontal: false,
            world_paint_mirror_vertical: false,
            world_paint_last_report: "World paint idle".to_string(),
            world_paint_delta_status: if world_paint_edit_sequence > 0 {
                format!(
                    "Paint delta sequence restored at #{:04}",
                    world_paint_edit_sequence
                )
            } else {
                "No paint deltas recorded".to_string()
            },
            world_paint_inspector_status: "Material inspector idle".to_string(),
            world_paint_inspector: None,
            world_paint_adjacency_status: "Material adjacency idle".to_string(),
            world_paint_adjacency: None,
            world_paint_tile_resolver_status: "Transition tile resolver idle".to_string(),
            world_paint_tile_resolution: None,
            world_paint_render_status: "World paint render bindings idle".to_string(),
            world_paint_render_bindings: WorldPaintRenderBindingCache::empty(),
            world_paint_edit_sequence,
            inspector,
            status_message: startup_status,
            last_replication_status: "Net idle".to_string(),
            replication_sequence: 0,
            validation_messages: Vec::new(),
            show_world_graph: false,
            // F3 must open as a lightweight authoring shell. Expensive world
            // diagnostics are opt-in (H/C/I/T) rather than automatically
            // submitting thousands of overlay primitives on the first frame.
            show_footprint_overlay: false,
            show_collision_overlay: false,
            show_interaction_overlay: false,
            show_terrain_debug_overlay: false,
            show_transition_rule_inspector: false,
            show_transition_rule_preview: false,
            transition_rule_preview_index: 0,
            transition_rule_editor_filter: TransitionRuleCatalogFilter::All,
            transition_rule_editor_index: 0,
            transition_rule_editor_scroll: 0,
            asset_reference_grid_filter: AssetReferenceGridFilter::All,
            asset_reference_family_filter: AssetReferenceFamilyFilter::All,
            asset_reference_policy_filter: AssetReferencePolicyFilter::All,
            asset_reference_index: 0,
            asset_reference_scroll: 0,
            ui_layout,
            layout_edit_mode: false,
            layout_drag: None,
            editor_resizing: false,
            command_bus: EditorCommandBus::with_limit(UNDO_LIMIT),
            terrain_cache,
            base_terrain_cache: std::cell::RefCell::new(
                base_terrain_cache::BaseTerrainChunkCache::default(),
            ),
            chunk_surface_cache: std::cell::RefCell::new(
                chunk_surface_cache::ChunkSurfaceDescriptorCache::default(),
            ),
            visible_terrain_plan: std::cell::RefCell::new(
                runtime_terrain_pass::VisibleTerrainPlanCache::default(),
            ),
            terrain_scene_surface: std::cell::RefCell::new(
                terrain_scene_surface::TerrainSceneSurfaceCache::default(),
            ),
            scene_backdrop_height_cache: std::cell::RefCell::new(
                runtime_terrain_pass::SceneBackdropHeightCache::default(),
            ),
            terrain_render_telemetry: render_telemetry::TerrainRenderTelemetry::default(),
            water_material,
            water_ripples: water_ripple_runtime::WaterRippleRuntime::default(),
            terrain_cache_next_sync_at: get_time() + 0.35,
            character_autosave_next_at: get_time() + 120.0,
            character_state_sequence: 0,
            last_applied_character_state_sequence: 0,
            building_state_sequence: 0,
            last_applied_building_state_sequence: 0,
            character_appearance_reload_requested: false,
            terrain_atlas,
            lpc_terrain_source,
            lpc_terrain_v7_source,
            lpc_bridge_source,
            lpc_cliff_source,
            lpc_waterfall_source,
            oga_cliff_source,
            lpc_mapped_terrain_atlas,
            live_autotile_atlas,
            object_atlas,
            world_tile_atlas,
            player_walk_atlas,
            hud_vitals_frame,
            hud_hotbar_frame,
            hud_minimap_frame,
            item_icon_atlas,
            item_icon_rects,
            world_map,
            runtime_character_appearance,
            stamp_registry,
            placeable_registry,
            stamp_textures,
            placeable_textures,
            world_visual_override_textures,
            collision_override_registry,
            asset_binding_counts: (render_bindings.len(), render_bindings.fallback_count(), resource_bindings.len()),
            surface_chunks: runtime_surface_streaming::SurfaceChunkRuntime::default(),
            asset_session,
            _texture_cache: texture_cache,
            log,
        }
    }
}


/// W57K runtime bridge: linked BuildingRecipe interiors are deterministic scene
/// authority, not an editor-only convenience. Existing authored interiors are
/// preserved; only missing scenes/doorway links are created or repaired.
fn ensure_linked_building_interior_scenes(
    world: &mut GameWorld,
    instances: &haven_assets::building_instance::BuildingInstanceRegistry,
    recipes: &haven_assets::building_recipe::BuildingRecipeRegistry,
    placeables: &haven_assets::placeable_asset_registry::PublishedWorldAssetRegistry,
) -> Result<usize, Vec<String>> {
    let exterior_ids = world
        .scenes
        .iter()
        .filter(|scene| scene.kind == SceneKind::Exterior)
        .map(|scene| scene.id.clone())
        .collect::<Vec<_>>();
    let mut ensured = 0usize;
    let mut errors = Vec::new();

    for source_id in exterior_ids {
        let Some(source_snapshot) = world.scene_by_id(&source_id).cloned() else { continue; };
        let manifest = haven_world::continuous_surface::ContinuousSurfaceManifest::for_world(world);
        let origin = manifest
            .chunk_for_scene(&source_snapshot.id)
            .map(|chunk| [chunk.x * MAP_W as i32, chunk.y * MAP_H as i32]);
        let resolved = instances.resolved_for_scene(
            source_snapshot.id.code(),
            manifest.pcg_region.as_deref(),
            origin,
            [source_snapshot.dimensions.width as i32, source_snapshot.dimensions.height as i32],
            recipes,
        );

        for instance in resolved {
            let Some(recipe) = recipes.entry(&instance.recipe_id) else { continue; };
            if recipe.persistence.interior_policy != "linked_enclosed_scene" {
                continue;
            }
            let Some(level) = recipe.level(recipe.default_level) else {
                errors.push(format!("{} has no default level", recipe.id));
                continue;
            };
            let Some(opening) = level
                .openings
                .iter()
                .find(|opening| opening.id == "front_door")
                .or_else(|| level.openings.iter().find(|opening| {
                    opening.kind == haven_assets::building_recipe::BuildingOpeningKind::Door
                }))
            else {
                errors.push(format!("{} has no linked exterior doorway", recipe.id));
                continue;
            };
            let exterior_tile = [
                instance.anchor_tile[0] + opening.tile[0],
                instance.anchor_tile[1] + opening.tile[1],
            ];
            // A continuous-surface building may overlap neighboring storage
            // partitions. Only the partition that actually owns its doorway
            // materializes the linked scene/transition.
            if !source_snapshot.contains_cell(exterior_tile[0], exterior_tile[1]) {
                continue;
            }

            let materialized = match haven_assets::building_recipe::materialize_linked_building_interior(
                recipe,
                level,
                placeables,
                &source_snapshot.id,
                &source_snapshot.name,
                &instance.id,
                opening.tile[0],
            ) {
                Ok(value) => value,
                Err(error) => {
                    errors.push(format!("{}: {error}", instance.id));
                    continue;
                }
            };
            let target_id = materialized.scene.id.clone();
            let destination_spawn = [materialized.scene.spawn_x, materialized.scene.spawn_y];
            let return_threshold = materialized.entry_threshold;

            // W57K8 canonical-envelope migration: generated linked interiors may
            // follow a canonical recipe footprint change. Only auto-refresh a
            // scene that still has the materializer's generated name and whose
            // dimensions differ from the current recipe output. The known legacy
            // 10x8 starter-cottage shell is also migrated even if it used the
            // older shortened generated name visible in K5/K6. Other authored
            // interiors are not globally replaced.
            let legacy_generated_name = format!("{} Interior", recipe.label);
            let legacy_generated_suffix = format!("— {legacy_generated_name}");
            let refresh_generated = world.scene_by_id(&target_id).is_some_and(|existing| {
                let generated_name = existing.name == materialized.scene.name
                    || existing.name == legacy_generated_name
                    || existing.name.ends_with(&legacy_generated_suffix);
                let legacy_cottage_dimensions = recipe.id == "havenwild.estate.starter_cottage"
                    && existing.dimensions.width == 10
                    && existing.dimensions.height == 8;
                existing.kind == haven_core::SceneKind::Interior
                    && existing.dimensions != materialized.scene.dimensions
                    && (generated_name || legacy_cottage_dimensions)
            });
            if refresh_generated {
                let replace_at = world.scenes.position(&target_id).unwrap_or(world.scenes.len());
                let _ = world.scenes.remove(&target_id);
                if let Err(error) = world.scenes.insert_at(replace_at, materialized.scene) {
                    errors.push(format!("{}: {error}", target_id));
                    continue;
                }
            } else if world.scene_by_id(&target_id).is_none() {
                if let Err(error) = world.scenes.insert(materialized.scene) {
                    errors.push(format!("{}: {error}", target_id));
                    continue;
                }
            }

            if let Some(source) = world.scene_mut_by_id(&source_id) {
                upsert_runtime_transition(
                    source,
                    exterior_tile,
                    target_id.clone(),
                    destination_spawn,
                    format!("Enter {}", recipe.label),
                );
            }
            let return_x = exterior_tile[0].clamp(0, source_snapshot.dimensions.width as i32 - 1);
            let return_y = (exterior_tile[1] + 1)
                .clamp(0, source_snapshot.dimensions.height as i32 - 1);
            if let Some(interior) = world.scene_mut_by_id(&target_id) {
                upsert_runtime_transition(
                    interior,
                    return_threshold,
                    source_id.clone(),
                    [return_x, return_y],
                    format!("Exit {}", recipe.label),
                );
            }
            ensured += 1;
        }
    }

    if errors.is_empty() { Ok(ensured) } else { Err(errors) }
}

fn upsert_runtime_transition(
    scene: &mut SceneMap,
    tile: [i32; 2],
    target: haven_core::ProjectSceneId,
    spawn: [i32; 2],
    label: String,
) {
    if let Some(existing) = scene.transition_at_mut(tile[0], tile[1]) {
        existing.x = tile[0];
        existing.y = tile[1];
        existing.w = 1;
        existing.h = 1;
        existing.target = target.into();
        existing.spawn_x = spawn[0];
        existing.spawn_y = spawn[1];
        existing.label = label;
        return;
    }
    let stable_key = format!("{}:{}:{}:{}", scene.id.code(), tile[0], tile[1], target.code());
    scene.insert_transition(haven_core::Transition {
        id: haven_core::TransitionId::from_stable_key(&stable_key),
        x: tile[0],
        y: tile[1],
        w: 1,
        h: 1,
        target: target.into(),
        spawn_x: spawn[0],
        spawn_y: spawn[1],
        label,
    });
}
