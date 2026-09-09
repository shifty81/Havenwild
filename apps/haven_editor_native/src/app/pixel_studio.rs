use super::pixel_new_document::NewPixelDialogState;
use super::sprite_canvas_authority::*;
use super::*;
use haven_assets::asset_intake::{repo_root_dir, AssetIntakeTargetKind};
use haven_pixel::{
    record_recent_pixel_document, scan_pixel_library, AnimationSocket, PixelAssetKind,
    PixelBrushKind, PixelClipboard, PixelDocument, PixelDocumentKind, PixelLibraryCategory, PixelLibraryEntry, PixelPreviewMode,
    PixelSelection, PixelTool,
};
use std::path::Path;

const ZOOM_LEVELS: [f32; 18] = [
    0.0625, 0.125, 0.25, 0.5, 1.0, 2.0, 4.0, 6.0, 8.0, 12.0, 16.0, 24.0, 32.0, 40.0, 48.0, 56.0,
    64.0, 72.0,
];
const MAX_PIXEL_EDIT_DIMENSION: u32 = 8_192;
const MAX_PIXEL_EDIT_PIXELS: u64 = 16_777_216;
pub(crate) const PALETTE: [[u8; 4]; 16] = [
    [0, 0, 0, 0],
    [24, 27, 34, 255],
    [65, 49, 45, 255],
    [111, 78, 55, 255],
    [177, 117, 69, 255],
    [226, 172, 91, 255],
    [242, 222, 166, 255],
    [239, 239, 224, 255],
    [34, 74, 52, 255],
    [57, 111, 62, 255],
    [104, 157, 75, 255],
    [166, 195, 94, 255],
    [26, 72, 104, 255],
    [43, 117, 155, 255],
    [79, 171, 190, 255],
    [169, 220, 209, 255],
];

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum PixelInspectorTab {
    Asset,
    Animation,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum PixelSelectionMode {
    Pixels,
    Frame,
}

impl PixelSelectionMode {
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Pixels => "Pixels",
            Self::Frame => "Frame",
        }
    }

    pub(crate) fn cycle(self) -> Self {
        match self {
            Self::Pixels => Self::Frame,
            Self::Frame => Self::Pixels,
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum PixelAssetRole {
    RepeatTexture,
    Character,
    Object,
    General,
}

impl PixelAssetRole {
    pub(crate) fn from_document(document: &PixelDocument) -> Self {
        match document.metadata.preview_mode {
            PixelPreviewMode::Repeat => Self::RepeatTexture,
            PixelPreviewMode::Character => Self::Character,
            PixelPreviewMode::Object => Self::Object,
            PixelPreviewMode::Ui | PixelPreviewMode::None => match document.metadata.asset_kind {
                PixelAssetKind::Tile | PixelAssetKind::Tilesheet => Self::RepeatTexture,
                PixelAssetKind::SpriteSheet
                | PixelAssetKind::AnimationSheet
                | PixelAssetKind::CharacterLayer => Self::Character,
                PixelAssetKind::ObjectSprite => Self::Object,
                PixelAssetKind::UiTexture | PixelAssetKind::General => Self::General,
            },
        }
    }

    pub(crate) fn supports_repeat_preview(self) -> bool {
        matches!(self, Self::RepeatTexture)
    }
}

#[derive(Clone, Debug)]
pub(crate) struct WorldAssetEditContext {
    pub origin_scene_id: ProjectSceneId,
    pub origin_cell: [i32; 2],
    pub origin_camera: CanvasCameraState,
    pub origin_viewport_mode: EditorViewportMode,
    pub origin_world_cursor: [i32; 2],
    pub origin_world_camera: CanvasCameraState,
    pub origin_landmass_id: i32,
    pub semantic_id: String,
    pub generated_output: bool,
}


#[derive(Clone, Debug)]
pub(crate) struct WorldRegionPixelEditContext {
    pub scene_id: ProjectSceneId,
    pub local_rect: GridRect,
    pub global_rect: GridRect,
    pub scope_kind: String,
    pub revision: String,
    pub origin_viewport_mode: EditorViewportMode,
    pub origin_scene_id: Option<ProjectSceneId>,
    pub origin_scene_cursor: [i32; 2],
    pub origin_scene_camera: CanvasCameraState,
    pub origin_world_camera: CanvasCameraState,
    pub origin_landmass_id: i32,
    pub output_path: String,
}

#[derive(Clone, Debug)]
pub(crate) struct PixelAnimationEditContext {
    pub animation_asset_id: String,
    pub animation_display_name: String,
    pub clip_index: usize,
    pub frame_index: usize,
    pub clip_label: String,
    pub direction_label: String,
    pub source_path_before_edit: String,
    pub frame_source: PixelSelection,
    pub previous_source: Option<PixelSelection>,
    pub next_source: Option<PixelSelection>,
    pub shadow_offset: [i32; 2],
    pub sockets: Vec<AnimationSocket>,
    pub onion_skin: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum RepeatPreviewMode { Off, X, Y, Both }

impl RepeatPreviewMode {
    pub(crate) fn next(self) -> Self { match self { Self::Off=>Self::X, Self::X=>Self::Y, Self::Y=>Self::Both, Self::Both=>Self::Off } }
    pub(crate) fn label(self) -> &'static str { match self { Self::Off=>"Off", Self::X=>"X", Self::Y=>"Y", Self::Both=>"XY" } }
}


#[derive(Clone)]
pub(crate) struct PixelDocumentSession {
    pub document: PixelDocument,
    pub animation_context: Option<PixelAnimationEditContext>,
    pub world_asset_context: Option<WorldAssetEditContext>,
    pub world_region_context: Option<WorldRegionPixelEditContext>,
    pub zoom_index: usize,
    pub pan: Vec2,
    pub show_pixel_grid: bool,
    pub show_atlas_grid: bool,
    pub repeat_preview_mode: RepeatPreviewMode,
    pub selection_mode: PixelSelectionMode,
}

impl PixelDocumentSession {
    fn key(&self) -> String {
        pixel_document_key(&self.document)
    }
}

#[derive(Clone, Debug)]
pub(crate) struct PixelDocumentTabInfo {
    pub index: usize,
    pub label: String,
    pub dirty: bool,
    pub active: bool,
}

fn pixel_document_key(document: &PixelDocument) -> String {
    if !document.metadata.output_path.trim().is_empty() {
        format!("output:{}", document.metadata.output_path.replace('\\', "/").to_ascii_lowercase())
    } else if !document.metadata.source_path.trim().is_empty() {
        format!("source:{}", document.metadata.source_path.replace('\\', "/").to_ascii_lowercase())
    } else {
        format!("asset:{}", document.metadata.asset_id.to_ascii_lowercase())
    }
}

pub(crate) struct PixelStudioState {
    pub library: Vec<PixelLibraryEntry>,
    pub library_loaded: bool,
    pub library_filter: String,
    pub library_category_index: usize,
    pub selected_entry: usize,
    pub library_offset: usize,
    pub document: Option<PixelDocument>,
    /// W60E19: stable multi-document slots. The active slot is represented by `None`
    /// while its document lives in `document` so legacy canvas code keeps one truthful
    /// active document authority without cloning or shadow copies.
    pub document_tabs: Vec<Option<PixelDocumentSession>>,
    pub active_document_tab: Option<usize>,
    /// Recently closed full sessions power Ctrl+Shift+T without losing pan,
    /// context, or unsaved working state. Closing a view is not resource deletion.
    pub recently_closed_documents: Vec<PixelDocumentSession>,
    /// Shared Pixel Studio clipboard survives document switches so selection areas
    /// can be copied/cut/pasted between any open Pixel documents.
    pub clipboard: Option<PixelClipboard>,
    pub texture: Option<Texture2D>,
    /// Side-by-side companion document. The active document can live in either
    /// pane; clicking the other pane activates that document in-place without
    /// visually swapping left/right positions.
    pub secondary_document_tab: Option<usize>,
    pub secondary_texture: Option<Texture2D>,
    pub active_document_on_right: bool,
    pub tool: PixelTool,
    pub selected_color: [u8; 4],
    pub background_color: [u8; 4],
    pub brush_opacity: u8,
    pub brush_size: u8,
    pub brush_kind: PixelBrushKind,
    pub brush_density: u8,
    pub brush_angle_degrees: i16,
    pub stroke_uses_background: bool,
    pub symmetry_horizontal: bool,
    pub symmetry_vertical: bool,
    pub zoom_index: usize,
    pub pan: Vec2,
    pub needs_frame: bool,
    pub show_pixel_grid: bool,
    pub show_atlas_grid: bool,
    pub show_repeat_preview: bool,
    pub repeat_preview_mode: RepeatPreviewMode,
    pub symmetry_axis_x: Option<u32>,
    pub symmetry_axis_y: Option<u32>,
    pub selection_mode: PixelSelectionMode,
    pub grid_realign_armed: bool,
    pub grid_realign_enabled: bool,
    pub grid_drag_origin: Option<(i32, i32)>,
    pub drag_start: Option<(u32, u32)>,
    pub drag_current: Option<(u32, u32)>,
    pub stroke_started: bool,
    pub pan_drag: Option<Vec2>,
    pub target_kind: AssetIntakeTargetKind,
    pub target_index: usize,
    pub inspector_tab: PixelInspectorTab,
    pub layer_offset: usize,
    pub layer_rename_buffer: Option<String>,
    pub resize_width: u32,
    pub resize_height: u32,
    pub next_autosave_at: f64,
    pub autosave_status: String,
    pub animation_context: Option<PixelAnimationEditContext>,
    pub world_asset_context: Option<WorldAssetEditContext>,
    pub world_region_context: Option<WorldRegionPixelEditContext>,
    pub new_dialog: Option<NewPixelDialogState>,
}

impl PixelStudioState {
    fn capture_active_session(&mut self) -> Option<PixelDocumentSession> {
        let document = self.document.take()?;
        Some(PixelDocumentSession {
            document,
            animation_context: self.animation_context.take(),
            world_asset_context: self.world_asset_context.take(),
            world_region_context: self.world_region_context.take(),
            zoom_index: self.zoom_index,
            pan: self.pan,
            show_pixel_grid: self.show_pixel_grid,
            show_atlas_grid: self.show_atlas_grid,
            repeat_preview_mode: self.repeat_preview_mode,
            selection_mode: self.selection_mode,
        })
    }

    fn restore_session(&mut self, session: PixelDocumentSession) {
        self.document = Some(session.document);
        self.animation_context = session.animation_context;
        self.world_asset_context = session.world_asset_context;
        self.world_region_context = session.world_region_context;
        self.zoom_index = session.zoom_index;
        self.pan = session.pan;
        self.show_pixel_grid = session.show_pixel_grid;
        self.show_atlas_grid = session.show_atlas_grid;
        self.repeat_preview_mode = session.repeat_preview_mode;
        self.show_repeat_preview = !matches!(session.repeat_preview_mode, RepeatPreviewMode::Off);
        self.selection_mode = session.selection_mode;
        self.texture = None;
        self.needs_frame = false;
        self.refresh_texture();
    }

    fn stash_active_session(&mut self) {
        let Some(index) = self.active_document_tab else { return; };
        let Some(session) = self.capture_active_session() else { return; };
        if index >= self.document_tabs.len() {
            self.document_tabs.resize_with(index + 1, || None);
        }
        self.document_tabs[index] = Some(session);
    }

    /// Opens a Pixel Studio document in the shared document host. If that source is
    /// already open, its existing in-memory session is focused rather than duplicated.
    /// Returns true when a new tab was created.
    pub(crate) fn open_document_session(&mut self, document: PixelDocument) -> bool {
        let key = pixel_document_key(&document);
        if self.document.as_ref().is_some_and(|active| pixel_document_key(active) == key) {
            return false;
        }
        if let Some(existing_index) = self.document_tabs.iter().position(|slot| {
            slot.as_ref().is_some_and(|session| session.key() == key)
        }) {
            self.stash_active_session();
            if let Some(session) = self.document_tabs.get_mut(existing_index).and_then(Option::take) {
                self.active_document_tab = Some(existing_index);
                self.restore_session(session);
            }
            return false;
        }
        self.stash_active_session();
        let index = self.document_tabs.len();
        self.document_tabs.push(None);
        self.active_document_tab = Some(index);
        self.document = Some(document);
        self.animation_context = None;
        self.world_asset_context = None;
        self.world_region_context = None;
        true
    }

    pub(crate) fn document_tab_info(&self) -> Vec<PixelDocumentTabInfo> {
        self.document_tabs
            .iter()
            .enumerate()
            .filter_map(|(index, slot)| {
                if self.active_document_tab == Some(index) {
                    self.document.as_ref().map(|document| PixelDocumentTabInfo {
                        index,
                        label: document.metadata.display_name.clone(),
                        dirty: document.dirty,
                        active: true,
                    })
                } else {
                    slot.as_ref().map(|session| PixelDocumentTabInfo {
                        index,
                        label: session.document.metadata.display_name.clone(),
                        dirty: session.document.dirty,
                        active: false,
                    })
                }
            })
            .collect()
    }

    pub(crate) fn activate_document_tab(&mut self, index: usize) -> bool {
        if self.active_document_tab == Some(index) || index >= self.document_tabs.len() {
            return false;
        }
        self.stash_active_session();
        let Some(session) = self.document_tabs.get_mut(index).and_then(Option::take) else {
            return false;
        };
        self.active_document_tab = Some(index);
        self.restore_session(session);
        true
    }

    pub(crate) fn close_document_tab(&mut self, index: usize) -> bool {
        if index >= self.document_tabs.len() {
            return false;
        }
        self.secondary_document_tab = None;
        self.secondary_texture = None;
        self.active_document_on_right = false;

        let active = self.active_document_tab == Some(index);
        let closed = if active {
            self.capture_active_session()
        } else {
            self.document_tabs.get_mut(index).and_then(Option::take)
        };
        if let Some(session) = closed {
            self.recently_closed_documents.push(session);
            if self.recently_closed_documents.len() > 12 {
                self.recently_closed_documents.remove(0);
            }
        }

        self.document_tabs.remove(index);
        if active {
            self.document = None;
            self.texture = None;
            self.animation_context = None;
            self.world_asset_context = None;
            self.world_region_context = None;
            if self.document_tabs.is_empty() {
                self.active_document_tab = None;
                return true;
            }
            let next = index.min(self.document_tabs.len() - 1);
            let Some(session) = self.document_tabs.get_mut(next).and_then(Option::take) else {
                self.active_document_tab = None;
                return true;
            };
            self.active_document_tab = Some(next);
            self.restore_session(session);
        } else if let Some(active_index) = self.active_document_tab {
            if index < active_index {
                self.active_document_tab = Some(active_index - 1);
            }
        }
        true
    }

    pub(crate) fn close_all_documents(&mut self) {
        if let Some(session) = self.capture_active_session() {
            self.recently_closed_documents.push(session);
        }
        for session in self.document_tabs.iter_mut().filter_map(Option::take) {
            self.recently_closed_documents.push(session);
        }
        if self.recently_closed_documents.len() > 12 {
            let excess = self.recently_closed_documents.len() - 12;
            self.recently_closed_documents.drain(0..excess);
        }
        self.document = None;
        self.texture = None;
        self.secondary_texture = None;
        self.secondary_document_tab = None;
        self.active_document_on_right = false;
        self.document_tabs.clear();
        self.active_document_tab = None;
        self.animation_context = None;
        self.world_asset_context = None;
        self.world_region_context = None;
    }

    pub(crate) fn reopen_last_closed_document(&mut self) -> bool {
        while let Some(session) = self.recently_closed_documents.pop() {
            let key = session.key();
            let already_open = self.document.as_ref().is_some_and(|document| pixel_document_key(document) == key)
                || self.document_tabs.iter().filter_map(Option::as_ref).any(|open| open.key() == key);
            if already_open {
                continue;
            }
            self.stash_active_session();
            let index = self.document_tabs.len();
            self.document_tabs.push(None);
            self.active_document_tab = Some(index);
            self.restore_session(session);
            return true;
        }
        false
    }

    pub(crate) fn any_document_dirty(&self) -> bool {
        self.document.as_ref().is_some_and(|document| document.dirty)
            || self.document_tabs.iter().filter_map(Option::as_ref).any(|session| session.document.dirty)
            || self.recently_closed_documents.iter().any(|session| session.document.dirty)
    }

    pub(crate) fn save_document_tab(&mut self, index: usize) -> Result<(), String> {
        if self.active_document_tab == Some(index) {
            if self.world_region_context.is_some() {
                return Err("world-region Pixel documents must publish through the world bridge".to_string());
            }
            return self.document.as_mut().ok_or_else(|| "active Pixel document is unavailable".to_string())?.save(repo_root_dir());
        }
        self.document_tabs
            .get_mut(index)
            .and_then(Option::as_mut)
            .ok_or_else(|| format!("Pixel document tab {index} is unavailable"))
            .and_then(|session| {
                if session.world_region_context.is_some() {
                    Err("world-region Pixel documents must publish through the world bridge".to_string())
                } else {
                    session.document.save(repo_root_dir())
                }
            })
    }

    pub(crate) fn save_inactive_documents(&mut self) -> Result<usize, String> {
        let mut saved = 0usize;
        for session in self.document_tabs.iter_mut().filter_map(Option::as_mut) {
            // World-region working copies publish through the authoritative world
            // bridge when active. Do not silently write them as ordinary assets.
            if session.world_region_context.is_some() {
                continue;
            }
            session.document.save(repo_root_dir())?;
            saved += 1;
        }
        // A closed tab is only a closed view. Dirty working state remains under the
        // same document lifecycle authority until explicitly saved or discarded.
        for session in &mut self.recently_closed_documents {
            if session.world_region_context.is_some() || !session.document.dirty {
                continue;
            }
            session.document.save(repo_root_dir())?;
            saved += 1;
        }
        Ok(saved)
    }

    pub(crate) fn ensure_secondary_document(&mut self) {
        let active = self.active_document_tab;
        let candidate_valid = self.secondary_document_tab.is_some_and(|index| {
            active != Some(index)
                && self.document_tabs.get(index).is_some_and(|slot| slot.is_some())
        });
        if !candidate_valid {
            self.secondary_document_tab = self
                .document_tabs
                .iter()
                .enumerate()
                .find_map(|(index, slot)| (active != Some(index) && slot.is_some()).then_some(index));
            self.secondary_texture = None;
        }
        if self.secondary_texture.is_none() {
            if let Some(index) = self.secondary_document_tab {
                self.secondary_texture = self
                    .document_tabs
                    .get(index)
                    .and_then(Option::as_ref)
                    .and_then(|session| texture_from_document(&session.document).ok());
            }
        }
    }

    pub(crate) fn secondary_document(&self) -> Option<&PixelDocument> {
        let index = self.secondary_document_tab?;
        self.document_tabs.get(index)?.as_ref().map(|session| &session.document)
    }

    pub(crate) fn activate_secondary_document(&mut self) -> bool {
        let Some(index) = self.secondary_document_tab else { return false; };
        let previous_active = self.active_document_tab;
        let changed = self.activate_document_tab(index);
        if changed {
            // Keep both documents in the same visual panes. The old active
            // document becomes the companion and the edit focus crosses the
            // splitter instead of moving the document itself.
            self.secondary_document_tab = previous_active;
            self.secondary_texture = self
                .secondary_document_tab
                .and_then(|tab| self.document_tabs.get(tab))
                .and_then(Option::as_ref)
                .and_then(|session| texture_from_document(&session.document).ok());
            self.active_document_on_right = !self.active_document_on_right;
            self.ensure_secondary_document();
        }
        changed
    }

    pub(crate) fn active_palette(&self) -> Vec<[u8; 4]> {
        self.document
            .as_ref()
            .filter(|document| !document.metadata.palette.is_empty())
            .map(|document| document.metadata.palette.clone())
            .unwrap_or_else(|| PALETTE.to_vec())
    }

    pub(crate) fn add_color_to_palette(&mut self, color: [u8; 4]) -> Result<bool, String> {
        let document = self
            .document
            .as_mut()
            .ok_or_else(|| "Open a Pixel Studio document before editing its palette".to_string())?;
        if document.metadata.palette.is_empty() {
            document.metadata.palette = PALETTE.to_vec();
        }
        if document.metadata.palette.contains(&color) {
            return Ok(false);
        }
        if document.metadata.palette.len() >= 24 {
            return Err("Document palette already contains the maximum 24 colors".to_string());
        }
        document.begin_edit();
        document.metadata.palette.push(color);
        document.dirty = true;
        Ok(true)
    }

    pub(crate) fn new() -> Self {
        Self {
            // The LPC source library can contain tens of thousands of sheets.
            // Do not recursively scan it while the editor process is starting.
            // The Pixel Studio library is populated only after the user presses
            // Rescan, using the bounded project-library policy in haven_pixel.
            library: Vec::new(),
            library_loaded: false,
            library_filter: String::new(),
            library_category_index: 0,
            selected_entry: 0,
            library_offset: 0,
            document: None,
            document_tabs: Vec::new(),
            active_document_tab: None,
            recently_closed_documents: Vec::new(),
            clipboard: None,
            texture: None,
            secondary_document_tab: None,
            secondary_texture: None,
            active_document_on_right: false,
            tool: PixelTool::Selection,
            selected_color: PALETTE[7],
            background_color: PALETTE[1],
            brush_opacity: 255,
            brush_size: 1,
            brush_kind: PixelBrushKind::Square,
            brush_density: 128,
            brush_angle_degrees: 0,
            stroke_uses_background: false,
            symmetry_horizontal: false,
            symmetry_vertical: false,
            zoom_index: 7,
            pan: Vec2::ZERO,
            needs_frame: true,
            show_pixel_grid: true,
            show_atlas_grid: true,
            show_repeat_preview: false,
            repeat_preview_mode: RepeatPreviewMode::Off,
            symmetry_axis_x: None,
            symmetry_axis_y: None,
            selection_mode: PixelSelectionMode::Frame,
            grid_realign_armed: false,
            grid_realign_enabled: false,
            grid_drag_origin: None,
            drag_start: None,
            drag_current: None,
            stroke_started: false,
            pan_drag: None,
            target_kind: AssetIntakeTargetKind::Object,
            target_index: 0,
            inspector_tab: PixelInspectorTab::Asset,
            layer_offset: 0,
            layer_rename_buffer: None,
            resize_width: 32,
            resize_height: 32,
            next_autosave_at: get_time() + 10.0,
            autosave_status: "Autosave ready".to_string(),
            animation_context: None,
            world_asset_context: None,
            world_region_context: None,
            new_dialog: None,
        }
    }

    pub(crate) fn reset_authoring_defaults(&mut self) {
        // W60E6: Pixel Studio always begins with a true 1-image-pixel pencil.
        // Grid scale and world tile size never inflate the brush implicitly.
        self.brush_size = 1;
        self.symmetry_horizontal = false;
        self.symmetry_vertical = false;
        self.symmetry_axis_x = None;
        self.symmetry_axis_y = None;
        self.selection_mode = PixelSelectionMode::Pixels;
        self.tool = PixelTool::Selection;
    }

    pub(crate) fn adjust_brush_size(&mut self, delta: i32) {
        const SIZES: [u8; 10] = [1, 2, 3, 4, 5, 8, 12, 16, 24, 32];
        let current = SIZES.iter().position(|size| *size == self.brush_size).unwrap_or(0) as i32;
        let next = (current + delta).clamp(0, SIZES.len() as i32 - 1) as usize;
        self.brush_size = SIZES[next];
    }

    pub(crate) fn cycle_brush_angle(&mut self, delta: i16) {
        let mut angle = (self.brush_angle_degrees + delta) % 360;
        if angle < 0 { angle += 360; }
        self.brush_angle_degrees = angle;
    }

    pub(crate) fn symmetry_label(&self) -> &'static str {
        match (self.symmetry_horizontal, self.symmetry_vertical) {
            (false, false) => "Off",
            (true, false) => "H",
            (false, true) => "V",
            (true, true) => "H+V",
        }
    }

    pub(crate) fn library_categories(&self) -> Vec<PixelLibraryCategory> {
        let mut categories: Vec<_> = self.library.iter().map(|entry| entry.category).collect();
        categories.sort();
        categories.dedup();
        categories
    }

    pub(crate) fn active_library_category(&self) -> Option<PixelLibraryCategory> {
        self.library_category_index
            .checked_sub(1)
            .and_then(|index| self.library_categories().get(index).copied())
    }

    pub(crate) fn cycle_library_category(&mut self) {
        let count = self.library_categories().len();
        self.library_category_index = (self.library_category_index + 1) % (count + 1).max(1);
        self.library_offset = 0;
        if let Some(index) = self.filtered_library_indices().first().copied() {
            self.selected_entry = index;
        }
    }

    pub(crate) fn filtered_library_indices(&self) -> Vec<usize> {
        let query = self.library_filter.trim().to_ascii_lowercase();
        let category = self.active_library_category();
        self.library
            .iter()
            .enumerate()
            .filter_map(|(index, entry)| {
                let category_matches = category.map_or(true, |active| entry.category == active);
                let query_matches = query.is_empty()
                    || entry.display_name.to_ascii_lowercase().contains(&query)
                    || entry.relative_path.to_ascii_lowercase().contains(&query)
                    || entry.source.label().to_ascii_lowercase().contains(&query)
                    || entry.category.label().to_ascii_lowercase().contains(&query)
                    || entry
                        .license
                        .source_name
                        .to_ascii_lowercase()
                        .contains(&query);
                (category_matches && query_matches).then_some(index)
            })
            .collect()
    }

    pub(crate) fn refresh_library(&mut self) -> Result<usize, String> {
        self.library = scan_pixel_library(repo_root_dir())?;
        self.library_loaded = true;
        let category_count = self.library_categories().len();
        self.library_category_index = self.library_category_index.min(category_count);
        self.selected_entry = self
            .selected_entry
            .min(self.library.len().saturating_sub(1));
        self.library_offset = 0;
        let filtered = self.filtered_library_indices();
        if !filtered.contains(&self.selected_entry) {
            if let Some(index) = filtered.first().copied() {
                self.selected_entry = index;
            }
        }
        Ok(self.library.len())
    }

    pub(crate) fn load_selected(&mut self) -> Result<String, String> {
        let entry = self
            .library
            .get(self.selected_entry)
            .ok_or_else(|| "Pixel library is empty".to_string())?
            .clone();
        validate_editable_image(&entry.path)?;

        let document = PixelDocument::load(&entry.path, &entry.display_name, entry.license)?;
        let texture = texture_from_document(&document)?;

        let _ = record_recent_pixel_document(
            repo_root_dir(),
            &entry.relative_path,
            &entry.display_name,
        );
        self.resize_width = document.width();
        self.resize_height = document.height();
        self.layer_offset = 0;
        self.layer_rename_buffer = None;
        let recovered = document.recovered_from_autosave;
        let created_tab = self.open_document_session(document);
        if created_tab {
            self.texture = Some(texture);
        } else {
            self.refresh_texture();
        }
        self.animation_context = None;
        self.world_asset_context = None;
        self.world_region_context = None;
        self.reset_authoring_defaults();
        if let Some(document) = self.document.as_mut() {
            if document.metadata.palette.is_empty() {
                document.metadata.palette = PALETTE.to_vec();
            }
            let role = PixelAssetRole::from_document(document);
            self.show_repeat_preview = role.supports_repeat_preview();
            self.repeat_preview_mode = if self.show_repeat_preview { RepeatPreviewMode::Both } else { RepeatPreviewMode::Off };
            self.selection_mode = PixelSelectionMode::Pixels;
            if matches!(role, PixelAssetRole::Character) {
                let grid = document.metadata.grid;
                let selection = document.metadata.selection;
                if selection.width != grid.cell_width || selection.height != grid.cell_height {
                    document.metadata.selection = PixelSelection {
                        x: grid.offset_x.max(0) as u32,
                        y: grid.offset_y.max(0) as u32,
                        width: grid.cell_width.min(document.width()).max(1),
                        height: grid.cell_height.min(document.height()).max(1),
                    };
                }
            }
        }
        self.needs_frame = true;
        self.next_autosave_at = get_time() + 10.0;
        self.autosave_status = if recovered {
            "Recovered autosaved changes; Save to keep them".to_string()
        } else {
            "Autosave ready".to_string()
        };
        Ok(format!(
            "Opened {} from {}{}",
            entry.display_name,
            entry.source.label(),
            if recovered {
                " (recovered autosave)"
            } else {
                ""
            }
        ))
    }

    pub(crate) fn open_new_dialog(&mut self) {
        self.new_dialog = Some(NewPixelDialogState::new());
    }

    pub(crate) fn create_from_dialog(&mut self) -> Result<String, String> {
        let (mut document, label, promotion) = {
            let dialog = self
                .new_dialog
                .as_ref()
                .ok_or_else(|| "new-document dialog is not open".to_string())?;
            if let Some(clipboard) = dialog.promotion.as_ref() {
                if dialog.spec.width < clipboard.width() || dialog.spec.height < clipboard.height() {
                    return Err(format!(
                        "promotion canvas {}x{} cannot be smaller than the {}x{} selected source; enlarge the canvas or cancel",
                        dialog.spec.width,
                        dialog.spec.height,
                        clipboard.width(),
                        clipboard.height()
                    ));
                }
            }
            (
                dialog.spec.create_document()?,
                dialog.spec.kind.label().to_string(),
                dialog.promotion.clone(),
            )
        };
        let promoted = promotion.is_some();
        if let Some(clipboard) = promotion {
            document.metadata.license = clipboard.source_license.clone();
            document.metadata.tags.push("promoted_selection".to_string());
            document
                .metadata
                .tags
                .push(format!("derived_from:{}", clipboard.source_asset_id));
            if clipboard.merged_visible {
                document.metadata.tags.push("promoted_from_merged_visible".to_string());
            }
            let _ = document.paste_pixel_clipboard(&clipboard, 0, 0);
            let pivot_max_x = document.width().saturating_sub(1) as i32;
            let pivot_max_y = document.height().saturating_sub(1) as i32;
            document.metadata.pivot = [
                clipboard.pivot_offset[0].clamp(0, pivot_max_x),
                clipboard.pivot_offset[1].clamp(0, pivot_max_y),
            ];
            document.dirty = true;
        }
        let width = document.width();
        let height = document.height();
        self.open_document_session(document);
        if let Some(document) = self.document.as_mut() {
            if document.metadata.palette.is_empty() {
                document.metadata.palette = PALETTE.to_vec();
            }
        }
        self.animation_context = None;
        self.world_asset_context = None;
        self.world_region_context = None;
        self.reset_authoring_defaults();
        self.resize_width = width;
        self.resize_height = height;
        self.layer_offset = 0;
        self.layer_rename_buffer = None;
        self.autosave_status = if promoted {
            "Promoted selection; save to publish the new asset".to_string()
        } else {
            "New document; autosave pending".to_string()
        };
        self.next_autosave_at = get_time() + 10.0;
        self.refresh_texture();
        self.needs_frame = true;
        self.new_dialog = None;
        Ok(if promoted {
            format!("Promoted selection to {label} at {width}x{height}")
        } else {
            format!("Created {label} at {width}x{height}")
        })
    }

    pub(crate) fn copy_selection_to_clipboard(&mut self, merged_visible: bool) -> Result<String, String> {
        let document = self
            .document
            .as_ref()
            .ok_or_else(|| "Open a Pixel Studio document before copying".to_string())?;
        let clipboard = document
            .copy_selection_pixels(merged_visible)
            .ok_or_else(|| "The active Pixel selection is empty".to_string())?;
        let summary = clipboard.summary();
        self.clipboard = Some(clipboard);
        Ok(format!("Copied {summary}"))
    }

    pub(crate) fn cut_selection_to_clipboard(&mut self) -> Result<String, String> {
        let document = self
            .document
            .as_mut()
            .ok_or_else(|| "Open a Pixel Studio document before cutting".to_string())?;
        let clipboard = document
            .cut_selection_pixels()
            .ok_or_else(|| "The active Pixel selection is empty or its layer is locked".to_string())?;
        let summary = clipboard.summary();
        self.clipboard = Some(clipboard);
        self.refresh_texture();
        Ok(format!("Cut {summary}"))
    }

    pub(crate) fn paste_clipboard_into_selection(&mut self) -> Result<String, String> {
        let clipboard = self
            .clipboard
            .clone()
            .ok_or_else(|| "Pixel clipboard is empty".to_string())?;
        let document = self
            .document
            .as_mut()
            .ok_or_else(|| "Open a Pixel Studio document before pasting".to_string())?;
        let anchor = document.metadata.selection;
        if !document.paste_pixel_clipboard(&clipboard, anchor.x, anchor.y) {
            return Err("Paste did not change the active Pixel document".to_string());
        }
        self.refresh_texture();
        Ok(format!(
            "Pasted {}x{} pixels at {}, {}",
            clipboard.width(), clipboard.height(), anchor.x, anchor.y
        ))
    }

    pub(crate) fn duplicate_selection(&mut self) -> Result<String, String> {
        let document = self
            .document
            .as_mut()
            .ok_or_else(|| "Open a Pixel Studio document before duplicating".to_string())?;
        let clipboard = document
            .duplicate_selection_pixels()
            .ok_or_else(|| "The active Pixel selection could not be duplicated".to_string())?;
        let summary = clipboard.summary();
        self.clipboard = Some(clipboard);
        self.refresh_texture();
        Ok(format!("Duplicated {summary}"))
    }

    pub(crate) fn open_promote_selection_wizard(&mut self) -> Result<String, String> {
        let document = self
            .document
            .as_ref()
            .ok_or_else(|| "Open a Pixel Studio document before promoting a selection".to_string())?;
        let clipboard = document
            .copy_selection_pixels(true)
            .ok_or_else(|| "The active Pixel selection is empty".to_string())?;
        let role = PixelAssetRole::from_document(document);
        let kind = match role {
            PixelAssetRole::RepeatTexture => {
                if clipboard.width() == document.metadata.grid.cell_width
                    && clipboard.height() == document.metadata.grid.cell_height
                {
                    PixelDocumentKind::Tile
                } else {
                    PixelDocumentKind::Tilesheet
                }
            }
            PixelAssetRole::Character => PixelDocumentKind::CharacterLayer,
            PixelAssetRole::Object => PixelDocumentKind::ObjectSprite,
            PixelAssetRole::General => PixelDocumentKind::FreeCanvas,
        };
        let suggested_name = format!("{} Selection", document.metadata.display_name);
        self.new_dialog = Some(NewPixelDialogState::for_promotion(clipboard, kind, suggested_name));
        Ok("Promote Selection wizard opened; choose the reusable asset type and name".to_string())
    }

    pub(crate) fn cycle_new_kind(&mut self, direction: i32) {
        let Some(dialog) = self.new_dialog.as_mut() else {
            return;
        };
        let current = PixelDocumentKind::ALL
            .iter()
            .position(|kind| *kind == dialog.spec.kind)
            .unwrap_or(0);
        let len = PixelDocumentKind::ALL.len() as i32;
        let next = (current as i32 + direction).rem_euclid(len) as usize;
        dialog.select_kind(PixelDocumentKind::ALL[next]);
    }

    pub(crate) fn refresh_texture(&mut self) {
        let Some(document) = &self.document else {
            self.texture = None;
            return;
        };
        let pixel_count = u64::from(document.width()) * u64::from(document.height());
        if pixel_count > 4_194_304 {
            self.autosave_status = format!(
                "Live preview deferred for {}x{} document; save or frame a smaller asset",
                document.width(),
                document.height()
            );
            return;
        }
        match texture_from_document(document) {
            Ok(texture) => self.texture = Some(texture),
            Err(error) => {
                self.texture = None;
                self.autosave_status = format!("Pixel preview unavailable: {error}");
            }
        }
    }

    pub(crate) fn zoom(&self) -> f32 {
        ZOOM_LEVELS[self.zoom_index]
    }

    pub(crate) fn zoom_in(&mut self) {
        self.zoom_index = (self.zoom_index + 1).min(ZOOM_LEVELS.len() - 1);
    }

    pub(crate) fn zoom_out(&mut self) {
        self.zoom_index = self.zoom_index.saturating_sub(1);
    }

    pub(crate) fn zoom_one_to_one(&mut self) {
        self.zoom_index = ZOOM_LEVELS
            .iter()
            .enumerate()
            .min_by(|(_, left), (_, right)| {
                (*left - 1.0_f32)
                    .abs()
                    .partial_cmp(&(*right - 1.0_f32).abs())
                    .unwrap_or(std::cmp::Ordering::Equal)
            })
            .map(|(index, _)| index)
            .unwrap_or(0);
        self.pan = Vec2::ZERO;
    }

    pub(crate) fn frame_document(&mut self, canvas: Rect) {
        let Some(document) = &self.document else {
            return;
        };
        let fit = (canvas.w / document.width().max(1) as f32)
            .min(canvas.h / document.height().max(1) as f32)
            .clamp(ZOOM_LEVELS[0], ZOOM_LEVELS[ZOOM_LEVELS.len() - 1]);
        self.zoom_index = ZOOM_LEVELS
            .iter()
            .enumerate()
            .min_by(|(_, left), (_, right)| {
                (*left - fit)
                    .abs()
                    .partial_cmp(&(*right - fit).abs())
                    .unwrap_or(std::cmp::Ordering::Equal)
            })
            .map(|(index, _)| index)
            .unwrap_or(3);
        self.pan = Vec2::ZERO;
        self.needs_frame = false;
    }

    pub(crate) fn frame_selection(&mut self, canvas: Rect) {
        let Some(document) = &self.document else {
            return;
        };
        let selection = document.metadata.selection;
        if selection.is_empty() {
            self.frame_document(canvas);
            return;
        }
        let fit = ((canvas.w * 0.72) / selection.width.max(1) as f32)
            .min((canvas.h * 0.72) / selection.height.max(1) as f32)
            .clamp(ZOOM_LEVELS[0], ZOOM_LEVELS[ZOOM_LEVELS.len() - 1]);
        self.zoom_index = ZOOM_LEVELS
            .iter()
            .enumerate()
            .min_by(|(_, left), (_, right)| {
                (*left - fit)
                    .abs()
                    .partial_cmp(&(*right - fit).abs())
                    .unwrap_or(std::cmp::Ordering::Equal)
            })
            .map(|(index, _)| index)
            .unwrap_or(3);
        let zoom = self.zoom();
        let base_x = canvas.x + (canvas.w - document.width() as f32 * zoom) * 0.5;
        let base_y = canvas.y + (canvas.h - document.height() as f32 * zoom) * 0.5;
        let selection_center_x = (selection.x as f32 + selection.width as f32 * 0.5) * zoom;
        let selection_center_y = (selection.y as f32 + selection.height as f32 * 0.5) * zoom;
        self.pan = vec2(
            canvas.x + canvas.w * 0.5 - (base_x + selection_center_x),
            canvas.y + canvas.h * 0.5 - (base_y + selection_center_y),
        );
        self.needs_frame = false;
    }

    pub(crate) fn canvas_transform(&self, canvas: Rect) -> Option<SpriteCanvasTransform> {
        let document = self.document.as_ref()?;
        Some(SpriteCanvasTransform::new(
            canvas,
            document.width(),
            document.height(),
            self.zoom(),
            self.pan,
        ))
    }

    pub(crate) fn image_rect(&self, canvas: Rect) -> Option<Rect> {
        self.canvas_transform(canvas)
            .map(|transform| transform.image)
    }

    pub(crate) fn screen_to_pixel(&self, canvas: Rect, point: Vec2) -> Option<(u32, u32)> {
        self.canvas_transform(canvas)?.screen_to_pixel(point)
    }

    pub(crate) fn update_autosave(&mut self) -> Option<Result<String, String>> {
        if get_time() < self.next_autosave_at {
            return None;
        }
        self.next_autosave_at = get_time() + 10.0;
        let result = {
            let document = self.document.as_mut()?;
            if !document.dirty {
                return None;
            }
            let pixel_count = u64::from(document.width()) * u64::from(document.height());
            if pixel_count > 4_194_304 {
                self.autosave_status =
                    "Autosave deferred for large document; use Ctrl+S".to_string();
                return None;
            }
            document.autosave(repo_root_dir())
        };
        Some(match result {
            Ok(path) => {
                let message = format!("Autosaved recovery to {}", path.display());
                self.autosave_status = message.clone();
                Ok(message)
            }
            Err(error) => Err(error),
        })
    }

    pub(crate) fn target_code(&self) -> &'static str {
        match self.target_kind {
            AssetIntakeTargetKind::Tile => {
                TileKind::ALL[self.target_index % TileKind::ALL.len()].code()
            }
            AssetIntakeTargetKind::Object => {
                OBJECT_BRUSHES[self.target_index % OBJECT_BRUSHES.len()].code()
            }
        }
    }

    pub(crate) fn target_label(&self) -> &'static str {
        match self.target_kind {
            AssetIntakeTargetKind::Tile => {
                TileKind::ALL[self.target_index % TileKind::ALL.len()].label()
            }
            AssetIntakeTargetKind::Object => {
                OBJECT_BRUSHES[self.target_index % OBJECT_BRUSHES.len()].label()
            }
        }
    }
}

fn validate_editable_image(path: &Path) -> Result<(), String> {
    let (width, height) = image::image_dimensions(path)
        .map_err(|error| format!("failed to inspect {}: {error}", path.display()))?;
    validate_editable_dimensions(width, height)
}

fn validate_editable_dimensions(width: u32, height: u32) -> Result<(), String> {
    let pixels = u64::from(width) * u64::from(height);
    if width == 0 || height == 0 {
        return Err("image has zero width or height".to_string());
    }
    if width > MAX_PIXEL_EDIT_DIMENSION || height > MAX_PIXEL_EDIT_DIMENSION {
        return Err(format!(
            "image is {width}x{height}; Pixel Studio currently supports up to {MAX_PIXEL_EDIT_DIMENSION}px per side"
        ));
    }
    if pixels > MAX_PIXEL_EDIT_PIXELS {
        return Err(format!(
            "image is {width}x{height} ({pixels} pixels); create a cropped working copy before editing"
        ));
    }
    Ok(())
}

fn texture_from_document(document: &PixelDocument) -> Result<Texture2D, String> {
    validate_editable_dimensions(document.width(), document.height())?;
    let width = u16::try_from(document.width())
        .map_err(|_| "pixel document width exceeds texture limits".to_string())?;
    let height = u16::try_from(document.height())
        .map_err(|_| "pixel document height exceeds texture limits".to_string())?;
    let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        Texture2D::from_rgba8(width, height, document.rgba_bytes())
    }));
    let texture = result.map_err(|_| {
        format!(
            "GPU rejected the {}x{} preview texture; the document was not opened",
            document.width(),
            document.height()
        )
    })?;
    texture.set_filter(FilterMode::Nearest);
    Ok(texture)
}
