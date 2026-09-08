use super::*;

#[test]
fn exact_editor_paint_does_not_expand_one_land_cell_into_a_shallow_square() {
    let mut map = TavernMap::empty_with(TileKind::DeepWater);
    map.set(8, 8, TileKind::Dirt);

    let report = apply_editor_terrain_paint_policy(&mut map, 8, 8, 8, 8, TerrainPaintMode::Exact)
        .expect("exact terrain paint");

    assert_eq!(report.total_mutations(), 0);
    assert_eq!(map.get(8, 8), TileKind::Dirt);
    for (x, y) in [
        (7, 7),
        (8, 7),
        (9, 7),
        (7, 8),
        (9, 8),
        (7, 9),
        (8, 9),
        (9, 9),
    ] {
        assert_eq!(map.get(x, y), TileKind::DeepWater);
    }
}

#[test]
fn coastline_mode_explicitly_builds_a_shallow_buffer() {
    let mut map = TavernMap::empty_with(TileKind::DeepWater);
    map.set(8, 8, TileKind::Sand);

    let report =
        apply_editor_terrain_paint_policy(&mut map, 8, 8, 8, 8, TerrainPaintMode::Coastline)
            .expect("coastline terrain paint");

    assert!(report.total_mutations() > 0);
    assert_eq!(map.get(8, 8), TileKind::Sand);
    for (x, y) in [(7, 8), (9, 8), (8, 7), (8, 9)] {
        assert_eq!(map.get(x, y), TileKind::ShallowWater);
    }
}

#[test]
fn hydrology_mode_uses_canonical_one_tile_shallow_rim() {
    let mut map = TavernMap::empty_with(TileKind::DeepWater);
    map.set(8, 8, TileKind::Dirt);

    let report =
        apply_editor_terrain_paint_policy(&mut map, 8, 8, 8, 8, TerrainPaintMode::Hydrology)
            .expect("hydrology terrain paint");

    assert!(report.total_mutations() > 0);
    assert_eq!(map.get(8, 8), TileKind::Dirt);
    for (x, y) in [(7, 8), (9, 8), (8, 7), (8, 9)] {
        assert_eq!(map.get(x, y), TileKind::ShallowWater);
    }
    assert_eq!(map.get(6, 8), TileKind::DeepWater);
    assert_eq!(map.get(10, 8), TileKind::DeepWater);
}

#[test]
fn exact_editor_paint_preserves_incompatible_mountain_path_for_diagnostics() {
    let mut map = TavernMap::empty_with(TileKind::Grass);
    map.set(8, 8, TileKind::MountainPath);
    map.set(9, 8, TileKind::Sand);

    let report = apply_editor_terrain_paint_policy(&mut map, 8, 8, 9, 8, TerrainPaintMode::Exact)
        .expect("exact terrain paint");

    assert_eq!(report.total_mutations(), 0);
    assert!(report.unsupported_contacts > 0);
    assert_eq!(map.get(8, 8), TileKind::MountainPath);
    assert_eq!(map.get(9, 8), TileKind::Sand);
}

#[test]
fn coastline_mode_can_apply_the_authored_v7_road_shoulder() {
    let mut map = TavernMap::empty_with(TileKind::Grass);
    map.set(8, 8, TileKind::MountainPath);
    map.set(9, 8, TileKind::Sand);

    let report =
        apply_editor_terrain_paint_policy(&mut map, 8, 8, 9, 8, TerrainPaintMode::Coastline)
            .expect("coastline terrain paint");

    assert!(report.total_mutations() > 0);
    assert_eq!(map.get(8, 8), TileKind::Road);
    assert_eq!(map.get(9, 8), TileKind::Sand);
}
