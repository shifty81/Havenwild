#[cfg(test)]
mod surface_maintenance_tests {
    use super::*;

    #[test]
    fn maintenance_is_throttled_until_deadline_or_chunk_change() {
        assert!(!surface_maintenance_due(10.10, 10.25, false));
        assert!(surface_maintenance_due(10.25, 10.25, false));
        assert!(surface_maintenance_due(10.10, 10.25, true));
    }

    #[test]
    fn hydrology_signature_changes_only_with_residency_state() {
        let stable = HydrologyResidencySignature {
            active_x: 0,
            active_y: 0,
            preload_count: 25,
            loaded_count: 25,
        };
        let changed = HydrologyResidencySignature {
            active_x: 1,
            ..stable
        };
        assert_ne!(stable, changed);
        assert_eq!(stable.loaded_count, stable.preload_count);
    }

    #[test]
    fn one_level_straight_cliff_blocks_one_projected_face_row() {
        let host = haven_world::StructuralCellV2 {
            exposed_edges: haven_world::EdgeMaskV2(haven_world::EdgeMaskV2::SOUTH),
            face_segments: 1,
            ..Default::default()
        };
        assert_eq!(
            structural_south_face_projection_depth(
                host,
                crate::runtime_structural_cliff_shapes::DiagonalChainRole::Isolated,
            ),
            1
        );
        assert!(tile_within_south_face_projection(10, 11, 1));
        assert!(!tile_within_south_face_projection(10, 12, 1));
    }

    #[test]
    fn one_level_rounded_corner_matches_uniform_straight_depth() {
        let host = haven_world::StructuralCellV2 {
            exposed_edges: haven_world::EdgeMaskV2(
                haven_world::EdgeMaskV2::SOUTH | haven_world::EdgeMaskV2::WEST,
            ),
            face_segments: 1,
            ..Default::default()
        };
        assert_eq!(
            structural_south_face_projection_depth(
                host,
                crate::runtime_structural_cliff_shapes::DiagonalChainRole::Isolated,
            ),
            1
        );
        assert_eq!(
            structural_south_face_projection_depth(
                host,
                crate::runtime_structural_cliff_shapes::DiagonalChainRole::Middle,
            ),
            1
        );
    }

    #[test]
    fn north_exposed_diagonal_turn_keeps_uniform_collision_depth() {
        let host = haven_world::StructuralCellV2 {
            exposed_edges: haven_world::EdgeMaskV2(
                haven_world::EdgeMaskV2::NORTH
                    | haven_world::EdgeMaskV2::SOUTH
                    | haven_world::EdgeMaskV2::WEST,
            ),
            face_segments: 1,
            ..Default::default()
        };
        assert_eq!(
            structural_south_face_projection_depth(
                host,
                crate::runtime_structural_cliff_shapes::DiagonalChainRole::Isolated,
            ),
            1
        );
        assert_eq!(
            structural_south_face_projection_depth(
                host,
                crate::runtime_structural_cliff_shapes::DiagonalChainRole::Middle,
            ),
            1
        );
    }

    #[test]
    fn authored_terminal_matches_uniform_one_level_projection() {
        for mask in [
            haven_world::EdgeMaskV2::EAST
                | haven_world::EdgeMaskV2::SOUTH
                | haven_world::EdgeMaskV2::WEST,
            haven_world::EdgeMaskV2::NORTH
                | haven_world::EdgeMaskV2::EAST
                | haven_world::EdgeMaskV2::SOUTH
                | haven_world::EdgeMaskV2::WEST,
        ] {
            let host = haven_world::StructuralCellV2 {
                exposed_edges: haven_world::EdgeMaskV2(mask),
                face_segments: 1,
                ..Default::default()
            };
            assert_eq!(
                structural_south_face_projection_depth(
                    host,
                    crate::runtime_structural_cliff_shapes::DiagonalChainRole::Isolated,
                ),
                1
            );
        }
    }

    #[test]
    fn multi_level_cliff_projection_depth_tracks_rendered_face() {
        let straight = haven_world::StructuralCellV2 {
            exposed_edges: haven_world::EdgeMaskV2(haven_world::EdgeMaskV2::SOUTH),
            face_segments: 3,
            ..Default::default()
        };
        assert_eq!(
            structural_south_face_projection_depth(
                straight,
                crate::runtime_structural_cliff_shapes::DiagonalChainRole::Isolated,
            ),
            3
        );
        assert!(tile_within_south_face_projection(4, 7, 3));
        assert!(!tile_within_south_face_projection(4, 8, 3));
    }
    #[test]
    fn tier_delta_depth_is_uniform_for_straight_diagonal_and_terminal_roles() {
        use haven_world::EdgeMaskV2;
        for (tiers, expected_depth) in [(1_u8, 1_i32), (2, 2), (3, 3), (4, 4)] {
            for mask in [
                EdgeMaskV2::SOUTH,
                EdgeMaskV2::SOUTH | EdgeMaskV2::WEST,
                EdgeMaskV2::EAST | EdgeMaskV2::SOUTH,
                EdgeMaskV2::EAST | EdgeMaskV2::SOUTH | EdgeMaskV2::WEST,
            ] {
                let host = haven_world::StructuralCellV2 {
                    exposed_edges: haven_world::EdgeMaskV2(mask),
                    face_segments: tiers,
                    ..Default::default()
                };
                for chain_role in [
                    crate::runtime_structural_cliff_shapes::DiagonalChainRole::Isolated,
                    crate::runtime_structural_cliff_shapes::DiagonalChainRole::Middle,
                ] {
                    assert_eq!(
                        structural_south_face_projection_depth(host, chain_role),
                        expected_depth,
                        "tier {tiers} mask {mask:#06b} must keep uniform contour depth",
                    );
                }
            }
        }
    }

    #[test]
    fn authored_terminal_collision_covers_natural_three_column_width() {
        let terminal = haven_world::StructuralCellV2 {
            exposed_edges: haven_world::EdgeMaskV2(
                haven_world::EdgeMaskV2::EAST
                    | haven_world::EdgeMaskV2::SOUTH
                    | haven_world::EdgeMaskV2::WEST,
            ),
            face_segments: 1,
            ..Default::default()
        };
        assert!(structural_south_face_covers_column(10, 9, terminal));
        assert!(structural_south_face_covers_column(10, 10, terminal));
        assert!(structural_south_face_covers_column(10, 11, terminal));
        assert!(!structural_south_face_covers_column(10, 8, terminal));
        assert!(!structural_south_face_covers_column(10, 12, terminal));

        let straight = haven_world::StructuralCellV2 {
            exposed_edges: haven_world::EdgeMaskV2(haven_world::EdgeMaskV2::SOUTH),
            ..Default::default()
        };
        assert!(structural_south_face_covers_column(10, 10, straight));
        assert!(!structural_south_face_covers_column(10, 9, straight));
    }

}
