//! Coastal structural presentation helpers.
//!
//! Source-native coastal structural helpers.
//!
//! Havenwild worldgen no longer manufactures a generic one-level coastal cliff
//! vocabulary. Generated cliffs use the same even structural tiers as inland
//! landforms (0/2/4), while odd tiers remain reserved exclusively for the
//! authored LPC 3x4 ramp corridor. Water-facing true cliffs remain a separate
//! connector class and never receive a fabricated constructed ladder.

use std::collections::VecDeque;

use haven_core::TileKind;

pub(crate) const COASTAL_CORE_CLEARANCE_CELLS: u16 = 8;

pub(crate) fn marine_shore_tile(tile: TileKind) -> bool {
    matches!(
        tile,
        TileKind::OceanDeep
            | TileKind::OceanShallow
            | TileKind::RiverMouthBlend
            | TileKind::Sand
            | TileKind::WetSand
            | TileKind::PebbleShore
            | TileKind::ShoreFoam
    )
}

pub(crate) fn shoreline_distance_cells(
    marine_shore: &[bool],
    present: &[bool],
    width: usize,
    height: usize,
    max_distance: u16,
) -> Vec<u16> {
    let unreachable = max_distance.saturating_add(1);
    let mut distance = vec![unreachable; marine_shore.len()];
    let mut queue = VecDeque::new();
    for (index, shore) in marine_shore.iter().copied().enumerate() {
        if shore && present[index] {
            distance[index] = 0;
            queue.push_back(index);
        }
    }
    while let Some(index) = queue.pop_front() {
        let next_distance = distance[index].saturating_add(1);
        if next_distance > max_distance {
            continue;
        }
        let x = index % width;
        let y = index / width;
        for neighbor in [
            y.checked_sub(1).map(|ny| ny * width + x),
            (x + 1 < width).then_some(y * width + x + 1),
            (y + 1 < height).then_some((y + 1) * width + x),
            x.checked_sub(1).map(|nx| y * width + nx),
        ]
        .into_iter()
        .flatten()
        {
            if !present[neighbor] || distance[neighbor] <= next_distance {
                continue;
            }
            distance[neighbor] = next_distance;
            queue.push_back(neighbor);
        }
    }
    distance
}

pub(crate) fn choose_shoreline_ladder_hosts(
    _levels: &[u8],
    _marine_shore: &[bool],
    _present: &[bool],
    _protected: &[bool],
    _width: usize,
    _height: usize,
    _seed: u64,
) -> Vec<usize> {
    // Source-native rule: a constructed ladder is not valid on a water-facing
    // cliff. A future NaturalVine/shore connector must arrive as an authored
    // source-backed family; until then generation fails closed instead of
    // synthesizing a rotated/mirrored ladder.
    Vec::new()
}
