//! Alderreach capital and harbor layout helpers for the mainland surface pass.

use haven_core::{ObjectKind, TileKind, ZoneKind, MAP_H, MAP_W};

use super::{SurfaceAssembly, SurfaceCell, CITY_HARBOR_MAX_LINK_DISTANCE_TILES};

fn willowmere_feature_hash(seed: u64, salt: u64, value: i32) -> u64 {
    let mut hash = seed ^ salt ^ (value as i64 as u64).wrapping_mul(0x9e37_79b9_7f4a_7c15);
    hash ^= hash >> 30;
    hash = hash.wrapping_mul(0xbf58_476d_1ce4_e5b9);
    hash ^= hash >> 27;
    hash = hash.wrapping_mul(0x94d0_49bb_1331_11eb);
    hash ^ (hash >> 31)
}

fn willowmere_lane_offset(seed: u64, salt: u64, position: i32, segment: i32, amplitude: i32) -> i32 {
    if amplitude <= 0 || segment <= 0 {
        return 0;
    }
    let section = position.div_euclid(segment);
    let local = position.rem_euclid(segment);
    let sample = |index: i32| -> i32 {
        let span = amplitude * 2 + 1;
        (willowmere_feature_hash(seed, salt, index) % span as u64) as i32 - amplitude
    };
    let a = sample(section);
    let b = sample(section + 1);
    (a * (segment - local) + b * local) / segment
}

fn planning_zone_priority(zone: ZoneKind) -> Option<u8> {
    match zone {
        ZoneKind::None => Some(0),
        ZoneKind::AgriculturalLot => Some(1),
        ZoneKind::CivicLot
        | ZoneKind::MarketLot
        | ZoneKind::ResidentialLot
        | ZoneKind::ArtisanLot => Some(2),
        ZoneKind::HarborLot => Some(3),
        // Runtime/navigation zones are not mainland planning metadata and may
        // never be silently replaced by a later reservation pass.
        _ => None,
    }
}

fn can_reserve_planning_zone(existing: ZoneKind, requested: ZoneKind) -> bool {
    if existing == requested {
        return true;
    }
    match (planning_zone_priority(existing), planning_zone_priority(requested)) {
        (Some(existing_priority), Some(requested_priority)) => {
            requested_priority > existing_priority
        }
        _ => false,
    }
}

impl SurfaceAssembly<'_> {
    pub(super) fn paint_city_streets(&mut self, center: SurfaceCell, seed: u64) -> usize {
        let mut street_cells = Vec::new();
        let mut paint_lane_cell = |cell: SurfaceCell, radius: i32| {
            for oy in -radius..=radius {
                for ox in -radius..=radius {
                    if ox.abs() + oy.abs() <= radius + 1 {
                        street_cells.push(SurfaceCell::new(cell.x + ox, cell.y + oy));
                    }
                }
            }
        };

        // Main east/west and north/south roads gently meander instead of
        // producing a perfect grid. Integer interpolation keeps the lane smooth
        // and deterministic without introducing diagonal one-cell gaps.
        for dx in -40..=40 {
            let bend = willowmere_lane_offset(seed, 0x4557_4d41_494e, dx, 9, 4);
            paint_lane_cell(SurfaceCell::new(center.x + dx, center.y + bend), 1);
        }
        for dy in -32..=32 {
            let bend = willowmere_lane_offset(seed, 0x4e53_4d41_494e, dy, 8, 3);
            paint_lane_cell(SurfaceCell::new(center.x + bend, center.y + dy), 1);
        }

        // Two secondary residential/market lanes remain broadly east/west but
        // are not parallel ruler lines. Short spurs tie them back into the main
        // north/south route and leave irregular blocks for the staggered lots.
        for (base_y, salt) in [(-21, 0x4e4f_5254_4801_u64), (21, 0x534f_5554_4802_u64)] {
            for dx in -34..=34 {
                let bend = willowmere_lane_offset(seed, salt, dx, 11, 3);
                paint_lane_cell(SurfaceCell::new(center.x + dx, center.y + base_y + bend), 0);
            }
        }
        for (base_x, salt) in [(-28, 0x5745_5354_0003_u64), (29, 0x4541_5354_0004_u64)] {
            for dy in -18..=18 {
                let bend = willowmere_lane_offset(seed, salt, dy, 10, 2);
                paint_lane_cell(SurfaceCell::new(center.x + base_x + bend, center.y + dy), 0);
            }
        }

        street_cells.sort_unstable();
        street_cells.dedup();
        let mut changed = 0;
        for cell in street_cells {
            if self.is_road_land(cell) && self.set_tile(cell, TileKind::Road) {
                changed += 1;
            }
        }
        changed
    }

    pub(super) fn naturalize_road_path(
        &self,
        path: &[SurfaceCell],
        seed: u64,
        salt: u64,
    ) -> Vec<SurfaceCell> {
        if path.len() < 5 {
            return path.to_vec();
        }
        let mut result = Vec::with_capacity(path.len());
        for (index, cell) in path.iter().copied().enumerate() {
            if index == 0 || index + 1 == path.len() {
                result.push(cell);
                continue;
            }
            let previous = path[index - 1];
            let next = path[index + 1];
            let offset = willowmere_lane_offset(seed, salt, index as i32, 13, 2);
            let candidate = if previous.y == next.y {
                SurfaceCell::new(cell.x, cell.y + offset)
            } else if previous.x == next.x {
                SurfaceCell::new(cell.x + offset, cell.y)
            } else {
                cell
            };
            result.push(if self.is_road_land(candidate) { candidate } else { cell });
        }
        result
    }

    pub(super) fn neighboring_water_count(&self, cell: SurfaceCell) -> usize {
        let mut count = 0;
        for oy in -1..=1 {
            for ox in -1..=1 {
                if ox == 0 && oy == 0 {
                    continue;
                }
                count += usize::from(
                    self.tile(SurfaceCell::new(cell.x + ox, cell.y + oy))
                        .is_some_and(TileKind::is_water),
                );
            }
        }
        count
    }

    pub(super) fn is_coastal_land(&self, cell: SurfaceCell) -> bool {
        self.is_road_land(cell) && self.neighboring_water_count(cell) > 0
    }

    pub(super) fn find_harbor_landfall(&self, preferred: SurfaceCell) -> Option<SurfaceCell> {
        let surface_height = self.max_y - self.min_y + 1;
        let southern_band = self.min_y + surface_height * 3 / 5;
        let mut best: Option<(i32, SurfaceCell)> = None;
        for y in southern_band..=self.max_y {
            for x in self.min_x..=self.max_x {
                let cell = SurfaceCell::new(x, y);
                if !self.is_coastal_land(cell) {
                    continue;
                }
                let water_contacts = self.neighboring_water_count(cell) as i32;
                let distance = (x - preferred.x).abs() * 2 + (y - preferred.y).abs();
                let score = distance - water_contacts * 3;
                if best.is_none_or(|(best_score, _)| score < best_score) {
                    best = Some((score, cell));
                }
            }
        }
        best.map(|(_, cell)| cell)
    }

    pub(super) fn existing_willowmere_center(&self) -> Option<SurfaceCell> {
        for (chunk, index) in &self.scene_by_chunk {
            if let Some(object) = self.scenes[*index]
                .map
                .objects
                .iter()
                .find(|object| object.kind == ObjectKind::Well)
            {
                return Some(SurfaceCell::new(
                    chunk.x * MAP_W as i32 + object.x,
                    chunk.y * MAP_H as i32 + object.y,
                ));
            }
        }

        // Z84 removed the misclassified water-cooler well, so current saves
        // recover Willowmere from the symmetric civic/market/residential/
        // artisan lot metadata instead of depending on a decorative object.
        let mut sum_x = 0_i64;
        let mut sum_y = 0_i64;
        let mut count = 0_i64;
        for (chunk, index) in &self.scene_by_chunk {
            let scene = &self.scenes[*index];
            for y in 0..MAP_H as i32 {
                for x in 0..MAP_W as i32 {
                    if !matches!(
                        scene.zone_at(x, y),
                        ZoneKind::CivicLot
                            | ZoneKind::MarketLot
                            | ZoneKind::ResidentialLot
                            | ZoneKind::ArtisanLot
                    ) {
                        continue;
                    }
                    sum_x += i64::from(chunk.x * MAP_W as i32 + x);
                    sum_y += i64::from(chunk.y * MAP_H as i32 + y);
                    count += 1;
                }
            }
        }
        if count > 0 {
            return Some(SurfaceCell::new(
                (sum_x / count) as i32,
                (sum_y / count) as i32,
            ));
        }

        // Pre-zone saves may still contain the compact 11x11 StonePath plaza.
        // Its centroid is a stronger capital marker than the road network,
        // which may extend across the entire mainland.
        let mut stone_sum_x = 0_i64;
        let mut stone_sum_y = 0_i64;
        let mut stone_count = 0_i64;
        for (chunk, index) in &self.scene_by_chunk {
            let scene = &self.scenes[*index];
            for y in 0..MAP_H as i32 {
                for x in 0..MAP_W as i32 {
                    if scene.map.get(x, y) != TileKind::StonePath {
                        continue;
                    }
                    stone_sum_x += i64::from(chunk.x * MAP_W as i32 + x);
                    stone_sum_y += i64::from(chunk.y * MAP_H as i32 + y);
                    stone_count += 1;
                }
            }
        }
        (49..=256).contains(&stone_count).then(|| {
            SurfaceCell::new(
                (stone_sum_x / stone_count) as i32,
                (stone_sum_y / stone_count) as i32,
            )
        })
    }

    pub(super) fn paint_civic_plaza(&mut self, center: SurfaceCell) -> usize {
        let mut changed = 0;
        for y in center.y - 5..=center.y + 5 {
            for x in center.x - 5..=center.x + 5 {
                let cell = SurfaceCell::new(x, y);
                if self.is_city_land(cell) && self.set_tile(cell, TileKind::StonePath) {
                    changed += 1;
                }
            }
        }
        changed
    }

    pub(super) fn paint_civic_plaza_apron(&mut self, center: SurfaceCell) -> usize {
        let stone_cells = (center.y - 5..=center.y + 5)
            .flat_map(|y| (center.x - 5..=center.x + 5).map(move |x| (x, y)))
            .filter(|(x, y)| self.tile(SurfaceCell::new(*x, *y)) == Some(TileKind::StonePath))
            .count();
        if stone_cells < 81 {
            return 0;
        }

        // Stone_Tan has complete authored V7 tuples against Dirt_Tan (Road),
        // while Stone_Tan touching Dirt_Brown directly has no source tuple.
        // A one-cell Road apron guarantees the authored sequence
        // StonePath -> Road -> natural ground at every plaza edge and corner.
        let mut changed = 0;
        for y in center.y - 6..=center.y + 6 {
            for x in center.x - 6..=center.x + 6 {
                let dx = (x - center.x).abs();
                let dy = (y - center.y).abs();
                if dx != 6 && dy != 6 {
                    continue;
                }
                let cell = SurfaceCell::new(x, y);
                if self.is_city_land(cell)
                    && self.tile(cell) != Some(TileKind::StonePath)
                    && self.set_tile(cell, TileKind::Road)
                {
                    changed += 1;
                }
            }
        }
        changed
    }

    pub(super) fn reserve_city_plot(
        &mut self,
        center: SurfaceCell,
        half_w: i32,
        half_h: i32,
        zone: ZoneKind,
    ) -> (usize, usize) {
        let mut eligible = 0;
        let area = (half_w * 2 + 1) * (half_h * 2 + 1);
        for y in center.y - half_h..=center.y + half_h {
            for x in center.x - half_w..=center.x + half_w {
                let cell = SurfaceCell::new(x, y);
                let Some((scene_index, local_x, local_y)) = self.local_cell(cell) else {
                    continue;
                };
                let existing_zone = self.scenes[scene_index].zone_at(local_x, local_y);
                if self.is_city_land(cell)
                    && self.tile(cell) != Some(TileKind::Road)
                    && can_reserve_planning_zone(existing_zone, zone)
                {
                    eligible += 1;
                }
            }
        }
        if eligible * 100 < area * 78 {
            return (0, 0);
        }

        let mut changed = 0;
        let mut removed = 0;
        for y in center.y - half_h..=center.y + half_h {
            for x in center.x - half_w..=center.x + half_w {
                let cell = SurfaceCell::new(x, y);
                let Some((scene_index, local_x, local_y)) = self.local_cell(cell) else {
                    continue;
                };
                let existing_zone = self.scenes[scene_index].zone_at(local_x, local_y);
                if !self.is_city_land(cell)
                    || self.tile(cell) == Some(TileKind::Road)
                    || !can_reserve_planning_zone(existing_zone, zone)
                {
                    continue;
                }
                removed += self.clear_natural_objects_at(cell);
                changed += usize::from(self.set_zone(cell, zone));
            }
        }
        (changed, removed)
    }

    pub(super) fn dominant_ground_around(
        &self,
        center: SurfaceCell,
        half_w: i32,
        half_h: i32,
    ) -> TileKind {
        const CANDIDATES: [TileKind; 4] = [
            TileKind::Grass,
            TileKind::Dirt,
            TileKind::Sand,
            TileKind::MudBank,
        ];
        let mut counts = [0usize; CANDIDATES.len()];
        for y in center.y - half_h - 2..=center.y + half_h + 2 {
            for x in center.x - half_w - 2..=center.x + half_w + 2 {
                if x > center.x - half_w - 1
                    && x < center.x + half_w + 1
                    && y > center.y - half_h - 1
                    && y < center.y + half_h + 1
                {
                    continue;
                }
                let Some(tile) = self.tile(SurfaceCell::new(x, y)) else {
                    continue;
                };
                if let Some(index) = CANDIDATES.iter().position(|candidate| *candidate == tile) {
                    counts[index] += 1;
                }
            }
        }
        counts
            .iter()
            .enumerate()
            .max_by_key(|(_, count)| **count)
            .map(|(index, _)| CANDIDATES[index])
            .unwrap_or(TileKind::Grass)
    }

    pub(super) fn clear_legacy_plot_foundation(
        &mut self,
        center: SurfaceCell,
        half_w: i32,
        half_h: i32,
    ) -> usize {
        let area = ((half_w * 2 + 1) * (half_h * 2 + 1)) as usize;
        let stone_cells = (center.y - half_h..=center.y + half_h)
            .flat_map(|y| (center.x - half_w..=center.x + half_w).map(move |x| (x, y)))
            .filter(|(x, y)| self.tile(SurfaceCell::new(*x, *y)) == Some(TileKind::StonePath))
            .count();
        if stone_cells * 100 < area * 70 {
            return 0;
        }
        let replacement = self.dominant_ground_around(center, half_w, half_h);
        let mut changed = 0;
        for y in center.y - half_h..=center.y + half_h {
            for x in center.x - half_w..=center.x + half_w {
                let cell = SurfaceCell::new(x, y);
                if self.tile(cell) == Some(TileKind::StonePath) && self.set_tile(cell, replacement)
                {
                    changed += 1;
                }
            }
        }
        changed
    }

    pub(super) fn reserve_harbor_district(
        &mut self,
        landfall: SurfaceCell,
        city_center: SurfaceCell,
    ) -> (usize, usize) {
        // AC3: Harbor is a city district. Start on the city<->coast axis and
        // search only a compact neighborhood between civic core and landfall.
        // This replaces the old independent coastal-POI search, which could
        // produce a detached harbor followed by a long wilderness connector.
        let dx = landfall.x - city_center.x;
        let dy = landfall.y - city_center.y;
        let preferred = SurfaceCell::new(
            city_center.x + dx * 3 / 4,
            city_center.y + dy * 3 / 4,
        );
        for axial in [0, -4, 4, -8, 8] {
            for lateral in [0, -6, 6, -12, 12] {
                let center = SurfaceCell::new(preferred.x + lateral, preferred.y + axial);
                let city_distance =
                    (center.x - city_center.x).abs() + (center.y - city_center.y).abs();
                let coast_distance =
                    (center.x - landfall.x).abs() + (center.y - landfall.y).abs();
                if city_distance > CITY_HARBOR_MAX_LINK_DISTANCE_TILES || coast_distance > 48 {
                    continue;
                }
                let reserved = self.reserve_city_plot(center, 18, 9, ZoneKind::HarborLot);
                if reserved.0 > 0 {
                    return reserved;
                }
            }
        }
        (0, 0)
    }

    pub(super) fn paint_reserved_harbor_surface(&mut self) -> usize {
        let mut targets = Vec::new();
        for (chunk, index) in &self.scene_by_chunk {
            let scene = &self.scenes[*index];
            for y in 0..MAP_H as i32 {
                for x in 0..MAP_W as i32 {
                    if scene.zone_at(x, y) == ZoneKind::HarborLot {
                        targets.push(SurfaceCell::new(
                            chunk.x * MAP_W as i32 + x,
                            chunk.y * MAP_H as i32 + y,
                        ));
                    }
                }
            }
        }

        let target_set = targets.iter().copied().collect::<std::collections::BTreeSet<_>>();
        let mut changed = 0;
        for cell in &targets {
            let Some(tile) = self.tile(*cell) else { continue; };
            if tile.is_water() || matches!(tile, TileKind::PlankFloor | TileKind::WoodFloor | TileKind::Bridge) {
                continue;
            }
            changed += usize::from(self.set_tile(*cell, TileKind::StonePath));
        }

        // Stone_Tan needs a supported dry transition instead of touching raw
        // brown dirt/grass at a hard rectangular boundary. Ring the dry harbor
        // floor with the authored road family; the coast/water side remains open
        // for the future wooden dock/pier materializer.
        let mut apron = Vec::new();
        for cell in &targets {
            for neighbor in [
                SurfaceCell::new(cell.x - 1, cell.y),
                SurfaceCell::new(cell.x + 1, cell.y),
                SurfaceCell::new(cell.x, cell.y - 1),
                SurfaceCell::new(cell.x, cell.y + 1),
            ] {
                if target_set.contains(&neighbor) {
                    continue;
                }
                let Some(tile) = self.tile(neighbor) else { continue; };
                if tile.is_water() || !self.is_road_land(neighbor) {
                    continue;
                }
                apron.push(neighbor);
            }
        }
        apron.sort_unstable();
        apron.dedup();
        for cell in apron {
            changed += usize::from(self.set_tile(cell, TileKind::Road));
        }
        changed
    }

    pub(super) fn paint_harbor_pier(&mut self, landfall: SurfaceCell) -> usize {
        // The ordinary road authority terminates on this dry coastal tile. The
        // existing audited LPC wood-bridge family owns the first over-water
        // traversal so the harbor reads as stone quay -> wood pier -> water.
        // Prefer south from this southern harbor band, then choose the cardinal
        // direction with the longest immediately contiguous water run.
        let mut best: Option<(usize, i32, i32)> = None;
        for (dx, dy) in [(0, 1), (1, 0), (-1, 0), (0, -1)] {
            let mut run = 0usize;
            for distance in 1..=12_i32 {
                let cell = SurfaceCell::new(
                    landfall.x + dx * distance,
                    landfall.y + dy * distance,
                );
                if self.tile(cell).is_some_and(TileKind::is_water) {
                    run += 1;
                } else {
                    break;
                }
            }
            if run >= 2 && best.is_none_or(|(best_run, _, _)| run > best_run) {
                best = Some((run, dx, dy));
            }
        }
        let Some((run, dx, dy)) = best else {
            return 0;
        };

        let mut changed = 0;
        for distance in 1..=run.min(8) as i32 {
            let cell = SurfaceCell::new(
                landfall.x + dx * distance,
                landfall.y + dy * distance,
            );
            if self.tile(cell).is_some_and(TileKind::is_water)
                && self.set_tile(cell, TileKind::Bridge)
            {
                changed += 1;
            }
        }
        changed
    }

    pub(super) fn repair_harbor_road_intrusions(&mut self, landfall: SurfaceCell) -> usize {
        let mut changed = 0;
        for y in landfall.y - 4..=landfall.y + 10 {
            for x in landfall.x - 6..=landfall.x + 6 {
                let cell = SurfaceCell::new(x, y);
                if self.tile(cell) != Some(TileKind::Road) || self.neighboring_water_count(cell) < 4
                {
                    continue;
                }
                let replacement = [
                    SurfaceCell::new(x - 1, y),
                    SurfaceCell::new(x + 1, y),
                    SurfaceCell::new(x, y - 1),
                    SurfaceCell::new(x, y + 1),
                ]
                .into_iter()
                .filter_map(|neighbor| self.tile(neighbor))
                .find(|tile| tile.is_water())
                .unwrap_or(TileKind::OceanShallow);
                changed += usize::from(self.set_tile(cell, replacement));
            }
        }
        changed
    }
}
