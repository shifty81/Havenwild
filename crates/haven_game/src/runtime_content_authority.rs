use super::*;
use std::fs;
use std::path::{Path, PathBuf};

const CONTENT_AUTHORITY_REVISION: &str = "167Z109W53B";
const CONTENT_AUTHORITY_MARKER: &str = "runtime_content_authority_v1.json";
const HOME_ISLAND_AUTHORITY_PACK: &str =
    "content/worldgen/packs/worldgen_home_island_test_v0_11.json";
const ESTATE_VISUAL_TEST_PACK: &str =
    "content/worldgen/packs/worldgen_estate_visual_test_v0_1.json";
const W56_INTEGRATED_VISUAL_ACCEPTANCE_PACK: &str =
    "content/worldgen/packs/worldgen_w56_integrated_visual_acceptance_v0_1.json";
const W56_INTEGRATED_VISUAL_ACCEPTANCE_SCENE: &str = "w56_integrated_visual_acceptance";

const REFRESHED_LEGACY_SCENES: [&str; 6] = [
    "farmstead",
    "north_road",
    "south_field",
    "east_woods",
    "cave_mouth",
    "cave_depths",
];

// These old scene identities are superseded by same-world BuildingInstance levels.
// They must not remain reachable after W47/W48 because they create a second,
// contradictory interior authority.
const RETIRED_INTERIOR_SCENES: [&str; 3] = ["tavern_interior", "cellar", "guest_floor"];

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub(super) enum RuntimeContentMode {
    #[default]
    Normal,
    EstateVisualTest,
    IntegratedVisualAcceptance,
}

impl RuntimeContentMode {
    pub(super) fn is_estate_visual_test(self) -> bool {
        matches!(self, Self::EstateVisualTest)
    }

    pub(super) fn is_integrated_visual_acceptance(self) -> bool {
        matches!(self, Self::IntegratedVisualAcceptance)
    }
}

#[derive(Clone, Debug, Default)]
pub(super) struct RuntimeContentAuthorityReport {
    pub status: Option<String>,
    pub visual_test_active: bool,
    pub rebased_saved_world: bool,
}

pub(super) fn converge_runtime_content_authority(
    world: &mut GameWorld,
    save_paths: &ClientSavePaths,
    log: &mut GameLog,
    mode: RuntimeContentMode,
) -> RuntimeContentAuthorityReport {
    if mode.is_estate_visual_test() {
        return activate_estate_visual_test(world, log);
    }
    if mode.is_integrated_visual_acceptance() {
        return activate_integrated_visual_acceptance(world, log);
    }

    let marker_path = Path::new(&save_paths.root).join(CONTENT_AUTHORITY_MARKER);
    if marker_matches(&marker_path) {
        return RuntimeContentAuthorityReport::default();
    }

    if !contains_legacy_scene_bank(world) {
        if let Err(error) = write_marker(&marker_path, "non_legacy_world") {
            log.event(&format!("Runtime content authority marker write skipped: {error}"));
        }
        return RuntimeContentAuthorityReport::default();
    }

    let authority_path = runtime_root().join(HOME_ISLAND_AUTHORITY_PACK);
    let (authority_world, report) = match load_worldgen_pack_from_path(&authority_path) {
        Ok(value) => value,
        Err(error) => {
            let status = format!(
                "W53B content rebase unavailable; preserving saved world ({error})"
            );
            log.event(&status);
            return RuntimeContentAuthorityReport {
                status: Some(status),
                visual_test_active: false,
                rebased_saved_world: false,
            };
        }
    };
    log.event(&format!(
        "W53B content authority loaded {}",
        report.status_line()
    ));

    backup_if_present(
        Path::new(&save_paths.world),
        &backup_path(Path::new(&save_paths.world), "pre-w53b-content-authority"),
        log,
    );
    backup_if_present(
        Path::new(&save_paths.world_paint_delta),
        &backup_path(
            Path::new(&save_paths.world_paint_delta),
            "pre-w53b-content-authority",
        ),
        log,
    );

    let mut refreshed = 0usize;
    let active_before = world.active_scene.code().to_string();
    for scene_code in REFRESHED_LEGACY_SCENES {
        let id = haven_core::ProjectSceneId::new(scene_code);
        let Some(source) = authority_world.scene_by_id(&id).cloned() else {
            log.event(&format!(
                "W53B content authority missing canonical scene {scene_code}; saved scene retained"
            ));
            continue;
        };
        if let Some(target) = world.scene_mut_by_id(&id) {
            *target = source;
        } else if let Err(error) = world.insert_scene(source) {
            log.event(&format!(
                "W53B content authority could not insert scene {scene_code}: {error}"
            ));
            continue;
        }
        refreshed += 1;
    }

    let retired = retire_parallel_interior_scenes(world);
    strip_transitions_to_retired_interiors(world);

    if world
        .scene_by_reference(&world.active_scene.clone())
        .is_none()
        || RETIRED_INTERIOR_SCENES.contains(&active_before.as_str())
    {
        let estate = SceneReference::new("farmstead");
        if world.scene_by_reference(&estate).is_some() {
            let _ = world.set_active_scene(estate);
        }
    }

    // Old world-paint operations were authored against the stale scene substrate.
    // Keep them in the backup above, then remove only records targeting refreshed
    // or retired legacy scenes. Operations on modern/generated scenes survive.
    let filtered_paint = filter_legacy_world_paint_deltas(Path::new(&save_paths.world_paint_delta), log);

    if let Err(error) = save_world_to_path(&save_paths.world, world) {
        let status = format!("W53B content rebase could not persist repaired world: {error}");
        log.event(&status);
        return RuntimeContentAuthorityReport {
            status: Some(status),
            visual_test_active: false,
            rebased_saved_world: false,
        };
    }

    if let Err(error) = write_marker(&marker_path, "legacy_scene_bank_rebased") {
        log.event(&format!("Runtime content authority marker write failed: {error}"));
    }

    let status = format!(
        "W53B content authority rebased {refreshed} legacy scene(s), retired {retired} parallel interior scene(s), removed {filtered_paint} stale paint delta(s)"
    );
    log.event(&status);
    RuntimeContentAuthorityReport {
        status: Some(status),
        visual_test_active: false,
        rebased_saved_world: true,
    }
}

pub(super) fn is_authored_scene(scene_code: &str) -> bool {
    REFRESHED_LEGACY_SCENES.contains(&scene_code)
}

pub(super) fn is_retired_parallel_interior(scene_code: &str) -> bool {
    RETIRED_INTERIOR_SCENES.contains(&scene_code)
}

fn activate_estate_visual_test(
    world: &mut GameWorld,
    log: &mut GameLog,
) -> RuntimeContentAuthorityReport {
    let authority_path = runtime_root().join(ESTATE_VISUAL_TEST_PACK);
    let (mut visual_world, report) = match load_worldgen_pack_from_path(&authority_path) {
        Ok(value) => value,
        Err(error) => {
            let status = format!("W53B Estate visual test pack failed to load: {error}");
            log.event(&status);
            return RuntimeContentAuthorityReport {
                status: Some(status),
                visual_test_active: true,
                rebased_saved_world: false,
            };
        }
    };

    retire_parallel_interior_scenes(&mut visual_world);
    retain_visual_test_scene_set(&mut visual_world);
    strip_transitions_to_retired_interiors(&mut visual_world);
    let estate = SceneReference::new("farmstead");
    if visual_world.scene_by_reference(&estate).is_some() {
        let _ = visual_world.set_active_scene(estate);
    }
    *world = visual_world;

    let status = format!(
        "DEV — W54D2 Estate | source={} | save bypassed | {} scene(s)",
        ESTATE_VISUAL_TEST_PACK, report.scene_count
    );
    log.event(&status);
    RuntimeContentAuthorityReport {
        status: Some(status),
        visual_test_active: true,
        rebased_saved_world: false,
    }
}

pub(super) fn estate_visual_test_world_is_current(world: &GameWorld) -> bool {
    if world.active_scene.code() != "farmstead" {
        return false;
    }
    REFRESHED_LEGACY_SCENES.iter().all(|code| {
        world
            .scene_by_reference(&SceneReference::new((*code).to_string()))
            .is_some()
    }) && world
        .scene_by_reference(&SceneReference::new("willowmere_outskirts_open_world"))
        .is_none()
}

fn activate_integrated_visual_acceptance(
    world: &mut GameWorld,
    log: &mut GameLog,
) -> RuntimeContentAuthorityReport {
    let authority_path = runtime_root().join(W56_INTEGRATED_VISUAL_ACCEPTANCE_PACK);
    let (mut visual_world, report) = match load_worldgen_pack_from_path(&authority_path) {
        Ok(value) => value,
        Err(error) => {
            let status = format!("W56 integrated visual acceptance pack failed to load: {error}");
            log.event(&status);
            return RuntimeContentAuthorityReport {
                status: Some(status),
                visual_test_active: true,
                rebased_saved_world: false,
            };
        }
    };

    let scene = SceneReference::new(W56_INTEGRATED_VISUAL_ACCEPTANCE_SCENE);
    if visual_world.scene_by_reference(&scene).is_some() {
        let _ = visual_world.set_active_scene(scene);
    }
    *world = visual_world;

    let status = format!(
        "DEV — W56I/J Integrated Visual Acceptance | source={} | save bypassed | {} scene(s)",
        W56_INTEGRATED_VISUAL_ACCEPTANCE_PACK, report.scene_count
    );
    log.event(&status);
    RuntimeContentAuthorityReport {
        status: Some(status),
        visual_test_active: true,
        rebased_saved_world: false,
    }
}

pub(super) fn integrated_visual_acceptance_world_is_current(world: &GameWorld) -> bool {
    world.active_scene.code() == W56_INTEGRATED_VISUAL_ACCEPTANCE_SCENE
        && world
            .scene_by_reference(&SceneReference::new(W56_INTEGRATED_VISUAL_ACCEPTANCE_SCENE))
            .is_some()
        && world.scenes.len() == 1
}

fn contains_legacy_scene_bank(world: &GameWorld) -> bool {
    SceneId::ALL
        .iter()
        .any(|id| world.scene(*id).is_some())
}

fn retire_parallel_interior_scenes(world: &mut GameWorld) -> usize {
    let mut removed = 0usize;
    for code in RETIRED_INTERIOR_SCENES {
        let id = haven_core::ProjectSceneId::new(code);
        if world.scenes.remove(&id).is_some() {
            removed += 1;
        }
    }
    removed
}

fn strip_transitions_to_retired_interiors(world: &mut GameWorld) {
    for scene in world.scenes.iter_mut() {
        scene.transitions.retain(|transition| {
            !RETIRED_INTERIOR_SCENES.contains(&transition.target.code())
        });
    }
}

fn retain_visual_test_scene_set(world: &mut GameWorld) {
    let remove = world
        .scenes
        .iter()
        .filter(|scene| !REFRESHED_LEGACY_SCENES.contains(&scene.id.code()))
        .map(|scene| scene.id.clone())
        .collect::<Vec<_>>();
    for id in remove {
        let _ = world.scenes.remove(&id);
    }
}

fn marker_matches(path: &Path) -> bool {
    fs::read_to_string(path)
        .ok()
        .is_some_and(|text| text.contains(CONTENT_AUTHORITY_REVISION))
}

fn write_marker(path: &Path, mode: &str) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|error| error.to_string())?;
    }
    let body = format!(
        "{{\n  \"schema\": \"havenwild.runtime_content_authority.v1\",\n  \"revision\": \"{}\",\n  \"mode\": \"{}\",\n  \"rule\": \"saved progression persists; obsolete scene baselines rebase once per content revision\"\n}}\n",
        CONTENT_AUTHORITY_REVISION, mode
    );
    fs::write(path, body).map_err(|error| error.to_string())
}

fn backup_path(path: &Path, suffix: &str) -> PathBuf {
    let file_name = path
        .file_name()
        .and_then(|value| value.to_str())
        .unwrap_or("save");
    path.with_file_name(format!("{file_name}.{suffix}.bak"))
}

fn backup_if_present(source: &Path, backup: &Path, log: &mut GameLog) {
    if !source.is_file() || backup.is_file() {
        return;
    }
    match fs::copy(source, backup) {
        Ok(_) => log.event(&format!(
            "W53B preserved pre-rebase backup {}",
            backup.display()
        )),
        Err(error) => log.event(&format!(
            "W53B backup failed for {}: {error}",
            source.display()
        )),
    }
}

fn filter_legacy_world_paint_deltas(path: &Path, log: &mut GameLog) -> usize {
    let Ok(mut document) = load_world_paint_delta_document(path) else {
        return 0;
    };
    let before = document.records.len();
    document.records.retain(|record| {
        !REFRESHED_LEGACY_SCENES.contains(&record.scene_id.as_str())
            && !RETIRED_INTERIOR_SCENES.contains(&record.scene_id.as_str())
    });
    let removed = before.saturating_sub(document.records.len());
    if removed == 0 {
        return 0;
    }
    match haven_world::save_world_paint_delta_document(path, &document) {
        Ok(()) => log.event(&format!(
            "W53B removed {removed} stale legacy-scene world-paint delta record(s)"
        )),
        Err(error) => log.event(&format!(
            "W53B could not rewrite filtered world-paint delta document: {error}"
        )),
    }
    removed
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn retired_interiors_are_not_part_of_same_world_building_authority() {
        assert_eq!(
            RETIRED_INTERIOR_SCENES,
            ["tavern_interior", "cellar", "guest_floor"]
        );
    }

    #[test]
    fn estate_is_a_refreshed_authored_scene() {
        assert!(REFRESHED_LEGACY_SCENES.contains(&"farmstead"));
    }
}
