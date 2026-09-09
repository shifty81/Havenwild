//! Havenwild-owned 2D spatial-query seam.
//!
//! The initial vector-backed index keeps project types independent of an OSS
//! implementation. rstar/geo/parry2d can replace the backend without changing
//! authored world, selection or save schemas.

use serde::{Deserialize, Serialize};


/// Canonical semantic tile coordinate. This identifies the owner cell only;
/// presentation anchors are resolved explicitly through [`TileAnchor`].
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct TileCoord {
    pub x: i32,
    pub y: i32,
}

impl TileCoord {
    pub const fn new(x: i32, y: i32) -> Self {
        Self { x, y }
    }
}

/// Named tile-space anchors used by Havenwild placement systems.
///
/// Several anchors intentionally resolve to the same numeric point today. The
/// semantic distinction prevents a terrain-intersection rule from silently
/// leaking into structural, object, actor, or editor placement code later.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub enum TileAnchor {
    /// Ordinary terrain/structural owner-cell origin.
    CellTopLeft,
    /// Center of one semantic 1x1 owner cell.
    CellCenter,
    /// Authored corner-tuple/Wang presentation origin. This is the explicit
    /// dual-tile correction that moves presentation half a tile down/right
    /// instead of leaving it at the semantic owner's upper-left corner.
    TerrainTuplePresentationOrigin,
    /// Bottom-center physical root of a one-cell footprint.
    CellBottomCenterFoot,
    /// Structural owner origin; semantically distinct from generic terrain.
    StructuralHost,
    /// Structural receiver-cell origin used by projected faces/connectors.
    StructuralReceiver,
}

pub const TERRAIN_TUPLE_PRESENTATION_OFFSET_TILES: f32 = 0.5;

/// Resolve a named anchor in tile units. No pixel-size assumption lives here.
pub const fn tile_anchor_tiles(tile: TileCoord, anchor: TileAnchor) -> [f32; 2] {
    let x = tile.x as f32;
    let y = tile.y as f32;
    match anchor {
        TileAnchor::CellTopLeft | TileAnchor::StructuralHost | TileAnchor::StructuralReceiver => {
            [x, y]
        }
        TileAnchor::CellCenter => [x + 0.5, y + 0.5],
        TileAnchor::TerrainTuplePresentationOrigin => [
            x + TERRAIN_TUPLE_PRESENTATION_OFFSET_TILES,
            y + TERRAIN_TUPLE_PRESENTATION_OFFSET_TILES,
        ],
        TileAnchor::CellBottomCenterFoot => [x + 0.5, y + 1.0],
    }
}

/// Apply a structural/authoring offset to an owner tile without introducing
/// implicit half-tile or pixel corrections.
pub const fn offset_tile(tile: TileCoord, offset: (i8, i8)) -> TileCoord {
    TileCoord::new(tile.x + offset.0 as i32, tile.y + offset.1 as i32)
}

/// Canonical bottom-center root for an integer tile rectangle.
///
/// Object/stamp rendering, selection and depth sorting can share this helper so
/// multi-cell footprints never fall back to their upper-left owner cell.
pub const fn tile_rect_bottom_center_tiles(
    x: i32,
    y: i32,
    width: i32,
    height: i32,
) -> [f32; 2] {
    [
        x as f32 + width as f32 * 0.5,
        (y + height) as f32,
    ]
}

#[derive(Clone, Copy, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Aabb2 {
    pub min: [f32; 2],
    pub max: [f32; 2],
}

impl Aabb2 {
    pub fn intersects(self, other: Self) -> bool {
        self.min[0] <= other.max[0]
            && self.max[0] >= other.min[0]
            && self.min[1] <= other.max[1]
            && self.max[1] >= other.min[1]
    }
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SpatialEntry {
    pub id: String,
    pub bounds: Aabb2,
}

#[derive(Clone, Debug, Default)]
pub struct SpatialIndex {
    entries: Vec<SpatialEntry>,
}

impl SpatialIndex {
    pub fn rebuild(entries: Vec<SpatialEntry>) -> Self {
        Self { entries }
    }

    pub fn query(&self, bounds: Aabb2) -> Vec<&SpatialEntry> {
        self.entries
            .iter()
            .filter(|entry| entry.bounds.intersects(bounds))
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn query_returns_intersecting_entries() {
        let index = SpatialIndex::rebuild(vec![SpatialEntry {
            id: "tree".to_string(),
            bounds: Aabb2 { min: [0.0, 0.0], max: [2.0, 2.0] },
        }]);
        assert_eq!(index.query(Aabb2 { min: [1.0, 1.0], max: [3.0, 3.0] }).len(), 1);
    }

    #[test]
    fn dual_tile_terrain_presentation_never_falls_back_to_owner_top_left() {
        let tile = TileCoord::new(7, 11);
        assert_eq!(tile_anchor_tiles(tile, TileAnchor::CellTopLeft), [7.0, 11.0]);
        assert_eq!(
            tile_anchor_tiles(tile, TileAnchor::TerrainTuplePresentationOrigin),
            [7.5, 11.5]
        );
    }

    #[test]
    fn structural_offsets_do_not_inherit_terrain_half_tile_correction() {
        let owner = TileCoord::new(10, 20);
        assert_eq!(offset_tile(owner, (-1, 0)), TileCoord::new(9, 20));
        assert_eq!(
            tile_anchor_tiles(owner, TileAnchor::StructuralHost),
            [10.0, 20.0]
        );
    }

    #[test]
    fn multi_cell_foot_is_bottom_center_not_upper_left() {
        assert_eq!(tile_rect_bottom_center_tiles(4, 7, 3, 2), [5.5, 9.0]);
    }
}
