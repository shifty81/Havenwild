use macroquad::prelude::*;
use std::backtrace::Backtrace;
use std::io::Write;
use std::time::{SystemTime, UNIX_EPOCH};
mod asset_reference_browser_panel;
mod base_terrain_cache;
mod bridge_render;
mod building_instance_runtime;
mod building_instance_sync;
mod character_creator_catalog;
mod character_creator_model;
mod character_equipment_runtime;
mod character_ecs_runtime;
mod client_controls;
mod runtime_cache_contract;
mod runtime_structural_cliff_shapes;
mod runtime_structural_connectors;
mod runtime_structural_cliff_ramps;
mod runtime_structural_waterfall_owner;
mod runtime_structural_waterfall_draw;
mod runtime_structural_cliff_contours;
mod runtime_structural_cliff_caps;
#[allow(dead_code)]
mod character_repository_catalog;
mod character_runtime_compositor;
mod character_vitals_runtime;
mod character_visual_policy;
mod character_world_runtime;
mod character_world_sync;
mod chunk_render_contract;
mod chunk_surface_cache;
mod client_character_frontend_draw;
mod client_entry;
mod client_frontend;
mod development_launch;
mod development_live_bridge;
mod development_resource_context;
mod client_pause_menu;
mod client_save_generation;
mod client_save_generation_city;
mod clothing_loot_runtime;
mod editor_state;
mod game_log;
mod gameplay_hotbar;
mod gameplay_tool_runtime;
mod universal_lpc_gameplay_equipment;
mod map_edit_runtime;
#[cfg(target_os = "windows")]
mod native_crash_windows;
mod object_edit_runtime;
mod placeable_behavior_runtime;
mod player_inventory_ui;
mod render_queue;
mod render_telemetry;
mod runtime_assets;
mod runtime_commands;
mod runtime_collision_overrides;
mod runtime_content_authority;
mod runtime_config;
mod runtime_diagnostics;
mod runtime_draw;
mod runtime_editor_draw;
mod runtime_editor_shell;
mod runtime_hud;
mod runtime_chat;
mod runtime_item_icons;
mod runtime_ui_theme;
mod runtime_input;
mod runtime_interactions;
mod runtime_object_draw;
mod runtime_performance_snapshot;
mod runtime_persistence;
mod runtime_render_bindings;
mod runtime_scene_navigation;
mod runtime_stamp_draw;
mod runtime_startup;
mod runtime_surface_streaming;
mod runtime_structural_cliff_draw;
mod runtime_terrain_base_draw;
mod runtime_terrain_pass;
mod runtime_terrain_plan;
mod runtime_texture_cache;
mod runtime_visual_override_draw;
mod runtime_view_culling;
mod runtime_world_map;
mod station_interaction_runtime;
mod station_placement_runtime;
mod terrain_chunk_mesh;
mod terrain_debug_overlay;
mod terrain_generation;
mod terrain_render;
mod terrain_scene_surface;
mod transition_edit_runtime;
mod transition_rule_editor_panel;
mod transition_rule_inspector_overlay;
mod transition_rule_preview_overlay;
mod water_material;
mod water_render_budget;
mod water_ripple_runtime;
mod world_paint_editor_draw;
mod world_paint_editor_panel;
mod world_paint_lifecycle;
mod world_paint_render_binding;
mod world_rules_runtime;
mod world_creation_wizard;
use asset_reference_browser_panel::{
    AssetReferenceFamilyFilter, AssetReferenceGridFilter, AssetReferencePolicyFilter,
};
use client_frontend::ClientFrontend;
use client_pause_menu::ClientRuntimeFlow;
use editor_state::{
    EditorTab, FootprintEditTarget, LayoutDrag, MapBrushMode, TileContextMenu, TransitionEdit,
};
use game_log::GameLog;
use gameplay_hotbar::GameplayTool;
use haven_assets::asset_registry::{audited_object_footprint_for_cell, object_asset_entry_for_cell};
use haven_assets::authored_terrain_contacts::normalize_lpc_authored_material_contacts_region;
use haven_assets::lpc_mapped_terrain::{
    audit_lpc_tuple_compatibility, lpc_mapped_terrain_diagnostic_for_map,
    lpc_mapped_terrain_preview_entry, lpc_mapped_terrain_runtime_entry_for_tile_sampler,
    lpc_mapped_terrain_transition_entry_for_tile_sampler, LpcMappedTerrainEntry,
    LpcTupleResolutionStatus,
};
use haven_authoring::{
    apply_terrain_paint_mode_to_map, inspect_scene_cell, validate_world, AuthoringPalette,
    EditorCommand, EditorCommandBus, EditorCommandKind, EditorCommandSource, GridPos,
    InspectorReport, TerrainPaintModeReport,
};
use haven_core::{
    water_source_class, BuildTool, GameWorld, ObjectId, ObjectKind, PlacedObject, SceneBiome,
    SceneId, SceneKind, SceneMap, SceneReference, TavernMap, TerrainPaintMode, TileAutoGroup,
    TileInteraction, TileKind, Transition, UiAnchor, UiLayoutState, UiPanelId, WaterSourceClass,
    ZoneKind, MAP_H, MAP_W, TILE_SIZE,
};
use haven_net::replicate_editor_command;
use haven_render::{
    atlas_rect, draw_editor_button, draw_inspector_overlay, draw_layout_guides,
    draw_object_fallback, draw_panel, draw_validation_overlay, draw_world_graph_overlay,
    object_origin, object_sort_y, panel_grid_from_screen, player_sort_y, resolve_panel_rect,
    sky_color, snap_panel_to_grid, UiPanelRect,
};
use haven_save::{
    load_character_world_link, load_surface_chunk, load_ui_layout_from_path, load_world_from_path,
    load_world_topology_from_path, load_world_save_metadata, save_surface_chunk_baseline, save_surface_chunk_delta,
    save_ui_layout_to_path, save_world_save_metadata, save_world_to_path, world_save_paths,
    CharacterId, CharacterVitalsState, CharacterWorldLink, ClientSavePaths, WorldSaveId,
    CURRENT_CLIENT_GENERATION_VERSION,
};
use haven_sim::{clock_label, customer_sort_y, night_amount, update_tavern_customers, Customer, CharacterAnimationIntent, CharacterRuntimeState, RuntimeEntityIdentity};
use haven_ecs::{EntityId, EntityWorld};
use client_controls::{ControlAction, ControlRuntime};
use client_pause_menu::PauseMenuPage;
use haven_world::{
    append_world_paint_delta_record, apply_coastline_tile_pass, apply_world_paint_brush,
    apply_world_paint_delta_record_to_material_state_path, export_worldgen_pack_to_path,
    inspect_world_paint_material_cell_path, load_and_replay_world_paint_deltas,
    load_world_paint_delta_document, load_worldgen_pack_from_path,
    refresh_world_paint_render_cache_scene,
    resolve_world_paint_material_adjacency_path, resolve_world_paint_material_scene_adjacency_path,
    resolve_world_paint_scene_transition_tiles, resolve_world_paint_transition_tile,
    world_paint_layer_render_order, LiveAutotileCache, ResolvedTerrainTransitions,
    TransitionRuleCatalogFilter, WorldPaintBrushSettings, WorldPaintDeltaRecord, WorldPaintFamily,
    WorldPaintLayer, WorldPaintMaterialAdjacencyReport, WorldPaintMaterialCellInspection,
    WorldPaintSubcellMode, WorldPaintTransitionTileResolution,
};
use render_queue::RenderCommand;
use runtime_assets::RuntimeAssets;
use runtime_config::{
    runtime_layout_path, runtime_root, runtime_save_root, runtime_worldgen_export_path,
    runtime_worldgen_pack_path, window_conf, PLAYER_SPEED, RUNTIME_CAMERA_DEFAULT_ZOOM,
    RUNTIME_CAMERA_MAX_ZOOM, RUNTIME_CAMERA_MIN_ZOOM, RUNTIME_CAMERA_ZOOM_STEP, UI_GRID,
    UNDO_LIMIT,
};
use terrain_generation::{
    classify_height_tile, default_interaction_for_tile, terrain_height, TerrainClassificationInput,
};
use terrain_render::{draw_tile_border, draw_tile_detail, tile_color, zone_color};
use world_paint_render_binding::WorldPaintRenderBindingCache;
fn building_instance_save_path(save_root: &str) -> std::path::PathBuf {
    std::path::Path::new(save_root)
        .join("buildings")
        .join("building_instance_deltas.json")
}

struct Game {
    world_id: WorldSaveId,
    character_id: CharacterId,
    character_world_link: CharacterWorldLink,
    save_paths: ClientSavePaths,
    world_creation_settings: haven_world::WorldCreationSettings,
    world_topology: haven_world::WorldTopologyConfig,
    ecs_world: EntityWorld,
    player_entity: EntityId,
    world: GameWorld,
    building_recipe_registry: haven_assets::building_recipe::BuildingRecipeRegistry,
    building_instance_registry: haven_assets::building_instance::BuildingInstanceRegistry,
    building_instance_views: std::collections::BTreeMap<
        String,
        haven_assets::building_instance::BuildingInstanceViewState,
    >,
    building_door_animations: std::collections::BTreeMap<
        String,
        building_instance_runtime::RuntimeBuildingDoorAnimation,
    >,
    scene_door_animations: std::collections::BTreeMap<
        String,
        runtime_interactions::RuntimeSceneDoorAnimation,
    >,
    palette: AuthoringPalette,
    selected_tool: usize,
    selected_gameplay_tool: usize,
    universal_lpc_gameplay_equipment: universal_lpc_gameplay_equipment::UniversalLpcGameplayEquipmentRuntime,
    pending_gameplay_tool_action: Option<gameplay_tool_runtime::PendingGameplayToolAction>,
    ranged_aim: Option<gameplay_tool_runtime::RangedAimState>,
    runtime_projectiles: Vec<gameplay_tool_runtime::RuntimeProjectile>,
    editor_tab: EditorTab,
    terrain_paint_mode: TerrainPaintMode,
    tool_page: usize,
    selected_transition_target: usize,
    selected_transition_index: usize,
    selected_object_index: Option<usize>,
    selected_placeable_index: usize,
    object_list_offset: usize,
    footprint_edit_target: FootprintEditTarget,
    selected_rule_tile: usize,
    player: Vec2,
    camera_target: Vec2,
    camera_zoom: f32,
    _runtime_content_mode: runtime_content_authority::RuntimeContentMode,
    dev_mode: bool,
    dev_toggle_armed: bool,
    build_mode: bool,
    editor_minimized: bool,
    tavern_open: bool,
    pause_menu_open: bool,
    pause_menu_page: PauseMenuPage,
    pause_menu_selection: usize,
    controls: ControlRuntime,
    player_inventory_ui: player_inventory_ui::PlayerInventoryUi,
    runtime_chat: runtime_chat::RuntimeChatState,
    character_vitals: CharacterVitalsState,
    lpc_waterfall_source: Option<Texture2D>,
    oga_cliff_source: Option<Texture2D>,
    day_clock: f32,
    reputation: i32,
    coin: i32,
    customers: Vec<Customer>,
    customer_timer: f32,
    selected_cell: (i32, i32),
    tile_context_menu: Option<TileContextMenu>,
    copied_tile: Option<TileKind>,
    brush_size: i32,
    world_seed: u64,
    map_water_level: i32,
    map_mountain_level: i32,
    map_brush: MapBrushMode,
    world_paint_family: WorldPaintFamily,
    world_paint_layer: WorldPaintLayer,
    world_paint_subcell_mode: WorldPaintSubcellMode,
    world_paint_strength: f32,
    world_paint_autotile: bool,
    world_paint_mirror_horizontal: bool,
    world_paint_mirror_vertical: bool,
    world_paint_last_report: String,
    world_paint_delta_status: String,
    world_paint_inspector_status: String,
    world_paint_inspector: Option<WorldPaintMaterialCellInspection>,
    world_paint_adjacency_status: String,
    world_paint_adjacency: Option<WorldPaintMaterialAdjacencyReport>,
    world_paint_tile_resolver_status: String,
    world_paint_tile_resolution: Option<WorldPaintTransitionTileResolution>,
    world_paint_render_status: String,
    world_paint_render_bindings: WorldPaintRenderBindingCache,
    world_paint_edit_sequence: u64,
    inspector: InspectorReport,
    status_message: String,
    last_replication_status: String,
    replication_sequence: u64,
    validation_messages: Vec<String>,
    show_world_graph: bool,
    show_footprint_overlay: bool,
    show_collision_overlay: bool,
    show_interaction_overlay: bool,
    show_terrain_debug_overlay: bool,
    show_transition_rule_inspector: bool,
    show_transition_rule_preview: bool,
    transition_rule_preview_index: usize,
    transition_rule_editor_filter: TransitionRuleCatalogFilter,
    transition_rule_editor_index: usize,
    transition_rule_editor_scroll: usize,
    asset_reference_grid_filter: AssetReferenceGridFilter,
    asset_reference_family_filter: AssetReferenceFamilyFilter,
    asset_reference_policy_filter: AssetReferencePolicyFilter,
    asset_reference_index: usize,
    asset_reference_scroll: usize,
    ui_layout: UiLayoutState,
    layout_edit_mode: bool,
    layout_drag: Option<LayoutDrag>,
    editor_resizing: bool,
    command_bus: EditorCommandBus,
    terrain_cache: LiveAutotileCache,
    base_terrain_cache: std::cell::RefCell<base_terrain_cache::BaseTerrainChunkCache>,
    chunk_surface_cache: std::cell::RefCell<chunk_surface_cache::ChunkSurfaceDescriptorCache>,
    visible_terrain_plan: std::cell::RefCell<runtime_terrain_pass::VisibleTerrainPlanCache>,
    terrain_scene_surface: std::cell::RefCell<terrain_scene_surface::TerrainSceneSurfaceCache>,
    scene_backdrop_height_cache: std::cell::RefCell<runtime_terrain_pass::SceneBackdropHeightCache>,
    terrain_render_telemetry: render_telemetry::TerrainRenderTelemetry,
    water_material: water_material::WaterMaterialRuntime,
    water_ripples: water_ripple_runtime::WaterRippleRuntime,
    terrain_cache_next_sync_at: f64,
    character_autosave_next_at: f64,
    character_state_sequence: u64,
    last_applied_character_state_sequence: u64,
    building_state_sequence: u64,
    last_applied_building_state_sequence: u64,
    character_appearance_reload_requested: bool,
    terrain_atlas: Option<Texture2D>,
    lpc_terrain_source: Option<Texture2D>,
    lpc_terrain_v7_source: Option<Texture2D>,
    lpc_bridge_source: Option<Texture2D>,
    lpc_cliff_source: Option<Texture2D>,
    lpc_mapped_terrain_atlas: Option<Texture2D>,
    live_autotile_atlas: Option<Texture2D>,
    object_atlas: Option<Texture2D>,
    world_tile_atlas: Option<Texture2D>,
    player_walk_atlas: Option<Texture2D>,
    hud_vitals_frame: Option<Texture2D>,
    hud_hotbar_frame: Option<Texture2D>,
    hud_minimap_frame: Option<Texture2D>,
    item_icon_atlas: Option<Texture2D>,
    item_icon_rects: std::collections::HashMap<String, [f32; 4]>,
    world_map: runtime_world_map::WorldMapState,
    runtime_character_appearance: Option<character_runtime_compositor::RuntimeCharacterAppearance>,
    stamp_registry: haven_assets::stamp_registry::StampRegistry,
    placeable_registry: haven_assets::placeable_asset_registry::PublishedWorldAssetRegistry,
    stamp_textures: std::collections::HashMap<String, Texture2D>,
    placeable_textures: std::collections::HashMap<String, Texture2D>,
    world_visual_override_textures: std::collections::HashMap<String, Texture2D>,
    collision_override_registry: runtime_collision_overrides::RuntimeCollisionOverrideRegistry,
    asset_session: Option<haven_assets::runtime_asset_cache::RuntimeAssetSession>,
    asset_binding_counts: (usize, usize, usize),
    surface_chunks: runtime_surface_streaming::SurfaceChunkRuntime,
    _texture_cache: runtime_texture_cache::StableTextureCache,
    log: GameLog,
}
include!("game_bootstrap.rs");

fn client_session_timestamp() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_secs())
        .unwrap_or_default()
}

fn write_client_session_state(state: &str) {
    let logs = runtime_root().join("logs");
    let _ = std::fs::create_dir_all(&logs);
    let _ = std::fs::write(logs.join("haven_game_session_state.txt"), state.as_bytes());
}

fn mark_client_session_running() {
    let logs = runtime_root().join("logs");
    let crashes = logs.join("crashes");
    let _ = std::fs::create_dir_all(&crashes);
    let state_path = logs.join("haven_game_session_state.txt");
    let timestamp = client_session_timestamp();

    if let Ok(previous) = std::fs::read_to_string(&state_path) {
        if previous.starts_with("running ") {
            let report = format!(
                "Havenwild detected an unclean previous client termination at unix={timestamp}.\nPrevious session state: {previous}\n"
            );
            let report_path = crashes.join(format!("haven_game_unclean_{timestamp}.log"));
            let _ = std::fs::write(&report_path, report.as_bytes());
            let _ = std::fs::write(logs.join("LATEST_CLIENT_CRASH.txt"), report.as_bytes());
        }
    }

    #[cfg(target_os = "windows")]
    let native_dump = native_crash_windows::dump_candidate_path()
        .map(|path| format!("native_dump_candidate={path}\n"))
        .unwrap_or_default();
    #[cfg(not(target_os = "windows"))]
    let native_dump = String::new();

    write_client_session_state(&format!("running unix={timestamp}\n{native_dump}"));
}

fn mark_client_session_clean_exit() {
    write_client_session_state(&format!("clean_exit unix={}\n", client_session_timestamp()));
}

fn install_game_panic_log_hook() {
    let default_hook = std::panic::take_hook();
    std::panic::set_hook(Box::new(move |info| {
        let logs = runtime_root().join("logs");
        let crashes = logs.join("crashes");
        let _ = std::fs::create_dir_all(&crashes);
        let timestamp = client_session_timestamp();
        let cwd = std::env::current_dir()
            .map(|path| path.display().to_string())
            .unwrap_or_else(|_| "<unavailable>".to_string());
        let executable = std::env::current_exe()
            .map(|path| path.display().to_string())
            .unwrap_or_else(|_| "<unavailable>".to_string());
        let crash = format!(
            "Havenwild game panic at unix={timestamp}\nruntime_root={}\ncwd={cwd}\nexecutable={executable}\n{info}\n\nBacktrace:\n{}\n",
            runtime_root().display(),
            Backtrace::force_capture()
        );
        let _ = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(logs.join("haven_game_crash.log"))
            .and_then(|mut file| file.write_all(crash.as_bytes()));
        let report_path = crashes.join(format!("haven_game_panic_{timestamp}.log"));
        let _ = std::fs::write(&report_path, crash.as_bytes());
        let _ = std::fs::write(logs.join("LATEST_CLIENT_CRASH.txt"), crash.as_bytes());
        write_client_session_state(&format!(
            "crashed unix={timestamp}\nreport={}\n",
            report_path.display()
        ));
        default_hook(info);
    }));
}

#[macroquad::main(window_conf)]
async fn main() {
    install_game_panic_log_hook();
    #[cfg(target_os = "windows")]
    native_crash_windows::install();
    mark_client_session_running();
    client_entry::run().await;
    mark_client_session_clean_exit();
}
