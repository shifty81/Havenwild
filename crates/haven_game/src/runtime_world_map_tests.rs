#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn landmass_region_matching_accepts_project_prefixes() {
        assert!(region_matches_landmass("mainland", "Mainland"));
        assert!(region_matches_landmass("havenwild_mainland", "Mainland"));
        assert!(region_matches_landmass("mainland", "Alderreach"));
        assert!(region_matches_landmass("havenwild_mainland", "Alderreach"));
        assert!(!region_matches_landmass("gullmere", "Alderreach"));
    }

    #[test]
    fn world_map_colors_keep_marine_and_land_visually_distinct() {
        assert_ne!(
            world_map_tile_color(TileKind::OceanDeep),
            world_map_tile_color(TileKind::Grass)
        );
        assert_ne!(
            world_map_tile_color(TileKind::OceanShallow),
            world_map_tile_color(TileKind::Sand)
        );
    }

    #[test]
    fn world_map_clipping_stays_inside_viewport() {
        let viewport = Rect::new(10.0, 10.0, 20.0, 20.0);
        let clipped = rect_intersection(Rect::new(0.0, 15.0, 50.0, 10.0), viewport)
            .expect("overlapping map rectangle");
        assert_eq!(clipped, Rect::new(10.0, 15.0, 20.0, 10.0));
    }

    #[test]
    fn explored_map_priority_keeps_routes_and_cliffs_visible() {
        assert!(world_map_code_priority(7) > world_map_code_priority(6));
        assert!(world_map_code_priority(6) > world_map_code_priority(5));
        assert!(world_map_code_priority(8) > world_map_code_priority(3));
        assert!(world_map_code_priority(11) > world_map_code_priority(3));
    }

    #[test]
    fn forest_habitat_has_distinct_reveal_all_color() {
        assert_ne!(geographic_overview_color(11), geographic_overview_color(3));
    }

    #[test]
    fn explored_map_bounds_follow_revealed_cells_not_storage_partitions() {
        let mut first = empty_world_map_chunk_snapshot(ChunkCoord::new(0, 0));
        first.cells[10 * first.cols + 12] = 3;
        let mut chunks = BTreeMap::new();
        chunks.insert((0, 0), first);
        assert_eq!(explored_world_map_bounds(&chunks), Some((24, 20, 26, 22)));

        let mut second = empty_world_map_chunk_snapshot(ChunkCoord::new(1, -1));
        second.cells[5 * second.cols + 2] = 7;
        chunks.insert((1, -1), second);
        assert_eq!(
            explored_world_map_bounds(&chunks),
            Some((24, -(MAP_H as i32) + 10, 102, 22))
        );
    }

    #[test]
    fn unexplored_cells_do_not_contribute_map_bounds() {
        let mut chunks = BTreeMap::new();
        chunks.insert((0, 0), empty_world_map_chunk_snapshot(ChunkCoord::new(0, 0)));
        assert_eq!(explored_world_map_bounds(&chunks), None);
    }

    #[test]
    fn natural_object_markers_cover_existing_flora_categories() {
        assert!(natural_object_map_color(ObjectKind::Tree).is_some());
        assert!(natural_object_map_color(ObjectKind::Bush).is_some());
        assert!(natural_object_map_color(ObjectKind::Herb).is_some());
        assert!(natural_object_map_color(ObjectKind::Mushroom).is_some());
        assert!(natural_object_map_color(ObjectKind::Table).is_none());
    }
}
