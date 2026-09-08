use haven_core::TILE_SIZE;
use haven_world::{
    water_render_mask::{
        WaterRenderMask, WATER_CORNER_NORTH_EAST, WATER_CORNER_NORTH_WEST,
        WATER_CORNER_SOUTH_EAST, WATER_CORNER_SOUTH_WEST, WATER_MASK_EAST,
        WATER_MASK_NORTH, WATER_MASK_SOUTH, WATER_MASK_WEST,
    },
    DiagonalDirection,
};
use macroquad::prelude::*;

const LPC_SOURCE_CELL_SIZE: f32 = 32.0;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct DirectLpcTransitionBlock {
    outer_col: u8,
    outer_row: u8,
    inner: Option<(u8, u8)>,
}

fn direct_lpc_transition_block(group: &str) -> Option<DirectLpcTransitionBlock> {
    let block = match group {
        "grass_over_dirt" => DirectLpcTransitionBlock {
            outer_col: 6,
            outer_row: 0,
            inner: Some((6, 3)),
        },
        "grass_over_sand" => DirectLpcTransitionBlock {
            outer_col: 6,
            outer_row: 5,
            inner: Some((6, 8)),
        },
        "grass_bank_over_shallow" => DirectLpcTransitionBlock {
            outer_col: 0,
            outer_row: 10,
            inner: Some((0, 13)),
        },
        "dirt_bank_over_shallow" => DirectLpcTransitionBlock {
            outer_col: 6,
            outer_row: 10,
            inner: Some((6, 13)),
        },
        "sand_bank_over_shallow" => DirectLpcTransitionBlock {
            outer_col: 0,
            outer_row: 20,
            inner: Some((3, 20)),
        },
        "shallow_rim_over_deep" => DirectLpcTransitionBlock {
            outer_col: 0,
            outer_row: 23,
            inner: Some((3, 23)),
        },
        "sand_over_wet_sand" => DirectLpcTransitionBlock {
            outer_col: 9,
            outer_row: 5,
            inner: Some((9, 8)),
        },
        "pebble_path_over_dirt" => DirectLpcTransitionBlock {
            outer_col: 9,
            outer_row: 0,
            inner: None,
        },
        _ => return None,
    };
    Some(block)
}

fn inner_cell(block: DirectLpcTransitionBlock, direction: DiagonalDirection) -> Option<(u8, u8)> {
    let (inner_col, inner_row) = block.inner?;
    Some(match direction {
        DiagonalDirection::NorthEast => (inner_col, inner_row + 1),
        DiagonalDirection::SouthEast => (inner_col, inner_row),
        DiagonalDirection::SouthWest => (inner_col + 1, inner_row),
        DiagonalDirection::NorthWest => (inner_col + 1, inner_row + 1),
    })
}

/// Select a complete authored cell from the LPC 3x3 shallow/deep block.
///
/// Deep water owns this transition. A full source cell is preferred for the
/// normal one-edge and adjacent-corner masks so the authored rounded pixels
/// remain intact instead of being reconstructed as four independently chosen
/// square quadrants.
const DEPTH_MASK_NORTH_EAST: u8 = WATER_MASK_NORTH | WATER_MASK_EAST;
const DEPTH_MASK_SOUTH_EAST: u8 = WATER_MASK_SOUTH | WATER_MASK_EAST;
const DEPTH_MASK_SOUTH_WEST: u8 = WATER_MASK_SOUTH | WATER_MASK_WEST;
const DEPTH_MASK_NORTH_WEST: u8 = WATER_MASK_NORTH | WATER_MASK_WEST;

fn depth_outer_cell(mask4: u8) -> Option<(u8, u8)> {
    match mask4 {
        WATER_MASK_NORTH => Some((1, 0)),
        DEPTH_MASK_NORTH_EAST => Some((2, 0)),
        WATER_MASK_EAST => Some((2, 1)),
        DEPTH_MASK_SOUTH_EAST => Some((2, 2)),
        WATER_MASK_SOUTH => Some((1, 2)),
        DEPTH_MASK_SOUTH_WEST => Some((0, 2)),
        WATER_MASK_WEST => Some((0, 1)),
        DEPTH_MASK_NORTH_WEST => Some((0, 0)),
        _ => None,
    }
}

fn draw_full_depth_cell(
    texture: &Texture2D,
    px: f32,
    py: f32,
    role_col: u8,
    role_row: u8,
) {
    let block = direct_lpc_transition_block("shallow_rim_over_deep")
        .expect("reviewed shallow/deep LPC block");
    draw_texture_ex(
        texture,
        px,
        py,
        WHITE,
        DrawTextureParams {
            dest_size: Some(vec2(TILE_SIZE, TILE_SIZE)),
            source: Some(Rect::new(
                f32::from(block.outer_col + role_col) * LPC_SOURCE_CELL_SIZE,
                f32::from(block.outer_row + role_row) * LPC_SOURCE_CELL_SIZE,
                LPC_SOURCE_CELL_SIZE,
                LPC_SOURCE_CELL_SIZE,
            )),
            ..Default::default()
        },
    );
}

fn draw_full_depth_inner_cell(
    texture: &Texture2D,
    px: f32,
    py: f32,
    direction: DiagonalDirection,
) -> bool {
    let block = direct_lpc_transition_block("shallow_rim_over_deep")
        .expect("reviewed shallow/deep LPC block");
    let Some((source_col, source_row)) = inner_cell(block, direction) else {
        return false;
    };
    draw_texture_ex(
        texture,
        px,
        py,
        WHITE,
        DrawTextureParams {
            dest_size: Some(vec2(TILE_SIZE, TILE_SIZE)),
            source: Some(Rect::new(
                f32::from(source_col) * LPC_SOURCE_CELL_SIZE,
                f32::from(source_row) * LPC_SOURCE_CELL_SIZE,
                LPC_SOURCE_CELL_SIZE,
                LPC_SOURCE_CELL_SIZE,
            )),
            ..Default::default()
        },
    );
    true
}

fn draw_depth_inner_corners(
    texture: &Texture2D,
    px: f32,
    py: f32,
    corner_mask: u8,
) -> bool {
    if corner_mask.count_ones() != 1 {
        return false;
    }
    let corners = [
        (WATER_CORNER_NORTH_WEST, DiagonalDirection::NorthWest),
        (WATER_CORNER_NORTH_EAST, DiagonalDirection::NorthEast),
        (WATER_CORNER_SOUTH_WEST, DiagonalDirection::SouthWest),
        (WATER_CORNER_SOUTH_EAST, DiagonalDirection::SouthEast),
    ];
    let mut drew_any = false;
    for (bit, direction) in corners {
        if corner_mask & bit != 0 {
            drew_any |= draw_full_depth_inner_cell(texture, px, py, direction);
        }
    }
    drew_any
}

/// Draw the authored rounded shallow/deep rim from the LPC summer sheet using
/// the dedicated water topology mask rather than generic terrain transitions.
///
/// This keeps pond and ocean semantics separate while giving both domains the
/// same authored rounded depth contour. It also prevents a mixed-material
/// junction from selecting only part of a depth edge and leaving the visible
/// square towers seen in the previous runtime.
pub(crate) fn draw_direct_water_depth_rim(
    texture: &Texture2D,
    px: f32,
    py: f32,
    mask: WaterRenderMask,
) -> bool {
    if !mask.has_depth_transition()
        || (mask.depth_edges != 0 && mask.depth_corners != 0)
        || mask.depth_corners.count_ones() > 1
    {
        return false;
    }

    let mut drew_any = false;
    if let Some((role_col, role_row)) = depth_outer_cell(mask.depth_edges) {
        draw_full_depth_cell(texture, px, py, role_col, role_row);
        drew_any = true;
    }
    // The authored sheet has complete cells for straight edges, adjacent
    // outer corners, and diagonal-only inner corners. Opposite and three-sided
    // masks are semantic topology errors and are normalized before rendering;
    // never synthesize them from cropped quadrants or a generated atlas.
    let drew_inner = draw_depth_inner_corners(texture, px, py, mask.depth_corners);
    drew_any || drew_inner
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn common_depth_masks_select_complete_authored_cells() {
        assert_eq!(depth_outer_cell(WATER_MASK_NORTH), Some((1, 0)));
        assert_eq!(
            depth_outer_cell(WATER_MASK_NORTH | WATER_MASK_EAST),
            Some((2, 0))
        );
        assert_eq!(depth_outer_cell(WATER_MASK_EAST), Some((2, 1)));
        assert_eq!(
            depth_outer_cell(WATER_MASK_SOUTH | WATER_MASK_WEST),
            Some((0, 2))
        );
        assert_eq!(depth_outer_cell(WATER_MASK_NORTH | WATER_MASK_SOUTH), None);
    }

    #[test]
    fn diagonal_only_depth_contact_uses_inner_corner_path() {
        let mask = WaterRenderMask {
            shoreline_edges: 0,
            depth_edges: 0,
            depth_corners: WATER_CORNER_NORTH_EAST,
        };
        assert!(mask.has_depth_transition());
        assert_eq!(depth_outer_cell(mask.depth_edges), None);
    }

    #[test]
    fn inner_depth_corners_select_complete_authored_cells() {
        let block = direct_lpc_transition_block("shallow_rim_over_deep")
            .expect("reviewed depth block");
        assert_eq!(inner_cell(block, DiagonalDirection::NorthEast), Some((3, 24)));
        assert_eq!(inner_cell(block, DiagonalDirection::SouthEast), Some((3, 23)));
        assert_eq!(inner_cell(block, DiagonalDirection::SouthWest), Some((4, 23)));
        assert_eq!(inner_cell(block, DiagonalDirection::NorthWest), Some((4, 24)));
    }

    #[test]
    fn unsupported_depth_masks_are_not_synthesized() {
        assert_eq!(depth_outer_cell(WATER_MASK_NORTH | WATER_MASK_SOUTH), None);
        assert_eq!(
            depth_outer_cell(WATER_MASK_NORTH | WATER_MASK_EAST | WATER_MASK_SOUTH),
            None
        );
    }

    #[test]
    fn direct_transition_blocks_do_not_alias_non_water_shoulders_to_pond_art() {
        assert!(direct_lpc_transition_block("riverbank_mud").is_none());
    }

    #[test]
    fn direct_transition_blocks_stay_inside_the_authored_sheet() {
        for group in [
            "grass_over_dirt",
            "grass_over_sand",
            "grass_bank_over_shallow",
            "dirt_bank_over_shallow",
            "sand_bank_over_shallow",
            "shallow_rim_over_deep",
            "sand_over_wet_sand",
            "pebble_path_over_dirt",
        ] {
            let block = direct_lpc_transition_block(group)
                .unwrap_or_else(|| panic!("missing direct LPC transition mapping for {group}"));
            assert!(block.outer_col + 2 < 16);
            assert!(block.outer_row + 2 < 26);
            if let Some((column, row)) = block.inner {
                assert!(column + 1 < 16);
                assert!(row + 1 < 26);
            }
        }
    }
}
