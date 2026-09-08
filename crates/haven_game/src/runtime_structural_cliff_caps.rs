use super::*;
use crate::runtime_structural_cliff_shapes::{
    authored_body_rows, SOUTH_TERMINAL_BODY_ROW, SOUTH_TERMINAL_CREST_ROW,
    SOUTH_TERMINAL_FOOT_ROW,
};

impl Game {
    /// Draw ElizaWy's natural-scale three-column rounded south terminal.
    ///
    /// The source sheet already authors this feature as left/center/right
    /// 32x32 cells. Preserve those cells and their authored offsets exactly:
    /// no half-tile crop, mirroring, stretching, or recomposition is permitted.
    pub(super) fn draw_authored_south_terminal(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        texture: &Texture2D,
        global_x: i32,
        global_y: i32,
        host_level: u8,
        face_segments: u8,
    ) {
        let body_rows = authored_body_rows(face_segments);

        let draw_row = |this: &Self, row: &[Rect; 3], target_y: i32| {
            for (column_offset, source) in row.iter().copied().enumerate() {
                let target_x = global_x + column_offset as i32 - 1;
                if target_y != global_y
                    && !this.cliff_projection_row_visible(
                        manifest,
                        target_x,
                        target_y,
                        host_level,
                    )
                {
                    continue;
                }
                this.draw_cliff_source_cell(
                    texture,
                    source,
                    target_x as f32 * TILE_SIZE,
                    target_y as f32 * TILE_SIZE,
                );
            }
        };

        // W14: terminal crest is upper-level presentation. Receiver-facing
        // height is body x (N-1) + one foot row, identical to straight/diagonal.
        draw_row(self, &SOUTH_TERMINAL_CREST_ROW, global_y);
        for row_index in 0..body_rows {
            draw_row(
                self,
                &SOUTH_TERMINAL_BODY_ROW,
                global_y + 1 + row_index as i32,
            );
        }
        draw_row(
            self,
            &SOUTH_TERMINAL_FOOT_ROW,
            global_y + 1 + body_rows as i32,
        );
    }

    /// Foreground/depth replay of the rounded terminal without its crest row.
    /// The crest belongs to upper terrain and is already drawn by the base pass;
    /// only receiver-facing body/foot pixels participate in actor occlusion.
    pub(super) fn draw_authored_south_terminal_projection(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        texture: &Texture2D,
        global_x: i32,
        global_y: i32,
        host_level: u8,
        face_segments: u8,
    ) {
        let body_rows = authored_body_rows(face_segments);
        let draw_row = |this: &Self, row: &[Rect; 3], target_y: i32| {
            for (column_offset, source) in row.iter().copied().enumerate() {
                let target_x = global_x + column_offset as i32 - 1;
                if !this.cliff_projection_row_visible(
                    manifest,
                    target_x,
                    target_y,
                    host_level,
                ) {
                    continue;
                }
                this.draw_cliff_source_cell(
                    texture,
                    source,
                    target_x as f32 * TILE_SIZE,
                    target_y as f32 * TILE_SIZE,
                );
            }
        };

        for row_index in 0..body_rows {
            draw_row(
                self,
                &SOUTH_TERMINAL_BODY_ROW,
                global_y + 1 + row_index as i32,
            );
        }
        draw_row(
            self,
            &SOUTH_TERMINAL_FOOT_ROW,
            global_y + 1 + body_rows as i32,
        );
    }
}
