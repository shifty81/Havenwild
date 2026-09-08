use super::*;

impl Game {
    pub(super) fn draw_side_waterfall_if_present(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        cell: haven_world::StructuralCellV2,
        global_x: i32,
        global_y: i32,
    ) {
        for direction in [
            haven_world::CardinalDirectionV2::West,
            haven_world::CardinalDirectionV2::East,
        ] {
            if haven_world::waterfall_source_valid_v2(cell, direction) {
                let _ = self.draw_waterfall_connector(manifest, global_x, global_y, direction);
            }
        }
    }

    pub(super) fn draw_waterfall_connector(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        global_x: i32,
        global_y: i32,
        direction: haven_world::CardinalDirectionV2,
    ) -> bool {
        // H20V2B6: a multi-cell river exposes a contiguous run of structural
        // waterfall source cells. The LPC connector artwork is itself multi-cell,
        // so exactly one deterministic center cell owns the draw. Without this
        // guard each source cell stamps another offset waterfall.
        if !self.waterfall_connector_is_run_owner(manifest, global_x, global_y, direction) {
            return false;
        }
        let Some(texture) = self.lpc_waterfall_source.as_ref() else {
            return false;
        };
        let frame = ((get_time() * 7.0).floor() as usize) % 4;
        let (source, world_x, world_y, width, height) = match direction {
            haven_world::CardinalDirectionV2::South => (
                Rect::new(frame as f32 * 96.0, 0.0, 96.0, 160.0),
                (global_x - 1) as f32 * TILE_SIZE,
                (global_y + 1) as f32 * TILE_SIZE,
                TILE_SIZE * 3.0,
                TILE_SIZE * 5.0,
            ),
            haven_world::CardinalDirectionV2::West => (
                Rect::new(frame as f32 * 96.0, 160.0, 64.0, 224.0),
                (global_x - 2) as f32 * TILE_SIZE,
                (global_y - 2) as f32 * TILE_SIZE,
                TILE_SIZE * 2.0,
                TILE_SIZE * 7.0,
            ),
            haven_world::CardinalDirectionV2::East => (
                Rect::new(32.0 + frame as f32 * 96.0, 384.0, 64.0, 224.0),
                (global_x + 1) as f32 * TILE_SIZE,
                (global_y - 2) as f32 * TILE_SIZE,
                TILE_SIZE * 2.0,
                TILE_SIZE * 7.0,
            ),
            haven_world::CardinalDirectionV2::North => return false,
        };
        self.draw_cliff_source_rect(texture, source, world_x, world_y, width, height);
        true
    }
}
