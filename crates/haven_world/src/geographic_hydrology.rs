//! Deterministic geographic drainage corridors for Havenwild world generation.
//!
//! Rivers are explicit source-to-sink features, not thresholded noise streaks.
//! An elevated source pool always owns a continuous river corridor to either
//! marine water or a generated lowland pond/lake.  When that corridor crosses a
//! structural Level 2+ -> lower-ground boundary, the ordinary structural resolver sees
//! RiverWater on both sides and therefore emits the required waterfall edge.
//! Waterfall art remains presentation; hydrology owns the continuous water path.

use crate::{
    geographic_surface::{sample_geographic_surface, GeographicGenerationProfile},
};
use serde::{Deserialize, Serialize};

pub const GEOGRAPHIC_HYDROLOGY_SCHEMA: &str = "havenwild.geographic_hydrology.v0_1";

const WATERSHED_MACRO_TILES: i32 = 640;
const DRAINAGE_DOMAIN: u64 = 0x4452_4149_4e41_4745;
const SOURCE_DOMAIN: u64 = 0x5352_4345_504f_4f4c;
const SINK_DOMAIN: u64 = 0x5349_4e4b_504f_4f4c;

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub enum GeographicWaterFeatureKind {
    #[default]
    None,
    SourcePool,
    River,
    SinkPond,
    SinkLake,
    RiverMouth,
}

#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct GeographicHydrologySample {
    pub kind: GeographicWaterFeatureKind,
    pub feature_id: u64,
    pub progress: f32,
    pub source_structural_level: u8,
}

impl GeographicHydrologySample {
    pub const fn is_water(self) -> bool {
        !matches!(self.kind, GeographicWaterFeatureKind::None)
    }

    pub const fn is_river(self) -> bool {
        matches!(
            self.kind,
            GeographicWaterFeatureKind::River | GeographicWaterFeatureKind::RiverMouth
        )
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Serialize, Deserialize)]
pub struct DrainageFeature {
    pub id: u64,
    pub source_x: f64,
    pub source_y: f64,
    pub sink_x: f64,
    pub sink_y: f64,
    pub control_x: f64,
    pub control_y: f64,
    pub source_radius: f64,
    pub sink_radius: f64,
    pub river_half_width: f64,
    pub source_structural_level: u8,
    pub sink_is_ocean: bool,
    pub sink_is_lake: bool,
}

impl DrainageFeature {
    fn from_macro_cell(
        seed: u64,
        cell_x: i32,
        cell_y: i32,
        profile: GeographicGenerationProfile,
    ) -> Option<Self> {
        let id = hash2(seed ^ DRAINAGE_DOMAIN, cell_x, cell_y);
        // River density controls how many drainage systems exist. Waterfall
        // density biases how often those systems originate on uplands, but it
        // never suppresses a waterfall once a generated watercourse crosses a
        // structural drop.
        let enabled_threshold = (0.055
            + f64::from(profile.river_density) * 0.19
            + f64::from(profile.waterfall_density) * 0.11)
            .clamp(0.05, 0.36);
        if unit_from_hash(id) >= enabled_threshold {
            return None;
        }

        let source = choose_upland_source(seed, cell_x, cell_y, profile)?;
        let sink = choose_sink(seed, id, source, profile)?;
        let dx = sink.0 - source.0;
        let dy = sink.1 - source.1;
        let length = (dx * dx + dy * dy).sqrt();
        if length < 96.0 {
            return None;
        }
        let nx = -dy / length;
        let ny = dx / length;
        let bend_sign = if id & 1 == 0 { -1.0 } else { 1.0 };
        let bend = bend_sign
            * length
            * (0.07 + hash01(id ^ 0x4354_524c, cell_x, cell_y) * 0.10);
        let mut feature = Self {
            id,
            source_x: source.0,
            source_y: source.1,
            sink_x: sink.0,
            sink_y: sink.1,
            control_x: (source.0 + sink.0) * 0.5 + nx * bend,
            control_y: (source.1 + sink.1) * 0.5 + ny * bend,
            // Upland sources range from tiny springs/tarns to substantial
            // mountain pools. Every one gets a valid outflow before it is
            // admitted to the generated world.
            source_radius: 2.5
                + hash01(id ^ SOURCE_DOMAIN, cell_x, cell_y)
                    * (4.5
                        + f64::from(profile.pond_density) * 6.0
                        + f64::from(profile.lake_density) * 6.0),
            sink_radius: 6.0
                + f64::from(profile.pond_density) * 4.0
                + hash01(id ^ SINK_DOMAIN, cell_x, cell_y) * 9.0,
            river_half_width: 1.55 + f64::from(profile.river_density) * 2.15,
            source_structural_level: source.2,
            sink_is_ocean: sink.2,
            sink_is_lake: false,
        };
        feature.sink_is_lake = !feature.sink_is_ocean
            && unit_from_hash(id ^ 0x4c41_4b45) < f64::from(profile.lake_density) * 0.72;
        if feature.sink_is_lake {
            feature.sink_radius *= 1.55;
        }

        // A river may descend through multiple structural levels but must not
        // climb back onto another plateau after it has descended.  Try a
        // straightened control point if the initial meander violates that rule.
        if !feature.structural_levels_are_monotonic(seed, profile) {
            feature.control_x = (feature.source_x + feature.sink_x) * 0.5;
            feature.control_y = (feature.source_y + feature.sink_y) * 0.5;
        }
        if !feature.structural_levels_are_monotonic(seed, profile) {
            return None;
        }
        Some(feature)
    }

    fn structural_levels_are_monotonic(
        self,
        seed: u64,
        profile: GeographicGenerationProfile,
    ) -> bool {
        let dx = self.sink_x - self.source_x;
        let dy = self.sink_y - self.source_y;
        let direct_length = (dx * dx + dy * dy).sqrt();
        // Sample at roughly four-tile intervals (with sensible bounds) so a
        // narrow raised shelf cannot hide between sparse control samples. The
        // rasterized river may descend directly across a normalized true cliff
        // (for example 2->0), but may never climb after it has descended.
        let steps = ((direct_length / 4.0).ceil() as usize).clamp(32, 256);
        if !self.structural_levels_are_monotonic_at_steps(seed, profile, steps) {
            return false;
        }
        // Runtime/certification observes the connector corridor at 64 steps.
        // Re-check at that resolution so a narrow uphill shelf cannot hide
        // between the denser samples. Multi-level downward drops are valid
        // waterfall cliffs under the normalized Level-2+ structural grammar.
        self.structural_levels_are_monotonic_at_steps(seed, profile, 64)
    }

    fn structural_levels_are_monotonic_at_steps(
        self,
        seed: u64,
        profile: GeographicGenerationProfile,
        steps: usize,
    ) -> bool {
        let steps = steps.max(1);
        let mut previous = self.source_structural_level;
        for step in 1..=steps {
            let t = step as f64 / steps as f64;
            let (x, y) = self.point(t);
            let base = sample_geographic_surface(seed, x.round() as i32, y.round() as i32, profile);
            let level = if base.land { base.structural_level } else { 0 };
            if level > previous {
                return false;
            }
            previous = level;
        }
        true
    }

    pub fn point(self, t: f64) -> (f64, f64) {
        let t = t.clamp(0.0, 1.0);
        let inv = 1.0 - t;
        (
            inv * inv * self.source_x + 2.0 * inv * t * self.control_x + t * t * self.sink_x,
            inv * inv * self.source_y + 2.0 * inv * t * self.control_y + t * t * self.sink_y,
        )
    }

    fn sample(self, seed: u64, x: i32, y: i32, profile: GeographicGenerationProfile) -> GeographicHydrologySample {
        let px = x as f64 + 0.5;
        let py = y as f64 + 0.5;
        let source_distance = distance(px, py, self.source_x, self.source_y);
        if source_distance <= self.source_radius {
            return GeographicHydrologySample {
                kind: GeographicWaterFeatureKind::SourcePool,
                feature_id: self.id,
                progress: 0.0,
                source_structural_level: self.source_structural_level,
            };
        }

        let sink_distance = distance(px, py, self.sink_x, self.sink_y);
        if !self.sink_is_ocean && sink_distance <= self.sink_radius {
            return GeographicHydrologySample {
                kind: if self.sink_is_lake {
                    GeographicWaterFeatureKind::SinkLake
                } else {
                    GeographicWaterFeatureKind::SinkPond
                },
                feature_id: self.id,
                progress: 1.0,
                source_structural_level: self.source_structural_level,
            };
        }

        let (path_distance, progress) = distance_to_curve(self, px, py);
        // Rivers broaden downstream rather than reading as one constant-width
        // procedural stripe across the landscape.
        let local_half_width = self.river_half_width * (0.72 + progress * 0.72);
        if path_distance > local_half_width {
            return GeographicHydrologySample::default();
        }
        let base = sample_geographic_surface(seed, x, y, profile);
        GeographicHydrologySample {
            kind: if !base.land && progress > 0.76 {
                GeographicWaterFeatureKind::RiverMouth
            } else {
                GeographicWaterFeatureKind::River
            },
            feature_id: self.id,
            progress: progress as f32,
            source_structural_level: self.source_structural_level,
        }
    }
}

pub fn sample_geographic_hydrology(
    seed: u64,
    global_x: i32,
    global_y: i32,
    profile: GeographicGenerationProfile,
) -> GeographicHydrologySample {
    let features = drainage_features_for_bounds(
        seed,
        global_x,
        global_y,
        global_x,
        global_y,
        profile,
    );
    sample_geographic_hydrology_from_features(
        seed,
        global_x,
        global_y,
        profile,
        &features,
    )
}

/// Build the small set of drainage features that can intersect a geographic
/// rectangle. Chunk generation calls this once, then samples all 4096 cells
/// against the cached feature list instead of rediscovering watersheds for
/// every tile.
pub fn drainage_features_for_bounds(
    seed: u64,
    min_x: i32,
    min_y: i32,
    max_x: i32,
    max_y: i32,
    profile: GeographicGenerationProfile,
) -> Vec<DrainageFeature> {
    let min_macro_x = min_x.div_euclid(WATERSHED_MACRO_TILES) - 1;
    let max_macro_x = max_x.div_euclid(WATERSHED_MACRO_TILES) + 1;
    let min_macro_y = min_y.div_euclid(WATERSHED_MACRO_TILES) - 1;
    let max_macro_y = max_y.div_euclid(WATERSHED_MACRO_TILES) + 1;
    let mut features = Vec::new();
    for cell_y in min_macro_y..=max_macro_y {
        for cell_x in min_macro_x..=max_macro_x {
            if let Some(feature) = DrainageFeature::from_macro_cell(seed, cell_x, cell_y, profile) {
                features.push(feature);
            }
        }
    }
    features
}

pub fn sample_geographic_hydrology_from_features(
    seed: u64,
    global_x: i32,
    global_y: i32,
    profile: GeographicGenerationProfile,
    features: &[DrainageFeature],
) -> GeographicHydrologySample {
    let mut best = GeographicHydrologySample::default();
    for &feature in features {
        let sample = feature.sample(seed, global_x, global_y, profile);
        if sample.is_water() && priority(sample.kind) > priority(best.kind) {
            best = sample;
        }
    }
    best
}

pub fn drainage_feature_for_macro_cell(
    seed: u64,
    cell_x: i32,
    cell_y: i32,
    profile: GeographicGenerationProfile,
) -> Option<DrainageFeature> {
    DrainageFeature::from_macro_cell(seed, cell_x, cell_y, profile)
}

fn choose_upland_source(
    seed: u64,
    cell_x: i32,
    cell_y: i32,
    profile: GeographicGenerationProfile,
) -> Option<(f64, f64, u8)> {
    let id = hash2(seed ^ SOURCE_DOMAIN, cell_x, cell_y);
    let x0 = cell_x * WATERSHED_MACRO_TILES;
    let y0 = cell_y * WATERSHED_MACRO_TILES;
    let mut best: Option<(f64, f64, u8, f32)> = None;

    // Keep the cheap seed-random probes as the first lane. They preserve the
    // existing look on worlds where they already find a suitable upland.
    for candidate in 0..24_i32 {
        let hx = hash01(id ^ (candidate as u64).wrapping_mul(0x31), cell_x, cell_y);
        let hy = hash01(id ^ (candidate as u64).wrapping_mul(0x53), cell_x, cell_y);
        let x = x0 as f64 + 48.0 + hx * f64::from(WATERSHED_MACRO_TILES - 96);
        let y = y0 as f64 + 48.0 + hy * f64::from(WATERSHED_MACRO_TILES - 96);
        let sample = sample_geographic_surface(seed, x.round() as i32, y.round() as i32, profile);
        if !sample.land || sample.structural_level == 0 || sample.coast_distance_tiles < 24.0 {
            continue;
        }
        let score = source_score(sample.structural_level, sample.elevation, sample.coast_distance_tiles);
        if best.map(|entry| score > entry.3).unwrap_or(true) {
            best = Some((x, y, sample.structural_level, score));
        }
    }

    // H20R2 deterministic fallback. The finite-archipelago surface can place
    // broad uplands between the old random probes, particularly when the world
    // profile changes scale or landmass count. A seed-shifted 9x9 stratified
    // scan guarantees that an available upland is discoverable without turning
    // hydrology into a full-resolution search.
    if best.is_none() {
        let divisions = 9_i32;
        let span = WATERSHED_MACRO_TILES - 64;
        let offset_x = (id as i32).rem_euclid(divisions);
        let offset_y = ((id >> 8) as i32).rem_euclid(divisions);
        for row in 0..divisions {
            for column in 0..divisions {
                let sx = (column + offset_x).rem_euclid(divisions);
                let sy = (row + offset_y).rem_euclid(divisions);
                let x = x0 as f64 + 32.0 + (f64::from(sx) + 0.5) * f64::from(span) / f64::from(divisions);
                let y = y0 as f64 + 32.0 + (f64::from(sy) + 0.5) * f64::from(span) / f64::from(divisions);
                let sample = sample_geographic_surface(seed, x.round() as i32, y.round() as i32, profile);
                if !sample.land || sample.structural_level == 0 || sample.coast_distance_tiles < 12.0 {
                    continue;
                }
                let score = source_score(sample.structural_level, sample.elevation, sample.coast_distance_tiles);
                if best.map(|entry| score > entry.3).unwrap_or(true) {
                    best = Some((x, y, sample.structural_level, score));
                }
            }
        }
    }

    best.map(|(x, y, level, _)| (x, y, level))
}

fn source_score(structural_level: u8, elevation: f32, coast_distance_tiles: f32) -> f32 {
    // Prefer real raised ground. Level 1 is reserved for authored walking-ramp
    // transitions and is not a geographic drainage source tier; production
    // uplands begin at Level 2 under the normalized structural grammar.
    let level_score = 0.72 + f32::from(structural_level.min(4)) * 0.08;
    elevation * 0.55 + level_score + (coast_distance_tiles.min(160.0) / 160.0) * 0.12
}

fn choose_sink(
    seed: u64,
    id: u64,
    source: (f64, f64, u8),
    profile: GeographicGenerationProfile,
) -> Option<(f64, f64, bool)> {
    let base_angle = hash01(id ^ SINK_DOMAIN, 0, 0) * std::f64::consts::TAU;
    let mut best: Option<(f64, f64, bool, f64)> = None;

    // Search a denser, scale-independent radial field. A candidate is admitted
    // only if the straight source->sink corridor is monotonically downhill.
    // A normalized true cliff may descend directly 2->0 (or farther from a
    // higher plateau); the later Bezier meander may be retained when valid, and the
    // existing straightening fallback is therefore guaranteed to have a legal
    // corridor to fall back to.
    for ring in 0..9 {
        let distance = 112.0 + ring as f64 * 64.0;
        for spoke in 0..32 {
            let phase = spoke as f64 * std::f64::consts::TAU / 32.0;
            let angle = base_angle + phase;
            let x = source.0 + angle.cos() * distance;
            let y = source.1 + angle.sin() * distance;
            let sample = sample_geographic_surface(seed, x.round() as i32, y.round() as i32, profile);
            if sample.land && sample.structural_level > 0 {
                continue;
            }
            if !straight_corridor_is_monotonic(seed, source, x, y, profile) {
                continue;
            }
            let ocean = !sample.land;
            let score = if ocean {
                -2_000.0 + distance * 0.025 + f64::from(sample.coast_distance_tiles.abs()) * 0.02
            } else {
                -900.0 + f64::from(sample.elevation) * 80.0 + distance * 0.02
            };
            if best.map(|entry| score < entry.3).unwrap_or(true) {
                best = Some((x, y, ocean, score));
            }
        }
        if best.map(|entry| entry.2).unwrap_or(false) {
            break;
        }
    }

    best.map(|(x, y, ocean, _)| (x, y, ocean))
}

fn straight_corridor_is_monotonic(
    seed: u64,
    source: (f64, f64, u8),
    sink_x: f64,
    sink_y: f64,
    profile: GeographicGenerationProfile,
) -> bool {
    let dx = sink_x - source.0;
    let dy = sink_y - source.1;
    let length = (dx * dx + dy * dy).sqrt();
    if length < 96.0 {
        return false;
    }
    let steps = ((length / 3.0).ceil() as usize).clamp(40, 256);
    let mut previous = source.2;
    let mut saw_drop = false;
    for step in 1..=steps {
        let t = step as f64 / steps as f64;
        let x = source.0 + dx * t;
        let y = source.1 + dy * t;
        let sample = sample_geographic_surface(seed, x.round() as i32, y.round() as i32, profile);
        let level = if sample.land { sample.structural_level } else { 0 };
        if level > previous {
            return false;
        }
        saw_drop |= level < previous;
        previous = level;
    }
    // A raised source must actually drain off its source shelf. This also keeps
    // the waterfall-eligibility invariant meaningful rather than producing a
    // same-level decorative river that never crosses structural terrain.
    previous == 0 && saw_drop
}

fn distance_to_curve(feature: DrainageFeature, px: f64, py: f64) -> (f64, f64) {
    let mut best_distance = f64::INFINITY;
    let mut best_progress = 0.0;
    let mut previous = feature.point(0.0);
    for step in 1..=32 {
        let t = step as f64 / 32.0;
        let current = feature.point(t);
        let (distance, local_t) = distance_to_segment(px, py, previous.0, previous.1, current.0, current.1);
        if distance < best_distance {
            best_distance = distance;
            best_progress = (step as f64 - 1.0 + local_t) / 32.0;
        }
        previous = current;
    }
    (best_distance, best_progress)
}

fn distance_to_segment(
    px: f64,
    py: f64,
    ax: f64,
    ay: f64,
    bx: f64,
    by: f64,
) -> (f64, f64) {
    let vx = bx - ax;
    let vy = by - ay;
    let wx = px - ax;
    let wy = py - ay;
    let length_sq = vx * vx + vy * vy;
    if length_sq <= f64::EPSILON {
        return (distance(px, py, ax, ay), 0.0);
    }
    let t = ((wx * vx + wy * vy) / length_sq).clamp(0.0, 1.0);
    let cx = ax + vx * t;
    let cy = ay + vy * t;
    (distance(px, py, cx, cy), t)
}

fn distance(ax: f64, ay: f64, bx: f64, by: f64) -> f64 {
    let dx = ax - bx;
    let dy = ay - by;
    (dx * dx + dy * dy).sqrt()
}

fn priority(kind: GeographicWaterFeatureKind) -> u8 {
    match kind {
        GeographicWaterFeatureKind::None => 0,
        GeographicWaterFeatureKind::SinkPond | GeographicWaterFeatureKind::SinkLake => 1,
        GeographicWaterFeatureKind::RiverMouth => 2,
        GeographicWaterFeatureKind::River => 3,
        GeographicWaterFeatureKind::SourcePool => 4,
    }
}

fn hash01(seed: u64, x: i32, y: i32) -> f64 {
    unit_from_hash(hash2(seed, x, y))
}

fn unit_from_hash(value: u64) -> f64 {
    (value as f64) / (u64::MAX as f64)
}

fn hash2(seed: u64, x: i32, y: i32) -> u64 {
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
    fn generated_upland_water_sources_have_a_complete_downhill_sink_path() {
        let profile = GeographicGenerationProfile::default();
        // This invariant belongs to the production Archipelago profile rather
        // than to one historical BalancedContinent fixture. Search a small,
        // deterministic seed set so a future topology adjustment cannot turn
        // "this exact macro cell happens to contain a river" into the thing
        // under test. The WATERFALL seed is also used by the structural-drop
        // regression below and is known to exercise generated drainage.
        let seeds = [
            0x4859_4452_4f4c_4f47,
            0x5741_5445_5246_414c,
            0x4152_4348_4950_454c,
        ];
        let mut found = None;
        'search: for seed in seeds {
            for my in -8..=8 {
                for mx in -8..=8 {
                    if let Some(feature) = drainage_feature_for_macro_cell(seed, mx, my, profile) {
                        found = Some((seed, feature));
                        break 'search;
                    }
                }
            }
        }
        let (seed, feature) =
            found.expect("expected at least one deterministic Archipelago drainage feature");
        assert!(feature.source_structural_level > 0);
        assert!(feature.sink_is_ocean || {
            let sink = sample_geographic_surface(
                seed,
                feature.sink_x.round() as i32,
                feature.sink_y.round() as i32,
                profile,
            );
            sink.structural_level == 0
        });
        assert!(feature.structural_levels_are_monotonic(seed, profile));
    }

    #[test]
    fn any_structural_drop_along_a_river_is_waterfall_eligible_by_construction() {
        let profile = GeographicGenerationProfile::default();
        let seed = 0x5741_5445_5246_414c;
        let mut checked = false;
        for my in -8..=8 {
            for mx in -8..=8 {
                let Some(feature) = drainage_feature_for_macro_cell(seed, mx, my, profile) else {
                    continue;
                };
                let mut previous_level = feature.source_structural_level;
                for step in 1..=64 {
                    let t = step as f64 / 64.0;
                    let (x, y) = feature.point(t);
                    let sample = sample_geographic_surface(seed, x.round() as i32, y.round() as i32, profile);
                    let level = if sample.land { sample.structural_level } else { 0 };
                    if level < previous_level {
                        assert!(
                            previous_level >= 2,
                            "generated waterfall source must be a true Level-2+ cliff"
                        );
                        assert_ne!(level, 1, "Level 1 is reserved for authored walking ramps");
                        let hydro = sample_geographic_hydrology(
                            seed,
                            x.round() as i32,
                            y.round() as i32,
                            profile,
                        );
                        assert!(hydro.is_water());
                        checked = true;
                    }
                    previous_level = level;
                }
                if checked {
                    return;
                }
            }
        }
        assert!(checked, "expected at least one drainage feature to cross a structural drop");
    }
}
