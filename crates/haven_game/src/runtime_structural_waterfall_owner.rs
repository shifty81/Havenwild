use super::*;

const MAX_WATERFALL_RUN_SCAN: usize = 32;

impl Game {
    /// Returns true for the single deterministic renderer-owner cell in a
    /// contiguous waterfall source run. Wide rivers may expose several
    /// neighboring structural waterfall cells; only the center owner should
    /// stamp the multi-cell waterfall artwork.
    pub(super) fn waterfall_connector_is_run_owner(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        global_x: i32,
        global_y: i32,
        direction: haven_world::CardinalDirectionV2,
    ) -> bool {
        let is_source = |x: i32, y: i32| {
            self.surface_structural_at_global_in_manifest(manifest, x, y)
                .is_some_and(|cell| haven_world::waterfall_source_valid_v2(cell, direction))
        };

        if !is_source(global_x, global_y) {
            return false;
        }

        // A waterfall run extends perpendicular to its fall direction.
        let (step_x, step_y) = match direction {
            haven_world::CardinalDirectionV2::North | haven_world::CardinalDirectionV2::South => {
                (1, 0)
            }
            haven_world::CardinalDirectionV2::East | haven_world::CardinalDirectionV2::West => {
                (0, 1)
            }
        };

        let mut before = 0usize;
        for distance in 1..=MAX_WATERFALL_RUN_SCAN {
            let d = distance as i32;
            if !is_source(global_x - step_x * d, global_y - step_y * d) {
                break;
            }
            before += 1;
        }

        let mut after = 0usize;
        for distance in 1..=MAX_WATERFALL_RUN_SCAN {
            let d = distance as i32;
            if !is_source(global_x + step_x * d, global_y + step_y * d) {
                break;
            }
            after += 1;
        }

        let run_len = before + 1 + after;
        // For even runs select the lower-index (west/north) middle cell. This
        // is stable across frames, partition boundaries, and traversal order.
        before == (run_len - 1) / 2
    }
}
