//! Save-local materialization of Willowmere's first visible building block.
//!
//! The mainland feature pass owns roads, plaza, plots, harbor, and the chosen
//! global capital center. This adapter turns those reservations into ordinary
//! save-backed ContinuousSurface BuildingInstances so runtime, interiors,
//! persistence, and later player edits all consume the existing building
//! authority instead of a city-specific renderer.

use std::collections::{BTreeMap, BTreeSet};
use std::fs::{create_dir_all, read_to_string, write};
use std::path::Path;

use haven_assets::building_instance::{
    BuildingInstanceDefinition, BuildingInstanceOrigin, BuildingInstanceWorldStateFile,
    BuildingPlacementSpace, BUILDING_INSTANCE_SCHEMA, BUILDING_INSTANCE_WORLD_STATE_PASS,
    BUILDING_INSTANCE_WORLD_STATE_SCHEMA,
};

const MAINLAND_REGION: &str = "havenwild_mainland";

pub(crate) fn write_willowmere_worldgen_buildings(
    save_root: &str,
    world_id: &str,
    source_scene_id: &str,
    center: [i32; 2],
) -> Result<usize, String> {
    let upserts = willowmere_building_instances(source_scene_id, center);
    let document = BuildingInstanceWorldStateFile {
        schema: BUILDING_INSTANCE_WORLD_STATE_SCHEMA.to_string(),
        pass: BUILDING_INSTANCE_WORLD_STATE_PASS.to_string(),
        world_id: world_id.to_string(),
        revision: 1,
        upserts,
        removed_instance_ids: Vec::new(),
        instance_states: Vec::new(),
    };
    let payload = serde_json::to_string_pretty(&document).map_err(|error| error.to_string())?;
    let path = building_state_path(save_root);
    if let Some(parent) = path.parent() {
        create_dir_all(parent).map_err(|error| format!("{}: {error}", parent.display()))?;
    }
    write(&path, format!("{payload}\n"))
        .map_err(|error| format!("{}: {error}", path.display()))?;
    Ok(document.upserts.len())
}

/// Reconcile only the generated Willowmere slice of an existing world-state
/// overlay. Player/authored/non-Willowmere upserts, persistent states and
/// tombstones remain authoritative. A tombstoned Willowmere id is not
/// resurrected. Persistent state is retained when a building keeps the same
/// recipe, and dropped only when this migration replaces that recipe (for
/// example the retired diagnostic civic prototype).
pub(crate) fn reconcile_willowmere_worldgen_buildings(
    save_root: &str,
    world_id: &str,
    source_scene_id: &str,
    center: [i32; 2],
) -> Result<usize, String> {
    let path = building_state_path(save_root);
    let desired = willowmere_building_instances(source_scene_id, center);
    let desired_by_id = desired
        .into_iter()
        .map(|definition| (definition.id.clone(), definition))
        .collect::<BTreeMap<_, _>>();

    let mut document = if path.exists() {
        serde_json::from_str::<BuildingInstanceWorldStateFile>(
            &read_to_string(&path).map_err(|error| format!("{}: {error}", path.display()))?,
        )
        .map_err(|error| format!("{}: {error}", path.display()))?
    } else {
        BuildingInstanceWorldStateFile {
            schema: BUILDING_INSTANCE_WORLD_STATE_SCHEMA.to_string(),
            pass: BUILDING_INSTANCE_WORLD_STATE_PASS.to_string(),
            world_id: world_id.to_string(),
            revision: 0,
            upserts: Vec::new(),
            removed_instance_ids: Vec::new(),
            instance_states: Vec::new(),
        }
    };
    if document.schema != BUILDING_INSTANCE_WORLD_STATE_SCHEMA {
        return Err(format!(
            "{} uses unsupported schema {}",
            path.display(), document.schema
        ));
    }
    if document.world_id != world_id {
        return Err(format!(
            "{} belongs to world {}, expected {}",
            path.display(), document.world_id, world_id
        ));
    }

    let tombstoned = document
        .removed_instance_ids
        .iter()
        .cloned()
        .collect::<BTreeSet<_>>();
    let old_recipe_by_id = document
        .upserts
        .iter()
        .filter(|definition| definition.id.starts_with("pcg.willowmere."))
        .map(|definition| (definition.id.clone(), definition.recipe_id.clone()))
        .collect::<BTreeMap<_, _>>();

    let mut upserts = document
        .upserts
        .into_iter()
        .filter(|definition| !definition.id.starts_with("pcg.willowmere."))
        .collect::<Vec<_>>();
    for (id, definition) in &desired_by_id {
        if !tombstoned.contains(id) {
            upserts.push(definition.clone());
        }
    }
    upserts.sort_by(|left, right| left.id.cmp(&right.id));

    document.instance_states.retain(|state| {
        if !state.instance_id.starts_with("pcg.willowmere.") {
            return true;
        }
        let Some(desired) = desired_by_id.get(&state.instance_id) else {
            return false;
        };
        old_recipe_by_id
            .get(&state.instance_id)
            .is_some_and(|old| old == &desired.recipe_id)
    });
    document.upserts = upserts;
    document.pass = BUILDING_INSTANCE_WORLD_STATE_PASS.to_string();
    document.revision = document.revision.saturating_add(1);

    if let Some(parent) = path.parent() {
        create_dir_all(parent).map_err(|error| format!("{}: {error}", parent.display()))?;
    }
    let payload = serde_json::to_string_pretty(&document).map_err(|error| error.to_string())?;
    write(&path, format!("{payload}\n"))
        .map_err(|error| format!("{}: {error}", path.display()))?;
    Ok(document
        .upserts
        .iter()
        .filter(|definition| definition.id.starts_with("pcg.willowmere."))
        .count())
}

fn building_state_path(save_root: &str) -> std::path::PathBuf {
    Path::new(save_root)
        .join("buildings")
        .join("building_instance_deltas.json")
}

fn willowmere_building_instances(
    source_scene_id: &str,
    center: [i32; 2],
) -> Vec<BuildingInstanceDefinition> {
    // Source-native city placement: use only current production recipes at
    // their declared footprints. Do not rotate/stretch a recipe to manufacture
    // variety and never allow diagnostic-only prototype buildings into worldgen.
    // Plot offsets match the asymmetric reservations in mainland_features and
    // keep the central south avenue open toward the attached harbor district.
    let specs = [
        ("pcg.willowmere.civic_hall.001", "havenwild.estate.house_two_story_upgrade", [-24, -16], [9, 11]),
        ("pcg.willowmere.tavern.001", "havenwild.tavern.standard_three_level", [23, -13], [15, 11]),
        ("pcg.willowmere.house.001", "havenwild.estate.starter_cottage", [-28, 6], [9, 9]),
        ("pcg.willowmere.artisan.001", "havenwild.estate.house_two_story_upgrade", [28, 8], [9, 11]),
        ("pcg.willowmere.civic_house.002", "havenwild.estate.starter_cottage", [-10, -22], [9, 9]),
        ("pcg.willowmere.market_house.002", "havenwild.estate.house_two_story_upgrade", [11, -20], [9, 11]),
        ("pcg.willowmere.house.003", "havenwild.estate.starter_cottage", [-30, 20], [9, 9]),
        ("pcg.willowmere.house.004", "havenwild.estate.starter_cottage", [30, 19], [9, 9]),
    ];
    specs
        .into_iter()
        .map(|(id, recipe_id, offset, footprint)| {
            let plot_center = [center[0] + offset[0], center[1] + offset[1]];
            let anchor = [
                plot_center[0] - footprint[0] / 2,
                plot_center[1] - footprint[1] / 2,
            ];
            BuildingInstanceDefinition {
                schema: BUILDING_INSTANCE_SCHEMA.to_string(),
                id: id.to_string(),
                recipe_id: recipe_id.to_string(),
                scene_id: source_scene_id.to_string(),
                anchor_tile: anchor,
                initial_level: 0,
                diagnostic_only: false,
                origin: BuildingInstanceOrigin::Worldgen,
                placement_space: BuildingPlacementSpace::ContinuousSurface,
                surface_region_id: Some(MAINLAND_REGION.to_string()),
                global_anchor_tile: Some(anchor),
            }
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn willowmere_materializes_eight_continuous_surface_buildings() {
        let buildings = willowmere_building_instances("pcg_surface_havenwild_mainland_x_p0_y_p0", [100, 200]);
        assert_eq!(buildings.len(), 8);
        assert!(buildings.iter().all(|definition| {
            definition.placement_space == BuildingPlacementSpace::ContinuousSurface
                && definition.surface_region_id.as_deref() == Some(MAINLAND_REGION)
                && definition.global_anchor_tile.is_some()
                && definition.origin == BuildingInstanceOrigin::Worldgen
        }));
        assert!(buildings.iter().any(|definition| definition.id == "pcg.willowmere.tavern.001"));
        assert!(buildings.iter().all(|definition| {
            definition.recipe_id != "havenwild.prototype.three_level_house"
        }), "production worldgen must never place the diagnostic three-level prototype");
        assert!(
            buildings
                .iter()
                .map(|definition| definition.recipe_id.as_str())
                .collect::<BTreeSet<_>>()
                .len()
                >= 3,
            "Willowmere should consume every current production building family before repeating cottages"
        );
    }

    #[test]
    fn willowmere_reconcile_preserves_non_city_state_and_tombstones() {
        let root = std::env::temp_dir().join(format!(
            "havenwild_willowmere_reconcile_{}_{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .expect("clock")
                .as_nanos()
        ));
        let root_text = root.to_string_lossy().to_string();
        let mut old = willowmere_building_instances("scene", [0, 0]);
        let civic = old
            .iter_mut()
            .find(|definition| definition.id == "pcg.willowmere.civic_hall.001")
            .expect("civic");
        civic.recipe_id = "havenwild.prototype.three_level_house".to_string();
        let mut external = old[1].clone();
        external.id = "player.authored.house.001".to_string();
        external.origin = BuildingInstanceOrigin::Authored;
        let document = BuildingInstanceWorldStateFile {
            schema: BUILDING_INSTANCE_WORLD_STATE_SCHEMA.to_string(),
            pass: BUILDING_INSTANCE_WORLD_STATE_PASS.to_string(),
            world_id: "world_test".to_string(),
            revision: 4,
            upserts: old.into_iter().chain([external]).collect(),
            removed_instance_ids: vec!["pcg.willowmere.house.004".to_string()],
            instance_states: Vec::new(),
        };
        let path = building_state_path(&root_text);
        create_dir_all(path.parent().expect("parent")).expect("dir");
        write(
            &path,
            serde_json::to_string_pretty(&document).expect("serialize"),
        )
        .expect("write");

        reconcile_willowmere_worldgen_buildings(
            &root_text,
            "world_test",
            "scene",
            [20, 30],
        )
        .expect("reconcile");
        let updated: BuildingInstanceWorldStateFile = serde_json::from_str(
            &read_to_string(&path).expect("read"),
        )
        .expect("parse");
        assert!(updated
            .upserts
            .iter()
            .any(|definition| definition.id == "player.authored.house.001"));
        assert!(updated.upserts.iter().any(|definition| {
            definition.id == "pcg.willowmere.civic_hall.001"
                && definition.recipe_id == "havenwild.estate.house_two_story_upgrade"
        }));
        assert!(!updated
            .upserts
            .iter()
            .any(|definition| definition.id == "pcg.willowmere.house.004"));
        let _ = std::fs::remove_dir_all(root);
    }

    #[test]
    fn willowmere_building_ids_and_anchors_are_unique() {
        let buildings = willowmere_building_instances("scene", [0, 0]);
        let ids = buildings.iter().map(|entry| entry.id.as_str()).collect::<std::collections::BTreeSet<_>>();
        let anchors = buildings.iter().filter_map(|entry| entry.global_anchor_tile).collect::<std::collections::BTreeSet<_>>();
        assert_eq!(ids.len(), buildings.len());
        assert_eq!(anchors.len(), buildings.len());
    }
}
