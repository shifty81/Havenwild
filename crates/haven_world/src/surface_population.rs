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
    // AC3R4F idempotence: cached generated baselines may be reconciled more than
    // once as runtime asset/worldgen authority advances. Existing trees count
    // toward the deterministic floor so reconciliation never stacks duplicates.
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
            // building plot simply because its floor is still Grass.
            if scene.zone_at(x, y) != ZoneKind::None {
                continue;
            }
            let gx = chunk.x * MAP_W as i32 + x;
            let gy = chunk.y * MAP_H as i32 + y;
            // Z108: populate recognizable groves/forest belts with feathered
            // woodland edges and deterministic clearings. The habitat field is
            // a bounded macro feature, not a thresholded noise contour.
            let habitat = geographic_forest_habitat(habitat_seed, gx, gy);
            if tile == TileKind::Grass && habitat >= 0.52 {
                report.forest_habitat_cells += 1;
            }
            let distance_to_spawn = (x - scene.spawn_x).abs().max((y - scene.spawn_y).abs());
            if tile == TileKind::Grass && distance_to_spawn > 4 {
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

            let kind =
                if distance_to_spawn > 5 && tile == TileKind::MountainRock && ore_roll < 0.018 {
                    Some(ObjectKind::OreNode)
                } else if distance_to_spawn > 4
                    && matches!(
                        tile,
                        TileKind::MountainRock | TileKind::Dirt | TileKind::Grass
                    )
                    && boulder_roll
                        < if tile == TileKind::MountainRock {
                            0.052
                        } else {
                            0.006
                        }
                {
                    Some(ObjectKind::Boulder)
                } else if tile != TileKind::Grass {
                    None
                } else {
                    let roll = deterministic_cell_roll(object_seed, gx, gy, 0x4e41_5455);
                    if distance_to_spawn > 4
                        && roll < tree_spawn_chance(tree_density, habitat)
                    {
                        Some(ObjectKind::Tree)
                    } else {
                        let bush_roll = deterministic_cell_roll(object_seed, gx, gy, 0x4255_5348);
                        let flower_roll = deterministic_cell_roll(object_seed, gx, gy, 0x464c_4f57);
                        let mushroom_roll = deterministic_cell_roll(object_seed, gx, gy, 0x4d55_5348);
                        if distance_to_spawn > 2 && habitat > 0.28 && bush_roll < 0.025 {
                            Some(ObjectKind::Bush)
                        } else if flower_roll < if habitat < 0.18 { 0.030 } else { 0.052 } {
                            Some(ObjectKind::Herb)
                        } else if habitat > 0.58 && mushroom_roll < 0.014 {
                            Some(ObjectKind::Mushroom)
                        } else {
                            None
                        }
                    }
                };

            let Some(kind) = kind else {
                continue;
            };
            if matches!(kind, ObjectKind::Boulder | ObjectKind::OreNode)
                && !resource_footprint_is_compatible(scene, kind, x, y)
            {
                continue;
            }
            if scene.map.place_object(kind, x, y).is_none() {
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
    // AC3R4E ecology fail-safe: a normal grass partition must never be visually
    // treeless just because its probabilistic rolls happen to miss. The normal
    // habitat-driven pass above remains authoritative; this deterministic floor
    // only fills a severe deficit and therefore does not flatten grove/forest
    // clustering. Candidate order is seed/world-coordinate stable.
    let minimum_trees = minimum_partition_tree_count(eligible_field_tree_cells);
    if report.trees < minimum_trees {
        field_tree_floor_candidates.sort_by(|left, right| {
            left.0.total_cmp(&right.0)
                .then_with(|| left.2.cmp(&right.2))
                .then_with(|| left.1.cmp(&right.1))
        });
        for (_, x, y, habitat) in field_tree_floor_candidates {
            if report.trees >= minimum_trees {
                break;
            }
            if scene.map.place_object(ObjectKind::Tree, x, y).is_some() {
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

/// AC2 ecology closure: forest habitat controls clustering/density, not whether
/// trees are allowed to exist at all. The previous hard `habitat > 0.40` gate
/// produced enormous completely treeless grasslands whenever the player was
/// between finite grove patches. Dense grove cores remain strongly wooded,
/// shoulders thin naturally, and open grass receives sparse field trees.
fn tree_spawn_chance(tree_density: f32, habitat: f32) -> f32 {
    let density = tree_density.clamp(0.0, 0.22);
    let habitat = habitat.clamp(0.0, 1.0);
    // AC3R4D: ecology acceptance is player-visible, not merely nonzero. The
    // R4C meadow floor still worked out to only ~0.68% per eligible grass cell
    // on the mainland, which can leave multiple normal camera views completely
    // treeless. Preserve strong habitat clustering while guaranteeing sparse
    // but tangible field trees between grove/forest patches.
    let chance = if habitat >= 0.55 {
        density * (0.88 + habitat * 0.92)
    } else if habitat >= 0.18 {
        (0.020 + density * (0.30 + habitat * 0.55)).max(0.022)
    } else {
        0.015 + habitat * 0.035
    };
    chance.clamp(0.0, 0.32)
}

fn resource_footprint_is_compatible(scene: &SceneMap, kind: ObjectKind, x: i32, y: i32) -> bool {
    let object = PlacedObject::new(kind, x, y);
    let (cx, cy, cw, ch) = object.collision_rect();
    for fy in cy..cy + ch.max(1) {
        for fx in cx..cx + cw.max(1) {
            if scene.zone_at(fx, fy) != ZoneKind::None {
                return false;
            }
            let tile = scene.map.get(fx, fy);
            let compatible = match kind {
                ObjectKind::Boulder => {
                    matches!(
                        tile,
                        TileKind::Grass | TileKind::Dirt | TileKind::MountainRock
                    )
                }
                ObjectKind::OreNode => tile == TileKind::MountainRock,
                _ => true,
            };
            if !compatible {
                return false;
            }
        }
    }
    true
}

/// Restores deterministic natural/resource objects into older PCG saves that
/// were generated before authored surface population was enabled. Existing
/// natural or player-authored objects are never removed or duplicated.
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
        let region_seed = stable_region_seed(world_seed, &region);
        let report = populate_pcg_natural_objects_with_habitat_seed(
            scene,
            chunk,
            region_seed,
            world_seed,
            natural_object_density_for_region(&region),
        );
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

fn minimum_partition_tree_count(eligible_grass_cells: usize) -> usize {
    let mut minimum = eligible_grass_cells / 180;
    if eligible_grass_cells >= 256 {
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
mod ac2_ecology_tests {
    use super::*;

    #[test]
    fn open_grass_keeps_sparse_nonzero_tree_probability() {
        let open = tree_spawn_chance(natural_object_density_for_landmass(0), 0.0);
        let edge = tree_spawn_chance(natural_object_density_for_landmass(0), 0.30);
        let grove = tree_spawn_chance(natural_object_density_for_landmass(0), 0.80);
        assert!(open >= 0.015, "open meadow tree floor must remain visibly nonzero");
        assert!(edge > open);
        assert!(grove > edge);
    }

    #[test]
    fn ordinary_grass_partition_has_a_tangible_tree_floor() {
        assert_eq!(minimum_partition_tree_count(0), 0);
        assert_eq!(minimum_partition_tree_count(255), 1);
        assert_eq!(minimum_partition_tree_count(256), 6);
        assert!(minimum_partition_tree_count(2048) >= 11);
        assert_eq!(minimum_partition_tree_count(4096), 22);
    }

    #[test]
    fn deterministic_tree_floor_is_idempotent_when_baseline_is_reconciled_again() {
        let mut scene = SceneMap::blank(
            crate::pcg_surface_scene_id("mainland", ChunkCoord::new(0, 0)),
            "Tree idempotence",
            haven_core::SceneKind::Exterior,
            haven_core::SceneBiome::Temperate,
        );
        scene.map = haven_core::TavernMap::empty_with(TileKind::Grass);
        scene.spawn_x = MAP_W as i32 / 2;
        scene.spawn_y = MAP_H as i32 / 2;
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

}
