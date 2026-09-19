use std::collections::{BTreeMap, BTreeSet};
use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use macroquad::prelude::*;
use rfd::FileDialog;
use serde::{Deserialize, Serialize};

mod review;
mod scene_audit;

const TILE_SIZE: i32 = 32;
const TOP_BAR_H: f32 = 98.0;
const STATUS_H: f32 = 32.0;
const SOURCE_SHEET_STACK_MIN_H: f32 = 176.0;
const SHEET_LIST_TOP: f32 = 103.0;
const SOURCE_PREVIEW_TOP_PAD: f32 = 12.0;
const SHEET_CARD_H: f32 = 34.0;
const MAX_LIBRARY_SHEETS: usize = 100_000; // Full ElizaWy index; textures remain lazy.
const MAX_UNDO_STEPS: usize = 64;
const GAP: f32 = 12.0;
const INSPECTOR_W: f32 = 292.0;
const MIN_SOURCE_ZOOM: f32 = 0.50;
const MAX_SOURCE_ZOOM: f32 = 6.00;
const MIN_CANVAS_ZOOM: f32 = 1.00;
const MAX_CANVAS_ZOOM: f32 = 4.00;
const DEFAULT_CANVAS_ZOOM: f32 = 2.00;
const ZOOM_STEP: f32 = 1.07;
const PROJECT_SCHEMA: &str = "havenwild.atlas_mapper_project.v0_6"; // Compatible B48R14 persistence.
const LEGACY_PROJECT_SCHEMA_V5: &str = "havenwild.atlas_mapper_project.v0_5";
const LEGACY_PROJECT_SCHEMA: &str = "havenwild.atlas_mapper_project.v0_1";
const LEGACY_PROJECT_SCHEMA_V2: &str = "havenwild.atlas_mapper_project.v0_2";
const LEGACY_PROJECT_SCHEMA_V3: &str = "havenwild.atlas_mapper_project.v0_3";
const LEGACY_PROJECT_SCHEMA_V4: &str = "havenwild.atlas_mapper_project.v0_4";
const HANDOFF_SCHEMA: &str = "havenwild.atlas_assembly_handoff.v0_7";
const MAPPED_SHEET_SCHEMA: &str = "havenwild.atlas_mapper_mapped_sheet.v0_5";
const TERRAIN_ATLAS_CATALOG_REL: &str = "content/assets/terrain_atlas_catalog_v2.json";
const EXTERNAL_ASSET_ROOTS_REL: &str = "content/assets/intake/external_asset_roots_v0_1.json";
const LOCAL_EXTERNAL_ASSET_ROOTS_REL: &str = ".local/havenwild_external_asset_roots.json";
const MAPPED_TILE_STATUS_DRAFT: &str = "draft_mapped";
const MAPPED_TILE_STATUS_LEARNED: &str = "learned_mapping";
const MAPPED_TILE_STATUS_APPROVED: &str = "approved_mapping";
const MAX_REASSEMBLY_CELLS: usize = 24;
const MAPPER_BUILD: &str = "B48R23 source-library / erase repair";

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum AuthorTool {
    Select,
    Elevation,
    Water,
}

impl AuthorTool {
    fn label(self) -> &'static str {
        match self { Self::Select => "Select", Self::Elevation => "Height", Self::Water => "Water" }
    }
}

// The library browser groups entire original sheets; a grouping is not a claim
// that its individual 32px cells have gameplay roles or are approved.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum SourceGroup {
    Ground, Water, Cliffs, Plants, Buildings, Structures, Furniture,
    Characters, Items, Effects,
}

impl SourceGroup {
    // Character authoring has a separate lane; keep its schema compatibility.
    const ALL: [Self; 9] = [
        Self::Ground, Self::Water, Self::Cliffs, Self::Plants, Self::Buildings,
        Self::Structures, Self::Furniture, Self::Items, Self::Effects,
    ];

    fn label(self) -> &'static str {
        match self {
            Self::Ground => "Ground", Self::Water => "Water", Self::Cliffs => "Cliffs",
            Self::Plants => "Plants", Self::Buildings => "Buildings", Self::Structures => "Structures",
            Self::Furniture => "Furniture", Self::Characters => "Characters", Self::Items => "Items",
            Self::Effects => "FX / UI",
        }
    }

    fn from_path(path: &Path) -> Self {
        let name = path.file_name().and_then(|n| n.to_str()).unwrap_or("").to_ascii_lowercase();
        let key = normalize_path_key(path);
        // Prefer a sheet's actual subject to generic ancestor names such as
        // Characters or Terrain. Furniture variants are composite objects, not
        // automatically terrain cells or character animation frames.
        if ["chair", "table", "stool", "bed", "sofa", "cabinet", "shelf", "dresser", "desk", "bench", "wardrobe"]
            .iter().any(|word| name.contains(word)) { Self::Furniture }
        else if name.contains("water") || name.contains("pond") || name.contains("river") || name.contains("ocean") || name.contains("shore") { Self::Water }
        else if name.contains("cliff") || name.contains("mountain") || name.contains("ladder")
            || name.contains("vine") || name.contains("handhold") { Self::Cliffs }
        else if name.contains("tree") || name.contains("flower") || name.contains("bush")
            || name.contains("plant") || name.contains("foliage") || name.contains("crop") { Self::Plants }
        else if name.contains("house") || name.contains("building") || name.contains("roof")
            || name.contains("tavern") { Self::Buildings }
        else if name.contains("fence") || name.contains("bridge") || name.contains("wall")
            || name.contains("door") || name.contains("window") || name.contains("floor") { Self::Structures }
        else if name.contains("character") || name.contains("body") || name.contains("hair")
            || name.contains("backslash") || key.contains("/characters/") { Self::Characters }
        else if name.contains("tool") || name.contains("weapon") || name.contains("item")
            || name.contains("equipment") || name.contains("armor") { Self::Items }
        else if name.contains("fx") || name.contains("effect") || name.contains("particle")
            || name.contains("icon") || key.contains("/ui/") { Self::Effects }
        else if key.contains("/terrain/") || name.contains("grass") || name.contains("sand") { Self::Ground }
        else { match AssetCategory::from_file_hint(path) {
            AssetCategory::Cliff => Self::Cliffs,
            AssetCategory::Terrain => Self::Ground,
            AssetCategory::House => Self::Buildings,
            AssetCategory::Structure => Self::Structures,
            AssetCategory::Character => Self::Characters,
            AssetCategory::Equipment => Self::Items,
            AssetCategory::Fx | AssetCategory::Ui => Self::Effects,
            AssetCategory::Object => Self::Furniture,
        }}
    }
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
enum AssetCategory {
    Terrain,
    Cliff,
    Structure,
    House,
    Object,
    Character,
    Equipment,
    Fx,
    Ui,
}

impl AssetCategory {
    const ALL: [AssetCategory; 9] = [
        AssetCategory::Terrain,
        AssetCategory::Cliff,
        AssetCategory::Structure,
        AssetCategory::House,
        AssetCategory::Object,
        AssetCategory::Character,
        AssetCategory::Equipment,
        AssetCategory::Fx,
        AssetCategory::Ui,
    ];

    fn label(self) -> &'static str {
        match self {
            AssetCategory::Terrain => "Terrain",
            AssetCategory::Cliff => "Cliff",
            AssetCategory::Structure => "Structure",
            AssetCategory::House => "House",
            AssetCategory::Object => "Object",
            AssetCategory::Character => "Character",
            AssetCategory::Equipment => "Equipment",
            AssetCategory::Fx => "FX",
            AssetCategory::Ui => "UI",
        }
    }

    fn stable_key(self) -> &'static str {
        match self {
            AssetCategory::Terrain => "terrain",
            AssetCategory::Cliff => "structural_cliff",
            AssetCategory::Structure => "structure",
            AssetCategory::House => "building_or_house",
            AssetCategory::Object => "object",
            AssetCategory::Character => "character",
            AssetCategory::Equipment => "equipment",
            AssetCategory::Fx => "fx",
            AssetCategory::Ui => "ui",
        }
    }

    fn from_stable_key(value: &str) -> Option<Self> {
        match value {
            "terrain" => Some(AssetCategory::Terrain),
            "structural_cliff" | "cliff" => Some(AssetCategory::Cliff),
            "structure" => Some(AssetCategory::Structure),
            "building_or_house" | "house" | "building" => Some(AssetCategory::House),
            "object" | "objects" => Some(AssetCategory::Object),
            "character" | "characters" => Some(AssetCategory::Character),
            "equipment" | "tool" | "weapon" => Some(AssetCategory::Equipment),
            "fx" | "effect" => Some(AssetCategory::Fx),
            "ui" | "icon" => Some(AssetCategory::Ui),
            _ => None,
        }
    }

    fn from_file_hint(path: &Path) -> Self {
        let hint = path.to_string_lossy().to_lowercase();
        let file = path.file_name().and_then(|name| name.to_str()).unwrap_or("").to_ascii_lowercase();
        if ["chair", "table", "stool", "bed", "sofa", "cabinet", "shelf", "dresser", "desk", "bench", "wardrobe"]
            .iter().any(|word| file.contains(word)) { AssetCategory::Object }
        else if file.contains("waterfall") || file.contains("water") { AssetCategory::Terrain }
        else if hint.contains("cliff") || hint.contains("ramp") || hint.contains("ledge") || hint.contains("elevation") {
            AssetCategory::Cliff
        } else if hint.contains("house") || hint.contains("building") || hint.contains("roof") || hint.contains("wall") {
            AssetCategory::House
        } else if hint.contains("structure") || hint.contains("floor") || hint.contains("door") || hint.contains("fence") {
            AssetCategory::Structure
        } else if hint.contains("character") || hint.contains("body") || hint.contains("hair") || hint.contains("clothes") || hint.contains("armor") {
            AssetCategory::Character
        } else if hint.contains("tool") || hint.contains("weapon") || hint.contains("equipment") || hint.contains("item") {
            AssetCategory::Equipment
        } else if hint.contains("fx") || hint.contains("effect") || hint.contains("waterfall") || hint.contains("torch") {
            AssetCategory::Fx
        } else if hint.contains("ui") || hint.contains("icon") || hint.contains("hud") {
            AssetCategory::Ui
        } else if hint.contains("terrain") || hint.contains("grass") || hint.contains("water") || hint.contains("shore") || hint.contains("farm") || hint.contains("tree") {
            AssetCategory::Terrain
        } else {
            AssetCategory::Object
        }
    }

    fn default_layout(self) -> (i32, i32, &'static str) {
        match self {
            AssetCategory::Terrain => (5, 4, "terrain tile sampler"),
            AssetCategory::Cliff => (6, 3, "cliff face/cap sampler"),
            AssetCategory::Structure => (6, 4, "structure module sampler"),
            AssetCategory::House => (6, 5, "building puzzle sampler"),
            AssetCategory::Object => (5, 4, "prop/object sampler"),
            AssetCategory::Character => (4, 4, "character layer sampler"),
            AssetCategory::Equipment => (6, 3, "equipment/icon sampler"),
            AssetCategory::Fx => (6, 3, "animation/fx sampler"),
            AssetCategory::Ui => (8, 2, "ui/icon sampler"),
        }
    }

    fn color(self) -> Color {
        match self {
            AssetCategory::Terrain => Color::new(0.18, 0.48, 0.31, 1.0),
            AssetCategory::Cliff => Color::new(0.53, 0.39, 0.25, 1.0),
            AssetCategory::Structure => Color::new(0.38, 0.45, 0.55, 1.0),
            AssetCategory::House => Color::new(0.50, 0.35, 0.20, 1.0),
            AssetCategory::Object => Color::new(0.40, 0.34, 0.55, 1.0),
            AssetCategory::Character => Color::new(0.40, 0.30, 0.52, 1.0),
            AssetCategory::Equipment => Color::new(0.42, 0.43, 0.47, 1.0),
            AssetCategory::Fx => Color::new(0.20, 0.44, 0.62, 1.0),
            AssetCategory::Ui => Color::new(0.23, 0.35, 0.58, 1.0),
        }
    }
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
struct SourceTile {
    tile_x: i32,
    tile_y: i32,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum SourceSheetStatus {
    Unmapped,
    Draft,
    Mapped,
    Validated,
    Published,
    NeedsReview,
}

impl SourceSheetStatus {
    fn label(self) -> &'static str {
        match self {
            SourceSheetStatus::Unmapped => "□",
            SourceSheetStatus::Draft => "◐",
            SourceSheetStatus::Mapped => "✓",
            SourceSheetStatus::Validated => "✓+",
            SourceSheetStatus::Published => "★",
            SourceSheetStatus::NeedsReview => "⚠",
        }
    }

    fn description(self) -> &'static str {
        match self {
            SourceSheetStatus::Unmapped => "unmapped",
            SourceSheetStatus::Draft => "draft",
            SourceSheetStatus::Mapped => "mapped",
            SourceSheetStatus::Validated => "validated",
            SourceSheetStatus::Published => "published",
            SourceSheetStatus::NeedsReview => "review",
        }
    }

    fn is_good(self) -> bool {
        matches!(self, SourceSheetStatus::Mapped | SourceSheetStatus::Validated | SourceSheetStatus::Published)
    }
}

#[derive(Clone, Debug)]
struct SourceSheetCard {
    path: PathBuf,
    display_name: String,
    family: String,
    category: AssetCategory,
    status: SourceSheetStatus,
    mapped_tile_count: usize,
    coverage_percent: f32,
    source_address_count: usize, // Pixel matches only; never semantic/visual certification.
}

#[derive(Clone, Copy, Debug)]
struct SheetMappingSummary {
    status: SourceSheetStatus,
    mapped_tile_count: usize,
    coverage_percent: f32,
}

impl SheetMappingSummary {
    const fn unmapped() -> Self {
        Self {
            status: SourceSheetStatus::Unmapped,
            mapped_tile_count: 0,
            coverage_percent: 0.0,
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum CellRole {
    Empty,
    Grass,
    Water,
    Cliff,
    Sand,
    Wood,
    Stone,
    Detail,
}

impl CellRole {
    fn label(self) -> &'static str {
        match self {
            CellRole::Empty => "empty",
            CellRole::Grass => "grass/top surface",
            CellRole::Water => "water",
            CellRole::Cliff => "cliff/earth face",
            CellRole::Sand => "sand/path",
            CellRole::Wood => "wood/structure",
            CellRole::Stone => "stone/neutral",
            CellRole::Detail => "detail/decor",
        }
    }
}

#[derive(Clone, Copy, Debug)]
struct SourceCellProfile {
    tile_x: i32,
    tile_y: i32,
    coverage: f32,
    avg_rgb: [f32; 3],
    role: CellRole,
}

#[derive(Clone, Copy, Debug)]
struct SourceSceneWindow {
    x: i32,
    y: i32,
    w: i32,
    h: i32,
    score: f32,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct AssemblyPiece {
    id: u32,
    source_tile_x: i32,
    source_tile_y: i32,
    source_rect: [i32; 4],
    canvas_grid_x: i32,
    canvas_grid_y: i32,
    rotation_degrees: i32,
    flip_x: bool,
    flip_y: bool,
    layer: i32,
    semantic_role: String,
    #[serde(default)]
    source_asset_id: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct SourceAssetDocument {
    id: String,
    path: String,
    file_name: String,
    // Source bytes are verified by the mapper-owned review exporter before evidence is produced.
    #[serde(default)]
    source_sha256: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct TerrainHeightCell {
    x: i32,
    y: i32,
    elevation: u8,
    #[serde(default)]
    water_surface: Option<u8>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct MapperProjectDocument {
    schema: String,
    tool: String,
    source_atlas_path: String,
    source_atlas_file_name: String,
    source_is_modified: bool,
    tile_size: i32,
    category: String,
    category_label: String,
    assembly_name: String,
    next_piece_id: u32,
    source_pan: [f32; 2],
    source_zoom: f32,
    canvas_pan: [f32; 2],
    canvas_zoom: f32,
    pieces: Vec<AssemblyPiece>,
    #[serde(default)]
    source_assets: Vec<SourceAssetDocument>,
    #[serde(default)]
    active_source_asset_id: String,
    #[serde(default)]
    heightmap: Vec<TerrainHeightCell>,
    authoring_notes: Vec<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct IterationSourceCoverage {
    source_asset_id: String,
    source_file: String,
    nonempty_source_cells: usize,
    represented_in_scene: usize,
    learned_candidate_cells: usize,
    approved_mapping_cells: usize,
    missing_cells: Vec<[i32; 2]>,
    unresolved_scene_cells: usize,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct HandoffDocument {
    schema: String,
    tool: String,
    project_schema: String,
    project_file: Option<String>,
    source_atlas_path: String,
    source_atlas_file_name: String,
    source_is_modified: bool,
    tile_size: i32,
    category: String,
    category_label: String,
    assembly_name: String,
    exported_unix_seconds: u64,
    pieces: Vec<AssemblyPiece>,
    source_assets: Vec<SourceAssetDocument>,
    heightmap: Vec<TerrainHeightCell>,
    certification_stage: String,
    #[serde(default)]
    iteration_coverage: Vec<IterationSourceCoverage>,
    #[serde(default)]
    generation_passes: u32,
    engine_notes: Vec<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct MappedSheetTileRecord {
    source_tile_x: i32,
    source_tile_y: i32,
    source_rect: [i32; 4],
    semantic_role: String,
    terrain_family: String,
    topology_role: String,
    layer: i32,
    layer_role: String,
    collision_profile: String,
    compatibility_class: String,
    status: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct MappedSheetRecord {
    schema: String,
    tool: String,
    source_atlas_path: String,
    source_atlas_file_name: String,
    tile_size: i32,
    category: String,
    category_label: String,
    assembly_name: String,
    source_sheet_profile: String,
    provider: String,
    season: String,
    terrain_lane_authority: String,
    piece_count: usize,
    mapped_tile_count: usize,
    mapped_tiles: Vec<MappedSheetTileRecord>,
    coverage_percent: f32,
    lifecycle_stage: String,
    correction_scene_count: u32,
    learned_from_scene: bool,
    terrain_lane_role_binding: String,
    project_file: Option<String>,
    handoff_file: Option<String>,
    updated_unix_seconds: u64,
    compatibility_notes: Vec<String>,
    asset_intake_notes: Vec<String>,
}

struct LoadedAtlas {
    id: String,
    path: PathBuf,
    texture: Texture2D,
    width: i32,
    height: i32,
    cell_profiles: Vec<SourceCellProfile>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum DragState {
    None,
    SourceTile(SourceTile),
    ExistingPiece(usize),
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum MappingStage {
    SourceOnly,
    DraftMapped,
    ProjectSaved,
    HandoffExported,
}

impl MappingStage {
    fn label(self) -> &'static str {
        match self {
            MappingStage::SourceOnly => "SOURCE ONLY",
            MappingStage::DraftMapped => "MAPPED DRAFT",
            MappingStage::ProjectSaved => "PROJECT SAVED",
            MappingStage::HandoffExported => "HANDOFF EXPORTED",
        }
    }

    fn is_green(self) -> bool {
        !matches!(self, MappingStage::SourceOnly)
    }
}

#[derive(Clone)]
struct SceneSnapshot {
    pieces: Vec<AssemblyPiece>,
    heightmap: Vec<TerrainHeightCell>,
    next_piece_id: u32,
    selected_piece: Option<usize>,
}

struct MapperApp {
    atlas: Option<LoadedAtlas>,
    source_stack: Vec<LoadedAtlas>,
    heightmap: Vec<TerrainHeightCell>,
    undo_stack: Vec<SceneSnapshot>,
    redo_stack: Vec<SceneSnapshot>,
    author_tool: AuthorTool,
    paint_elevation: u8,
    dirty: bool,
    project_path: Option<PathBuf>,
    last_handoff_path: Option<PathBuf>,
    selected_tile: Option<SourceTile>,
    selected_piece: Option<usize>,
    drag: DragState,
    drag_origin: Option<(usize, i32, i32)>,
    pieces: Vec<AssemblyPiece>,
    next_piece_id: u32,
    category: AssetCategory,
    assembly_name: String,
    source_pan: Vec2,
    source_zoom: f32,
    canvas_pan: Vec2,
    canvas_zoom: f32,
    is_panning_source: bool,
    is_panning_canvas: bool,
    is_painting_height: bool,
    last_mouse: Vec2,
    status: String,
    mapping_stage: MappingStage,
    auto_seed: u64,
    scene_generation_count: u32,
    sheet_library: Vec<SourceSheetCard>,
    sheet_library_visible: Vec<usize>,
    sheet_library_search: String,
    sheet_library_group: Option<SourceGroup>,
    sheet_library_search_focused: bool,
    sheet_library_scroll: f32,
    library_notice: String,
    show_inspector: bool,
    pane_ratio: f32,
    resizing_divider: bool,
    atlas_focus: bool,
}

impl Default for MapperApp {
    fn default() -> Self {
        Self {
            atlas: None,
            source_stack: Vec::new(),
            heightmap: Vec::new(),
            undo_stack: Vec::new(),
            redo_stack: Vec::new(),
            author_tool: AuthorTool::Select,
            paint_elevation: 1,
            dirty: false,
            project_path: None,
            last_handoff_path: None,
            selected_tile: None,
            selected_piece: None,
            drag: DragState::None,
            drag_origin: None,
            pieces: Vec::new(),
            next_piece_id: 1,
            category: AssetCategory::Terrain,
            assembly_name: "new_atlas_assembly".to_string(),
            source_pan: vec2(18.0, 72.0),
            source_zoom: 1.0,
            canvas_pan: vec2(56.0, 116.0),
            canvas_zoom: DEFAULT_CANVAS_ZOOM,
            is_panning_source: false,
            is_panning_canvas: false,
            is_painting_height: false,
            last_mouse: Vec2::ZERO,
            status: "Summer authoring: no certified editable demo scene is bundled. Load an existing project or select original sheets; drafts are not approved.".to_string(),
            mapping_stage: MappingStage::SourceOnly,
            auto_seed: 1,
            scene_generation_count: 0,
            sheet_library: Vec::new(),
            sheet_library_visible: Vec::new(),
            sheet_library_search: String::new(),
            sheet_library_group: Some(SourceGroup::Ground),
            sheet_library_search_focused: false,
            sheet_library_scroll: 0.0,
            library_notice: "Asset lane index not scanned yet.".to_string(),
            show_inspector: false,
            pane_ratio: 0.5,
            resizing_divider: false,
            atlas_focus: true,
        }
    }
}

// Only the original ElizaWy family is active for this pass; nonseasonal sheets
// (e.g. objects/fences and shared animated waterfall) belong in Summer.
// The V7 provider and the other seasons are preserved on disk, not indexed here.
fn is_summer_elizawy_source(path: &Path) -> bool {
    let normalized = normalize_path_key(path);
    if !(normalized.contains("lpc_revised") || normalized.contains("elizawy")) { return false; }
    if normalized.contains("/characters/") || normalized.contains("/character/") { return false; }
    let file = path.file_name().and_then(|name| name.to_str()).unwrap_or("").to_ascii_lowercase();
    // Multi-season split originals ("Spring & Summer", "Non-Winter") are
    // legitimate Summer sources. The substring "fall" is part of WATERFALL:
    // only an isolated Fall season token may exclude an otherwise-neutral file.
    if file.contains("summer") || file.contains("non-winter") { return true; }
    !["spring", "autumn", "winter", "frozen"].iter().any(|season| file.contains(season))
        && !file.split(|ch: char| !ch.is_ascii_alphanumeric()).any(|token| token == "fall")
}

fn summer_known_source_addresses(root: &Path) -> BTreeMap<String, usize> {
    let mut addresses: BTreeMap<String, BTreeSet<(i32, i32)>> = BTreeMap::new();
    let original_root = root.join("assets/source/licensed/lpc_revised");
    let path = root.join("content/assets/lpc/elizawy_summer_atlas_source_crosswalk_b48r7_v0_1.json");
    if let Ok(text) = fs::read_to_string(path) {
        if let Ok(value) = serde_json::from_str::<serde_json::Value>(&text) {
            if let Some(entries) = value.get("entries").and_then(|x| x.as_array()) {
                for entry in entries {
                    let Some(reference) = entry.get("referencePath").and_then(|x| x.as_str()) else { continue; };
                    let Some(cell) = entry.get("referenceCell").and_then(|x| x.as_array()) else { continue; };
                    if let (Some(x), Some(y)) = (cell.first().and_then(|v| v.as_i64()), cell.get(1).and_then(|v| v.as_i64())) {
                        let source_path = original_root.join(reference);
                        addresses.entry(normalize_path_key(&source_path)).or_default().insert((x as i32, y as i32));
                    }
                    if let (Some(target), Some(cells)) = (entry.get("mainAtlasPath").and_then(|v| v.as_str()), entry.get("exactMainAtlasCells").and_then(|v| v.as_array())) {
                        {
                            let coords = addresses.entry(normalize_path_key(&original_root.join(target))).or_default();
                            for cell in cells {
                                if let Some(pair) = cell.as_array() {
                                    if let (Some(x), Some(y)) = (pair.first().and_then(|v| v.as_i64()), pair.get(1).and_then(|v| v.as_i64())) {
                                        coords.insert((x as i32, y as i32));
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    let recovered = root.join("content/assets/lpc/elizawy_mountain_waterfall_transition_source_b48r8_v0_1.json");
    if let Ok(text) = fs::read_to_string(recovered) {
        if let Ok(value) = serde_json::from_str::<serde_json::Value>(&text) {
            if let Some(cells) = value.get("cells").and_then(|v| v.as_array()) {
                let set = addresses.entry(normalize_path_key(&original_root.join("Terrain/Mountain, Waterfall Transitions (Summer).png"))).or_default();
                for cell in cells {
                    if let Some(pair) = cell.get("grid").and_then(|v| v.as_array()) {
                        if let (Some(x),Some(y))=(pair.first().and_then(|v| v.as_i64()),pair.get(1).and_then(|v| v.as_i64())) {
                            set.insert((x as i32,y as i32));
                        }
                    }
                }
            }
        }
    }
    // B48R9 supplies more summer source addresses than the earlier B48R7
    // crosswalk. Import exact pixel-address evidence, never infer semantic roles.
    let seasonal = root.join("content/assets/lpc/elizawy_all_seasons_split_source_crosswalk_b48r9_v0_1.json");
    if let Ok(text) = fs::read_to_string(seasonal) {
        if let Ok(value) = serde_json::from_str::<serde_json::Value>(&text) {
            if let Some(entries) = value.get("entries").and_then(|x| x.as_array()) {
                for entry in entries {
                    let Some(targets) = entry.get("targets").and_then(|x| x.as_array()) else { continue; };
                    // A nonwinter source sheet may target three seasons. Only
                    // the summer target is eligible for this isolated lane.
                    let summer: Vec<_> = targets.iter()
                        .filter(|target| target.get("season").and_then(|v| v.as_str()) == Some("summer"))
                        .collect();
                    if summer.is_empty() { continue; }
                    if let (Some(reference), Some(pair)) = (
                        entry.get("referencePath").and_then(|v| v.as_str()),
                        entry.get("referenceCell").and_then(|v| v.as_array()),
                    ) {
                        if let (Some(x), Some(y)) = (
                            pair.first().and_then(|v| v.as_i64()),
                            pair.get(1).and_then(|v| v.as_i64()),
                        ) {
                            let reference_path = if reference.eq_ignore_ascii_case("Terrain/Waterfall.png") {
                                // Different original Waterfall.png variants have different bytes.
                                // B48R9 references the four-season split, not the combined atlas.
                                original_root.join("seasonal_split/Terrain/Waterfall.png")
                            } else { original_root.join(reference) };
                            addresses.entry(normalize_path_key(&reference_path)).or_default().insert((x as i32, y as i32));
                        }
                    }
                    for target in summer {
                        let Some(canonical) = target.get("canonicalAtlas").and_then(|v| v.as_str()) else { continue; };
                        let coords = addresses.entry(normalize_path_key(&original_root.join(canonical))).or_default();
                        if let Some(cells) = target.get("exactCanonicalCells").and_then(|v| v.as_array()) {
                            for pair in cells.iter().filter_map(|cell| cell.as_array()) {
                                if let (Some(x), Some(y)) = (
                                    pair.first().and_then(|v| v.as_i64()),
                                    pair.get(1).and_then(|v| v.as_i64()),
                                ) {
                                    coords.insert((x as i32, y as i32));
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    addresses.into_iter().map(|(name, cells)| (name, cells.len())).collect()
}

fn pinned_summer_source_hashes(root: &Path) -> BTreeMap<String, String> {
    let path = root.join("content/assets/lpc/elizawy_summer_source_registry_b48r15_v0_1.json");
    let Ok(text) = fs::read_to_string(path) else { return BTreeMap::new(); };
    let Ok(value) = serde_json::from_str::<serde_json::Value>(&text) else { return BTreeMap::new(); };
    let Some(sources) = value.get("sources").and_then(|v| v.as_array()) else { return BTreeMap::new(); };
    let mut hashes = BTreeMap::new();
    for source in sources {
        if let (Some(path), Some(sha)) = (
            source.get("path").and_then(|v| v.as_str()),
            source.get("sha256").and_then(|v| v.as_str()),
        ) {
            if sha.len() == 64 && sha.chars().all(|ch| ch.is_ascii_hexdigit()) {
                hashes.insert(normalize_path_key(Path::new(path)), sha.to_ascii_lowercase());
            }
        }
    }
    hashes
}

impl MapperApp {
    fn scene_snapshot(&self) -> SceneSnapshot {
        SceneSnapshot {
            pieces: self.pieces.clone(), heightmap: self.heightmap.clone(),
            next_piece_id: self.next_piece_id, selected_piece: self.selected_piece,
        }
    }

    fn checkpoint_scene(&mut self) {
        if self.undo_stack.len() == MAX_UNDO_STEPS { self.undo_stack.remove(0); }
        self.undo_stack.push(self.scene_snapshot());
        self.redo_stack.clear();
    }

    fn restore_snapshot(&mut self, snapshot: SceneSnapshot) {
        self.pieces = snapshot.pieces;
        self.heightmap = snapshot.heightmap;
        self.next_piece_id = snapshot.next_piece_id;
        self.selected_piece = snapshot.selected_piece.filter(|index| *index < self.pieces.len());
        self.dirty = true; // An undo is not evidence that the last saved file is identical.
        self.mapping_stage = if self.pieces.is_empty() { MappingStage::SourceOnly } else { MappingStage::DraftMapped };
        self.last_handoff_path = None;
    }

    fn undo_scene(&mut self) {
        if let Some(previous) = self.undo_stack.pop() {
            if self.redo_stack.len() == MAX_UNDO_STEPS { self.redo_stack.remove(0); }
            self.redo_stack.push(self.scene_snapshot());
            self.restore_snapshot(previous);
            self.status = format!("Undo scene edit ({} remaining)", self.undo_stack.len());
        } else { self.status = "Nothing to undo.".to_string(); }
    }

    fn redo_scene(&mut self) {
        if let Some(next) = self.redo_stack.pop() {
            if self.undo_stack.len() == MAX_UNDO_STEPS { self.undo_stack.remove(0); }
            self.undo_stack.push(self.scene_snapshot());
            self.restore_snapshot(next);
            self.status = format!("Redo scene edit ({} remaining)", self.redo_stack.len());
        } else { self.status = "Nothing to redo.".to_string(); }
    }

    fn asset_id(path: &Path) -> String {
        let root = env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
        let relative = path.strip_prefix(&root).unwrap_or(path);
        format!("source:{}", normalize_path_key(relative))
    }

    fn source_assets(&self) -> Vec<SourceAssetDocument> {
        let root = env::current_dir().unwrap_or_default();
        let pinned = pinned_summer_source_hashes(&root);
        self.source_stack.iter().chain(self.atlas.iter()).map(|atlas| {
            let path = atlas.path.strip_prefix(&root).unwrap_or(&atlas.path);
            SourceAssetDocument {
                id: atlas.id.clone(),
                path: path.to_string_lossy().replace('\\', "/"),
                file_name: atlas.path.file_name().and_then(|s| s.to_str()).unwrap_or("sheet").to_string(),
                // Registry hashes pin the user's supplied, original source bytes;
                // unknown external sheets remain observed-only, never falsely pinned.
                source_sha256: pinned.get(&normalize_path_key(path)).cloned(),
            }
        }).collect()
    }

    fn texture_for_piece(&self, piece: &AssemblyPiece) -> Option<&Texture2D> {
        if piece.source_asset_id.is_empty() {
            return self.atlas.as_ref().map(|atlas| &atlas.texture);
        }
        self.atlas.iter().chain(self.source_stack.iter())
            .find(|atlas| atlas.id == piece.source_asset_id)
            .map(|atlas| &atlas.texture)
    }

    fn rebuild_sheet_library_visibility(&mut self) {
        let query = self.sheet_library_search.trim().to_ascii_lowercase();
        self.sheet_library_visible = self.sheet_library.iter().enumerate()
            .filter(|(_, card)| self.sheet_library_group.map_or(true, |group| SourceGroup::from_path(&card.path) == group))
            .filter(|(_, card)| query.is_empty()
                || card.display_name.to_ascii_lowercase().contains(&query)
                || card.family.to_ascii_lowercase().contains(&query)
                || card.category.label().to_ascii_lowercase().contains(&query))
            .map(|(index, _)| index).collect();
        self.sheet_library_scroll = 0.0;
    }

    fn refresh_sheet_library(&mut self) {
        let Ok(root) = env::current_dir() else {
            self.library_notice = "Could not resolve repository root for asset lane scan.".to_string();
            return;
        };
        let mut seen = BTreeSet::new();
        let mut cards = Vec::new();
        let source_matches = summer_known_source_addresses(&root);
        self.collect_declared_sheet_cards(&root, &mut seen, &mut cards);

        let mut scan_roots = default_asset_sheet_scan_roots(&root);
        scan_roots.extend(declared_external_asset_roots(&root));
        for scan_root in scan_roots {
            self.collect_sheet_cards(&root, &scan_root, &mut seen, &mut cards);
            if cards.len() >= MAX_LIBRARY_SHEETS { break; }
        }
        // Match full original source paths, never basenames: the two different
        // Waterfall.png source versions must not inherit each other's evidence.
        for card in &mut cards { card.source_address_count = source_matches.get(&normalize_path_key(&card.path)).copied().unwrap_or(0); }
        cards.sort_by(|a, b| {
            a.category.label().cmp(b.category.label())
                .then_with(|| a.family.cmp(&b.family))
                .then_with(|| a.display_name.cmp(&b.display_name))
        });
        let count = cards.len();
        self.sheet_library = cards;
        self.rebuild_sheet_library_visibility();
        self.library_notice = if count == 0 {
            format!("NO ELIZAWY SHEETS FOUND. Root: {}. Required: assets/source/licensed/lpc_revised. Verify source installation or use Havenwild's PCC launcher.", root.display())
        } else if count >= MAX_LIBRARY_SHEETS {
            format!("Summer ElizaWy: first {count} indexed; cap reached. Textures load only when activated.")
        } else {
            format!("Summer ElizaWy: {count} available originals indexed. ON/OFF controls scene source activation.")
        };
        self.status = self.library_notice.clone();
    }

    fn collect_declared_sheet_cards(&self, root: &Path, seen: &mut BTreeSet<String>, cards: &mut Vec<SourceSheetCard>) {
        let catalog_path = root.join(TERRAIN_ATLAS_CATALOG_REL);
        let Ok(text) = fs::read_to_string(&catalog_path) else { return; };
        let Ok(value) = serde_json::from_str::<serde_json::Value>(&text) else { return; };
        let Some(atlases) = value.get("atlases").and_then(|items| items.as_array()) else { return; };
        for atlas in atlases {
            if cards.len() >= MAX_LIBRARY_SHEETS { return; }
            for key in ["sourcePath", "publishedPath"] {
                let Some(rel_path) = atlas.get(key).and_then(|path| path.as_str()) else { continue; };
                let path = root.join(rel_path);
                if !is_supported_image_path(&path) || !path.exists() || !is_summer_elizawy_source(&path) { continue; }
                let key = normalize_path_key(&path);
                if !seen.insert(key) { continue; }
                let display_name = path.file_name().and_then(|name| name.to_str()).unwrap_or("source_sheet").to_string();
                let category = AssetCategory::from_file_hint(&path);
                let mut family = atlas.get("id")
                    .and_then(|id| id.as_str())
                    .map(|id| id.replace('.', "_"))
                    .unwrap_or_else(|| infer_sheet_family(root, &path, category));
                if family.trim().is_empty() {
                    family = infer_sheet_family(root, &path, category);
                }
                let summary = self.mapping_summary_for_sheet_path(&path, category);
                cards.push(SourceSheetCard {
                    path: path.clone(),
                    display_name,
                    family,
                    category,
                    status: summary.status,
                    mapped_tile_count: summary.mapped_tile_count,
                    coverage_percent: summary.coverage_percent,
                    source_address_count: 0,
                });

                self.collect_seasonal_sibling_cards(root, &path, seen, cards);
            }
        }
    }

    fn collect_seasonal_sibling_cards(&self, root: &Path, path: &Path, seen: &mut BTreeSet<String>, cards: &mut Vec<SourceSheetCard>) {
        let Some(file_name) = path.file_name().and_then(|name| name.to_str()) else { return; };
        let Some(parent) = path.parent() else { return; };
        let lower = file_name.to_ascii_lowercase();
        if !(lower.starts_with("terrain_") && lower.ends_with(".png")) { return; }
        for season in ["summer"] {
            if cards.len() >= MAX_LIBRARY_SHEETS { return; }
            let sibling = parent.join(format!("terrain_{season}.png"));
            if !sibling.exists() || !is_summer_elizawy_source(&sibling) { continue; }
            let key = normalize_path_key(&sibling);
            if !seen.insert(key) { continue; }
            let display_name = sibling.file_name().and_then(|name| name.to_str()).unwrap_or("terrain_season.png").to_string();
            let category = AssetCategory::Terrain;
            let summary = self.mapping_summary_for_sheet_path(&sibling, category);
            cards.push(SourceSheetCard {
                path: sibling,
                display_name,
                family: format!("lpc_revised_seasonal_{season}"),
                category,
                status: summary.status,
                mapped_tile_count: summary.mapped_tile_count,
                coverage_percent: summary.coverage_percent,
                source_address_count: 0,
            });
        }
    }

    fn collect_sheet_cards(&self, root: &Path, scan_root: &Path, seen: &mut BTreeSet<String>, cards: &mut Vec<SourceSheetCard>) {
        if cards.len() >= MAX_LIBRARY_SHEETS || !scan_root.exists() { return; }
        let Ok(entries) = fs::read_dir(scan_root) else { return; };
        for entry in entries.flatten() {
            if cards.len() >= MAX_LIBRARY_SHEETS { return; }
            let path = entry.path();
            if path.is_dir() {
                self.collect_sheet_cards(root, &path, seen, cards);
                continue;
            }
            if !is_supported_image_path(&path) || !is_summer_elizawy_source(&path) { continue; }
            let key = normalize_path_key(&path);
            if !seen.insert(key) { continue; }
            let display_name = path.file_name().and_then(|name| name.to_str()).unwrap_or("source_sheet").to_string();
            let category = AssetCategory::from_file_hint(&path);
            let family = infer_sheet_family(root, &path, category);
            let summary = self.mapping_summary_for_sheet_path(&path, category);
            cards.push(SourceSheetCard {
                path,
                display_name,
                family,
                category,
                status: summary.status,
                mapped_tile_count: summary.mapped_tile_count,
                coverage_percent: summary.coverage_percent,
                source_address_count: 0,
            });
        }
    }

    fn mapping_record_path_for(root: &Path, path: &Path, category: AssetCategory) -> Option<PathBuf> {
        let stem = path.file_stem().and_then(|stem| stem.to_str()).map(sanitize_file_stem)?;
        // Include the normalized source path in the record identity. Do not overwrite
        // another archive's same-basename sheet. Legacy records remain read-only.
        let identity = Self::asset_id(path);
        let suffix = format!("{:016x}", stable_path_hash(identity.as_bytes()));
        Some(root
            .join("artifacts")
            .join("asset-intake")
            .join("atlas-mapper")
            .join("mapped-sheets")
            .join(format!("{}__{}__{}.mapped-sheet.json", stem, category.stable_key(), suffix)))
    }

    fn mapping_summary_for_sheet_path(&self, path: &Path, category: AssetCategory) -> SheetMappingSummary {
        let Ok(root) = env::current_dir() else { return SheetMappingSummary::unmapped(); };
        let Some(record) = Self::mapping_record_path_for(&root, path, category) else {
            return SheetMappingSummary { status: SourceSheetStatus::NeedsReview, mapped_tile_count: 0, coverage_percent: 0.0 };
        };
        let Ok(text) = fs::read_to_string(record) else { return SheetMappingSummary::unmapped(); };
        let Ok(value) = serde_json::from_str::<serde_json::Value>(&text) else {
            return SheetMappingSummary { status: SourceSheetStatus::NeedsReview, mapped_tile_count: 0, coverage_percent: 0.0 };
        };

        let mapped_tile_count = value.get("mapped_tile_count")
            .or_else(|| value.get("mappedTileCount"))
            .and_then(|count| count.as_u64())
            .or_else(|| value.get("mapped_tiles")
                .or_else(|| value.get("mappedTiles"))
                .and_then(|tiles| tiles.as_array())
                .map(|tiles| tiles.len() as u64))
            .unwrap_or(0) as usize;
        let coverage_percent = value.get("coverage_percent")
            .or_else(|| value.get("coveragePercent"))
            .and_then(|coverage| coverage.as_f64())
            .unwrap_or(0.0) as f32;
        let lifecycle = value.get("lifecycle_stage")
            .or_else(|| value.get("lifecycleStage"))
            .and_then(|stage| stage.as_str())
            .unwrap_or("")
            .to_ascii_lowercase();
        // A source address, guessed draft role, or learned candidate is NOT a complete map.
        // Full-sheet green requires documented coverage and explicit per-cell approval.
        let all_approved = value.get("mapped_tiles").and_then(|tiles| tiles.as_array())
            .is_some_and(|tiles| !tiles.is_empty() && tiles.iter().all(|tile|
                tile.get("status").and_then(|v| v.as_str()) == Some(MAPPED_TILE_STATUS_APPROVED)));
        let complete = mapped_tile_count > 0 && coverage_percent >= 99.999 && all_approved;
        let status = if complete && lifecycle.contains("published") {
            SourceSheetStatus::Published
        } else if complete && (lifecycle.contains("runtime_certified") || lifecycle.contains("topology_validated") || lifecycle.contains("visual_approved")) {
            SourceSheetStatus::Validated
        } else if mapped_tile_count > 0 {
            SourceSheetStatus::Draft
        } else {
            SourceSheetStatus::Unmapped
        };
        SheetMappingSummary { status, mapped_tile_count, coverage_percent }
    }

    fn persisted_mapped_tiles_for_current_sheet(&self) -> BTreeMap<(i32, i32), String> {
        let Some(atlas) = &self.atlas else { return BTreeMap::new(); };
        self.persisted_mapped_tiles_for_sheet(&atlas.path, self.category)
    }

    fn persisted_mapped_tiles_for_sheet(&self, source_path: &Path, category: AssetCategory) -> BTreeMap<(i32, i32), String> {
        let Ok(root) = env::current_dir() else { return BTreeMap::new(); };
        let Some(record) = Self::mapping_record_path_for(&root, source_path, category) else { return BTreeMap::new(); };
        let Ok(text) = fs::read_to_string(record) else { return BTreeMap::new(); };
        let Ok(value) = serde_json::from_str::<serde_json::Value>(&text) else { return BTreeMap::new(); };
        let Some(tiles) = value.get("mapped_tiles")
            .or_else(|| value.get("mappedTiles"))
            .and_then(|tiles| tiles.as_array()) else { return BTreeMap::new(); };
        let mut out = BTreeMap::new();
        for tile in tiles {
            let Some(x) = tile.get("source_tile_x").or_else(|| tile.get("sourceTileX")).and_then(|x| x.as_i64()) else { continue; };
            let Some(y) = tile.get("source_tile_y").or_else(|| tile.get("sourceTileY")).and_then(|y| y.as_i64()) else { continue; };
            let status = tile.get("status")
                .and_then(|status| status.as_str())
                .unwrap_or(MAPPED_TILE_STATUS_DRAFT)
                .to_string();
            out.insert((x as i32, y as i32), status);
        }
        out
    }

    fn open_sheet_from_library(&mut self, index: usize) {
        let Some(card) = self.sheet_library.get(index).cloned() else { return; };
        // Selecting an existing source card switches the source picker only;
        // all placements from earlier sheets remain in the scene and retain IDs.
        self.category = card.category;
        self.load_atlas(card.path);
    }

    fn source_is_activated(&self, id: &str) -> bool {
        self.atlas.as_ref().is_some_and(|source| source.id == id)
            || self.source_stack.iter().any(|source| source.id == id)
    }

    fn deactivate_sheet(&mut self, index: usize) {
        let Some(card) = self.sheet_library.get(index) else { return; };
        let id = Self::asset_id(&card.path);
        if self.pieces.iter().any(|piece| piece.source_asset_id == id) {
            self.status = "Sheet still used by scene placements. Remove its pieces before deactivating; no source references were broken.".to_string();
            return;
        }
        if self.atlas.as_ref().is_some_and(|source| source.id == id) {
            self.atlas = self.source_stack.pop();
            self.selected_tile = None;
            self.drag = DragState::None;
        } else {
            self.source_stack.retain(|source| source.id != id);
        }
        self.undo_stack.clear();
        self.redo_stack.clear(); // Cannot resurrect pieces from an unloaded source.
        self.dirty = true;
        self.status = "Sheet deactivated. Undo history cleared to prevent orphaned source references.".to_string();
    }

    fn source_sheet_card_at(&self, panel: Rect, mouse: Vec2) -> Option<usize> {
        let stack = source_sheet_stack_rect(panel, self.atlas_focus);
        if !stack.contains(mouse) || mouse.y < stack.y + SHEET_LIST_TOP || mouse.y > stack.y + stack.h - 4.0 { return None; }
        let local_y = mouse.y - (stack.y + SHEET_LIST_TOP) - self.sheet_library_scroll;
        if local_y < 0.0 { return None; }
        let index = (local_y / SHEET_CARD_H).floor() as usize;
        self.sheet_library_visible.get(index).copied()
    }

    fn load_atlas(&mut self, path: PathBuf) {
        if !is_summer_elizawy_source(&path) {
            self.status = "Summer ElizaWy lane: source must be in an ElizaWy/LPC_Revised source root, and cannot be a different season or V7.".to_string();
            return;
        }
        let id = Self::asset_id(&path);
        if self.atlas.as_ref().is_some_and(|atlas| atlas.id == id) { return; }
        if let Some(index) = self.source_stack.iter().position(|atlas| atlas.id == id) {
            self.category = AssetCategory::from_file_hint(&path);
            let next = self.source_stack.remove(index);
            if let Some(previous) = self.atlas.replace(next) { self.source_stack.push(previous); }
            self.status = format!("Switched active sheet; {} source sheets in this scene.", self.source_stack.len() + 1);
            return;
        }
        match fs::read(&path) {
            Ok(bytes) => {
                let texture = Texture2D::from_file_with_format(&bytes, None);
                texture.set_filter(FilterMode::Nearest);
                let width = texture.width().round() as i32;
                let height = texture.height().round() as i32;
                let file_name = path.file_name().and_then(|name| name.to_str()).unwrap_or("atlas").to_string();
                if self.pieces.is_empty() {
                    self.category = AssetCategory::from_file_hint(&path);
                    self.mapping_stage = MappingStage::SourceOnly;
                } else {
                    self.mapping_stage = MappingStage::DraftMapped;
                }
                if self.assembly_name == "new_atlas_assembly" || self.assembly_name.trim().is_empty() {
                    if let Some(stem) = path.file_stem().and_then(|stem| stem.to_str()) {
                        self.assembly_name = format!("{stem}_assembly");
                    }
                }
                self.auto_seed = unix_seconds()
                    ^ ((width as u64) << 17)
                    ^ ((height as u64) << 5)
                    ^ self.category.stable_key().bytes().map(u64::from).sum::<u64>();
                let cell_profiles = analyze_tile_sheet(&bytes, width, height);
                let mapped_cells = cell_profiles.iter().filter(|cell| cell.role != CellRole::Empty).count();
                if let Some(previous) = self.atlas.take() { self.source_stack.push(previous); self.dirty = true; }
                self.atlas = Some(LoadedAtlas { id, path: path.clone(), texture, width, height, cell_profiles });
                self.selected_tile = None;
                self.selected_piece = None;
                self.drag = DragState::None;
                self.drag_origin = None;
                self.refresh_mapping_stage_from_record();
                self.status = format!("Loaded {file_name} ({width}x{height}); inferred category {}; profiled {mapped_cells} non-empty 32px cells. Source remains read-only.", self.category.label());
            }
            Err(error) => self.status = format!("Atlas load failed: {error}"),
        }
    }

    fn load_atlas_dialog(&mut self) {
        if let Some(path) = FileDialog::new()
            .add_filter("PNG atlas", &["png"])
            .add_filter("Images", &["png", "bmp", "jpg", "jpeg", "webp"])
            .pick_file()
        {
            // Changing the source picker must not destroy the assembled multi-sheet scene.
            if is_summer_elizawy_source(&path) {
                self.category = AssetCategory::from_file_hint(&path);
            }
            self.load_atlas(path);
        }
    }

    fn save_project_dialog(&mut self) {
        if self.atlas.is_none() {
            self.status = "Load an atlas before saving a mapper project.".to_string();
            return;
        }
        let default_name = format!("{}.hw-atlas-map.json", sanitize_file_stem(&self.assembly_name));
        if let Some(path) = FileDialog::new()
            .add_filter("Havenwild atlas mapper project", &["json"])
            .set_file_name(&default_name)
            .save_file()
        {
            self.save_project(&path);
        }
    }

    // An explicitly saved scene becomes the next launch's editable Summer
    // master. It may still be UNREVIEWED; saving does not approve a recipe.
    fn save_startup_summer_demo(&mut self) {
        if self.atlas.is_none() || self.pieces.is_empty() {
            self.status = "Place source-exact Summer pieces before designating a startup demo. The rejected B48R10 PNG is not an editable scene.".into();
            return;
        }
        let Ok(root) = env::current_dir() else {
            self.status = "Cannot find repository root for Summer demo save.".into();
            return;
        };
        let path = root.join("artifacts/asset-intake/atlas-mapper/projects/elizawy_summer_master.mapper.json");
        if let Some(parent) = path.parent() {
            if let Err(error) = fs::create_dir_all(parent) {
                self.status = format!("Summer demo directory creation failed: {error}");
                return;
            }
        }
        self.save_project(&path);
        if !self.dirty {
            self.status = format!("Saved startup Summer scene (not approved): {}. Reopen mapper to resume it.", path.display());
        }
    }

    fn save_project_current_or_dialog(&mut self) {
        if let Some(path) = self.project_path.clone() {
            self.save_project(&path);
        } else {
            self.save_project_dialog();
        }
    }

    fn save_project(&mut self, path: &Path) {
        match self.current_project_document() {
            Some(document) => match serde_json::to_string_pretty(&document) {
                Ok(text) => match fs::write(path, text) {
                    Ok(()) => {
                        self.project_path = Some(path.to_path_buf());
                        self.dirty = false;
                        self.mapping_stage = MappingStage::ProjectSaved;
                        self.write_mapping_record(None);
                        self.status = format!("Saved mapper project: {}", path.to_string_lossy());
                    }
                    Err(error) => self.status = format!("Project save failed: {error}"),
                },
                Err(error) => self.status = format!("Project serialization failed: {error}"),
            },
            None => self.status = "Load an atlas before saving a mapper project.".to_string(),
        }
    }

    fn load_project_dialog(&mut self) {
        if self.dirty {
            self.status = "Unsaved edits: save this scene before opening another project.".to_string();
            return;
        }
        if let Some(path) = FileDialog::new()
            .add_filter("Havenwild atlas mapper project", &["json"])
            .pick_file()
        {
            self.load_project(&path);
        }
    }

    fn load_project(&mut self, path: &Path) {
        let text = match fs::read_to_string(path) {
            Ok(text) => text,
            Err(error) => {
                self.status = format!("Project load failed: {error}");
                return;
            }
        };
        let document: MapperProjectDocument = match serde_json::from_str(&text) {
            Ok(document) => document,
            Err(error) => {
                self.status = format!("Project parse failed: {error}");
                return;
            }
        };
        if document.schema != PROJECT_SCHEMA
            && document.schema != LEGACY_PROJECT_SCHEMA
            && document.schema != LEGACY_PROJECT_SCHEMA_V2
            && document.schema != LEGACY_PROJECT_SCHEMA_V3
            && document.schema != LEGACY_PROJECT_SCHEMA_V4
            && document.schema != LEGACY_PROJECT_SCHEMA_V5
        {
            self.status = format!("Project schema mismatch: expected {PROJECT_SCHEMA}, got {}", document.schema);
            return;
        }
        if document.tile_size != TILE_SIZE {
            self.status = format!("Unsupported tile size {}; this tool maps 32x32 atlas cells.", document.tile_size);
            return;
        }
        let Some(category) = AssetCategory::from_stable_key(&document.category) else {
            self.status = format!("Unknown asset category in mapper project: {}", document.category);
            return;
        };

        // Preflight all source references BEFORE touching the current editing session.
        // A missing sheet must not silently erase a working multi-source scene.
        let source_refs = if document.source_assets.is_empty() {
            vec![SourceAssetDocument {
                id: Self::asset_id(&PathBuf::from(&document.source_atlas_path)),
                path: document.source_atlas_path.clone(),
                file_name: document.source_atlas_file_name.clone(), source_sha256: None,
            }]
        } else { document.source_assets.clone() };
        let root = env::current_dir().unwrap_or_default();
        let missing: Vec<String> = source_refs.iter().filter_map(|source| {
            let raw = PathBuf::from(&source.path);
            let resolved = if raw.exists() { raw } else { root.join(&raw) };
            if resolved.is_file() { None } else { Some(source.path.clone()) }
        }).collect();
        if !missing.is_empty() {
            self.status = format!("Project load blocked; current scene preserved. Missing sources: {}", missing.join(", "));
            return;
        }
        if source_refs.iter().any(|source| {
            let raw = PathBuf::from(&source.path);
            let resolved = if raw.exists() { raw } else { root.join(raw) };
            !is_summer_elizawy_source(&resolved)
        }) {
            self.status = "Project load blocked; current scene preserved. Other seasons, V7 or non-ElizaWy sources must use a separate project.".into();
            return;
        }
        // Fail closed BEFORE clearing the current scene: source IDs, image decodes,
        // placements and duplicate height coordinates must all be coherent.
        let mut dimensions = BTreeMap::new();
        for source in &source_refs {
            if source.id.trim().is_empty() || dimensions.contains_key(&source.id) {
                self.status = "Project load blocked: duplicate/empty source identity. Current scene preserved.".into();
                return;
            }
            let raw = PathBuf::from(&source.path);
            let resolved = if raw.exists() { raw } else { root.join(raw) };
            let Ok(size) = image::image_dimensions(&resolved) else {
                self.status = format!("Project load blocked: source image cannot be decoded: {}", source.path);
                return;
            };
            dimensions.insert(source.id.clone(), size);
        }
        let legacy_id = Self::asset_id(&PathBuf::from(&document.source_atlas_path));
        let mut placement_ids = BTreeSet::new();
        for piece in &document.pieces {
            let source_id = if piece.source_asset_id.is_empty() { &legacy_id } else { &piece.source_asset_id };
            let Some(&(width, height)) = dimensions.get(source_id) else {
                self.status = format!("Project load blocked: piece {} refers to unlisted source. Current scene preserved.", piece.id);
                return;
            };
            let [sx, sy, sw, sh] = piece.source_rect;
            if !placement_ids.insert(piece.id) || sx < 0 || sy < 0 || sw != TILE_SIZE || sh != TILE_SIZE
                || i64::from(sx) + i64::from(sw) > i64::from(width)
                || i64::from(sy) + i64::from(sh) > i64::from(height)
                || piece.rotation_degrees.rem_euclid(90) != 0
            {
                self.status = format!("Project load blocked: invalid/duplicate piece {}. Current scene preserved.", piece.id);
                return;
            }
        }
        let mut height_positions = BTreeSet::new();
        if document.heightmap.iter().any(|cell| !height_positions.insert((cell.x, cell.y))) {
            self.status = "Project load blocked: duplicate heightmap cells. Current scene preserved.".into();
            return;
        }
        if document.heightmap.iter().any(|cell| cell.elevation > 30 || cell.water_surface.is_some_and(|water| water > 30)) {
            self.status = "Project load blocked: invalid elevation outside real 0..30. Current scene preserved.".into();
            return;
        }
        if self.dirty {
            self.status = "Project load blocked: unsaved current scene. Save before opening another project.".into();
            return;
        }
        self.project_path = Some(path.to_path_buf());
        self.last_handoff_path = None;
        self.source_stack.clear();
        self.atlas = None;
        self.heightmap = document.heightmap.clone();
        self.undo_stack.clear();
        self.redo_stack.clear();
        self.pieces = document.pieces;
        for piece in &mut self.pieces {
            if piece.source_asset_id.is_empty() { piece.source_asset_id = legacy_id.clone(); }
        }
        self.next_piece_id = document.next_piece_id.max(self.pieces.iter().map(|piece| piece.id.saturating_add(1)).max().unwrap_or(1));
        self.category = category;
        self.assembly_name = document.assembly_name;
        self.source_pan = vec2(document.source_pan[0], document.source_pan[1]);
        self.source_zoom = document.source_zoom.clamp(MIN_SOURCE_ZOOM, MAX_SOURCE_ZOOM);
        self.canvas_pan = vec2(document.canvas_pan[0], document.canvas_pan[1]);
        self.canvas_zoom = document.canvas_zoom.clamp(MIN_CANVAS_ZOOM, MAX_CANVAS_ZOOM);
        self.selected_tile = None;
        self.selected_piece = None;
        self.drag = DragState::None;
        self.drag_origin = None;
        self.mapping_stage = if self.pieces.is_empty() { MappingStage::SourceOnly } else { MappingStage::ProjectSaved };

        let sources = source_refs;
        let active_id = if document.active_source_asset_id.is_empty() {
            Self::asset_id(&PathBuf::from(&document.source_atlas_path))
        } else { document.active_source_asset_id };
        let mut missing = Vec::new();
        for source in sources {
            let raw = PathBuf::from(&source.path);
            let resolved = if raw.exists() { raw } else { env::current_dir().unwrap_or_default().join(&raw) };
            if !resolved.exists() { missing.push(source.path); continue; }
            self.load_atlas(resolved);
            // Preserve IDs present in a v0_6 project across folder moves.
            if let Some(atlas) = self.atlas.as_mut() { atlas.id = source.id.clone(); }
        }
        if let Some(index) = self.source_stack.iter().position(|atlas| atlas.id == active_id) {
            let selected = self.source_stack.remove(index);
            if let Some(previous) = self.atlas.replace(selected) { self.source_stack.push(previous); }
        }
        if let Some(atlas) = &self.atlas {
            self.sheet_library_group = Some(SourceGroup::from_path(&atlas.path));
            self.rebuild_sheet_library_visibility();
        }
        self.dirty = false;
        if missing.is_empty() {
            if !self.pieces.is_empty() { self.mapping_stage = MappingStage::ProjectSaved; }
            self.status = format!("Loaded mapper project with {} sheets: {}", self.source_stack.len() + usize::from(self.atlas.is_some()), path.to_string_lossy());
        } else {
            self.status = format!("Project opened with {} missing source(s): {}. Review/export blocked until restored.", missing.len(), missing.join(", "));
        }
    }

    fn export_scene_audit(&mut self) {
        if self.dirty {
            self.status = "Save the current project before emitting its scene audit.".into();
            return;
        }
        let Some(project) = self.project_path.as_ref() else {
            self.status = "Save a mapper project first; scene audit needs a traceable project path.".into();
            return;
        };
        let report = scene_audit::audit_scene(&self.pieces, &self.heightmap, &self.source_assets());
        let path = project.with_extension("scene-audit.json");
        match serde_json::to_vec_pretty(&report) {
            Ok(bytes) => match fs::write(&path, bytes) {
                Ok(()) => self.status = format!("UNREVIEWED audit: {} error(s), {} warning(s), {} elevation boundaries. {}",
                    report.errors, report.warnings, report.elevation_boundaries, path.display()),
                Err(error) => self.status = format!("Cannot write scene audit: {error}"),
            },
            Err(error) => self.status = format!("Cannot serialize scene audit: {error}"),
        }
    }

    fn export_review_dialog(&mut self) {
        if self.dirty {
            self.status = "Save the current source scene before generating a reproducible review.".to_string();
            return;
        }
        if self.pieces.is_empty() { self.status = "Place source tiles first.".to_string(); return; }
        let name = format!("{}_SOURCE_REVIEW.png", sanitize_file_stem(&self.assembly_name));
        if let Some(path) = FileDialog::new().add_filter("Source-exact PNG", &["png"])
            .set_file_name(&name).save_file() {
            let sources = self.source_assets();
            match review::write_review(&path, &sources, &self.pieces, &self.heightmap) {
                Ok(ledger) => self.status = format!("Unreviewed PNG and placement ledger exported: {}", ledger.to_string_lossy()),
                Err(error) => self.status = format!("Review export blocked: {error}"),
            }
        }
    }

    fn export_handoff_dialog(&mut self) {
        if self.dirty {
            self.status = "Save your scene before exporting a reproducible candidate handoff.".to_string();
            return;
        }
        if self.atlas.is_none() {
            self.status = "Load an atlas before exporting.".to_string();
            return;
        }
        if self.pieces.is_empty() {
            self.status = "Place or auto-map at least one piece before exporting.".to_string();
            return;
        }
        let default_name = format!("{}_handoff.json", sanitize_file_stem(&self.assembly_name));
        if let Some(path) = FileDialog::new()
            .add_filter("Havenwild atlas handoff", &["json"])
            .set_file_name(&default_name)
            .save_file()
        {
            self.export_handoff(&path);
        }
    }

    fn export_handoff(&mut self, path: &Path) {
        let Some(atlas) = &self.atlas else { return; };
        if self.pieces.iter().any(|piece| self.texture_for_piece(piece).is_none()) {
            self.status = "Candidate export blocked: scene refers to missing source artwork.".to_string();
            return;
        }
        let source_path = atlas.path.to_string_lossy().replace('\\', "/");
        let source_name = atlas.path.file_name().and_then(|name| name.to_str()).unwrap_or("atlas").to_string();
        let document = HandoffDocument {
            schema: HANDOFF_SCHEMA.to_string(),
            tool: "haven_atlas_mapper_lite".to_string(),
            project_schema: PROJECT_SCHEMA.to_string(),
            project_file: self.project_path.as_ref().map(|path| path.to_string_lossy().replace('\\', "/")),
            source_atlas_path: source_path,
            source_atlas_file_name: source_name,
            source_is_modified: false,
            tile_size: TILE_SIZE,
            category: self.category.stable_key().to_string(),
            category_label: self.category.label().to_string(),
            assembly_name: self.assembly_name.clone(),
            exported_unix_seconds: unix_seconds(),
            pieces: self.pieces.clone(),
            source_assets: self.source_assets(),
            heightmap: self.heightmap.clone(),
            certification_stage: "candidate_export_not_validated".to_string(),
            iteration_coverage: self.iteration_coverage(),
            generation_passes: self.scene_generation_count,
            engine_notes: vec![
                "The source atlas is immutable and was not modified.".to_string(),
                "Each piece maps one 32x32 source tile to an assembly grid cell.".to_string(),
                "Unreviewed iteration packet: iteration_coverage lists each activated sheet's missing/learned/approved source cells. Unresolved correction-tray pieces are not complete mappings.".to_string(),
                "Asset Authority may not publish without source hashes, visual approval, adjacency, collision, traversal, animation, runtime parity and PCC gate receipts.".to_string(),
            ],
        };
        match serde_json::to_string_pretty(&document) {
            Ok(text) => match fs::write(path, text) {
                Ok(()) => {
                    self.last_handoff_path = Some(path.to_path_buf());
                    self.mapping_stage = MappingStage::HandoffExported;
                    self.write_all_mapping_records(Some(path), MAPPED_TILE_STATUS_DRAFT, "CANDIDATE_HANDOFF_EXPORTED", false);
                    self.status = format!("Exported candidate only (NOT validated): {}", path.to_string_lossy());
                }
                Err(error) => self.status = format!("Export failed: {error}"),
            },
            Err(error) => self.status = format!("Handoff serialization failed: {error}"),
        }
    }

    fn current_project_document(&self) -> Option<MapperProjectDocument> {
        let atlas = self.atlas.as_ref()?;
        let source_path = atlas.path.to_string_lossy().replace('\\', "/");
        let source_name = atlas.path.file_name().and_then(|name| name.to_str()).unwrap_or("atlas").to_string();
        Some(MapperProjectDocument {
            schema: PROJECT_SCHEMA.to_string(),
            tool: "haven_atlas_mapper_lite".to_string(),
            source_atlas_path: source_path,
            source_atlas_file_name: source_name,
            source_is_modified: false,
            tile_size: TILE_SIZE,
            category: self.category.stable_key().to_string(),
            category_label: self.category.label().to_string(),
            assembly_name: self.assembly_name.clone(),
            next_piece_id: self.next_piece_id,
            source_pan: [self.source_pan.x, self.source_pan.y],
            source_zoom: self.source_zoom,
            canvas_pan: [self.canvas_pan.x, self.canvas_pan.y],
            canvas_zoom: self.canvas_zoom,
            pieces: self.pieces.clone(),
            source_assets: self.source_assets(),
            active_source_asset_id: atlas.id.clone(),
            heightmap: self.heightmap.clone(),
            authoring_notes: vec![
                "Mapper project files are editable tool state, not runtime assets.".to_string(),
                "Source atlas pixels remain immutable; this file stores placement and transform metadata only.".to_string(),
                "Mapped sheets are draft source evidence only; export does not certify artwork topology, collision, navigation or gameplay.".to_string(),
                format!("Scene generation passes recorded this session: {}", self.scene_generation_count),
            ],
        })
    }

    fn add_piece_from_tile(&mut self, tile: SourceTile, grid_x: i32, grid_y: i32) {
        self.checkpoint_scene();
        let id = self.next_piece_id;
        self.next_piece_id = self.next_piece_id.saturating_add(1);
        let piece = AssemblyPiece {
            id,
            source_tile_x: tile.tile_x,
            source_tile_y: tile.tile_y,
            source_rect: [tile.tile_x * TILE_SIZE, tile.tile_y * TILE_SIZE, TILE_SIZE, TILE_SIZE],
            canvas_grid_x: grid_x,
            canvas_grid_y: grid_y,
            rotation_degrees: 0,
            flip_x: false,
            flip_y: false,
            layer: self.next_default_layer(),
            semantic_role: self.category.stable_key().to_string(),
            source_asset_id: self.atlas.as_ref().map(|atlas| atlas.id.clone()).unwrap_or_default(),
        };
        self.pieces.push(piece);
        self.dirty = true;
        self.selected_piece = Some(self.pieces.len() - 1);
        self.mapping_stage = MappingStage::DraftMapped;
        self.status = format!("Placed tile {},{} as {} piece.", tile.tile_x, tile.tile_y, self.category.label());
    }

    fn auto_map_sheet(&mut self) {
        self.build_scene_draft(false);
    }

    fn generate_next_missing_draft(&mut self) {
        self.build_scene_draft(true);
    }

    fn iteration_coverage(&self) -> Vec<IterationSourceCoverage> {
        let mut result = Vec::new();
        for atlas in self.atlas.iter().chain(self.source_stack.iter()) {
            let category = AssetCategory::from_file_hint(&atlas.path);
            let saved = self.persisted_mapped_tiles_for_sheet(&atlas.path, category);
            let mut represented = BTreeSet::new();
            let mut unresolved = 0;
            for piece in self.pieces.iter().filter(|piece| piece.source_asset_id == atlas.id) {
                represented.insert((piece.source_tile_x, piece.source_tile_y));
                if piece.semantic_role.starts_with("unresolved.") { unresolved += 1; }
            }
            let nonempty: Vec<_> = atlas.cell_profiles.iter()
                .filter(|cell| cell.coverage > 0.0)
                .map(|cell| (cell.tile_x, cell.tile_y)).collect();
            let missing_cells = nonempty.iter().filter(|coord| !represented.contains(*coord))
                .map(|(x,y)| [*x,*y]).collect();
            result.push(IterationSourceCoverage {
                source_asset_id: atlas.id.clone(),
                source_file: atlas.path.to_string_lossy().to_string(),
                nonempty_source_cells: nonempty.len(),
                represented_in_scene: nonempty.iter().filter(|coord| represented.contains(*coord)).count(),
                learned_candidate_cells: nonempty.iter().filter(|coord|
                    saved.get(*coord).is_some_and(|status| status == MAPPED_TILE_STATUS_LEARNED)).count(),
                approved_mapping_cells: nonempty.iter().filter(|coord|
                    saved.get(*coord).is_some_and(|status| status == MAPPED_TILE_STATUS_APPROVED)).count(),
                missing_cells,
                unresolved_scene_cells: unresolved,
            });
        }
        result
    }

    // Reassemble from the corrected, saved scene as a *template*. Never erase
    // authored positions, elevation, water, earlier source choices or approvals.
    // There is no certified topology resolver yet: new source cells appear in a
    // clearly labelled correction tray, NOT silently painted into water/cliffs.
    fn reassemble_from_mapped_scene(&mut self) {
        if self.dirty || self.project_path.is_none() {
            self.status = "Save the corrected scene before Reassemble; no edits were replaced.".into();
            return;
        }
        if self.pieces.is_empty() {
            self.status = "Build or open an example scene first; Reassemble preserves its geometry.".into();
            return;
        }
        let coverage = self.iteration_coverage();
        let mut next = Vec::new();
        for entry in &coverage {
            for [x,y] in &entry.missing_cells {
                if next.len() == MAX_REASSEMBLY_CELLS { break; }
                next.push((entry.source_asset_id.clone(), *x, *y));
            }
            if next.len() == MAX_REASSEMBLY_CELLS { break; }
        }
        let unresolved: usize = coverage.iter().map(|entry| entry.unresolved_scene_cells).sum();
        if next.is_empty() {
            self.status = format!("No unrepresented source cells in activated sheets; {unresolved} correction-tray cell(s) still unresolved. Coverage does NOT certify tile roles, seams or game use.");
            return;
        }
        self.checkpoint_scene();
        let start_x = self.pieces.iter().map(|piece| piece.canvas_grid_x).max().unwrap_or(0).saturating_add(4);
        let start_y = self.pieces.iter().map(|piece| piece.canvas_grid_y).min().unwrap_or(0);
        let added = next.len();
        for (i,(source_asset_id,x,y)) in next.into_iter().enumerate() {
            let id = self.next_piece_id;
            self.next_piece_id = self.next_piece_id.saturating_add(1);
            self.pieces.push(AssemblyPiece {
                id, source_tile_x: x, source_tile_y: y,
                source_rect: [x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE],
                canvas_grid_x: start_x.saturating_add(i as i32 % 6),
                canvas_grid_y: start_y.saturating_add((i as i32 / 6) * 2),
                rotation_degrees: 0, flip_x: false, flip_y: false, layer: 0,
                semantic_role: "unresolved.source_cell.needs_authoring".into(),
                source_asset_id,
            });
        }
        self.scene_generation_count = self.scene_generation_count.saturating_add(1);
        self.selected_piece = None;
        self.dirty = true;
        self.mapping_stage = MappingStage::DraftMapped;
        self.status = format!("Reassembled saved scene without replacing edits. Added {added} missing source cells in a correction tray at right; assign roles and positions, save, audit, and export a candidate review.");
    }

    fn build_scene_draft(&mut self, prefer_unmapped: bool) {
        let Some(atlas) = &self.atlas else {
            self.status = "Load a tile sheet before building a correction draft.".to_string();
            return;
        };
        let cols = (atlas.width / TILE_SIZE).max(1);
        let rows = (atlas.height / TILE_SIZE).max(1);
        let file_hint = atlas.path.file_name().and_then(|name| name.to_str()).unwrap_or("sheet").to_string();
        let full_profiles = atlas.cell_profiles.clone();
        let mut profiles = full_profiles.clone();
        let mut skipped_known = 0usize;
        if prefer_unmapped {
            let persisted = self.persisted_mapped_tiles_for_current_sheet();
            if !persisted.is_empty() {
                for cell in &mut profiles {
                    if persisted.contains_key(&(cell.tile_x, cell.tile_y)) {
                        cell.role = CellRole::Empty;
                        cell.coverage = 0.0;
                        skipped_known += 1;
                    }
                }
            }
        }
        if self.dirty || self.source_stack.len() > 0 {
            self.status = "Scene draft generation would erase edited/multi-source work. Save and use a fresh single-sheet project; blocked.".to_string();
            return;
        }
        self.checkpoint_scene();
        self.pieces.clear();
        self.selected_piece = None;
        self.next_piece_id = 1;
        self.canvas_zoom = DEFAULT_CANVAS_ZOOM;
        self.canvas_pan = vec2(72.0, 116.0);
        self.scene_generation_count = self.scene_generation_count.saturating_add(1);

        let scene_label = match self.category {
            AssetCategory::Character | AssetCategory::Fx => self.generate_source_strip_draft(&profiles, cols, rows),
            AssetCategory::Object | AssetCategory::Equipment | AssetCategory::Ui => self.generate_component_gallery_draft(&profiles, cols, rows),
            _ => self.generate_source_window_scene_draft(&profiles, cols, rows),
        };

        if prefer_unmapped && self.pieces.is_empty() && skipped_known > 0 {
            let fallback_label = match self.category {
                AssetCategory::Character | AssetCategory::Fx => self.generate_source_strip_draft(&full_profiles, cols, rows),
                AssetCategory::Object | AssetCategory::Equipment | AssetCategory::Ui => self.generate_component_gallery_draft(&full_profiles, cols, rows),
                _ => self.generate_source_window_scene_draft(&full_profiles, cols, rows),
            };
            self.status = format!(
                "All obvious unmapped cells were exhausted for {file_hint}; rebuilt {fallback_label} from full sheet for review."
            );
        } else {
            let missing_note = if prefer_unmapped {
                format!(" skipped {skipped_known} already-mapped source cells")
            } else {
                String::new()
            };
            self.status = format!(
                "Built {scene_label} from {file_hint} as {} pass #{}{}. Correct roles/layers, Learn From Scene, then Generate Next Missing Draft.",
                self.category.label(),
                self.scene_generation_count,
                missing_note,
            );
        }
        self.selected_piece = None;
        self.dirty = true;
        self.mapping_stage = if self.pieces.is_empty() { MappingStage::SourceOnly } else { MappingStage::DraftMapped };
    }

    fn push_generated_piece(&mut self, tile: SourceTile, grid_x: i32, grid_y: i32, semantic_role: &str, layer: i32) {
        let id = self.next_piece_id;
        self.next_piece_id = self.next_piece_id.saturating_add(1);
        self.pieces.push(AssemblyPiece {
            id,
            source_tile_x: tile.tile_x,
            source_tile_y: tile.tile_y,
            source_rect: [tile.tile_x * TILE_SIZE, tile.tile_y * TILE_SIZE, TILE_SIZE, TILE_SIZE],
            canvas_grid_x: grid_x,
            canvas_grid_y: grid_y,
            rotation_degrees: 0,
            flip_x: false,
            flip_y: false,
            layer,
            semantic_role: semantic_role.to_string(),
            source_asset_id: self.atlas.as_ref().map(|atlas| atlas.id.clone()).unwrap_or_default(),
        });
    }

    fn push_profile_piece(&mut self, cell: SourceCellProfile, grid_x: i32, grid_y: i32, local_x: i32, local_y: i32) {
        if cell.role == CellRole::Empty || cell.coverage < 0.10 { return; }
        let semantic = self.semantic_for_cell(cell, local_x, local_y);
        let layer = self.layer_for_cell(cell, local_y);
        self.push_generated_piece(SourceTile { tile_x: cell.tile_x, tile_y: cell.tile_y }, grid_x, grid_y, &semantic, layer);
    }

    fn generate_source_window_scene_draft(&mut self, profiles: &[SourceCellProfile], cols: i32, rows: i32) -> &'static str {
        let (layout_w, layout_h, _) = self.category.default_layout();
        let window_w = layout_w.max(6).min(cols.max(1));
        let window_h = layout_h.max(4).min(rows.max(1));
        let window = best_scene_window(profiles, cols, rows, window_w, window_h, self.category)
            .unwrap_or(SourceSceneWindow { x: 0, y: 0, w: window_w, h: window_h, score: 0.0 });
        for sy in window.y..(window.y + window.h) {
            for sx in window.x..(window.x + window.w) {
                if let Some(cell) = profile_at(profiles, cols, sx, sy) {
                    let local_x = sx - window.x;
                    let local_y = sy - window.y;
                    self.push_profile_piece(cell, local_x, local_y, local_x, local_y);
                }
            }
        }
        if self.pieces.is_empty() {
            self.generate_component_gallery_draft(profiles, cols, rows)
        } else {
            "coherent source-window correction scene"
        }
    }

    fn generate_source_strip_draft(&mut self, profiles: &[SourceCellProfile], cols: i32, rows: i32) -> &'static str {
        let row_limit = 4.min(rows.max(1));
        let col_limit = 12.min(cols.max(1));
        let mut target_y = 0;
        for sy in 0..rows {
            if target_y >= row_limit { break; }
            let row_cells: Vec<SourceCellProfile> = (0..cols)
                .filter_map(|sx| profile_at(profiles, cols, sx, sy))
                .filter(|cell| cell.role != CellRole::Empty && cell.coverage >= 0.10)
                .take(col_limit as usize)
                .collect();
            if row_cells.is_empty() { continue; }
            for (target_x, cell) in row_cells.into_iter().enumerate() {
                self.push_profile_piece(cell, target_x as i32, target_y * 2, target_x as i32, target_y);
            }
            target_y += 1;
        }
        if self.pieces.is_empty() {
            self.generate_component_gallery_draft(profiles, cols, rows)
        } else {
            "source-row animation/layer strip draft"
        }
    }

    fn generate_component_gallery_draft(&mut self, profiles: &[SourceCellProfile], _cols: i32, _rows: i32) -> &'static str {
        let mut target_x = 0;
        let mut target_y = 0;
        for cell in profiles.iter().copied().filter(|cell| cell.role != CellRole::Empty && cell.coverage >= 0.10).take(32) {
            self.push_profile_piece(cell, target_x * 2, target_y * 2, target_x, target_y);
            target_x += 1;
            if target_x >= 8 {
                target_x = 0;
                target_y += 1;
            }
        }
        "source-linked review gallery draft"
    }

    fn semantic_for_cell(&self, cell: SourceCellProfile, local_x: i32, local_y: i32) -> String {
        match self.category {
            AssetCategory::Cliff => match cell.role {
                CellRole::Grass | CellRole::Sand => "terrain.cliff.top_or_lip".to_string(),
                CellRole::Water => "terrain.cliff.water_or_lower_pool".to_string(),
                CellRole::Cliff | CellRole::Wood | CellRole::Stone => "terrain.cliff.face_or_support".to_string(),
                CellRole::Detail => "terrain.cliff.detail_transition".to_string(),
                CellRole::Empty => "terrain.cliff.empty".to_string(),
            },
            AssetCategory::Terrain => {
                if let Some(atlas) = &self.atlas {
                    if let Some(role) = terrain_lane_profile_role(&atlas.path, cell.tile_x, cell.tile_y, cell.role, local_x, local_y) {
                        return role;
                    }
                }
                match cell.role {
                    CellRole::Water => "terrain.water_or_shore".to_string(),
                    CellRole::Grass => "terrain.ground_top_surface".to_string(),
                    CellRole::Sand => "terrain.path_or_bank".to_string(),
                    CellRole::Stone => "terrain.rock_or_hard_edge".to_string(),
                    _ => format!("terrain.scene_cell_{}_{}", local_x, local_y),
                }
            },
            AssetCategory::Structure | AssetCategory::House => match cell.role {
                CellRole::Wood => "structure.wood_wall_floor_or_trim".to_string(),
                CellRole::Stone => "structure.stone_floor_wall_or_foundation".to_string(),
                CellRole::Sand | CellRole::Grass => "structure.ground_or_transition".to_string(),
                CellRole::Cliff => "structure.earth_or_support".to_string(),
                _ => format!("structure.scene_cell_{}_{}", local_x, local_y),
            },
            AssetCategory::Character => format!("character.layer_or_frame_{}_{}", local_x, local_y),
            AssetCategory::Fx => format!("fx.animation_frame_{}_{}", local_x, local_y),
            AssetCategory::Object => format!("object.review_piece_{}_{}", local_x, local_y),
            AssetCategory::Equipment => format!("equipment.review_piece_{}_{}", local_x, local_y),
            AssetCategory::Ui => format!("ui.icon_piece_{}_{}", local_x, local_y),
        }
    }

    fn layer_for_cell(&self, cell: SourceCellProfile, local_y: i32) -> i32 {
        match self.category {
            AssetCategory::Cliff => match cell.role {
                CellRole::Grass | CellRole::Sand => 0,
                CellRole::Water => 2,
                CellRole::Cliff | CellRole::Wood | CellRole::Stone => 10 + local_y,
                CellRole::Detail => 20 + local_y,
                CellRole::Empty => local_y,
            },
            AssetCategory::Structure | AssetCategory::House => match cell.role {
                CellRole::Wood | CellRole::Stone | CellRole::Cliff => 10 + local_y,
                _ => local_y,
            },
            _ => local_y,
        }
    }

    fn next_default_layer(&self) -> i32 {
        self.pieces.iter().map(|piece| piece.layer).max().unwrap_or(-1) + 1
    }

    fn learn_from_scene(&mut self) {
        if self.dirty || self.project_path.is_none() {
            self.status = "Save your corrected scene before recording learned mappings.".into();
            return;
        }
        if self.pieces.iter().any(|piece| piece.semantic_role.starts_with("unresolved.")) {
            self.status = "Correction tray still has unresolved tiles: place and assign exact roles first. No learning recorded.".into();
            return;
        }
        if self.atlas.is_none() {
            self.status = "Load a sheet before learning from a corrected scene.".to_string();
            return;
        }
        if self.pieces.is_empty() {
            self.status = "Place or generate at least one mapped source tile before learning from scene.".to_string();
            return;
        }
        self.mapping_stage = MappingStage::ProjectSaved;
        self.write_all_mapping_records(None, MAPPED_TILE_STATUS_LEARNED, "LEARNED_MAPPING", true);
        self.status = "Saved source-linked scene learning for ALL activated sheets. Source roles remain draft; no cliff-water visual approval or runtime publication implied.".to_string();
    }

    fn assign_selected_semantic(&mut self, role: &str) {
        if self.selected_piece.and_then(|index| self.pieces.get(index)).is_some_and(|piece| piece.semantic_role != role) {
            self.checkpoint_scene();
        }
        if let Some(piece) = self.selected_piece_mut() {
            piece.semantic_role = role.to_string();
            self.dirty = true;
            self.mapping_stage = MappingStage::DraftMapped;
            self.status = format!("Assigned selected source tile to role: {role}");
        } else {
            self.status = "Select a canvas piece before assigning a semantic role.".to_string();
        }
    }

    fn category_role_presets(&self) -> Vec<&'static str> {
        match self.category {
            AssetCategory::Terrain => vec![
                "terrain.base_ground",
                "terrain.transition_edge",
                "terrain.overlay_patch",
                "terrain.water_topology",
                "terrain.shoreline_or_bank",
                "terrain.detail_scatter",
            ],
            AssetCategory::Cliff => vec![
                "terrain.cliff.crest",
                "terrain.cliff.face",
                "terrain.cliff.foot",
                "terrain.cliff.corner",
                "terrain.connector.climbable_vine_candidate",
                "terrain.connector.cliff_handhold_candidate",
                "terrain.connector.ladder_candidate",
                "terrain.cliff.walkable_termination_candidate",
            ],
            AssetCategory::Structure | AssetCategory::House => vec![
                "structure.floor",
                "structure.wall_back",
                "structure.wall_front",
                "structure.roof",
                "structure.door_socket",
                "structure.trim_or_detail",
            ],
            AssetCategory::Character => vec![
                "character.body_layer",
                "character.hair_layer",
                "character.clothing_layer",
                "character.equipment_layer",
                "character.animation_frame",
            ],
            AssetCategory::Fx => vec![
                "fx.animation_frame",
                "fx.looping_water",
                "fx.fire_or_light",
                "fx.impact_or_particle",
            ],
            AssetCategory::Object => vec![
                "object.prop",
                "object.interactable",
                "object.ground_overlay",
                "object.foreground_occluder",
            ],
            AssetCategory::Equipment => vec![
                "equipment.icon",
                "equipment.held_item",
                "equipment.tool_head",
                "equipment.weapon_or_armor",
            ],
            AssetCategory::Ui => vec![
                "ui.icon",
                "ui.frame",
                "ui.button_or_panel",
                "ui.status_element",
            ],
        }
    }

    fn selected_piece_mut(&mut self) -> Option<&mut AssemblyPiece> {
        self.selected_piece.and_then(|index| self.pieces.get_mut(index))
    }

    fn remove_selected_piece(&mut self) {
        let Some(index) = self.selected_piece.filter(|index| *index < self.pieces.len()) else {
            self.status = "Select a scene tile, then Delete or Erase selected. Right-click a tile to erase it directly.".into();
            return;
        };
        self.checkpoint_scene();
        let removed = self.pieces.remove(index);
        self.selected_piece = None;
        self.drag = DragState::None;
        self.drag_origin = None;
        self.dirty = true;
        self.last_handoff_path = None;
        self.mapping_stage = if self.pieces.is_empty() { MappingStage::SourceOnly } else { MappingStage::DraftMapped };
        self.status = format!("Erased tile id {} at ({},{}). Undo available. Height/water data preserved.", removed.id, removed.canvas_grid_x, removed.canvas_grid_y);
    }

    fn set_height_cell(&mut self, x: i32, y: i32, level: u8) {
        let level = level.min(30);
        if let Some(cell) = self.heightmap.iter_mut().find(|cell| cell.x == x && cell.y == y) {
            if cell.elevation != level { cell.elevation = level; self.dirty = true; }
        } else {
            self.heightmap.push(TerrainHeightCell { x, y, elevation: level, water_surface: None });
            self.dirty = true;
        }
        self.status = format!("Height paint ({x},{y}) = +{level}");
    }

    fn toggle_water_cell(&mut self, x: i32, y: i32) {
        if let Some(cell) = self.heightmap.iter_mut().find(|cell| cell.x == x && cell.y == y) {
            cell.water_surface = if cell.water_surface.is_some() { None } else { Some(cell.elevation) };
        } else {
            self.heightmap.push(TerrainHeightCell { x, y, elevation: self.paint_elevation, water_surface: Some(self.paint_elevation) });
        }
        self.dirty = true;
        self.status = format!("Water paint toggled at ({x},{y})");
    }

    fn terrain_cell(&self, x: i32, y: i32) -> Option<&TerrainHeightCell> {
        self.heightmap.iter().find(|cell| cell.x == x && cell.y == y)
    }

    fn edit_selected_height(&mut self, delta: i8) {
        let Some(piece) = self.selected_piece.and_then(|i| self.pieces.get(i)) else {
            self.status = "Select a scene tile before editing its elevation.".to_string();
            return;
        };
        let (x, y) = (piece.canvas_grid_x, piece.canvas_grid_y);
        self.checkpoint_scene();
        if let Some(cell) = self.heightmap.iter_mut().find(|cell| cell.x == x && cell.y == y) {
            cell.elevation = (i16::from(cell.elevation) + i16::from(delta)).clamp(0, 30) as u8;
            self.status = format!("Terrain at ({x},{y}) now has genuine elevation +{}", cell.elevation);
        } else {
            let level = i16::from(delta).clamp(0, 30) as u8;
            self.heightmap.push(TerrainHeightCell { x, y, elevation: level, water_surface: None });
            self.status = format!("Created real heightmap cell ({x},{y}) elevation +{level}");
        }
        self.dirty = true;
    }

    fn toggle_selected_water(&mut self) {
        let Some(piece) = self.selected_piece.and_then(|i| self.pieces.get(i)) else { return; };
        let (x, y) = (piece.canvas_grid_x, piece.canvas_grid_y);
        self.checkpoint_scene();
        if let Some(cell) = self.heightmap.iter_mut().find(|cell| cell.x == x && cell.y == y) {
            cell.water_surface = if cell.water_surface.is_some() { None } else { Some(cell.elevation) };
        } else {
            self.heightmap.push(TerrainHeightCell { x, y, elevation: 0, water_surface: Some(0) });
        }
        self.dirty = true;
        self.status = format!("Toggled explicit water at ({x},{y}); review hydrology before approval.");
    }

    fn handle_shortcuts(&mut self) {
        let ctrl = is_key_down(KeyCode::LeftControl) || is_key_down(KeyCode::RightControl);
        let shift = is_key_down(KeyCode::LeftShift) || is_key_down(KeyCode::RightShift);
        if ctrl && is_key_pressed(KeyCode::F) {
            self.sheet_library_search_focused = true;
            self.status = "Summer library search active. Type to filter; Enter or Esc finishes.".to_string();
            return;
        }
        if self.sheet_library_search_focused {
            if is_key_pressed(KeyCode::Escape) || is_key_pressed(KeyCode::Enter) {
                self.sheet_library_search_focused = false;
                return;
            }
            let mut changed = false;
            if is_key_pressed(KeyCode::Backspace) {
                self.sheet_library_search.pop();
                changed = true;
            }
            // Receive text only while focused, so ordinary editor hotkeys do
            // not simultaneously edit the scene or delete its selected piece.
            if !ctrl {
                while let Some(ch) = get_char_pressed() {
                    if !ch.is_control() && self.sheet_library_search.chars().count() < 72 {
                        self.sheet_library_search.push(ch);
                        changed = true;
                    }
                }
            }
            if changed { self.rebuild_sheet_library_visibility(); }
            return;
        }
        if !ctrl && is_key_pressed(KeyCode::I) {
            self.show_inspector = !self.show_inspector;
            self.status = if self.show_inspector { "Details open; scene editing is disabled beneath the overlay." } else { "Details closed; scene canvas is fully available." }.to_string();
            return;
        }
        if ctrl && is_key_pressed(KeyCode::Z) { if shift { self.redo_scene(); } else { self.undo_scene(); } return; }
        if ctrl && is_key_pressed(KeyCode::Y) { self.redo_scene(); return; }
        if ctrl && is_key_pressed(KeyCode::O) {
            if shift { self.load_project_dialog(); } else { self.load_atlas_dialog(); }
        }
        if ctrl && is_key_pressed(KeyCode::S) { self.save_project_current_or_dialog(); }
        if ctrl && shift && is_key_pressed(KeyCode::A) { self.export_scene_audit(); return; }
        if ctrl && is_key_pressed(KeyCode::E) { self.export_handoff_dialog(); }
        if ctrl && shift && is_key_pressed(KeyCode::P) { self.export_review_dialog(); }
        if ctrl && is_key_pressed(KeyCode::G) { self.auto_map_sheet(); }
        if ctrl && is_key_pressed(KeyCode::L) { self.refresh_sheet_library(); }
        if ctrl && is_key_pressed(KeyCode::M) { self.reassemble_from_mapped_scene(); }
        if ctrl && shift && is_key_pressed(KeyCode::Enter) { self.learn_from_scene(); }
        if is_key_pressed(KeyCode::PageUp) { self.edit_selected_height(1); }
        if is_key_pressed(KeyCode::PageDown) { self.edit_selected_height(-1); }
        if ctrl && is_key_pressed(KeyCode::W) { self.toggle_selected_water(); }
        if is_key_pressed(KeyCode::Key1) { self.author_tool = AuthorTool::Select; self.status = "Select/placement tool active.".to_string(); }
        if is_key_pressed(KeyCode::Key2) { self.author_tool = AuthorTool::Elevation; self.status = format!("Height paint active at +{}.", self.paint_elevation); }
        if is_key_pressed(KeyCode::Key3) { self.author_tool = AuthorTool::Water; self.status = "Water paint active.".to_string(); }
        if is_key_pressed(KeyCode::Minus) { self.paint_elevation = self.paint_elevation.saturating_sub(1); }
        if is_key_pressed(KeyCode::Equal) { self.paint_elevation = (self.paint_elevation + 1).min(30); }
        if !ctrl && is_key_pressed(KeyCode::R) {
            if self.selected_piece.is_some() { self.checkpoint_scene(); }
            if let Some(piece) = self.selected_piece_mut() {
                piece.rotation_degrees = (piece.rotation_degrees + 90) % 360;
                self.dirty = true;
            }
        }
        if !ctrl && is_key_pressed(KeyCode::H) {
            if self.selected_piece.is_some() { self.checkpoint_scene(); }
            if let Some(piece) = self.selected_piece_mut() { piece.flip_x = !piece.flip_x; self.dirty = true; }
        }
        if !ctrl && is_key_pressed(KeyCode::V) {
            if self.selected_piece.is_some() { self.checkpoint_scene(); }
            if let Some(piece) = self.selected_piece_mut() { piece.flip_y = !piece.flip_y; self.dirty = true; }
        }
        if !ctrl && (is_key_pressed(KeyCode::Delete) || is_key_pressed(KeyCode::Backspace)) {
            self.remove_selected_piece();
        }
        if !ctrl && is_key_pressed(KeyCode::LeftBracket) {
            if self.selected_piece.is_some() { self.checkpoint_scene(); }
            if let Some(piece) = self.selected_piece_mut() { piece.layer -= 1; self.dirty = true; }
        }
        if !ctrl && is_key_pressed(KeyCode::RightBracket) {
            if self.selected_piece.is_some() { self.checkpoint_scene(); }
            if let Some(piece) = self.selected_piece_mut() { piece.layer += 1; self.dirty = true; }
        }
    }

    fn handle_input(&mut self, source_rect: Rect, canvas_rect: Rect, inspector_rect: Rect) {
        self.handle_shortcuts();
        let mouse = mouse_position_local();
        let delta = mouse - self.last_mouse;
        let over_source = source_rect.contains(mouse);
        // The optional details drawer is opaque: never edit the scene through it.
        let blocked_by_details = self.show_inspector && inspector_rect.contains(mouse);
        let edit_canvas = canvas_edit_rect(canvas_rect).contains(mouse) && !blocked_by_details;
        if edit_canvas && is_mouse_button_pressed(MouseButton::Right) && self.author_tool == AuthorTool::Select {
            self.selected_piece = self.hit_piece(canvas_rect, mouse);
            self.remove_selected_piece();
            self.last_mouse = mouse;
            return;
        }
        let divider = Rect::new(source_rect.x + source_rect.w, source_rect.y, GAP, source_rect.h);
        if is_mouse_button_pressed(MouseButton::Left) && divider.contains(mouse) {
            self.resizing_divider = true;
        }
        if self.resizing_divider {
            if is_mouse_button_down(MouseButton::Left) {
                let available = source_rect.w + canvas_rect.w;
                self.pane_ratio = ((mouse.x - source_rect.x) / available).clamp(0.40, 0.60);
            }
            if is_mouse_button_released(MouseButton::Left) { self.resizing_divider = false; }
            self.last_mouse = mouse;
            return; // A divider drag must never select, paint, or move source artwork.
        }
        let space_pan = is_key_down(KeyCode::Space);
        let (_wheel_x, wheel_y) = mouse_wheel();

        if wheel_y != 0.0 {
            let zoom_factor = if wheel_y > 0.0 { ZOOM_STEP } else { 1.0 / ZOOM_STEP };
            if over_source && source_sheet_stack_rect(source_rect, self.atlas_focus).contains(mouse) {
                let visible_h = (source_sheet_stack_rect(source_rect, self.atlas_focus).h - SHEET_LIST_TOP).max(0.0);
                let content_h = self.sheet_library_visible.len() as f32 * SHEET_CARD_H;
                let min_scroll = (visible_h - content_h).min(0.0);
                self.sheet_library_scroll = (self.sheet_library_scroll + wheel_y * 28.0).clamp(min_scroll, 0.0);
            } else if over_source {
                self.source_zoom = (self.source_zoom * zoom_factor).clamp(MIN_SOURCE_ZOOM, MAX_SOURCE_ZOOM);
            } else if edit_canvas {
                self.canvas_zoom = (self.canvas_zoom * zoom_factor).clamp(MIN_CANVAS_ZOOM, MAX_CANVAS_ZOOM);
            }
        }

        if is_mouse_button_pressed(MouseButton::Left) {
            self.is_panning_source = false;
            self.is_panning_canvas = false;
            self.is_painting_height = false;
            self.drag_origin = None;
            if space_pan && over_source {
                self.is_panning_source = true;
            } else if space_pan && edit_canvas {
                self.is_panning_canvas = true;
            } else if over_source {
                if let Some(index) = self.source_sheet_card_at(source_rect, mouse) {
                    let row = source_sheet_stack_rect(source_rect, self.atlas_focus);
                    if mouse.x >= row.x + row.w - 67.0 {
                        let path = self.sheet_library[index].path.clone();
                        if self.source_is_activated(&Self::asset_id(&path)) { self.deactivate_sheet(index); }
                        else { self.open_sheet_from_library(index); }
                    } else {
                        self.open_sheet_from_library(index);
                    }
                } else if let Some(tile) = self.source_tile_at(source_rect, mouse) {
                    self.selected_tile = Some(tile);
                    self.selected_piece = None;
                    self.drag = DragState::SourceTile(tile);
                }
            } else if edit_canvas {
                if self.author_tool == AuthorTool::Elevation {
                    if let Some((gx, gy)) = self.canvas_grid_at(canvas_rect, mouse) {
                        self.checkpoint_scene();
                        self.is_painting_height = true;
                        self.set_height_cell(gx, gy, self.paint_elevation);
                    }
                } else if self.author_tool == AuthorTool::Water {
                    if let Some((gx, gy)) = self.canvas_grid_at(canvas_rect, mouse) {
                        self.checkpoint_scene();
                        self.toggle_water_cell(gx, gy);
                    }
                } else if let Some(index) = self.hit_piece(canvas_rect, mouse) {
                    self.selected_piece = Some(index);
                    self.selected_tile = None;
                    if let Some(piece) = self.pieces.get(index) {
                        self.drag_origin = Some((index, piece.canvas_grid_x, piece.canvas_grid_y));
                    }
                    self.checkpoint_scene();
                    self.drag = DragState::ExistingPiece(index);
                } else {
                    self.selected_piece = None;
                }
            }
        }

        if is_mouse_button_down(MouseButton::Left) {
            if self.is_panning_source {
                self.source_pan += delta;
            } else if self.is_panning_canvas {
                self.canvas_pan += delta;
            } else if edit_canvas && self.is_painting_height && self.author_tool == AuthorTool::Elevation {
                if let Some((gx, gy)) = self.canvas_grid_at(canvas_rect, mouse) { self.set_height_cell(gx, gy, self.paint_elevation); }
            } else if let DragState::ExistingPiece(index) = self.drag {
                if edit_canvas {
                    if let Some((gx, gy)) = self.canvas_grid_at(canvas_rect, mouse) {
                        if let Some(piece) = self.pieces.get_mut(index) {
                            if piece.canvas_grid_x != gx || piece.canvas_grid_y != gy { self.dirty = true; }
                            piece.canvas_grid_x = gx;
                            piece.canvas_grid_y = gy;
                        }
                    }
                }
            }
        }

        if is_mouse_button_released(MouseButton::Left) {
            match self.drag {
                DragState::SourceTile(tile) => {
                    if edit_canvas {
                        if let Some((gx, gy)) = self.canvas_grid_at(canvas_rect, mouse) {
                            self.add_piece_from_tile(tile, gx, gy);
                        }
                    } else {
                        self.status = "Drag canceled: release source tiles over the assembly canvas to place them.".to_string();
                    }
                }
                DragState::ExistingPiece(index) => {
                    if !edit_canvas {
                        if let Some((origin_index, gx, gy)) = self.drag_origin {
                            if origin_index == index {
                                if let Some(piece) = self.pieces.get_mut(index) {
                                    piece.canvas_grid_x = gx;
                                    piece.canvas_grid_y = gy;
                                }
                                self.status = "Move canceled: piece returned to its previous canvas cell.".to_string();
                            }
                        }
                    }
                }
                DragState::None => {}
            }
            self.drag = DragState::None;
            self.drag_origin = None;
            self.is_panning_source = false;
            self.is_panning_canvas = false;
            self.is_painting_height = false;
        }

        self.last_mouse = mouse;
    }

    fn source_tile_at(&self, panel: Rect, mouse: Vec2) -> Option<SourceTile> {
        let atlas = self.atlas.as_ref()?;
        let preview = source_preview_rect(panel, self.atlas_focus);
        if !preview.contains(mouse) { return None; }
        let local = (mouse - vec2(preview.x, preview.y) - self.source_pan) / self.source_zoom;
        if local.x < 0.0 || local.y < 0.0 || local.x >= atlas.width as f32 || local.y >= atlas.height as f32 {
            return None;
        }
        let tile_x = (local.x as i32) / TILE_SIZE;
        let tile_y = (local.y as i32) / TILE_SIZE;
        Some(SourceTile { tile_x, tile_y })
    }

    fn canvas_grid_at(&self, panel: Rect, mouse: Vec2) -> Option<(i32, i32)> {
        if !panel.contains(mouse) || mouse.y < panel.y + 38.0 { return None; }
        let local = (mouse - vec2(panel.x, panel.y) - self.canvas_pan) / self.canvas_zoom;
        Some(((local.x / TILE_SIZE as f32).floor() as i32, (local.y / TILE_SIZE as f32).floor() as i32))
    }

    fn hit_piece(&self, panel: Rect, mouse: Vec2) -> Option<usize> {
        let mut indices: Vec<usize> = (0..self.pieces.len()).collect();
        indices.sort_by_key(|index| self.pieces[*index].layer);
        indices.into_iter().rev().find(|index| {
            let piece = &self.pieces[*index];
            let pos = self.canvas_piece_rect(panel, piece);
            pos.contains(mouse)
        })
    }

    fn canvas_piece_rect(&self, panel: Rect, piece: &AssemblyPiece) -> Rect {
        Rect::new(
            panel.x + self.canvas_pan.x + piece.canvas_grid_x as f32 * TILE_SIZE as f32 * self.canvas_zoom,
            panel.y + self.canvas_pan.y + piece.canvas_grid_y as f32 * TILE_SIZE as f32 * self.canvas_zoom,
            TILE_SIZE as f32 * self.canvas_zoom,
            TILE_SIZE as f32 * self.canvas_zoom,
        )
    }

    fn reset_canvas_view(&mut self) {
        self.canvas_zoom = DEFAULT_CANVAS_ZOOM;
        self.canvas_pan = vec2(56.0, 116.0);
        self.status = "Canvas view reset to a readable 2x authoring scale.".to_string();
    }

    fn fit_canvas_to_pieces(&mut self, panel: Rect) {
        if self.pieces.is_empty() {
            self.reset_canvas_view();
            return;
        }
        let min_x = self.pieces.iter().map(|piece| piece.canvas_grid_x).min().unwrap_or(0);
        let max_x = self.pieces.iter().map(|piece| piece.canvas_grid_x).max().unwrap_or(0);
        let min_y = self.pieces.iter().map(|piece| piece.canvas_grid_y).min().unwrap_or(0);
        let max_y = self.pieces.iter().map(|piece| piece.canvas_grid_y).max().unwrap_or(0);
        let width_tiles = (max_x - min_x + 1).max(1) as f32;
        let height_tiles = (max_y - min_y + 1).max(1) as f32;
        let fit_zoom_x = (panel.w - 96.0).max(96.0) / (width_tiles * TILE_SIZE as f32);
        let fit_zoom_y = (panel.h - 150.0).max(96.0) / (height_tiles * TILE_SIZE as f32);
        self.canvas_zoom = fit_zoom_x.min(fit_zoom_y).clamp(MIN_CANVAS_ZOOM, MAX_CANVAS_ZOOM);
        self.canvas_pan = vec2(
            56.0 - min_x as f32 * TILE_SIZE as f32 * self.canvas_zoom,
            116.0 - min_y as f32 * TILE_SIZE as f32 * self.canvas_zoom,
        );
        self.status = "Canvas view fit to current assembly without dropping below 100% zoom.".to_string();
    }

    fn mapping_record_path(&self) -> Option<PathBuf> {
        let atlas = self.atlas.as_ref()?;
        let root = env::current_dir().ok()?;
        Self::mapping_record_path_for(&root, &atlas.path, self.category)
    }

    fn write_mapping_record(&mut self, handoff_path: Option<&Path>) {
        self.write_all_mapping_records(handoff_path, MAPPED_TILE_STATUS_DRAFT, self.mapping_stage.label(), false);
    }

    fn write_all_mapping_records(&mut self, handoff_path: Option<&Path>, tile_status: &str, lifecycle_stage: &str, learned_from_scene: bool) {
        // Saved records are per source, not per currently highlighted sheet.
        // Swap temporarily without loading source bytes or changing scene placements.
        let Some(original) = self.atlas.take() else { return; };
        let sources = std::mem::take(&mut self.source_stack);
        let selected_category = self.category;
        let mut restored = Vec::with_capacity(sources.len());
        self.atlas = Some(original);
        self.category = AssetCategory::from_file_hint(&self.atlas.as_ref().expect("source present").path);
        self.write_mapping_record_with_status(handoff_path, tile_status, lifecycle_stage, learned_from_scene);
        for sheet in sources {
            let previous = self.atlas.replace(sheet).expect("active atlas restored before cycling");
            restored.push(previous);
            self.category = AssetCategory::from_file_hint(&self.atlas.as_ref().expect("source present").path);
            self.write_mapping_record_with_status(handoff_path, tile_status, lifecycle_stage, learned_from_scene);
        }
        self.source_stack = restored;
        // This order restores the originally highlighted source last, not the
        // intermediate sources; the source selected in the UI is unchanged.
        if !self.source_stack.is_empty() {
            let original = self.source_stack.remove(0);
            let selected = self.atlas.replace(original).expect("active source exists");
            self.source_stack.push(selected);
        }
        self.category = selected_category;
    }

    fn write_mapping_record_with_status(&mut self, handoff_path: Option<&Path>, tile_status: &str, lifecycle_stage: &str, learned_from_scene: bool) {
        if self.atlas.is_none() || self.pieces.is_empty() { return; }
        let Some(path) = self.mapping_record_path() else { return; };
        let Some(atlas) = &self.atlas else { return; };
        let atlas_path = atlas.path.clone();
        let source_name = atlas_path.file_name().and_then(|name| name.to_str()).unwrap_or("atlas").to_string();
        let source_atlas_path = atlas_path.to_string_lossy().replace('\\', "/");
        let parent = path.parent().map(Path::to_path_buf);
        if let Some(parent) = parent {
            if let Err(error) = fs::create_dir_all(&parent) {
                self.status = format!("Mapping record folder failed: {error}");
                return;
            }
        }
        let previous_records: BTreeMap<(i32, i32), (String, String)> = fs::read_to_string(&path)
            .ok().and_then(|text| serde_json::from_str::<MappedSheetRecord>(&text).ok())
            .map(|record| record.mapped_tiles.into_iter().map(|tile|
                ((tile.source_tile_x, tile.source_tile_y), (tile.semantic_role, tile.status))).collect())
            .unwrap_or_default();
        let mapped_tiles: Vec<MappedSheetTileRecord> = self.pieces.iter()
            .filter(|piece| piece.source_asset_id == atlas.id)
            .map(|piece| MappedSheetTileRecord {
            source_tile_x: piece.source_tile_x,
            source_tile_y: piece.source_tile_y,
            source_rect: piece.source_rect,
            semantic_role: piece.semantic_role.clone(),
            terrain_family: terrain_family_for_piece(&atlas_path, &piece.semantic_role, self.category),
            topology_role: topology_role_for_piece(&piece.semantic_role),
            layer: piece.layer,
            layer_role: layer_role_for_piece(&piece.semantic_role, piece.layer),
            collision_profile: collision_profile_for_piece(&piece.semantic_role),
            compatibility_class: compatibility_class_for_piece(&piece.semantic_role),
            // Re-saving an unchanged corrected role must not discard learning.
            // Never carry approval across a changed semantic role.
            status: if piece.semantic_role.starts_with("unresolved.") {
                MAPPED_TILE_STATUS_DRAFT.to_string()
            } else { previous_records.get(&(piece.source_tile_x, piece.source_tile_y))
                .filter(|(old_role, _)| old_role.as_str() == piece.semantic_role.as_str())
                .map(|(_,old_status)| if old_status == MAPPED_TILE_STATUS_APPROVED ||
                    (old_status == MAPPED_TILE_STATUS_LEARNED && tile_status == MAPPED_TILE_STATUS_DRAFT)
                    { old_status.clone() } else { tile_status.to_string() })
                .unwrap_or_else(|| tile_status.to_string()) },
        }).collect();
        if mapped_tiles.is_empty() { return; } // Never overwrite an existing sheet mapping with another sheet's empty record.
        let unique_tile_count = mapped_tiles
            .iter()
            .map(|tile| (tile.source_tile_x, tile.source_tile_y))
            .collect::<BTreeSet<_>>()
            .len();
        let nonempty_cells = atlas.cell_profiles.iter().filter(|cell| cell.coverage > 0.0).count().max(1);
        let valid_cells: BTreeSet<(i32, i32)> = atlas.cell_profiles.iter()
            .filter(|cell| cell.coverage > 0.0)
            .map(|cell| (cell.tile_x, cell.tile_y)).collect();
        let valid_mapped = mapped_tiles.iter().map(|tile| (tile.source_tile_x, tile.source_tile_y))
            .collect::<BTreeSet<_>>().intersection(&valid_cells).count();
        let coverage_percent = (valid_mapped as f32 / nonempty_cells as f32 * 100.0).min(100.0);
        let record = MappedSheetRecord {
            schema: MAPPED_SHEET_SCHEMA.to_string(),
            tool: "haven_atlas_mapper_lite".to_string(),
            source_atlas_path,
            source_atlas_file_name: source_name,
            tile_size: TILE_SIZE,
            category: self.category.stable_key().to_string(),
            category_label: self.category.label().to_string(),
            assembly_name: self.assembly_name.clone(),
            source_sheet_profile: source_sheet_profile_id(&atlas_path, self.category),
            provider: provider_for_sheet(&atlas_path, self.category),
            season: season_for_sheet(&atlas_path).unwrap_or("none").to_string(),
            terrain_lane_authority: "content/worldgen/terrain_lane_authority_v1.json".to_string(),
            piece_count: mapped_tiles.len(),
            mapped_tile_count: unique_tile_count,
            mapped_tiles,
            coverage_percent,
            lifecycle_stage: lifecycle_stage.to_string(),
            correction_scene_count: self.scene_generation_count,
            learned_from_scene,
            terrain_lane_role_binding: format!("{}:{}", self.category.stable_key(), self.assembly_name),
            project_file: self.project_path.as_ref().map(|p| p.to_string_lossy().replace('\\', "/")),
            handoff_file: handoff_path
                .map(|p| p.to_string_lossy().replace('\\', "/"))
                .or_else(|| self.last_handoff_path.as_ref().map(|p| p.to_string_lossy().replace('\\', "/"))),
            updated_unix_seconds: unix_seconds(),
            compatibility_notes: vec![
                "Terrain Lane records bind exact source cells to provider-neutral terrain roles; V7 remains a legacy/compatibility provider until seasonal profiles are complete.".to_string(),
                "Mapped seasonal terrain cells are source-art grammar evidence first and runtime provider entries only after coverage/collision/layer validation.".to_string(),
                "Structural providers such as cliffs, ramps, ladders, and waterfalls remain compatible by terrain role and layer, not by pretending all sheets share one atlas layout.".to_string(),
            ],
            asset_intake_notes: vec![
                "Per-tile green badges mean exact source-cell metadata exists for that tile in the asset intake lane.".to_string(),
                "Sheet green state means mapper metadata exists; runtime publication still requires sockets, footprint, collision, traversal, provenance, and validation.".to_string(),
                "v0.4 records distinguish draft mapped cells from learned correction-scene evidence for Terrain Lane compatibility checks.".to_string(),
            ],
        };
        if let Ok(text) = serde_json::to_string_pretty(&record) {
            if fs::write(path, text).is_ok() {
                let atlas_key = normalize_path_key(&atlas_path);
                let summary = self.mapping_summary_for_sheet_path(&atlas_path, self.category);
                for card in &mut self.sheet_library {
                    if normalize_path_key(&card.path) == atlas_key {
                        card.status = summary.status;
                        card.mapped_tile_count = summary.mapped_tile_count;
                        card.coverage_percent = summary.coverage_percent;
                    }
                }
            }
        }
    }

    fn refresh_mapping_stage_from_record(&mut self) {
        if !self.pieces.is_empty() { return; }
        if let Some(path) = self.mapping_record_path() {
            if path.exists() {
                self.mapping_stage = MappingStage::ProjectSaved;
            }
        }
    }
}


fn source_sheet_profile_id(path: &Path, category: AssetCategory) -> String {
    let name = path.file_name()
        .and_then(|name| name.to_str())
        .unwrap_or("source_sheet")
        .to_ascii_lowercase();
    let path_key = path.to_string_lossy().replace('\\', "/").to_ascii_lowercase();
    if is_lpc_revised_seasonal_terrain_sheet(path) {
        format!("terrain.source.lpc_revised.seasonal.{}", season_for_sheet(path).unwrap_or("unknown"))
    } else if path_key.contains("lpc-terrains-v7") || name.contains("terrain-v7") || name.contains("terrain-map-v7") {
        "terrain.provider.lpc_v7_legacy.compatibility".to_string()
    } else if path_key.contains("cliffs_grass_top") || name.contains("lpc_cliffs_") {
        "terrain.provider.lpc_directional_ramp_and_contour.source".to_string()
    } else if name.contains("cliff") {
        "terrain.provider.elizawy_cliff.source".to_string()
    } else if name.contains("waterfall") {
        "terrain.provider.elizawy_waterfall.source".to_string()
    } else {
        format!("asset.source.{}.unprofiled", category.stable_key())
    }
}

fn provider_for_sheet(path: &Path, category: AssetCategory) -> String {
    let profile = source_sheet_profile_id(path, category);
    if profile.contains("lpc_revised") {
        "lpc_revised_seasonal".to_string()
    } else if profile.contains("lpc_v7") {
        "lpc_v7_legacy".to_string()
    } else if profile.contains("lpc_directional") {
        "oga_lpc_cliff_family".to_string()
    } else if profile.contains("elizawy_cliff") || profile.contains("elizawy_waterfall") {
        "elizawy_lpc_revised".to_string()
    } else {
        category.stable_key().to_string()
    }
}

fn is_lpc_revised_seasonal_terrain_sheet(path: &Path) -> bool {
    let Some(name) = path.file_name().and_then(|name| name.to_str()) else { return false; };
    matches!(name.to_ascii_lowercase().as_str(), "terrain_spring.png" | "terrain_summer.png" | "terrain_autumn.png" | "terrain_winter.png")
}

fn season_for_sheet(path: &Path) -> Option<&'static str> {
    let name = path.file_name()?.to_str()?.to_ascii_lowercase();
    if name.contains("spring") { Some("spring") }
    else if name.contains("summer") { Some("summer") }
    else if name.contains("autumn") || name.contains("fall") { Some("autumn") }
    else if name.contains("winter") || name.contains("snow") { Some("winter") }
    else { None }
}

fn terrain_lane_profile_role(path: &Path, tile_x: i32, tile_y: i32, visual_role: CellRole, local_x: i32, local_y: i32) -> Option<String> {
    if !is_lpc_revised_seasonal_terrain_sheet(path) {
        return None;
    }
    let season = season_for_sheet(path).unwrap_or("seasonal");
    let role = match visual_role {
        CellRole::Empty => "terrain.empty_or_padding".to_string(),
        CellRole::Water => {
            if tile_y >= 20 {
                "terrain.water.depth_or_rim".to_string()
            } else if tile_y >= 10 {
                "terrain.water.shoreline_or_bank_topology".to_string()
            } else {
                "terrain.water.surface_or_channel".to_string()
            }
        }
        CellRole::Grass => {
            if tile_y >= 10 {
                "terrain.shoreline.grass_bank_or_island_edge".to_string()
            } else if tile_y <= 4 {
                "terrain.base.grass_or_field".to_string()
            } else {
                "terrain.overlay.grass_patch_or_transition".to_string()
            }
        }
        CellRole::Sand => {
            if tile_y >= 10 {
                "terrain.shoreline.sand_or_path_bank".to_string()
            } else {
                "terrain.base.path_sand_or_bank".to_string()
            }
        }
        CellRole::Stone => "terrain.detail.rock_hard_edge_or_pebble_path".to_string(),
        CellRole::Cliff => "terrain.bank.earth_cut_or_transition".to_string(),
        CellRole::Wood => "terrain.detail.wood_bridge_or_debris_candidate".to_string(),
        CellRole::Detail => "terrain.detail.scatter_overlay".to_string(),
    };
    Some(format!("{role}.{season}.cell_{tile_x}_{tile_y}.draft_profile_{local_x}_{local_y}"))
}

fn terrain_family_for_piece(path: &Path, semantic_role: &str, category: AssetCategory) -> String {
    if category != AssetCategory::Terrain {
        return category.stable_key().to_string();
    }
    if semantic_role.contains("water") || semantic_role.contains("shoreline") {
        "terrain.water_and_shoreline".to_string()
    } else if semantic_role.contains("base") || semantic_role.contains("ground") {
        "terrain.base_surface".to_string()
    } else if semantic_role.contains("overlay") || semantic_role.contains("detail") {
        "terrain.overlay_and_detail".to_string()
    } else if is_lpc_revised_seasonal_terrain_sheet(path) {
        "terrain.lpc_revised_seasonal".to_string()
    } else {
        "terrain.unclassified".to_string()
    }
}

fn topology_role_for_piece(semantic_role: &str) -> String {
    if semantic_role.contains("shoreline") || semantic_role.contains("bank") {
        "edge_or_bank_transition".to_string()
    } else if semantic_role.contains("water") && semantic_role.contains("depth") {
        "depth_rim_or_center".to_string()
    } else if semantic_role.contains("water") {
        "water_surface_or_channel".to_string()
    } else if semantic_role.contains("overlay") || semantic_role.contains("detail") {
        "overlay_detail".to_string()
    } else if semantic_role.contains("base") || semantic_role.contains("ground") {
        "base_fill".to_string()
    } else if semantic_role.contains("cliff") || semantic_role.contains("connector") {
        "structural_connector_or_boundary".to_string()
    } else {
        "unclassified_cell".to_string()
    }
}

fn layer_role_for_piece(semantic_role: &str, layer: i32) -> String {
    if semantic_role.contains("base") || semantic_role.contains("ground") {
        "terrain_base".to_string()
    } else if semantic_role.contains("shoreline") || semantic_role.contains("transition") || semantic_role.contains("bank") {
        "terrain_transition".to_string()
    } else if semantic_role.contains("overlay") || semantic_role.contains("detail") {
        "terrain_overlay_detail".to_string()
    } else if semantic_role.contains("water") {
        "terrain_water".to_string()
    } else if layer >= 10 {
        "structural_or_foreground".to_string()
    } else {
        "layer_unassigned".to_string()
    }
}

fn collision_profile_for_piece(semantic_role: &str) -> String {
    if semantic_role.contains("water") {
        "water_or_blocked_until_role_confirmed".to_string()
    } else if semantic_role.contains("overlay") || semantic_role.contains("detail") {
        "inherit_from_base_pass_through".to_string()
    } else if semantic_role.contains("cliff") {
        "structural_cliff_collision_required".to_string()
    } else {
        "inherit_from_terrain_role".to_string()
    }
}

fn compatibility_class_for_piece(semantic_role: &str) -> String {
    if semantic_role.contains("shoreline") || semantic_role.contains("bank") {
        "terrain_water_land_boundary".to_string()
    } else if semantic_role.contains("overlay") || semantic_role.contains("detail") {
        "overlay_compatible_with_host_surface".to_string()
    } else if semantic_role.contains("water") {
        "water_family".to_string()
    } else if semantic_role.contains("base") || semantic_role.contains("ground") {
        "base_surface_family".to_string()
    } else {
        "needs_compatibility_review".to_string()
    }
}


fn analyze_tile_sheet(bytes: &[u8], fallback_width: i32, fallback_height: i32) -> Vec<SourceCellProfile> {
    let Ok(image) = image::load_from_memory(bytes) else {
        return fallback_profiles(fallback_width, fallback_height);
    };
    let rgba = image.to_rgba8();
    let width = rgba.width() as i32;
    let height = rgba.height() as i32;
    let cols = (width / TILE_SIZE).max(1);
    let rows = (height / TILE_SIZE).max(1);
    let mut profiles = Vec::with_capacity((cols * rows).max(0) as usize);
    for tile_y in 0..rows {
        for tile_x in 0..cols {
            let mut count = 0.0f32;
            let mut r = 0.0f32;
            let mut g = 0.0f32;
            let mut b = 0.0f32;
            for py in 0..TILE_SIZE {
                for px in 0..TILE_SIZE {
                    let sx = tile_x * TILE_SIZE + px;
                    let sy = tile_y * TILE_SIZE + py;
                    if sx < 0 || sy < 0 || sx >= width || sy >= height { continue; }
                    let pixel = rgba.get_pixel(sx as u32, sy as u32).0;
                    if pixel[3] > 18 {
                        count += 1.0;
                        r += pixel[0] as f32;
                        g += pixel[1] as f32;
                        b += pixel[2] as f32;
                    }
                }
            }
            let coverage = count / ((TILE_SIZE * TILE_SIZE) as f32);
            let (ar, ag, ab) = if count > 0.0 { (r / count, g / count, b / count) } else { (0.0, 0.0, 0.0) };
            profiles.push(SourceCellProfile {
                tile_x,
                tile_y,
                coverage,
                avg_rgb: [ar, ag, ab],
                role: classify_cell_role(coverage, ar, ag, ab),
            });
        }
    }
    profiles
}

fn fallback_profiles(width: i32, height: i32) -> Vec<SourceCellProfile> {
    let cols = (width / TILE_SIZE).max(1);
    let rows = (height / TILE_SIZE).max(1);
    let mut profiles = Vec::with_capacity((cols * rows).max(0) as usize);
    for tile_y in 0..rows {
        for tile_x in 0..cols {
            profiles.push(SourceCellProfile { tile_x, tile_y, coverage: 1.0, avg_rgb: [128.0, 128.0, 128.0], role: CellRole::Detail });
        }
    }
    profiles
}

fn classify_cell_role(coverage: f32, r: f32, g: f32, b: f32) -> CellRole {
    if coverage < 0.10 { return CellRole::Empty; }
    if b > g * 1.08 && b > r * 1.20 { return CellRole::Water; }
    if g > r * 1.05 && g > b * 1.08 { return CellRole::Grass; }
    if r > 145.0 && g > 112.0 && b < 115.0 && (r - g).abs() < 70.0 { return CellRole::Sand; }
    if r > g * 1.05 && g > b * 1.08 && r > 72.0 { return CellRole::Cliff; }
    if r > 70.0 && g > 45.0 && b < 88.0 { return CellRole::Wood; }
    if (r - g).abs() < 28.0 && (g - b).abs() < 28.0 && r > 48.0 { return CellRole::Stone; }
    CellRole::Detail
}

fn profile_at(profiles: &[SourceCellProfile], cols: i32, tile_x: i32, tile_y: i32) -> Option<SourceCellProfile> {
    if tile_x < 0 || tile_y < 0 || cols <= 0 { return None; }
    let index = (tile_y * cols + tile_x) as usize;
    profiles.get(index).copied().filter(|cell| cell.tile_x == tile_x && cell.tile_y == tile_y)
}

fn best_scene_window(
    profiles: &[SourceCellProfile],
    cols: i32,
    rows: i32,
    requested_w: i32,
    requested_h: i32,
    category: AssetCategory,
) -> Option<SourceSceneWindow> {
    if profiles.is_empty() || cols <= 0 || rows <= 0 { return None; }
    let w = requested_w.clamp(1, cols.max(1));
    let h = requested_h.clamp(1, rows.max(1));
    let max_x = (cols - w).max(0);
    let max_y = (rows - h).max(0);
    let mut best: Option<SourceSceneWindow> = None;
    for y in 0..=max_y {
        for x in 0..=max_x {
            let score = scene_window_score(profiles, cols, x, y, w, h, category);
            if best.map(|window| score > window.score).unwrap_or(true) {
                best = Some(SourceSceneWindow { x, y, w, h, score });
            }
        }
    }
    best
}

fn scene_window_score(profiles: &[SourceCellProfile], cols: i32, x: i32, y: i32, w: i32, h: i32, category: AssetCategory) -> f32 {
    let mut score = 0.0f32;
    let mut grass = 0.0f32;
    let mut water = 0.0f32;
    let mut cliff = 0.0f32;
    let mut wood = 0.0f32;
    let mut stone = 0.0f32;
    let mut detail = 0.0f32;
    let mut occupied = 0.0f32;
    for sy in y..(y + h) {
        for sx in x..(x + w) {
            let Some(cell) = profile_at(profiles, cols, sx, sy) else { continue; };
            if cell.role == CellRole::Empty || cell.coverage < 0.10 { continue; }
            occupied += cell.coverage.max(0.25);
            score += cell.coverage;
            match cell.role {
                CellRole::Grass | CellRole::Sand => grass += 1.0,
                CellRole::Water => water += 1.0,
                CellRole::Cliff => cliff += 1.0,
                CellRole::Wood => wood += 1.0,
                CellRole::Stone => stone += 1.0,
                CellRole::Detail => detail += 1.0,
                CellRole::Empty => {}
            }
        }
    }
    score += occupied * 0.45;
    match category {
        AssetCategory::Cliff => {
            score += cliff * 5.0 + grass * 2.0 + water * 2.0 + detail * 0.6;
            if cliff > 0.0 && grass > 0.0 { score += 6.0; }
            if cliff > 0.0 && water > 0.0 { score += 4.0; }
        }
        AssetCategory::Terrain => {
            score += grass * 3.0 + water * 2.4 + stone * 1.1 + detail * 0.8;
            if grass > 0.0 && water > 0.0 { score += 5.0; }
        }
        AssetCategory::Structure | AssetCategory::House => {
            score += wood * 3.5 + stone * 2.0 + detail * 1.0;
            if wood + stone > 4.0 { score += 4.0; }
        }
        AssetCategory::Object | AssetCategory::Equipment | AssetCategory::Ui => {
            score += detail * 3.0 + wood * 1.2 + stone * 1.2;
        }
        AssetCategory::Character | AssetCategory::Fx => {
            score += detail * 2.5 + grass * 0.8 + wood * 0.8 + stone * 0.8;
        }
    }
    score
}

fn choose_tile_from_profiles(
    profiles: &[SourceCellProfile],
    cols: i32,
    rows: i32,
    seed: &mut u64,
    roles: &[CellRole],
    ordinal: u64,
) -> SourceTile {
    let mut candidates: Vec<SourceCellProfile> = profiles
        .iter()
        .copied()
        .filter(|cell| roles.contains(&cell.role) && cell.coverage >= 0.10)
        .collect();
    if candidates.is_empty() {
        candidates = profiles.iter().copied().filter(|cell| cell.role != CellRole::Empty && cell.coverage >= 0.10).collect();
    }
    if candidates.is_empty() {
        return SourceTile { tile_x: ordinal as i32 % cols.max(1), tile_y: (ordinal as i32 / cols.max(1)).rem_euclid(rows.max(1)) };
    }
    *seed = seed.wrapping_mul(2862933555777941757).wrapping_add(3037000493 ^ ordinal);
    let index = ((*seed >> 32) as usize) % candidates.len();
    let picked = candidates[index];
    SourceTile { tile_x: picked.tile_x, tile_y: picked.tile_y }
}

fn sanitize_file_stem(value: &str) -> String {
    let mut output = String::new();
    for ch in value.chars() {
        if ch.is_ascii_alphanumeric() || ch == '-' || ch == '_' {
            output.push(ch);
        } else if !output.ends_with('_') {
            output.push('_');
        }
    }
    let trimmed = output.trim_matches('_');
    if trimmed.is_empty() { "atlas_assembly".to_string() } else { trimmed.to_string() }
}

fn mouse_position_local() -> Vec2 {
    let (x, y) = mouse_position();
    vec2(x, y)
}

fn unix_seconds() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_secs())
        .unwrap_or(0)
}

fn next_index(seed: &mut u64, max: i32) -> i32 {
    if max <= 1 { return 0; }
    *seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
    ((*seed >> 32) as i32).rem_euclid(max)
}

fn draw_button(rect: Rect, label: &str, active: bool) -> bool {
    let mouse = mouse_position_local();
    let hovered = rect.contains(mouse);
    let fill = if active {
        Color::new(0.18, 0.36, 0.48, 1.0)
    } else if hovered {
        Color::new(0.13, 0.17, 0.22, 1.0)
    } else {
        Color::new(0.075, 0.092, 0.118, 1.0)
    };
    draw_rectangle(rect.x + 1.0, rect.y + 2.0, rect.w, rect.h, Color::new(0.0, 0.0, 0.0, 0.22));
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, fill);
    draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 1.0, if hovered { Color::new(0.40, 0.54, 0.66, 1.0) } else { Color::new(0.23, 0.28, 0.35, 1.0) });
    draw_text(label, rect.x + 8.0, rect.y + rect.h * 0.66, 16.0, Color::new(0.88, 0.91, 0.94, 1.0));
    hovered && is_mouse_button_pressed(MouseButton::Left)
}

fn draw_panel(rect: Rect, title: &str, subtitle: &str) {
    draw_rectangle(rect.x + 3.0, rect.y + 4.0, rect.w, rect.h, Color::new(0.0, 0.0, 0.0, 0.26));
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, Color::new(0.030, 0.036, 0.047, 1.0));
    draw_rectangle(rect.x + 1.0, rect.y + 1.0, rect.w - 2.0, rect.h - 2.0, Color::new(0.044, 0.053, 0.069, 1.0));
    draw_rectangle(rect.x, rect.y, rect.w, 38.0, Color::new(0.060, 0.073, 0.096, 1.0));
    draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 1.0, Color::new(0.23, 0.29, 0.36, 1.0));
    draw_line(rect.x, rect.y + 38.0, rect.x + rect.w, rect.y + 38.0, 1.0, Color::new(0.14, 0.18, 0.23, 1.0));
    draw_text(title, rect.x + 12.0, rect.y + 22.0, 18.0, Color::new(0.92, 0.94, 0.96, 1.0));
    draw_text(subtitle, rect.x + 12.0, rect.y + 34.0, 12.0, Color::new(0.56, 0.64, 0.72, 1.0));
}

fn draw_dock_tabs(rect: Rect, labels: &[&str], active_index: usize) {
    let mut x = rect.x + 12.0;
    let y = rect.y + 40.0;
    for (index, label) in labels.iter().enumerate() {
        let w = ((*label).len() as f32 * 7.5 + 26.0).clamp(72.0, 168.0);
        let active = index == active_index;
        let fill = if active { Color::new(0.10, 0.22, 0.31, 1.0) } else { Color::new(0.052, 0.064, 0.083, 1.0) };
        let line = if active { Color::new(0.19, 0.57, 0.72, 1.0) } else { Color::new(0.16, 0.21, 0.27, 1.0) };
        draw_rectangle(x, y, w, 22.0, fill);
        draw_rectangle_lines(x, y, w, 22.0, 1.0, line);
        if active { draw_rectangle(x, y + 20.0, w, 2.0, Color::new(0.12, 0.75, 0.92, 1.0)); }
        draw_text(label, x + 10.0, y + 15.0, 13.0, Color::new(0.78, 0.86, 0.91, 1.0));
        x += w + 6.0;
    }
}

fn draw_grid(rect: Rect, pan: Vec2, zoom: f32, line_color: Color) {
    let step = TILE_SIZE as f32 * zoom;
    if step < 4.0 { return; }
    let start_x = rect.x + pan.x.rem_euclid(step);
    let start_y = rect.y + pan.y.rem_euclid(step);
    let mut x = start_x;
    while x < rect.x + rect.w {
        draw_line(x, rect.y + 38.0, x, rect.y + rect.h, 1.0, line_color);
        x += step;
    }
    let mut y = start_y;
    while y < rect.y + rect.h {
        draw_line(rect.x, y, rect.x + rect.w, y, 1.0, line_color);
        y += step;
    }
}

fn draw_status_pill(rect: Rect, label: &str, good: bool) {
    let color = if good { Color::new(0.13, 0.48, 0.28, 1.0) } else { Color::new(0.42, 0.30, 0.14, 1.0) };
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, color);
    draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 1.0, Color::new(0.58, 0.69, 0.72, 0.55));
    draw_text(label, rect.x + 8.0, rect.y + rect.h * 0.68, 14.0, Color::new(0.96, 0.98, 0.98, 1.0));
}

fn draw_wrapped_line(text: &str, x: f32, y: f32, max_chars: usize, font_size: f32, color: Color) -> f32 {
    let mut line = String::new();
    let mut yy = y;
    for word in text.split_whitespace() {
        if !line.is_empty() && line.len() + word.len() + 1 > max_chars {
            draw_text(&line, x, yy, font_size, color);
            yy += font_size + 6.0;
            line.clear();
        }
        if !line.is_empty() { line.push(' '); }
        line.push_str(word);
    }
    if !line.is_empty() {
        draw_text(&line, x, yy, font_size, color);
        yy += font_size + 6.0;
    }
    yy
}

fn stable_path_hash(bytes: &[u8]) -> u64 {
    // FNV-1a is a deterministic filename disambiguator, NOT a source integrity proof.
    let mut hash = 0xcbf29ce484222325u64;
    for byte in bytes { hash = (hash ^ u64::from(*byte)).wrapping_mul(0x100000001b3); }
    hash
}

fn draw_top_bar(app: &mut MapperApp) {
    draw_rectangle(0.0, 0.0, screen_width(), TOP_BAR_H, Color::new(0.028, 0.035, 0.047, 1.0));
    draw_rectangle(0.0, 0.0, screen_width(), 4.0, Color::new(0.12, 0.32, 0.45, 1.0));
    draw_text("ElizaWy | Summer Mapper", 14.0, 27.0, 23.0, WHITE);
    draw_text(MAPPER_BUILD, 14.0, 92.0, 11.0, Color::new(0.41, 0.84, 0.71, 1.0));
    draw_text("SOURCE ATLAS   <->   EXAMPLE SCENE", 14.0, 49.0, 13.0, Color::new(0.65, 0.80, 0.88, 1.0));
    draw_text("Draft > correct > save > learn > stage > review", 14.0, 75.0, 12.0, Color::new(0.73, 0.78, 0.82, 1.0));
    // One toolbar owns project actions; the second owns the mapping workflow.
    // No duplicate commands in the optional inspector or decorative tabs.
    let x = 346.0;
    let first = 9.0;
    if draw_button(Rect::new(x, first, 91.0, 27.0), "Open scene", false) { app.load_project_dialog(); }
    if draw_button(Rect::new(x + 97.0, first, 66.0, 27.0), "Save", false) { app.save_project_current_or_dialog(); }
    if draw_button(Rect::new(x + 169.0, first, 95.0, 27.0), "Save master", false) { app.save_startup_summer_demo(); }
    if draw_button(Rect::new(x + 270.0, first, 82.0, 27.0), "Load PNG", false) { app.load_atlas_dialog(); }
    if draw_button(Rect::new(x + 358.0, first, 68.0, 27.0), "Undo", false) { app.undo_scene(); }
    if draw_button(Rect::new(x + 432.0, first, 68.0, 27.0), "Redo", false) { app.redo_scene(); }
    if draw_button(Rect::new(x + 506.0, first, 82.0, 27.0), if app.show_inspector { "Hide info" } else { "Details [I]" }, app.show_inspector) {
        app.show_inspector = !app.show_inspector;
    }

    let second = 46.0;
    if draw_button(Rect::new(x, second, 101.0, 27.0), "1 Draft", false) { app.auto_map_sheet(); }
    if draw_button(Rect::new(x + 107.0, second, 101.0, 27.0), "2 Learn", false) { app.learn_from_scene(); }
    if draw_button(Rect::new(x + 214.0, second, 125.0, 27.0), "3 Stage missing cells", false) { app.reassemble_from_mapped_scene(); }
    if draw_button(Rect::new(x + 345.0, second, 90.0, 27.0), "4 Audit", false) { app.export_scene_audit(); }
    if draw_button(Rect::new(x + 441.0, second, 94.0, 27.0), "5 Review", false) { app.export_review_dialog(); }
    if draw_button(Rect::new(x + 541.0, second, 100.0, 27.0), "6 Handoff", false) { app.export_handoff_dialog(); }
    draw_text("No recipe reroll yet; candidate only.", x + 649.0, 64.0, 12.0, Color::new(0.94, 0.73, 0.45, 1.0));
}

fn draw_source_panel(app: &mut MapperApp, source_rect: Rect) {
    draw_panel(source_rect, "LEFT | ElizaWy Summer Source Library", "Browse by group; select a source without changing scene geometry");
    if draw_button(Rect::new(source_rect.x + source_rect.w - 198.0, source_rect.y + 9.0, 104.0, 21.0),
        if app.atlas_focus { "More library" } else { "Larger atlas" }, false) {
        app.atlas_focus = !app.atlas_focus;
        app.sheet_library_scroll = 0.0;
    }
    if draw_button(Rect::new(source_rect.x + source_rect.w - 88.0, source_rect.y + 9.0, 74.0, 21.0), "Refresh", false) {
        app.refresh_sheet_library();
    }

    let stack = source_sheet_stack_rect(source_rect, app.atlas_focus);
    draw_rectangle(stack.x, stack.y, stack.w, stack.h, Color::new(0.022, 0.028, 0.037, 1.0));
    draw_rectangle_lines(stack.x, stack.y, stack.w, stack.h, 1.0, Color::new(0.14, 0.19, 0.25, 1.0));
    draw_text("Original sheets | ON = activated for this scene", stack.x + 8.0, stack.y + 18.0, 14.0, Color::new(0.72, 0.80, 0.86, 1.0));
    let search_label = if app.sheet_library_search_focused { "SEARCH ACTIVE" } else { "Ctrl+F search" };
    let query_label = if app.sheet_library_search.is_empty() { "" } else { &app.sheet_library_search };
    let prompt = format!("{} | {} / {} | {} {}", search_label, app.sheet_library_visible.len(), app.sheet_library.len(), query_label,
        if app.sheet_library_search_focused { "_" } else { "" });
    draw_text(&prompt, stack.x + 8.0, stack.y + 38.0, 13.0, Color::new(0.62, 0.79, 0.86, 1.0));
    if draw_button(Rect::new(stack.x + stack.w - 67.0, stack.y + 25.0, 60.0, 20.0),
        if app.sheet_library_search.is_empty() { "Find" } else { "Reset" }, false) {
        if app.sheet_library_search.is_empty() {
            app.sheet_library_search_focused = true;
        } else {
            app.sheet_library_search.clear();
            app.rebuild_sheet_library_visibility();
            app.sheet_library_search_focused = false;
        }
    }

    // Two rows of genuine group filters replace the unrelated nine category
    // tabs in the application chrome. Filtering NEVER toggles a sheet OFF.
    let filter_width = (stack.w - 16.0) / 6.0;
    for filter_index in 0..=SourceGroup::ALL.len() {
        let group = if filter_index == 0 { None } else { Some(SourceGroup::ALL[filter_index - 1]) };
        let active = app.sheet_library_group == group;
        let label = group.map_or("ALL", SourceGroup::label);
        let column = filter_index % 6;
        let row = filter_index / 6;
        if draw_button(Rect::new(stack.x + 8.0 + filter_width * column as f32,
            stack.y + 49.0 + 23.0 * row as f32, filter_width - 3.0, 20.0), label, active) {
            app.sheet_library_group = group;
            app.rebuild_sheet_library_visibility();
            app.status = format!("Summer source group: {label}. Filtering does not alter activated scene sheets.");
        }
    }
    draw_text("Select = inspect | ON/OFF = activate | ? draft | L learned | check approved",
        stack.x + 8.0, stack.y + 96.0, 11.0, Color::new(0.63, 0.74, 0.81, 1.0));
    let clip_y = stack.y + SHEET_LIST_TOP;
    // Virtualize large ElizaWy libraries: do not walk tens of thousands of
    // character sheets on every rendered frame just to skip offscreen cards.
    let first_visible = ((-app.sheet_library_scroll / SHEET_CARD_H).ceil().max(0.0) as usize)
        .min(app.sheet_library_visible.len());
    let mut row_y = clip_y + app.sheet_library_scroll + first_visible as f32 * SHEET_CARD_H;
    let active_key = app.atlas.as_ref().map(|atlas| normalize_path_key(&atlas.path));
    for &index in app.sheet_library_visible.iter().skip(first_visible) {
        let card = &app.sheet_library[index];
        if row_y + SHEET_CARD_H > stack.y + stack.h - 4.0 { break; }
        let active = active_key.as_deref() == Some(normalize_path_key(&card.path).as_str());
        let enabled = app.source_is_activated(&MapperApp::asset_id(&card.path));
        let row = Rect::new(stack.x + 6.0, row_y, stack.w - 12.0, SHEET_CARD_H - 4.0);
        let fill = if active { Color::new(0.08, 0.18, 0.25, 1.0) } else { Color::new(0.040, 0.050, 0.066, 1.0) };
        draw_rectangle(row.x, row.y, row.w, row.h, fill);
        draw_rectangle_lines(row.x, row.y, row.w, row.h, 1.0, if active { Color::new(0.20, 0.58, 0.72, 1.0) } else { Color::new(0.12, 0.17, 0.22, 1.0) });
        if card.status.is_good() {
            draw_rectangle(row.x + 1.0, row.y + 2.0, 3.0, row.h - 4.0, Color::new(0.16, 0.75, 0.34, 0.95));
        }
        draw_text(card.status.label(), row.x + 8.0, row.y + 20.0, 17.0, if card.status.is_good() { Color::new(0.44, 0.92, 0.58, 1.0) } else { Color::new(0.80, 0.73, 0.46, 1.0) });
        let truncated_name: String = card.display_name.chars().take(27).collect();
        draw_text(&truncated_name, row.x + 34.0, row.y + 14.0, 13.0, Color::new(0.88, 0.91, 0.94, 1.0));
        let folder: String = card.path.parent()
            .and_then(|path| path.file_name())
            .and_then(|name| name.to_str())
            .unwrap_or("source")
            .chars().take(13).collect();
        let progress = if card.mapped_tile_count == 0 {
            format!("{folder} | no roles | {} exact px", card.source_address_count)
        } else {
            format!("{folder} | {:.0}% mapped | {} exact px", card.coverage_percent, card.source_address_count)
        };
        draw_text(&progress, row.x + 34.0, row.y + 28.0, 11.0, Color::new(0.55, 0.64, 0.72, 1.0));
        draw_rectangle(row.x + row.w - 63.0, row.y + 3.0, 58.0, row.h - 6.0, if enabled { Color::new(0.11, 0.39, 0.27, 1.0) } else { Color::new(0.16, 0.19, 0.23, 1.0) });
        draw_text(if enabled { "ON" } else { "OFF" }, row.x + row.w - 48.0, row.y + 21.0, 13.0, if enabled { Color::new(0.60, 0.98, 0.70, 1.0) } else { Color::new(0.68, 0.75, 0.81, 1.0) });
        row_y += SHEET_CARD_H;
    }
    if app.sheet_library_visible.is_empty() {
        draw_text(if app.sheet_library.is_empty() { "NO ORIGINAL FILES FOUND - check source root" } else { "No sheets in group. Select ALL or reset search." },
            stack.x + 10.0, clip_y + 22.0, 13.0, Color::new(0.92, 0.66, 0.43, 1.0));
        if app.sheet_library.is_empty() {
            draw_wrapped_line(&app.library_notice, stack.x + 10.0, clip_y + 42.0,
                62, 12.0, Color::new(0.86, 0.71, 0.54, 1.0));
        }
    }

    let preview = source_preview_rect(source_rect, app.atlas_focus);
    draw_rectangle(preview.x, preview.y, preview.w, preview.h, Color::new(0.016, 0.021, 0.029, 1.0));
    draw_rectangle_lines(preview.x, preview.y, preview.w, preview.h, 1.0, Color::new(0.13, 0.18, 0.24, 1.0));
    if let Some(atlas) = &app.atlas {
        let file = atlas.path.file_name().and_then(|name| name.to_str()).unwrap_or("sheet");
        let summary = app.mapping_summary_for_sheet_path(&atlas.path, app.category);
        let badge = match summary.status {
            SourceSheetStatus::Unmapped => "UNMAPPED",
            SourceSheetStatus::Draft => "DRAFT",
            SourceSheetStatus::Mapped => "MAPPED",
            SourceSheetStatus::Validated => "VALIDATED",
            SourceSheetStatus::Published => "PUBLISHED",
            SourceSheetStatus::NeedsReview => "REVIEW",
        };
        draw_status_pill(Rect::new(preview.x + preview.w - 104.0, preview.y + 8.0, 90.0, 21.0), badge, summary.status.is_good());
        draw_text(&format!("{}  |  {}x{}  |  {} mapped cells · {:.1}%", file, atlas.width, atlas.height, summary.mapped_tile_count, summary.coverage_percent), preview.x + 14.0, preview.y + 24.0, 16.0, Color::new(0.78, 0.84, 0.89, 1.0));
        let draw_pos = vec2(preview.x, preview.y) + app.source_pan;
        draw_texture_ex(
            &atlas.texture,
            draw_pos.x,
            draw_pos.y,
            WHITE,
            DrawTextureParams {
                dest_size: Some(vec2(atlas.width as f32 * app.source_zoom, atlas.height as f32 * app.source_zoom)),
                ..Default::default()
            },
        );
        draw_grid(preview, app.source_pan, app.source_zoom, Color::new(1.0, 1.0, 1.0, 0.13));
        draw_mapped_tile_badges(app, preview);
        if let Some(tile) = app.selected_tile {
            let rect = Rect::new(
                preview.x + app.source_pan.x + tile.tile_x as f32 * TILE_SIZE as f32 * app.source_zoom,
                preview.y + app.source_pan.y + tile.tile_y as f32 * TILE_SIZE as f32 * app.source_zoom,
                TILE_SIZE as f32 * app.source_zoom,
                TILE_SIZE as f32 * app.source_zoom,
            );
            draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 3.0, Color::new(1.0, 0.82, 0.20, 1.0));
        }
    } else {
        draw_text("No atlas loaded.", preview.x + 18.0, preview.y + 52.0, 22.0, Color::new(0.75, 0.80, 0.84, 1.0));
        if app.sheet_library.is_empty() {
            draw_wrapped_line(&app.library_notice, preview.x + 18.0, preview.y + 82.0,
                48, 15.0, Color::new(0.92, 0.69, 0.48, 1.0));
        } else {
            draw_text("Select a sheet above; other selected sheets stay in the scene.", preview.x + 18.0, preview.y + 82.0, 15.0, Color::new(0.55, 0.63, 0.70, 1.0));
        }
    }
}


fn source_sheet_stack_rect(panel: Rect, atlas_focus: bool) -> Rect {
    let usable_h = (panel.h - 205.0).max(130.0);
    let fraction = if atlas_focus { 0.28 } else { 0.62 };
    Rect::new(panel.x + 10.0, panel.y + 58.0, panel.w - 20.0,
        (panel.h * fraction).max(SOURCE_SHEET_STACK_MIN_H).min(usable_h))
}

fn source_preview_rect(panel: Rect, atlas_focus: bool) -> Rect {
    let stack = source_sheet_stack_rect(panel, atlas_focus);
    let y = stack.y + stack.h + SOURCE_PREVIEW_TOP_PAD;
    Rect::new(panel.x + 10.0, y, panel.w - 20.0, (panel.y + panel.h - y - 10.0).max(120.0))
}

fn draw_mapped_tile_badges(app: &MapperApp, preview: Rect) {
    let mut mapped = app.persisted_mapped_tiles_for_current_sheet();
    let active_id = app.atlas.as_ref().map(|atlas| atlas.id.as_str());
    for piece in &app.pieces {
        if active_id == Some(piece.source_asset_id.as_str()) {
            let key = (piece.source_tile_x, piece.source_tile_y);
            if !mapped.contains_key(&key) || app.dirty {
                mapped.insert(key, MAPPED_TILE_STATUS_DRAFT.to_string());
            }
        }
    }
    if mapped.is_empty() { return; }
    for ((tile_x, tile_y), status) in mapped {
        let x = preview.x + app.source_pan.x + tile_x as f32 * TILE_SIZE as f32 * app.source_zoom;
        let y = preview.y + app.source_pan.y + tile_y as f32 * TILE_SIZE as f32 * app.source_zoom;
        let tile_screen = TILE_SIZE as f32 * app.source_zoom;
        if x + tile_screen < preview.x || y + tile_screen < preview.y || x > preview.x + preview.w || y > preview.y + preview.h {
            continue;
        }
        let size = (10.0 * app.source_zoom).clamp(8.0, 16.0);
        let (label, color) = if status == MAPPED_TILE_STATUS_APPROVED {
            ("✓", Color::new(0.06, 0.60, 0.28, 0.96))
        } else if status == MAPPED_TILE_STATUS_LEARNED {
            ("L", Color::new(0.18, 0.42, 0.76, 0.96))
        } else {
            ("?", Color::new(0.65, 0.43, 0.12, 0.94))
        };
        draw_rectangle(x + 2.0, y + 2.0, size, size, color);
        draw_text(label, x + 3.0, y + size + 1.0, size + 2.0, Color::new(0.86, 1.0, 0.88, 1.0));
    }
}

fn is_supported_image_path(path: &Path) -> bool {
    path.extension()
        .and_then(|ext| ext.to_str())
        .map(|ext| matches!(ext.to_ascii_lowercase().as_str(), "png" | "bmp" | "jpg" | "jpeg" | "webp"))
        .unwrap_or(false)
}

fn default_asset_sheet_scan_roots(root: &Path) -> Vec<PathBuf> {
    vec![
        root.join("assets/source/licensed/lpc_revised/Terrain"),
        root.join("assets/source/licensed/lpc_revised/Terrain Objects"),
        root.join("assets/source/licensed/lpc_revised/seasonal_split"),
        root.join("assets/source/licensed/lpc_revised/Objects"),
        root.join("assets/source/licensed/lpc_revised/Structure"),
        root.join("assets/source/licensed/lpc_revised/Structures"),
        root.join("assets/source/licensed/lpc_revised/Equipment"),
        root.join("assets/source/licensed/lpc_revised/FX"),
        root.join("assets/source/licensed/lpc_revised/UI"),
        root.join("content/assets/oga_lpc/source"),
        root.join("content/assets/lpc/source"),
        root.join("assets/generated/worldgen_v0_1/terrain"),
    ]
}

// A standalone executable can be launched outside the repository. Resolve the
// same project root used by the PCC before scanning immutable source sheets.
fn discover_havenwild_root() -> Option<PathBuf> {
    let mut starts = Vec::new();
    if let Some(value) = env::var_os("HAVENWILD_ROOT") { starts.push(PathBuf::from(value)); }
    if let Ok(path) = env::current_dir() { starts.push(path); }
    if let Ok(path) = env::current_exe() { starts.push(path); }
    for start in starts {
        for candidate in start.ancestors().take(12) {
            if candidate.join("Cargo.toml").is_file()
                && candidate.join("apps/haven_atlas_mapper_lite/Cargo.toml").is_file() {
                return Some(candidate.to_path_buf());
            }
        }
    }
    None
}

fn declared_external_asset_roots(root: &Path) -> Vec<PathBuf> {
    let mut roots = Vec::new();
    for rel in [EXTERNAL_ASSET_ROOTS_REL, LOCAL_EXTERNAL_ASSET_ROOTS_REL] {
        let path = root.join(rel);
        let Ok(text) = fs::read_to_string(path) else { continue; };
        let Ok(value) = serde_json::from_str::<serde_json::Value>(&text) else { continue; };
        collect_json_root_paths(root, &value, &mut roots);
    }
    roots
}

fn collect_json_root_paths(root: &Path, value: &serde_json::Value, out: &mut Vec<PathBuf>) {
    if let Some(path) = value.get("path").and_then(|path| path.as_str()) {
        out.push(resolve_declared_path(root, path));
    }
    if let Some(items) = value.get("roots").and_then(|items| items.as_array()) {
        for item in items {
            collect_json_root_paths(root, item, out);
        }
    }
    if let Some(items) = value.as_array() {
        for item in items {
            collect_json_root_paths(root, item, out);
        }
    }
}

fn resolve_declared_path(root: &Path, value: &str) -> PathBuf {
    let normalized = value.replace('\\', "/");
    if let Some(stripped) = normalized.strip_prefix("~/") {
        if let Some(home) = env::var_os("USERPROFILE").or_else(|| env::var_os("HOME")) {
            return PathBuf::from(home).join(stripped);
        }
    }
    let candidate = PathBuf::from(&normalized);
    if candidate.is_absolute() { candidate } else { root.join(candidate) }
}

fn normalize_path_key(path: &Path) -> String {
    path.to_string_lossy().replace('\\', "/").to_ascii_lowercase()
}

fn infer_sheet_family(root: &Path, path: &Path, category: AssetCategory) -> String {
    let rel = path.strip_prefix(root).unwrap_or(path).to_string_lossy().replace('\\', "/").to_ascii_lowercase();
    if rel.contains("lpc-terrains-v7") { return "lpc_v7_compat".to_string(); }
    if rel.contains("worldgen_v0_1/terrain") { return "generated_runtime".to_string(); }
    if rel.contains("cliffs_grass_top") { return "lpc_cliff_ramps".to_string(); }
    if rel.contains("lpc_revised/terrain") { return "lpc_revised_seasonal".to_string(); }
    match category {
        AssetCategory::Terrain => "terrain".to_string(),
        AssetCategory::Cliff => "cliff".to_string(),
        AssetCategory::Structure => "structure".to_string(),
        AssetCategory::House => "building".to_string(),
        AssetCategory::Object => "object".to_string(),
        AssetCategory::Character => "character".to_string(),
        AssetCategory::Equipment => "equipment".to_string(),
        AssetCategory::Fx => "fx".to_string(),
        AssetCategory::Ui => "ui".to_string(),
    }
}

fn canvas_edit_rect(panel: Rect) -> Rect {
    // Toolbar occupies top 72px; opaque controls panel occupies bottom 110px.
    // Never paint behind a button or through instructional chrome.
    Rect::new(panel.x + 2.0, panel.y + 74.0, (panel.w - 4.0).max(0.0), (panel.h - 184.0).max(0.0))
}

fn draw_height_overlay(app: &MapperApp, canvas_rect: Rect) {
    for cell in &app.heightmap {
        let x = canvas_rect.x + app.canvas_pan.x + cell.x as f32 * TILE_SIZE as f32 * app.canvas_zoom;
        let y = canvas_rect.y + app.canvas_pan.y + cell.y as f32 * TILE_SIZE as f32 * app.canvas_zoom;
        let size = TILE_SIZE as f32 * app.canvas_zoom;
        if x + size < canvas_rect.x || y + size < canvas_rect.y + 38.0 || x > canvas_rect.x + canvas_rect.w || y > canvas_rect.y + canvas_rect.h { continue; }
        let alpha = (0.12 + (cell.elevation as f32 / 30.0) * 0.28).min(0.42);
        draw_rectangle(x, y, size, size, Color::new(0.95, 0.72, 0.18, alpha));
        if cell.water_surface.is_some() { draw_rectangle(x + 2.0, y + 2.0, size - 4.0, size - 4.0, Color::new(0.10, 0.55, 0.92, 0.30)); }
        if app.canvas_zoom >= 1.25 {
            draw_text(&format!("+{}", cell.elevation), x + 4.0, y + 15.0, 13.0, Color::new(0.98, 0.98, 0.92, 0.95));
        }
    }
}

fn draw_canvas_panel(app: &mut MapperApp, canvas_rect: Rect) {
    draw_panel(canvas_rect, "RIGHT | Summer Example Scene", "Source-exact draft; edit and save before learning");

    draw_grid(canvas_rect, app.canvas_pan, app.canvas_zoom, Color::new(1.0, 1.0, 1.0, 0.10));
    draw_height_overlay(app, canvas_rect);
    if let Some(atlas) = &app.atlas {
        let mut draw_order: Vec<usize> = (0..app.pieces.len()).collect();
        draw_order.sort_by_key(|index| app.pieces[*index].layer);
        for index in draw_order {
            let piece = &app.pieces[index];
            let Some(texture) = app.texture_for_piece(piece) else { continue; };
            let dest = app.canvas_piece_rect(canvas_rect, piece);
            let source = Rect::new(piece.source_rect[0] as f32, piece.source_rect[1] as f32, TILE_SIZE as f32, TILE_SIZE as f32);
            let center = vec2(dest.x + dest.w * 0.5, dest.y + dest.h * 0.5);
            draw_texture_ex(
                texture,
                dest.x,
                dest.y,
                WHITE,
                DrawTextureParams {
                    dest_size: Some(vec2(dest.w, dest.h)),
                    source: Some(source),
                    rotation: (piece.rotation_degrees as f32).to_radians(),
                    flip_x: piece.flip_x,
                    flip_y: piece.flip_y,
                    pivot: Some(center),
                    ..Default::default()
                },
            );
            if let Some(cell) = app.heightmap.iter().find(|cell|
                cell.x == piece.canvas_grid_x && cell.y == piece.canvas_grid_y) {
                draw_text(&format!("+{}{}", cell.elevation,
                    if cell.water_surface.is_some() { " W" } else { "" }),
                    dest.x + 2.0, dest.y + 14.0, 13.0, YELLOW);
            }
            if app.selected_piece == Some(index) {
                draw_rectangle_lines(dest.x, dest.y, dest.w, dest.h, 3.0, Color::new(0.30, 0.72, 0.94, 1.0));
                let label = format!("id:{} layer:{} rot:{}", piece.id, piece.layer, piece.rotation_degrees);
                draw_text(&label, dest.x + 2.0, dest.y - 4.0, 14.0, Color::new(0.40, 0.80, 1.0, 1.0));
            }
        }
        if let DragState::SourceTile(tile) = app.drag {
            let mouse = mouse_position_local();
            let source = Rect::new((tile.tile_x * TILE_SIZE) as f32, (tile.tile_y * TILE_SIZE) as f32, TILE_SIZE as f32, TILE_SIZE as f32);
            draw_texture_ex(
                &atlas.texture,
                mouse.x - 16.0,
                mouse.y - 16.0,
                Color::new(1.0, 1.0, 1.0, 0.74),
                DrawTextureParams { dest_size: Some(vec2(48.0, 48.0)), source: Some(source), ..Default::default() },
            );
            draw_rectangle_lines(mouse.x - 16.0, mouse.y - 16.0, 48.0, 48.0, 2.0, Color::new(1.0, 0.85, 0.22, 0.9));
        }
    }

    draw_rectangle(canvas_rect.x, canvas_rect.y, canvas_rect.w, 74.0, Color::new(0.030, 0.039, 0.052, 1.0));
    draw_text("RIGHT | ElizaWy Summer Scene Workspace", canvas_rect.x + 12.0, canvas_rect.y + 24.0, 17.0, WHITE);
    draw_text("EDITABLE: scene + height/water  |  collision/traversal: audit only",
        canvas_rect.x + 12.0, canvas_rect.y + 38.0, 12.0, Color::new(0.64, 0.76, 0.83, 1.0));
    let ty = canvas_rect.y + 42.0;
    if draw_button(Rect::new(canvas_rect.x + 12.0, ty, 66.0, 22.0), "1 Select", app.author_tool == AuthorTool::Select) { app.author_tool = AuthorTool::Select; }
    if draw_button(Rect::new(canvas_rect.x + 84.0, ty, 72.0, 22.0), "2 Height", app.author_tool == AuthorTool::Elevation) { app.author_tool = AuthorTool::Elevation; }
    if draw_button(Rect::new(canvas_rect.x + 162.0, ty, 70.0, 22.0), "3 Water", app.author_tool == AuthorTool::Water) { app.author_tool = AuthorTool::Water; }
    if draw_button(Rect::new(canvas_rect.x + 238.0, ty, 34.0, 22.0), "-", false) { app.paint_elevation = app.paint_elevation.saturating_sub(1); }
    draw_text(&format!("+{}", app.paint_elevation), canvas_rect.x + 280.0, ty + 17.0, 15.0, Color::new(0.88, 0.91, 0.94, 1.0));
    if draw_button(Rect::new(canvas_rect.x + 310.0, ty, 34.0, 22.0), "+", false) { app.paint_elevation = (app.paint_elevation + 1).min(30); }
    if draw_button(Rect::new(canvas_rect.x + 358.0, ty, 125.0, 22.0), "Erase selected", false) { app.remove_selected_piece(); }
    draw_text(&format!("zoom {:.0}%", app.canvas_zoom * 100.0), canvas_rect.x + canvas_rect.w - 216.0, canvas_rect.y + 24.0, 15.0, Color::new(0.64, 0.72, 0.80, 1.0));
    if draw_button(Rect::new(canvas_rect.x + canvas_rect.w - 148.0, canvas_rect.y + 8.0, 58.0, 23.0), "2x", false) { app.reset_canvas_view(); }
    if draw_button(Rect::new(canvas_rect.x + canvas_rect.w - 82.0, canvas_rect.y + 8.0, 66.0, 23.0), "Fit", false) { app.fit_canvas_to_pieces(canvas_rect); }


    let info_y = canvas_rect.y + canvas_rect.h - 36.0;
    draw_rectangle(canvas_rect.x + 10.0, info_y, canvas_rect.w - 20.0, 24.0, Color::new(0.018, 0.023, 0.031, 0.90));
    draw_text("Select + Delete / right-click erase / Ctrl+Z undo / Space pan / wheel zoom / Ctrl+S save",
        canvas_rect.x + 15.0, info_y + 17.0, 13.0, Color::new(0.68, 0.75, 0.82, 1.0));
}

fn draw_inspector(app: &mut MapperApp, inspector_rect: Rect) {
    // An optional, opaque overlay; never a permanent third column.
    draw_panel(inspector_rect, "Mapping details", "Tile roles / mapping evidence / candidate only");
    let mut y = inspector_rect.y + 44.0;
    draw_status_pill(Rect::new(inspector_rect.x + 14.0, y, 128.0, 24.0), app.mapping_stage.label(), app.mapping_stage.is_green());
    draw_status_pill(Rect::new(inspector_rect.x + 150.0, y, 92.0, 24.0), app.category.label(), true);
    y += 44.0;
    let file = app.atlas.as_ref()
        .and_then(|atlas| atlas.path.file_name().and_then(|name| name.to_str()))
        .unwrap_or("no sheet loaded");
    draw_text("Current sheet", inspector_rect.x + 14.0, y, 16.0, Color::new(0.60, 0.70, 0.78, 1.0));
    y += 22.0;
    y = draw_wrapped_line(file, inspector_rect.x + 14.0, y, 30, 16.0, Color::new(0.88, 0.91, 0.94, 1.0));
    y += 8.0;

    if let Some(atlas) = &app.atlas {
        let summary = app.mapping_summary_for_sheet_path(&atlas.path, app.category);
        draw_text("Coverage", inspector_rect.x + 14.0, y, 16.0, Color::new(0.60, 0.70, 0.78, 1.0));
        y += 22.0;
        draw_text(&format!("{} mapped source cells · {:.1}%", summary.mapped_tile_count, summary.coverage_percent), inspector_rect.x + 14.0, y, 16.0, Color::new(0.82, 0.90, 0.86, 1.0));
        y += 20.0;
        draw_text("Amber ? = draft, blue L = learned, green check = explicitly approved cell only.", inspector_rect.x + 14.0, y, 13.0, Color::new(0.60, 0.69, 0.74, 1.0));
        y += 24.0;
        let profile = source_sheet_profile_id(&atlas.path, app.category);
        draw_text("Source profile", inspector_rect.x + 14.0, y, 16.0, Color::new(0.60, 0.70, 0.78, 1.0));
        y += 20.0;
        y = draw_wrapped_line(&profile, inspector_rect.x + 14.0, y, 31, 14.0, Color::new(0.78, 0.85, 0.88, 1.0));
        y += 8.0;
    }

    draw_text("WORKFLOW: Draft > Save > Learn > Stage > Audit", inspector_rect.x + 14.0, y, 12.0, Color::new(0.68, 0.84, 0.90, 1.0));
    y += 18.0;
    draw_text("Use the top toolbar for all scene actions.", inspector_rect.x + 14.0, y, 12.0, Color::new(0.77, 0.83, 0.88, 1.0));
    y += 18.0;
    draw_text("Recipe-driven reroll is NOT implemented.", inspector_rect.x + 14.0, y, 12.0, Color::new(0.95, 0.73, 0.44, 1.0));
    y += 25.0;

    if let Some(index) = app.selected_piece {
        if let Some(piece) = app.pieces.get(index) {
            draw_text("Selected tile role", inspector_rect.x + 14.0, y, 16.0, Color::new(0.60, 0.70, 0.78, 1.0));
            y += 22.0;
            let role = piece.semantic_role.clone();
            y = draw_wrapped_line(&role, inspector_rect.x + 14.0, y, 31, 15.0, Color::new(0.88, 0.91, 0.94, 1.0));
            y += 4.0;
        }
        for preset in app.category_role_presets().into_iter().take(6) {
            if y > inspector_rect.y + inspector_rect.h - 190.0 { break; }
            if draw_button(Rect::new(inspector_rect.x + 14.0, y, inspector_rect.w - 28.0, 24.0), preset, false) {
                app.assign_selected_semantic(preset);
            }
            y += 29.0;
        }
        y += 14.0;
    }

    if app.category == AssetCategory::Object {
        draw_text("Furniture: map whole objects and views,", inspector_rect.x + 14.0, y, 13.0, Color::new(0.75, 0.85, 0.91, 1.0));
        draw_text("not each 32px cell as terrain.", inspector_rect.x + 14.0, y + 18.0, 13.0, Color::new(0.75, 0.85, 0.91, 1.0));
    }

    let bottom_y = inspector_rect.y + inspector_rect.h - 96.0;
    draw_rectangle(inspector_rect.x + 12.0, bottom_y, inspector_rect.w - 24.0, 78.0, app.category.color());
    draw_rectangle(inspector_rect.x + 14.0, bottom_y + 2.0, inspector_rect.w - 28.0, 74.0, Color::new(0.025, 0.030, 0.038, 0.78));
    draw_text("Mapped-sheet meaning", inspector_rect.x + 20.0, bottom_y + 25.0, 16.0, Color::new(0.92, 0.95, 0.96, 1.0));
    draw_text("Green check = approved cell only", inspector_rect.x + 20.0, bottom_y + 49.0, 14.0, Color::new(0.74, 0.82, 0.84, 1.0));
    draw_text("Not runtime-published yet", inspector_rect.x + 20.0, bottom_y + 69.0, 15.0, Color::new(0.74, 0.82, 0.84, 1.0));
}

fn draw_app(app: &mut MapperApp, source_rect: Rect, canvas_rect: Rect, inspector_rect: Rect) {
    clear_background(Color::new(0.020, 0.026, 0.034, 1.0));
    draw_top_bar(app);
    draw_source_panel(app, source_rect);
    let divider_x = source_rect.x + source_rect.w;
    draw_rectangle(divider_x, source_rect.y, GAP, source_rect.h, Color::new(0.08, 0.12, 0.16, 1.0));
    draw_line(divider_x + GAP * 0.5, source_rect.y + 8.0, divider_x + GAP * 0.5,
        source_rect.y + source_rect.h - 8.0, 2.0, Color::new(0.26, 0.48, 0.59, 1.0));
    draw_canvas_panel(app, canvas_rect);
    if app.show_inspector { draw_inspector(app, inspector_rect); }

    draw_rectangle(0.0, screen_height() - STATUS_H, screen_width(), STATUS_H, Color::new(0.030, 0.038, 0.050, 1.0));
    draw_line(0.0, screen_height() - STATUS_H, screen_width(), screen_height() - STATUS_H, 1.0, Color::new(0.13, 0.18, 0.23, 1.0));
    let project_label = app.project_path.as_ref()
        .and_then(|path| path.file_name().and_then(|name| name.to_str()))
        .unwrap_or("unsaved project");
    draw_text(
        &format!("{} | {} | {} +{} | tiles {} | elevations {} | sheets {} | {}", app.status, app.mapping_stage.label(), app.author_tool.label(), app.paint_elevation, app.pieces.len(), app.heightmap.len(), app.source_stack.len() + usize::from(app.atlas.is_some()), project_label),
        12.0,
        screen_height() - 10.0,
        16.0,
        Color::new(0.86, 0.90, 0.93, 1.0),
    );
}

fn window_conf() -> Conf {
    Conf {
        window_title: "Havenwild ElizaWy Mapping Workspace".to_string(),
        window_width: 1600,
        window_height: 940,
        high_dpi: true,
        ..Default::default()
    }
}

#[macroquad::main(window_conf)]
async fn main() {
    if let Some(root) = discover_havenwild_root() {
        if let Err(error) = env::set_current_dir(&root) {
            eprintln!("B48R23 mapper cannot set Havenwild root {}: {error}", root.display());
        } else {
            println!("B48R23 mapper source root: {}", root.display());
        }
    } else {
        eprintln!("B48R23 mapper cannot find Havenwild root from cwd/executable/HAVENWILD_ROOT");
    }
    let mut app = MapperApp::default();
    app.refresh_sheet_library();
    if let Some(path) = env::args().nth(1) {
        let path = PathBuf::from(path);
        if path.extension().and_then(|ext| ext.to_str()).map(|ext| ext.eq_ignore_ascii_case("json")).unwrap_or(false) {
            app.load_project(&path);
        } else {
            app.load_atlas(path);
        }
    } else {
        // Resume an actual saved authoring project if present. The B48R7 fixture
        // describes topology but is NOT an editable sprite-placement project;
        // never silently load the rejected B48R10 assembly as a starter.
        if let Ok(root) = env::current_dir() {
            let demo = root.join("artifacts/asset-intake/atlas-mapper/projects/elizawy_summer_master.mapper.json");
            if demo.is_file() { app.load_project(&demo); }
        }
    }
    loop {
        let width = screen_width();
        let height = screen_height();
        let body_top = TOP_BAR_H + GAP;
        let body_h = height - TOP_BAR_H - STATUS_H - GAP * 2.0;
        // Two equal inspection surfaces by default; drag the central divider
        // between 40/60 and 60/40 without introducing a permanent third column.
        let available = (width - GAP * 3.0).max(500.0);
        let source_w = available * app.pane_ratio;
        let canvas_w = available - source_w;
        let source_rect = Rect::new(GAP, body_top, source_w, body_h);
        let canvas_rect = Rect::new(source_rect.x + source_w + GAP, body_top, canvas_w, body_h);
        let inspector_w = INSPECTOR_W.min((canvas_w - 24.0).max(210.0));
        let inspector_rect = Rect::new(canvas_rect.x + canvas_rect.w - inspector_w - 8.0,
            canvas_rect.y + 78.0, inspector_w, (canvas_rect.h - 122.0).max(200.0));
        app.handle_input(source_rect, canvas_rect, inspector_rect);
        draw_app(&mut app, source_rect, canvas_rect, inspector_rect);
        next_frame().await;
    }
}
