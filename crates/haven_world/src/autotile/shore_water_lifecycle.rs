use haven_core::{TavernMap, TileKind};

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct ShoreWaterLifecycleReport {
    pub deep_to_shallow: usize,
    pub shallow_to_deep: usize,
    pub dry_sand_to_wet: usize,
    pub stale_wet_to_dry: usize,
    pub generated_foam: usize,
    pub removed_stale_foam: usize,
    pub generated_river_mouths: usize,
    pub removed_stale_river_mouths: usize,
    pub unsupported_depth_topology_to_shallow: usize,
}

impl ShoreWaterLifecycleReport {
    pub fn total_mutations(self) -> usize {
        self.deep_to_shallow
            + self.shallow_to_deep
            + self.dry_sand_to_wet
            + self.stale_wet_to_dry
            + self.generated_foam
            + self.removed_stale_foam
            + self.generated_river_mouths
            + self.removed_stale_river_mouths
            + self.unsupported_depth_topology_to_shallow
    }

    pub fn status_line(self) -> String {
        format!(
            "shore lifecycle semantic reset: {} mutations (expected 0)",
            self.total_mutations()
        )
    }
}

/// Semantic water depth is now owned by PCG/editor-authored hydrology.
///
/// This compatibility entry point intentionally performs no terrain mutation.
/// Wet-sand, foam, mouth blending, shallow/deep transitions, and unsupported
/// visual topology belong to presentation or explicit hydrology authoring, not
/// an automatic post-process that changes the gameplay map.
pub fn normalize_shore_water_lifecycle_region(
    map: &mut TavernMap,
    min_x: i32,
    min_y: i32,
    max_x: i32,
    max_y: i32,
    _passes: usize,
) -> ShoreWaterLifecycleReport {
    let _ = normalize_authored_depth_topology_region(map, min_x, min_y, max_x, max_y);
    ShoreWaterLifecycleReport::default()
}

/// Retained only for old internal/test callers. An unsupported authored visual
/// combination is a renderer/catalog diagnostic; it is never permission to
/// rewrite deep water into shallow water.
pub(super) fn normalize_authored_depth_topology_region(
    _map: &mut TavernMap,
    _min_x: i32,
    _min_y: i32,
    _max_x: i32,
    _max_y: i32,
) -> usize {
    0
}

#[allow(dead_code)]
pub(super) fn shallow_variant(tile: TileKind) -> TileKind {
    match tile {
        TileKind::OceanDeep | TileKind::OceanShallow => TileKind::OceanShallow,
        TileKind::RiverWater | TileKind::RiverMouthBlend => TileKind::RiverWater,
        _ => TileKind::ShallowWater,
    }
}

#[allow(dead_code)]
pub(super) fn deep_variant(tile: TileKind) -> TileKind {
    match tile {
        TileKind::OceanDeep | TileKind::OceanShallow => TileKind::OceanDeep,
        TileKind::RiverWater | TileKind::RiverMouthBlend => TileKind::RiverWater,
        _ => TileKind::DeepWater,
    }
}

#[allow(dead_code)]
pub(super) fn is_depth_water(tile: TileKind) -> bool {
    matches!(
        tile,
        TileKind::OceanDeep
            | TileKind::OceanShallow
            | TileKind::RiverWater
            | TileKind::RiverMouthBlend
            | TileKind::Water
            | TileKind::ShallowWater
            | TileKind::DeepWater
    )
}
