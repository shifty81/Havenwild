use super::*;

impl Game {
    /// One animated multi-cell waterfall sprite owns each continuous fall edge.
    /// Wide rivers used to draw the same 3x5/2x7 sprite once per source cell,
    /// producing the stacked waterfall mess visible in runtime screenshots.
    pub(super) fn waterfall_connector_is_run_owner(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        global_x: i32,
        global_y: i32,
        direction: haven_world::CardinalDirectionV2,
    ) -> bool {
        let valid = |x: i32, y: i32| {
            self.surface_structural_at_global_in_manifest(manifest, x, y)
                .is_some_and(|cell| haven_world::waterfall_source_valid_v2(cell, direction))
        };
        if !valid(global_x, global_y) {
            return false;
        }
        let (step_x, step_y) = match direction {
            haven_world::CardinalDirectionV2::North
            | haven_world::CardinalDirectionV2::South => (1, 0),
            haven_world::CardinalDirectionV2::East
            | haven_world::CardinalDirectionV2::West => (0, 1),
        };
        let mut start_x = global_x;
        let mut start_y = global_y;
        for _ in 0..16 {
            let nx = start_x - step_x;
            let ny = start_y - step_y;
            if !valid(nx, ny) { break; }
            start_x = nx;
            start_y = ny;
        }
        let mut end_x = global_x;
        let mut end_y = global_y;
        for _ in 0..16 {
            let nx = end_x + step_x;
            let ny = end_y + step_y;
            if !valid(nx, ny) { break; }
            end_x = nx;
            end_y = ny;
        }
        let owner_x = (start_x + end_x) / 2;
        let owner_y = (start_y + end_y) / 2;
        global_x == owner_x && global_y == owner_y
    }

}
