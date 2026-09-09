//! Editor/runtime bridge for Havenwild Terrain Standard v1.
//!
//! Semantic `TileKind` values remain save and gameplay authority. This module
//! derives the four-corner visual tuple used by the exact authored transition
//! catalog and reports the cells dirtied by a semantic paint operation.

use haven_core::{TavernMap, TileKind};
use haven_spatial::{tile_anchor_tiles, TileAnchor, TileCoord};

use crate::{
    embedded_terrain_tuple_resolver, TerrainCornerTuple, TerrainTupleResolution,
    TerrainTupleResolver,
};

/// Corner-tuple terrain cells are authored around the intersection between four
/// semantic cell centers. A tuple sampled at `(x, y)` therefore renders half a
/// tile down and right from the semantic-cell origin. Both the native editor and
/// the runtime must use this same offset or painted terrain appears in the
/// upper-left corner of the highlighted cell.
pub const TERRAIN_TUPLE_RENDER_OFFSET_TILES: f32 =
    haven_spatial::TERRAIN_TUPLE_PRESENTATION_OFFSET_TILES;

/// World-space origin for the authored 32x32 corner-tuple tile sampled at
/// `(x, y)`. The returned units are terrain tiles rather than pixels.
pub const fn terrain_tuple_render_origin_tiles(x: i32, y: i32) -> (f32, f32) {
    let [draw_x, draw_y] = tile_anchor_tiles(
        TileCoord::new(x, y),
        TileAnchor::TerrainTuplePresentationOrigin,
    );
    (draw_x, draw_y)
}

/// Stable Standard-v1 ordinal used by the promoted TSX tuple catalog.
/// Exact presentation identity is intentionally resolved from TileKind here;
/// gameplay/topology `BaseTerrain` groups are too coarse for atlas truth.
pub const fn terrain_standard_ordinal(tile: TileKind) -> u16 {
    match tile {
        TileKind::Grass | TileKind::TallGrass | TileKind::GreenhouseZone => 5,
        TileKind::Dirt => 0,
        TileKind::Sand | TileKind::WetSand => 22,
        TileKind::PebbleShore => 9,
        TileKind::Road | TileKind::Bridge => 3,
        TileKind::StonePath => 26,
        TileKind::MountainPath => 2,
        TileKind::MountainRock => 19,
        TileKind::CaveFloor => 16,
        TileKind::TilledSoil | TileKind::Crop => 25,
        TileKind::WateredSoil | TileKind::MudBank => 15,
        TileKind::ShallowWater | TileKind::RiverMouthBlend => 32,
        TileKind::OceanShallow | TileKind::ShoreFoam => 33,
        TileKind::Water | TileKind::RiverWater => 28,
        TileKind::DeepWater | TileKind::OceanDeep => 29,
        TileKind::WoodFloor | TileKind::PlankFloor => 3,
        TileKind::StoneFloor | TileKind::BrickFloor => 20,
        TileKind::Wall | TileKind::CaveWall => 18,
        TileKind::Cliff => 19,
    }
}

pub const fn terrain_standard_code(tile: TileKind) -> &'static str {
    match terrain_standard_ordinal(tile) {
        0 => "Dirt_Brown", 2 => "Dirt_Roots", 3 => "Dirt_Tan", 5 => "Grass",
        9 => "Gravel_1", 15 => "Mud_Brown", 16 => "Mudstone_Brown",
        18 => "Rock_Black", 19 => "Rock_Dark", 20 => "Rock_Gray", 22 => "Sand",
        25 => "Soil", 26 => "Stone_Tan", 28 => "Water", 29 => "Water_Deep",
        32 => "Water_Shallows_Dirt", 33 => "Water_Shallows_Sand", _ => "Dirt_Tan",
    }
}

/// Tuple for the cell whose top-left semantic sample is `(x, y)`.
///
/// The corner order exactly matches the promoted TSX contract:
/// top-left, top-right, bottom-left, bottom-right.
pub fn semantic_tuple_at(map: &TavernMap, x: i32, y: i32) -> TerrainCornerTuple {
    TerrainCornerTuple::new(
        Some(terrain_standard_ordinal(map.get(x, y))),
        Some(terrain_standard_ordinal(map.get(x + 1, y))),
        Some(terrain_standard_ordinal(map.get(x, y + 1))),
        Some(terrain_standard_ordinal(map.get(x + 1, y + 1))),
    )
}

pub fn resolve_semantic_tuple_at(
    resolver: &TerrainTupleResolver,
    map: &TavernMap,
    x: i32,
    y: i32,
) -> TerrainTupleResolution {
    resolver.resolve(semantic_tuple_at(map, x, y))
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum TerrainTupleCompatibility {
    Compatible,
    UnlistedCombination,
}

/// Compatibility is derived from terrain-family pairs demonstrated by the
/// promoted tuple catalog. A multi-material junction may be contact-compatible
/// even when no single exact four-corner atlas cell exists for that signature.
pub fn terrain_tuple_compatibility(tuple: TerrainCornerTuple) -> TerrainTupleCompatibility {
    let Ok(resolver) = embedded_terrain_tuple_resolver() else {
        return TerrainTupleCompatibility::UnlistedCombination;
    };
    let mut ordinals = Vec::new();
    for ordinal in [
        tuple.top_left,
        tuple.top_right,
        tuple.bottom_left,
        tuple.bottom_right,
    ]
    .into_iter()
    .flatten()
    {
        if !ordinals.contains(&ordinal) {
            ordinals.push(ordinal);
        }
    }
    for first_index in 0..ordinals.len() {
        for second_index in first_index + 1..ordinals.len() {
            if !resolver.supports_material_pair(ordinals[first_index], ordinals[second_index]) {
                return TerrainTupleCompatibility::UnlistedCombination;
            }
        }
    }
    TerrainTupleCompatibility::Compatible
}

/// A semantic paint at `(x, y)` can affect the four tuple cells that share the
/// edited sample. This list is coordinate-only and can be wrapped/clamped by
/// the owning world topology before cache invalidation.
pub const fn tuple_cells_affected_by_semantic_edit(x: i32, y: i32) -> [(i32, i32); 4] {
    [(x - 1, y - 1), (x, y - 1), (x - 1, y), (x, y)]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn semantic_tuple_uses_the_canonical_corner_order() {
        let mut map = TavernMap::empty_with(TileKind::Grass);
        map.set(4, 3, TileKind::Sand);
        map.set(5, 3, TileKind::ShallowWater);
        map.set(4, 4, TileKind::Dirt);
        map.set(5, 4, TileKind::TilledSoil);

        let tuple = semantic_tuple_at(&map, 4, 3);
        assert_eq!(tuple.top_left, Some(22));
        assert_eq!(tuple.top_right, Some(32));
        assert_eq!(tuple.bottom_left, Some(0));
        assert_eq!(tuple.bottom_right, Some(25));
    }

    #[test]
    fn compatibility_reports_known_and_unlisted_combinations() {
        assert_eq!(
            terrain_tuple_compatibility(TerrainCornerTuple::new(
                Some(28),
                Some(33),
                Some(22),
                Some(22)
            )),
            TerrainTupleCompatibility::Compatible
        );
        assert_eq!(
            terrain_tuple_compatibility(TerrainCornerTuple::new(
                Some(26),
                Some(22),
                Some(5),
                Some(5)
            )),
            TerrainTupleCompatibility::Compatible
        );
        assert_eq!(
            terrain_tuple_compatibility(TerrainCornerTuple::new(
                Some(14),
                Some(5),
                Some(23),
                Some(28)
            )),
            TerrainTupleCompatibility::UnlistedCombination
        );
    }

    #[test]
    fn semantic_tile_reports_stable_standard_family_code() {
        assert_eq!(terrain_standard_code(TileKind::Grass), "Grass");
        assert_eq!(terrain_standard_code(TileKind::Sand), "Sand");
        assert_eq!(terrain_standard_code(TileKind::ShallowWater), "Water_Shallows_Dirt");
    }

    #[test]
    fn stone_path_grass_tuple_keeps_exact_stone_tan_presentation() {
        let mut map = TavernMap::empty_with(TileKind::StonePath);
        map.set(4, 3, TileKind::Grass);
        let tuple = semantic_tuple_at(&map, 4, 3);
        assert_eq!(tuple.signature(), "5,26,26,26");
    }

    #[test]
    fn semantic_edit_invalidates_only_the_four_sharing_tuple_cells() {
        assert_eq!(
            tuple_cells_affected_by_semantic_edit(10, 8),
            [(9, 7), (10, 7), (9, 8), (10, 8)]
        );
    }

    #[test]
    fn editor_and_runtime_share_the_embedded_exact_resolver() {
        let resolver = TerrainTupleResolver::embedded().expect("embedded tuple catalog");
        let map = TavernMap::empty_with(TileKind::Grass);
        let result = resolve_semantic_tuple_at(&resolver, &map, 2, 2);
        assert_eq!(result.selected_tile_id, Some(5));
        assert!(result.is_resolved());
    }

    #[test]
    fn corner_tuple_render_origin_is_half_a_tile_down_and_right() {
        assert_eq!(TERRAIN_TUPLE_RENDER_OFFSET_TILES, 0.5);
        assert_eq!(terrain_tuple_render_origin_tiles(7, 11), (7.5, 11.5));
        assert_ne!(terrain_tuple_render_origin_tiles(7, 11), (7.0, 11.0));
    }

    #[test]
    fn dual_tile_presentation_uses_shared_spatial_authority() {
        let [shared_x, shared_y] = tile_anchor_tiles(
            TileCoord::new(4, 9),
            TileAnchor::TerrainTuplePresentationOrigin,
        );
        assert_eq!(terrain_tuple_render_origin_tiles(4, 9), (shared_x, shared_y));
    }
}
