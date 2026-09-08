use std::collections::{BTreeMap, BTreeSet, VecDeque};

// H21A14AC1: traversal access scales with cliff perimeter instead of being a
// rare global decoration. The caps remain deliberately bounded so a malformed
// candidate field cannot flood a world with connectors.
const MAX_GENERATED_RAMPS: usize = 32;
const MAX_GENERATED_LADDERS: usize = 128;
const RAMP_CLUSTER_SPACING: i32 = 16;
const LADDER_CLUSTER_SPACING: i32 = 12;
const LADDER_RAMP_CLEARANCE: i32 = 6;
const RAMP_PATH_PROXIMITY_RADIUS: i32 = 14;

pub(crate) fn directional_ramp_corridor_indices(
    upper: usize,
    lower: usize,
    width: usize,
    height: usize,
    rises_right: bool,
) -> Vec<usize> {
    debug_assert_eq!(upper.checked_add(width), Some(lower));
    let upper_x = (upper % width) as i32;
    let upper_y = (upper / width) as i32;
    let side = if rises_right { 1 } else { -1 };
    let offsets = [
        (side, -1),
        (side, 0),
        (0, 0),
        (0, 1),
        (-side, 1),
        (-side, 2),
    ];
    offsets
        .into_iter()
        .filter_map(|(dx, dy)| {
            let x = upper_x + dx;
            let y = upper_y + dy;
            ((0..width as i32).contains(&x) && (0..height as i32).contains(&y))
                .then(|| y as usize * width + x as usize)
        })
        .collect()
}

/// The authored 3x4 ramp spans an exact two-level structural descent while
/// reserving the intermediate level only inside the six-cell MountainPath
/// corridor. This works for both an outer 2->0 cliff and an inner 4->2 tier.
pub(crate) fn directional_ramp_corridor_levels(upper_level: u8, lower_level: u8) -> Option<[u8; 6]> {
    if upper_level.checked_sub(lower_level) != Some(2) {
        return None;
    }
    let middle = upper_level.checked_sub(1)?;
    Some([
        upper_level,
        upper_level,
        upper_level,
        middle,
        middle,
        lower_level,
    ])
}

pub(crate) fn directional_ramp_orientation_for_candidate(
    upper: usize,
    lower: usize,
    levels: &[u8],
    land: &[bool],
    protected: &[bool],
    width: usize,
    height: usize,
    seed: u64,
) -> Option<bool> {
    let upper_level = levels[upper];
    let lower_level = levels[lower];
    // H21A14AC1: a complete authored ramp owns an exact two-level descent. The
    // middle level is carved only after a gateway is selected. This permits the
    // same certified ramp geometry on 2->0 and 4->2 faces without introducing
    // generic one-high cliff shoulders.
    directional_ramp_corridor_levels(upper_level, lower_level)?;
    let viable = |rises_right: bool| {
        let corridor = directional_ramp_corridor_indices(upper, lower, width, height, rises_right);
        if corridor.len() != 6 {
            return false;
        }
        corridor.iter().enumerate().all(|(step, index)| {
            let expected_before_carve = if step <= 2 { upper_level } else { lower_level };
            land[*index]
                && !protected[*index]
                && levels[*index] == expected_before_carve
        })
    };
    match (viable(true), viable(false)) {
        (false, false) => None,
        (true, false) => Some(true),
        (false, true) => Some(false),
        (true, true) => {
            let x = (upper % width) as i32;
            let y = (upper / width) as i32;
            Some(seeded_edge_score(seed ^ 0x57_37, x, y) & 1 == 0)
        }
    }
}

#[derive(Clone, Copy, Debug)]
struct RampCandidate {
    component: usize,
    path_distance: i32,
    seeded: u64,
    upper: usize,
    lower: usize,
    rises_right: bool,
}

pub(crate) fn choose_south_ramp_edges(
    levels: &[u8],
    land: &[bool],
    protected: &[bool],
    width: usize,
    height: usize,
    seed: u64,
) -> Vec<(usize, usize, bool)> {
    if height < 2 || width == 0 {
        return Vec::new();
    }

    // Accessibility is component-based. Each exact raised tier receives a
    // gateway when a complete authored south-facing corridor exists, while
    // larger perimeters receive several spatially separated gateways.
    let components = exact_level_component_labels(levels, land, protected, width, height);
    let mut candidates = Vec::new();
    for y in 0..height - 1 {
        for x in 0..width {
            let Some(upper) = y.checked_mul(width).and_then(|row| row.checked_add(x)) else {
                continue;
            };
            let Some(lower) = upper.checked_add(width) else {
                continue;
            };
            if !land[upper]
                || !land[lower]
                || protected[upper]
                || protected[lower]
                || directional_ramp_corridor_levels(levels[upper], levels[lower]).is_none()
            {
                continue;
            }
            let component = components[upper];
            if component == usize::MAX {
                continue;
            }
            let Some(rises_right) = directional_ramp_orientation_for_candidate(
                upper, lower, levels, land, protected, width, height, seed,
            ) else {
                continue;
            };
            let path_distance = nearest_true_distance(
                protected,
                width,
                height,
                x as i32,
                y as i32,
                RAMP_PATH_PROXIMITY_RADIUS,
            );
            let seeded = seeded_edge_score(seed, x as i32, y as i32);
            candidates.push(RampCandidate {
                component,
                path_distance,
                seeded,
                upper,
                lower,
                rises_right,
            });
        }
    }
    if candidates.is_empty() {
        return Vec::new();
    }

    candidates.sort_by_key(|entry| (entry.component, entry.path_distance, entry.seeded));

    let mut candidate_counts = BTreeMap::<usize, usize>::new();
    for candidate in &candidates {
        *candidate_counts.entry(candidate.component).or_default() += 1;
    }
    // A long usable south perimeter should not still receive only one ramp.
    // Candidate count is a stable proxy for usable perimeter length.
    let targets = candidate_counts
        .into_iter()
        .map(|(component, count)| {
            let target = (1 + count / 48).clamp(1, 2);
            (component, target)
        })
        .collect::<BTreeMap<_, _>>();

    let mut selected = Vec::<(usize, usize, bool)>::new();
    let mut selected_counts = BTreeMap::<usize, usize>::new();
    let mut claimed_corridor_cells = BTreeSet::<usize>::new();

    // First pass guarantees one gateway per component where a certified,
    // non-overlapping corridor is actually possible. Nested 4->2 and outer
    // 2->0 routes can therefore coexist without carving through one another.
    for candidate in &candidates {
        if selected.len() >= MAX_GENERATED_RAMPS {
            break;
        }
        if *selected_counts.get(&candidate.component).unwrap_or(&0) != 0 {
            continue;
        }
        let corridor = ramp_candidate_corridor(*candidate, width, height);
        if corridor.len() != 6
            || corridor
                .iter()
                .any(|index| claimed_corridor_cells.contains(index))
        {
            continue;
        }
        claimed_corridor_cells.extend(corridor);
        selected.push((candidate.upper, candidate.lower, candidate.rises_right));
        *selected_counts.entry(candidate.component).or_default() += 1;
    }

    // Additional passes fill each component's size-scaled target while keeping
    // gateways far enough apart to read as intentional routes rather than a
    // picket fence of ramps.
    let mut extras = candidates.clone();
    extras.sort_by_key(|entry| (entry.path_distance, entry.seeded));
    for candidate in extras {
        if selected.len() >= MAX_GENERATED_RAMPS {
            break;
        }
        let target = *targets.get(&candidate.component).unwrap_or(&1);
        let current = *selected_counts.get(&candidate.component).unwrap_or(&0);
        if current >= target {
            continue;
        }
        if selected.iter().any(|(existing, _, _)| {
            grid_manhattan_distance(*existing, candidate.upper, width) < RAMP_CLUSTER_SPACING
        }) {
            continue;
        }
        let corridor = ramp_candidate_corridor(candidate, width, height);
        if corridor.len() != 6
            || corridor
                .iter()
                .any(|index| claimed_corridor_cells.contains(index))
        {
            continue;
        }
        claimed_corridor_cells.extend(corridor);
        selected.push((candidate.upper, candidate.lower, candidate.rises_right));
        *selected_counts.entry(candidate.component).or_default() += 1;
    }

    selected
}

/// AC2 accessibility solver. Natural ramp footprints are preferred, but a
/// generated raised component is not allowed to remain inaccessible merely
/// because its contour failed to accidentally contain the exact six-cell LPC
/// corridor. When coverage is short, a small unprotected south-boundary bay is
/// reshaped into the certified 2->1->0 or 4->3->2 profile.
/// Compatibility wording: Level-2 -> 1 -> 0 corridor.
pub(crate) fn choose_or_carve_south_ramp_edges(
    levels: &mut [u8],
    land: &[bool],
    protected: &[bool],
    width: usize,
    height: usize,
    seed: u64,
) -> Vec<(usize, usize, bool)> {
    if width == 0 || height < 2 || levels.len() != width.saturating_mul(height) {
        return Vec::new();
    }

    let component_labels = exact_level_component_labels(levels, land, protected, width, height);
    let mut selected = choose_south_ramp_edges(levels, land, protected, width, height, seed);
    let mut claimed = BTreeSet::<usize>::new();
    let mut selected_counts = BTreeMap::<usize, usize>::new();
    for (upper, lower, rises_right) in &selected {
        let component = component_labels[*upper];
        if component != usize::MAX {
            *selected_counts.entry(component).or_default() += 1;
        }

        // AC2R2: choose_or_carve owns the complete returned corridor contract.
        // Natural candidates selected by choose_south_ramp_edges previously
        // remained at [upper, upper, upper, lower, lower, lower] until the
        // caller's later materialization pass. That made this helper return
        // ramps that were not yet traversable and broke direct accessibility
        // certification. Carve natural selections here exactly like repaired
        // bays; the downstream materializer remains safely idempotent.
        let corridor = directional_ramp_corridor_indices(
            *upper, *lower, width, height, *rises_right,
        );
        if let Some(expected) = directional_ramp_corridor_levels(levels[*upper], levels[*lower]) {
            for (step, index) in corridor.iter().copied().enumerate() {
                levels[index] = expected[step];
            }
        }
        claimed.extend(corridor);
    }

    let mut component_sizes = BTreeMap::<usize, usize>::new();
    let mut component_levels = BTreeMap::<usize, u8>::new();
    for (index, component) in component_labels.iter().copied().enumerate() {
        if component == usize::MAX || levels[index] < 2 {
            continue;
        }
        *component_sizes.entry(component).or_default() += 1;
        component_levels.entry(component).or_insert(levels[index]);
    }

    let mut targets = component_sizes
        .into_iter()
        .map(|(component, cells)| (component, (1 + cells / 900).clamp(1, 2)))
        .collect::<Vec<_>>();
    targets.sort_unstable();

    for (component, target) in targets {
        if selected.len() >= MAX_GENERATED_RAMPS {
            break;
        }
        let upper_level = *component_levels.get(&component).unwrap_or(&0);
        let Some(lower_level) = upper_level.checked_sub(2) else { continue; };
        while *selected_counts.get(&component).unwrap_or(&0) < target
            && selected.len() < MAX_GENERATED_RAMPS
        {
            let mut candidates = Vec::<(i32, usize, u64, usize, usize, bool, Vec<usize>)>::new();
            for y in 1..height.saturating_sub(2) {
                for x in 1..width.saturating_sub(1) {
                    let upper = y * width + x;
                    if component_labels[upper] != component || levels[upper] != upper_level {
                        continue;
                    }
                    let lower = upper + width;
                    if !land[lower] || protected[lower] || levels[lower] != lower_level {
                        continue;
                    }
                    for rises_right in [true, false] {
                        let corridor = directional_ramp_corridor_indices(
                            upper, lower, width, height, rises_right,
                        );
                        if corridor.len() != 6
                            || corridor.iter().any(|index| {
                                !land[*index] || protected[*index] || claimed.contains(index)
                            })
                        {
                            continue;
                        }
                        let Some(expected) = directional_ramp_corridor_levels(upper_level, lower_level)
                        else { continue; };
                        // Carving may only reshape this exact generated tier pair.
                        // It never cuts roads/civic cells, water, another tier or
                        // an authored connector.
                        if corridor.iter().any(|index| {
                            let value = levels[*index];
                            value != upper_level && value != lower_level && value != expected[3]
                        }) {
                            continue;
                        }
                        let edits = corridor.iter().enumerate()
                            .filter(|(step, index)| levels[**index] != expected[*step])
                            .count() as i32;
                        let path_distance = nearest_true_distance(
                            protected, width, height, x as i32, y as i32, RAMP_PATH_PROXIMITY_RADIUS,
                        );
                        candidates.push((
                            edits,
                            usize::MAX - path_distance.max(0) as usize,
                            seeded_edge_score(seed ^ 0xAC2A_0001, x as i32, y as i32),
                            upper,
                            lower,
                            rises_right,
                            corridor,
                        ));
                    }
                }
            }
            if candidates.is_empty() {
                break;
            }
            candidates.sort_by_key(|candidate| (candidate.0, candidate.1, candidate.2));
            let Some((_, _, _, upper, lower, rises_right, corridor)) = candidates
                .into_iter()
                .find(|candidate| {
                    selected.iter().all(|(existing, _, _)| {
                        grid_manhattan_distance(*existing, candidate.3, width) >= RAMP_CLUSTER_SPACING
                    })
                })
            else {
                break;
            };
            let Some(expected) = directional_ramp_corridor_levels(upper_level, lower_level)
            else { break; };
            for (step, index) in corridor.iter().copied().enumerate() {
                levels[index] = expected[step];
                claimed.insert(index);
            }
            selected.push((upper, lower, rises_right));
            *selected_counts.entry(component).or_default() += 1;
        }
    }

    selected
}

fn ramp_candidate_corridor(candidate: RampCandidate, width: usize, height: usize) -> Vec<usize> {
    directional_ramp_corridor_indices(
        candidate.upper,
        candidate.lower,
        width,
        height,
        candidate.rises_right,
    )
}

/// Select dry inland ladders as secondary access routes on genuine straight
/// south cliff faces. Water-facing cliffs remain reserved for vines/natural
/// climbs, and ramp footprints are kept clear so connector art never overlaps.
pub(crate) fn choose_inland_ladder_hosts(
    levels: &[u8],
    dry_land: &[bool],
    protected: &[bool],
    ramp_claimed: &[bool],
    width: usize,
    height: usize,
    seed: u64,
) -> Vec<usize> {
    if height < 2 || width == 0 || levels.len() != width.saturating_mul(height) {
        return Vec::new();
    }

    let components = exact_level_component_labels(levels, dry_land, protected, width, height);
    let mut candidates = Vec::<(usize, i32, u64, usize)>::new();
    for y in 0..height - 1 {
        for x in 0..width {
            let upper = y * width + x;
            let lower = upper + width;
            if !dry_land[upper]
                || !dry_land[lower]
                || protected[upper]
                || protected[lower]
                || ramp_claimed.get(upper).copied().unwrap_or(false)
                || ramp_claimed.get(lower).copied().unwrap_or(false)
            {
                continue;
            }
            let host_level = levels[upper];
            let receiver_level = levels[lower];
            if host_level < 2 || host_level.saturating_sub(receiver_level) < 2 {
                continue;
            }
            if !straight_south_face(levels, width, height, x, y, host_level) {
                continue;
            }
            let ramp_distance = nearest_true_distance(
                ramp_claimed,
                width,
                height,
                x as i32,
                y as i32,
                LADDER_RAMP_CLEARANCE,
            );
            if ramp_distance < LADDER_RAMP_CLEARANCE {
                continue;
            }
            let component = components[upper];
            if component == usize::MAX {
                continue;
            }
            candidates.push((
                component,
                -ramp_distance,
                seeded_edge_score(seed ^ 0x4c41_4444_4552, x as i32, y as i32),
                upper,
            ));
        }
    }
    if candidates.is_empty() {
        return Vec::new();
    }
    candidates.sort_unstable();

    let mut counts = BTreeMap::<usize, usize>::new();
    for (component, _, _, _) in &candidates {
        *counts.entry(*component).or_default() += 1;
    }
    let targets = counts
        .into_iter()
        .map(|(component, count)| (component, (1 + count / 24).clamp(1, 3)))
        .collect::<BTreeMap<_, _>>();

    let mut selected = Vec::new();
    let mut selected_counts = BTreeMap::<usize, usize>::new();
    let mut selected_set = BTreeSet::new();
    for (component, _, _, host) in candidates {
        if selected.len() >= MAX_GENERATED_LADDERS {
            break;
        }
        let target = *targets.get(&component).unwrap_or(&1);
        if *selected_counts.get(&component).unwrap_or(&0) >= target {
            continue;
        }
        if selected.iter().any(|existing| {
            grid_manhattan_distance(*existing, host, width) < LADDER_CLUSTER_SPACING
        }) {
            continue;
        }
        if selected_set.insert(host) {
            selected.push(host);
            *selected_counts.entry(component).or_default() += 1;
        }
    }
    selected
}

fn straight_south_face(
    levels: &[u8],
    width: usize,
    height: usize,
    x: usize,
    y: usize,
    host_level: u8,
) -> bool {
    if y + 1 >= height || levels[(y + 1) * width + x] >= host_level {
        return false;
    }
    // Runtime ladder art is certified only for an exact straight south face.
    // Reject cells that would also expose a lower neighbor on N/E/W.
    if y > 0 && levels[(y - 1) * width + x] < host_level {
        return false;
    }
    if x > 0 && levels[y * width + (x - 1)] < host_level {
        return false;
    }
    if x + 1 < width && levels[y * width + (x + 1)] < host_level {
        return false;
    }
    true
}

fn exact_level_component_labels(
    levels: &[u8],
    land: &[bool],
    protected: &[bool],
    width: usize,
    height: usize,
) -> Vec<usize> {
    let mut labels = vec![usize::MAX; levels.len()];
    let mut next_label = 0usize;
    for index in 0..levels.len() {
        if labels[index] != usize::MAX || levels[index] == 0 || !land[index] || protected[index] {
            continue;
        }
        let level = levels[index];
        let mut queue = VecDeque::from([index]);
        labels[index] = next_label;
        while let Some(current) = queue.pop_front() {
            let x = current % width;
            let y = current / width;
            for neighbor in cardinal_indices(x, y, width, height) {
                if labels[neighbor] != usize::MAX
                    || levels[neighbor] != level
                    || !land[neighbor]
                    || protected[neighbor]
                {
                    continue;
                }
                labels[neighbor] = next_label;
                queue.push_back(neighbor);
            }
        }
        next_label += 1;
    }
    labels
}

fn cardinal_indices(x: usize, y: usize, width: usize, height: usize) -> Vec<usize> {
    let mut result = Vec::with_capacity(4);
    if y > 0 {
        result.push((y - 1) * width + x);
    }
    if x + 1 < width {
        result.push(y * width + x + 1);
    }
    if y + 1 < height {
        result.push((y + 1) * width + x);
    }
    if x > 0 {
        result.push(y * width + x - 1);
    }
    result
}

fn nearest_true_distance(
    values: &[bool],
    width: usize,
    height: usize,
    x: i32,
    y: i32,
    radius: i32,
) -> i32 {
    let mut best = radius + 1;
    for offset_y in -radius..=radius {
        for offset_x in -radius..=radius {
            let distance = offset_x.abs() + offset_y.abs();
            if distance >= best || distance > radius {
                continue;
            }
            let nx = x + offset_x;
            let ny = y + offset_y;
            if nx < 0 || ny < 0 || nx >= width as i32 || ny >= height as i32 {
                continue;
            }
            if values.get(ny as usize * width + nx as usize).copied().unwrap_or(false) {
                best = distance;
            }
        }
    }
    best
}

fn grid_manhattan_distance(left: usize, right: usize, width: usize) -> i32 {
    let left_x = (left % width) as i32;
    let left_y = (left / width) as i32;
    let right_x = (right % width) as i32;
    let right_y = (right / width) as i32;
    (left_x - right_x).abs() + (left_y - right_y).abs()
}

fn seeded_edge_score(seed: u64, x: i32, y: i32) -> u64 {
    let mut value = seed ^ (x as i64 as u64).wrapping_mul(0x9e37_79b9_7f4a_7c15);
    value ^= (y as i64 as u64).wrapping_mul(0xc2b2_ae3d_27d4_eb4f);
    value ^= value >> 30;
    value = value.wrapping_mul(0xbf58_476d_1ce4_e5b9);
    value ^= value >> 27;
    value.wrapping_mul(0x94d0_49bb_1331_11eb) ^ (value >> 31)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ramp_levels_support_outer_and_inner_two_level_drops() {
        assert_eq!(
            directional_ramp_corridor_levels(2, 0),
            Some([2, 2, 2, 1, 1, 0])
        );
        assert_eq!(
            directional_ramp_corridor_levels(4, 2),
            Some([4, 4, 4, 3, 3, 2])
        );
        assert_eq!(directional_ramp_corridor_levels(4, 3), None);
    }

    #[test]
    fn large_south_perimeter_receives_multiple_ramps() {
        let width = 64;
        let height = 8;
        let mut levels = vec![0u8; width * height];
        for y in 1..=3 {
            for x in 4..60 {
                levels[y * width + x] = 2;
            }
        }
        let land = vec![true; levels.len()];
        let protected = vec![false; levels.len()];
        let ramps = choose_south_ramp_edges(&levels, &land, &protected, width, height, 0xAC1);
        assert!(
            ramps.len() >= 2,
            "large usable cliff perimeter should receive multiple ramps: {ramps:?}"
        );
    }

    #[test]
    fn dry_straight_true_cliff_can_receive_ladder() {
        let width = 12;
        let height = 7;
        let mut levels = vec![0u8; width * height];
        for y in 1..=2 {
            for x in 2..=9 {
                levels[y * width + x] = 2;
            }
        }
        let dry = vec![true; levels.len()];
        let protected = vec![false; levels.len()];
        let ramp_claimed = vec![false; levels.len()];
        let ladders = choose_inland_ladder_hosts(
            &levels,
            &dry,
            &protected,
            &ramp_claimed,
            width,
            height,
            0x1ADD3,
        );
        assert!(!ladders.is_empty(), "expected at least one inland ladder");
        for host in ladders {
            assert_eq!(levels[host], 2);
            assert_eq!(levels[host + width], 0);
        }
    }
    #[test]
    fn nested_highland_receives_outer_and_inner_access_corridors() {
        let width = 30;
        let height = 18;
        let mut levels = vec![0u8; width * height];

        // Broad level-2 shelf with a nested level-4 plateau. Both tier
        // boundaries are long enough to provide independent south access.
        for y in 2..=12 {
            for x in 3..=26 {
                levels[y * width + x] = 2;
            }
        }
        for y in 4..=8 {
            for x in 9..=20 {
                levels[y * width + x] = 4;
            }
        }

        let land = vec![true; levels.len()];
        let protected = vec![false; levels.len()];
        let ramps = choose_or_carve_south_ramp_edges(
            &mut levels, &land, &protected, width, height, 0xAC20_0242,
        );

        let corridors = ramps
            .iter()
            .map(|(upper, lower, rises_right)| {
                directional_ramp_corridor_indices(
                    *upper, *lower, width, height, *rises_right,
                )
                .into_iter()
                .map(|index| levels[index])
                .collect::<Vec<_>>()
            })
            .collect::<Vec<_>>();

        assert!(
            corridors.iter().any(|levels| levels == &[2, 2, 2, 1, 1, 0]),
            "outer level-2 shelf must have a certified route to level 0: {corridors:?}"
        );
        assert!(
            corridors.iter().any(|levels| levels == &[4, 4, 4, 3, 3, 2]),
            "nested level-4 plateau must have a certified route to level 2: {corridors:?}"
        );
    }

    #[test]
    fn accessibility_solver_carves_a_certified_bay_when_contour_is_jagged() {
        let width = 16;
        let height = 10;
        let mut levels = vec![0u8; width * height];
        // Deliberately jag the south edge so no exact six-cell corridor exists.
        for y in 2..=5 {
            for x in 3..=12 {
                levels[y * width + x] = 2;
            }
        }
        levels[5 * width + 6] = 0;
        levels[5 * width + 9] = 0;
        let land = vec![true; levels.len()];
        let protected = vec![false; levels.len()];
        let ramps = choose_or_carve_south_ramp_edges(
            &mut levels, &land, &protected, width, height, 0xAC2,
        );
        assert!(!ramps.is_empty(), "raised generated component must receive access");
        let (upper, lower, rises_right) = ramps[0];
        let corridor = directional_ramp_corridor_indices(upper, lower, width, height, rises_right);
        let expected = directional_ramp_corridor_levels(2, 0).unwrap();
        assert_eq!(
            corridor.iter().map(|index| levels[*index]).collect::<Vec<_>>(),
            expected.to_vec()
        );
    }


}
