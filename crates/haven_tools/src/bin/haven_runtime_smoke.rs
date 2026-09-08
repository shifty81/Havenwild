use haven_assets::asset_pack::AssetCategory;
use haven_assets::runtime_asset_cache::RuntimeAssetSession;
use haven_assets::semantic_asset_resolution::AssetResolutionContext;
use haven_save::{
    load_character_world_link, load_world_save_metadata, save_character_world_link,
    save_world_save_metadata, scan_world_saves, world_save_paths, CharacterAppearance,
    CharacterAppearanceLayer, CharacterProfile, CharacterProfileStore, CharacterWorldLink,
    PortableAssetRef, WorldSaveId, WorldSaveMetadata,
};
use serde::Serialize;
use std::env;
use std::fs::{create_dir_all, remove_dir_all, write};
use std::path::{Path, PathBuf};

#[derive(Serialize)]
struct SmokeCheck {
    id: &'static str,
    passed: bool,
    detail: String,
}

#[derive(Serialize)]
struct SmokeReport {
    schema: &'static str,
    passed: bool,
    project_root: String,
    scratch_root: String,
    mounted_packs: usize,
    stable_sources: usize,
    checks: Vec<SmokeCheck>,
}

fn main() {
    let mut project_root = PathBuf::from(".");
    let mut output = PathBuf::from("logs/smoke/runtime-smoke-latest.json");
    let mut keep_scratch = false;
    let args: Vec<String> = env::args().collect();
    let mut index = 1;
    while index < args.len() {
        match args[index].as_str() {
            "--project-root" if index + 1 < args.len() => {
                project_root = PathBuf::from(&args[index + 1]);
                index += 2;
            }
            "--output" if index + 1 < args.len() => {
                output = PathBuf::from(&args[index + 1]);
                index += 2;
            }
            "--keep-scratch" => {
                keep_scratch = true;
                index += 1;
            }
            other => fail(&format!("unknown argument: {other}")),
        }
    }

    let project_root = project_root.canonicalize().unwrap_or(project_root);
    let scratch_root = project_root.join("WORKSPACE/smoke_test/pass149a");
    if scratch_root.exists() {
        remove_dir_all(&scratch_root).unwrap_or_else(|error| fail(&error.to_string()));
    }
    create_dir_all(&scratch_root).unwrap_or_else(|error| fail(&error.to_string()));

    let mut checks = Vec::new();
    let asset_session = RuntimeAssetSession::discover(&project_root).unwrap_or_else(|report| {
        let diagnostics = report
            .records
            .iter()
            .flat_map(|record| record.diagnostics.iter())
            .cloned()
            .collect::<Vec<_>>();
        fail(&format!(
            "asset discovery failed: {} failed record(s); diagnostics={diagnostics:?}",
            report.failed_count()
        ))
    });
    let mounted_pack_count = asset_session.registry.mounted_packs().count();
    checks.push(check(
        "asset_pack_discovery",
        mounted_pack_count > 0,
        format!("{mounted_pack_count} production packs mounted"),
    ));
    checks.push(check(
        "stable_asset_source_cache",
        !asset_session.sources.is_empty(),
        format!("{} stable source bindings", asset_session.sources.len()),
    ));

    for (id, category) in [
        ("terrain.grass", AssetCategory::Terrain),
        ("character.player.base", AssetCategory::Character),
        ("object.catalog.runtime", AssetCategory::TileObject),
    ] {
        let resolved =
            asset_session.resolve_source(id, category, AssetResolutionContext::default());
        checks.push(check(
            "semantic_asset_resolution",
            resolved.is_some(),
            resolved
                .map(|source| format!("{id} -> {}", source.source_path.display()))
                .unwrap_or_else(|| format!("{id} did not resolve")),
        ));
    }

    let profile_store = CharacterProfileStore::new(scratch_root.join("profiles/characters"));
    let profile = CharacterProfile::new("Foundation Tester", smoke_appearance());
    profile_store
        .create(&profile)
        .unwrap_or_else(|error| fail(&error));
    let profiles = profile_store.scan().unwrap_or_else(|error| fail(&error));
    checks.push(check(
        "character_profile_round_trip",
        profiles.len() == 1 && profiles[0].character_id == profile.character_id,
        format!("{} profile(s) restored", profiles.len()),
    ));

    let save_root = scratch_root.join("saves");
    let save_root_text = save_root.to_string_lossy().to_string();
    let world_id = WorldSaveId("world_test_foundation_001".to_string());
    let paths = world_save_paths(&save_root_text, &world_id).unwrap_or_else(|error| fail(&error));
    paths
        .ensure_directories()
        .unwrap_or_else(|error| fail(&error));
    let mut metadata =
        WorldSaveMetadata::new(world_id.clone(), "Foundation Test World", 148_149_001, 1);
    metadata.starting_scene_code = "mainland_spawn".to_string();
    save_world_save_metadata(&paths.metadata, &metadata).unwrap_or_else(|error| fail(&error));
    write(&paths.world, b"havenwild smoke world\n")
        .unwrap_or_else(|error| fail(&error.to_string()));
    let restored_metadata =
        load_world_save_metadata(&paths.metadata).unwrap_or_else(|error| fail(&error));
    let worlds = scan_world_saves(&save_root_text).unwrap_or_else(|error| fail(&error));
    checks.push(check(
        "dynamic_world_round_trip",
        restored_metadata.world_id == world_id
            && worlds
                .iter()
                .any(|world| world.world_id == world_id && world.occupied()),
        format!("{} dynamic world(s) discovered", worlds.len()),
    ));

    let mut link = CharacterWorldLink::new(profile.character_id.clone(), world_id.clone());
    link.world_scene = "mainland_spawn".to_string();
    link.world_position = [37, 52];
    link.world_reputation.insert("capital".to_string(), 12);
    link.world_relationships
        .insert("npc_test_innkeeper".to_string(), 4);
    link.world_quest_flags
        .push("foundation_smoke_started".to_string());
    save_character_world_link(Path::new(&paths.root), &link).unwrap_or_else(|error| fail(&error));
    let restored_link = load_character_world_link(Path::new(&paths.root), &profile.character_id)
        .unwrap_or_else(|error| fail(&error));
    checks.push(check(
        "character_world_state_round_trip",
        restored_link.world_id == world_id
            && restored_link.world_scene == "mainland_spawn"
            && restored_link.world_position == [37, 52]
            && restored_link.world_reputation.get("capital") == Some(&12)
            && restored_link.world_relationships.get("npc_test_innkeeper") == Some(&4)
            && restored_link
                .world_quest_flags
                .iter()
                .any(|flag| flag == "foundation_smoke_started"),
        "scene, position, reputation, relationship, and quest state restored".to_string(),
    ));

    let passed = checks.iter().all(|item| item.passed);
    let report = SmokeReport {
        schema: "havenwild.testable_foundation_smoke.v1",
        passed,
        project_root: project_root.to_string_lossy().to_string(),
        scratch_root: scratch_root.to_string_lossy().to_string(),
        mounted_packs: mounted_pack_count,
        stable_sources: asset_session.sources.len(),
        checks,
    };
    let output = if output.is_absolute() {
        output
    } else {
        project_root.join(output)
    };
    if let Some(parent) = output.parent() {
        create_dir_all(parent).unwrap_or_else(|error| fail(&error.to_string()));
    }
    let json =
        serde_json::to_string_pretty(&report).unwrap_or_else(|error| fail(&error.to_string()));
    write(&output, json).unwrap_or_else(|error| fail(&error.to_string()));

    for item in &report.checks {
        println!(
            "{} {}: {}",
            if item.passed { "PASS" } else { "FAIL" },
            item.id,
            item.detail
        );
    }
    println!("Smoke report: {}", output.display());

    if !keep_scratch {
        remove_dir_all(&scratch_root).unwrap_or_else(|error| fail(&error.to_string()));
    }
    if !passed {
        std::process::exit(1);
    }
}

fn smoke_appearance() -> CharacterAppearance {
    CharacterAppearance {
        body_profile: "lpc.standard".to_string(),
        animation_profile: "lpc.eight_direction".to_string(),
        portrait_profile: "lpc.generated".to_string(),
        layers: vec![CharacterAppearanceLayer {
            slot: "body/base".to_string(),
            asset: PortableAssetRef {
                pack_id: "havenwild_characters".to_string(),
                category: "character".to_string(),
                asset_id: "player_base".to_string(),
                source_id: "generated_player_walk".to_string(),
                variant_id: None,
            },
            palette_id: None,
            tint_rgba: None,
            enabled: true,
        }],
    }
}

fn check(id: &'static str, passed: bool, detail: String) -> SmokeCheck {
    SmokeCheck { id, passed, detail }
}

fn fail(message: &str) -> ! {
    eprintln!("ERROR: {message}");
    std::process::exit(1)
}
