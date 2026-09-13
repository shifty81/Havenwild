use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use macroquad::prelude::*;
use rfd::FileDialog;
use serde::{Deserialize, Serialize};

const TILE_SIZE: i32 = 32;
const TOP_BAR_H: f32 = 64.0;
const STATUS_H: f32 = 30.0;
const GAP: f32 = 12.0;
const MIN_SOURCE_ZOOM: f32 = 0.50;
const MAX_SOURCE_ZOOM: f32 = 6.00;
const MIN_CANVAS_ZOOM: f32 = 0.75;
const MAX_CANVAS_ZOOM: f32 = 4.00;
const DEFAULT_CANVAS_ZOOM: f32 = 2.00;
const ZOOM_STEP: f32 = 1.12;
const PROJECT_SCHEMA: &str = "havenwild.atlas_mapper_project.v0_1";
const HANDOFF_SCHEMA: &str = "havenwild.atlas_assembly_handoff.v0_2";

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
            "building_or_house" | "house" => Some(AssetCategory::House),
            "object" => Some(AssetCategory::Object),
            "character" => Some(AssetCategory::Character),
            "equipment" => Some(AssetCategory::Equipment),
            "fx" => Some(AssetCategory::Fx),
            "ui" => Some(AssetCategory::Ui),
            _ => None,
        }
    }
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
struct SourceTile {
    tile_x: i32,
    tile_y: i32,
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

struct LoadedAtlas {
    path: PathBuf,
    texture: Texture2D,
    width: i32,
    height: i32,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum DragState {
    None,
    SourceTile(SourceTile),
    ExistingPiece(usize),
}

struct MapperApp {
    atlas: Option<LoadedAtlas>,
    project_path: Option<PathBuf>,
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
}

impl Default for MapperApp {
    fn default() -> Self {
        Self {
            atlas: None,
            project_path: None,
            selected_tile: None,
            selected_piece: None,
            drag: DragState::None,
            drag_origin: None,
            pieces: Vec::new(),
            next_piece_id: 1,
            category: AssetCategory::Terrain,
            assembly_name: "new_atlas_assembly".to_string(),
            source_pan: vec2(16.0, 38.0),
            source_zoom: 1.0,
            canvas_pan: vec2(32.0, 38.0),
            canvas_zoom: DEFAULT_CANVAS_ZOOM,
            is_panning_source: false,
            is_panning_canvas: false,
            last_mouse: Vec2::ZERO,
            status: "Open from PCC Run menu. Load a PNG atlas, drag 32x32 tiles to the assembly canvas, save project, export handoff JSON.".to_string(),
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
                if self.assembly_name == "new_atlas_assembly" {
                    if let Some(stem) = path.file_stem().and_then(|stem| stem.to_str()) {
                        self.assembly_name = format!("{stem}_assembly");
                    }
                }
                self.atlas = Some(LoadedAtlas { path, texture, width, height });
                self.selected_tile = None;
                self.selected_piece = None;
                self.drag = DragState::None;
                self.drag_origin = None;
                self.status = format!("Loaded {file_name} ({width}x{height}); source atlas remains read-only.");
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
        if document.schema != PROJECT_SCHEMA {
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

        let atlas_path = PathBuf::from(&document.source_atlas_path);
        if atlas_path.exists() {
            self.load_atlas(atlas_path);
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
            self.status = "Place at least one piece before exporting.".to_string();
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
        let exported_unix_seconds = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|duration| duration.as_secs())
            .unwrap_or(0);
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
            exported_unix_seconds,
            pieces: self.pieces.clone(),
            engine_notes: vec![
                "The source atlas is immutable and was not modified.".to_string(),
                "Each piece maps one 32x32 source tile to an assembly grid cell.".to_string(),
                "This handoff is assembly evidence; engine import must add sockets, footprints, collision, traversal, provenance, and runtime validation before publication.".to_string(),
            ],
        };
        match serde_json::to_string_pretty(&document) {
            Ok(text) => match fs::write(path, text) {
                Ok(()) => self.status = format!("Exported handoff: {}", path.to_string_lossy()),
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
        self.status = format!("Placed tile {},{} as {} piece.", tile.tile_x, tile.tile_y, self.category.label());
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
        if mouse.y < panel.y + 30.0 { return None; }
        let local = (mouse - vec2(panel.x, panel.y) - self.source_pan) / self.source_zoom;
        if local.x < 0.0 || local.y < 0.0 || local.x >= atlas.width as f32 || local.y >= atlas.height as f32 {
            return None;
        }
        let tile_x = (local.x as i32) / TILE_SIZE;
        let tile_y = (local.y as i32) / TILE_SIZE;
        Some(SourceTile { tile_x, tile_y })
    }

    fn canvas_grid_at(&self, panel: Rect, mouse: Vec2) -> Option<(i32, i32)> {
        if !panel.contains(mouse) || mouse.y < panel.y + 30.0 { return None; }
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
        self.canvas_pan = vec2(48.0, 56.0);
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
            48.0 - min_x as f32 * TILE_SIZE as f32 * self.canvas_zoom,
            64.0 - min_y as f32 * TILE_SIZE as f32 * self.canvas_zoom,
        );
        self.status = "Canvas view fit to current assembly without dropping below readable zoom.".to_string();
    }

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

fn draw_button(rect: Rect, label: &str, active: bool) -> bool {
    let mouse = mouse_position_local();
    let hovered = rect.contains(mouse);
    let fill = if active {
        Color::new(0.19, 0.32, 0.44, 1.0)
    } else if hovered {
        Color::new(0.13, 0.16, 0.20, 1.0)
    } else {
        Color::new(0.08, 0.10, 0.13, 1.0)
    };
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, fill);
    draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 1.0, Color::new(0.24, 0.29, 0.34, 1.0));
    draw_text(label, rect.x + 8.0, rect.y + 20.0, 17.0, Color::new(0.88, 0.91, 0.94, 1.0));
    hovered && is_mouse_button_pressed(MouseButton::Left)
}

fn draw_panel(rect: Rect, title: &str) {
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, Color::new(0.032, 0.037, 0.047, 1.0));
    draw_rectangle(rect.x + 1.0, rect.y + 1.0, rect.w - 2.0, rect.h - 2.0, Color::new(0.045, 0.052, 0.066, 1.0));
    draw_rectangle(rect.x, rect.y, rect.w, 30.0, Color::new(0.060, 0.071, 0.091, 1.0));
    draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 1.0, Color::new(0.24, 0.28, 0.34, 1.0));
    draw_line(rect.x, rect.y + 30.0, rect.x + rect.w, rect.y + 30.0, 1.0, Color::new(0.13, 0.16, 0.20, 1.0));
    draw_text(title, rect.x + 10.0, rect.y + 21.0, 18.0, Color::new(0.88, 0.91, 0.94, 1.0));
}

fn draw_grid(rect: Rect, pan: Vec2, zoom: f32, line_color: Color) {
    let step = TILE_SIZE as f32 * zoom;
    if step < 4.0 { return; }
    let start_x = rect.x + pan.x.rem_euclid(step);
    let start_y = rect.y + pan.y.rem_euclid(step);
    let mut x = start_x;
    while x < rect.x + rect.w {
        draw_line(x, rect.y + 30.0, x, rect.y + rect.h, 1.0, line_color);
        x += step;
    }
    let mut y = start_y;
    while y < rect.y + rect.h {
        draw_line(rect.x, y, rect.x + rect.w, y, 1.0, line_color);
        y += step;
    }
}

fn draw_app(app: &mut MapperApp, source_rect: Rect, canvas_rect: Rect) {
    clear_background(Color::new(0.025, 0.030, 0.038, 1.0));
    draw_rectangle(0.0, 0.0, screen_width(), TOP_BAR_H, Color::new(0.040, 0.048, 0.060, 1.0));
    draw_text("Havenwild Atlas Mapper Lite", 16.0, 30.0, 24.0, Color::new(0.92, 0.94, 0.96, 1.0));
    draw_text("read-only source atlas -> 32x32 puzzle assembly -> project JSON -> engine handoff", 18.0, 53.0, 16.0, Color::new(0.62, 0.69, 0.75, 1.0));

    let mut bx = 310.0;
    if draw_button(Rect::new(bx, 12.0, 82.0, 28.0), "Load PNG", false) { app.load_atlas_dialog(); }
    bx += 90.0;
    if draw_button(Rect::new(bx, 12.0, 98.0, 28.0), "Load Project", false) { app.load_project_dialog(); }
    bx += 106.0;
    if draw_button(Rect::new(bx, 12.0, 100.0, 28.0), "Save Project", false) { app.save_project_current_or_dialog(); }
    bx += 108.0;
    if draw_button(Rect::new(bx, 12.0, 118.0, 28.0), "Export Handoff", false) { app.export_handoff_dialog(); }
    bx += 126.0;
    if draw_button(Rect::new(bx, 12.0, 62.0, 28.0), "Clear", false) {
        app.pieces.clear();
        app.selected_piece = None;
        app.status = "Assembly canvas cleared; source atlas remains unchanged.".to_string();
    }

    let mut x = 310.0;
    let y = 38.0;
    for category in AssetCategory::ALL {
        let w = match category { AssetCategory::Equipment => 92.0, AssetCategory::Character => 88.0, _ => 72.0 };
        if draw_button(Rect::new(x, y, w, 22.0), category.label(), app.category == category) {
            app.category = category;
            app.status = format!("Saving category set to {}.", category.label());
        }
        x += w + 5.0;
    }

    draw_panel(source_rect, "Source Atlas - immutable 32x32 tile picker");
    draw_panel(canvas_rect, "Assembly Canvas - drag, reorder, rotate, and export recipe");

    draw_text(&format!("zoom {:.0}%", app.source_zoom * 100.0), source_rect.x + source_rect.w - 92.0, source_rect.y + 21.0, 15.0, Color::new(0.64, 0.72, 0.80, 1.0));
    draw_text(&format!("zoom {:.0}%", app.canvas_zoom * 100.0), canvas_rect.x + canvas_rect.w - 198.0, canvas_rect.y + 21.0, 15.0, Color::new(0.64, 0.72, 0.80, 1.0));
    if draw_button(Rect::new(canvas_rect.x + canvas_rect.w - 130.0, canvas_rect.y + 5.0, 54.0, 21.0), "2x", false) { app.reset_canvas_view(); }
    if draw_button(Rect::new(canvas_rect.x + canvas_rect.w - 70.0, canvas_rect.y + 5.0, 54.0, 21.0), "Fit", false) { app.fit_canvas_to_pieces(canvas_rect); }

    if let Some(atlas) = &app.atlas {
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
        draw_grid(source_rect, app.source_pan, app.source_zoom, Color::new(1.0, 1.0, 1.0, 0.12));
        if let Some(tile) = app.selected_tile {
            let rect = Rect::new(
                source_rect.x + app.source_pan.x + tile.tile_x as f32 * TILE_SIZE as f32 * app.source_zoom,
                source_rect.y + app.source_pan.y + tile.tile_y as f32 * TILE_SIZE as f32 * app.source_zoom,
                TILE_SIZE as f32 * app.source_zoom,
                TILE_SIZE as f32 * app.source_zoom,
            );
            draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 3.0, YELLOW);
        }
    } else {
        draw_text("No atlas loaded. Click Load PNG, load a mapper project, or pass a file path as an argument.", source_rect.x + 18.0, source_rect.y + 66.0, 20.0, GRAY);
    }

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
                draw_rectangle_lines(dest.x, dest.y, dest.w, dest.h, 3.0, SKYBLUE);
                let label = format!("id:{} layer:{} rot:{}", piece.id, piece.layer, piece.rotation_degrees);
                draw_text(&label, dest.x + 2.0, dest.y - 4.0, 14.0, SKYBLUE);
            }
        }
        if let DragState::SourceTile(tile) = app.drag {
            let mouse = mouse_position_local();
            let source = Rect::new((tile.tile_x * TILE_SIZE) as f32, (tile.tile_y * TILE_SIZE) as f32, TILE_SIZE as f32, TILE_SIZE as f32);
            draw_texture_ex(
                &atlas.texture,
                mouse.x - 16.0,
                mouse.y - 16.0,
                Color::new(1.0, 1.0, 1.0, 0.75),
                DrawTextureParams { dest_size: Some(vec2(32.0, 32.0)), source: Some(source), ..Default::default() },
            );
        }
    }

    let info_y = canvas_rect.y + canvas_rect.h - 108.0;
    draw_rectangle(canvas_rect.x + 10.0, info_y, canvas_rect.w - 20.0, 92.0, Color::new(0.02, 0.025, 0.032, 0.88));
    draw_text("Controls: drag tile source -> canvas only | release outside cancels safely | select piece then R/H/V/Del/[ ]", canvas_rect.x + 18.0, info_y + 24.0, 18.0, LIGHTGRAY);
    draw_text("Mouse wheel zooms hovered panel. Hold Space + drag to pan. Ctrl+O load PNG, Ctrl+Shift+O load project.", canvas_rect.x + 18.0, info_y + 50.0, 18.0, LIGHTGRAY);
    draw_text("Ctrl+S saves mapper project. Ctrl+E exports engine handoff. Source atlas pixels are never modified.", canvas_rect.x + 18.0, info_y + 76.0, 18.0, LIGHTGRAY);

    draw_rectangle(0.0, screen_height() - STATUS_H, screen_width(), STATUS_H, Color::new(0.040, 0.048, 0.060, 1.0));
    let atlas_label = app.atlas.as_ref()
        .and_then(|atlas| atlas.path.file_name().and_then(|name| name.to_str()))
        .unwrap_or("no atlas");
    let project_label = app.project_path.as_ref()
        .and_then(|path| path.file_name().and_then(|name| name.to_str()))
        .unwrap_or("unsaved project");
    draw_text(
        &format!("{} | category: {} | pieces: {} | atlas: {} | project: {}", app.status, app.category.label(), app.pieces.len(), atlas_label, project_label),
        12.0,
        screen_height() - 9.0,
        17.0,
        Color::new(0.86, 0.90, 0.93, 1.0),
    );
}

fn window_conf() -> Conf {
    Conf {
        window_title: "Havenwild Atlas Mapper Lite".to_string(),
        window_width: 1500,
        window_height: 900,
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
        let left_w = (width * 0.43).clamp(420.0, 760.0);
        let source_rect = Rect::new(GAP, body_top, left_w - GAP * 1.5, body_h);
        let canvas_rect = Rect::new(left_w + GAP, body_top, width - left_w - GAP * 2.0, body_h);
        app.handle_input(source_rect, canvas_rect);
        draw_app(&mut app, source_rect, canvas_rect);
        next_frame().await;
    }
}
