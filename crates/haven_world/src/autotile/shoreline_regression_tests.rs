use haven_core::{MAP_H, MAP_W};
use super::super::shore_water_lifecycle::normalize_authored_depth_topology_region;
use super::*;

#[test]
fn unsupported_depth_topology_is_reported_by_rendering_not_rewritten_here() {
    let mut map = TavernMap::empty_with(TileKind::DeepWater);
    map.set(10, 9, TileKind::ShallowWater);
    map.set(10, 11, TileKind::ShallowWater);
    let before = map.tiles.clone();

    let changed = normalize_authored_depth_topology_region(&mut map, 8, 8, 12, 12);

    assert_eq!(changed, 0);
    assert_eq!(map.tiles, before);
}

#[test]
fn small_freshwater_body_keeps_authored_water_identity() {
    let mut map = TavernMap::empty_with(TileKind::Grass);
    for y in 10..13 {
        for x in 10..13 {
            map.set(x, y, TileKind::Water);
        }
    }
    let before = map.tiles.clone();

    let report =
        normalize_shore_water_lifecycle_region(&mut map, 0, 0, MAP_W as i32 - 1, MAP_H as i32 - 1, 3);

    assert_eq!(map.tiles, before);
    assert_eq!(report.total_mutations(), 0);
}

#[test]
fn deep_ocean_stays_deep_at_land_contact_until_hydrology_authors_otherwise() {
    let mut map = TavernMap::empty_with(TileKind::OceanDeep);
    map.set(10, 10, TileKind::Grass);
    let before = map.tiles.clone();

    apply_coastline_tile_pass(&mut map, SceneBiome::Coastal);

    assert_eq!(map.tiles, before);
    assert_eq!(map.get(10, 9), TileKind::OceanDeep);
}

#[test]
fn checkerboard_semantics_are_preserved_for_renderer_diagnostics() {
    let mut map = TavernMap::empty_with(TileKind::Grass);
    map.set(8, 8, TileKind::Sand);
    map.set(9, 8, TileKind::ShallowWater);
    map.set(8, 9, TileKind::ShallowWater);
    map.set(9, 9, TileKind::Sand);
    let before = map.tiles.clone();

    let report = apply_coastline_tile_pass(&mut map, SceneBiome::Coastal);

    assert_eq!(map.tiles, before);
    assert_eq!(report.unsupported_shapes_repaired, 0);
}

#[test]
fn explicit_sand_remains_sand_but_grass_is_not_promoted_to_beach() {
    let mut map = TavernMap::empty_with(TileKind::Grass);
    map.set(4, 4, TileKind::Sand);
    map.set(5, 4, TileKind::OceanShallow);
    let before = map.tiles.clone();

    apply_coastline_tile_pass(&mut map, SceneBiome::Coastal);

    assert_eq!(map.tiles, before);
    assert_eq!(map.get(4, 4), TileKind::Sand);
    assert_eq!(map.get(4, 5), TileKind::Grass);
}
