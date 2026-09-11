//! Authored directional ramp assemblies from the LPC grass-top cliff family.
//!
//! The ramp art is already complete in the source sheets. Havenwild places the
//! 3x4 stamps at natural scale and never mirrors, rotates, crops, or stretches
//! them. The left/right variants are distinct authored assemblies.

use crate::{
    authored_terrain_provider::AuthoredSourceStamp,
    terrain_atlas_catalog_v2::{
        LPC_CLIFF_RAMP_DIRT_SOURCE_PATH_V2, LPC_CLIFF_RAMP_GRASS_SOURCE_PATH_V2,
        ATLAS_ID_LPC_CLIFF_RAMP_GRASS, LPC_CLIFF_RAMP_SAND_SOURCE_PATH_V2,
        LPC_CLIFF_RAMP_SNOW_SOURCE_PATH_V2,
    },
};
use haven_spatial::{offset_tile, TileCoord};

pub const LPC_CLIFF_RAMP_GRASS_SOURCE_PATH: &str = LPC_CLIFF_RAMP_GRASS_SOURCE_PATH_V2;
pub const LPC_CLIFF_RAMP_DIRT_SOURCE_PATH: &str = LPC_CLIFF_RAMP_DIRT_SOURCE_PATH_V2;
pub const LPC_CLIFF_RAMP_SAND_SOURCE_PATH: &str = LPC_CLIFF_RAMP_SAND_SOURCE_PATH_V2;
pub const LPC_CLIFF_RAMP_SNOW_SOURCE_PATH: &str = LPC_CLIFF_RAMP_SNOW_SOURCE_PATH_V2;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum LpcDirectionalCliffRampRole {
    /// Green corridor climbs from lower-left toward upper-right.
    RiseRight,
    /// Green corridor climbs from lower-right toward upper-left.
    RiseLeft,
}

impl LpcDirectionalCliffRampRole {
    pub const fn atlas_id(self) -> &'static str {
        let _ = self;
        ATLAS_ID_LPC_CLIFF_RAMP_GRASS
    }

    pub const fn source_stamp(self) -> AuthoredSourceStamp {
        match self {
            // Catalogued in the project source as the complete authored left
            // and right 3x4 directional ramp assemblies.
            Self::RiseRight => AuthoredSourceStamp::new(3, 5, 3, 4),
            Self::RiseLeft => AuthoredSourceStamp::new(6, 5, 3, 4),
        }
    }

    /// Canonical source-authoritative ramp placement relative to the structural
    /// owner. H20 visual acceptance moved the complete 3x4 authored stamp one
    /// full row down from the older W7 contract: one cell left, same owner Y.
    ///
    /// Do not fold the terrain tuple's +0.5/+0.5 presentation correction into
    /// this structural anchor. Terrain intersections and structural hosts are
    /// distinct coordinate contracts.
    pub const fn host_anchor_offset(self) -> (i8, i8) {
        let _ = self;
        (-1, 0)
    }

    /// Typed owner -> authored stamp origin. Runtime/editor consumers can use
    /// this instead of reimplementing the offset arithmetic.
    pub const fn stamp_origin(self, structural_owner: TileCoord) -> TileCoord {
        offset_tile(structural_owner, self.host_anchor_offset())
    }
}

/// Exact connected contour modules from the same LPC grass-top cliff family.
/// These are not generated substitutes: each role returns a complete authored
/// source span placed at natural 32px cell scale.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum LpcCliffContourStampRole {
    /// Repeatable interior row for a one-cell-wide north/south ridge. The
    /// center world cell remains walkable plateau; the authored left/right
    /// cliff flanks occupy the adjacent visual cells.
    VerticalRidgeMiddle,
}

impl LpcCliffContourStampRole {
    pub const fn atlas_id(self) -> &'static str {
        let _ = self;
        ATLAS_ID_LPC_CLIFF_RAMP_GRASS
    }

    pub const fn source_stamp(self) -> AuthoredSourceStamp {
        match self {
            Self::VerticalRidgeMiddle => AuthoredSourceStamp::new(8, 2, 3, 1),
        }
    }

    pub const fn host_anchor_offset(self) -> (i8, i8) {
        let _ = self;
        (-1, 0)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn directional_ramps_are_complete_natural_scale_3x4_stamps() {
        assert_eq!(
            LpcDirectionalCliffRampRole::RiseRight.atlas_id(),
            ATLAS_ID_LPC_CLIFF_RAMP_GRASS
        );
        assert_eq!(
            LpcDirectionalCliffRampRole::RiseRight.source_stamp(),
            AuthoredSourceStamp::new(3, 5, 3, 4)
        );
        assert_eq!(
            LpcDirectionalCliffRampRole::RiseLeft.source_stamp(),
            AuthoredSourceStamp::new(6, 5, 3, 4)
        );
        assert_eq!(
            LpcDirectionalCliffRampRole::RiseRight.host_anchor_offset(),
            (-1, 0)
        );
        assert_eq!(
            LpcDirectionalCliffRampRole::RiseLeft.host_anchor_offset(),
            (-1, 0)
        );
    }

    #[test]
    fn directional_ramp_visual_rows_use_same_y_structural_owner_contract() {
        let owner = TileCoord::new(10, 20);
        for role in [
            LpcDirectionalCliffRampRole::RiseRight,
            LpcDirectionalCliffRampRole::RiseLeft,
        ] {
            let origin = role.stamp_origin(owner);
            let stamp = role.source_stamp();
            assert_eq!(origin, TileCoord::new(9, 20));
            assert_ne!(origin, TileCoord::new(9, 19));
            assert_eq!(stamp.height_cells, 4);
            assert_eq!(origin.y + i32::from(stamp.height_cells) - 1, 23);
        }
    }

    #[test]
    fn vertical_ridge_middle_is_an_exact_three_cell_authored_row() {
        assert_eq!(
            LpcCliffContourStampRole::VerticalRidgeMiddle.source_stamp(),
            AuthoredSourceStamp::new(8, 2, 3, 1)
        );
        assert_eq!(
            LpcCliffContourStampRole::VerticalRidgeMiddle.host_anchor_offset(),
            (-1, 0)
        );
    }
}
