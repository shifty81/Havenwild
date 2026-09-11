use haven_core::{SceneBiome, TavernMap, TileKind};

use super::family_neighbors;
pub use super::shore_water_lifecycle::{
    normalize_shore_water_lifecycle_region, ShoreWaterLifecycleReport,
};

/// Read-only shoreline observation. Rendering may use this adjacency information,
/// but world semantics are never rewritten merely to satisfy an atlas tuple.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct ShorelineCell {
    pub x: i32,
    pub y: i32,
    pub tile: TileKind,
    pub touches_water: bool,
    pub touches_land: bool,
}

/// Compatibility shape retained for project/editor callers while the old
/// coastline-normalization controls are retired.
///
/// All production defaults are deliberately disabled. PCG owns terrain material
/// and hydrology. Presentation consumes those semantics; it does not rewrite them.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct CoastlineGenerationProfile {
    pub cleanup_passes: usize,
    pub shallow_water_only: bool,
    pub repair_diagonal_contacts: bool,
    pub beach_band_width: usize,
    pub repair_unsupported_shapes: bool,
}

impl CoastlineGenerationProfile {
    pub const fn mainland_hydrology() -> Self {
        Self {
            cleanup_passes: 0,
            shallow_water_only: false,
            repair_diagonal_contacts: false,
            beach_band_width: 0,
            repair_unsupported_shapes: false,
        }
    }

    /// Kept only so old callers compile during the reset. It intentionally has
    /// the same semantics-preserving behavior as the production profile.
    pub const fn mainland_shallow_stabilization() -> Self {
        Self::mainland_hydrology()
    }
}

impl Default for CoastlineGenerationProfile {
    fn default() -> Self {
        Self::mainland_hydrology()
    }
}

/// Compatibility report retained for diagnostics/API stability.
///
/// Reset authority requires every field to remain zero for the shoreline pass:
/// the pass observes terrain but performs no semantic mutations.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct CoastlineCleanupReport {
    pub removed_water_speckles: usize,
    pub eroded_land_spikes: usize,
    pub shallow_water_band_tiles: usize,
    pub deep_water_tiles: usize,
    pub primary_shore_tiles: usize,
    pub secondary_shore_tiles: usize,
    pub unsupported_topology_cells: usize,
    pub unsupported_shapes_repaired: usize,
    pub preserved_structural_tiles: usize,
    pub lifecycle_mutations: usize,
}

impl CoastlineCleanupReport {
    pub fn total_mutations(self) -> usize {
        self.removed_water_speckles
            + self.eroded_land_spikes
            + self.shallow_water_band_tiles
            + self.deep_water_tiles
            + self.primary_shore_tiles
            + self.secondary_shore_tiles
            + self.unsupported_shapes_repaired
            + self.lifecycle_mutations
    }

    pub fn status_line(self) -> String {
        format!(
            "coast semantic reset: {} mutations (expected 0)",
            self.total_mutations()
        )
    }
}

pub fn analyze_shoreline_cell(map: &TavernMap, x: i32, y: i32) -> ShorelineCell {
    let tile = map.get(x, y);
    let neighbors = family_neighbors(map, x, y);
    ShorelineCell {
        x,
        y,
        tile,
        touches_water: neighbors.water_cardinal_mask() != 0,
        touches_land: neighbors.land_cardinal_mask() != 0,
    }
}

/// Legacy entry point retained as a semantics-preserving compatibility boundary.
///
/// Prior versions converted grass to sand/mud, created fixed-width beach bands,
/// eroded narrow land, removed water speckles, changed water depth, and rewrote
/// unsupported 2x2 contacts so rendering tables would fit. That policy is
/// retired. The renderer must now adapt to the authored world, not vice versa.
pub fn apply_coastline_tile_pass(
    _map: &mut TavernMap,
    _biome: SceneBiome,
) -> CoastlineCleanupReport {
    CoastlineCleanupReport::default()
}

pub fn apply_coastline_tile_pass_with_profile(
    _map: &mut TavernMap,
    _biome: SceneBiome,
    _profile: CoastlineGenerationProfile,
) -> CoastlineCleanupReport {
    CoastlineCleanupReport::default()
}

#[cfg(test)]
#[path = "shoreline_regression_tests.rs"]
mod depth_domain_regression_tests;

#[cfg(test)]
#[path = "shoreline_resolver_tests.rs"]
mod tests;
