use haven_core::TileKind;

use super::{
    cell_variant_seed, lpc_mapped_terrain_manifest, mapped_terrain_name, LpcMappedTerrainEntry,
};

/// Resolves a pure owner fill from an arbitrary global terrain sampler.
///
/// Exterior partitions are storage chunks of one surface. The sampler may
/// therefore read across partition edges, unlike the legacy TavernMap-only
/// resolver whose out-of-bounds cells intentionally terminate at one map.
pub fn lpc_mapped_terrain_runtime_entry_for_tile_sampler<F>(
    tile_at: &F,
    x: i32,
    y: i32,
) -> Option<LpcMappedTerrainEntry>
where
    F: Fn(i32, i32) -> Option<TileKind>,
{
    let owner = sampled_mapped_terrain_at(tile_at, x, y)?;
    let manifest = lpc_mapped_terrain_manifest().ok()?;
    if sampled_touches_different_mapped_material(tile_at, x, y, owner) {
        return manifest.quiet_entry_for_corners([owner; 4]);
    }
    manifest.entry_for_corners([owner; 4], cell_variant_seed(x, y))
}

/// Resolves one exact mixed V7 tuple from an arbitrary global terrain sampler.
/// Unsupported contacts intentionally return None so owner fill + diagnostics
/// can route the pair to the W77 hand-authoring workbench.
pub fn lpc_mapped_terrain_transition_entry_for_tile_sampler<F>(
    tile_at: &F,
    x: i32,
    y: i32,
) -> Option<LpcMappedTerrainEntry>
where
    F: Fn(i32, i32) -> Option<TileKind>,
{
    let corners = sampled_mapped_terrain_corners(tile_at, x, y)?;
    let manifest = lpc_mapped_terrain_manifest().ok()?;
    let seed = cell_variant_seed(x, y);
    manifest
        .entry_for_corners(corners, seed)
        .filter(|entry| entry.is_mixed)
}

fn sampled_mapped_terrain_corners<F>(tile_at: &F, x: i32, y: i32) -> Option<[&'static str; 4]>
where
    F: Fn(i32, i32) -> Option<TileKind>,
{
    Some([
        sampled_mapped_terrain_at(tile_at, x, y)?,
        sampled_mapped_terrain_at(tile_at, x + 1, y)?,
        sampled_mapped_terrain_at(tile_at, x, y + 1)?,
        sampled_mapped_terrain_at(tile_at, x + 1, y + 1)?,
    ])
}

fn sampled_mapped_terrain_at<F>(tile_at: &F, x: i32, y: i32) -> Option<&'static str>
where
    F: Fn(i32, i32) -> Option<TileKind>,
{
    let tile = tile_at(x, y)?;
    if matches!(tile, TileKind::DeepWater | TileKind::OceanDeep)
        && (sampled_touches_same_domain_shallow_water(tile_at, x, y, tile)
            || sampled_touches_authored_medium_water_land_contact(tile_at, x, y))
    {
        return Some("Water");
    }
    mapped_terrain_name(tile)
}

fn sampled_touches_same_domain_shallow_water<F>(
    tile_at: &F,
    x: i32,
    y: i32,
    deep_tile: TileKind,
) -> bool
where
    F: Fn(i32, i32) -> Option<TileKind>,
{
    [
        (0, -1),
        (1, 0),
        (0, 1),
        (-1, 0),
        (-1, -1),
        (1, -1),
        (-1, 1),
        (1, 1),
    ]
    .into_iter()
    .filter_map(|(offset_x, offset_y)| tile_at(x + offset_x, y + offset_y))
    .any(|neighbor| match deep_tile {
        TileKind::OceanDeep => neighbor == TileKind::OceanShallow,
        TileKind::DeepWater => matches!(neighbor, TileKind::ShallowWater | TileKind::Water),
        _ => false,
    })
}

fn sampled_touches_authored_medium_water_land_contact<F>(tile_at: &F, x: i32, y: i32) -> bool
where
    F: Fn(i32, i32) -> Option<TileKind>,
{
    for offset_y in -1..=1 {
        for offset_x in -1..=1 {
            if offset_x == 0 && offset_y == 0 {
                continue;
            }
            let Some(neighbor) = tile_at(x + offset_x, y + offset_y).and_then(mapped_terrain_name)
            else {
                continue;
            };
            if matches!(neighbor, "Grass" | "Sand" | "Dirt_Brown" | "Dirt_Tan") {
                return true;
            }
        }
    }
    false
}
fn sampled_touches_different_mapped_material<F>(
    tile_at: &F,
    x: i32,
    y: i32,
    owner: &'static str,
) -> bool
where
    F: Fn(i32, i32) -> Option<TileKind>,
{
    for offset_y in -1..=1 {
        for offset_x in -1..=1 {
            if offset_x == 0 && offset_y == 0 {
                continue;
            }
            let Some(neighbor) = sampled_mapped_terrain_at(tile_at, x + offset_x, y + offset_y)
            else {
                continue;
            };
            if neighbor != owner {
                return true;
            }
        }
    }
    false
}

