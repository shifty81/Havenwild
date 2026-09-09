use super::*;
use crate::runtime_structural_cliff_shapes::{
    authored_body_rows, resolve_cliff_visual_recipe_v1, shape_exposes, CliffVisualShape,
    DiagonalChainRole, DiagonalFaceRecipe, VerticalFaceRecipe, EAST_EDGE_CELL,
    SOUTH_EAST_DIAGONAL_FACE, SOUTH_STRAIGHT_FACE, SOUTH_WEST_DIAGONAL_FACE, WEST_EDGE_CELL,
};
use crate::runtime_structural_connectors::{
    CAVE_NARROW_SOURCE, WATER_CLIFF_VALLEY_SOURCE,
};
use haven_world::open_world::WorldTileCoord;

fn generated_surface_uses_orthogonal_cliff_grammar(scene_id: &haven_core::ProjectSceneId) -> bool {
    haven_world::parse_pcg_surface_scene_id(scene_id).is_some()
        || haven_world::parse_generated_chunk_scene_id(scene_id).is_some()
}

fn runtime_cliff_visual_shape(
    _generated_surface: bool,
    visual_shape: CliffVisualShape,
) -> CliffVisualShape {
    // R1: topology is authority. Generated and authored surfaces both consume
    // the same resolved cliff visual shape. The previous generated-surface
    // override forcibly collapsed every diagonal/terminal recipe to Orthogonal,
    // which is why structurally stepped contours rendered as long square walls.
    visual_shape
}

fn exposed_shape_neighbors_complete(
    shape: haven_world::CliffShape15,
    north_loaded: bool,
    east_loaded: bool,
    south_loaded: bool,
    west_loaded: bool,
) -> bool {
    use haven_world::EdgeMaskV2;
    (!shape_exposes(shape, EdgeMaskV2::NORTH) || north_loaded)
        && (!shape_exposes(shape, EdgeMaskV2::EAST) || east_loaded)
        && (!shape_exposes(shape, EdgeMaskV2::SOUTH) || south_loaded)
        && (!shape_exposes(shape, EdgeMaskV2::WEST) || west_loaded)
}

/// HW-CLIFF-02: ordinary one-structural-step relief stays visually retired, but
/// a certified ramp corridor is allowed to resolve its one-step retaining walls.
/// This makes the ramp an opening in the same cliff topology rather than a
/// foreign sprite pasted over a deleted corridor.
fn structural_cliff_projection_visible(maximum_drop: i16, in_ramp_corridor: bool) -> bool {
    in_ramp_corridor
        || maximum_drop > haven_world::STRUCTURAL_ELEVATION_RESOLVER_STEP_V2
}

impl Game {
    /// Canonical structural cliff renderer.
    ///
    /// The world provides one discrete structural-level grid. Its four exposed
    /// cardinal bits resolve to exactly one of the fifteen `CliffShape15`
    /// masks. The ElizaWy square plateau is then projected as edge/corner
    /// components around that one logical host cell. Source-image dimensions do
    /// not participate in world topology or collision.
    pub(super) fn draw_structural_cliffs(&self) {
        if self.world.active().kind != SceneKind::Exterior {
            return;
        }
        let Some(texture) = self.lpc_cliff_source.as_ref() else {
            return;
        };

        let manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
        let viewport = vec2(screen_width().max(1.0), screen_height().max(1.0));
        let half_visible = viewport / self.camera_zoom.max(0.01) * 0.5;
        let min_x = ((self.camera_target.x - half_visible.x) / TILE_SIZE).floor() as i32 - 4;
        let min_y = ((self.camera_target.y - half_visible.y) / TILE_SIZE).floor() as i32 - 8;
        let max_x = ((self.camera_target.x + half_visible.x) / TILE_SIZE).ceil() as i32 + 4;
        let max_y = ((self.camera_target.y + half_visible.y) / TILE_SIZE).ceil() as i32 + 7;
        for global_y in min_y..=max_y {
            for global_x in min_x..=max_x {
                #[cfg(target_os = "windows")]
                {
                    crate::native_crash_windows::set_cliff_context(global_x, global_y, 0);
                    crate::native_crash_windows::set_cliff_stage(
                        crate::native_crash_windows::CLIFF_STAGE_CELL_LOOKUP,
                    );
                }
                let Some(center) =
                    self.surface_structural_at_global_in_manifest(&manifest, global_x, global_y)
                else {
                    continue;
                };
                #[cfg(target_os = "windows")]
                crate::native_crash_windows::set_cliff_stage(
                    crate::native_crash_windows::CLIFF_STAGE_RECIPE_RESOLVE,
                );
                let Some(shared_recipe) = resolve_cliff_visual_recipe_v1(center, |dx, dy| {
                    self.surface_structural_at_global_in_manifest(
                        &manifest,
                        global_x + dx,
                        global_y + dy,
                    )
                }) else {
                    continue;
                };
                let shape = shared_recipe.shape;
                // AC3R4F residency boundary rule: an unloaded neighboring
                // structural partition is unknown, not Level 0. Never turn the
                // edge of the structural cache into a kilometer-long fake cliff.
                if !exposed_shape_neighbors_complete(
                    shape,
                    self.surface_structural_at_global_in_manifest(&manifest, global_x, global_y - 1).is_some(),
                    self.surface_structural_at_global_in_manifest(&manifest, global_x + 1, global_y).is_some(),
                    self.surface_structural_at_global_in_manifest(&manifest, global_x, global_y + 1).is_some(),
                    self.surface_structural_at_global_in_manifest(&manifest, global_x - 1, global_y).is_some(),
                ) {
                    continue;
                }
                #[cfg(target_os = "windows")]
                {
                    crate::native_crash_windows::set_cliff_context(
                        global_x,
                        global_y,
                        shared_recipe.south_face_segments.max(1),
                    );
                    crate::native_crash_windows::set_cliff_stage(
                        crate::native_crash_windows::CLIFF_STAGE_RAMP_OWNERSHIP,
                    );
                }
                // HW-CLIFF-02 connected structural ownership:
                //
                // The six MountainPath cells are the semantic/traversal ramp
                // corridor, not six deleted cliff cells. Each corridor cell
                // still resolves its structural edges so the same ElizaWy cliff
                // family supplies retaining walls, shoulders and terminals.
                // Only an exact Ramp connector edge is opened below.
                let ramp_corridor_owner =
                    self.complete_directional_ramp_owner_for_cell(&manifest, global_x, global_y);

                // One-step cliff presentation stays retired globally. The odd
                // middle structural tier reserved inside a certified 2->1->0
                // or 4->3->2 ramp is the sole exception.
                if !structural_cliff_projection_visible(
                    center.maximum_drop,
                    ramp_corridor_owner.is_some(),
                ) {
                    continue;
                }

                #[cfg(target_os = "windows")]
                crate::native_crash_windows::set_cliff_stage(
                    crate::native_crash_windows::CLIFF_STAGE_CONNECTOR_RESOLVE,
                );use haven_world::{CardinalDirectionV2, EdgeMaskV2};
                let connector_for = |direction: CardinalDirectionV2, edge: u8| {
                    shape_exposes(shape, edge)
                        .then(|| {
                            self.structural_connector_from_host_edge_in_manifest(
                                &manifest, global_x, global_y, direction,
                            )
                        })
                        .flatten()
                };
                let north_connector = connector_for(CardinalDirectionV2::North, EdgeMaskV2::NORTH);
                let east_connector = connector_for(CardinalDirectionV2::East, EdgeMaskV2::EAST);
                let south_connector = connector_for(CardinalDirectionV2::South, EdgeMaskV2::SOUTH);
                let west_connector = connector_for(CardinalDirectionV2::West, EdgeMaskV2::WEST);

                let north_open = north_connector.is_none();
                let west_waterfall = haven_world::waterfall_source_valid_v2(
                    center,
                    haven_world::CardinalDirectionV2::West,
                );
                let east_waterfall = haven_world::waterfall_source_valid_v2(
                    center,
                    haven_world::CardinalDirectionV2::East,
                );
                let west_open = west_connector.is_none() && !west_waterfall;
                let east_open = east_connector.is_none() && !east_waterfall;

                let south_exposed = shape_exposes(shape, EdgeMaskV2::SOUTH);
                let cave_host = south_exposed
                    && center.cave_host_eligible
                    && self.surface_cave_origin_at_global_in_manifest(
                        &manifest,
                        WorldTileCoord::new(global_x, global_y),
                    );
                let south_waterfall = south_exposed
                    && haven_world::waterfall_source_valid_v2(
                        center,
                        haven_world::CardinalDirectionV2::South,
                    );
                // H20V1R8: ladders attach to an existing cliff face; they do
                // not replace the face the way an authored 3x4 ramp does. Keep
                // the canonical south face behind a ladder so neighboring
                // straight/diagonal cells retain one continuous rock contour.
                // The ladder art then overlays only its center receiver lane.
                let ladder_overlay = south_connector
                    == Some(crate::runtime_structural_connectors::StructuralConnectorKind::Ladder);
                let south_open = south_exposed
                    && !cave_host
                    && !south_waterfall
                    && (south_connector.is_none() || ladder_overlay);

                let address = haven_world::surface_tile_address(WorldTileCoord::new(global_x, global_y));
                let host_scene_id = manifest.scene_id_for_chunk(address.chunk);
                let generated_surface = generated_surface_uses_orthogonal_cliff_grammar(&host_scene_id);
                let visual_shape = runtime_cliff_visual_shape(
                    generated_surface,
                    shared_recipe.visual_shape,
                );
                let diagonal_chain_role = shared_recipe.diagonal_chain_role;

                let host_level = self
                    .surface_structural_level_at_global_in_manifest(&manifest, global_x, global_y)
                    .unwrap_or(0);
                let south_face_segments = shared_recipe.south_face_segments;
                #[cfg(target_os = "windows")]
                crate::native_crash_windows::set_cliff_stage(
                    crate::native_crash_windows::CLIFF_STAGE_BASE_DRAW,
                );
                self.draw_base_cliff_shape(
                    &manifest,
                    texture,
                    global_x,
                    global_y,
                    host_level,
                    shape,
                    visual_shape,
                    north_open,
                    east_open,
                    south_open,
                    west_open,
                    diagonal_chain_role,
                    south_face_segments.max(1),
                );

                #[cfg(target_os = "windows")]
                crate::native_crash_windows::set_cliff_stage(
                    crate::native_crash_windows::CLIFF_STAGE_CONNECTOR_ART,
                );
                if cave_host {
                    // W8: ordinary generated caves are always the authored
                    // one-tile-wide doorway-scale mouth. Cliff height must not
                    // widen the opening. Extra structural tiers remain ordinary
                    // rock continuation above the fixed 1x3 cave recipe. Large
                    // 3x3 openings are reserved for an explicit road/cart
                    // tunnel semantic and are never inferred from face height.
                    let cave_y = global_y
                        + 1
                        + crate::runtime_structural_cliff_shapes::extra_authored_body_rows(
                            south_face_segments.max(1),
                        ) as i32;
                    self.draw_cliff_source_rect(
                        texture,
                        CAVE_NARROW_SOURCE,
                        global_x as f32 * TILE_SIZE,
                        cave_y as f32 * TILE_SIZE,
                        TILE_SIZE,
                        TILE_SIZE * 3.0,
                    );
                } else if south_waterfall
                    && self.draw_waterfall_connector(
                        &manifest,
                        global_x,
                        global_y,
                        haven_world::CardinalDirectionV2::South,
                    )
                {
                    // Animated Waterfall.png owns the complete south connector.
                                } else if let Some(connector) = south_connector {
                    if connector
                        != crate::runtime_structural_connectors::StructuralConnectorKind::Ramp
                    {
                        self.draw_south_connector_face(
                            &manifest,
                            texture,
                            global_x,
                            global_y,
                            host_level,
                            south_face_segments.max(1),
                            connector,
                        );
                    }
                    // A Ramp is an opening in the cliff recipe. MountainPath
                    // terrain owns its walk surface; structural cliff recipes
                    // own all rock surrounding the open edge.
                }

                #[cfg(target_os = "windows")]
                crate::native_crash_windows::set_cliff_stage(
                    crate::native_crash_windows::CLIFF_STAGE_SIDE_WATERFALL,
                );
                self.draw_side_waterfall_if_present(&manifest, center, global_x, global_y);
                #[cfg(target_os = "windows")]
                crate::native_crash_windows::set_cliff_stage(
                    crate::native_crash_windows::CLIFF_STAGE_WATER_VALLEY,
                );
                self.draw_water_facing_valley_if_anchor(
                    &manifest, texture, center, global_x, global_y,
                );
            }
        }
        // HW-CLIFF-02: no deferred foreign ramp overlay. The normal terrain
        // pass plus structural cliff recipe are the complete ramp authority.}
    // HW-CLIFF-02R7 doc-boundary method-close repair:
    // close draw_structural_cliffs() before the foreground function docs.
    }

    /// Replay only the receiver-facing portion of one south cliff into the
    /// actor depth queue. The structural pass already owns crest/back/side rim
    /// presentation; this replay deliberately excludes those upper-level pixels
    /// and exists only so lower-ground actors can pass behind the wall.
    /// Replay only the receiver-facing portion of one south cliff into the
    /// actor depth queue. The structural pass already owns crest/back/side rim
    /// presentation; this replay deliberately excludes those upper-level pixels
    /// and exists only so lower-ground actors can pass behind the wall.
    ///
    /// HW-CLIFF-02R4 foreground parser repair: ramp corridor cells retain normal
    /// structural depth ownership. Only the exact Ramp connector edge itself is
    /// omitted, matching traversal/collision authority.
    pub(super) fn draw_structural_cliff_foreground_face(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        global_x: i32,
        global_y: i32,
    ) {
        let Some(texture) = self.lpc_cliff_source.as_ref() else {
            return;
        };
        let Some(center) =
            self.surface_structural_at_global_in_manifest(manifest, global_x, global_y)
        else {
            return;
        };
        let Some(shared_recipe) = resolve_cliff_visual_recipe_v1(center, |dx, dy| {
            self.surface_structural_at_global_in_manifest(
                manifest,
                global_x + dx,
                global_y + dy,
            )
        }) else {
            return;
        };
        let shape = shared_recipe.shape;
        if !exposed_shape_neighbors_complete(
            shape,
            self.surface_structural_at_global_in_manifest(manifest, global_x, global_y - 1)
                .is_some(),
            self.surface_structural_at_global_in_manifest(manifest, global_x + 1, global_y)
                .is_some(),
            self.surface_structural_at_global_in_manifest(manifest, global_x, global_y + 1)
                .is_some(),
            self.surface_structural_at_global_in_manifest(manifest, global_x - 1, global_y)
                .is_some(),
        ) {
            return;
        }
        if !shape_exposes(shape, haven_world::EdgeMaskV2::SOUTH)
            || shared_recipe.south_face_segments < 2
        {
            return;
        }

        let south_connector = self.structural_connector_from_host_edge_in_manifest(
            manifest,
            global_x,
            global_y,
            haven_world::CardinalDirectionV2::South,
        );
        if south_connector
            == Some(crate::runtime_structural_connectors::StructuralConnectorKind::Ramp)
        {
            return;
        }
        let cave_host = center.cave_host_eligible
            && self.surface_cave_origin_at_global_in_manifest(
                manifest,
                WorldTileCoord::new(global_x, global_y),
            );
        let south_waterfall = haven_world::waterfall_source_valid_v2(
            center,
            haven_world::CardinalDirectionV2::South,
        );
        if cave_host || south_waterfall {
            // Cave/waterfall connector artwork owns the receiver column and has
            // its own depth semantics. Do not replay a hidden ordinary wall.
            return;
        }

        let ladder_overlay = south_connector
            == Some(crate::runtime_structural_connectors::StructuralConnectorKind::Ladder);
        if south_connector.is_some() && !ladder_overlay {
            return;
        }

        let host_level = self
            .surface_structural_level_at_global_in_manifest(manifest, global_x, global_y)
            .unwrap_or(0);
        let face_segments = shared_recipe.south_face_segments.max(1);

        // R1 ladder actor-depth corridor. A composed LPC player is 64px wide,
        // so the one-cell ladder lane can overlap the two immediately adjacent
        // wall columns while climbing/cresting. The old foreground replay drew
        // those receiver faces after the player and left only the head visible.
        // Keep the base cliff/ladder presentation, but suppress foreground replay
        // in the local three-column ladder corridor while the player is physically
        // beside it. This preserves normal cliff occlusion everywhere else.
        let ladder_host_nearby = [-1_i32, 0, 1].into_iter().any(|dx| {
            self.structural_connector_from_host_edge_in_manifest(
                manifest,
                global_x + dx,
                global_y,
                haven_world::CardinalDirectionV2::South,
            ) == Some(crate::runtime_structural_connectors::StructuralConnectorKind::Ladder)
        });
        let player_tile = self.surface_global_tile();
        let player_in_ladder_depth_corridor = ladder_host_nearby
            && (player_tile.x - global_x).abs() <= 1
            && player_tile.y >= global_y - 1
            && player_tile.y <= global_y + i32::from(face_segments) + 1;
        if ladder_overlay || player_in_ladder_depth_corridor {
            return;
        }
        let east = shape_exposes(shape, haven_world::EdgeMaskV2::EAST);
        let west = shape_exposes(shape, haven_world::EdgeMaskV2::WEST);

        let address = haven_world::surface_tile_address(WorldTileCoord::new(global_x, global_y));
        let host_scene_id = manifest.scene_id_for_chunk(address.chunk);
        let visual_shape = runtime_cliff_visual_shape(
            generated_surface_uses_orthogonal_cliff_grammar(&host_scene_id),
            shared_recipe.visual_shape,
        );
        match visual_shape {
            CliffVisualShape::SouthWestDiagonal if west => {
                self.draw_diagonal_cliff_projection(
                    manifest,
                    texture,
                    global_x,
                    global_y,
                    host_level,
                    face_segments,
                    -1,
                    SOUTH_WEST_DIAGONAL_FACE,
                );
            }
            CliffVisualShape::SouthEastDiagonal if east => {
                self.draw_diagonal_cliff_projection(
                    manifest,
                    texture,
                    global_x,
                    global_y,
                    host_level,
                    face_segments,
                    1,
                    SOUTH_EAST_DIAGONAL_FACE,
                );
            }
            CliffVisualShape::SouthAuthoredTerminal if east && west => {
                self.draw_authored_south_terminal_projection(
                    manifest,
                    texture,
                    global_x,
                    global_y,
                    host_level,
                    face_segments,
                );
            }
            CliffVisualShape::Orthogonal
            | CliffVisualShape::SouthWestDiagonal
            | CliffVisualShape::SouthEastDiagonal
            | CliffVisualShape::SouthAuthoredTerminal => {
                self.draw_cliff_vertical_face(
                    manifest,
                    texture,
                    global_x,
                    global_y,
                    host_level,
                    face_segments,
                    VerticalFaceRecipe {
                        leading: None,
                        body: SOUTH_STRAIGHT_FACE.body,
                        foot: SOUTH_STRAIGHT_FACE.foot,
                    },
                );
            }
        }
    }

    fn draw_diagonal_cliff_projection(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        texture: &Texture2D,
        global_x: i32,
        global_y: i32,
        host_level: u8,
        face_segments: u8,
        low_side_dx: i32,
        recipe: DiagonalFaceRecipe,
    ) {
        let world_x = global_x as f32 * TILE_SIZE;
        let world_y = global_y as f32 * TILE_SIZE;
        let body_rows = authored_body_rows(face_segments);
        debug_assert!(matches!(low_side_dx, -1 | 1));
        let receiver_x = global_x + low_side_dx;

        for row in 0..body_rows {
            let target_y = global_y + 1 + row as i32;
            if !self.cliff_projection_row_visible(manifest, receiver_x, target_y, host_level) {
                continue;
            }
            self.draw_cliff_source_cell(
                texture,
                recipe.body,
                world_x,
                world_y + (row as f32 + 1.0) * TILE_SIZE,
            );
        }
        let foot_y = global_y + 1 + body_rows as i32;
        if self.cliff_projection_row_visible(manifest, receiver_x, foot_y, host_level) {
            self.draw_cliff_source_cell(
                texture,
                recipe.foot,
                world_x,
                world_y + (body_rows as f32 + 1.0) * TILE_SIZE,
            );
        }
    }

    #[allow(clippy::too_many_arguments)]
    fn draw_base_cliff_shape(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        texture: &Texture2D,
        global_x: i32,
        global_y: i32,
        host_level: u8,
        shape: haven_world::CliffShape15,
        visual_shape: CliffVisualShape,
        north_open: bool,
        east_open: bool,
        south_open: bool,
        west_open: bool,
        diagonal_chain_role: DiagonalChainRole,
        face_segments: u8,
    ) {
        use haven_world::EdgeMaskV2;
        let north = shape_exposes(shape, EdgeMaskV2::NORTH) && north_open;
        let east = shape_exposes(shape, EdgeMaskV2::EAST) && east_open;
        let south = shape_exposes(shape, EdgeMaskV2::SOUTH) && south_open;
        let west = shape_exposes(shape, EdgeMaskV2::WEST) && west_open;

        // W8 connected contour grammar. Fresh generated landforms have already
        // removed three/four-edge one-cell caps, so non-south hosts resolve to
        // exact N/E/W, authored NE/NW corner cells, or the complete companion
        // E+W ridge row. No adjacent straight-edge cells are stacked to fake a
        // corner.
        if !south {
            self.draw_non_south_connected_contour(
                texture, global_x, global_y, north, east, west,
            );
            return;
        }

        // A south-facing composite can also expose the north/back boundary.
        // Preserve that exact authored rim independently; the south family
        // remains owner of the visible face/turn/terminal.
        self.draw_north_back_rim_for_south_shape(
            texture, global_x, global_y, north,
        );

        // Perspective-visible south contours already have certified connected
        // source families. These own the complete visible turn/terminal. Do not
        // paint an additional north/east/west square-template cell over the same
        // host merely because the structural mask also exposes a back edge.
        match visual_shape {
            CliffVisualShape::SouthWestDiagonal if west => {
                self.draw_diagonal_cliff_face(
                    manifest,
                    texture,
                    global_x,
                    global_y,
                    host_level,
                    face_segments,
                    diagonal_chain_role,
                    -1,
                    SOUTH_WEST_DIAGONAL_FACE,
                );
                return;
            }
            CliffVisualShape::SouthEastDiagonal if east => {
                self.draw_diagonal_cliff_face(
                    manifest,
                    texture,
                    global_x,
                    global_y,
                    host_level,
                    face_segments,
                    diagonal_chain_role,
                    1,
                    SOUTH_EAST_DIAGONAL_FACE,
                );
                return;
            }
            CliffVisualShape::SouthAuthoredTerminal if east && west => {
                self.draw_authored_south_terminal(
                    manifest,
                    texture,
                    global_x,
                    global_y,
                    host_level,
                    face_segments,
                );
                return;
            }
            CliffVisualShape::Orthogonal
            | CliffVisualShape::SouthWestDiagonal
            | CliffVisualShape::SouthEastDiagonal
            | CliffVisualShape::SouthAuthoredTerminal => {}
        }

        // Orthogonal contours retain exact source-native side edges. Diagonal
        // and terminal recipes above now remain reachable on generated surfaces
        // instead of being collapsed to this fallback unconditionally.
        if visual_shape == CliffVisualShape::Orthogonal {
            if west {
                self.draw_cliff_overlay_cell(texture, WEST_EDGE_CELL, global_x, global_y);
            }
            if east {
                self.draw_cliff_overlay_cell(texture, EAST_EDGE_CELL, global_x, global_y);
            }
        }

        // W14 straight south host: the demo-grounded c2 crest/body/foot
        // family owns the complete visible face. The crest is drawn on the
        // plateau host row; the receiver-facing height is exactly the structural
        // tier delta and terminates in the authored c2r8 foot.
        self.draw_cliff_vertical_face(
            manifest,
            texture,
            global_x,
            global_y,
            host_level,
            face_segments,
            SOUTH_STRAIGHT_FACE,
        );
    }

    /// Project one complete authored 32x32 ElizaWy source cell onto the same
    /// 32x32 world cell. W3 deliberately has no strip/crop/stretch path here:
    /// semantic surface pixels are removed in the derived cliff overlay while
    /// the authored cliff/rim geometry and source-cell footprint stay exact.
    pub(super) fn draw_cliff_overlay_cell(
        &self,
        texture: &Texture2D,
        source: Rect,
        global_x: i32,
        global_y: i32,
    ) {
        debug_assert_eq!(source.w, TILE_SIZE);
        debug_assert_eq!(source.h, TILE_SIZE);
        self.draw_cliff_source_cell(
            texture,
            source,
            global_x as f32 * TILE_SIZE,
            global_y as f32 * TILE_SIZE,
        );
    }

    fn draw_diagonal_cliff_face(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        texture: &Texture2D,
        global_x: i32,
        global_y: i32,
        host_level: u8,
        face_segments: u8,
        chain_role: DiagonalChainRole,
        low_side_dx: i32,
        recipe: DiagonalFaceRecipe,
    ) {
        let world_x = global_x as f32 * TILE_SIZE;
        let world_y = global_y as f32 * TILE_SIZE;
        let body_rows = authored_body_rows(face_segments);

        // W14: the c1/c3 r7 crest is upper-level presentation, matching the
        // straight c2r7 crest. It must not add a receiver-facing height row.
        self.draw_cliff_source_cell(texture, recipe.crest, world_x, world_y);

        // Preserve W13's correct low-side receiver ownership for diagonal
        // visibility, but project exactly N receiver rows for an N-tier drop.
        let _ = chain_role;
        debug_assert!(matches!(low_side_dx, -1 | 1));
        let receiver_x = global_x + low_side_dx;
        let first_body_offset = 1_i32;

        for row in 0..body_rows {
            let target_y = global_y + first_body_offset + row as i32;
            if !self.cliff_projection_row_visible(manifest, receiver_x, target_y, host_level) {
                continue;
            }
            self.draw_cliff_source_cell(
                texture,
                recipe.body,
                world_x,
                world_y + (first_body_offset as f32 + row as f32) * TILE_SIZE,
            );
        }
        let foot_y = global_y + first_body_offset + body_rows as i32;
        if self.cliff_projection_row_visible(manifest, receiver_x, foot_y, host_level) {
            self.draw_cliff_source_cell(
                texture,
                recipe.foot,
                world_x,
                world_y + (first_body_offset as f32 + body_rows as f32) * TILE_SIZE,
            );
        }
    }

    pub(super) fn draw_cliff_vertical_face(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        texture: &Texture2D,
        global_x: i32,
        global_y: i32,
        host_level: u8,
        face_segments: u8,
        recipe: VerticalFaceRecipe,
    ) {
        let world_x = global_x as f32 * TILE_SIZE;
        let host_y = global_y as f32 * TILE_SIZE;
        let body_rows = authored_body_rows(face_segments);

        // W14: the authored crest belongs to the upper host row. It supplies
        // the top edge detail without increasing the receiver-facing wall depth.
        if let Some(leading) = recipe.leading {
            self.draw_cliff_source_cell(texture, leading, world_x, host_y);
        }

        for row in 0..body_rows {
            let target_y = global_y + 1 + row as i32;
            if !self.cliff_projection_row_visible(manifest, global_x, target_y, host_level) {
                continue;
            }
            self.draw_cliff_source_cell(
                texture,
                recipe.body,
                world_x,
                host_y + (row as f32 + 1.0) * TILE_SIZE,
            );
        }
        let foot_y = global_y + 1 + body_rows as i32;
        if self.cliff_projection_row_visible(manifest, global_x, foot_y, host_level) {
            self.draw_cliff_source_cell(
                texture,
                recipe.foot,
                world_x,
                host_y + (body_rows as f32 + 1.0) * TILE_SIZE,
            );
        }
    }

    /// Fixed connector/feature columns such as the authored ladder retain
    /// their pre-W14 receiver-row envelope. W14's host-row crest rule applies
    /// only to ordinary south cliff grammar; it must not silently relocate
    /// independent connector artwork.
    pub(super) fn draw_cliff_feature_vertical_face(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        texture: &Texture2D,
        global_x: i32,
        global_y: i32,
        host_level: u8,
        face_segments: u8,
        recipe: VerticalFaceRecipe,
    ) {
        let world_x = global_x as f32 * TILE_SIZE;
        let world_y = (global_y + 1) as f32 * TILE_SIZE;
        let body_rows = authored_body_rows(face_segments);

        let mut row_offset = 0_usize;
        if let Some(leading) = recipe.leading {
            if self.cliff_projection_row_visible(manifest, global_x, global_y + 1, host_level) {
                self.draw_cliff_source_cell(texture, leading, world_x, world_y);
            }
            row_offset += 1;
        }
        for row in 0..body_rows {
            let target_y = global_y + 1 + (row_offset + row) as i32;
            if !self.cliff_projection_row_visible(manifest, global_x, target_y, host_level) {
                continue;
            }
            self.draw_cliff_source_cell(
                texture,
                recipe.body,
                world_x,
                world_y + (row_offset + row) as f32 * TILE_SIZE,
            );
        }
        let foot_y = global_y + 1 + (row_offset + body_rows) as i32;
        if self.cliff_projection_row_visible(manifest, global_x, foot_y, host_level) {
            self.draw_cliff_source_cell(
                texture,
                recipe.foot,
                world_x,
                world_y + (row_offset + body_rows) as f32 * TILE_SIZE,
            );
        }
    }

    /// A south-facing LPC wall is perspective overhang, not terrain ownership.
    /// Concave contours can place another equal/higher platform beneath that
    /// overhang; in that case the raised platform occludes the projected wall.
    pub(super) fn cliff_projection_row_visible(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        global_x: i32,
        global_y: i32,
        host_level: u8,
    ) -> bool {
        self.surface_structural_level_at_global_in_manifest(manifest, global_x, global_y)
            .is_none_or(|target_level| target_level < host_level)
    }

    fn draw_water_facing_valley_if_anchor(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        texture: &Texture2D,
        center: haven_world::StructuralCellV2,
        global_x: i32,
        global_y: i32,
    ) {
        use haven_world::{CardinalDirectionV2, EdgeMaskV2};
        if !center.water_facing_edges.contains(EdgeMaskV2::SOUTH)
            || haven_world::waterfall_source_valid_v2(center, CardinalDirectionV2::South)
        {
            return;
        }

        let is_water_face = |x: i32| {
            self.surface_structural_at_global_in_manifest(manifest, x, global_y)
                .is_some_and(|cell| {
                    cell.water_facing_edges.contains(EdgeMaskV2::SOUTH)
                        && !haven_world::waterfall_source_valid_v2(cell, CardinalDirectionV2::South)
                })
        };
        if !is_water_face(global_x) {
            return;
        }

        let mut run_start = global_x;
        while is_water_face(run_start - 1) {
            run_start -= 1;
            if global_x - run_start > 64 {
                break;
            }
        }
        let offset = global_x - run_start;
        if offset.rem_euclid(3) != 0 || !is_water_face(global_x + 1) || !is_water_face(global_x + 2)
        {
            return;
        }

        self.draw_cliff_source_rect(
            texture,
            WATER_CLIFF_VALLEY_SOURCE,
            global_x as f32 * TILE_SIZE,
            (global_y + 1) as f32 * TILE_SIZE,
            TILE_SIZE * 3.0,
            TILE_SIZE * 3.0,
        );
    }

    pub(super) fn draw_cliff_source_cell(
        &self,
        texture: &Texture2D,
        source: Rect,
        world_x: f32,
        world_y: f32,
    ) {
        self.draw_cliff_source_rect(texture, source, world_x, world_y, TILE_SIZE, TILE_SIZE);
    }

    pub(super) fn draw_cliff_source_rect(
        &self,
        texture: &Texture2D,
        source: Rect,
        world_x: f32,
        world_y: f32,
        width: f32,
        height: f32,
    ) {
        self.draw_cliff_source_rect_flipped(
            texture, source, world_x, world_y, width, height, false,
        );
    }

    fn draw_cliff_source_rect_flipped(
        &self,
        texture: &Texture2D,
        source: Rect,
        world_x: f32,
        world_y: f32,
        width: f32,
        height: f32,
        flip_x: bool,
    ) {
        // Structural cliff quads must use the same device-pixel camera origin as
        // the terrain pass. Direct runtime_world_to_screen() leaves the smoothed
        // camera target fractional; adjacent 32px cliff quads then rasterize on
        // slightly different device-pixel boundaries and reveal grid seams while
        // the camera moves.
        let viewport = vec2(screen_width().max(1.0), screen_height().max(1.0));
        let snapped_origin = crate::runtime_terrain_plan::pixel_snapped_screen_origin(
            self.camera_target,
            viewport,
            self.camera_zoom,
        );
        let screen = vec2(world_x, world_y) + snapped_origin;
        draw_texture_ex(
            texture,
            screen.x,
            screen.y,
            WHITE,
            DrawTextureParams {
                dest_size: Some(vec2(width, height)),
                source: Some(source),
                flip_x,
                ..Default::default()
            },
        );
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::runtime_structural_cliff_shapes::authored_face_segments_for_edge;

    #[test]
    fn straight_face_matches_w14_demo_grounded_source_roles() {
        assert_eq!(SOUTH_STRAIGHT_FACE.leading, Some(Rect::new(64.0, 224.0, 32.0, 32.0)));
        assert_eq!(SOUTH_STRAIGHT_FACE.body, Rect::new(64.0, 96.0, 32.0, 32.0));
        assert_eq!(SOUTH_STRAIGHT_FACE.foot, Rect::new(64.0, 256.0, 32.0, 32.0));
    }

    #[test]
    fn diagonal_face_uses_same_crest_body_foot_height_grammar() {
        assert_eq!(SOUTH_WEST_DIAGONAL_FACE.crest, Rect::new(32.0, 224.0, 32.0, 32.0));
        assert_eq!(SOUTH_WEST_DIAGONAL_FACE.body, Rect::new(32.0, 96.0, 32.0, 32.0));
        assert_eq!(SOUTH_WEST_DIAGONAL_FACE.foot, Rect::new(32.0, 256.0, 32.0, 32.0));
    }

    #[test]
    fn multi_level_extension_repeats_only_middle_modules_beyond_the_first_tier() {
        assert_eq!(authored_body_rows(1), 0);
        assert_eq!(authored_body_rows(2), 1);
        assert_eq!(authored_body_rows(3), 2);
        assert_eq!(SOUTH_STRAIGHT_FACE.body, Rect::new(64.0, 96.0, 32.0, 32.0));
    }

    #[test]
    fn waterfall_frames_match_certified_multi_cell_envelopes() {
        assert_eq!(Rect::new(0.0, 0.0, 96.0, 160.0).w, TILE_SIZE * 3.0);
        assert_eq!(Rect::new(0.0, 160.0, 64.0, 224.0).h, TILE_SIZE * 7.0);
    }
    #[test]
    fn edge_specific_segments_preserve_level_2_mixed_drop_geometry() {
        let mut cell = haven_world::StructuralCellV2::default();
        cell.exposed_edges.insert(haven_world::EdgeMaskV2::SOUTH);
        cell.exposed_edges.insert(haven_world::EdgeMaskV2::WEST);
        cell.edge_deltas[2] = 4; // Level 2 -> Level 0 south.
        cell.edge_deltas[3] = 2; // Level 2 -> Level 1 west.
        cell.face_segments = 2;
        assert_eq!(authored_face_segments_for_edge(cell, haven_world::EdgeMaskV2::SOUTH), 2);
        assert_eq!(authored_face_segments_for_edge(cell, haven_world::EdgeMaskV2::WEST), 1);
    }

    #[test]
    fn generated_surface_preserves_resolved_diagonal_cliff_topology() {
        assert_eq!(
            runtime_cliff_visual_shape(true, CliffVisualShape::SouthWestDiagonal),
            CliffVisualShape::SouthWestDiagonal
        );
        assert_eq!(
            runtime_cliff_visual_shape(false, CliffVisualShape::SouthEastDiagonal),
            CliffVisualShape::SouthEastDiagonal
        );
    }

    #[test]
    fn exposed_cache_boundary_is_unknown_not_a_fake_cliff_receiver() {
        use haven_world::{CliffShape15, EdgeMaskV2};
        let shape = CliffShape15::from_mask(EdgeMaskV2::EAST)
            .expect("east cliff shape");
        assert!(!exposed_shape_neighbors_complete(shape, true, false, true, true));
        assert!(exposed_shape_neighbors_complete(shape, true, true, true, true));
    }

    #[test]
    fn full_diagonal_and_straight_level_2_faces_share_the_same_foot_row() {
        let level_2_segments = 2_u8;
        // W14: crest sits on the host; one body + foot ends at host+2.
        let straight_foot_offset = 1 + authored_body_rows(level_2_segments) as i32;
        let diagonal_foot_offset = 1 + authored_body_rows(level_2_segments) as i32;
        assert_eq!(straight_foot_offset, 2);
        assert_eq!(diagonal_foot_offset, 2);
    }
}

#[cfg(test)]
mod hw_cliff_02_regression_tests {
    use super::*;

    #[test]
    fn certified_ramp_corridor_keeps_one_step_retaining_walls_visible() {
        let step = haven_world::STRUCTURAL_ELEVATION_RESOLVER_STEP_V2;
        assert!(!structural_cliff_projection_visible(step, false));
        assert!(structural_cliff_projection_visible(step, true));
        assert!(structural_cliff_projection_visible(step * 2, false));
    }
}
