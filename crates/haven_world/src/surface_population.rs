use haven_core::{GameWorld, ObjectKind, PlacedObject, SceneMap, TileKind, ZoneKind, MAP_H, MAP_W};

use crate::{
    geographic_landforms::geographic_forest_habitat,
    mainland_features::MainlandFeatureReport,
    open_world::ChunkCoord,
    surface_world_plan::{materialize_mainland_world_plan_compatibility, SurfaceWorldPlanV1},
};

pub const fn natural_object_density_for_landmass(landmass_id: i32) -> f32 {
    if landmass_id == 0 {
        0.085
    } else {
        0.065
    }
}

pub fn natural_object_density_for_region(region: &str) -> f32 {
    if region.split('_').any(|part| part == "mainland") {
        natural_object_density_for_landmass(0)
    } else {
        natural_object_density_for_landmass(1)
    }
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct NaturalObjectPopulationReport {
    pub partitions_populated: usize,
    pub trees: usize,
    pub bushes: usize,
    pub herbs_and_flowers: usize,
    pub mushrooms: usize,
    pub forest_habitat_cells: usize,
    pub forest_trees: usize,
    pub boulders: usize,
    pub ore_nodes: usize,
    /// Legacy/generated natural objects removed because their footprint crossed
    /// a structural cliff/ramp/route boundary. This is repair telemetry only and
    /// is intentionally excluded from `total_objects()`.
    pub structural_conflicts_removed: usize,
}

impl NaturalObjectPopulationReport {
    pub const fn total_objects(self) -> usize {
        self.trees
            + self.bushes
            + self.herbs_and_flowers
            + self.mushrooms
            + self.boulders
            + self.ore_nodes
    }

    fn add(&mut self, other: Self) {
        self.partitions_populated += other.partitions_populated;
        self.trees += other.trees;
        self.bushes += other.bushes;
        self.herbs_and_flowers += other.herbs_and_flowers;
        self.mushrooms += other.mushrooms;
        self.forest_habitat_cells += other.forest_habitat_cells;
        self.forest_trees += other.forest_trees;
        self.boulders += other.boulders;
        self.ore_nodes += other.ore_nodes;
        self.structural_conflicts_removed += other.structural_conflicts_removed;
    }
}

/// Populates one PCG storage partition with deterministic authored natural
/// objects. Terrain remains the placement authority: trees, bushes, flowers,
/// herbs, mushrooms, boulders, and ore nodes are objects layered over compatible
/// ground, never replacement terrain tiles.
pub fn populate_pcg_natural_objects(
    scene: &mut SceneMap,
    chunk: ChunkCoord,
    seed: u64,
    tree_density: f32,
) -> NaturalObjectPopulationReport {
    populate_pcg_natural_objects_with_habitat_seed(scene, chunk, seed, seed, tree_density)
}

/// Variant used by continuous streamed regions. Object-variant rolls may keep a
/// region-specific seed, while the forest habitat itself must use the same
/// world-geography seed consumed by terrain and the Reveal-All map.
pub fn populate_pcg_natural_objects_with_habitat_seed(
    scene: &mut SceneMap,
    chunk: ChunkCoord,
    object_seed: u64,
    habitat_seed: u64,
    tree_density: f32,
) -> NaturalObjectPopulationReport {
    let mut report = NaturalObjectPopulationReport::default();

    // Idempotence: reconciliation may run more than once. Existing generated
    // trees count toward the deterministic floor so a repair/reconcile pass does
    // not stack a second forest on top of the first one.
    for object in &scene.map.objects {
        if object.kind == ObjectKind::Tree {
            report.trees += 1;
            let gx = chunk.x * MAP_W as i32 + object.x;
            let gy = chunk.y * MAP_H as i32 + object.y;
            if geographic_forest_habitat(habitat_seed, gx, gy) >= 0.52 {
                report.forest_trees += 1;
            }
        }
    }

    let tree_density = tree_density.clamp(0.0, 0.22);
    let mut eligible_field_tree_cells = 0usize;
    let mut field_tree_floor_candidates = Vec::<(f32, i32, i32, f32)>::new();

    for y in 0..MAP_H as i32 {
        for x in 0..MAP_W as i32 {
            let tile = scene.map.get(x, y);
            // City/harbor/agricultural reservations are semantic protected
            // areas. Ecology must never grow through a reserved Willowmere
            // building plot simply because its visible cap is grass-compatible.
            if scene.zone_at(x, y) != ZoneKind::None {
                continue;
            }
            let gx = chunk.x * MAP_W as i32 + x;
            let gy = chunk.y * MAP_H as i32 + y;
            let habitat = geographic_forest_habitat(habitat_seed, gx, gy);
            if tile == TileKind::Grass && habitat >= 0.52 {
                report.forest_habitat_cells += 1;
            }
            let distance_to_spawn = (x - scene.spawn_x).abs().max((y - scene.spawn_y).abs());

            // The floor only counts cells on which a complete mature tree can
            // actually stand. This prevents the minimum-tree pass from chasing
            // impossible cliff-edge/ramp/path candidates.
            if distance_to_spawn > 4
                && tree_surface_tile(tile)
                && natural_object_footprint_is_compatible(scene, ObjectKind::Tree, x, y)
            {
                eligible_field_tree_cells += 1;
                field_tree_floor_candidates.push((
                    deterministic_cell_roll(object_seed, gx, gy, 0x5452_4545_464c_4f4f),
                    x,
                    y,
                    habitat,
                ));
            }

            let boulder_roll = deterministic_cell_roll(object_seed, gx, gy, 0x424f_554c);
            let ore_roll = deterministic_cell_roll(object_seed, gx, gy, 0x4f52_454e);

            let kind = if distance_to_spawn > 5
                && tile == TileKind::MountainRock
                && ore_roll < 0.018
            {
                Some(ObjectKind::OreNode)
            } else if distance_to_spawn > 4
                && matches!(tile, TileKind::MountainRock | TileKind::Dirt | TileKind::Grass)
                && boulder_roll
                    < if tile == TileKind::MountainRock {
                        0.052
                    } else {
                        0.006
                    }
            {
                Some(ObjectKind::Boulder)
            } else if !tree_surface_tile(tile) {
                None
            } else {
                let roll = deterministic_cell_roll(object_seed, gx, gy, 0x4e41_5455);
                if distance_to_spawn > 4 && roll < tree_spawn_chance(tree_density, habitat) {
                    Some(ObjectKind::Tree)
                } else {
                    let bush_roll = deterministic_cell_roll(object_seed, gx, gy, 0x4255_5348);
                    let flower_roll = deterministic_cell_roll(object_seed, gx, gy, 0x464c_4f57);
                    let mushroom_roll = deterministic_cell_roll(object_seed, gx, gy, 0x4d55_5348);
                    if distance_to_spawn > 2
                        && habitat > 0.28
                        && bush_roll < if tile == TileKind::MountainRock { 0.010 } else { 0.025 }
                    {
                        Some(ObjectKind::Bush)
                    } else if tile == TileKind::Grass
                        && flower_roll < if habitat < 0.18 { 0.030 } else { 0.052 }
                    {
                        Some(ObjectKind::Herb)
                    } else if tile == TileKind::Grass && habitat > 0.58 && mushroom_roll < 0.014 {
                        Some(ObjectKind::Mushroom)
                    } else {
                        None
                    }
                }
            };

            let Some(kind) = kind else {
                continue;
            };
            if !natural_object_footprint_is_compatible(scene, kind, x, y) {
                continue;
            }
            if !place_generated_natural_object(scene, kind, x, y) {
                continue;
            }
            match kind {
                ObjectKind::Tree => {
                    report.trees += 1;
                    if habitat >= 0.52 {
                        report.forest_trees += 1;
                    }
                }
                ObjectKind::Bush => report.bushes += 1,
                ObjectKind::Herb => report.herbs_and_flowers += 1,
                ObjectKind::Mushroom => report.mushrooms += 1,
                ObjectKind::Boulder => report.boulders += 1,
                ObjectKind::OreNode => report.ore_nodes += 1,
                _ => {}
            }
        }
    }

    // A normal ecology partition must never be visually treeless just because
    // its random rolls miss. Candidate order is deterministic and every candidate
    // has already passed complete-footprint structural clearance.
    let minimum_trees = minimum_partition_tree_count(eligible_field_tree_cells);
    if report.trees < minimum_trees {
        field_tree_floor_candidates.sort_by(|left, right| {
            left.0
                .total_cmp(&right.0)
                .then_with(|| left.2.cmp(&right.2))
                .then_with(|| left.1.cmp(&right.1))
        });
        for (_, x, y, habitat) in field_tree_floor_candidates {
            if report.trees >= minimum_trees {
                break;
            }
            if place_generated_natural_object(scene, ObjectKind::Tree, x, y) {
                report.trees += 1;
                if habitat >= 0.52 {
                    report.forest_trees += 1;
                }
            }
        }
    }

    if report.total_objects() > 0 {
        report.partitions_populated = 1;
    }
    report
}

/// Forest habitat controls clustering/density, not whether trees can exist at
/// all. Sparse field trees remain possible outside grove cores, while elevated
/// grass-capped MountainRock can carry highland ecology when the complete
/// structural footprint is safe.
fn tree_spawn_chance(tree_density: f32, habitat: f32) -> f32 {
    let density = tree_density.clamp(0.0, 0.22);
    let habitat = habitat.clamp(0.0, 1.0);
    let chance = if habitat >= 0.55 {
        density * (0.88 + habitat * 0.92)
    } else if habitat >= 0.18 {
        (0.020 + density * (0.30 + habitat * 0.55)).max(0.022)
    } else {
        0.015 + habitat * 0.035
    };
    chance.clamp(0.0, 0.32)
}

fn tree_surface_tile(tile: TileKind) -> bool {
    matches!(tile, TileKind::Grass | TileKind::MountainRock)
}

fn natural_object_kind(kind: ObjectKind) -> bool {
    matches!(
        kind,
        ObjectKind::Tree
            | ObjectKind::Bush
            | ObjectKind::Herb
            | ObjectKind::Mushroom
            | ObjectKind::Boulder
            | ObjectKind::OreNode
    )
}

fn natural_ground_compatible(kind: ObjectKind, anchor_tile: TileKind, tile: TileKind) -> bool {
    match kind {
        ObjectKind::Tree | ObjectKind::Bush => {
            if anchor_tile == TileKind::MountainRock {
                tile == TileKind::MountainRock
            } else {
                matches!(tile, TileKind::Grass | TileKind::TallGrass)
            }
        }
        ObjectKind::Herb | ObjectKind::Mushroom => {
            matches!(tile, TileKind::Grass | TileKind::TallGrass)
        }
        ObjectKind::Boulder => {
            matches!(tile, TileKind::Grass | TileKind::Dirt | TileKind::MountainRock)
        }
        ObjectKind::OreNode => tile == TileKind::MountainRock,
        _ => false,
    }
}

fn structural_clearance_forbidden_tile(tile: TileKind) -> bool {
    tile.is_water()
        || matches!(
            tile,
            TileKind::Road
                | TileKind::StonePath
                | TileKind::MountainPath
                | TileKind::Bridge
                | TileKind::Cliff
                | TileKind::Wall
                | TileKind::CaveWall
                | TileKind::Sand
                | TileKind::WetSand
                | TileKind::PebbleShore
                | TileKind::MudBank
                | TileKind::ShoreFoam
        )
}

/// PCG natural objects are validated against their entire authored footprint,
/// not just the anchor tile. Mature trees additionally keep a one-cell halo from
/// structural drops and route/ramp semantics so a 3x4 canopy/trunk cannot hang
/// across a cliff face even when its foot happens to stand on valid ground.
fn natural_object_footprint_is_compatible(
    scene: &SceneMap,
    kind: ObjectKind,
    x: i32,
    y: i32,
) -> bool {
    if !natural_object_kind(kind)
        || x < 0
        || y < 0
        || x >= MAP_W as i32
        || y >= MAP_H as i32
        || scene.zone_at(x, y) != ZoneKind::None
    {
        return false;
    }

    let object = PlacedObject::new(kind, x, y);
    let anchor_tile = scene.map.get(x, y);
    let anchor_level = crate::structural_level_for_surface_recipe_v1(&scene.map, x, y);
    // Use the complete authored visual envelope for every generated natural.
    // This matters for multi-cell boulder variants as well as mature trees: a
    // one-cell collision anchor is not enough to prove the artwork belongs on
    // one structural surface.
    let footprint = object.visual_rect();
    let (fx0, fy0, fw, fh) = footprint;

    for fy in fy0..fy0 + fh.max(1) {
        for fx in fx0..fx0 + fw.max(1) {
            if fx < 0 || fy < 0 || fx >= MAP_W as i32 || fy >= MAP_H as i32 {
                return false;
            }
            if scene.zone_at(fx, fy) != ZoneKind::None {
                return false;
            }
            let tile = scene.map.get(fx, fy);
            if !natural_ground_compatible(kind, anchor_tile, tile)
                || structural_clearance_forbidden_tile(tile)
                || crate::structural_level_for_surface_recipe_v1(&scene.map, fx, fy) != anchor_level
            {
                return false;
            }
        }
    }

    // Blocking natural objects keep a one-cell structural/route halo. Herbs and
    // mushrooms are intentionally pass-through and may grow close to safe edges,
    // but never on an incompatible anchor/footprint above.
    if matches!(
        kind,
        ObjectKind::Tree | ObjectKind::Bush | ObjectKind::Boulder | ObjectKind::OreNode
    ) {
        for hy in fy0 - 1..=fy0 + fh {
            for hx in fx0 - 1..=fx0 + fw {
                if hx < 0 || hy < 0 || hx >= MAP_W as i32 || hy >= MAP_H as i32 {
                    continue;
                }
                if scene.zone_at(hx, hy) != ZoneKind::None {
                    return false;
                }
                let tile = scene.map.get(hx, hy);
                if structural_clearance_forbidden_tile(tile)
                    || crate::structural_level_for_surface_recipe_v1(&scene.map, hx, hy)
                        != anchor_level
                {
                    return false;
                }
            }
        }
    }

    true
}

/// `TavernMap::place_object` applies building-support rules to all blocking
/// objects. That is correct for furniture/buildings but rejects legitimate trees,
/// boulders, and ore on walkable elevated MountainRock. PCG therefore performs
/// its explicit ecology/structure preflight above, then uses the custom-object
/// path only after overlap and bounds validation have succeeded. No overlapping
/// object is removed because the preflight must be clean first.
fn place_generated_natural_object(scene: &mut SceneMap, kind: ObjectKind, x: i32, y: i32) -> bool {
    if !natural_object_footprint_is_compatible(scene, kind, x, y) {
        return false;
    }
    let placed = PlacedObject::new(kind, x, y);
    let mut preflight = placed;
    preflight.footprint.blocks_movement = false;
    if !scene.map.can_place_custom_object(preflight) {
        return false;
    }
    scene.map.place_custom_object(placed).is_some()
}

fn repair_generated_natural_object_structural_conflicts(scene: &mut SceneMap) -> usize {
    let invalid = scene
        .map
        .objects
        .iter()
        .enumerate()
        .filter_map(|(index, object)| {
            // Stable/pack-defined refs are authored content. This repair is for
            // generated legacy naturals only and must not silently rewrite editor
            // or content-pack placement.
            if scene.map.object_asset_ref(object.id).is_some()
                || !natural_object_kind(object.kind)
                || natural_object_footprint_is_compatible(scene, object.kind, object.x, object.y)
            {
                None
            } else {
                Some(index)
            }
        })
        .collect::<Vec<_>>();
    let removed = invalid.len();
    for index in invalid.into_iter().rev() {
        let _ = scene.map.remove_object_index(index);
    }
    removed
}

/// Reconciles deterministic natural/resource objects in older PCG saves.
/// Stable/pack-referenced authored objects are preserved. Unreferenced legacy
/// naturals whose complete visual footprint now conflicts with structural
/// terrain are removed before deterministic ecology is filled back in.
pub fn populate_missing_pcg_natural_objects(
    world: &mut GameWorld,
    world_seed: u64,
) -> NaturalObjectPopulationReport {
    let targets = world
        .scenes
        .iter()
        .filter_map(|scene| {
            let (region, chunk) = crate::parse_pcg_surface_scene_id(&scene.id)?;
            Some((scene.id.clone(), region, chunk))
        })
        .collect::<Vec<_>>();

    let mut total = NaturalObjectPopulationReport::default();
    for (scene_id, region, chunk) in targets {
        let Some(scene) = world.scene_mut_by_id(&scene_id) else {
            continue;
        };
        let removed = repair_generated_natural_object_structural_conflicts(scene);
        let region_seed = stable_region_seed(world_seed, &region);
        let mut report = populate_pcg_natural_objects_with_habitat_seed(
            scene,
            chunk,
            region_seed,
            world_seed,
            natural_object_density_for_region(&region),
        );
        report.structural_conflicts_removed = removed;
        total.add(report);
    }
    total
}

/// Materializes missing Willowmere roads, civic foundations, and a cave host
/// into an existing mainland PCG save. Existing road layouts are preserved.
pub fn populate_missing_pcg_mainland_features(
    world: &mut GameWorld,
    world_seed: u64,
) -> Result<MainlandFeatureReport, String> {
    let targets = world
        .scenes
        .iter()
        .filter_map(|scene| {
            let (region, chunk) = crate::parse_pcg_surface_scene_id(&scene.id)?;
            region
                .split('_')
                .any(|part| part == "mainland")
                .then(|| (scene.id.clone(), chunk))
        })
        .collect::<Vec<_>>();
    if targets.is_empty() {
        return Ok(MainlandFeatureReport::default());
    }

    let mut scenes = targets
        .iter()
        .filter_map(|(scene_id, _)| world.scene_by_id(scene_id).cloned())
        .collect::<Vec<_>>();
    let chunks = targets.iter().map(|(_, chunk)| *chunk).collect::<Vec<_>>();
    if scenes.len() != targets.len() {
        return Err("mainland feature migration lost a PCG scene during collection".to_string());
    }
    let harbor_index = chunks
        .iter()
        .enumerate()
        .max_by_key(|(_, chunk)| (chunk.y, -chunk.x.abs()))
        .map(|(index, _)| index)
        .unwrap_or(0);
    let harbor_id = scenes
        .get(harbor_index)
        .map(|scene| scene.id.clone())
        .ok_or_else(|| {
            "mainland feature migration could not identify a harbor partition".to_string()
        })?;
    let world_plan = SurfaceWorldPlanV1::build(
        0,
        "Alderreach",
        "havenwild_mainland",
        world_seed,
        chunks.clone(),
        harbor_id,
    )?;
    let highland_repairs = crate::materialize_highland_shoulders(&mut scenes, &chunks)?;
    let mut report = materialize_mainland_world_plan_compatibility(
        &world_plan,
        &mut scenes,
        true,
    )?;
    report.repaired_legacy_tiles += highland_repairs;
    for ((scene_id, _), replacement) in targets.iter().zip(scenes) {
        if let Some(scene) = world.scene_mut_by_id(scene_id) {
            *scene = replacement;
        }
    }
    Ok(report)
}

fn minimum_partition_tree_count(eligible_surface_cells: usize) -> usize {
    let mut minimum = eligible_surface_cells / 180;
    if eligible_surface_cells >= 256 {
        minimum = minimum.max(6);
    }
    minimum.min(24)
}

fn deterministic_cell_roll(seed: u64, x: i32, y: i32, salt: u64) -> f32 {
    let mut value = seed ^ salt;
    value ^= (x as i64 as u64).wrapping_mul(0x9e37_79b9_7f4a_7c15);
    value = value.rotate_left(21);
    value ^= (y as i64 as u64).wrapping_mul(0xc2b2_ae3d_27d4_eb4f);
    value ^= value >> 30;
    value = value.wrapping_mul(0xbf58_476d_1ce4_e5b9);
    value ^= value >> 27;
    value = value.wrapping_mul(0x94d0_49bb_1331_11eb);
    value ^= value >> 31;
    (value as f64 / u64::MAX as f64) as f32
}

fn stable_region_seed(world_seed: u64, region: &str) -> u64 {
    let mut value = world_seed ^ 0x5245_4749_4f4e;
    for byte in region.bytes() {
        value ^= byte as u64;
        value = value.wrapping_mul(0x100_0000_01b3);
    }
    value
}

#[cfg(test)]
mod structural_natural_population_tests {
    use super::*;

    fn grass_scene() -> SceneMap {
        let mut scene = SceneMap::blank(
            crate::pcg_surface_scene_id("mainland", ChunkCoord::new(0, 0)),
            "Natural placement test",
            haven_core::SceneKind::Exterior,
            haven_core::SceneBiome::Temperate,
        );
        scene.map = haven_core::TavernMap::empty_with(TileKind::Grass);
        scene.spawn_x = MAP_W as i32 / 2;
        scene.spawn_y = MAP_H as i32 / 2;
        scene
    }

    #[test]
    fn mature_tree_rejects_visual_footprint_crossing_structural_drop() {
        let mut scene = grass_scene();
        let anchor = (20, 20);
        // Make the tree's exact 3x4 visual footprint Level 2, but leave the
        // surrounding halo Level 0. The anchor is valid grass, yet the mature
        // tree would sit directly on a cliff boundary and must be rejected.
        for y in anchor.1 - 3..=anchor.1 {
            for x in anchor.0 - 1..=anchor.0 + 1 {
                scene.map.set_structural_level(x, y, Some(2));
            }
        }
        assert!(!natural_object_footprint_is_compatible(
            &scene,
            ObjectKind::Tree,
            anchor.0,
            anchor.1,
        ));
    }

    #[test]
    fn mature_tree_accepts_safe_same_level_plateau_interior() {
        let mut scene = grass_scene();
        let anchor = (20, 20);
        for y in anchor.1 - 4..=anchor.1 + 1 {
            for x in anchor.0 - 2..=anchor.0 + 2 {
                scene.map.set_structural_level(x, y, Some(2));
            }
        }
        assert!(natural_object_footprint_is_compatible(
            &scene,
            ObjectKind::Tree,
            anchor.0,
            anchor.1,
        ));
    }

    #[test]
    fn mountain_path_inside_tree_clearance_rejects_tree() {
        let mut scene = grass_scene();
        let anchor = (20, 20);
        scene.map.set(18, 20, TileKind::MountainPath);
        assert!(!natural_object_footprint_is_compatible(
            &scene,
            ObjectKind::Tree,
            anchor.0,
            anchor.1,
        ));
    }

    #[test]
    fn generated_repair_removes_only_unreferenced_structural_conflicts() {
        let mut scene = grass_scene();
        let bad = scene.map.place_object(ObjectKind::Tree, 20, 20).expect("tree");
        // The tree anchor stays level 0 while one canopy cell is raised, making
        // the generated placement structurally invalid.
        scene.map.set_structural_level(20, 18, Some(2));
        let removed = repair_generated_natural_object_structural_conflicts(&mut scene);
        assert_eq!(removed, 1);
        assert!(scene.map.object(bad).is_none());
    }

    #[test]
    fn highland_mountainrock_is_an_ecology_surface_when_structurally_safe() {
        let mut scene = grass_scene();
        let anchor = (24, 24);
        for y in anchor.1 - 4..=anchor.1 + 1 {
            for x in anchor.0 - 2..=anchor.0 + 2 {
                scene.map.set(x, y, TileKind::MountainRock);
                scene.map.set_structural_level(x, y, Some(2));
            }
        }
        assert!(natural_object_footprint_is_compatible(
            &scene,
            ObjectKind::Tree,
            anchor.0,
            anchor.1,
        ));
        assert!(place_generated_natural_object(
            &mut scene,
            ObjectKind::Tree,
            anchor.0,
            anchor.1,
        ));
    }

    #[test]
    fn deterministic_tree_floor_is_idempotent_when_baseline_is_reconciled_again() {
        let mut scene = grass_scene();
        let first = populate_pcg_natural_objects_with_habitat_seed(
            &mut scene,
            ChunkCoord::new(0, 0),
            0x1234,
            0x5678,
            natural_object_density_for_landmass(0),
        );
        let object_count = scene.map.objects.len();
        let second = populate_pcg_natural_objects_with_habitat_seed(
            &mut scene,
            ChunkCoord::new(0, 0),
            0x1234,
            0x5678,
            natural_object_density_for_landmass(0),
        );
        assert!(first.trees >= minimum_partition_tree_count((MAP_W * MAP_H) - 81));
        assert_eq!(scene.map.objects.len(), object_count);
        assert_eq!(second.trees, first.trees);
    }

    #[test]
    fn ecology_probability_and_floor_remain_tangible() {
        let open = tree_spawn_chance(natural_object_density_for_landmass(0), 0.0);
        let edge = tree_spawn_chance(natural_object_density_for_landmass(0), 0.30);
        let grove = tree_spawn_chance(natural_object_density_for_landmass(0), 0.80);
        assert!(open >= 0.015);
        assert!(edge > open);
        assert!(grove > edge);
        assert_eq!(minimum_partition_tree_count(255), 1);
        assert_eq!(minimum_partition_tree_count(256), 6);
        assert_eq!(minimum_partition_tree_count(4096), 22);
    }
}

