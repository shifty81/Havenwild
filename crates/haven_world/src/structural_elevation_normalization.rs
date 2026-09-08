//! H20S structural elevation normalization authority.
//!
//! True Havenwild cliffs are Level 2+ for the current production grammar.
//! Odd structural levels are reserved for certified authored MountainPath ramp
//! transitions. Legacy/AUTO MountainRock is promoted to Level 2. Standalone
//! Level-1 regions are either promoted to a real plateau when broad, or
//! collapsed to low-relief Level 0 when thin/small. Complete six-cell LPC ramp
//! corridors preserve their exact two-level span across partition borders,
//! including 2 -> 1 -> 0 and nested 4 -> 3 -> 2 highland routes.

use std::collections::{BTreeMap, BTreeSet, VecDeque};

use haven_core::{TavernMap, TileKind, MAP_H, MAP_W};

use crate::{
    open_world::ChunkCoord,
    structural_landform_ramps::directional_ramp_corridor_levels,
};

pub const STRUCTURAL_ELEVATION_NORMALIZATION_V1_SCHEMA: &str =
    "havenwild.structural_elevation_normalization.v1";

const BROAD_LEVEL_ONE_MIN_CELLS: usize = 12;
const BROAD_LEVEL_ONE_MIN_SPAN: i32 = 3;

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct StructuralElevationNormalizationReportV1 {
    pub promoted_legacy_mountainrock: usize,
    pub promoted_level_one_cells: usize,
    pub collapsed_level_one_cells: usize,
    pub certified_ramps: usize,
    pub certified_ramp_cells: usize,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum CertifiedRampOrientationV1 {
    RiseRight,
    RiseLeft,
}

// Retain the internal short name while restoring the public editor/runtime
// compatibility contract consumed by haven_editor. AC1 generalized the ramp
// planner but must not retire the certified V1 API used by authoring tools.
type RampOrientation = CertifiedRampOrientationV1;

pub fn normalize_partitioned_structural_elevation_v1(
    partitions: &mut [(ChunkCoord, TavernMap)],
) -> StructuralElevationNormalizationReportV1 {
    let mut report = StructuralElevationNormalizationReportV1::default();
    if partitions.is_empty() {
        return report;
    }

    let mut location = BTreeMap::<(i32, i32), (usize, i32, i32)>::new();
    for (partition_index, (chunk, _)) in partitions.iter().enumerate() {
        for local_y in 0..MAP_H as i32 {
            for local_x in 0..MAP_W as i32 {
                location.insert(
                    (
                        chunk.x * MAP_W as i32 + local_x,
                        chunk.y * MAP_H as i32 + local_y,
                    ),
                    (partition_index, local_x, local_y),
                );
            }
        }
    }

    let tile_at = |partitions: &[(ChunkCoord, TavernMap)], gx: i32, gy: i32| {
        location.get(&(gx, gy)).map(|(index, x, y)| partitions[*index].1.get(*x, *y))
    };

    let level_at = |partitions: &[(ChunkCoord, TavernMap)], gx: i32, gy: i32| {
        location.get(&(gx, gy)).map(|(index, x, y)| {
            partitions[*index]
                .1
                .get_structural_level(*x, *y)
                .unwrap_or_else(|| {
                    if partitions[*index].1.get(*x, *y) == TileKind::MountainRock {
                        2
                    } else {
                        0
                    }
                })
        })
    };

    // First migrate AUTO MountainRock to an explicit Level-2 plateau. This
    // removes the legacy one-face fallback from the normalized runtime domain.
    for (_, map) in partitions.iter_mut() {
        for y in 0..MAP_H as i32 {
            for x in 0..MAP_W as i32 {
                if map.get_structural_level(x, y).is_none() && map.get(x, y) == TileKind::MountainRock {
                    map.set_structural_level(x, y, Some(2));
                    report.promoted_legacy_mountainrock += 1;
                }
            }
        }
    }

    // Discover complete authored MountainPath corridors globally so a storage
    // partition boundary can never split or invalidate a ramp.
    let mut ramp_hosts = Vec::<(i32, i32, RampOrientation)>::new();
    for &(gx, gy) in location.keys() {
        if tile_at(partitions, gx, gy) != Some(TileKind::MountainPath) {
            continue;
        }
        let right = RISE_RIGHT_OFFSETS
            .iter()
            .all(|(dx, dy)| tile_at(partitions, gx + dx, gy + dy) == Some(TileKind::MountainPath));
        let left = RISE_LEFT_OFFSETS
            .iter()
            .all(|(dx, dy)| tile_at(partitions, gx + dx, gy + dy) == Some(TileKind::MountainPath));
        match (right, left) {
            (true, false) => ramp_hosts.push((gx, gy, RampOrientation::RiseRight)),
            (false, true) => ramp_hosts.push((gx, gy, RampOrientation::RiseLeft)),
            (true, true) => ramp_hosts.push((
                gx,
                gy,
                if (gx ^ gy) & 1 == 0 {
                    RampOrientation::RiseRight
                } else {
                    RampOrientation::RiseLeft
                },
            )),
            (false, false) => {}
        }
    }
    ramp_hosts.sort_unstable_by_key(|(x, y, orientation)| {
        (*y, *x, matches!(orientation, RampOrientation::RiseLeft))
    });

    let mut ramp_cells = BTreeSet::<(i32, i32)>::new();
    let mut accepted_ramps = Vec::new();
    for (gx, gy, orientation) in ramp_hosts {
        let offsets = ramp_offsets(orientation);
        let footprint = offsets
            .iter()
            .map(|(dx, dy)| (gx + dx, gy + dy))
            .collect::<Vec<_>>();
        if footprint.iter().any(|coord| ramp_cells.contains(coord)) {
            continue;
        }
        // Legacy/editor-authored certified ramps may consist of the complete
        // six-cell MountainPath footprint without pre-authored structural
        // levels. Preserve that established V1 contract by interpreting a
        // wholly-unlevelled certified footprint as the outer 2->0 descent.
        // AC1-generated and nested ramps carry explicit endpoint levels, so
        // those continue through the generalized two-level-drop authority.
        let footprint_has_explicit_level = footprint.iter().any(|(fx, fy)| {
            location
                .get(&(*fx, *fy))
                .and_then(|(index, x, y)| partitions[*index].1.get_structural_level(*x, *y))
                .is_some()
        });
        let (upper_level, lower_level) = if footprint_has_explicit_level {
            let upper_level = level_at(partitions, gx, gy).unwrap_or(0);
            let (lower_dx, lower_dy) = *offsets.last().expect("ramp offsets are non-empty");
            let lower_level = level_at(partitions, gx + lower_dx, gy + lower_dy).unwrap_or(0);
            (upper_level, lower_level)
        } else {
            (2, 0)
        };
        if directional_ramp_corridor_levels(upper_level, lower_level).is_none() {
            continue;
        }
        ramp_cells.extend(footprint);
        accepted_ramps.push((gx, gy, orientation, upper_level, lower_level));
    }

    // Classify every non-ramp explicit Level-1 connected component. Broad
    // regions are legacy plateaus and promote to 2. Thin/small shelves are
    // low-relief detail and collapse to 0 rather than remaining cliff walls.
    let mut unvisited = BTreeSet::new();
    for &(gx, gy) in location.keys() {
        if !ramp_cells.contains(&(gx, gy)) && level_at(partitions, gx, gy) == Some(1) {
            unvisited.insert((gx, gy));
        }
    }
    while let Some(seed) = unvisited.iter().next().copied() {
        let mut queue = VecDeque::from([seed]);
        let mut component = Vec::new();
        unvisited.remove(&seed);
        while let Some((x, y)) = queue.pop_front() {
            component.push((x, y));
            for (dx, dy) in [(0, -1), (1, 0), (0, 1), (-1, 0)] {
                let next = (x + dx, y + dy);
                if unvisited.remove(&next) {
                    queue.push_back(next);
                }
            }
        }
        let min_x = component.iter().map(|(x, _)| *x).min().unwrap_or(seed.0);
        let max_x = component.iter().map(|(x, _)| *x).max().unwrap_or(seed.0);
        let min_y = component.iter().map(|(_, y)| *y).min().unwrap_or(seed.1);
        let max_y = component.iter().map(|(_, y)| *y).max().unwrap_or(seed.1);
        let touches_real_plateau = component.iter().any(|(x, y)| {
            [(0, -1), (1, 0), (0, 1), (-1, 0)].into_iter().any(|(dx, dy)| {
                level_at(partitions, x + dx, y + dy).is_some_and(|level| level >= 2)
            })
        });
        let broad = touches_real_plateau
            || (component.len() >= BROAD_LEVEL_ONE_MIN_CELLS
                && max_x - min_x + 1 >= BROAD_LEVEL_ONE_MIN_SPAN
                && max_y - min_y + 1 >= BROAD_LEVEL_ONE_MIN_SPAN);
        let target = if broad { 2 } else { 0 };
        for (gx, gy) in component {
            if let Some((index, x, y)) = location.get(&(gx, gy)).copied() {
                partitions[index].1.set_structural_level(x, y, Some(target));
                if broad {
                    report.promoted_level_one_cells += 1;
                } else {
                    report.collapsed_level_one_cells += 1;
                }
            }
        }
    }

    // Apply the certified authored ramp last. The six path cells preserve the
    // exact two-level span they were generated for: 2->1->0 on an outer cliff
    // or 4->3->2 on a nested highland tier. Odd levels remain connector-local.
    for (gx, gy, orientation, upper_level, lower_level) in accepted_ramps {
        let Some(ramp_levels) = directional_ramp_corridor_levels(upper_level, lower_level) else {
            continue;
        };
        for ((dx, dy), level) in ramp_offsets(orientation).iter().zip(ramp_levels) {
            if let Some((index, x, y)) = location.get(&(gx + dx, gy + dy)).copied() {
                partitions[index].1.set_structural_level(x, y, Some(level));
                report.certified_ramp_cells += 1;
            }
        }
        report.certified_ramps += 1;
    }

    report
}

pub fn normalize_surface_map_structural_elevation_v1(
    map: &mut TavernMap,
    chunk: ChunkCoord,
) -> StructuralElevationNormalizationReportV1 {
    let mut partitions = vec![(chunk, map.clone())];
    let report = normalize_partitioned_structural_elevation_v1(&mut partitions);
    if let Some((_, normalized)) = partitions.pop() {
        map.structural_levels = normalized.structural_levels;
    }
    report
}


/// Constructed ladders are reserved for genuine true-cliff access. A one-level
/// difference is low-relief/ramp-transition territory, and a water receiver is
/// owned by the natural vine/climb lane instead of a freestanding ladder.
/// Ordinary editor/worldgen structural authoring uses 0,2,3,4. Level 1 is
/// reserved for the certified ramp planner and is never a generic paint value.
pub const fn normalize_structural_authoring_level_v1(level: u8) -> u8 {
    let level = if level > haven_core::MAX_STRUCTURAL_LEVEL {
        haven_core::MAX_STRUCTURAL_LEVEL
    } else {
        level
    };
    if level == 1 { 2 } else { level }
}

pub const fn step_structural_authoring_level_v1(current: u8, delta: i8) -> u8 {
    let current = normalize_structural_authoring_level_v1(current);
    if delta > 0 {
        match current {
            0 => 2,
            2 => 3,
            3 => 4,
            _ => haven_core::MAX_STRUCTURAL_LEVEL,
        }
    } else if delta < 0 {
        match current {
            4 => 3,
            3 => 2,
            2 => 0,
            _ => 0,
        }
    } else {
        current
    }
}

pub const fn constructed_ladder_allowed_v1(level_drop: u8, receiver_swimmable: bool) -> bool {
    level_drop >= 2 && !receiver_swimmable
}

pub const fn natural_vine_preferred_v1(level_drop: u8, receiver_swimmable: bool) -> bool {
    level_drop >= 2 && receiver_swimmable
}

const RISE_RIGHT_OFFSETS: [(i32, i32); 6] =
    [(1, -1), (1, 0), (0, 0), (0, 1), (-1, 1), (-1, 2)];
const RISE_LEFT_OFFSETS: [(i32, i32); 6] =
    [(-1, -1), (-1, 0), (0, 0), (0, 1), (1, 1), (1, 2)];
const CERTIFIED_RAMP_LEVELS_V1: [u8; 6] = [2, 2, 2, 1, 1, 0];

/// Stable authoring/editor footprint contract for the certified six-cell LPC
/// directional ramp. This API predates AC1 and remains public so editor tools
/// and runtime normalization share one footprint authority.
pub const fn certified_ramp_offsets_v1(
    orientation: CertifiedRampOrientationV1,
) -> &'static [(i32, i32); 6] {
    match orientation {
        CertifiedRampOrientationV1::RiseRight => &RISE_RIGHT_OFFSETS,
        CertifiedRampOrientationV1::RiseLeft => &RISE_LEFT_OFFSETS,
    }
}

/// Stable outer-ramp structural level pattern used by editor authoring. Nested
/// AC1 ramps derive their shifted 4->3->2 pattern from the same relative shape.
pub const fn certified_ramp_levels_v1() -> &'static [u8; 6] {
    &CERTIFIED_RAMP_LEVELS_V1
}

const fn ramp_offsets(orientation: RampOrientation) -> &'static [(i32, i32); 6] {
    certified_ramp_offsets_v1(orientation)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn thin_one_high_shelf_collapses_to_relief() {
        let mut map = TavernMap::empty_with(TileKind::Grass);
        for x in 10..18 {
            map.set_structural_level(x, 12, Some(1));
        }
        let report = normalize_surface_map_structural_elevation_v1(&mut map, ChunkCoord::new(0, 0));
        assert_eq!(report.collapsed_level_one_cells, 8);
        assert!((10..18).all(|x| map.get_structural_level(x, 12) == Some(0)));
    }

    #[test]
    fn broad_legacy_one_high_region_promotes_to_true_plateau() {
        let mut map = TavernMap::empty_with(TileKind::Grass);
        for y in 10..14 {
            for x in 10..14 {
                map.set_structural_level(x, y, Some(1));
            }
        }
        let report = normalize_surface_map_structural_elevation_v1(&mut map, ChunkCoord::new(0, 0));
        assert_eq!(report.promoted_level_one_cells, 16);
        assert_eq!(map.get_structural_level(11, 11), Some(2));
    }

    #[test]
    fn auto_mountainrock_becomes_level_two() {
        let mut map = TavernMap::empty_with(TileKind::Grass);
        map.set(8, 8, TileKind::MountainRock);
        assert_eq!(map.get_structural_level(8, 8), None);
        let report = normalize_surface_map_structural_elevation_v1(&mut map, ChunkCoord::new(0, 0));
        assert_eq!(report.promoted_legacy_mountainrock, 1);
        assert_eq!(map.get_structural_level(8, 8), Some(2));
    }

    #[test]
    fn complete_ramp_is_exact_two_one_zero_transition() {
        let mut map = TavernMap::empty_with(TileKind::Grass);
        let host = (20, 20);
        for (dx, dy) in RISE_RIGHT_OFFSETS {
            map.set(host.0 + dx, host.1 + dy, TileKind::MountainPath);
        }
        let report = normalize_surface_map_structural_elevation_v1(&mut map, ChunkCoord::new(0, 0));
        assert_eq!(report.certified_ramps, 1);
        assert_eq!(report.certified_ramp_cells, 6);
        let levels = RISE_RIGHT_OFFSETS
            .into_iter()
            .map(|(dx, dy)| map.get_structural_level(host.0 + dx, host.1 + dy).unwrap())
            .collect::<Vec<_>>();
        assert_eq!(levels, vec![2, 2, 2, 1, 1, 0]);
    }

    #[test]
    fn nested_level_four_ramp_preserves_four_three_two_transition() {
        let mut map = TavernMap::empty_with(TileKind::Grass);
        let host = (20, 20);
        for (step, (dx, dy)) in RISE_RIGHT_OFFSETS.into_iter().enumerate() {
            map.set(host.0 + dx, host.1 + dy, TileKind::MountainPath);
            let level = if step <= 2 { 4 } else { 2 };
            map.set_structural_level(host.0 + dx, host.1 + dy, Some(level));
        }
        normalize_surface_map_structural_elevation_v1(&mut map, ChunkCoord::new(0, 0));
        let levels = RISE_RIGHT_OFFSETS
            .into_iter()
            .map(|(dx, dy)| map.get_structural_level(host.0 + dx, host.1 + dy).unwrap())
            .collect::<Vec<_>>();
        assert_eq!(levels, vec![4, 4, 4, 3, 3, 2]);
    }

    #[test]
    fn ordinary_authoring_skips_reserved_level_one() {
        assert_eq!(normalize_structural_authoring_level_v1(1), 2);
        assert_eq!(step_structural_authoring_level_v1(0, 1), 2);
        assert_eq!(step_structural_authoring_level_v1(2, -1), 0);
        assert_eq!(step_structural_authoring_level_v1(2, 1), 3);
    }

    #[test]
    fn ladder_and_vine_policy_follow_true_cliff_receiver_rules() {
        assert!(!constructed_ladder_allowed_v1(1, false));
        assert!(constructed_ladder_allowed_v1(2, false));
        assert!(!constructed_ladder_allowed_v1(2, true));
        assert!(natural_vine_preferred_v1(2, true));
        assert!(!natural_vine_preferred_v1(1, true));
    }

    #[test]
    fn certified_editor_ramp_api_matches_outer_runtime_corridor() {
        assert_eq!(
            certified_ramp_offsets_v1(CertifiedRampOrientationV1::RiseRight),
            &RISE_RIGHT_OFFSETS,
        );
        assert_eq!(
            certified_ramp_offsets_v1(CertifiedRampOrientationV1::RiseLeft),
            &RISE_LEFT_OFFSETS,
        );
        assert_eq!(
            certified_ramp_levels_v1(),
            &directional_ramp_corridor_levels(2, 0)
                .expect("outer ramp corridor must remain certified"),
        );
    }

    #[test]
    fn ramp_can_cross_partition_boundary() {
        let mut left = TavernMap::empty_with(TileKind::Grass);
        let mut right = TavernMap::empty_with(TileKind::Grass);
        let host_global = (MAP_W as i32 - 1, 20);
        let expected_levels = directional_ramp_corridor_levels(2, 0)
            .expect("a production outer ramp must encode a certified 2->1->0 corridor");
        for ((dx, dy), level) in RISE_LEFT_OFFSETS.iter().zip(expected_levels) {
            let gx = host_global.0 + dx;
            let gy = host_global.1 + dy;
            if gx < MAP_W as i32 {
                left.set(gx, gy, TileKind::MountainPath);
                left.set_structural_level(gx, gy, Some(level));
            } else {
                let lx = gx - MAP_W as i32;
                right.set(lx, gy, TileKind::MountainPath);
                right.set_structural_level(lx, gy, Some(level));
            }
        }
        let mut partitions = vec![(ChunkCoord::new(0, 0), left), (ChunkCoord::new(1, 0), right)];
        let report = normalize_partitioned_structural_elevation_v1(&mut partitions);
        assert_eq!(report.certified_ramps, 1);
        for ((dx, dy), expected) in RISE_LEFT_OFFSETS.iter().zip(expected_levels) {
            let gx = host_global.0 + dx;
            let gy = host_global.1 + dy;
            let map = if gx < MAP_W as i32 { &partitions[0].1 } else { &partitions[1].1 };
            let lx = gx.rem_euclid(MAP_W as i32);
            assert_eq!(map.get_structural_level(lx, gy), Some(expected));
        }
    }
}
