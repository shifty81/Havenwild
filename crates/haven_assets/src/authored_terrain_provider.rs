//! Shared source-authored terrain/provider primitives.
//!
//! Havenwild resolves semantic topology first and then asks an authored source
//! provider for an existing 32x32 cell or natural-scale multi-cell stamp. This
//! module intentionally has no image synthesis, crop, mirror, stretch, or
//! rotation API: if a provider cannot name authored source cells for a role,
//! the role remains unresolved until the source catalog/world topology is fixed.

use crate::{
    lpc_mapped_terrain::{
        canonical_corner_tuple_for_map_tile, lpc_mapped_terrain_exact_entry_for_map,
        lpc_mapped_terrain_runtime_entry_for_map, lpc_mapped_terrain_transition_entry_for_map,
        CanonicalCornerTuple, LpcMappedTerrainEntry,
    },
    terrain_atlas_catalog_v2::{ATLAS_ID_V7_MAPPED, V7_MAPPED_ATLAS_PATH},
};
use haven_core::TavernMap;

pub const AUTHORED_TERRAIN_CELL_PX: u16 = 32;
pub const AUTHORED_SURFACE_DRAW_PLAN_V2_SCHEMA: &str = "havenwild.authored_surface_draw_plan.v2";

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct AuthoredSourceCell {
    pub column: u8,
    pub row: u8,
}

impl AuthoredSourceCell {
    pub const fn new(column: u8, row: u8) -> Self {
        Self { column, row }
    }

    pub const fn x_px(self) -> u16 {
        self.column as u16 * AUTHORED_TERRAIN_CELL_PX
    }

    pub const fn y_px(self) -> u16 {
        self.row as u16 * AUTHORED_TERRAIN_CELL_PX
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct AuthoredSourceStamp {
    pub column: u8,
    pub row: u8,
    pub width_cells: u8,
    pub height_cells: u8,
}

impl AuthoredSourceStamp {
    pub const fn new(column: u8, row: u8, width_cells: u8, height_cells: u8) -> Self {
        Self {
            column,
            row,
            width_cells,
            height_cells,
        }
    }

    pub const fn width_px(self) -> u16 {
        self.width_cells as u16 * AUTHORED_TERRAIN_CELL_PX
    }

    pub const fn height_px(self) -> u16 {
        self.height_cells as u16 * AUTHORED_TERRAIN_CELL_PX
    }
}

/// Exact V7 source selections for one rendered terrain location. Base and
/// transition remain separate because V7 mixed corner tuples are drawn on the
/// intersection-aligned transition lane while the gameplay cell keeps its pure
/// semantic owner fill.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct AuthoredSurfaceResolution {
    pub base: Option<LpcMappedTerrainEntry>,
    pub transition: Option<LpcMappedTerrainEntry>,
}

/// Explicit atlas-resolution state shared by runtime, editor and diagnostics.
/// `OwnerFillFallback` is not fabricated art: it means the semantic owner fill
/// remains visible while the unsupported mixed tuple is routed to authoring.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum AuthoredSurfaceResolutionStatusV2 {
    ExactTuple,
    OwnerFillFallback,
    Unmapped,
}

/// Provider-facing visual plan for one V7 render location. This is the first
/// atlas-level record that editor and runtime can both consume directly. It
/// carries stable atlas identity plus the exact tuple that produced the draw,
/// while gameplay/collision authority stays in `haven_world::SurfaceTerrainRecipeV1`.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct AuthoredSurfaceDrawPlanV2 {
    pub atlas_id: &'static str,
    pub atlas_path: &'static str,
    pub tuple: Option<CanonicalCornerTuple>,
    pub status: AuthoredSurfaceResolutionStatusV2,
    pub base: Option<LpcMappedTerrainEntry>,
    pub transition: Option<LpcMappedTerrainEntry>,
}

impl AuthoredSurfaceDrawPlanV2 {
    pub const fn is_exact(self) -> bool {
        matches!(self.status, AuthoredSurfaceResolutionStatusV2::ExactTuple)
    }

    pub const fn has_any_authored_pixels(self) -> bool {
        self.base.is_some() || self.transition.is_some()
    }
}

pub fn resolve_authored_v7_surface_draw_plan_v2(
    map: &TavernMap,
    x: i32,
    y: i32,
) -> AuthoredSurfaceDrawPlanV2 {
    let tuple = canonical_corner_tuple_for_map_tile(map, x, y);
    let exact = lpc_mapped_terrain_exact_entry_for_map(map, x, y);
    let base = lpc_mapped_terrain_runtime_entry_for_map(map, x, y);
    let transition = lpc_mapped_terrain_transition_entry_for_map(map, x, y);
    let status = if exact.is_some() {
        AuthoredSurfaceResolutionStatusV2::ExactTuple
    } else if base.is_some() {
        AuthoredSurfaceResolutionStatusV2::OwnerFillFallback
    } else {
        AuthoredSurfaceResolutionStatusV2::Unmapped
    };

    AuthoredSurfaceDrawPlanV2 {
        atlas_id: ATLAS_ID_V7_MAPPED,
        atlas_path: V7_MAPPED_ATLAS_PATH,
        tuple,
        status,
        base,
        transition,
    }
}

pub fn resolve_authored_v7_surface_for_map(
    map: &TavernMap,
    x: i32,
    y: i32,
) -> AuthoredSurfaceResolution {
    let plan = resolve_authored_v7_surface_draw_plan_v2(map, x, y);
    AuthoredSurfaceResolution {
        base: plan.base,
        transition: plan.transition,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use haven_core::TileKind;

    #[test]
    fn source_cells_are_always_whole_32px_units() {
        let cell = AuthoredSourceCell::new(3, 7);
        assert_eq!(cell.x_px(), 96);
        assert_eq!(cell.y_px(), 224);
        let stamp = AuthoredSourceStamp::new(1, 6, 3, 3);
        assert_eq!(stamp.width_px(), 96);
        assert_eq!(stamp.height_px(), 96);
    }

    #[test]
    fn v2_draw_plan_keeps_stable_atlas_identity() {
        let map = TavernMap::empty_with(TileKind::Grass);
        let plan = resolve_authored_v7_surface_draw_plan_v2(&map, 4, 4);
        assert_eq!(plan.atlas_id, ATLAS_ID_V7_MAPPED);
        assert_eq!(plan.atlas_path, V7_MAPPED_ATLAS_PATH);
        assert!(plan.is_exact());
        assert!(plan.base.is_some());
    }

    #[test]
    fn legacy_resolution_is_a_projection_of_v2_plan() {
        let map = TavernMap::empty_with(TileKind::Sand);
        let plan = resolve_authored_v7_surface_draw_plan_v2(&map, 4, 4);
        let legacy = resolve_authored_v7_surface_for_map(&map, 4, 4);
        assert_eq!(legacy.base, plan.base);
        assert_eq!(legacy.transition, plan.transition);
    }
}
