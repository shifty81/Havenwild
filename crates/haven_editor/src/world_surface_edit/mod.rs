mod address;
mod clipboard;
mod operations;

pub use address::{
    resolve_world_surface_cell, validate_world_surface_footprint, world_surface_bounds,
};
pub use clipboard::{copy_world_surface_rectangle, paste_world_surface_clipboard};
pub use operations::{
    adjust_world_structural_levels, flood_fill_world_surface, paint_world_surface_cells,
    paint_world_surface_rectangle, place_world_structural_connector,
    replace_world_surface_value, resolve_world_structural_connector_plan,
};

use haven_authoring::{GridPos, GridRect};
use haven_core::{ObjectFootprint, ObjectKind, ProjectSceneId, TileKind, ZoneKind, MAP_H, MAP_W};
use haven_world::scene_rectangles::SceneRectangleSpec;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct WorldSurfaceCellAddress {
    pub rectangle_index: usize,
    pub rectangle_id: String,
    pub scene_id: ProjectSceneId,
    pub global: GridPos,
    pub local: GridPos,
    pub partition_origin: GridPos,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum WorldSurfaceLayer {
    Terrain,
    Zones,
    StructuralLevels,
}

impl WorldSurfaceLayer {
    pub fn label(self) -> &'static str {
        match self {
            WorldSurfaceLayer::Terrain => "Terrain",
            WorldSurfaceLayer::Zones => "Zones/Lots",
            WorldSurfaceLayer::StructuralLevels => "Levels & Cliffs",
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum WorldSurfaceValue {
    Terrain(TileKind),
    Zone(ZoneKind),
    StructuralLevel(u8),
}

impl WorldSurfaceValue {
    pub fn layer(self) -> WorldSurfaceLayer {
        match self {
            WorldSurfaceValue::Terrain(_) => WorldSurfaceLayer::Terrain,
            WorldSurfaceValue::Zone(_) => WorldSurfaceLayer::Zones,
            WorldSurfaceValue::StructuralLevel(_) => WorldSurfaceLayer::StructuralLevels,
        }
    }

    pub fn label(self) -> String {
        match self {
            WorldSurfaceValue::Terrain(tile) => tile.label().to_string(),
            WorldSurfaceValue::Zone(zone) => zone.label().to_string(),
            WorldSurfaceValue::StructuralLevel(level) => format!("Structural Level {level}"),
        }
    }
}


#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum WorldStructuralConnectorKind {
    Ramp,
    Ladder,
}

impl WorldStructuralConnectorKind {
    pub const fn label(self) -> &'static str {
        match self {
            Self::Ramp => "Ramp 2→1→0",
            Self::Ladder => "Ladder",
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct WorldStructuralConnectorPlan {
    pub kind: WorldStructuralConnectorKind,
    pub host: GridPos,
    pub ramp_orientation: Option<haven_world::CertifiedRampOrientationV1>,
    pub footprint: GridRect,
    pub global_cells: Vec<GridPos>,
}

impl WorldStructuralConnectorPlan {
    pub fn summary(&self) -> String {
        format!(
            "{} at {},{} | {}x{} footprint",
            self.kind.label(),
            self.host.x,
            self.host.y,
            self.footprint.width(),
            self.footprint.height()
        )
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct WorldSurfaceEditOutcome {
    pub message: String,
    pub operation_count: usize,
    pub scene_count: usize,
    pub global_cells: Vec<GridPos>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct WorldSurfaceClipboardCell {
    pub offset: GridPos,
    pub tile: TileKind,
    pub height: u8,
    pub structural_level: u8,
    pub zone: ZoneKind,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct WorldSurfaceClipboardObject {
    pub offset: GridPos,
    pub kind: ObjectKind,
    pub footprint: ObjectFootprint,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct WorldSurfaceClipboardStamp {
    pub offset: GridPos,
    pub stamp_key: String,
    pub footprint: ObjectFootprint,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct WorldSurfaceClipboard {
    pub width: i32,
    pub height: i32,
    pub cells: Vec<WorldSurfaceClipboardCell>,
    pub objects: Vec<WorldSurfaceClipboardObject>,
    pub stamps: Vec<WorldSurfaceClipboardStamp>,
}

impl WorldSurfaceClipboard {
    pub fn is_empty(&self) -> bool {
        self.cells.is_empty() && self.objects.is_empty() && self.stamps.is_empty()
    }

    pub fn summary(&self) -> String {
        format!(
            "{}x{} | {} cells | {} objects | {} stamps",
            self.width,
            self.height,
            self.cells.len(),
            self.objects.len(),
            self.stamps.len()
        )
    }
}

pub fn rectangle_origin(rectangle: &SceneRectangleSpec) -> GridPos {
    GridPos {
        x: rectangle.grid_x.unwrap_or(0) * MAP_W as i32,
        y: rectangle.grid_y.unwrap_or(0) * MAP_H as i32,
    }
}

fn is_surface_rectangle(rectangle: &SceneRectangleSpec) -> bool {
    rectangle.grid_x.is_some()
        && rectangle.grid_y.is_some()
        && !rectangle.kind.starts_with("special_")
}

#[cfg(test)]
mod tests;
