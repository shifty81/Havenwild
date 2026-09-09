mod animation_studio;
mod animation_studio_input;
mod animation_studio_render;
mod animation_studio_runtime_context;
mod asset_browser_ui;
mod authoring_publish;
mod asset_hot_reload;
mod asset_palette_panel;
mod atlas_render;
mod autotile_authoring;
mod autotile_render;
mod authoring_changeset;
mod bulk_result;
mod building_instance_preview;
mod brush_authoring;
mod brush_palette_drawer;
mod canvas_camera;
mod canvas_controller;
mod canvas_layers;
mod canvas_tool_rack;
mod canvas_view;
mod canvas_workspace;
mod command_registry;
mod character_studio;
mod character_studio_layout;
mod clipboard_tools;
mod collision_authoring;
mod draw;
mod development_session;
mod direct_visual_authoring;
mod document_authority;
mod document_lifecycle;
mod document_tabs;
mod pixel_library_panel;
mod world_surface_authoring_geometry;
mod editor_help;
mod editor_settings;
mod editor_menu;
mod editor_theme;
mod editor_text;
mod editor_types;
mod enclosed_scene_authoring;
mod gameplay_layer_authoring;
mod game_canvas_ui;
mod gui_authority;
mod gui_controls;
mod input;
mod island_authoring;
mod island_workspace;
mod logic_studio;
mod object_inspector;
mod terrain_transition_workbench;
mod terrain_tile_variant_authoring;
mod terrain_material_browser;
mod tooltip_overlay;
mod pixel_animation_bridge;
mod pixel_color_panel;
mod pixel_layer_input;
mod pixel_layer_rail;
mod pixel_context_layout;
mod pixel_new_document;
mod pixel_studio;
mod pixel_studio_input;
mod pixel_studio_layout;
mod pixel_studio_render;
mod pcg_exemplar_authoring;
mod production_tools;
mod prepared_canvas_composition;
mod render_helpers;
mod resource_context_bridge;
mod right_dock;
mod scene_render_helpers;
mod scene_asset_context;
mod scene_authoring;
mod scene_bank_workspace;
mod scene_outliner;
mod shared_palette;
mod selection_controller;
mod sprite_canvas_authority;
mod sprite_workspace;
mod sound_studio;
mod stamp_inspector_panel;
mod structural_cliff_preview;
mod tool_registry;
mod transform_gizmo;
mod ui_shell;
mod unified_asset_browser;
mod world_asset_pixel_bridge;
mod world_canvas_context;
mod world_surface_editor;
mod world_surface_authoring;
mod world_surface_authoring_ui;
mod world_surface_structural_authoring;
mod workspace_chrome;
mod workspace_shell;

use std::{collections::{HashMap, HashSet}, time::SystemTime};

use animation_studio::AnimationStudioState;
use atlas_render::EditorTextureSet;
use canvas_camera::CanvasCameraState;
use canvas_view::{
    draw_canvas_rulers, draw_canvas_toolbar, draw_infinite_grid, draw_scene_into_rect,
    CanvasToolbarKind,
};
use character_studio::CharacterStudioState;
use logic_studio::LogicStudioState;
pub(crate) use editor_types::*;
use editor_text::{draw_editor_text, measure_editor_text};
use haven_assets::{
    asset_browser::AssetBrowserSnapshot,
    asset_intake::{repo_root_dir, AssetIntakeCatalog},
    building_instance::{BuildingInstanceRegistry, BuildingInstanceViewState},
    building_recipe::BuildingRecipeRegistry,
    asset_palette::{
        AssetPaletteCatalog, AssetPaletteCategory, AssetPaletteState, PALETTE_OBJECTS,
    },
    live_autotile_atlas::live_autotile_atlas_registry,
    placeable_asset_registry::PublishedWorldAssetRegistry,
    runtime_asset_cache::RuntimeAssetSession,
    stamp_registry::StampRegistry,
};
use haven_core::{
    ObjectKind, PlacedObject, PlacedStamp, ProjectSceneId, SceneBiome, SceneId, SceneKind,
    SceneMap, TerrainPaintMode, TileKind, ZoneKind, MAP_H, MAP_W,
};
use haven_editor::{
    clear_scene_autotile_override, copy_scene_selection,
    create_project_scene, create_scene_transition, delete_project_scene, delete_scene_selection,
    duplicate_project_scene, erase_scene_cell,
    erase_scene_object, erase_scene_stamp, erase_scene_transition, flood_fill_scene,
    hit_test_scene_cell, load_active_scene_rectangle_assignments,
    load_active_scene_rectangle_manifest, load_editor_project_file_from_path, move_scene_object,
    move_scene_selection, move_scene_stamp, paint_scene_rectangle, paint_scene_tile_with_mode,
    paint_scene_zone, paste_scene_clipboard, place_scene_object_with_footprint,
    place_scene_pack_asset, place_scene_stamp, rename_project_scene, replace_scene_value,
    resize_scene_transition, update_scene_transition_destination, selection_bounds_for_items,
    selection_items_in_rect, set_scene_autotile_override, update_scene_object, update_scene_stamp,
    adjust_world_structural_levels, copy_world_surface_rectangle,
    flood_fill_world_surface,
    paint_world_surface_cells, paint_world_surface_rectangle, paste_world_surface_clipboard,
    place_world_structural_connector, replace_world_surface_value,
    resolve_world_structural_connector_plan, resolve_world_surface_cell,
    validate_world_surface_footprint,
    EditorCommand, EditorCommandBus,
    EditorCommandKind, EditorCommandSource, EditorSelection,
    EditorValidationReport, EditorWorldModel, GridPos, GridRect, RegionNodeId,
    SceneAuthoringLayer, SceneClipboard, SelectionItem, StampUpdateRequest,
    WorldStructuralConnectorKind, WorldStructuralConnectorPlan, WorldSurfaceClipboard,
    WorldSurfaceValue, STARTER_PROJECT_FILE_PATH,
};
use haven_save::{load_world_from_path, save_world_to_path};
use haven_world::autotile::{AutotileSyncReport, LiveAutotileCache};
use haven_world::harbor_routes::{HarborRouteCatalog, HARBOR_ROUTE_CATALOG_PATH};
use haven_world::region_graph::{
    IslandRegionGraph, RegionLink, RegionLinkKind, RegionNodeKind,
};
use haven_world::scene_rectangles::{
    scene_ownership_catalog, scene_role_catalog, SceneRectangleAssignmentsFile,
    SceneRectangleManifest, SCENE_RECTANGLE_ASSIGNMENTS_PATH, SCENE_RECTANGLE_MANIFEST_PATH,
};
use macroquad::prelude::*;
use pixel_studio::PixelStudioState;
use render_helpers::draw_scissored_text;
use scene_asset_context::SceneAssetContextMenu;
use sound_studio::SoundStudioState;
use structural_cliff_preview::StructuralCliffPreviewCache;
use world_canvas_context::WorldCanvasContextMenu;
use world_surface_editor::{
    draw_scene_rectangle_map, rectangle_is_overworld_surface, world_archipelago_overview_bounds,
    world_landmass_at_global_cell, world_overview_landmass_at_point,
    world_scene_grid_bounds_for_landmass, world_scene_grid_rect, WorldSurfaceViewOptions,
};
use workspace_shell::{DocumentSplitMode, EditorWorkspaceShellState, RightDockTab, WorkspaceResizeDrag};

const PANEL_BG: Color = Color::new(0.055, 0.065, 0.078, 0.98);
const PANEL_EDGE: Color = Color::new(0.24, 0.29, 0.35, 1.0);
const TEXT: Color = Color::new(0.91, 0.94, 0.97, 1.0);
const MUTED: Color = Color::new(0.58, 0.64, 0.71, 1.0);
const GOOD: Color = Color::new(0.32, 0.78, 0.55, 1.0);
const WARN: Color = Color::new(0.96, 0.62, 0.30, 1.0);
const ACCENT: Color = Color::new(0.20, 0.48, 0.78, 1.0);
const CONTROL_BG: Color = Color::new(0.09, 0.11, 0.14, 1.0);

const OBJECT_BRUSHES: [ObjectKind; PALETTE_OBJECTS.len()] = PALETTE_OBJECTS;
const ZONE_BRUSHES: [ZoneKind; 17] = [
    ZoneKind::Tavern,
    ZoneKind::Kitchen,
    ZoneKind::GuestRoom,
    ZoneKind::Cellar,
    ZoneKind::Greenhouse,
    ZoneKind::Field,
    ZoneKind::Cave,
    ZoneKind::StaffOnly,
    ZoneKind::PublicPath,
    ZoneKind::TavernExterior,
    ZoneKind::Bar,
    ZoneKind::CivicLot,
    ZoneKind::MarketLot,
    ZoneKind::ResidentialLot,
    ZoneKind::ArtisanLot,
    ZoneKind::HarborLot,
    ZoneKind::AgriculturalLot,
];

use std::time::Instant;

pub(crate) struct EditorApp {
    model: EditorWorldModel,
    selected_rectangle: usize,
    selected_landmass_id: i32,
    selected_scene: usize,
    scene_list_offset: usize,
    object_list_offset: usize,
    object_filter: String,
    asset_catalog: AssetPaletteCatalog,
    asset_palette_state: AssetPaletteState,
    asset_filter: String,
    asset_category: AssetPaletteCategory,
    asset_favorites_only: bool,
    asset_recent_only: bool,
    asset_list_offset: usize,
    brush_palette_offset: usize,
    asset_drag: Option<asset_palette_panel::AssetPaletteDrag>,
    selected_source_reference: Option<String>,
    asset_browser: AssetBrowserSnapshot,
    asset_pack_mounted_count: usize,
    asset_pack_failure_count: usize,
    asset_pack_source_count: usize,
    asset_intake_catalog: AssetIntakeCatalog,
    asset_hot_reload_requested: bool,
    asset_hot_reload_next_check: f64,
    asset_manifest_modified: Option<SystemTime>,
    editor_textures: EditorTextureSet,
    text_focus: EditorTextFocus,
    scene_name_edit: Option<SceneNameEditState>,
    scene_delete_armed: Option<ProjectSceneId>,
    footprint_edit_target: FootprintEditTarget,
    scene_cursor_x: i32,
    scene_cursor_y: i32,
    last_painted_cell: Option<(i32, i32)>,
    scene_edit_tool: SceneEditTool,
    scene_layer_mode: SceneLayerMode,
    terrain_paint_mode: TerrainPaintMode,
    selected_tile: usize,
    terrain_material_catalog: terrain_material_browser::TerrainMaterialCatalog,
    world_terrain_browser_open: bool,
    world_terrain_browser_scroll: usize,
    selected_object: usize,
    selected_placeable_id: Option<String>,
    selected_placeable_preview_state: usize,
    stamp_registry: StampRegistry,
    placeable_registry: PublishedWorldAssetRegistry,
    building_recipe_registry: BuildingRecipeRegistry,
    building_instance_registry: BuildingInstanceRegistry,
    building_preview_views: HashMap<String, BuildingInstanceViewState>,
    selected_stamp_id: Option<String>,
    selection: EditorSelection,
    scene_drag: Option<SceneCanvasDrag>,
    scene_clipboard: Option<SceneClipboard>,
    scene_paste_anchor: Option<GridPos>,
    scene_layers: [SceneLayerState; 4],
    selected_zone: usize,
    selected_transition_target: usize,
    selected_scene_cycle: usize,
    selected_role_cycle: usize,
    selected_ownership_cycle: usize,
    scene_rectangles: Option<SceneRectangleManifest>,
    scene_assignments: SceneRectangleAssignmentsFile,
    harbor_routes: HarborRouteCatalog,
    route_source_landmass_id: Option<i32>,
    viewport_mode: EditorViewportMode,
    workspace_shell: EditorWorkspaceShellState,
    workspace_resize_drag: Option<WorkspaceResizeDrag>,
    layout_audit_overlay: bool,
    pixel_symmetry_popup_open: bool,
    pixel_brush_popup_open: bool,
    canvas_layer_resize_active: bool,
    pixel_layer_drag: Option<pixel_layer_rail::PixelLayerDragState>,
    pixel_layer_menu_anchor: Option<Vec2>,
    canvas_active_tool: tool_registry::UniversalTool,
    canvas_layer_context_override: Option<canvas_layers::CanvasLayerKind>,
    /// A14AA: visible state and editing selection are separate authorities.
    /// The left visibility control toggles rendering only; row/name clicks may
    /// keep multiple Game Canvas layers selected for authoring.
    canvas_selected_layer_kinds: HashSet<canvas_layers::CanvasLayerKind>,
    canvas_hidden_layer_kinds: HashSet<canvas_layers::CanvasLayerKind>,
    canvas_authoring_context: brush_authoring::CanvasAuthoringContext,
    transform_gizmo_drag: Option<transform_gizmo::TransformGizmoDrag>,
    help_center: editor_help::HelpCenterState,
    direct_visual_canvas: Option<direct_visual_authoring::DirectVisualCanvasState>,
    pixel_color_popup_open: bool,
    pixel_color_edit_background: bool,
    pixel_color_add_mode: bool,
    pixel_color_draft: [u8; 4],
    unified_asset_browser: unified_asset_browser::UnifiedAssetBrowserRuntime,
    show_collision_overlay: bool,
    saved_undo_depth: usize,
    open_menu: Option<editor_menu::EditorMenuKind>,
    scene_canvas: CanvasCameraState,
    scene_canvas_states: HashMap<ProjectSceneId, CanvasCameraState>,
    scene_document_states: HashMap<ProjectSceneId, document_tabs::SceneDocumentUiState>,
    open_scene_documents: Vec<ProjectSceneId>,
    recently_closed_scene_documents: Vec<ProjectSceneId>,
    last_active_scene_document: Option<ProjectSceneId>,
    scene_document_dirty_ids: HashSet<ProjectSceneId>,
    scene_tab_overflow_open: bool,
    autotile_caches: HashMap<ProjectSceneId, LiveAutotileCache>,
    structural_cliff_caches: HashMap<ProjectSceneId, StructuralCliffPreviewCache>,
    autotile_preview_enabled: bool,
    autotile_dirty_overlay: bool,
    scene_show_grid: bool,
    selected_autotile_preset: usize,
    world_canvas: CanvasCameraState,
    world_canvas_pan_tool: bool,
    world_edit_tool: WorldEditTool,
    world_layer_mode: WorldLayerMode,
    world_drag: Option<WorldCanvasDrag>,
    world_selection: Option<GridRect>,
    world_clipboard: Option<WorldSurfaceClipboard>,
    world_paste_anchor: Option<GridPos>,
    world_asset_place_anchor: Option<GridPos>,
    world_structural_level: u8,
    world_brush_radius: i32,
    world_last_painted: Option<GridPos>,
    world_show_partitions: bool,
    /// Canonical creation settings for the persistent development world. The
    /// editor and runtime must derive macro geography from the same seed/profile.
    development_world_settings: haven_world::WorldCreationSettings,
    /// Complete finite-world semantic LOD shared with the runtime world map.
    /// This replaces the legacy `world_rect_preview_px` archipelago drawing.
    development_world_semantic_bake: Option<haven_world::SemanticWorldBakeV1>,
    /// Runtime/editor navigation authority. The gameplay client publishes this
    /// independently from its heartbeat so studio switches retain the exact
    /// character/equipment/action/frame chain.
    resource_context: Option<haven_authoring::ResourceContext>,
    resource_context_next_check: f64,
    resource_context_loaded_character: Option<String>,
    resource_context_runtime_ui_focus: Option<String>,
    /// UI/loading/menu documents are resources hosted inside Game Canvas, not a separate studio.
    game_canvas_ui: game_canvas_ui::GameCanvasUiState,
    /// R37: the World Studio camera defaults to the complete finite Havenwild
    /// world; the selected landmass remains the mutation/inspection context.
    world_show_entire_world: bool,
    world_cursor_x: i32,
    world_cursor_y: i32,
    world_canvas_context_menu: Option<WorldCanvasContextMenu>,
    scene_asset_context_menu: Option<SceneAssetContextMenu>,
    primary_pointer_owned_by_ui: bool,
    gui_interaction: gui_controls::GuiInteractionState,
    command_bus: EditorCommandBus,
    pixel_studio: PixelStudioState,
    animation_studio: AnimationStudioState,
    character_studio: CharacterStudioState,
    logic_studio: LogicStudioState,
    sound_studio: SoundStudioState,
    diagnostics: haven_diagnostics::DiagnosticsHub,
    background_jobs: Vec<haven_jobs::JobRecord>,
    authoring_session: Option<haven_authoring::AuthoringSession>,
    status_message: String,
    development_client: Option<std::process::Child>,
    editor_settings: editor_settings::EditorSettingsState,
    pending_document_close: Option<document_lifecycle::PendingDocumentClose>,
    closed_workspace_documents: HashSet<EditorViewportMode>,
    recently_closed_workspace_documents: Vec<EditorViewportMode>,
}

impl EditorApp {
    pub(crate) fn new_without_textures() -> Self {
        let asset_catalog = AssetPaletteCatalog::load_default().unwrap_or_default();
        let asset_palette_state = AssetPaletteState::load_default();
        let asset_browser = AssetBrowserSnapshot::load_project(std::path::Path::new("."));
        let asset_intake_catalog = AssetIntakeCatalog::load_default().unwrap_or_default();
        let asset_session = RuntimeAssetSession::discover_tolerant(&repo_root_dir());
        let asset_pack_mounted_count = asset_session.registry.mounted_pack_count();
        let asset_pack_failure_count = asset_session.discovery.failed_count();
        let asset_pack_source_count = asset_session.sources.len();
        let stamp_registry = StampRegistry::load_discovered(&asset_session)
            .or_else(|_| StampRegistry::load_default())
            .unwrap_or_default();
        let placeable_registry = PublishedWorldAssetRegistry::load_discovered(&asset_session)
            .unwrap_or_default();
        // W57K8: building and texture authority must resolve from the repository root, not
        // the process working directory. A native-editor launch can originate
        // from target/, a shortcut, or the Control Center, so using "." could
        // silently produce empty recipe/instance registries and hide every
        // building from the Scene Editor. Preserve a visible startup warning if
        // either registry fails instead of swallowing the error completely.
        let building_project_root = repo_root_dir();
        let mut building_authority_warnings = Vec::new();
        let building_recipe_registry = match BuildingRecipeRegistry::load_from_project_root(&building_project_root) {
            Ok(registry) => registry,
            Err(error) => {
                building_authority_warnings.push(format!("building recipes: {error}"));
                BuildingRecipeRegistry::default()
            }
        };
        let building_instance_registry = match BuildingInstanceRegistry::load_from_project_root(
            &building_project_root,
            &building_recipe_registry,
        ) {
            Ok(registry) => registry,
            Err(error) => {
                building_authority_warnings.push(format!("building instances: {error}"));
                BuildingInstanceRegistry::default()
            }
        };
        let building_preview_views = building_instance_registry
            .initial_view_states()
            .into_iter()
            .map(|(id, state)| {
                let state = building_instance_registry
                    .entry(&id)
                    .and_then(|instance| {
                        building_recipe_registry
                            .entry(&instance.recipe_id)
                            .map(|recipe| {
                                building_instance_preview::building_preview_state_for_recipe(
                                    instance, recipe,
                                )
                            })
                    })
                    .unwrap_or(state);
                (id, state)
            })
            .collect();
        let building_recipe_count = building_recipe_registry.entries().len();
        let building_instance_count = building_instance_registry.entries().len();
        let building_authority_warning_suffix = if building_authority_warnings.is_empty() {
            String::new()
        } else {
            format!(" WARNING [{}]", building_authority_warnings.join("; "))
        };
        let editor_textures = EditorTextureSet::empty();
        let terrain_material_catalog = terrain_material_browser::TerrainMaterialCatalog::load_default().unwrap_or_default();
        let development_world_settings = development_session::development_world_settings();
        let development_world_semantic_bake =
            development_session::development_semantic_world_bake(&development_world_settings);
        let asset_manifest_modified = None;
        let texture_summary = "asset textures deferred until the first visible frame".to_string();
        let mut model = EditorWorldModel::starter();
        let editor_world_path = development_session::editor_world_path();
        if let Ok(mut saved_world) = load_world_from_path(&editor_world_path.to_string_lossy()) {
            if let Ok(descriptor) = development_session::DevelopmentWorldDescriptor::load() {
                if development_session::ensure_acceptance_crate(&mut saved_world, &descriptor).is_ok() {
                    let _ = save_world_to_path(&editor_world_path.to_string_lossy(), &saved_world);
                }
            }
            model.world = saved_world;
        }
        let canonicalized_world_assets =
            placeable_registry.canonicalize_world_aliases(&mut model.world);
        let mut app = Self {
            model,
            selected_rectangle: 0,
            selected_landmass_id: 0,
            selected_scene: 0,
            scene_list_offset: 0,
            object_list_offset: 0,
            object_filter: String::new(),
            asset_catalog,
            asset_palette_state,
            asset_filter: String::new(),
            asset_category: AssetPaletteCategory::All,
            asset_favorites_only: false,
            asset_recent_only: false,
            asset_list_offset: 0,
            brush_palette_offset: 0,
            asset_drag: None,
            selected_source_reference: None,
            asset_browser,
            asset_pack_mounted_count,
            asset_pack_failure_count,
            asset_pack_source_count,
            asset_intake_catalog,
            asset_hot_reload_requested: false,
            asset_hot_reload_next_check: 0.0,
            asset_manifest_modified,
            editor_textures,
            text_focus: EditorTextFocus::None,
            scene_name_edit: None,
            scene_delete_armed: None,
            footprint_edit_target: FootprintEditTarget::Visual,
            scene_cursor_x: 24,
            scene_cursor_y: 16,
            last_painted_cell: None,
            scene_edit_tool: SceneEditTool::Select,
            scene_layer_mode: SceneLayerMode::Terrain,
            terrain_paint_mode: TerrainPaintMode::Exact,
            selected_tile: 5,
            terrain_material_catalog,
            world_terrain_browser_open: false,
            world_terrain_browser_scroll: 0,
            selected_object: 0,
            selected_placeable_id: placeable_registry
                .entries()
                .first()
                .map(|entry| entry.stable_id.clone()),
            selected_placeable_preview_state: 0,
            stamp_registry,
            placeable_registry,
            building_recipe_registry,
            building_instance_registry,
            building_preview_views,
            selected_stamp_id: None,
            selection: EditorSelection::default(),
            scene_drag: None,
            scene_clipboard: None,
            scene_paste_anchor: None,
            scene_layers: [
                SceneLayerState::default(),
                SceneLayerState::default(),
                SceneLayerState {
                    visible: false,
                    locked: false,
                    opacity: 1.0,
                },
                SceneLayerState {
                    visible: false,
                    locked: false,
                    opacity: 1.0,
                },
            ],
            selected_zone: 0,
            selected_transition_target: 1,
            selected_scene_cycle: 0,
            selected_role_cycle: 0,
            selected_ownership_cycle: 0,
            scene_rectangles: load_active_scene_rectangle_manifest().ok(),
            scene_assignments: load_active_scene_rectangle_assignments().unwrap_or(
                SceneRectangleAssignmentsFile {
                    schema: "havenwild.scene_rectangle_assignments.v008".to_string(),
                    assignments: Vec::new(),
                },
            ),
            harbor_routes: HarborRouteCatalog::load_from_path(HARBOR_ROUTE_CATALOG_PATH)
                .unwrap_or_default(),
            route_source_landmass_id: None,
            viewport_mode: EditorViewportMode::SceneRectangles,
            workspace_shell: EditorWorkspaceShellState::load_default(),
            workspace_resize_drag: None,
            layout_audit_overlay: false,
            pixel_symmetry_popup_open: false,
            pixel_brush_popup_open: false,
            canvas_layer_resize_active: false,
            pixel_layer_drag: None,
            pixel_layer_menu_anchor: None,
            canvas_active_tool: tool_registry::UniversalTool::Select,
            canvas_layer_context_override: None,
            canvas_selected_layer_kinds: [canvas_layers::CanvasLayerKind::Terrain].into_iter().collect(),
            canvas_hidden_layer_kinds: [
                canvas_layers::CanvasLayerKind::Collision,
                canvas_layers::CanvasLayerKind::Zones,
                canvas_layers::CanvasLayerKind::Links,
            ].into_iter().collect(),
            canvas_authoring_context: brush_authoring::CanvasAuthoringContext::default(),
            transform_gizmo_drag: None,
            help_center: editor_help::HelpCenterState::default(),
            direct_visual_canvas: None,
            pixel_color_popup_open: false,
            pixel_color_edit_background: false,
            pixel_color_add_mode: false,
            pixel_color_draft: [0, 0, 0, 255],
            unified_asset_browser: unified_asset_browser::UnifiedAssetBrowserRuntime::default(),
            show_collision_overlay: false,
            saved_undo_depth: 0,
            open_menu: None,
            editor_settings: editor_settings::EditorSettingsState::load_default(),
            pending_document_close: None,
            closed_workspace_documents: HashSet::new(),
            recently_closed_workspace_documents: Vec::new(),
            scene_canvas: CanvasCameraState::default(),
            scene_canvas_states: HashMap::new(),
            scene_document_states: HashMap::new(),
            open_scene_documents: Vec::new(),
            recently_closed_scene_documents: Vec::new(),
            last_active_scene_document: None,
            scene_document_dirty_ids: HashSet::new(),
            scene_tab_overflow_open: false,
            autotile_caches: HashMap::new(),
            structural_cliff_caches: HashMap::new(),
            autotile_preview_enabled: true,
            autotile_dirty_overlay: false,
            scene_show_grid: false,
            selected_autotile_preset: 15,
            world_canvas: CanvasCameraState::default(),
            world_canvas_pan_tool: false,
            world_edit_tool: WorldEditTool::Select,
            world_layer_mode: WorldLayerMode::Terrain,
            world_drag: None,
            world_selection: None,
            world_clipboard: None,
            world_paste_anchor: None,
            world_asset_place_anchor: None,
            world_structural_level: 2,
            world_brush_radius: 0,
            world_last_painted: None,
            world_show_partitions: false,
            development_world_settings,
            development_world_semantic_bake,
            resource_context: haven_authoring::read_resource_context(&repo_root_dir())
                .ok()
                .flatten(),
            resource_context_next_check: 0.0,
            resource_context_loaded_character: None,
            resource_context_runtime_ui_focus: None,
            game_canvas_ui: game_canvas_ui::GameCanvasUiState::load_default(),
            world_show_entire_world: true,
            world_cursor_x: 0,
            world_cursor_y: 0,
            world_canvas_context_menu: None,
            scene_asset_context_menu: None,
            primary_pointer_owned_by_ui: false,
            gui_interaction: gui_controls::GuiInteractionState::default(),
            command_bus: EditorCommandBus::with_limit(16),
            pixel_studio: PixelStudioState::new(),
            animation_studio: AnimationStudioState::new(),
            character_studio: CharacterStudioState::new(),
            logic_studio: LogicStudioState::new(),
            sound_studio: SoundStudioState::new(),
            diagnostics: haven_diagnostics::DiagnosticsHub::default(),
            background_jobs: vec![haven_jobs::JobRecord::queued("Asset library warm-up")],
            authoring_session: None,
            development_client: None,
            status_message: format!(
                "Asset palette ready | published aliases canonicalized={} | buildings recipes={} instances={}{} | {} | {}",
                canonicalized_world_assets,
                building_recipe_count,
                building_instance_count,
                building_authority_warning_suffix,
                live_autotile_atlas_registry()
                    .map(|registry| registry.coverage_summary())
                    .unwrap_or_else(|error| format!("live atlas warning: {error}")),
                texture_summary
            ),
        };
        app.diagnostics.emit(haven_diagnostics::DiagnosticEvent::new(
            haven_diagnostics::DiagnosticLevel::Info,
            "editor.foundation",
            "W62 unified diagnostics/identity/schema/jobs/audio/logic foundation initialized",
        ));
        app.restore_generated_harbor_routes();
        if let Ok(descriptor) = development_session::DevelopmentWorldDescriptor::load() {
            // AC2: the descriptor's default scene is useful selection/outliner
            // context, but it must not take ownership of the Game Canvas. The
            // previous farmstead fallback literally forced every editor launch
            // into Estate/SceneMap and auto-opened that document. The canonical Estate
            // remains a compatibility scene ID, but it is never a startup fallback.
            let requested_scene = ProjectSceneId::new(descriptor.default_scene.as_str());
            if let Some(index) = app.model.world.scenes.position(&requested_scene) {
                app.selected_scene = index;
                app.ensure_scene_visible();
                if let Some(scene) = app.model.world.scenes.get(index) {
                    app.scene_cursor_x = scene.spawn_x;
                    app.scene_cursor_y = scene.spawn_y;
                }
            }
        }
        // Complete World is the authoritative safe/default startup surface.
        // Individual Estate/interior/partition documents open only on explicit
        // user navigation (or a future persisted last-document restoration).
        app.frame_entire_world();
        app
    }

    pub(crate) async fn load_editor_assets(&mut self) {
        // Load only the compact runtime atlas set during startup. Raw intake
        // source sheets are intentionally loaded on demand from the Intake tab;
        // eager decoding of a large source sheet could block the Windows event
        // loop long enough for the editor window to be ghosted as unresponsive.
        let editor_textures = EditorTextureSet::load().await;
        self.asset_manifest_modified = editor_textures.user_registry().modified();
        let texture_summary = editor_textures.readiness_summary();
        self.editor_textures = editor_textures;
        self.status_message =
            format!("Editor assets loaded | {texture_summary} | intake previews load on demand");
    }
}

pub(crate) fn window_conf() -> Conf {
    let high_dpi = std::env::var("HAVENWILD_EDITOR_HIGH_DPI")
        .map(|value| {
            matches!(
                value.trim().to_ascii_lowercase().as_str(),
                "1" | "true" | "yes" | "on"
            )
        })
        .unwrap_or(false);
    Conf {
        window_title: "Havenwild Native Editor".to_string(),
        window_width: 1600,
        window_height: 900,
        high_dpi,
        sample_count: 1,
        ..Default::default()
    }
}

fn safe_mode_requested() -> bool {
    std::env::args().any(|argument| argument == "--safe-mode")
        || std::env::var("HAVENWILD_EDITOR_SAFE_MODE")
            .map(|value| {
                matches!(
                    value.trim().to_ascii_lowercase().as_str(),
                    "1" | "true" | "yes" | "on"
                )
            })
            .unwrap_or(false)
}

fn draw_bootstrap_screen(stage: &str, progress: f32) {
    // H21-A14Y: this deliberately uses Macroquad's bootstrap font instead of the
    // editor font atlas. It can therefore render *before* Segoe initialization and
    // eliminates the misleading blank/frozen window during font prewarm.
    set_default_camera();
    gl_use_default_material();
    clear_background(Color::new(0.025, 0.03, 0.04, 1.0));
    let width = screen_width();
    let height = screen_height();
    let panel_w = 620.0_f32.min((width - 40.0).max(260.0));
    let panel_h = 190.0_f32.min((height - 40.0).max(150.0));
    let panel = Rect::new((width - panel_w) * 0.5, (height - panel_h) * 0.5, panel_w, panel_h);
    draw_rectangle(panel.x, panel.y, panel.w, panel.h, Color::new(0.055, 0.06, 0.075, 1.0));
    draw_rectangle_lines(panel.x, panel.y, panel.w, panel.h, 2.0, Color::new(0.22, 0.24, 0.29, 1.0));
    draw_text("Havenwild Native Editor", panel.x + 28.0, panel.y + 54.0, 30.0, WHITE);
    draw_text(stage, panel.x + 28.0, panel.y + 94.0, 20.0, Color::new(0.72, 0.75, 0.80, 1.0));
    let track = Rect::new(panel.x + 28.0, panel.y + 124.0, (panel.w - 56.0).max(40.0), 12.0);
    draw_rectangle(track.x, track.y, track.w, track.h, Color::new(0.10, 0.11, 0.13, 1.0));
    draw_rectangle(track.x, track.y, track.w * progress.clamp(0.0, 1.0), track.h, Color::new(0.90, 0.26, 0.06, 1.0));
    draw_text("Startup diagnostics are written to the editor session log.", panel.x + 28.0, panel.y + 164.0, 15.0, Color::new(0.55, 0.58, 0.64, 1.0));
}

fn draw_startup_screen(stage: &str, detail: &str, progress: f32) {
    set_default_camera();
    gl_use_default_material();
    clear_background(Color::new(0.025, 0.03, 0.04, 1.0));
    let width = screen_width();
    let height = screen_height();
    let panel_w = 660.0_f32.min((width - 40.0).max(280.0));
    let panel_h = 214.0_f32.min((height - 40.0).max(170.0));
    let panel = Rect::new((width - panel_w) * 0.5, (height - panel_h) * 0.5, panel_w, panel_h);
    draw_rectangle(panel.x, panel.y, panel.w, panel.h, PANEL_BG);
    draw_rectangle_lines(panel.x, panel.y, panel.w, panel.h, 2.0, PANEL_EDGE);
    draw_editor_text("Havenwild Native Editor", panel.x + 28.0, panel.y + 52.0, 30.0, TEXT);
    draw_editor_text(stage, panel.x + 28.0, panel.y + 90.0, 20.0, TEXT);
    draw_scissored_text(detail, panel.x + 28.0, panel.y + 116.0, panel.w - 56.0, 15.0, MUTED);
    let track = Rect::new(panel.x + 28.0, panel.y + 144.0, (panel.w - 56.0).max(40.0), 12.0);
    draw_rectangle(track.x, track.y, track.w, track.h, editor_theme::colors::CONTROL_BG);
    draw_rectangle(track.x, track.y, track.w * progress.clamp(0.0, 1.0), track.h, editor_theme::colors::ACCENT);
    draw_editor_text(
        "Use --safe-mode if an imported asset causes startup trouble.",
        panel.x + 28.0,
        panel.y + 188.0,
        14.0,
        MUTED,
    );
}

fn panic_message(payload: Box<dyn std::any::Any + Send>) -> String {
    if let Some(message) = payload.downcast_ref::<&str>() {
        (*message).to_string()
    } else if let Some(message) = payload.downcast_ref::<String>() {
        message.clone()
    } else {
        "unknown editor panic".to_string()
    }
}

fn draw_fault_screen(message: &str) {
    set_default_camera();
    gl_use_default_material();
    clear_background(Color::new(0.035, 0.02, 0.025, 1.0));
    draw_editor_text("Editor frame fault contained", 36.0, 58.0, 30.0, WARN);
    draw_editor_text(
        "The editor stayed open so the diagnostic can be read.",
        36.0,
        94.0,
        20.0,
        TEXT,
    );
    draw_scissored_text(
        message,
        36.0,
        136.0,
        (screen_width() - 72.0).max(120.0),
        18.0,
        MUTED,
    );
    draw_editor_text(
        "Press R to rebuild the editor shell in safe mode.",
        36.0,
        184.0,
        18.0,
        TEXT,
    );
    draw_editor_text(
        "See logs/haven_editor_native_crash.log for the full panic record.",
        36.0,
        214.0,
        16.0,
        MUTED,
    );
}

pub(crate) async fn run() {
    let safe_mode = safe_mode_requested();
    let startup_started = Instant::now();

    // H21-A14Y: show useful feedback before any expensive synchronous startup
    // work. The previous sequence initialized/prewarmed the font atlas first,
    // leaving a visible window that appeared frozen for many seconds.
    draw_bootstrap_screen("Opening editor window...", 0.03);
    next_frame().await;
    draw_bootstrap_screen("Preparing editor font atlas...", 0.10);
    next_frame().await;
    let font_started = Instant::now();
    crate::append_editor_log(&editor_text::initialize_editor_font());
    editor_text::prewarm_editor_font();
    crate::append_editor_log(&format!(
        "STARTUP PHASE font atlas ready in {:.1} ms",
        font_started.elapsed().as_secs_f64() * 1000.0
    ));
    draw_startup_screen(
        "Editor typography ready",
        "Loading project authorities, registries, world settings, and workspace state...",
        0.24,
    );
    next_frame().await;

    let authority_started = Instant::now();
    let mut app = loop {
        match std::panic::catch_unwind(std::panic::AssertUnwindSafe(
            EditorApp::new_without_textures,
        )) {
            Ok(app) => break app,
            Err(payload) => {
                let message = format!("Startup fault: {}", panic_message(payload));
                loop {
                    draw_fault_screen(&message);
                    draw_editor_text(
                        "Press R to retry the startup shell, or close the window.",
                        36.0,
                        246.0,
                        17.0,
                        TEXT,
                    );
                    if is_key_pressed(KeyCode::R) {
                        break;
                    }
                    next_frame().await;
                }
            }
        }
    };
    crate::append_editor_log(&format!(
        "STARTUP PHASE project authority ready in {:.1} ms",
        authority_started.elapsed().as_secs_f64() * 1000.0
    ));
    if std::env::args().any(|argument| argument == "--pixel-studio") {
        app.viewport_mode = EditorViewportMode::PixelStudio;
        app.status_message = "Pixel Studio opened from the Bash workflow".to_string();
    }
    if std::env::args().any(|argument| argument == "--animation-studio") {
        app.viewport_mode = EditorViewportMode::AnimationStudio;
        app.status_message = "Animation Studio opened from the Bash workflow".to_string();
    }
    if std::env::args().any(|argument| argument == "--character-studio") {
        app.viewport_mode = EditorViewportMode::CharacterStudio;
        app.status_message = "Character Studio opened from the Bash workflow".to_string();
    }
    if std::env::args().any(|argument| argument == "--logic-studio") {
        app.viewport_mode = EditorViewportMode::LogicStudio;
        app.status_message = "Logic Studio opened from the Bash workflow".to_string();
    }
    if std::env::args().any(|argument| argument == "--sound-studio") {
        app.viewport_mode = EditorViewportMode::SoundStudio;
        app.status_message = "Sound Studio opened from the Bash workflow".to_string();
    }

    draw_startup_screen(
        "Preparing document surfaces",
        "Restoring canvas documents and editor-owned authoring state...",
        0.58,
    );
    next_frame().await;
    if safe_mode {
        app.status_message = "Safe mode active: atlas textures were not loaded".to_string();
    } else {
        draw_startup_screen(
            "Loading visual atlases",
            "Preparing project thumbnails, authored overrides, and render-ready editor assets...",
            0.72,
        );
        next_frame().await;
        let assets_started = Instant::now();
        app.load_editor_assets().await;
        crate::append_editor_log(&format!(
            "STARTUP PHASE visual assets ready in {:.1} ms",
            assets_started.elapsed().as_secs_f64() * 1000.0
        ));
    }
    draw_startup_screen(
        "Finalizing workspace",
        "Restoring Game Canvas state, studio documents, and panel layout...",
        0.92,
    );
    next_frame().await;

    let initial_draw = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| app.draw()));
    if let Err(payload) = initial_draw {
        let message = format!("Initial draw fault: {}", panic_message(payload));
        loop {
            draw_fault_screen(&message);
            if is_key_pressed(KeyCode::R) {
                app = EditorApp::new_without_textures();
                app.status_message = "Recovered in safe mode after initial draw fault".to_string();
                break;
            }
            next_frame().await;
        }
    }
    next_frame().await;
    crate::append_editor_log(&format!(
        "STARTUP COMPLETE editor interactive in {:.1} ms",
        startup_started.elapsed().as_secs_f64() * 1000.0
    ));

    let mut frame_fault: Option<String> = None;
    let mut last_slow_update_log_at = -10.0_f64;
    let mut last_slow_reload_log_at = -10.0_f64;
    let mut last_slow_draw_log_at = -10.0_f64;
    loop {
        if let Some(message) = frame_fault.as_deref() {
            draw_fault_screen(message);
            if is_key_pressed(KeyCode::R) {
                app = EditorApp::new_without_textures();
                app.status_message =
                    "Recovered in safe mode after a contained frame fault".to_string();
                frame_fault = None;
            }
            next_frame().await;
            continue;
        }

        let update_started = Instant::now();
        let update_result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            app.update();
            app.poll_asset_hot_reload();
        }));
        let update_elapsed = update_started.elapsed();
        if update_elapsed.as_millis() >= 250 && get_time() - last_slow_update_log_at >= 5.0 {
            last_slow_update_log_at = get_time();
            crate::append_editor_log(&format!(
                "slow editor update: {} ms in {:?}",
                update_elapsed.as_millis(),
                app.viewport_mode
            ));
        }
        if let Err(payload) = update_result {
            frame_fault = Some(format!("Update fault: {}", panic_message(payload)));
            continue;
        }

        let reload_started = Instant::now();
        app.reload_asset_outputs_if_requested().await;
        app.load_visible_asset_browser_thumbnails();
        let reload_elapsed = reload_started.elapsed();
        if reload_elapsed.as_millis() >= 250 && get_time() - last_slow_reload_log_at >= 5.0 {
            last_slow_reload_log_at = get_time();
            crate::append_editor_log(&format!(
                "slow editor asset reload: {} ms",
                reload_elapsed.as_millis()
            ));
        }

        let draw_started = Instant::now();
        let draw_result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| app.draw()));
        let draw_elapsed = draw_started.elapsed();
        if draw_elapsed.as_millis() >= 250 && get_time() - last_slow_draw_log_at >= 5.0 {
            last_slow_draw_log_at = get_time();
            crate::append_editor_log(&format!(
                "slow editor draw: {} ms in {:?}",
                draw_elapsed.as_millis(),
                app.viewport_mode
            ));
        }
        if let Err(payload) = draw_result {
            frame_fault = Some(format!("Draw fault: {}", panic_message(payload)));
            continue;
        }
        next_frame().await;
    }
}
