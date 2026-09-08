use super::*;
use crate::runtime_config::client_worldgen_test_world_enabled;

impl Game {
    fn migrate_legacy_exterior_flat_cliff_tiles(world: &mut GameWorld) -> usize {
        let mut migrated = 0usize;
        for scene in &mut world.scenes {
            if scene.kind != SceneKind::Exterior {
                continue;
            }
            let original = scene.map.tiles.clone();
            for y in 0..MAP_H {
                for x in 0..MAP_W {
                    let index = y * MAP_W + x;
                    if original.get(index) != Some(&TileKind::Cliff) {
                        continue;
                    }
                    let mut coastal_neighbor = false;
                    for oy in -1_i32..=1 {
                        for ox in -1_i32..=1 {
                            if ox == 0 && oy == 0 {
                                continue;
                            }
                            let nx = x as i32 + ox;
                            let ny = y as i32 + oy;
                            if nx < 0 || ny < 0 || nx >= MAP_W as i32 || ny >= MAP_H as i32 {
                                continue;
                            }
                            let neighbor = original[ny as usize * MAP_W + nx as usize];
                            if matches!(
                                neighbor,
                                TileKind::Sand
                                    | TileKind::WetSand
                                    | TileKind::ShallowWater
                                    | TileKind::DeepWater
                            ) {
                                coastal_neighbor = true;
                            }
                        }
                    }
                    scene.map.tiles[index] = if coastal_neighbor {
                        TileKind::Grass
                    } else {
                        TileKind::MountainRock
                    };
                    migrated += 1;
                }
            }
        }
        migrated
    }
    fn migrate_legacy_wet_sand_tiles(world: &mut GameWorld) -> usize {
        let mut migrated = 0usize;
        for scene in &mut world.scenes {
            for tile in &mut scene.map.tiles {
                if *tile == TileKind::WetSand {
                    *tile = TileKind::Sand;
                    migrated += 1;
                }
            }
        }
        migrated
    }

    fn migrate_legacy_natural_object_footprints(world: &mut GameWorld) -> usize {
        let mut migrated = 0usize;
        for scene in &mut world.scenes {
            let pack_defined_ids = scene
                .map
                .object_asset_refs
                .keys()
                .copied()
                .collect::<std::collections::BTreeSet<_>>();
            for object in &mut scene.map.objects {
                if pack_defined_ids.contains(&object.id)
                    || !matches!(
                        object.kind,
                        ObjectKind::Tree
                            | ObjectKind::Bush
                            | ObjectKind::Boulder
                            | ObjectKind::OreNode
                            | ObjectKind::Mushroom
                            | ObjectKind::Herb
                            | ObjectKind::Stump
                            | ObjectKind::Log
                    )
                {
                    continue;
                }
                let audited = audited_object_footprint_for_cell(object.kind, object.x, object.y);
                if object.footprint != audited {
                    object.footprint = audited;
                    migrated += 1;
                }
            }
        }
        migrated
    }

    /// Generated-world-only coastline cleanup. Never call this after replaying
    /// editor paint or immediately before saving an authored world.
    pub(super) fn apply_generated_coastline_cleanup(
        world: &mut GameWorld,
        log: &mut GameLog,
    ) -> (usize, usize) {
        let mut changed_scenes = 0usize;
        let mut changed_tiles = 0usize;
        for scene in &mut world.scenes {
            if scene.kind != SceneKind::Exterior {
                continue;
            }
            let report = apply_coastline_tile_pass(&mut scene.map, scene.biome);
            let contact_report = normalize_lpc_authored_material_contacts_region(
                &mut scene.map,
                0,
                0,
                MAP_W as i32 - 1,
                MAP_H as i32 - 1,
            );
            let tuple_report = audit_lpc_tuple_compatibility(&scene.map);
            let mutations = report
                .total_mutations()
                .saturating_add(contact_report.total_mutations());
            if mutations > 0 {
                changed_scenes += 1;
                changed_tiles += mutations;
                log.event(&format!(
                    "{} {}; authored contact repairs {}",
                    scene.name,
                    report.status_line(),
                    contact_report.total_mutations()
                ));
            }
            if !tuple_report.is_compatible() {
                let signature_summary = tuple_report
                    .unsupported_signatures
                    .iter()
                    .take(4)
                    .map(|(signature, count)| format!("{signature} x{count}"))
                    .collect::<Vec<_>>()
                    .join(", ");
                log.event(&format!(
                    "{} tuple compatibility: {} unsupported of {} inspected [{}]",
                    scene.name, tuple_report.unsupported, tuple_report.inspected, signature_summary
                ));
            }
        }
        if changed_scenes > 0 {
            log.event(&format!(
                "Generated coastline cleanup rebuilt {changed_tiles} tiles across {changed_scenes} scenes"
            ));
        }
        let footprint_repairs = Self::migrate_legacy_natural_object_footprints(world);
        if footprint_repairs > 0 {
            log.event(&format!(
                "Normalized {footprint_repairs} built-in natural object footprint(s) from the audited atlas manifest"
            ));
        }
        (changed_tiles, footprint_repairs)
    }
    pub(crate) fn load_startup_world(
        save_paths: &ClientSavePaths,
        log: &mut GameLog,
    ) -> (GameWorld, String) {
        if client_worldgen_test_world_enabled() {
            // During the current world-generation development lane the checked-in
            // production pack is authoritative because the build materializes every
            // current generator change into its test scene. A stale F11 editor export
            // must not hide new terrain work from the client. Editor export remains a
            // safe fallback until this temporary policy is lifted.
            let candidates = [
                (
                    "terrain certification worldgen pack",
                    runtime_worldgen_pack_path(),
                ),
                (
                    "editor worldgen export fallback",
                    runtime_worldgen_export_path(),
                ),
            ];
            let mut failures = Vec::new();
            for (label, path) in candidates {
                match load_worldgen_pack_from_path(&path) {
                    Ok((mut world, report)) => {
                        let status = format!(
                            "Worldgen test world active from {label}: {}",
                            report.status_line()
                        );
                        log.event(&status);
                        for warning in &report.warnings {
                            log.event(&format!("Worldgen warning: {warning}"));
                        }
                        let _ = Self::apply_generated_coastline_cleanup(&mut world, log);
                        let replay_status = Self::replay_world_paint_deltas_into_world(
                            &mut world,
                            log,
                            &save_paths.world_paint_delta,
                            None,
                            "Worldgen test-world paint delta replay",
                        );
                        return (
                            world,
                            format!(
                                "{status}; selected save baseline bypassed for terrain/worldgen testing; {replay_status}"
                            ),
                        );
                    }
                    Err(error) => failures.push(format!("{label} ({path}): {error}")),
                }
            }
            log.event(&format!(
                "Worldgen test-world loading failed; falling back to selected save: {}",
                failures.join(" | ")
            ));
        }

        match load_world_from_path(&save_paths.world) {
            Ok(world) => {
                let mut world = world;
                let mut status = format!("Loaded {} from {}", save_paths.root, save_paths.world);
                let saved_metadata = load_world_save_metadata(&save_paths.metadata).ok();
                let saved_generation = saved_metadata
                    .as_ref()
                    .map(|metadata| metadata.generation_version)
                    .unwrap_or(1);
                let saved_world_seed = saved_metadata
                    .as_ref()
                    .map(|metadata| metadata.world_seed)
                    .unwrap_or(1_337);
                if saved_generation < CURRENT_CLIENT_GENERATION_VERSION {
                    let migrated = Self::migrate_legacy_exterior_flat_cliff_tiles(&mut world);
                    let pcg_surface_migration =
                        haven_world::migrate_legacy_pcg_ocean_domains(&mut world);
                    let migrated_wet_sand = Self::migrate_legacy_wet_sand_tiles(&mut world);
                    // AC3R4F generation-20 migration: reconcile saved PCG partitions
                    // with the current source-native structural access and ecology
                    // authorities. Generation 20 intentionally reruns the idempotent
                    // natural-object top-up so older test worlds receive the deterministic
                    // per-partition tree floor without deleting existing objects.
                    let mut structural_ramps = 0usize;
                    let mut structural_ladders = 0usize;
                    let mut structural_partitions = 0usize;
                    for scene in &mut world.scenes {
                        if scene.kind != SceneKind::Exterior {
                            continue;
                        }
                        let Some((_, chunk)) = haven_world::parse_pcg_surface_scene_id(&scene.id) else {
                            continue;
                        };
                        let report = haven_world::reconcile_generated_surface_structural_access_v1(
                            scene,
                            saved_world_seed,
                            chunk,
                        );
                        structural_partitions += 1;
                        structural_ramps += report.generated_ramps;
                        structural_ladders += report.generated_ladders;
                    }
                    if structural_partitions > 0 {
                        log.event(&format!(
                            "Reconciled source-native structural access across {structural_partitions} saved PCG partition(s): {structural_ramps} ramp(s), {structural_ladders} ladder(s)"
                        ));
                    }
                    // Existing saves may contain exact editor-authored terrain.
                    // Do not rerun generated coastline cleanup during migration,
                    // because it would rewrite grass beside water into beach sand.
                    let mainland_features =
                        haven_world::island_pcg::populate_missing_pcg_mainland_features(
                            &mut world,
                            saved_world_seed,
                        )
                        .unwrap_or_else(|error| {
                            log.event(&format!(
                                "Mainland road/civic/cave migration was skipped: {error}"
                            ));
                            haven_world::MainlandFeatureReport::default()
                        });
                    let natural_objects =
                        haven_world::island_pcg::populate_missing_pcg_natural_objects(
                            &mut world,
                            saved_world_seed,
                        );
                    let willowmere_buildings = mainland_features
                        .willowmere_center
                        .and_then(|center| {
                            let metadata = saved_metadata.as_ref()?;
                            let source_scene = if metadata.starting_scene_code.trim().is_empty() {
                                world.active_scene.code().to_string()
                            } else {
                                metadata.starting_scene_code.clone()
                            };
                            Some(
                                crate::client_save_generation_city::reconcile_willowmere_worldgen_buildings(
                                    &save_paths.root,
                                    &metadata.world_id.0,
                                    &source_scene,
                                    center,
                                ),
                            )
                        });
                    match willowmere_buildings {
                        Some(Ok(count)) => log.event(&format!(
                            "Reconciled {count} source-native Willowmere worldgen building(s); diagnostic-only prototypes are excluded"
                        )),
                        Some(Err(error)) => log.event(&format!(
                            "Willowmere BuildingInstance migration was skipped: {error}"
                        )),
                        None => {}
                    }
                    let migrated_footprints =
                        Self::migrate_legacy_natural_object_footprints(&mut world);
                    if natural_objects.total_objects() > 0 {
                        log.event(&format!(
                            "Restored {} authored natural/resource object(s) across {} PCG partition(s): {} trees ({} inside {} forest-habitat grass cells), {} bushes, {} herbs/flowers, {} mushrooms, {} boulders, {} ore nodes",
                            natural_objects.total_objects(),
                            natural_objects.partitions_populated,
                            natural_objects.trees,
                            natural_objects.forest_trees,
                            natural_objects.forest_habitat_cells,
                            natural_objects.bushes,
                            natural_objects.herbs_and_flowers,
                            natural_objects.mushrooms,
                            natural_objects.boulders,
                            natural_objects.ore_nodes,
                        ));
                    }
                    if mainland_features.total_mutations() > 0 {
                        log.event(&format!(
                            "Materialized Alderreach authority: {} road tiles across {} partitions, {} Willowmere lot reservations ({} invisible tiles), {} harbor-reserved tiles, {} civic objects, {} cave entrance(s), {} legacy terrain repairs, and {} removed legacy/misclassified objects",
                            mainland_features.road_tiles,
                            mainland_features.road_partitions,
                            mainland_features.city_plot_reservations,
                            mainland_features.city_reserved_tiles,
                            mainland_features.harbor_reserved_tiles,
                            mainland_features.civic_objects,
                            mainland_features.cave_entrances,
                            mainland_features.repaired_legacy_tiles,
                            mainland_features.removed_legacy_objects,
                        ));
                    }
                    if migrated_wet_sand > 0 {
                        log.event(&format!(
                            "Normalized {migrated_wet_sand} legacy WetSand tile(s) to V7 Sand"
                        ));
                    }
                    if let Err(error) = save_world_to_path(&save_paths.world, &world) {
                        log.event(&format!("Terrain baseline migration save failed: {error}"));
                    }
                    match load_world_save_metadata(&save_paths.metadata) {
                        Ok(mut metadata) => {
                            metadata.generation_version = CURRENT_CLIENT_GENERATION_VERSION;
                            if let Err(error) =
                                save_world_save_metadata(&save_paths.metadata, &metadata)
                            {
                                log.event(&format!(
                                    "Terrain metadata migration save failed: {error}"
                                ));
                            }
                        }
                        Err(error) => {
                            log.event(&format!("Terrain metadata migration unavailable: {error}"))
                        }
                    }
                    status = format!(
                        "{status}; migrated procedural terrain generation {saved_generation}->{} ({migrated} legacy exterior flat-cliff cells, {} PCG marine-water cells, {} obsolete exterior transitions, {} mainland feature mutations, {migrated_footprints} natural object footprints normalized, and {} authored natural/resource objects restored)",
                        CURRENT_CLIENT_GENERATION_VERSION,
                        pcg_surface_migration.marine_tiles_reclassified,
                        pcg_surface_migration.exterior_transitions_removed,
                        mainland_features.total_mutations(),
                        natural_objects.total_objects(),
                    );
                }
                let stale_exterior_transitions =
                    haven_world::strip_pcg_exterior_transitions(&mut world);
                if stale_exterior_transitions > 0 {
                    log.event(&format!(
                        "Removed {stale_exterior_transitions} obsolete PCG exterior edge transition(s)"
                    ));
                }
                log.event(&status);
                let replay_status = Self::replay_world_paint_deltas_into_world(
                    &mut world,
                    log,
                    &save_paths.world_paint_delta,
                    None,
                    "Startup saved-world paint delta replay",
                );
                (world, format!("{status}; {replay_status}"))
            }
            Err(save_err) => {
                let worldgen_pack_path = runtime_worldgen_pack_path();
                match load_worldgen_pack_from_path(&worldgen_pack_path) {
                    Ok((mut world, report)) => {
                        let status = format!(
                            "{}; no saved world loaded ({save_err})",
                            report.status_line()
                        );
                        log.event(&status);
                        for warning in &report.warnings {
                            log.event(&format!("Worldgen warning: {warning}"));
                        }
                        let _ = Self::apply_generated_coastline_cleanup(&mut world, log);
                        let replay_status = Self::replay_world_paint_deltas_into_world(
                            &mut world,
                            log,
                            &save_paths.world_paint_delta,
                            None,
                            "Startup worldgen paint delta replay",
                        );
                        (world, format!("{status}; {replay_status}"))
                    }
                    Err(pack_err) => {
                        let status = format!(
                            "Starter world active; save load failed ({save_err}); worldgen pack load failed ({pack_err})"
                        );
                        log.event(&status);
                        let mut world = GameWorld::starter();
                        let _ = Self::apply_generated_coastline_cleanup(&mut world, log);
                        let replay_status = Self::replay_world_paint_deltas_into_world(
                            &mut world,
                            log,
                            &save_paths.world_paint_delta,
                            None,
                            "Startup starter-world paint delta replay",
                        );
                        (world, format!("{status}; {replay_status}"))
                    }
                }
            }
        }
    }
    pub(crate) fn load_saved_layout(log: &mut GameLog) -> UiLayoutState {
        let layout_path = runtime_layout_path();
        match load_ui_layout_from_path(&layout_path) {
            Ok(layout) => {
                log.event("Loaded saved editor layout");
                layout
            }
            Err(err) => {
                log.event(&format!("Using default editor layout ({err})"));
                UiLayoutState::default()
            }
        }
    }
}
