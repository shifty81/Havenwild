use super::*;

const ESTATE_VISUAL_TEST_ARG: &str = "--estate-visual-test";
const ESTATE_VISUAL_TEST_WORLD: &str = "world_w53b_estate_visual_test";
const ESTATE_VISUAL_TEST_CHARACTER: &str = "character_w53b_estate_visual_test";
const W56_VISUAL_ACCEPTANCE_ARG: &str = "--w56-visual-acceptance";
const W56_VISUAL_ACCEPTANCE_WORLD: &str = "world_w56_integrated_visual_acceptance";
const W56_VISUAL_ACCEPTANCE_CHARACTER: &str = "character_w56_integrated_visual_acceptance";

pub(crate) async fn run() {
    if std::env::args().any(|arg| arg == W56_VISUAL_ACCEPTANCE_ARG) {
        run_w56_integrated_visual_acceptance().await;
        return;
    }
    if std::env::args().any(|arg| arg == ESTATE_VISUAL_TEST_ARG) {
        run_estate_visual_test().await;
        return;
    }
    match development_launch::request_from_process_args() {
        Ok(Some(launch)) => {
            run_world(
                launch.world.clone(),
                Some(launch),
                runtime_content_authority::RuntimeContentMode::Normal,
            )
            .await;
        }
        Ok(None) => run_frontend().await,
        Err(error) => {
            eprintln!("Havenwild development launch failed: {error}");
            std::process::exit(2);
        }
    }
}

async fn run_w56_integrated_visual_acceptance() {
    let character_id = CharacterId(W56_VISUAL_ACCEPTANCE_CHARACTER.to_string());
    if let Err(error) = ensure_development_character_profile(&character_id) {
        eprintln!("Havenwild W56 visual-acceptance character provisioning failed: {error}");
        return;
    }
    let launch = client_frontend::WorldLaunchRequest {
        world_id: WorldSaveId(W56_VISUAL_ACCEPTANCE_WORLD.to_string()),
        character_id,
    };
    run_world(
        launch,
        None,
        runtime_content_authority::RuntimeContentMode::IntegratedVisualAcceptance,
    )
    .await;
}

async fn run_estate_visual_test() {
    let character_id = CharacterId(ESTATE_VISUAL_TEST_CHARACTER.to_string());
    if let Err(error) = ensure_development_character_profile(&character_id) {
        eprintln!("Havenwild Estate visual-test character provisioning failed: {error}");
        return;
    }
    let launch = client_frontend::WorldLaunchRequest {
        world_id: WorldSaveId(ESTATE_VISUAL_TEST_WORLD.to_string()),
        character_id,
    };
    run_world(
        launch,
        None,
        runtime_content_authority::RuntimeContentMode::EstateVisualTest,
    )
    .await;
}

async fn run_frontend() {
    let mut frontend = ClientFrontend::new().await;
    // Give Macroquad/miniquad several submitted frames to finish creating the
    // native audio device before requesting looped frontend playback.
    for _ in 0..3 {
        frontend.draw();
        next_frame().await;
    }
    frontend.start_frontend_music();
    loop {
        let launch = loop {
            if let Some(request) = frontend.update() {
                break request;
            }
            frontend.draw();
            next_frame().await;
        };
        frontend.stop_frontend_music();
        if !run_world(
            launch,
            None,
            runtime_content_authority::RuntimeContentMode::Normal,
        )
        .await
        {
            break;
        }
        frontend.refresh_slots();
        frontend.start_frontend_music();
    }
}

/// Runs one persistent world through the same runtime path regardless of
/// whether the request came from the shipping frontend or development tools.
/// Returns true when the runtime requested the normal frontend again.
async fn run_world(
    launch: client_frontend::WorldLaunchRequest,
    development: Option<development_launch::DevelopmentLaunchRequest>,
    content_mode: runtime_content_authority::RuntimeContentMode,
) -> bool {
    let startup_started = std::time::Instant::now();
    draw_runtime_startup_stage(
        if development.is_some() { "Opening Development World" } else { "Opening World" },
        "Preparing character and runtime assets...",
        0.08,
    )
    .await;
    if development.is_some() {
        if let Err(error) = ensure_development_character_profile(&launch.character_id) {
            eprintln!("Havenwild development character provisioning failed: {error}");
            return false;
        }
    }
    let assets_started = std::time::Instant::now();
    let assets = RuntimeAssets::load(&launch.character_id).await;
    let assets_elapsed = assets_started.elapsed();
    draw_runtime_startup_stage(
        if development.is_some() { "Opening Development World" } else { "Opening World" },
        "Loading world state and project authorities...",
        0.42,
    )
    .await;
    let game_started = std::time::Instant::now();
    let mut game = Game::new(launch.world_id, launch.character_id, assets, content_mode);
    let game_elapsed = game_started.elapsed();
    game.log.event(&format!(
        "Runtime startup phase: assets {:.1} ms; world/bootstrap {:.1} ms",
        assets_elapsed.as_secs_f64() * 1000.0,
        game_elapsed.as_secs_f64() * 1000.0,
    ));
    if content_mode.is_integrated_visual_acceptance() {
        if !runtime_content_authority::integrated_visual_acceptance_world_is_current(&game.world) {
            let message = format!(
                "W56 integrated visual acceptance failed closed: expected isolated acceptance pack, active scene is {}",
                game.world.active_scene
            );
            game.log.event(&message);
            eprintln!("Havenwild {message}");
            return false;
        }
        if game
            .building_instance_registry
            .entry("havenwild.acceptance.w56_integrated_cottage")
            .is_none()
        {
            let message = "W56 integrated visual acceptance failed closed: diagnostic starter-cottage BuildingInstance is missing";
            game.log.event(message);
            eprintln!("Havenwild {message}");
            return false;
        }
    }
    if content_mode.is_estate_visual_test() {
        if !runtime_content_authority::estate_visual_test_world_is_current(&game.world) {
            let message = format!(
                "Estate visual test failed closed: expected isolated farmstead/Estate pack, active scene is {}",
                game.world.active_scene
            );
            game.log.event(&message);
            eprintln!("Havenwild {message}");
            return false;
        }
        if game
            .building_instance_registry
            .entry("havenwild.estate.dev.starter_cottage")
            .is_none()
        {
            let message = "Estate visual test failed closed: starter cottage BuildingInstance is missing from authored authority";
            game.log.event(message);
            eprintln!("Havenwild {message}");
            return false;
        }
    }
    let starter_axe_changes = game.player_inventory_ui.ensure_fresh_character_primitive_axe();
    if starter_axe_changes > 0 {
        game.synchronize_inventory_equipment_with_profile();
        game.log.event(
            "Fresh-character starter equipment: real Universal LPC Primitive Axe equipped in Main Hand; hotbar remains player-authored",
        );
    }
    let requested_scene = development
        .as_ref()
        .and_then(|request| request.scene_id.as_deref())
        .map(|scene| haven_core::ProjectSceneId::new(scene.to_string()));
    game.log.event(&haven_core::format_world_sync(
        "CLIENT-LOAD",
        &game.world,
        requested_scene.as_ref(),
    ));
    if let Some(ref development) = development {
        if let Err(error) = apply_development_start(&mut game, development) {
            game.log
                .event(&format!("Development launch failed before runtime ready: {error}"));
            eprintln!("Havenwild development launch failed: {error}");
            return false;
        }
        game.dev_mode = true;
        let toolkit_changes = game.player_inventory_ui.ensure_development_toolkit();
        if toolkit_changes > 0 {
            game.synchronize_inventory_equipment_with_profile();
            game.log.event(&format!(
                "Development toolkit provisioned: {toolkit_changes} production tool/equipment change(s); hotbar remains player-authored"
            ));
        }
        game.log.event(&haven_core::format_world_sync(
            "CLIENT-DEVELOPMENT-START",
            &game.world,
            requested_scene.as_ref(),
        ));
    }
    draw_runtime_startup_stage(
        if development.is_some() { "Opening Development World" } else { "Opening World" },
        "Preparing local terrain, structures, and spawn...",
        0.78,
    )
    .await;
    let local_surface_started = std::time::Instant::now();
    game.prepare_initial_surface_structures();
    game.repair_exterior_player_spawn_if_unsafe();
    game.refresh_world_paint_render_bindings_for_active_scene(
        "Startup paint render binding refresh",
    );
    let local_surface_elapsed = local_surface_started.elapsed();
    game.log.event(&format!(
        "Runtime startup phase: local surface/spawn {:.1} ms; total before first runtime frame {:.1} ms",
        local_surface_elapsed.as_secs_f64() * 1000.0,
        startup_started.elapsed().as_secs_f64() * 1000.0,
    ));
    draw_runtime_startup_stage(
        if development.is_some() { "Development World Ready" } else { "World Ready" },
        "Starting runtime...",
        1.0,
    )
    .await;
    game.log.event(&haven_core::format_world_sync(
        "RUNTIME-READY",
        &game.world,
        requested_scene.as_ref(),
    ));
    let mut development_live_bridge = development.as_ref().map(|_| development_live_bridge::DevelopmentLiveBridge::enabled());
    let return_to_frontend = loop {
        let submitted_frame_started_at = get_time();
        #[cfg(target_os = "windows")]
        crate::native_crash_windows::set_phase(crate::native_crash_windows::PHASE_LIVE_BRIDGE);
        if let Some(bridge) = development_live_bridge.as_mut() {
            bridge.poll(&mut game);
        }
        #[cfg(target_os = "windows")]
        crate::native_crash_windows::set_phase(crate::native_crash_windows::PHASE_UPDATE);
        let update_started_at = get_time();
        let flow = game.update(get_frame_time().min(1.0 / 30.0));
        if game.take_character_appearance_reload_request() {
            #[cfg(target_os = "windows")]
            crate::native_crash_windows::set_phase(
                crate::native_crash_windows::PHASE_APPEARANCE_RELOAD,
            );
            game.reload_character_appearance().await;
            #[cfg(target_os = "windows")]
            crate::native_crash_windows::set_phase(crate::native_crash_windows::PHASE_UPDATE);
        }
        let update_seconds = get_time() - update_started_at;

        #[cfg(target_os = "windows")]
        crate::native_crash_windows::set_phase(crate::native_crash_windows::PHASE_DRAW);
        let draw_started_at = get_time();
        game.draw();
        if game.pause_menu_open {
            #[cfg(target_os = "windows")]
            crate::native_crash_windows::set_phase(crate::native_crash_windows::PHASE_PAUSE_DRAW);
            game.draw_pause_menu();
        }
        let draw_seconds = get_time() - draw_started_at;
        let submitted_frame_seconds = get_time() - submitted_frame_started_at;
        #[cfg(target_os = "windows")]
        crate::native_crash_windows::set_phase(crate::native_crash_windows::PHASE_PRESENT);
        next_frame().await;
        #[cfg(target_os = "windows")]
        crate::native_crash_windows::set_phase(crate::native_crash_windows::PHASE_TELEMETRY);
        let wall_frame_seconds = get_time() - submitted_frame_started_at;
        game.terrain_render_telemetry.record_frame_cpu(
            update_seconds,
            draw_seconds,
            submitted_frame_seconds,
            wall_frame_seconds,
        );
        let snapshot_now = get_time();
        if game
            .terrain_render_telemetry
            .should_emit_snapshot(snapshot_now)
        {
            #[cfg(target_os = "windows")]
            crate::native_crash_windows::set_phase(crate::native_crash_windows::PHASE_SNAPSHOT);
            let snapshot =
                runtime_performance_snapshot::format_performance_snapshot(&game, snapshot_now);
            game.log.event(&snapshot);
        }
        match flow {
            ClientRuntimeFlow::Continue => {}
            ClientRuntimeFlow::ReturnToMainMenu => break true,
            ClientRuntimeFlow::QuitDesktop => break false,
        }
    };
    #[cfg(target_os = "windows")]
    crate::native_crash_windows::set_phase(crate::native_crash_windows::PHASE_RUNTIME_EXIT);
    game.persist_runtime_exit_state(if return_to_frontend {
        "return to main menu"
    } else {
        "quit desktop"
    });
    return_to_frontend
}


async fn draw_runtime_startup_stage(title: &str, detail: &str, progress: f32) {
    clear_background(Color::from_rgba(18, 21, 27, 255));
    let width = screen_width();
    let height = screen_height();
    let panel_w = width.min(680.0) - 48.0;
    let panel_x = (width - panel_w) * 0.5;
    let panel_y = (height * 0.5 - 78.0).max(48.0);
    draw_text(title, panel_x, panel_y, 34.0, Color::from_rgba(232, 237, 244, 255));
    draw_text(detail, panel_x, panel_y + 36.0, 20.0, Color::from_rgba(166, 177, 191, 255));
    let bar_y = panel_y + 68.0;
    draw_rectangle(panel_x, bar_y, panel_w, 10.0, Color::from_rgba(42, 48, 58, 255));
    draw_rectangle(
        panel_x,
        bar_y,
        panel_w * progress.clamp(0.0, 1.0),
        10.0,
        Color::from_rgba(93, 156, 236, 255),
    );
    next_frame().await;
}

fn ensure_development_character_profile(character_id: &CharacterId) -> Result<(), String> {
    let save_root = runtime_save_root();
    let profile_root = std::path::Path::new(&save_root)
        .parent()
        .unwrap_or_else(|| std::path::Path::new(&save_root))
        .join("profiles")
        .join("characters");
    ensure_development_character_profile_at(&profile_root, character_id)
}

const DEVELOPMENT_PROFILE_RACE_WAIT_ATTEMPTS: usize = 25;
const DEVELOPMENT_PROFILE_RACE_WAIT_MILLIS: u64 = 10;

fn wait_for_development_profile(profile_path: &std::path::Path) -> bool {
    for _ in 0..DEVELOPMENT_PROFILE_RACE_WAIT_ATTEMPTS {
        if profile_path.is_file() {
            return true;
        }
        std::thread::sleep(std::time::Duration::from_millis(
            DEVELOPMENT_PROFILE_RACE_WAIT_MILLIS,
        ));
    }
    profile_path.is_file()
}

fn ensure_development_character_profile_at(
    profile_root: &std::path::Path,
    character_id: &CharacterId,
) -> Result<(), String> {
    let profile_directory = profile_root.join(&character_id.0);
    let profile_path = profile_directory.join("profile.json");
    if profile_path.is_file() {
        return Ok(());
    }

    // Development characters are deterministic bootstrap state. Two editor/dev
    // launches may target the same deterministic character at nearly the same
    // time. If another process has already created the directory, allow its
    // atomic profile write to complete before treating the directory as stale.
    if profile_directory.is_dir() && wait_for_development_profile(&profile_path) {
        return Ok(());
    }

    // A prior interrupted launch can still leave an incomplete character
    // directory behind. Once the short cross-process grace window expires,
    // repair that stale bootstrap rather than terminating Play.
    if profile_directory.exists() {
        if profile_directory.is_dir() {
            std::fs::remove_dir_all(&profile_directory).map_err(|error| {
                format!(
                    "unable to repair incomplete development profile {} at {}: {error}",
                    character_id.0,
                    profile_directory.display()
                )
            })?;
        } else {
            std::fs::remove_file(&profile_directory).map_err(|error| {
                format!(
                    "unable to repair invalid development profile path {} at {}: {error}",
                    character_id.0,
                    profile_directory.display()
                )
            })?;
        }
        eprintln!(
            "Havenwild repaired incomplete development character profile {}",
            character_id.0
        );
    }

    let store = haven_save::CharacterProfileStore::new(profile_root.to_path_buf());
    store.ensure()?;
    let appearance = crate::character_creator_model::StarterCreatorSelection::default().appearance();
    let mut profile = haven_save::CharacterProfile::new("Development Character", appearance);
    profile.character_id = character_id.clone();
    match store.create(&profile) {
        Ok(_) => Ok(()),
        Err(error) if error.contains("already exists") && wait_for_development_profile(&profile_path) => {
            Ok(())
        }
        Err(error) => Err(format!(
            "unable to create development profile {}: {error}",
            character_id.0
        )),
    }
}

#[cfg(test)]
mod development_character_profile_tests {
    use super::*;

    fn scratch_profile_root(label: &str) -> std::path::PathBuf {
        std::env::temp_dir().join(format!(
            "havenwild-{label}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .expect("system clock")
                .as_nanos()
        ))
    }

    #[test]
    fn development_profile_provisioning_is_idempotent() {
        let root = scratch_profile_root("development-profile-idempotent");
        let character_id = CharacterId("character_development_test".to_string());

        ensure_development_character_profile_at(&root, &character_id)
            .expect("first provisioning succeeds");
        ensure_development_character_profile_at(&root, &character_id)
            .expect("second provisioning reuses the existing profile");

        assert!(root.join(&character_id.0).join("profile.json").is_file());
        let _ = std::fs::remove_dir_all(root);
    }

    #[test]
    fn concurrent_development_profile_completion_is_reused_without_deletion() {
        let root = scratch_profile_root("development-profile-race");
        let character_id = CharacterId("character_development_test".to_string());
        let profile_directory = root.join(&character_id.0);
        let profile_path = profile_directory.join("profile.json");
        std::fs::create_dir_all(&profile_directory).expect("create concurrent profile directory");
        std::fs::write(profile_directory.join("owner.tmp"), b"other launcher")
            .expect("write concurrent owner marker");

        let writer_path = profile_path.clone();
        let writer_character_id = character_id.clone();
        let writer = std::thread::spawn(move || {
            std::thread::sleep(std::time::Duration::from_millis(25));
            let appearance =
                crate::character_creator_model::StarterCreatorSelection::default().appearance();
            let mut profile =
                haven_save::CharacterProfile::new("Development Character", appearance);
            profile.character_id = writer_character_id;
            std::fs::write(
                writer_path,
                serde_json::to_vec_pretty(&profile).expect("serialize concurrent profile"),
            )
            .expect("complete concurrent profile");
        });

        ensure_development_character_profile_at(&root, &character_id)
            .expect("concurrent completed development profile is reused");
        writer.join().expect("concurrent profile writer");

        assert!(profile_path.is_file());
        assert!(profile_directory.join("owner.tmp").is_file());
        let _ = std::fs::remove_dir_all(root);
    }

    #[test]
    fn incomplete_development_profile_directory_is_repaired() {
        let root = scratch_profile_root("development-profile-repair");
        let character_id = CharacterId("character_development_test".to_string());
        let stale_directory = root.join(&character_id.0);
        std::fs::create_dir_all(&stale_directory).expect("create stale development directory");
        std::fs::write(stale_directory.join("interrupted.tmp"), b"partial")
            .expect("write stale development marker");

        ensure_development_character_profile_at(&root, &character_id)
            .expect("incomplete development profile is repaired");

        assert!(stale_directory.join("profile.json").is_file());
        assert!(!stale_directory.join("interrupted.tmp").exists());
        let _ = std::fs::remove_dir_all(root);
    }
}

fn apply_development_start(
    game: &mut Game,
    launch: &development_launch::DevelopmentLaunchRequest,
) -> Result<(), String> {
    if let Some(scene_id) = launch.scene_id.as_deref() {
        let scene = SceneReference::new(scene_id.to_string());
        if game.world.scene_by_reference(&scene).is_some() {
            game.world.set_active_scene(scene)?;
            game.set_player_to_active_spawn();
        } else {
            // PCG scene identifiers may change when the deterministic development
            // world is reprovisioned. Preserve the world's validated active scene
            // instead of making the development environment unusable.
            let warning = format!(
                "Havenwild development scene '{}' is stale; using world scene '{}'",
                scene_id,
                game.world.active_scene_id()
            );
            game.log.event(&warning);
            eprintln!("{warning}");
        }
    }
    if let Some([requested_x, requested_y]) = launch.spawn {
        let [x, y] = if requested_x < 0
            || requested_y < 0
            || requested_x >= MAP_W as i32
            || requested_y >= MAP_H as i32
        {
            let active = game.world.active();
            let fallback = [
                active.spawn_x.clamp(0, MAP_W as i32 - 1),
                active.spawn_y.clamp(0, MAP_H as i32 - 1),
            ];
            game.log.event(&format!(
                "Development spawn {requested_x}, {requested_y} is outside scene bounds; \
falling back to canonical scene spawn {},{} for {}",
                fallback[0],
                fallback[1],
                game.world.active_scene_id()
            ));
            fallback
        } else {
            [requested_x, requested_y]
        };
        game.player = vec2(
            x as f32 * TILE_SIZE + TILE_SIZE * 0.5,
            y as f32 * TILE_SIZE + TILE_SIZE * 0.5,
        );
        game.camera_target = game.local_world_to_runtime_world(game.player);
        game.selected_cell = (x, y);
        game.inspector = inspect_scene_cell(game.world.active(), x, y);
    }
    Ok(())
}
