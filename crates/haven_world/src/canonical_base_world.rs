//! Shared deterministic materialization for a new Havenwild world foundation.
//! The editor uses the result once to create its authored Base World; New World
//! uses the same generator and subsequently owns an independent player save.
use std::collections::BTreeSet;

use haven_core::{GameWorld, ProjectSceneId, SceneRegistry};

use crate::{
    island_pcg::{generate_landmass, IslandGenerationSettings},
    scene_rectangles::SceneRectangleManifest,
    GeographicGenerationProfile, WorldCreationSettings,
};

pub const CANONICAL_BASE_WORLD_RELATIVE_PATH: &str =
    "content/worldgen/dev_worlds/core_dev_001/world.tworld";
pub const CANONICAL_BASE_WORLD_DESCRIPTOR_PATH: &str =
    "content/worldgen/dev_worlds/core_dev_001/development_world.json";

pub struct MaterializedBaseWorld {
    pub world: GameWorld,
    pub starting_scene: ProjectSceneId,
    pub willowmere_center: Option<[i32; 2]>,
}

pub fn materialize_base_world(
    manifest: &SceneRectangleManifest,
    settings: &WorldCreationSettings,
) -> Result<MaterializedBaseWorld, String> {
    settings.validate()?;
    let landmass_ids: BTreeSet<i32> = manifest.scene_rectangles.iter()
        .filter(|entry| entry.grid_x.is_some() && entry.grid_y.is_some())
        .map(|entry| entry.landmass_id).collect();
    if !landmass_ids.contains(&0) {
        return Err("Base World manifest has no Alderreach mainland".to_string());
    }
    let geography = GeographicGenerationProfile::from_world_creation(settings);
    let mut world = GameWorld::starter();
    // Retain the established tile rules without misrepresenting the nine
    // historical compatibility scenes as authored Havenwild world content.
    world.scenes = SceneRegistry::new();
    let mut starting_scene = None;
    let mut willowmere_center = None;
    for landmass_id in landmass_ids {
        let generated = generate_landmass(manifest, landmass_id, IslandGenerationSettings {
            seed: if landmass_id == 0 { settings.seed } else {
                island_seed(settings.seed, landmass_id)
            },
            mountain_radius: if landmass_id == 0 { settings.mountain_radius_hint() } else {
                (settings.mountain_radius_hint() * 0.72).clamp(0.20, 0.62)
            },
            shoreline_width: settings.shoreline_width_hint(),
            tree_density: crate::island_pcg::natural_object_density_for_landmass(landmass_id),
            geography,
        })?;
        if landmass_id == 0 {
            starting_scene = Some(generated.harbor_scene_id.clone());
            willowmere_center = generated.mainland_features.willowmere_center;
        }
        for generated_scene in generated.scenes {
            world.insert_scene(generated_scene.scene)?;
        }
    }
    let starting_scene = starting_scene.ok_or_else(||
        "Base World generation produced no mainland harbor".to_string())?;
    world.set_active_scene(starting_scene.clone())?;
    Ok(MaterializedBaseWorld { world, starting_scene, willowmere_center })
}

fn island_seed(world_seed: u64, landmass_id: i32) -> u64 {
    let mut value = world_seed ^ (landmass_id as i64 as u64).wrapping_mul(0x9e37_79b9_7f4a_7c15);
    value = value.wrapping_add(0x9e37_79b9_7f4a_7c15);
    value = (value ^ (value >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
    value = (value ^ (value >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
    value ^ (value >> 31)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn island_seed_is_deterministic_and_distinct() {
        assert_eq!(island_seed(1337, 2), island_seed(1337, 2));
        assert_ne!(island_seed(1337, 1), island_seed(1337, 2));
    }
    #[test]
    fn missing_mainland_fails_closed() {
        let manifest = SceneRectangleManifest::load_from_path(
            &format!("{}/../../content/worldgen/scene_rectangle_manifest_v0_8.json", env!("CARGO_MANIFEST_DIR"))
        ).expect("checked-in manifest");
        let mut without_mainland = manifest;
        without_mainland.scene_rectangles.retain(|entry| entry.landmass_id != 0);
        assert!(materialize_base_world(&without_mainland, &WorldCreationSettings::default())
            .err().expect("must fail").contains("no Alderreach mainland"));
    }
}
