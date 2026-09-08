use super::*;
use haven_world::open_world::WorldTileCoord;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(super) enum StructuralConnectorKind {
    Ramp,
    Stairs,
    Ladder,
    Bridge,
}

/// Returns whether a resolved structural connector owns an intentional
/// walkable corridor through an otherwise blocking cliff boundary/face.
///
/// Cave entrances and waterfalls are not represented by this enum and remain
/// blocking interaction/flow hosts. Keep this match exhaustive so any future
/// connector kind must opt in to traversal explicitly at compile time.
pub(super) const fn connector_opens_walk_corridor(connector: StructuralConnectorKind) -> bool {
    match connector {
        StructuralConnectorKind::Ramp
        | StructuralConnectorKind::Stairs
        | StructuralConnectorKind::Ladder
        | StructuralConnectorKind::Bridge => true,
    }
}

pub(super) const LADDER_A_SOURCE: Rect = Rect {
    x: 352.0,
    y: 288.0,
    w: 32.0,
    h: 96.0,
};
pub(super) const CAVE_NARROW_SOURCE: Rect = Rect {
    x: 192.0,
    y: 288.0,
    w: 32.0,
    h: 96.0,
};
/// Reserved authored 3x3 portal for an explicit road/cart mountain tunnel.
/// W8 forbids selecting this from ordinary cave-host height.
#[allow(dead_code)]
pub(super) const CAVE_WIDE_SOURCE: Rect = Rect {
    x: 224.0,
    y: 288.0,
    w: 96.0,
    h: 96.0,
};
pub(super) const WATER_CLIFF_VALLEY_SOURCE: Rect = Rect {
    x: 288.0,
    y: 0.0,
    w: 96.0,
    h: 96.0,
};

fn ladder_host_is_straight_south_face(cell: haven_world::StructuralCellV2) -> bool {
    // ElizaWy's current ladder source is a straight south-face attachment.
    // Corner/diagonal cliff cells may visually contain south-facing pixels, but
    // placing a vertical ladder there makes it climb an angled wall and float
    // across the adjacent face. Fail closed until a matching diagonal authored
    // connector exists.
    cell.exposed_edges.0 == haven_world::EdgeMaskV2::SOUTH
}

fn classify_connector(
    from_tile: TileKind,
    to_tile: TileKind,
    delta: i16,
    stairs: Option<bool>,
    supported_cliff_face: bool,
) -> Option<StructuralConnectorKind> {
    if delta == 0 {
        return None;
    }
    if from_tile == TileKind::Bridge || to_tile == TileKind::Bridge {
        return Some(StructuralConnectorKind::Bridge);
    }
    // The reviewed cliff-sheet ramp/ladder/cave connector lane is a south-facing
    // host face. Do not open east/west/north structural collision until matching
    // visible source geometry is certified; invisible traversal is forbidden.
    if !supported_cliff_face {
        return None;
    }
    if let Some(forced_ladder) = stairs {
        if forced_ladder
            && delta.abs() <= haven_world::STRUCTURAL_ELEVATION_RESOLVER_STEP_V2
        {
            // H20S: one-level relief/ramp-transition edges are never ladder
            // hosts. A stale forced-ladder object fails closed here.
            return None;
        }
        return Some(
            if forced_ladder || delta.abs() > haven_world::STRUCTURAL_ELEVATION_RESOLVER_STEP_V2 {
                StructuralConnectorKind::Ladder
            } else {
                StructuralConnectorKind::Stairs
            },
        );
    }
    if delta.abs() == haven_world::STRUCTURAL_ELEVATION_RESOLVER_STEP_V2
        && from_tile == TileKind::MountainPath
        && to_tile == TileKind::MountainPath
    {
        return Some(StructuralConnectorKind::Ramp);
    }
    None
}

impl Game {
    pub(super) fn surface_tile_kind_at_global_in_manifest(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        coord: WorldTileCoord,
    ) -> Option<TileKind> {
        let address = haven_world::surface_tile_address(coord);
        let scene_id = manifest.scene_id_for_chunk(address.chunk);
        self.world
            .scene_by_id(&scene_id)
            .map(|scene| scene.map.get(address.local_x, address.local_y))
    }

    fn surface_stairs_connector_at_global_in_manifest(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        coord: WorldTileCoord,
    ) -> Option<bool> {
        let address = haven_world::surface_tile_address(coord);
        let scene_id = manifest.scene_id_for_chunk(address.chunk);
        let scene = self.world.scene_by_id(&scene_id)?;
        scene.map.objects.iter().rev().find_map(|object| {
            if object.kind != ObjectKind::Stairs
                || !object.contains_tile(address.local_x, address.local_y)
            {
                return None;
            }
            let forced_ladder = scene
                .map
                .object_state(object.id)
                .is_some_and(|state| state.eq_ignore_ascii_case("ladder"));
            Some(forced_ladder)
        })
    }

    pub(super) fn surface_cave_origin_at_global_in_manifest(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        coord: WorldTileCoord,
    ) -> bool {
        let address = haven_world::surface_tile_address(coord);
        let scene_id = manifest.scene_id_for_chunk(address.chunk);
        self.world.scene_by_id(&scene_id).is_some_and(|scene| {
            scene.map.objects.iter().any(|object| {
                object.kind == ObjectKind::CaveEntrance
                    && object.x == address.local_x
                    && object.y == address.local_y
            })
        })
    }

    pub(super) fn structural_connector_for_edge(
        &self,
        from: WorldTileCoord,
        to: WorldTileCoord,
        direction: haven_world::CardinalDirectionV2,
    ) -> Option<StructuralConnectorKind> {
        let manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
        self.structural_connector_for_edge_in_manifest(&manifest, from, to, direction)
    }

    fn structural_connector_for_edge_in_manifest(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        from: WorldTileCoord,
        to: WorldTileCoord,
        direction: haven_world::CardinalDirectionV2,
    ) -> Option<StructuralConnectorKind> {
        let source = self.surface_structural_at_global_in_manifest(manifest, from.x, from.y);
        let destination = self.surface_structural_at_global_in_manifest(manifest, to.x, to.y);
        let delta = source
            .map(|cell| cell.edge_delta(direction.edge_bit()))
            .filter(|delta| *delta != 0)
            .or_else(|| destination.map(|cell| -cell.edge_delta(direction.opposite().edge_bit())))
            .unwrap_or(0);
        if delta == 0 {
            return None;
        }

        let from_tile = self.surface_tile_kind_at_global_in_manifest(manifest, from)?;
        let to_tile = self.surface_tile_kind_at_global_in_manifest(manifest, to)?;
        let host_direction = if delta > 0 {
            direction
        } else {
            direction.opposite()
        };
        let supported_cliff_face =
            host_direction == haven_world::CardinalDirectionV2::South;

        // Common render-time cases must not scan the scene object list. Bridges
        // and generated MountainPath ramps are completely identified by their
        // semantic tiles. Unsupported N/E/W faces also reject before looking
        // for stairs, which removes thousands of pointless object scans from a
        // typical visible cliff frame.
        if from_tile == TileKind::Bridge || to_tile == TileKind::Bridge {
            return Some(StructuralConnectorKind::Bridge);
        }
        if !supported_cliff_face {
            return None;
        }
        if delta.abs() == haven_world::STRUCTURAL_ELEVATION_RESOLVER_STEP_V2
            && from_tile == TileKind::MountainPath
            && to_tile == TileKind::MountainPath
        {
            return Some(StructuralConnectorKind::Ramp);
        }

        let stairs = self
            .surface_stairs_connector_at_global_in_manifest(manifest, from)
            .or_else(|| self.surface_stairs_connector_at_global_in_manifest(manifest, to));
        let connector = classify_connector(
            from_tile,
            to_tile,
            delta,
            stairs,
            supported_cliff_face,
        )?;
        if connector == StructuralConnectorKind::Ladder {
            let host = if delta > 0 { source } else { destination };
            if !host.is_some_and(ladder_host_is_straight_south_face) {
                return None;
            }
            let lower_tile = if delta > 0 { to_tile } else { from_tile };
            let receiver_swimmable = haven_core::terrain_gameplay_profile(lower_tile).water_depth
                != haven_core::WaterDepthClass::None;
            let level_drop = u8::try_from(
                delta.abs() / haven_world::STRUCTURAL_ELEVATION_RESOLVER_STEP_V2
            )
            .unwrap_or(u8::MAX);
            if !haven_world::constructed_ladder_allowed_v1(level_drop, receiver_swimmable) {
                // Water-facing true cliffs are reserved for the natural-vine
                // climb lane. One-level relief is route-around terrain.
                return None;
            }
        }
        Some(connector)
    }

    pub(super) fn structural_connector_from_host_edge_in_manifest(
        &self,
        manifest: &haven_world::ContinuousSurfaceManifest,
        global_x: i32,
        global_y: i32,
        direction: haven_world::CardinalDirectionV2,
    ) -> Option<StructuralConnectorKind> {
        let from = WorldTileCoord::new(global_x, global_y);
        let to = match direction {
            haven_world::CardinalDirectionV2::North => WorldTileCoord::new(global_x, global_y - 1),
            haven_world::CardinalDirectionV2::East => WorldTileCoord::new(global_x + 1, global_y),
            haven_world::CardinalDirectionV2::South => WorldTileCoord::new(global_x, global_y + 1),
            haven_world::CardinalDirectionV2::West => WorldTileCoord::new(global_x - 1, global_y),
        };
        self.structural_connector_for_edge_in_manifest(manifest, from, to, direction)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn connector_source_envelopes_stay_on_certified_grid() {
        assert_eq!(LADDER_A_SOURCE, Rect::new(352.0, 288.0, 32.0, 96.0));
        assert_eq!(CAVE_NARROW_SOURCE, Rect::new(192.0, 288.0, 32.0, 96.0));
        assert_eq!(CAVE_WIDE_SOURCE, Rect::new(224.0, 288.0, 96.0, 96.0));
        assert_eq!(WATER_CLIFF_VALLEY_SOURCE, Rect::new(288.0, 0.0, 96.0, 96.0));
    }

    #[test]
    fn path_pair_opens_one_level_as_ramp_only() {
        assert_eq!(
            classify_connector(
                TileKind::MountainPath,
                TileKind::MountainPath,
                2,
                None,
                true
            ),
            Some(StructuralConnectorKind::Ramp)
        );
        assert_eq!(
            classify_connector(
                TileKind::MountainPath,
                TileKind::MountainPath,
                4,
                None,
                true
            ),
            None
        );
    }

    #[test]
    fn stairs_upgrade_to_ladder_for_multi_level_face() {
        assert_eq!(
            classify_connector(TileKind::Grass, TileKind::Grass, 2, Some(false), true),
            Some(StructuralConnectorKind::Stairs)
        );
        assert_eq!(
            classify_connector(TileKind::Grass, TileKind::Grass, 4, Some(false), true),
            Some(StructuralConnectorKind::Ladder)
        );
        assert_eq!(
            classify_connector(TileKind::Grass, TileKind::Grass, 2, Some(true), true),
            None,
            "forced ladders cannot turn one-level relief into a cliff connector"
        );
    }

    #[test]
    fn ladder_hosts_require_one_straight_south_face() {
        let straight = haven_world::StructuralCellV2 {
            exposed_edges: haven_world::EdgeMaskV2(haven_world::EdgeMaskV2::SOUTH),
            ..haven_world::StructuralCellV2::default()
        };
        let angled = haven_world::StructuralCellV2 {
            exposed_edges: haven_world::EdgeMaskV2(
                haven_world::EdgeMaskV2::SOUTH | haven_world::EdgeMaskV2::EAST,
            ),
            ..haven_world::StructuralCellV2::default()
        };
        assert!(ladder_host_is_straight_south_face(straight));
        assert!(!ladder_host_is_straight_south_face(angled));
    }

    #[test]
    fn unsupported_cliff_face_never_opens_invisible_ramp_or_ladder() {
        assert_eq!(
            classify_connector(
                TileKind::MountainPath,
                TileKind::MountainPath,
                2,
                None,
                false
            ),
            None
        );
        assert_eq!(
            classify_connector(TileKind::Grass, TileKind::Grass, 4, Some(true), false),
            None
        );
    }

    #[test]
    fn bridge_tile_is_structural_crossing_authority() {
        assert_eq!(
            classify_connector(TileKind::Bridge, TileKind::Water, 2, None, false),
            Some(StructuralConnectorKind::Bridge)
        );
    }

    #[test]
    fn every_structural_connector_kind_explicitly_opens_its_walk_corridor() {
        for connector in [
            StructuralConnectorKind::Ramp,
            StructuralConnectorKind::Stairs,
            StructuralConnectorKind::Ladder,
            StructuralConnectorKind::Bridge,
        ] {
            assert!(connector_opens_walk_corridor(connector));
        }
    }
}
