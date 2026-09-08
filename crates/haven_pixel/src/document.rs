use crate::layers::composite_layers;
use image::{Rgba, RgbaImage};
use serde::{Deserialize, Serialize};
use std::collections::VecDeque;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PixelTool {
    Pencil,
    Eraser,
    Fill,
    Eyedropper,
    Selection,
    MagicSelect,
    Line,
    Rectangle,
    Ellipse,
    Gradient,
    Blur,
    Smudge,
    Lighten,
    Darken,
}

impl PixelTool {
    pub const ALL: [Self; 14] = [
        Self::Pencil,
        Self::Eraser,
        Self::Fill,
        Self::Eyedropper,
        Self::Selection,
        Self::MagicSelect,
        Self::Line,
        Self::Rectangle,
        Self::Ellipse,
        Self::Gradient,
        Self::Blur,
        Self::Smudge,
        Self::Lighten,
        Self::Darken,
    ];

    pub fn label(self) -> &'static str {
        match self {
            Self::Pencil => "Pencil",
            Self::Eraser => "Eraser",
            Self::Fill => "Fill",
            Self::Eyedropper => "Pick",
            Self::Selection => "Select",
            Self::MagicSelect => "Magic Select",
            Self::Line => "Line",
            Self::Rectangle => "Rect",
            Self::Ellipse => "Ellipse",
            Self::Gradient => "Gradient",
            Self::Blur => "Blur",
            Self::Smudge => "Smudge",
            Self::Lighten => "Lighten",
            Self::Darken => "Darken",
        }
    }
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PixelBlendMode {
    #[default]
    Normal,
    Multiply,
    Screen,
    Add,
    Erase,
}

impl PixelBlendMode {
    pub const ALL: [Self; 5] = [
        Self::Normal,
        Self::Multiply,
        Self::Screen,
        Self::Add,
        Self::Erase,
    ];

    pub fn label(self) -> &'static str {
        match self {
            Self::Normal => "Normal",
            Self::Multiply => "Multiply",
            Self::Screen => "Screen",
            Self::Add => "Add",
            Self::Erase => "Erase",
        }
    }

    pub fn next(self) -> Self {
        let index = Self::ALL
            .iter()
            .position(|candidate| *candidate == self)
            .unwrap_or(0);
        Self::ALL[(index + 1) % Self::ALL.len()]
    }
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PixelAssetKind {
    Tile,
    Tilesheet,
    SpriteSheet,
    AnimationSheet,
    UiTexture,
    ObjectSprite,
    CharacterLayer,
    #[default]
    General,
}

impl PixelAssetKind {
    pub fn label(self) -> &'static str {
        match self {
            Self::Tile => "Tile",
            Self::Tilesheet => "Tilesheet",
            Self::SpriteSheet => "Sprite Sheet",
            Self::AnimationSheet => "Animation Sheet",
            Self::UiTexture => "UI Texture",
            Self::ObjectSprite => "Object Sprite",
            Self::CharacterLayer => "Character Layer",
            Self::General => "General",
        }
    }

    pub fn is_character(self) -> bool {
        matches!(
            self,
            Self::CharacterLayer | Self::SpriteSheet | Self::AnimationSheet
        )
    }
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PixelPreviewMode {
    Repeat,
    Character,
    Object,
    Ui,
    #[default]
    None,
}

impl PixelPreviewMode {
    pub fn label(self) -> &'static str {
        match self {
            Self::Repeat => "Repeat",
            Self::Character => "Character",
            Self::Object => "Object",
            Self::Ui => "UI",
            Self::None => "None",
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PixelGrid {
    pub cell_width: u32,
    pub cell_height: u32,
    pub offset_x: i32,
    pub offset_y: i32,
    #[serde(default)]
    pub spacing_x: u32,
    #[serde(default)]
    pub spacing_y: u32,
    pub subgrid: u32,
}

impl Default for PixelGrid {
    fn default() -> Self {
        Self {
            cell_width: 32,
            cell_height: 32,
            offset_x: 0,
            offset_y: 0,
            spacing_x: 0,
            spacing_y: 0,
            subgrid: 8,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PixelSelection {
    pub x: u32,
    pub y: u32,
    pub width: u32,
    pub height: u32,
}

impl PixelSelection {
    pub fn from_points(ax: u32, ay: u32, bx: u32, by: u32) -> Self {
        let x = ax.min(bx);
        let y = ay.min(by);
        Self {
            x,
            y,
            width: ax.max(bx) - x + 1,
            height: ay.max(by) - y + 1,
        }
    }

    pub fn is_empty(self) -> bool {
        self.width == 0 || self.height == 0
    }
}

/// In-memory, cross-document Pixel Studio clipboard payload.
///
/// Pixels remain a rectangular RGBA payload while provenance, source selection,
/// pivot offset, and license travel with the copy. This lets Pixel Studio copy
/// between documents and lets Promote Selection preserve the source asset's
/// authorship/license metadata without flattening that policy into the UI.
#[derive(Clone, Debug)]
pub struct PixelClipboard {
    pub image: RgbaImage,
    pub source_asset_id: String,
    pub source_display_name: String,
    pub source_layer_id: String,
    pub source_selection: PixelSelection,
    pub pivot_offset: [i32; 2],
    pub source_license: PixelLicense,
    pub merged_visible: bool,
}

impl PixelClipboard {
    pub fn width(&self) -> u32 {
        self.image.width()
    }

    pub fn height(&self) -> u32 {
        self.image.height()
    }

    pub fn is_empty(&self) -> bool {
        self.width() == 0 || self.height() == 0
    }

    pub fn summary(&self) -> String {
        format!(
            "{}x{} pixels from {}{}",
            self.width(),
            self.height(),
            self.source_display_name,
            if self.merged_visible { " (merged visible)" } else { "" }
        )
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PixelLicense {
    pub status: String,
    pub source_name: String,
    #[serde(default)]
    pub source_url: String,
    #[serde(default)]
    pub notes: String,
}

impl Default for PixelLicense {
    fn default() -> Self {
        Self {
            status: "unverified".to_string(),
            source_name: String::new(),
            source_url: String::new(),
            notes: String::new(),
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PixelLayerMetadata {
    pub id: String,
    pub name: String,
    #[serde(default = "default_true")]
    pub visible: bool,
    #[serde(default)]
    pub locked: bool,
    #[serde(default = "default_opacity")]
    pub opacity: u8,
    #[serde(default)]
    pub blend_mode: PixelBlendMode,
    #[serde(default)]
    pub image_path: String,
}

impl PixelLayerMetadata {
    pub fn new(id: impl Into<String>, name: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            name: name.into(),
            visible: true,
            locked: false,
            opacity: u8::MAX,
            blend_mode: PixelBlendMode::Normal,
            image_path: String::new(),
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PixelLayer {
    pub metadata: PixelLayerMetadata,
    pub image: RgbaImage,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PixelDocumentMetadata {
    pub schema: String,
    pub asset_id: String,
    pub display_name: String,
    pub source_path: String,
    pub output_path: String,
    pub width: u32,
    pub height: u32,
    pub grid: PixelGrid,
    #[serde(default)]
    pub asset_kind: PixelAssetKind,
    #[serde(default)]
    pub preview_mode: PixelPreviewMode,
    #[serde(default)]
    pub palette: Vec<[u8; 4]>,
    pub selection: PixelSelection,
    /// Exact immutable upstream source region used to seed a derived Pixel Studio
    /// working copy. Coordinates are in the original source image, not the
    /// cropped working document. Older documents leave this unset.
    #[serde(default)]
    pub source_region: Option<PixelSelection>,
    pub pivot: [i32; 2],
    pub visual_footprint: [i32; 4],
    pub collision_footprint: [i32; 4],
    pub interaction_footprint: [i32; 4],
    #[serde(default)]
    pub tags: Vec<String>,
    pub license: PixelLicense,
    #[serde(default)]
    pub active_layer_id: String,
    #[serde(default)]
    pub layers: Vec<PixelLayerMetadata>,
}

impl PixelDocumentMetadata {
    pub fn sidecar_path(&self) -> String {
        replace_extension(&self.output_path, "hhasset.json")
    }

    pub fn package_directory(&self) -> String {
        replace_extension(&self.output_path, "hhpixel")
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
struct PixelDocumentSnapshot {
    metadata: PixelDocumentMetadata,
    layers: Vec<PixelLayer>,
}

#[derive(Clone)]
pub struct PixelDocument {
    pub metadata: PixelDocumentMetadata,
    pub(crate) layers: Vec<PixelLayer>,
    pub(crate) composite: RgbaImage,
    undo: VecDeque<PixelDocumentSnapshot>,
    redo: VecDeque<PixelDocumentSnapshot>,
    undo_limit: usize,
    pub dirty: bool,
    pub recovered_from_autosave: bool,
}

impl PixelDocument {
    pub(crate) fn from_loaded_parts(
        mut metadata: PixelDocumentMetadata,
        mut layers: Vec<PixelLayer>,
        dirty: bool,
        recovered_from_autosave: bool,
    ) -> Self {
        if layers.is_empty() {
            layers.push(PixelLayer {
                metadata: PixelLayerMetadata::new("layer_001", "Base"),
                image: RgbaImage::from_pixel(
                    metadata.width.max(1),
                    metadata.height.max(1),
                    Rgba([0, 0, 0, 0]),
                ),
            });
        }
        metadata.width = layers[0].image.width();
        metadata.height = layers[0].image.height();
        if metadata.active_layer_id.is_empty()
            || !layers
                .iter()
                .any(|layer| layer.metadata.id == metadata.active_layer_id)
        {
            metadata.active_layer_id = layers.last().unwrap().metadata.id.clone();
        }
        metadata.layers = layers.iter().map(|layer| layer.metadata.clone()).collect();
        let composite = composite_layers(&layers, metadata.width, metadata.height);
        Self {
            metadata,
            layers,
            composite,
            undo: VecDeque::new(),
            redo: VecDeque::new(),
            undo_limit: 64,
            dirty,
            recovered_from_autosave,
        }
    }

    pub fn from_rgba(width: u32, height: u32, display_name: impl Into<String>) -> Self {
        let display_name = display_name.into();
        let stem = slugify(&display_name);
        let metadata = PixelDocumentMetadata {
            schema: "havenwild.pixel_document.v0_3".to_string(),
            asset_id: format!("pixel/{stem}"),
            display_name,
            source_path: String::new(),
            output_path: format!("assets/source/original/pixel_studio/{stem}.png"),
            width: width.max(1),
            height: height.max(1),
            grid: PixelGrid::default(),
            asset_kind: PixelAssetKind::General,
            preview_mode: PixelPreviewMode::None,
            palette: Vec::new(),
            selection: PixelSelection {
                x: 0,
                y: 0,
                width: width.clamp(1, 32),
                height: height.clamp(1, 32),
            },
            source_region: None,
            pivot: [16, 28],
            visual_footprint: [0, 0, 1, 1],
            collision_footprint: [0, 0, 1, 1],
            interaction_footprint: [0, 0, 1, 1],
            tags: Vec::new(),
            license: PixelLicense {
                status: "project_owned".to_string(),
                source_name: "Havenwild Pixel Studio".to_string(),
                source_url: String::new(),
                notes: "Created in project".to_string(),
            },
            active_layer_id: "layer_001".to_string(),
            layers: Vec::new(),
        };
        Self::from_loaded_parts(
            metadata,
            vec![PixelLayer {
                metadata: PixelLayerMetadata::new("layer_001", "Base"),
                image: RgbaImage::from_pixel(width.max(1), height.max(1), Rgba([0, 0, 0, 0])),
            }],
            true,
            false,
        )
    }

    pub fn width(&self) -> u32 {
        self.composite.width()
    }

    pub fn height(&self) -> u32 {
        self.composite.height()
    }

    pub fn rgba_bytes(&self) -> &[u8] {
        self.composite.as_raw()
    }

    pub fn layers(&self) -> &[PixelLayer] {
        &self.layers
    }

    pub fn layer_count(&self) -> usize {
        self.layers.len()
    }

    pub fn active_layer_index(&self) -> usize {
        self.layers
            .iter()
            .position(|layer| layer.metadata.id == self.metadata.active_layer_id)
            .unwrap_or_else(|| self.layers.len().saturating_sub(1))
    }

    pub fn active_layer(&self) -> &PixelLayer {
        &self.layers[self.active_layer_index()]
    }

    pub fn active_layer_mut(&mut self) -> &mut PixelLayer {
        let index = self.active_layer_index();
        &mut self.layers[index]
    }

    pub fn select_layer(&mut self, index: usize) -> bool {
        let Some(layer) = self.layers.get(index) else {
            return false;
        };
        self.metadata.active_layer_id = layer.metadata.id.clone();
        true
    }

    pub fn can_edit_active_layer(&self) -> bool {
        !self.active_layer().metadata.locked
    }

    pub fn begin_edit(&mut self) {
        let snapshot = self.snapshot();
        if self.undo.back().is_some_and(|last| last == &snapshot) {
            return;
        }
        self.undo.push_back(snapshot);
        while self.undo.len() > self.undo_limit {
            self.undo.pop_front();
        }
        self.redo.clear();
    }

    pub fn undo(&mut self) -> bool {
        let Some(previous) = self.undo.pop_back() else {
            return false;
        };
        self.redo.push_back(self.snapshot());
        self.restore(previous);
        self.dirty = true;
        true
    }

    pub fn redo(&mut self) -> bool {
        let Some(next) = self.redo.pop_back() else {
            return false;
        };
        self.undo.push_back(self.snapshot());
        self.restore(next);
        self.dirty = true;
        true
    }

    pub fn color_at(&self, x: u32, y: u32) -> [u8; 4] {
        if x < self.width() && y < self.height() {
            self.composite.get_pixel(x, y).0
        } else {
            [0, 0, 0, 0]
        }
    }

    pub fn active_color_at(&self, x: u32, y: u32) -> [u8; 4] {
        if x < self.width() && y < self.height() {
            self.active_layer().image.get_pixel(x, y).0
        } else {
            [0, 0, 0, 0]
        }
    }

    pub fn set_pixel(&mut self, x: u32, y: u32, color: [u8; 4]) -> bool {
        if !self.can_edit_active_layer()
            || x >= self.width()
            || y >= self.height()
            || self.active_color_at(x, y) == color
        {
            return false;
        }
        self.active_layer_mut().image.put_pixel(x, y, Rgba(color));
        self.refresh_composite_pixel(x, y);
        self.dirty = true;
        true
    }

    pub fn flood_fill(&mut self, x: u32, y: u32, replacement: [u8; 4]) -> usize {
        if !self.can_edit_active_layer() || x >= self.width() || y >= self.height() {
            return 0;
        }
        let target = self.active_color_at(x, y);
        if target == replacement {
            return 0;
        }
        let width = self.width();
        let height = self.height();
        let mut queue = VecDeque::from([(x, y)]);
        let mut changed = 0usize;
        while let Some((px, py)) = queue.pop_front() {
            if self.active_color_at(px, py) != target {
                continue;
            }
            self.active_layer_mut()
                .image
                .put_pixel(px, py, Rgba(replacement));
            changed += 1;
            if px > 0 {
                queue.push_back((px - 1, py));
            }
            if py > 0 {
                queue.push_back((px, py - 1));
            }
            if px + 1 < width {
                queue.push_back((px + 1, py));
            }
            if py + 1 < height {
                queue.push_back((px, py + 1));
            }
        }
        if changed > 0 {
            self.refresh_composite();
            self.dirty = true;
        }
        changed
    }

    pub fn draw_line(&mut self, start: (u32, u32), end: (u32, u32), color: [u8; 4]) {
        let (mut x0, mut y0) = (start.0 as i32, start.1 as i32);
        let (x1, y1) = (end.0 as i32, end.1 as i32);
        let dx = (x1 - x0).abs();
        let sx = if x0 < x1 { 1 } else { -1 };
        let dy = -(y1 - y0).abs();
        let sy = if y0 < y1 { 1 } else { -1 };
        let mut error = dx + dy;
        loop {
            if x0 >= 0 && y0 >= 0 {
                self.set_pixel(x0 as u32, y0 as u32, color);
            }
            if x0 == x1 && y0 == y1 {
                break;
            }
            let doubled = error * 2;
            if doubled >= dy {
                error += dy;
                x0 += sx;
            }
            if doubled <= dx {
                error += dx;
                y0 += sy;
            }
        }
    }

    pub fn draw_rectangle(&mut self, selection: PixelSelection, color: [u8; 4], filled: bool) {
        if selection.is_empty() || !self.can_edit_active_layer() {
            return;
        }
        let right = selection.x + selection.width - 1;
        let bottom = selection.y + selection.height - 1;
        for y in selection.y..=bottom.min(self.height().saturating_sub(1)) {
            for x in selection.x..=right.min(self.width().saturating_sub(1)) {
                if filled || x == selection.x || x == right || y == selection.y || y == bottom {
                    self.set_pixel(x, y, color);
                }
            }
        }
    }


    pub fn draw_ellipse(&mut self, selection: PixelSelection, color: [u8; 4], filled: bool) {
        if selection.is_empty() || !self.can_edit_active_layer() {
            return;
        }
        let x0 = selection.x.min(self.width().saturating_sub(1));
        let y0 = selection.y.min(self.height().saturating_sub(1));
        let x1 = (selection.x + selection.width.saturating_sub(1)).min(self.width().saturating_sub(1));
        let y1 = (selection.y + selection.height.saturating_sub(1)).min(self.height().saturating_sub(1));
        let cx = (x0 + x1) as f32 * 0.5;
        let cy = (y0 + y1) as f32 * 0.5;
        let rx = ((x1.saturating_sub(x0) + 1) as f32 * 0.5).max(0.5);
        let ry = ((y1.saturating_sub(y0) + 1) as f32 * 0.5).max(0.5);
        let edge = (1.5 / rx.max(ry)).max(0.02);
        for y in y0..=y1 {
            for x in x0..=x1 {
                let dx = (x as f32 + 0.5 - cx) / rx;
                let dy = (y as f32 + 0.5 - cy) / ry;
                let d = dx * dx + dy * dy;
                if (filled && d <= 1.0) || (!filled && (d - 1.0).abs() <= edge * 2.0) {
                    self.set_pixel(x, y, color);
                }
            }
        }
    }

    pub fn magic_select_contiguous(&mut self, x: u32, y: u32) -> PixelSelection {
        if x >= self.width() || y >= self.height() {
            return PixelSelection::default();
        }
        let target = self.active_color_at(x, y);
        let width = self.width();
        let height = self.height();
        let mut visited = vec![false; (width as usize).saturating_mul(height as usize)];
        let mut queue = VecDeque::from([(x, y)]);
        let (mut min_x, mut max_x, mut min_y, mut max_y) = (x, x, y, y);
        let mut any = false;
        while let Some((px, py)) = queue.pop_front() {
            let index = py as usize * width as usize + px as usize;
            if visited[index] || self.active_color_at(px, py) != target {
                continue;
            }
            visited[index] = true;
            any = true;
            min_x = min_x.min(px); max_x = max_x.max(px);
            min_y = min_y.min(py); max_y = max_y.max(py);
            if px > 0 { queue.push_back((px - 1, py)); }
            if py > 0 { queue.push_back((px, py - 1)); }
            if px + 1 < width { queue.push_back((px + 1, py)); }
            if py + 1 < height { queue.push_back((px, py + 1)); }
        }
        let selection = if any {
            PixelSelection { x: min_x, y: min_y, width: max_x - min_x + 1, height: max_y - min_y + 1 }
        } else { PixelSelection::default() };
        self.metadata.selection = selection;
        self.dirty = true;
        selection
    }

    pub fn blur_region(&mut self, selection: PixelSelection) -> usize {
        if selection.is_empty() || !self.can_edit_active_layer() { return 0; }
        let source = self.active_layer().image.clone();
        let x1 = (selection.x + selection.width).min(self.width());
        let y1 = (selection.y + selection.height).min(self.height());
        let mut changed = 0usize;
        for y in selection.y.min(self.height())..y1 {
            for x in selection.x.min(self.width())..x1 {
                let mut sum = [0u32; 4];
                let mut count = 0u32;
                for oy in -1i32..=1 {
                    for ox in -1i32..=1 {
                        let sx = x as i32 + ox;
                        let sy = y as i32 + oy;
                        if sx < 0 || sy < 0 || sx >= self.width() as i32 || sy >= self.height() as i32 { continue; }
                        let px = source.get_pixel(sx as u32, sy as u32).0;
                        for channel in 0..4 { sum[channel] += px[channel] as u32; }
                        count += 1;
                    }
                }
                let color = [
                    (sum[0] / count.max(1)) as u8,
                    (sum[1] / count.max(1)) as u8,
                    (sum[2] / count.max(1)) as u8,
                    (sum[3] / count.max(1)) as u8,
                ];
                if self.set_pixel(x, y, color) { changed += 1; }
            }
        }
        changed
    }

    pub fn adjust_luma_region(&mut self, selection: PixelSelection, delta: i16) -> usize {
        if selection.is_empty() || !self.can_edit_active_layer() { return 0; }
        let x1 = (selection.x + selection.width).min(self.width());
        let y1 = (selection.y + selection.height).min(self.height());
        let mut changed = 0usize;
        for y in selection.y.min(self.height())..y1 {
            for x in selection.x.min(self.width())..x1 {
                let mut color = self.active_color_at(x, y);
                if color[3] == 0 { continue; }
                for channel in 0..3 {
                    color[channel] = (color[channel] as i16 + delta).clamp(0, 255) as u8;
                }
                if self.set_pixel(x, y, color) { changed += 1; }
            }
        }
        changed
    }

    pub fn smudge_pixel(&mut self, from: (u32, u32), to: (u32, u32)) -> bool {
        if from.0 >= self.width() || from.1 >= self.height() || to.0 >= self.width() || to.1 >= self.height() {
            return false;
        }
        let source = self.active_color_at(from.0, from.1);
        let target = self.active_color_at(to.0, to.1);
        let mixed = [
            ((source[0] as u16 + target[0] as u16) / 2) as u8,
            ((source[1] as u16 + target[1] as u16) / 2) as u8,
            ((source[2] as u16 + target[2] as u16) / 2) as u8,
            ((source[3] as u16 + target[3] as u16) / 2) as u8,
        ];
        self.set_pixel(to.0, to.1, mixed)
    }

    pub fn draw_gradient(
        &mut self,
        selection: PixelSelection,
        start: (u32, u32),
        end: (u32, u32),
        foreground: [u8; 4],
        background: [u8; 4],
    ) -> usize {
        if selection.is_empty() || !self.can_edit_active_layer() { return 0; }
        let vx = end.0 as f32 - start.0 as f32;
        let vy = end.1 as f32 - start.1 as f32;
        let length2 = vx * vx + vy * vy;
        let x1 = (selection.x + selection.width).min(self.width());
        let y1 = (selection.y + selection.height).min(self.height());
        let mut changed = 0usize;
        for y in selection.y.min(self.height())..y1 {
            for x in selection.x.min(self.width())..x1 {
                let t = if length2 <= f32::EPSILON { 0.0 } else {
                    (((x as f32 - start.0 as f32) * vx + (y as f32 - start.1 as f32) * vy) / length2).clamp(0.0, 1.0)
                };
                let mut color = [0u8; 4];
                for channel in 0..4 {
                    color[channel] = (foreground[channel] as f32 * (1.0 - t) + background[channel] as f32 * t).round() as u8;
                }
                if self.set_pixel(x, y, color) { changed += 1; }
            }
        }
        changed
    }

    pub fn refresh_composite(&mut self) {
        self.composite = composite_layers(&self.layers, self.metadata.width, self.metadata.height);
    }

    /// Marks a procedurally assembled editor document as the clean baseline.
    /// This is used after reference layers are materialized on open so the UI
    /// does not report user modifications before the first authored edit.
    pub fn mark_clean(&mut self) {
        self.set_clean();
    }

    pub(crate) fn sync_layer_metadata(&mut self) {
        self.metadata.layers = self
            .layers
            .iter()
            .map(|layer| layer.metadata.clone())
            .collect();
    }

    pub(crate) fn set_clean(&mut self) {
        self.dirty = false;
        self.recovered_from_autosave = false;
    }

    fn snapshot(&self) -> PixelDocumentSnapshot {
        PixelDocumentSnapshot {
            metadata: self.metadata.clone(),
            layers: self.layers.clone(),
        }
    }

    fn restore(&mut self, snapshot: PixelDocumentSnapshot) {
        self.metadata = snapshot.metadata;
        self.layers = snapshot.layers;
        self.sync_layer_metadata();
        self.refresh_composite();
    }
}

pub(crate) fn slugify(value: &str) -> String {
    let mut output = String::new();
    let mut underscore = false;
    for character in value.chars() {
        if character.is_ascii_alphanumeric() {
            output.push(character.to_ascii_lowercase());
            underscore = false;
        } else if !underscore && !output.is_empty() {
            output.push('_');
            underscore = true;
        }
    }
    let value = output.trim_matches('_');
    if value.is_empty() {
        "pixel_asset".to_string()
    } else {
        value.to_string()
    }
}

fn replace_extension(path: &str, extension: &str) -> String {
    let path = std::path::Path::new(path);
    path.with_extension(extension)
        .to_string_lossy()
        .replace('\\', "/")
}

fn default_true() -> bool {
    true
}

fn default_opacity() -> u8 {
    u8::MAX
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fill_and_undo_are_deterministic() {
        let mut document = PixelDocument::from_rgba(4, 4, "test");
        document.begin_edit();
        assert_eq!(document.flood_fill(0, 0, [12, 34, 56, 255]), 16);
        assert_eq!(document.color_at(3, 3), [12, 34, 56, 255]);
        assert!(document.undo());
        assert_eq!(document.color_at(3, 3), [0, 0, 0, 0]);
        assert!(document.redo());
        assert_eq!(document.color_at(3, 3), [12, 34, 56, 255]);
    }

    #[test]
    fn magic_select_uses_contiguous_color_bounds() {
        let mut document = PixelDocument::from_rgba(5, 5, "magic");
        document.set_pixel(1, 1, [255, 0, 0, 255]);
        document.set_pixel(2, 1, [255, 0, 0, 255]);
        document.set_pixel(4, 4, [255, 0, 0, 255]);
        let selection = document.magic_select_contiguous(1, 1);
        assert_eq!(selection, PixelSelection { x: 1, y: 1, width: 2, height: 1 });
    }

    #[test]
    fn blur_lighten_and_gradient_are_undoable_pixel_edits() {
        let mut document = PixelDocument::from_rgba(4, 4, "effects");
        document.set_pixel(1, 1, [20, 40, 60, 255]);
        document.begin_edit();
        assert!(document.adjust_luma_region(PixelSelection { x: 1, y: 1, width: 1, height: 1 }, 20) > 0);
        assert_eq!(document.active_color_at(1, 1), [40, 60, 80, 255]);
        assert!(document.undo());
        assert_eq!(document.active_color_at(1, 1), [20, 40, 60, 255]);

        document.begin_edit();
        let changed = document.draw_gradient(
            PixelSelection { x: 0, y: 0, width: 4, height: 1 },
            (0, 0),
            (3, 0),
            [0, 0, 0, 255],
            [255, 255, 255, 255],
        );
        assert_eq!(changed, 4);
        assert_eq!(document.active_color_at(0, 0), [0, 0, 0, 255]);
        assert_eq!(document.active_color_at(3, 0), [255, 255, 255, 255]);
    }

    #[test]
    fn ellipse_draws_without_leaving_document_bounds() {
        let mut document = PixelDocument::from_rgba(8, 8, "ellipse");
        document.begin_edit();
        document.draw_ellipse(PixelSelection { x: 1, y: 1, width: 6, height: 6 }, [255, 0, 0, 255], false);
        assert!(document.rgba_bytes().chunks_exact(4).any(|pixel| pixel[3] != 0));
    }

    #[test]
    fn layer_operations_are_part_of_document_history() {
        let mut document = PixelDocument::from_rgba(4, 4, "layers");
        document.add_layer("Shading");
        assert_eq!(document.layer_count(), 2);
        document.begin_edit();
        document.set_pixel(1, 1, [20, 40, 60, 255]);
        assert!(document.undo());
        assert_eq!(document.color_at(1, 1), [0, 0, 0, 0]);
        assert!(document.undo());
        assert_eq!(document.layer_count(), 1);
    }

    #[test]
    fn exact_layer_reorder_preserves_intervening_order_and_active_identity() {
        let mut document = PixelDocument::from_rgba(4, 4, "reorder");
        document.add_layer("Middle");
        document.add_layer("Top");
        let top_id = document.active_layer().metadata.id.clone();
        assert_eq!(document.layers()[0].metadata.name, "Base");
        assert_eq!(document.layers()[1].metadata.name, "Middle");
        assert_eq!(document.layers()[2].metadata.name, "Top");
        assert!(document.move_active_layer_to(0));
        assert_eq!(document.layers()[0].metadata.id, top_id);
        assert_eq!(document.layers()[1].metadata.name, "Base");
        assert_eq!(document.layers()[2].metadata.name, "Middle");
        assert_eq!(document.active_layer().metadata.id, top_id);
    }

    #[test]
    fn layer_opacity_and_blend_mode_have_exact_setters() {
        let mut document = PixelDocument::from_rgba(4, 4, "layer controls");
        assert!(document.set_active_layer_opacity(127));
        assert_eq!(document.active_layer().metadata.opacity, 127);
        assert!(document.set_active_layer_blend_mode(PixelBlendMode::Multiply));
        assert_eq!(document.active_layer().metadata.blend_mode, PixelBlendMode::Multiply);
        assert!(!document.set_active_layer_blend_mode(PixelBlendMode::Multiply));
    }

    #[test]
    fn sidecar_and_package_paths_replace_png_extension() {
        let document = PixelDocument::from_rgba(32, 32, "test tile");
        assert_eq!(
            document.metadata.sidecar_path(),
            "assets/source/original/pixel_studio/test_tile.hhasset.json"
        );
        assert_eq!(
            document.metadata.package_directory(),
            "assets/source/original/pixel_studio/test_tile.hhpixel"
        );
    }

    #[test]
    fn transform_selection_nearest_moves_pixels_and_updates_bounds() {
        let mut document = PixelDocument::from_rgba(6, 6, "transform");
        document.metadata.selection = PixelSelection { x: 0, y: 0, width: 2, height: 2 };
        document.set_pixel(0, 0, [255, 0, 0, 255]);
        assert!(document.transform_selection_nearest(PixelSelection {
            x: 3,
            y: 2,
            width: 2,
            height: 2,
        }));
        assert_eq!(document.active_color_at(0, 0), [0, 0, 0, 0]);
        assert_eq!(document.active_color_at(3, 2), [255, 0, 0, 255]);
        assert_eq!(document.metadata.selection.x, 3);
        assert_eq!(document.metadata.selection.y, 2);
    }

    #[test]
    fn pixel_clipboard_copies_across_documents_and_selects_paste() {
        let mut source = PixelDocument::from_rgba(4, 4, "clipboard source");
        source.metadata.selection = PixelSelection { x: 1, y: 1, width: 2, height: 2 };
        source.set_pixel(1, 1, [200, 20, 30, 255]);
        source.set_pixel(2, 2, [30, 40, 220, 255]);
        let clipboard = source.copy_selection_pixels(false).unwrap();
        assert_eq!(clipboard.width(), 2);
        assert_eq!(clipboard.height(), 2);

        let mut destination = PixelDocument::from_rgba(6, 6, "clipboard destination");
        assert!(destination.paste_pixel_clipboard(&clipboard, 3, 2));
        assert_eq!(destination.active_color_at(3, 2), [200, 20, 30, 255]);
        assert_eq!(destination.active_color_at(4, 3), [30, 40, 220, 255]);
        assert_eq!(destination.metadata.selection, PixelSelection { x: 3, y: 2, width: 2, height: 2 });
    }

    #[test]
    fn cut_selection_is_one_undoable_pixel_edit() {
        let mut document = PixelDocument::from_rgba(4, 4, "clipboard cut");
        document.metadata.selection = PixelSelection { x: 1, y: 1, width: 1, height: 1 };
        document.set_pixel(1, 1, [90, 100, 110, 255]);
        let clipboard = document.cut_selection_pixels().unwrap();
        assert_eq!(clipboard.image.get_pixel(0, 0).0, [90, 100, 110, 255]);
        assert_eq!(document.active_color_at(1, 1), [0, 0, 0, 0]);
        assert!(document.undo());
        assert_eq!(document.active_color_at(1, 1), [90, 100, 110, 255]);
    }

    #[test]
    fn mirrored_selection_mirrors_pivot_when_pivot_belongs_to_selection() {
        let mut document = PixelDocument::from_rgba(8, 8, "mirror pivot");
        document.metadata.selection = PixelSelection { x: 2, y: 2, width: 4, height: 3 };
        document.metadata.pivot = [2, 3];
        document.flip_selection_horizontal();
        assert_eq!(document.metadata.pivot, [5, 3]);
        document.flip_selection_vertical();
        assert_eq!(document.metadata.pivot, [5, 3]);
    }

    #[test]
    fn transformed_selection_carries_internal_pivot() {
        let mut document = PixelDocument::from_rgba(12, 12, "transform pivot");
        document.metadata.selection = PixelSelection { x: 2, y: 2, width: 3, height: 3 };
        document.metadata.pivot = [3, 3];
        document.set_pixel(3, 3, [255, 255, 255, 255]);
        assert!(document.transform_selection_nearest(PixelSelection { x: 6, y: 5, width: 5, height: 5 }));
        assert_eq!(document.metadata.pivot, [8, 7]);
    }

    #[test]
    fn arbitrary_rotation_keeps_a_non_empty_pixel_selection() {
        let mut document = PixelDocument::from_rgba(8, 8, "rotate");
        document.metadata.selection = PixelSelection { x: 2, y: 2, width: 3, height: 2 };
        document.set_pixel(2, 2, [255, 255, 255, 255]);
        assert!(document.rotate_selection_degrees(45.0, [3.5, 3.0]));
        assert!(!document.metadata.selection.is_empty());
        assert!(document.metadata.selection.x < document.width());
        assert!(document.metadata.selection.y < document.height());
    }

    #[test]
    fn selection_normalizes_drag_direction() {
        assert_eq!(
            PixelSelection::from_points(8, 9, 2, 3),
            PixelSelection {
                x: 2,
                y: 3,
                width: 7,
                height: 7,
            }
        );
    }
}
