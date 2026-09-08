use super::*;
use crate::runtime_structural_connectors::{StructuralConnectorKind, LADDER_A_SOURCE};
use haven_assets::lpc_cliff_ramp_provider::LpcDirectionalCliffRampRole;
use haven_world::open_world::WorldTileCoord;

impl Game {
    pub(super) fn draw_south_connector_face(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        texture: &Texture2D,
        global_x: i32,
        global_y: i32,
        host_level: u8,
        face_segments: u8,
        connector: StructuralConnectorKind,
    ) {
        match connector {
            StructuralConnectorKind::Ramp => {
                // W7: the source family already contains complete left/right
                // 3x4 directional ramps. Place one whole authored stamp at
                // natural 32px scale, centered on the exact structural south
                // edge that owns traversal. No crop/mirror/rotation/stretch.
                let _ = (texture, host_level, face_segments);
                self.draw_authored_directional_ramp(manifest, global_x, global_y);
            }
            StructuralConnectorKind::Ladder => {
                let top = Rect::new(LADDER_A_SOURCE.x, LADDER_A_SOURCE.y, 32.0, 32.0);
                let body = Rect::new(LADDER_A_SOURCE.x, LADDER_A_SOURCE.y + 32.0, 32.0, 32.0);
                let foot = Rect::new(LADDER_A_SOURCE.x, LADDER_A_SOURCE.y + 64.0, 32.0, 32.0);
                if face_segments <= 1 {
                    // Coastal one-tier cliffs use one projected face row. The
                    // old generic feature-column path always emitted leading
                    // + foot even when authored_body_rows(1) == 0, turning a
                    // one-tier coastal ladder into a visually three-row/tall
                    // connector. The middle source cell is the repeatable
                    // ladder-face module and cleanly overlays the one receiver
                    // row while surrounding cliff grammar owns crest and foot.
                    let receiver_y = global_y + 1;
                    if self.cliff_projection_row_visible(
                        manifest,
                        global_x,
                        receiver_y,
                        host_level,
                    ) {
                        // The authored foot cell contains the transparent
                        // lower fringe that blends into receiver ground. Using
                        // the repeatable body cell on a one-tier coastal cliff
                        // produced the hard rectangular bottom seen in visual
                        // acceptance. The base cliff now remains behind this
                        // overlay, so its left/right rock contacts stay continuous.
                        self.draw_cliff_source_cell(
                            texture,
                            foot,
                            global_x as f32 * TILE_SIZE,
                            receiver_y as f32 * TILE_SIZE,
                        );
                    }
                } else {
                    // AC3R4E: a ladder must terminate on the same receiver row
                    // as the cliff it climbs. The generic feature-column helper
                    // emitted leading + (N-1) body + foot rows for an N-tier
                    // face, making every multi-tier ladder one tile too long.
                    // The authored 3-cell source is instead a scalable column:
                    // top + max(N-2, 0) body + foot = exactly N receiver rows.
                    let world_x = global_x as f32 * TILE_SIZE;
                    let first_y = global_y + 1;
                    if self.cliff_projection_row_visible(
                        manifest,
                        global_x,
                        first_y,
                        host_level,
                    ) {
                        self.draw_cliff_source_cell(
                            texture,
                            top,
                            world_x,
                            first_y as f32 * TILE_SIZE,
                        );
                    }
                    let body_rows = face_segments.saturating_sub(2);
                    for row in 0..body_rows {
                        let target_y = global_y + 2 + i32::from(row);
                        if self.cliff_projection_row_visible(
                            manifest,
                            global_x,
                            target_y,
                            host_level,
                        ) {
                            self.draw_cliff_source_cell(
                                texture,
                                body,
                                world_x,
                                target_y as f32 * TILE_SIZE,
                            );
                        }
                    }
                    let foot_y = global_y + i32::from(face_segments);
                    if self.cliff_projection_row_visible(
                        manifest,
                        global_x,
                        foot_y,
                        host_level,
                    ) {
                        self.draw_cliff_source_cell(
                            texture,
                            foot,
                            world_x,
                            foot_y as f32 * TILE_SIZE,
                        );
                    }
                }
            }
            StructuralConnectorKind::Stairs | StructuralConnectorKind::Bridge => {
                // Authored stairs/bridge objects own their connector artwork.
            }
        }
    }


    pub(super) fn complete_directional_ramp_owner_for_cell(
        &self,
        _manifest: &haven_world::ContinuousSurfaceManifest,
        global_x: i32,
        global_y: i32,
    ) -> Option<(i32, i32)> {
        // AC3R4E: only the six semantic MountainPath corridor cells suppress
        // ordinary cliff ownership. The wider 3x4 artwork is drawn as a final
        // overlay after the base cliff pass, so transparent source pixels reveal
        // the surrounding continuous cliff instead of cutting rectangular holes.
        self.surface_authored_ramp_owner(global_x, global_y)
    }

    pub(super) fn complete_directional_ramp_role_for_host(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        global_x: i32,
        global_y: i32,
    ) -> Option<LpcDirectionalCliffRampRole> {
        let path = |dx: i32, dy: i32| {
            self.surface_tile_kind_at_global_in_manifest(
                manifest,
                WorldTileCoord::new(global_x + dx, global_y + dy),
            ) == Some(TileKind::MountainPath)
        };
        let rise_right = [(1, -1), (1, 0), (0, 0), (0, 1), (-1, 1), (-1, 2)]
            .into_iter()
            .all(|(dx, dy)| path(dx, dy));
        let rise_left = [(-1, -1), (-1, 0), (0, 0), (0, 1), (1, 1), (1, 2)]
            .into_iter()
            .all(|(dx, dy)| path(dx, dy));
        match (rise_right, rise_left) {
            (true, false) => Some(LpcDirectionalCliffRampRole::RiseRight),
            (false, true) => Some(LpcDirectionalCliffRampRole::RiseLeft),
            (true, true) => Some(self.directional_ramp_role_for_host(manifest, global_x, global_y)),
            (false, false) => None,
        }
    }

    pub(super) fn draw_authored_directional_ramp(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        global_x: i32,
        global_y: i32,
    ) {
        let Some(texture) = self.oga_cliff_source.as_ref() else {
            return;
        };
        let Some(role) =
            self.complete_directional_ramp_role_for_host(manifest, global_x, global_y)
        else {
            // Never paste a complete authored 3x4 ramp over an incomplete or
            // legacy two-cell MountainPath hint. Generation/authoring must own
            // the full certified corridor first.
            return;
        };
        let stamp = role.source_stamp();
        let (anchor_x, anchor_y) = role.host_anchor_offset();
        let source = Rect::new(
            stamp.column as f32 * TILE_SIZE,
            stamp.row as f32 * TILE_SIZE,
            stamp.width_cells as f32 * TILE_SIZE,
            stamp.height_cells as f32 * TILE_SIZE,
        );
        self.draw_cliff_source_rect(
            texture,
            source,
            (global_x + i32::from(anchor_x)) as f32 * TILE_SIZE,
            (global_y + i32::from(anchor_y)) as f32 * TILE_SIZE,
            stamp.width_cells as f32 * TILE_SIZE,
            stamp.height_cells as f32 * TILE_SIZE,
        );
    }

    fn directional_ramp_role_for_host(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        global_x: i32,
        global_y: i32,
    ) -> LpcDirectionalCliffRampRole {
        let path = |dx: i32, dy: i32| {
            self.surface_tile_kind_at_global_in_manifest(
                manifest,
                WorldTileCoord::new(global_x + dx, global_y + dy),
            ) == Some(TileKind::MountainPath)
        };

        // The authored RiseRight corridor runs lower-left -> upper-right; the
        // RiseLeft corridor is the exact opposite authored stamp. Prefer the
        // direction already implied by neighboring MountainPath cells. Fresh
        // W7 worldgen paints these approach/departure cells explicitly.
        let rise_right_score = usize::from(path(1, -1))
            + usize::from(path(1, 0))
            + usize::from(path(-1, 1))
            + usize::from(path(-1, 2));
        let rise_left_score = usize::from(path(-1, -1))
            + usize::from(path(-1, 0))
            + usize::from(path(1, 1))
            + usize::from(path(1, 2));
        if rise_right_score > rise_left_score {
            LpcDirectionalCliffRampRole::RiseRight
        } else if rise_left_score > rise_right_score {
            LpcDirectionalCliffRampRole::RiseLeft
        } else if (global_x ^ global_y) & 1 == 0 {
            // Existing saves from W6 have only the center MountainPath pair.
            // Keep their visual choice deterministic without persisting a new
            // runtime-only identifier into save data.
            LpcDirectionalCliffRampRole::RiseRight
        } else {
            LpcDirectionalCliffRampRole::RiseLeft
        }
    }

 }
