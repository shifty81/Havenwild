use std::collections::BTreeSet;
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};

use haven_assets::asset_registry::audited_object_footprint_for_cell;
use haven_core::{GameWorld, SceneReference};
use haven_save::{
    delete_world_save, load_or_create_world_social_state, save_chunk_manifest_to_path,
    save_world_save_metadata, save_world_to_path, save_world_topology_to_path, world_save_paths,
    ChunkManifest, ClientSavePaths, WorldSaveId, WorldSaveMetadata,
};
use haven_world::{
    archipelago_layout::generate_archipelago_layout,
    export_archipelago_preview,
    island_pcg::{generate_landmass, IslandGenerationSettings},
    scene_rectangles::{SceneRectangleManifest, SCENE_RECTANGLE_MANIFEST_PATH},
    build_semantic_world_bake_v1, save_semantic_world_bake_v1_to_path,
    save_world_creation_settings_to_path, GeographicGenerationProfile, HorizontalWrapMode,
    VerticalBoundaryMode, WorldCreationSettings, WorldTopologyConfig, WorldTopologyExtent,
    CLIENT_ARCHIPELAGO_PREVIEW_FILENAME, SEMANTIC_WORLD_BAKE_RELATIVE_PATH,
};

use crate::runtime_config::runtime_asset_path;

pub(crate) fn suggested_world_seed(world_id: &WorldSaveId) -> u64 {
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_nanos() as u64)
        .unwrap_or(1);
    let salt = world_id
        .0
        .bytes()
        .fold(0_u64, |value, byte| value.rotate_left(5) ^ u64::from(byte));
    splitmix64(now ^ salt).max(1)
}

#[allow(dead_code)]
pub(crate) fn create_seeded_world_save(
    base_root: &str,
    world_id: WorldSaveId,
    display_name: impl Into<String>,
    seed: u64,
) -> Result<WorldSaveMetadata, String> {
    let settings = WorldCreationSettings {
        display_name: display_name.into(),
        seed,
        ..Default::default()
    };
    create_seeded_world_save_with_settings(base_root, world_id, settings)
}

pub(crate) fn create_seeded_world_save_with_settings(
    base_root: &str,
    world_id: WorldSaveId,
    settings: WorldCreationSettings,
) -> Result<WorldSaveMetadata, String> {
    settings.validate()?;
    let paths = world_save_paths(base_root, &world_id)?;
    if Path::new(&paths.root).exists() {
        return Err(format!("world {} already exists", world_id.0));
    }
    paths.ensure_directories()?;
    let result = create_seeded_world_save_inner(&paths, world_id.clone(), &settings);
    if result.is_err() {
        let _ = delete_world_save(base_root, &world_id);
    }
    result
}

fn create_seeded_world_save_inner(
    paths: &ClientSavePaths,
    world_id: WorldSaveId,
    settings: &WorldCreationSettings,
) -> Result<WorldSaveMetadata, String> {
    let seed = settings.seed;
    let display_name = settings.display_name.clone();
    let source_manifest = runtime_asset_path(SCENE_RECTANGLE_MANIFEST_PATH);
    let mut manifest = SceneRectangleManifest::load_from_path(&source_manifest)?;
    generate_archipelago_layout(&mut manifest, seed)?;

    let landmass_ids: BTreeSet<i32> = manifest
        .scene_rectangles
        .iter()
        .filter(|rectangle| rectangle.grid_x.is_some() && rectangle.grid_y.is_some())
        .map(|rectangle| rectangle.landmass_id)
        .collect();
    let geography_profile = GeographicGenerationProfile::from_world_creation(settings);
    let generated_island_count = if geography_profile.finite_world
        && geography_profile.landform == haven_world::LandformPreset::Archipelago
    {
        haven_world::ArchipelagoSkeleton::for_geographic_profile(seed, geography_profile)
            .landmasses
            .len()
    } else {
        landmass_ids.len()
    };
    let generated_exterior_scene_count = manifest
        .scene_rectangles
        .iter()
        .filter(|rectangle| rectangle.grid_x.is_some() && rectangle.grid_y.is_some())
        .count();

    let mut world = GameWorld::starter();
    let mut mainland_start: Option<SceneReference> = None;
    let mut willowmere_center: Option<[i32; 2]> = None;
    for landmass_id in landmass_ids {
        let generated = generate_landmass(
            &manifest,
            landmass_id,
            IslandGenerationSettings {
                // The mainland must use the exact world seed because runtime
                // streaming samples the same global geographic field. Minor
                // islands retain their independent legacy seed lanes.
                seed: if landmass_id == 0 {
                    seed
                } else {
                    island_seed(seed, landmass_id)
                },
                mountain_radius: if landmass_id == 0 {
                    settings.mountain_radius_hint()
                } else {
                    (settings.mountain_radius_hint() * 0.72).clamp(0.20, 0.62)
                },
                shoreline_width: settings.shoreline_width_hint(),
                tree_density: haven_world::island_pcg::natural_object_density_for_landmass(
                    landmass_id,
                ),
                geography: geography_profile,
            },
        )?;
        if landmass_id == 0 {
            mainland_start = Some(SceneReference::from(generated.harbor_scene_id.clone()));
            willowmere_center = generated.mainland_features.willowmere_center;
        }
        for generated_scene in generated.scenes {
            let mut scene = generated_scene.scene;
            for object in &mut scene.map.objects {
                object.footprint =
                    audited_object_footprint_for_cell(object.kind, object.x, object.y);
            }
            world.insert_scene(scene)?;
        }
    }

    let starting_scene_code = mainland_start
        .as_ref()
        .map(|reference| reference.code().to_string())
        .unwrap_or_default();
    if let Some(start) = mainland_start {
        world.set_active_scene(start)?;
    }

    manifest.save_to_path(&paths.scene_manifest)?;
    save_world_to_path(&paths.world, &world)?;
    if let Some(center) = willowmere_center {
        crate::client_save_generation_city::write_willowmere_worldgen_buildings(
            &paths.root,
            &world_id.0,
            &starting_scene_code,
            center,
        )?;
    }
    let preview_path =
        std::path::Path::new(&paths.previews).join(CLIENT_ARCHIPELAGO_PREVIEW_FILENAME);
    export_archipelago_preview(&manifest, &world, &preview_path.to_string_lossy())?;

    let mut metadata =
        WorldSaveMetadata::new(world_id.clone(), display_name, seed, world.scenes.len());
    metadata.generated_exterior_scene_count = generated_exterior_scene_count;
    metadata.generated_island_count = generated_island_count;
    metadata.starting_scene_code = starting_scene_code;
    let [width, height] = settings.world_dimensions_tiles();
    metadata.world_width_tiles = width as i32;
    metadata.world_height_tiles = height as i32;
    metadata.world_chunk_size_tiles = settings.chunk_size_tiles as i32;
    metadata.world_wrap_east_west = false;

    let topology = WorldTopologyConfig {
        schema: haven_world::WORLD_TOPOLOGY_SCHEMA.to_string(),
        extent: if settings.is_endless() {
            WorldTopologyExtent::Endless
        } else {
            WorldTopologyExtent::Finite
        },
        width_tiles: width as i32,
        height_tiles: height as i32,
        // Keep the starter harbor near the southern part of a finite world
        // while leaving the majority of the mainland available to the north.
        // Both origins remain 64-tile aligned.
        origin_x_tiles: if settings.is_endless() { 0 } else { -(width as i32) / 2 },
        origin_y_tiles: if settings.is_endless() { 0 } else { 512 - height as i32 },
        chunk_size_tiles: settings.chunk_size_tiles as i32,
        horizontal_wrap: HorizontalWrapMode::Disabled,
        vertical_boundary: VerticalBoundaryMode::Clamped,
    };
    save_world_topology_to_path(&paths.world_topology, &topology)?;
    save_world_creation_settings_to_path(&paths.world_creation_settings, settings)?;

    // H20V2B1: finite New Game resolves and persists the complete low-LOD
    // world authority before success is reported. Detailed partitions may still
    // stream later, but their islands/rivers/cliffs/forests are no longer first
    // decided when the player reaches them.
    if geography_profile.finite_world {
        let mut semantic_bake = build_semantic_world_bake_v1(seed, geography_profile)
            .ok_or_else(|| "finite world semantic bake could not be constructed".to_string())?;
        if let Some([world_x, world_y]) = willowmere_center {
            if !semantic_bake
                .landmarks
                .iter()
                .any(|landmark| landmark.label.eq_ignore_ascii_case("Willowmere"))
            {
                semantic_bake.landmarks.push(haven_world::SemanticWorldBakeLandmarkV1 {
                    world_x,
                    world_y,
                    label: "Willowmere".to_string(),
                    capital: true,
                });
            }
        }
        let semantic_bake_path = Path::new(&paths.root).join(SEMANTIC_WORLD_BAKE_RELATIVE_PATH);
        save_semantic_world_bake_v1_to_path(&semantic_bake_path, &semantic_bake)?;
    }
    let _ = load_or_create_world_social_state(Path::new(&paths.root), world_id.0.clone())?;

    let chunk_manifest = ChunkManifest::new(seed, metadata.generation_version);
    save_chunk_manifest_to_path(&paths.chunk_manifest, &chunk_manifest)?;
    save_world_save_metadata(&paths.metadata, &metadata)?;
    Ok(metadata)
}

fn island_seed(world_seed: u64, landmass_id: i32) -> u64 {
    splitmix64(world_seed ^ (landmass_id as i64 as u64).wrapping_mul(0x9e37_79b9_7f4a_7c15))
}

fn splitmix64(mut value: u64) -> u64 {
    value = value.wrapping_add(0x9e37_79b9_7f4a_7c15);
    value = (value ^ (value >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
    value = (value ^ (value >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
    value ^ (value >> 31)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn suggested_seed_is_nonzero() {
        assert_ne!(
            suggested_world_seed(&WorldSaveId("world_test".to_string())),
            0
        );
    }

    #[test]
    fn island_seeds_are_stable_and_distinct() {
        assert_eq!(island_seed(1_337, 2), island_seed(1_337, 2));
        assert_ne!(island_seed(1_337, 1), island_seed(1_337, 2));
    }
}
