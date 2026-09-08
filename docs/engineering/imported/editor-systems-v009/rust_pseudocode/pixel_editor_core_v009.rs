// Havenwild V009 Pixel Editor Core Pseudocode

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum PixelEditorMode {
    SingleImage,
    TileAtlas,
    AnimationSheet,
    AutotileAuthoring,
    OverlayMask,
    CharacterLayer,
    UiSkin,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum PixelTool {
    Pencil,
    Eraser,
    Fill,
    Line,
    Rectangle,
    Ellipse,
    Eyedropper,
    Selection,
    MoveSelection,
    ReplaceColor,
    DitherBrush,
    SmudgeBlend,
    LightenDarken,
}

#[derive(Clone, Debug)]
pub struct PixelDocument {
    pub asset_id: String,
    pub image_size: UVec2,
    pub cell_size: UVec2,
    pub mode: PixelEditorMode,
    pub layers: Vec<PixelLayer>,
    pub palette: Vec<Rgba>,
    pub animations: Vec<AnimationStrip>,
    pub autotile_rules: Option<AutotileRules>,
    pub metadata_path: String,
    pub dirty: bool,
}

#[derive(Clone, Debug)]
pub struct PixelLayer {
    pub name: String,
    pub visible: bool,
    pub locked: bool,
    pub opacity: f32,
    pub pixels: Vec<Rgba>,
}

#[derive(Clone, Debug)]
pub enum AutotileMaskKind {
    CornerNwNeSeSw,
    CardinalNESW,
}

#[derive(Clone, Debug)]
pub struct AutotileRules {
    pub mask_kind: AutotileMaskKind,
    pub tile_family_name: String,
    pub preview_patch_size: UVec2,
}

#[derive(Clone, Debug)]
pub struct AnimationStrip {
    pub name: String,
    pub frame_indices: Vec<u32>,
    pub fps: f32,
    pub looped: bool,
}

pub struct PixelEditor {
    pub doc: PixelDocument,
    pub active_tool: PixelTool,
    pub zoom: u32,
    pub show_grid: bool,
    pub show_tile_grid: bool,
    pub onion_skin: bool,
}

impl PixelEditor {
    pub fn paint_pixel(&mut self, pos: IVec2, color: Rgba) {
        // Applies active layer edit and records undo patch through EditorCommandBus.
    }

    pub fn preview_autotile_patch(&self) {
        // Builds 3x3 or 5x5 visual preview from current tile family.
    }

    pub fn validate(&self) -> Vec<String> {
        let mut warnings = Vec::new();
        if self.doc.image_size.x % self.doc.cell_size.x != 0 {
            warnings.push("Image width is not divisible by cell width.".to_string());
        }
        if self.doc.image_size.y % self.doc.cell_size.y != 0 {
            warnings.push("Image height is not divisible by cell height.".to_string());
        }
        warnings
    }
}

#[derive(Clone, Copy, Debug)] pub struct UVec2 { pub x: u32, pub y: u32 }
#[derive(Clone, Copy, Debug)] pub struct IVec2 { pub x: i32, pub y: i32 }
#[derive(Clone, Copy, Debug)] pub struct Rgba { pub r: u8, pub g: u8, pub b: u8, pub a: u8 }
