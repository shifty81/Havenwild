use super::*;
use crate::runtime_structural_cliff_shapes::{
    EAST_EDGE_CELL, NORTH_EAST_CORNER_CELL, NORTH_LIP_CELL, NORTH_WEST_CORNER_CELL,
    WEST_EDGE_CELL,
};
use haven_assets::lpc_cliff_ramp_provider::LpcCliffContourStampRole;

impl Game {
    /// Draw the W8 connected contour grammar for a host that has no visible
    /// south face.
    ///
    /// Fresh PCG normalization removes three/four-edge one-cell caps before
    /// structural baking. The stable non-south generated vocabulary is thus:
    /// N, E, W, NE, NW, and E+W. Adjacent N+E/N+W turns use their dedicated
    /// authored corner cells. The E+W narrow ridge uses the complete 3x1 ridge
    /// row already authored in the companion LPC cliff-family sheet; it is not
    /// built by overlapping incompatible ElizaWy side cells.
    pub(super) fn draw_non_south_connected_contour(
        &self,
        texture: &Texture2D,
        global_x: i32,
        global_y: i32,
        north: bool,
        east: bool,
        west: bool,
    ) {
        match (north, east, west) {
            (false, false, false) => {}
            (true, false, false) => {
                self.draw_cliff_overlay_cell(texture, NORTH_LIP_CELL, global_x, global_y);
            }
            (false, true, false) => {
                self.draw_cliff_overlay_cell(texture, EAST_EDGE_CELL, global_x, global_y);
            }
            (false, false, true) => {
                self.draw_cliff_overlay_cell(texture, WEST_EDGE_CELL, global_x, global_y);
            }
            (true, true, false) => {
                self.draw_cliff_overlay_cell(
                    texture,
                    NORTH_EAST_CORNER_CELL,
                    global_x,
                    global_y,
                );
            }
            (true, false, true) => {
                self.draw_cliff_overlay_cell(
                    texture,
                    NORTH_WEST_CORNER_CELL,
                    global_x,
                    global_y,
                );
            }
            (false, true, true) => {
                let _ = self.draw_authored_vertical_ridge_middle(global_x, global_y);
            }
            (true, true, true) => {
                // A N+E+W cell has only one same-tier cardinal support. Fresh
                // generated terrain removes this thin cap before topology bake.
                // Do not manufacture a fake three-edge tile for explicit
                // editor/player-authored geometry; authoring diagnostics can
                // flag/repair it instead.
            }
        }
    }

    /// South-facing composite masks may also expose a north/back boundary.
    /// The north rim is a complete authored cell whose alpha footprint is
    /// disjoint from the certified straight south lip. Keeping it separate
    /// preserves the back edge without replacing the south diagonal/terminal.
    pub(super) fn draw_north_back_rim_for_south_shape(
        &self,
        texture: &Texture2D,
        global_x: i32,
        global_y: i32,
        north_open: bool,
    ) {
        if north_open {
            self.draw_cliff_overlay_cell(texture, NORTH_LIP_CELL, global_x, global_y);
        }
    }

    /// Exact 3x1 authored middle row for a one-cell-wide north/south ridge.
    /// The source sheet is already loaded for W7 ramps. The center source cell
    /// remains the walkable plateau strip and the two flanks are visual cliff
    /// overhang; structural edges remain collision/navigation authority.
    fn draw_authored_vertical_ridge_middle(&self, global_x: i32, global_y: i32) -> bool {
        let Some(texture) = self.oga_cliff_source.as_ref() else {
            return false;
        };
        let role = LpcCliffContourStampRole::VerticalRidgeMiddle;
        let stamp = role.source_stamp();
        let (anchor_x, anchor_y) = role.host_anchor_offset();
        self.draw_cliff_source_rect(
            texture,
            Rect::new(
                stamp.column as f32 * TILE_SIZE,
                stamp.row as f32 * TILE_SIZE,
                stamp.width_cells as f32 * TILE_SIZE,
                stamp.height_cells as f32 * TILE_SIZE,
            ),
            (global_x + i32::from(anchor_x)) as f32 * TILE_SIZE,
            (global_y + i32::from(anchor_y)) as f32 * TILE_SIZE,
            stamp.width_cells as f32 * TILE_SIZE,
            stamp.height_cells as f32 * TILE_SIZE,
        );
        true
    }
}
