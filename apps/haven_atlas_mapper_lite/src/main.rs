use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use macroquad::prelude::*;
use rfd::FileDialog;
use serde::{Deserialize, Serialize};

const TILE_SIZE: i32 = 32;
const TOP_BAR_H: f32 = 82.0;
const STATUS_H: f32 = 32.0;
const GAP: f32 = 12.0;
const INSPECTOR_W: f32 = 292.0;
const MIN_SOURCE_ZOOM: f32 = 0.50;
const MAX_SOURCE_ZOOM: f32 = 6.00;
const MIN_CANVAS_ZOOM: f32 = 1.00;
const MAX_CANVAS_ZOOM: f32 = 4.00;
const DEFAULT_CANVAS_ZOOM: f32 = 2.00;
const ZOOM_STEP: f32 = 1.07;
const PROJECT_SCHEMA: &str = "havenwild.atlas_mapper_project.v0_3";
const LEGACY_PROJECT_SCHEMA: &str = "havenwild.atlas_mapper_project.v0_1";
const LEGACY_PROJECT_SCHEMA_V2: &str = "havenwild.atlas_mapper_project.v0_2";
const HANDOFF_SCHEMA: &str = "havenwild.atlas_assembly_handoff.v0_4";
const MAPPED_SHEET_SCHEMA: &str = "havenwild.atlas_mapper_mapped_sheet.v0_1";

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
        if hint.contains("cliff") || hint.contains("ramp") || hint.contains("ledge") || hint.contains("elevation") {
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
    authoring_notes: Vec<String>,
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
    engine_notes: Vec<String>,
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
    piece_count: usize,
    lifecycle_stage: String,
    project_file: Option<String>,
    handoff_file: Option<String>,
    updated_unix_seconds: u64,
    asset_intake_notes: Vec<String>,
}

struct LoadedAtlas {
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

struct MapperApp {
    atlas: Option<LoadedAtlas>,
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
    last_mouse: Vec2,
    status: String,
    mapping_stage: MappingStage,
    auto_seed: u64,
    scene_generation_count: u32,
}

impl Default for MapperApp {
    fn default() -> Self {
        Self {
            atlas: None,
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
            source_pan: vec2(18.0, 48.0),
            source_zoom: 1.0,
            canvas_pan: vec2(56.0, 64.0),
            canvas_zoom: DEFAULT_CANVAS_ZOOM,
            is_panning_source: false,
            is_panning_canvas: false,
            last_mouse: Vec2::ZERO,
            status: "Load an atlas, map 32x32 cells as puzzle pieces, then save/export into the asset intake lane.".to_string(),
            mapping_stage: MappingStage::SourceOnly,
            auto_seed: 1,
            scene_generation_count: 0,
        }
    }
}

impl MapperApp {
    fn load_atlas(&mut self, path: PathBuf) {
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
                self.atlas = Some(LoadedAtlas { path: path.clone(), texture, width, height, cell_profiles });
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
            self.pieces.clear();
            self.next_piece_id = 1;
            self.project_path = None;
            self.last_handoff_path = None;
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
        if document.schema != PROJECT_SCHEMA && document.schema != LEGACY_PROJECT_SCHEMA && document.schema != LEGACY_PROJECT_SCHEMA_V2 {
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

        self.project_path = Some(path.to_path_buf());
        self.last_handoff_path = None;
        self.pieces = document.pieces;
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

        let atlas_path = PathBuf::from(&document.source_atlas_path);
        if atlas_path.exists() {
            self.load_atlas(atlas_path);
            if !self.pieces.is_empty() { self.mapping_stage = MappingStage::ProjectSaved; }
            self.status = format!("Loaded mapper project: {}", path.to_string_lossy());
        } else {
            self.atlas = None;
            self.status = format!("Loaded project, but atlas is missing: {}", document.source_atlas_path);
        }
    }

    fn export_handoff_dialog(&mut self) {
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
            engine_notes: vec![
                "The source atlas is immutable and was not modified.".to_string(),
                "Each piece maps one 32x32 source tile to an assembly grid cell.".to_string(),
                "This handoff is asset-intake evidence. Engine import must still add sockets, footprints, pixel collision masks, traversal, layer ownership, provenance, and runtime validation before publication.".to_string(),
            ],
        };
        match serde_json::to_string_pretty(&document) {
            Ok(text) => match fs::write(path, text) {
                Ok(()) => {
                    self.last_handoff_path = Some(path.to_path_buf());
                    self.mapping_stage = MappingStage::HandoffExported;
                    self.write_mapping_record(Some(path));
                    self.status = format!("Exported handoff and marked sheet mapped: {}", path.to_string_lossy());
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
            authoring_notes: vec![
                "Mapper project files are editable tool state, not runtime assets.".to_string(),
                "Source atlas pixels remain immutable; this file stores placement and transform metadata only.".to_string(),
                "Mapped sheets are recorded into the asset intake lane so the GUI can show mapped/unmapped state.".to_string(),
                format!("Scene generation passes recorded this session: {}", self.scene_generation_count),
            ],
        })
    }

    fn add_piece_from_tile(&mut self, tile: SourceTile, grid_x: i32, grid_y: i32) {
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
        };
        self.pieces.push(piece);
        self.selected_piece = Some(self.pieces.len() - 1);
        self.mapping_stage = MappingStage::DraftMapped;
        self.status = format!("Placed tile {},{} as {} piece.", tile.tile_x, tile.tile_y, self.category.label());
    }

    fn auto_map_sheet(&mut self) {
        let Some(atlas) = &self.atlas else {
            self.status = "Load a tile sheet before using Auto Scene.".to_string();
            return;
        };
        let cols = (atlas.width / TILE_SIZE).max(1);
        let rows = (atlas.height / TILE_SIZE).max(1);
        let file_hint = atlas.path.file_name().and_then(|name| name.to_str()).unwrap_or("sheet").to_string();
        let profiles = atlas.cell_profiles.clone();
        self.pieces.clear();
        self.selected_piece = None;
        self.next_piece_id = 1;
        self.canvas_zoom = DEFAULT_CANVAS_ZOOM;
        self.canvas_pan = vec2(76.0, 78.0);
        self.scene_generation_count = self.scene_generation_count.saturating_add(1);
        let mut seed = self.auto_seed
            ^ unix_seconds()
            ^ ((cols as u64) << 11)
            ^ ((rows as u64) << 3)
            ^ ((self.scene_generation_count as u64) << 23);

        let scene_label = match self.category {
            AssetCategory::Terrain => self.generate_terrain_scene(&profiles, cols, rows, &mut seed),
            AssetCategory::Cliff => self.generate_cliff_scene(&profiles, cols, rows, &mut seed),
            AssetCategory::Structure => self.generate_structure_scene(&profiles, cols, rows, &mut seed),
            AssetCategory::House => self.generate_house_scene(&profiles, cols, rows, &mut seed),
            AssetCategory::Object => self.generate_gallery_scene(&profiles, cols, rows, &mut seed, "object_review_scene"),
            AssetCategory::Character => self.generate_strip_scene(&profiles, cols, rows, &mut seed, "character_layer_strip"),
            AssetCategory::Equipment => self.generate_gallery_scene(&profiles, cols, rows, &mut seed, "equipment_review_scene"),
            AssetCategory::Fx => self.generate_strip_scene(&profiles, cols, rows, &mut seed, "fx_animation_strip"),
            AssetCategory::Ui => self.generate_gallery_scene(&profiles, cols, rows, &mut seed, "ui_icon_review_scene"),
        };

        self.selected_piece = None;
        self.mapping_stage = if self.pieces.is_empty() { MappingStage::SourceOnly } else { MappingStage::DraftMapped };
        self.status = format!(
            "Generated {scene_label} from {file_hint} as {} pass #{}. Correct it, then generate again or Save/Export for asset intake.",
            self.category.label(),
            self.scene_generation_count,
        );
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
        });
    }

    fn generated_tile(&self, profiles: &[SourceCellProfile], cols: i32, rows: i32, seed: &mut u64, roles: &[CellRole], ordinal: u64) -> SourceTile {
        choose_tile_from_profiles(profiles, cols, rows, seed, roles, ordinal)
    }

    fn generate_terrain_scene(&mut self, profiles: &[SourceCellProfile], cols: i32, rows: i32, seed: &mut u64) -> &'static str {
        for y in 0..5 {
            for x in 0..8 {
                let roles = if y >= 3 && x >= 3 && x <= 5 { &[CellRole::Water][..] } else { &[CellRole::Grass, CellRole::Sand, CellRole::Stone][..] };
                let semantic = if y >= 3 && x >= 3 && x <= 5 { "terrain.water.scene_channel" } else { "terrain.ground.scene_fill" };
                let tile = self.generated_tile(profiles, cols, rows, seed, roles, (x + y * 17) as u64);
                self.push_generated_piece(tile, x, y, semantic, y);
            }
        }
        "terrain scene sampler"
    }

    fn generate_cliff_scene(&mut self, profiles: &[SourceCellProfile], cols: i32, rows: i32, seed: &mut u64) -> &'static str {
        for x in 1..9 {
            let tile = self.generated_tile(profiles, cols, rows, seed, &[CellRole::Grass, CellRole::Sand], x as u64);
            self.push_generated_piece(tile, x, 0, "terrain.cliff.top_surface", 0);
        }
        for y in 1..4 {
            for x in 2..8 {
                let tile = self.generated_tile(profiles, cols, rows, seed, &[CellRole::Cliff, CellRole::Wood, CellRole::Stone], (x + y * 13) as u64);
                self.push_generated_piece(tile, x, y, "terrain.cliff.face_occluder", 10 + y);
            }
        }
        for x in 0..10 {
            let tile = self.generated_tile(profiles, cols, rows, seed, &[CellRole::Water, CellRole::Sand, CellRole::Grass], (x + 91) as u64);
            self.push_generated_piece(tile, x, 5, "terrain.water.bottom_pool", 2);
        }
        for (x, y, semantic) in [(1, 1, "terrain.cliff.left_shoulder"), (8, 1, "terrain.cliff.right_shoulder"), (4, 4, "terrain.cliff.debris_or_transition"), (5, 4, "terrain.cliff.debris_or_transition")] {
            let tile = self.generated_tile(profiles, cols, rows, seed, &[CellRole::Detail, CellRole::Cliff, CellRole::Grass], (x + y * 31) as u64);
            self.push_generated_piece(tile, x, y, semantic, 20 + y);
        }
        "cliff correction scene"
    }

    fn generate_structure_scene(&mut self, profiles: &[SourceCellProfile], cols: i32, rows: i32, seed: &mut u64) -> &'static str {
        for y in 1..5 {
            for x in 1..7 {
                let edge = x == 1 || x == 6 || y == 1 || y == 4;
                let roles = if edge { &[CellRole::Wood, CellRole::Stone, CellRole::Cliff][..] } else { &[CellRole::Sand, CellRole::Wood, CellRole::Stone][..] };
                let semantic = if edge { "structure.wall_or_edge" } else { "structure.floor_fill" };
                let tile = self.generated_tile(profiles, cols, rows, seed, roles, (x + y * 19) as u64);
                self.push_generated_piece(tile, x, y, semantic, if edge { 20 } else { 1 });
            }
        }
        "structure module scene"
    }

    fn generate_house_scene(&mut self, profiles: &[SourceCellProfile], cols: i32, rows: i32, seed: &mut u64) -> &'static str {
        for y in 0..6 {
            for x in 1..8 {
                let semantic = if y <= 1 { "building.roof_or_top" } else if y == 5 { "building.front_or_entry" } else { "building.wall_body" };
                let roles = if y <= 1 { &[CellRole::Wood, CellRole::Cliff, CellRole::Stone][..] } else { &[CellRole::Wood, CellRole::Stone, CellRole::Sand][..] };
                let tile = self.generated_tile(profiles, cols, rows, seed, roles, (x + y * 23) as u64);
                self.push_generated_piece(tile, x, y, semantic, 10 + y);
            }
        }
        "building correction scene"
    }

    fn generate_gallery_scene(&mut self, profiles: &[SourceCellProfile], cols: i32, rows: i32, seed: &mut u64, label: &'static str) -> &'static str {
        for y in 0..4 {
            for x in 0..6 {
                let tile = self.generated_tile(profiles, cols, rows, seed, &[CellRole::Detail, CellRole::Wood, CellRole::Stone, CellRole::Grass, CellRole::Cliff], (x + y * 29) as u64);
                self.push_generated_piece(tile, x * 2, y * 2, &format!("{}.candidate_{}", self.category.stable_key(), y * 6 + x), y);
            }
        }
        label
    }

    fn generate_strip_scene(&mut self, profiles: &[SourceCellProfile], cols: i32, rows: i32, seed: &mut u64, label: &'static str) -> &'static str {
        for y in 0..3 {
            for x in 0..8 {
                let tile = self.generated_tile(profiles, cols, rows, seed, &[CellRole::Detail, CellRole::Grass, CellRole::Wood, CellRole::Stone, CellRole::Cliff], (x + y * 37) as u64);
                self.push_generated_piece(tile, x, y * 2, &format!("{}.frame_row_{}", self.category.stable_key(), y), y);
            }
        }
        label
    }

    fn next_default_layer(&self) -> i32 {
        self.pieces.iter().map(|piece| piece.layer).max().unwrap_or(-1) + 1
    }

    fn selected_piece_mut(&mut self) -> Option<&mut AssemblyPiece> {
        self.selected_piece.and_then(|index| self.pieces.get_mut(index))
    }

    fn handle_shortcuts(&mut self) {
        let ctrl = is_key_down(KeyCode::LeftControl) || is_key_down(KeyCode::RightControl);
        let shift = is_key_down(KeyCode::LeftShift) || is_key_down(KeyCode::RightShift);
        if ctrl && is_key_pressed(KeyCode::O) {
            if shift { self.load_project_dialog(); } else { self.load_atlas_dialog(); }
        }
        if ctrl && is_key_pressed(KeyCode::S) { self.save_project_current_or_dialog(); }
        if ctrl && is_key_pressed(KeyCode::E) { self.export_handoff_dialog(); }
        if ctrl && is_key_pressed(KeyCode::G) { self.auto_map_sheet(); }
        if is_key_pressed(KeyCode::R) {
            if let Some(piece) = self.selected_piece_mut() {
                piece.rotation_degrees = (piece.rotation_degrees + 90) % 360;
            }
        }
        if is_key_pressed(KeyCode::H) {
            if let Some(piece) = self.selected_piece_mut() { piece.flip_x = !piece.flip_x; }
        }
        if is_key_pressed(KeyCode::V) {
            if let Some(piece) = self.selected_piece_mut() { piece.flip_y = !piece.flip_y; }
        }
        if is_key_pressed(KeyCode::Delete) || is_key_pressed(KeyCode::Backspace) {
            if let Some(index) = self.selected_piece.take() {
                if index < self.pieces.len() { self.pieces.remove(index); }
                self.mapping_stage = if self.pieces.is_empty() { MappingStage::SourceOnly } else { MappingStage::DraftMapped };
            }
        }
        if is_key_pressed(KeyCode::LeftBracket) {
            if let Some(piece) = self.selected_piece_mut() { piece.layer -= 1; }
        }
        if is_key_pressed(KeyCode::RightBracket) {
            if let Some(piece) = self.selected_piece_mut() { piece.layer += 1; }
        }
    }

    fn handle_input(&mut self, source_rect: Rect, canvas_rect: Rect) {
        self.handle_shortcuts();
        let mouse = mouse_position_local();
        let delta = mouse - self.last_mouse;
        let over_source = source_rect.contains(mouse);
        let over_canvas = canvas_rect.contains(mouse);
        let space_pan = is_key_down(KeyCode::Space);
        let (_wheel_x, wheel_y) = mouse_wheel();

        if wheel_y != 0.0 {
            let zoom_factor = if wheel_y > 0.0 { ZOOM_STEP } else { 1.0 / ZOOM_STEP };
            if over_source {
                self.source_zoom = (self.source_zoom * zoom_factor).clamp(MIN_SOURCE_ZOOM, MAX_SOURCE_ZOOM);
            } else if over_canvas {
                self.canvas_zoom = (self.canvas_zoom * zoom_factor).clamp(MIN_CANVAS_ZOOM, MAX_CANVAS_ZOOM);
            }
        }

        if is_mouse_button_pressed(MouseButton::Left) {
            self.is_panning_source = false;
            self.is_panning_canvas = false;
            self.drag_origin = None;
            if space_pan && over_source {
                self.is_panning_source = true;
            } else if space_pan && over_canvas {
                self.is_panning_canvas = true;
            } else if over_source {
                if let Some(tile) = self.source_tile_at(source_rect, mouse) {
                    self.selected_tile = Some(tile);
                    self.selected_piece = None;
                    self.drag = DragState::SourceTile(tile);
                }
            } else if over_canvas {
                if let Some(index) = self.hit_piece(canvas_rect, mouse) {
                    self.selected_piece = Some(index);
                    self.selected_tile = None;
                    if let Some(piece) = self.pieces.get(index) {
                        self.drag_origin = Some((index, piece.canvas_grid_x, piece.canvas_grid_y));
                    }
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
            } else if let DragState::ExistingPiece(index) = self.drag {
                if over_canvas {
                    if let Some((gx, gy)) = self.canvas_grid_at(canvas_rect, mouse) {
                        if let Some(piece) = self.pieces.get_mut(index) {
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
                    if over_canvas {
                        if let Some((gx, gy)) = self.canvas_grid_at(canvas_rect, mouse) {
                            self.add_piece_from_tile(tile, gx, gy);
                        }
                    } else {
                        self.status = "Drag canceled: release source tiles over the assembly canvas to place them.".to_string();
                    }
                }
                DragState::ExistingPiece(index) => {
                    if !over_canvas {
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
        }

        self.last_mouse = mouse;
    }

    fn source_tile_at(&self, panel: Rect, mouse: Vec2) -> Option<SourceTile> {
        let atlas = self.atlas.as_ref()?;
        if mouse.y < panel.y + 38.0 { return None; }
        let local = (mouse - vec2(panel.x, panel.y) - self.source_pan) / self.source_zoom;
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
        self.canvas_pan = vec2(56.0, 64.0);
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
            64.0 - min_y as f32 * TILE_SIZE as f32 * self.canvas_zoom,
        );
        self.status = "Canvas view fit to current assembly without dropping below 100% zoom.".to_string();
    }

    fn mapping_record_path(&self) -> Option<PathBuf> {
        let atlas = self.atlas.as_ref()?;
        let stem = atlas.path.file_stem().and_then(|stem| stem.to_str()).unwrap_or("atlas");
        let safe = sanitize_file_stem(stem);
        let file = format!("{}__{}.mapped-sheet.json", safe, self.category.stable_key());
        let root = env::current_dir().ok()?;
        Some(root.join("artifacts").join("asset-intake").join("atlas-mapper").join("mapped-sheets").join(file))
    }

    fn write_mapping_record(&mut self, handoff_path: Option<&Path>) {
        if self.atlas.is_none() || self.pieces.is_empty() { return; }
        let Some(path) = self.mapping_record_path() else { return; };
        let Some(atlas) = &self.atlas else { return; };
        let source_name = atlas.path.file_name().and_then(|name| name.to_str()).unwrap_or("atlas").to_string();
        let parent = path.parent().map(Path::to_path_buf);
        if let Some(parent) = parent {
            if let Err(error) = fs::create_dir_all(&parent) {
                self.status = format!("Mapping record folder failed: {error}");
                return;
            }
        }
        let record = MappedSheetRecord {
            schema: MAPPED_SHEET_SCHEMA.to_string(),
            tool: "haven_atlas_mapper_lite".to_string(),
            source_atlas_path: atlas.path.to_string_lossy().replace('\\', "/"),
            source_atlas_file_name: source_name,
            tile_size: TILE_SIZE,
            category: self.category.stable_key().to_string(),
            category_label: self.category.label().to_string(),
            assembly_name: self.assembly_name.clone(),
            piece_count: self.pieces.len(),
            lifecycle_stage: self.mapping_stage.label().to_string(),
            project_file: self.project_path.as_ref().map(|p| p.to_string_lossy().replace('\\', "/")),
            handoff_file: handoff_path
                .map(|p| p.to_string_lossy().replace('\\', "/"))
                .or_else(|| self.last_handoff_path.as_ref().map(|p| p.to_string_lossy().replace('\\', "/"))),
            updated_unix_seconds: unix_seconds(),
            asset_intake_notes: vec![
                "Green mapped state means the sheet has mapper metadata, not that it is published runtime content.".to_string(),
                "Promotion into PublishedWorldAssetMetadata still requires sockets, footprint, collision, traversal, provenance, and validation.".to_string(),
            ],
        };
        if let Ok(text) = serde_json::to_string_pretty(&record) {
            let _ = fs::write(path, text);
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

fn draw_top_bar(app: &mut MapperApp) {
    draw_rectangle(0.0, 0.0, screen_width(), TOP_BAR_H, Color::new(0.028, 0.035, 0.047, 1.0));
    draw_rectangle(0.0, 0.0, screen_width(), 4.0, Color::new(0.12, 0.32, 0.45, 1.0));
    draw_text("Havenwild Atlas Mapper Lite", 16.0, 30.0, 25.0, Color::new(0.94, 0.96, 0.98, 1.0));
    draw_text("asset intake sheet mapper | read-only source -> puzzle assembly -> mapped-sheet checkmark -> engine handoff", 18.0, 55.0, 15.0, Color::new(0.62, 0.70, 0.78, 1.0));

    let mut bx = 365.0;
    if draw_button(Rect::new(bx, 12.0, 84.0, 28.0), "Load PNG", false) { app.load_atlas_dialog(); }
    bx += 92.0;
    if draw_button(Rect::new(bx, 12.0, 104.0, 28.0), "Load Project", false) { app.load_project_dialog(); }
    bx += 112.0;
    if draw_button(Rect::new(bx, 12.0, 106.0, 28.0), "Save Project", false) { app.save_project_current_or_dialog(); }
    bx += 114.0;
    if draw_button(Rect::new(bx, 12.0, 124.0, 28.0), "Export Handoff", false) { app.export_handoff_dialog(); }
    bx += 132.0;
    if draw_button(Rect::new(bx, 12.0, 116.0, 28.0), "Auto Scene", false) { app.auto_map_sheet(); }
    bx += 124.0;
    if draw_button(Rect::new(bx, 12.0, 62.0, 28.0), "Clear", false) {
        app.pieces.clear();
        app.selected_piece = None;
        app.mapping_stage = MappingStage::SourceOnly;
        app.status = "Assembly canvas cleared; source atlas remains unchanged.".to_string();
    }

    let mut x = 365.0;
    let y = 48.0;
    for category in AssetCategory::ALL {
        let w = match category { AssetCategory::Equipment => 92.0, AssetCategory::Character => 88.0, _ => 72.0 };
        if draw_button(Rect::new(x, y, w, 24.0), category.label(), app.category == category) {
            app.category = category;
            if !app.pieces.is_empty() { app.mapping_stage = MappingStage::DraftMapped; }
            app.status = format!("Saving category set to {}.", category.label());
        }
        x += w + 5.0;
    }
}

fn draw_source_panel(app: &MapperApp, source_rect: Rect) {
    draw_panel(source_rect, "Source Tile Sheet", "immutable source atlas, selectable as 32x32 cells");
    let header_right = source_rect.x + source_rect.w - 184.0;
    draw_text(&format!("zoom {:.0}%", app.source_zoom * 100.0), header_right, source_rect.y + 24.0, 15.0, Color::new(0.64, 0.72, 0.80, 1.0));
    if let Some(atlas) = &app.atlas {
        let file = atlas.path.file_name().and_then(|name| name.to_str()).unwrap_or("sheet");
        let badge = if app.mapping_stage.is_green() { "MAPPED" } else { "UNMAPPED" };
        draw_status_pill(Rect::new(source_rect.x + source_rect.w - 92.0, source_rect.y + 9.0, 78.0, 21.0), badge, app.mapping_stage.is_green());
        draw_text(&format!("{}  |  {}x{}", file, atlas.width, atlas.height), source_rect.x + 14.0, source_rect.y + 56.0, 16.0, Color::new(0.78, 0.84, 0.89, 1.0));
        let draw_pos = vec2(source_rect.x, source_rect.y) + app.source_pan;
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
        draw_grid(source_rect, app.source_pan, app.source_zoom, Color::new(1.0, 1.0, 1.0, 0.13));
        if let Some(tile) = app.selected_tile {
            let rect = Rect::new(
                source_rect.x + app.source_pan.x + tile.tile_x as f32 * TILE_SIZE as f32 * app.source_zoom,
                source_rect.y + app.source_pan.y + tile.tile_y as f32 * TILE_SIZE as f32 * app.source_zoom,
                TILE_SIZE as f32 * app.source_zoom,
                TILE_SIZE as f32 * app.source_zoom,
            );
            draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 3.0, Color::new(1.0, 0.82, 0.20, 1.0));
        }
    } else {
        draw_text("No atlas loaded.", source_rect.x + 18.0, source_rect.y + 74.0, 22.0, Color::new(0.75, 0.80, 0.84, 1.0));
        draw_text("Use Load PNG, load a mapper project, or pass a file path from the PCC launcher.", source_rect.x + 18.0, source_rect.y + 104.0, 17.0, Color::new(0.55, 0.63, 0.70, 1.0));
    }
}

fn draw_canvas_panel(app: &mut MapperApp, canvas_rect: Rect) {
    draw_panel(canvas_rect, "Assembly Canvas", "drop puzzle pieces here; transforms write metadata only");
    draw_text(&format!("zoom {:.0}%", app.canvas_zoom * 100.0), canvas_rect.x + canvas_rect.w - 216.0, canvas_rect.y + 24.0, 15.0, Color::new(0.64, 0.72, 0.80, 1.0));
    if draw_button(Rect::new(canvas_rect.x + canvas_rect.w - 148.0, canvas_rect.y + 8.0, 58.0, 23.0), "2x", false) { app.reset_canvas_view(); }
    if draw_button(Rect::new(canvas_rect.x + canvas_rect.w - 82.0, canvas_rect.y + 8.0, 66.0, 23.0), "Fit", false) { app.fit_canvas_to_pieces(canvas_rect); }

    draw_grid(canvas_rect, app.canvas_pan, app.canvas_zoom, Color::new(1.0, 1.0, 1.0, 0.10));
    if let Some(atlas) = &app.atlas {
        let mut draw_order: Vec<usize> = (0..app.pieces.len()).collect();
        draw_order.sort_by_key(|index| app.pieces[*index].layer);
        for index in draw_order {
            let piece = &app.pieces[index];
            let dest = app.canvas_piece_rect(canvas_rect, piece);
            let source = Rect::new(piece.source_rect[0] as f32, piece.source_rect[1] as f32, TILE_SIZE as f32, TILE_SIZE as f32);
            let center = vec2(dest.x + dest.w * 0.5, dest.y + dest.h * 0.5);
            draw_texture_ex(
                &atlas.texture,
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

    let info_y = canvas_rect.y + canvas_rect.h - 94.0;
    draw_rectangle(canvas_rect.x + 10.0, info_y, canvas_rect.w - 20.0, 78.0, Color::new(0.018, 0.023, 0.031, 0.90));
    draw_rectangle_lines(canvas_rect.x + 10.0, info_y, canvas_rect.w - 20.0, 78.0, 1.0, Color::new(0.16, 0.22, 0.28, 1.0));
    draw_text("Controls", canvas_rect.x + 18.0, info_y + 22.0, 18.0, Color::new(0.88, 0.92, 0.95, 1.0));
    draw_text("drag source -> canvas | outside release cancels | Space+drag pan | wheel zoom | Ctrl+G auto scene", canvas_rect.x + 18.0, info_y + 46.0, 16.0, Color::new(0.68, 0.75, 0.82, 1.0));
    draw_text("select piece: R rotate, H/V flip, Delete remove, [ ] layer", canvas_rect.x + 18.0, info_y + 68.0, 16.0, Color::new(0.68, 0.75, 0.82, 1.0));
}

fn draw_inspector(app: &mut MapperApp, inspector_rect: Rect, canvas_rect: Rect) {
    draw_panel(inspector_rect, "Asset Intake", "mapping status, category, generated layout");
    let mut y = inspector_rect.y + 58.0;
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

    draw_text("Forge-style commands", inspector_rect.x + 14.0, y, 16.0, Color::new(0.60, 0.70, 0.78, 1.0));
    y += 10.0;
    if draw_button(Rect::new(inspector_rect.x + 14.0, y, inspector_rect.w - 28.0, 29.0), "Generate correction scene", false) { app.auto_map_sheet(); }
    y += 37.0;
    if draw_button(Rect::new(inspector_rect.x + 14.0, y, inspector_rect.w - 28.0, 29.0), "Save mapper project", false) { app.save_project_current_or_dialog(); }
    y += 37.0;
    if draw_button(Rect::new(inspector_rect.x + 14.0, y, inspector_rect.w - 28.0, 29.0), "Export engine handoff", false) { app.export_handoff_dialog(); }
    y += 37.0;
    if draw_button(Rect::new(inspector_rect.x + 14.0, y, inspector_rect.w - 28.0, 29.0), "Fit canvas", false) { app.fit_canvas_to_pieces(canvas_rect); }
    y += 50.0;

    let (layout_w, layout_h, layout_label) = app.category.default_layout();
    draw_text("Known-sheet scene generator", inspector_rect.x + 14.0, y, 16.0, Color::new(0.60, 0.70, 0.78, 1.0));
    y += 24.0;
    draw_text(layout_label, inspector_rect.x + 14.0, y, 17.0, Color::new(0.88, 0.91, 0.94, 1.0));
    y += 24.0;
    draw_text(&format!("{} x {} 32px cells", layout_w, layout_h), inspector_rect.x + 14.0, y, 16.0, Color::new(0.68, 0.75, 0.82, 1.0));
    y += 36.0;

    draw_text("Next asset-lane upgrade", inspector_rect.x + 14.0, y, 16.0, Color::new(0.60, 0.70, 0.78, 1.0));
    y += 24.0;
    let _ = draw_wrapped_line("Library browser will load the Havenwild tile-sheet catalog and show a green mapped check beside every sheet with a mapped-sheet record.", inspector_rect.x + 14.0, y, 31, 15.0, Color::new(0.70, 0.77, 0.84, 1.0));

    let bottom_y = inspector_rect.y + inspector_rect.h - 96.0;
    draw_rectangle(inspector_rect.x + 12.0, bottom_y, inspector_rect.w - 24.0, 78.0, app.category.color());
    draw_rectangle(inspector_rect.x + 14.0, bottom_y + 2.0, inspector_rect.w - 28.0, 74.0, Color::new(0.025, 0.030, 0.038, 0.78));
    draw_text("Mapped-sheet meaning", inspector_rect.x + 20.0, bottom_y + 25.0, 16.0, Color::new(0.92, 0.95, 0.96, 1.0));
    draw_text("Green = mapper metadata exists", inspector_rect.x + 20.0, bottom_y + 49.0, 15.0, Color::new(0.74, 0.82, 0.84, 1.0));
    draw_text("Not runtime-published yet", inspector_rect.x + 20.0, bottom_y + 69.0, 15.0, Color::new(0.74, 0.82, 0.84, 1.0));
}

fn draw_app(app: &mut MapperApp, source_rect: Rect, canvas_rect: Rect, inspector_rect: Rect) {
    clear_background(Color::new(0.020, 0.026, 0.034, 1.0));
    draw_top_bar(app);
    draw_source_panel(app, source_rect);
    draw_canvas_panel(app, canvas_rect);
    draw_inspector(app, inspector_rect, canvas_rect);

    draw_rectangle(0.0, screen_height() - STATUS_H, screen_width(), STATUS_H, Color::new(0.030, 0.038, 0.050, 1.0));
    draw_line(0.0, screen_height() - STATUS_H, screen_width(), screen_height() - STATUS_H, 1.0, Color::new(0.13, 0.18, 0.23, 1.0));
    let atlas_label = app.atlas.as_ref()
        .and_then(|atlas| atlas.path.file_name().and_then(|name| name.to_str()))
        .unwrap_or("no atlas");
    let project_label = app.project_path.as_ref()
        .and_then(|path| path.file_name().and_then(|name| name.to_str()))
        .unwrap_or("unsaved project");
    draw_text(
        &format!("{} | stage: {} | category: {} | pieces: {} | atlas: {} | project: {}", app.status, app.mapping_stage.label(), app.category.label(), app.pieces.len(), atlas_label, project_label),
        12.0,
        screen_height() - 10.0,
        16.0,
        Color::new(0.86, 0.90, 0.93, 1.0),
    );
}

fn window_conf() -> Conf {
    Conf {
        window_title: "Havenwild Atlas Mapper Lite".to_string(),
        window_width: 1600,
        window_height: 940,
        high_dpi: true,
        ..Default::default()
    }
}

#[macroquad::main(window_conf)]
async fn main() {
    let mut app = MapperApp::default();
    if let Some(path) = env::args().nth(1) {
        let path = PathBuf::from(path);
        if path.extension().and_then(|ext| ext.to_str()).map(|ext| ext.eq_ignore_ascii_case("json")).unwrap_or(false) {
            app.load_project(&path);
        } else {
            app.load_atlas(path);
        }
    }
    loop {
        let width = screen_width();
        let height = screen_height();
        let body_top = TOP_BAR_H + GAP;
        let body_h = height - TOP_BAR_H - STATUS_H - GAP * 2.0;
        let source_w = (width * 0.34).clamp(410.0, 650.0);
        let inspector_w = INSPECTOR_W.min((width * 0.24).max(260.0));
        let canvas_x = source_w + GAP;
        let canvas_w = width - source_w - inspector_w - GAP * 3.0;
        let source_rect = Rect::new(GAP, body_top, source_w - GAP * 0.5, body_h);
        let canvas_rect = Rect::new(canvas_x, body_top, canvas_w, body_h);
        let inspector_rect = Rect::new(canvas_x + canvas_w + GAP, body_top, inspector_w, body_h);
        app.handle_input(source_rect, canvas_rect);
        draw_app(&mut app, source_rect, canvas_rect, inspector_rect);
        next_frame().await;
    }
}
