use super::*;

#[test]
fn coastal_grass_touching_water_remains_grass() {
    let mut map = TavernMap::empty_with(TileKind::Grass);
    for y in 3..=5 {
        for x in 5..=7 {
            map.set(x, y, TileKind::OceanShallow);
        }
    }

    let before = map.tiles.clone();
    let report = apply_coastline_tile_pass(&mut map, SceneBiome::Coastal);

    assert_eq!(map.tiles, before);
    assert_eq!(map.get(4, 4), TileKind::Grass);
    assert_eq!(report.total_mutations(), 0);
}

#[test]
fn isolated_water_is_not_deleted_to_make_rendering_easier() {
    let mut map = TavernMap::empty_with(TileKind::Grass);
    map.set(4, 4, TileKind::Water);

    let report = apply_coastline_tile_pass(&mut map, SceneBiome::Coastal);

    assert_eq!(map.get(4, 4), TileKind::Water);
    assert_eq!(report.removed_water_speckles, 0);
}

#[test]
fn narrow_land_is_not_eroded_to_make_rendering_easier() {
    let mut map = TavernMap::empty_with(TileKind::DeepWater);
    map.set(4, 4, TileKind::Grass);

    let report = apply_coastline_tile_pass(&mut map, SceneBiome::Coastal);

    assert_eq!(map.get(4, 4), TileKind::Grass);
    assert_eq!(report.eroded_land_spikes, 0);
}

#[test]
fn authored_water_depth_is_preserved() {
    let mut map = TavernMap::empty_with(TileKind::OceanDeep);
    map.set(4, 4, TileKind::OceanShallow);
    map.set(5, 4, TileKind::Grass);

    let before = map.tiles.clone();
    let report =
        normalize_shore_water_lifecycle_region(&mut map, 0, 0, 8, 8, 3);

    assert_eq!(map.tiles, before);
    assert_eq!(report.total_mutations(), 0);
}

#[test]
fn compatibility_profiles_are_semantics_preserving() {
    let mut map = TavernMap::empty_with(TileKind::Grass);
    map.set(4, 4, TileKind::OceanDeep);
    let before = map.tiles.clone();

    let report = apply_coastline_tile_pass_with_profile(
        &mut map,
        SceneBiome::Coastal,
        CoastlineGenerationProfile::mainland_shallow_stabilization(),
    );

    assert_eq!(map.tiles, before);
    assert_eq!(report.total_mutations(), 0);
}

#[test]
fn shoreline_analysis_observes_without_mutating() {
    let mut map = TavernMap::empty_with(TileKind::Grass);
    map.set(5, 4, TileKind::ShallowWater);
    let before = map.tiles.clone();

    let cell = analyze_shoreline_cell(&map, 4, 4);

    assert_eq!(cell.tile, TileKind::Grass);
    assert!(cell.touches_water);
    assert_eq!(map.tiles, before);
}
