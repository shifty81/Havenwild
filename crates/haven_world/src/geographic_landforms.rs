//! Coherent macro-landform sampling for Havenwild's continuous surfaces.
//!
//! The old generator promoted raw noise contours directly into visible cliffs
//! and highland materials. That produced long diagonal ribbons and repeated
//! "tiger stripe" bands. This module instead generates bounded geographic
//! features (deterministic bent ridge chains and broad ridge bands) on a macro
//! lattice. Noise may still describe fine geology/hydrology, but it no longer
//! owns visible structural topology.

use serde::{Deserialize, Serialize};

pub const GEOGRAPHIC_LANDFORM_SCHEMA: &str = "havenwild.geographic_landforms.v0_1";

const MACRO_CELL_TILES: i32 = 192;
const NEIGHBOR_MACRO_RADIUS: i32 = 1;
const FEATURE_DOMAIN: u64 = 0x4745_4f46_4541_5431;
const LOBE_DOMAIN: u64 = 0x4c4f_4245_4645_4154;
const CORE_DOMAIN: u64 = 0x434f_5245_4645_4154;
const FOREST_DOMAIN: u64 = 0x464f_5245_5354_3031;
const FOREST_MACRO_CELL_TILES: i32 = 224;

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum GeographicLandformKind {
    #[default]
    Lowland,
    UplandPlateau,
    HighlandCore,
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct GeographicLandformSample {
    pub kind: GeographicLandformKind,
    pub structural_level: u8,
    pub feature_id: u64,
}

impl GeographicLandformSample {
    pub const fn is_upland(self) -> bool {
        self.structural_level > 0
    }

    pub const fn is_highland_core(self) -> bool {
        self.structural_level >= 2
    }
}

/// Returns the deterministic macro-geographic landform at one global tile.
///
/// Features are finite, broad shapes. Sampling a tile never compares a raw
/// noise value to a cliff threshold, so the result cannot become an unbounded
/// contour stripe. Neighboring storage chunks sample the same global features
/// and therefore stitch without chunk-edge special cases.
pub fn sample_geographic_landform(
    seed: u64,
    global_x: i32,
    global_y: i32,
    mountain_strength: f32,
) -> GeographicLandformSample {
    let strength = mountain_strength.clamp(0.0, 1.0) as f64;
    let macro_x = global_x.div_euclid(MACRO_CELL_TILES);
    let macro_y = global_y.div_euclid(MACRO_CELL_TILES);

    let mut best = GeographicLandformSample::default();
    let mut best_depth = f64::INFINITY;

    for cell_y in macro_y - NEIGHBOR_MACRO_RADIUS..=macro_y + NEIGHBOR_MACRO_RADIUS {
        for cell_x in macro_x - NEIGHBOR_MACRO_RADIUS..=macro_x + NEIGHBOR_MACRO_RADIUS {
            let feature_hash = hash2(seed ^ FEATURE_DOMAIN, cell_x, cell_y);
            if !feature_enabled(feature_hash, strength) {
                continue;
            }

            let feature = BentRidgeFeature::from_macro_cell(seed, cell_x, cell_y, strength);
            let depth = feature.outer_depth(global_x, global_y)
                / feature.contour_modulation(global_x, global_y, false);
            if depth > 1.0 || depth >= best_depth {
                continue;
            }

            let core_depth = feature.core_depth(global_x, global_y)
                / feature.contour_modulation(global_x, global_y, true);
            let structural_level = if feature.has_core && core_depth <= 1.0 {
                2
            } else {
                1
            };
            best_depth = depth;
            best = GeographicLandformSample {
                kind: if structural_level >= 2 {
                    GeographicLandformKind::HighlandCore
                } else {
                    GeographicLandformKind::UplandPlateau
                },
                structural_level,
                feature_id: feature.id,
            };
        }
    }

    best
}


/// Returns a broad deterministic forest-habitat weight in the range `0..=1`.
///
/// Forests are finite geographic patches rather than a raw-noise threshold.
/// The weight deliberately feathers at the perimeter so object population can
/// produce a dense interior, sparse woodland edge, and open meadow outside.
/// A deterministic clearing may be cut from the center of some forest patches.
pub fn geographic_forest_habitat(seed: u64, global_x: i32, global_y: i32) -> f32 {
    let macro_x = global_x.div_euclid(FOREST_MACRO_CELL_TILES);
    let macro_y = global_y.div_euclid(FOREST_MACRO_CELL_TILES);
    let mut best = 0.0_f64;

    for cell_y in macro_y - 1..=macro_y + 1 {
        for cell_x in macro_x - 1..=macro_x + 1 {
            let id = hash2(seed ^ FOREST_DOMAIN, cell_x, cell_y);
            if unit_from_hash(id) >= 0.62 {
                continue;
            }

            let x0 = cell_x * FOREST_MACRO_CELL_TILES;
            let y0 = cell_y * FOREST_MACRO_CELL_TILES;
            let center_x = x0 as f64 + 52.0 + hash01(id ^ 0x31, cell_x, cell_y) * 120.0;
            let center_y = y0 as f64 + 52.0 + hash01(id ^ 0x32, cell_x, cell_y) * 120.0;
            let radius_x = 48.0 + hash01(id ^ 0x33, cell_x, cell_y) * 42.0;
            let radius_y = 38.0 + hash01(id ^ 0x34, cell_x, cell_y) * 38.0;
            let angle = hash01(id ^ 0x35, cell_x, cell_y) * std::f64::consts::PI;
            let grove = RotatedEllipse::new(center_x, center_y, radius_x, radius_y, angle);
            let distance = grove.normalized_distance(global_x, global_y);
            if distance > 1.0 {
                continue;
            }

            // normalized_distance is squared elliptical distance. Converting it
            // to a radial distance gives a generous dense core and a broad,
            // naturally thinning edge rather than a hard tree wall.
            let radial = distance.sqrt();
            let mut weight = ((1.0 - radial) / 0.55).clamp(0.0, 1.0);

            // Roughly one third of groves contain a coherent meadow clearing.
            if unit_from_hash(id ^ 0x434c_4541_5249_4e47) < 0.34 {
                let clearing = RotatedEllipse::new(
                    center_x + (hash01(id ^ 0x36, cell_x, cell_y) - 0.5) * radius_x * 0.34,
                    center_y + (hash01(id ^ 0x37, cell_x, cell_y) - 0.5) * radius_y * 0.34,
                    radius_x * (0.16 + hash01(id ^ 0x38, cell_x, cell_y) * 0.08),
                    radius_y * (0.16 + hash01(id ^ 0x39, cell_x, cell_y) * 0.08),
                    angle,
                );
                let clearing_distance = clearing.normalized_distance(global_x, global_y);
                if clearing_distance <= 1.0 {
                    weight *= clearing_distance.sqrt().clamp(0.0, 1.0);
                }
            }

            best = best.max(weight);
        }
    }

    best as f32
}

pub fn geographic_structural_level(
    seed: u64,
    global_x: i32,
    global_y: i32,
    mountain_strength: f32,
) -> u8 {
    sample_geographic_landform(seed, global_x, global_y, mountain_strength).structural_level
}

fn feature_enabled(hash: u64, strength: f64) -> bool {
    // Roughly 36-63% of macro cells host an upland feature. Because each
    // feature occupies only part of its 192x192 macro cell, actual raised-land
    // coverage remains broad but restrained.
    let threshold = 0.36 + strength * 0.27;
    unit_from_hash(hash) < threshold
}

#[derive(Clone, Copy, Debug)]
struct BentRidgeFeature {
    id: u64,
    outer: RidgeBand,
    branch: Option<RidgeBand>,
    core: RidgeBand,
    core_branch: Option<RidgeBand>,
    has_core: bool,
}

impl BentRidgeFeature {
    fn from_macro_cell(seed: u64, cell_x: i32, cell_y: i32, strength: f64) -> Self {
        let id = hash2(seed ^ FEATURE_DOMAIN, cell_x, cell_y);
        let x0 = cell_x * MACRO_CELL_TILES;
        let y0 = cell_y * MACRO_CELL_TILES;

        // AC2: structural highlands are ridge/shelf systems, not constant-width
        // capsules. The primary spine has unequal ends and a displaced knee,
        // widths taper independently, and many features grow a secondary shelf
        // or spur. The resulting contour remains deterministic and broad enough
        // for LPC cliff grammar, but no longer reads as a stretched ellipse.
        let center_x = x0 as f64 + 34.0 + hash01(id ^ 0x01, cell_x, cell_y) * 124.0;
        let center_y = y0 as f64 + 34.0 + hash01(id ^ 0x02, cell_x, cell_y) * 124.0;
        let angle = hash01(id ^ 0x05, cell_x, cell_y) * std::f64::consts::TAU;
        let length = (78.0 + hash01(id ^ 0x03, cell_x, cell_y) * 92.0)
            * (0.86 + strength * 0.28);
        let tangent_x = angle.cos();
        let tangent_y = angle.sin();
        let normal_x = -tangent_y;
        let normal_y = tangent_x;
        let start_share = 0.34 + hash01(id ^ 0x11, cell_x, cell_y) * 0.24;
        let end_share = 1.0 - start_share;
        let bend = (hash01(id ^ LOBE_DOMAIN, cell_x, cell_y) - 0.5)
            * (36.0 + strength * 24.0);
        let along_knee = (hash01(id ^ 0x12, cell_x, cell_y) - 0.5) * length * 0.18;

        let start = RidgePoint {
            x: center_x - tangent_x * length * start_share,
            y: center_y - tangent_y * length * start_share,
        };
        let middle = RidgePoint {
            x: center_x + tangent_x * along_knee + normal_x * bend,
            y: center_y + tangent_y * along_knee + normal_y * bend,
        };
        let end = RidgePoint {
            x: center_x + tangent_x * length * end_share,
            y: center_y + tangent_y * length * end_share,
        };

        let base_width = (15.0 + hash01(id ^ 0x04, cell_x, cell_y) * 22.0)
            * (0.90 + strength * 0.28);
        let start_width = base_width * (0.50 + hash01(id ^ 0x13, cell_x, cell_y) * 0.48);
        let middle_width = base_width * (0.88 + hash01(id ^ 0x14, cell_x, cell_y) * 0.48);
        let end_width = base_width * (0.46 + hash01(id ^ 0x15, cell_x, cell_y) * 0.56);
        let outer = RidgeBand::new_tapered(
            start, middle, end, start_width, middle_width, end_width,
        );

        let branch_roll = unit_from_hash(id ^ 0x4252_414e_4348);
        let branch = if branch_roll < 0.64 {
            let side = if unit_from_hash(id ^ 0x5349_4445) < 0.5 { -1.0 } else { 1.0 };
            let branch_angle = angle
                + side * (0.62 + hash01(id ^ 0x16, cell_x, cell_y) * 0.72);
            let branch_length = 32.0 + hash01(id ^ 0x17, cell_x, cell_y) * 58.0;
            let branch_tangent = RidgePoint { x: branch_angle.cos(), y: branch_angle.sin() };
            let branch_start = point_toward(start, middle, 0.70);
            let branch_middle = RidgePoint {
                x: middle.x + branch_tangent.x * branch_length * 0.36,
                y: middle.y + branch_tangent.y * branch_length * 0.36,
            };
            let branch_end = RidgePoint {
                x: middle.x + branch_tangent.x * branch_length,
                y: middle.y + branch_tangent.y * branch_length,
            };
            Some(RidgeBand::new_tapered(
                branch_start,
                branch_middle,
                branch_end,
                base_width * 0.66,
                base_width * 0.52,
                base_width * 0.24,
            ))
        } else {
            None
        };

        let core_hash = hash2(seed ^ CORE_DOMAIN, cell_x, cell_y);
        let has_core = unit_from_hash(core_hash) < 0.58 + strength * 0.28;
        let core_scale = 0.50 + hash01(core_hash ^ 0x23, cell_x, cell_y) * 0.16;
        let core = RidgeBand::new_tapered(
            point_toward(start, middle, 0.38),
            RidgePoint {
                x: middle.x + normal_x * (hash01(core_hash ^ 0x21, cell_x, cell_y) - 0.5) * 10.0,
                y: middle.y + normal_y * (hash01(core_hash ^ 0x22, cell_x, cell_y) - 0.5) * 10.0,
            },
            point_toward(end, middle, 0.38),
            start_width * core_scale,
            middle_width * core_scale,
            end_width * core_scale,
        );
        let core_branch = if has_core && branch.is_some() && unit_from_hash(core_hash ^ 0x4342) < 0.36 {
            branch.map(|band| band.scaled_width(0.44))
        } else {
            None
        };

        Self { id, outer, branch, core, core_branch, has_core }
    }

    fn outer_depth(self, x: i32, y: i32) -> f64 {
        self.branch
            .map(|branch| self.outer.normalized_distance(x, y).min(branch.normalized_distance(x, y)))
            .unwrap_or_else(|| self.outer.normalized_distance(x, y))
    }

    fn core_depth(self, x: i32, y: i32) -> f64 {
        self.core_branch
            .map(|branch| self.core.normalized_distance(x, y).min(branch.normalized_distance(x, y)))
            .unwrap_or_else(|| self.core.normalized_distance(x, y))
    }

    fn contour_modulation(self, x: i32, y: i32, core: bool) -> f64 {
        // Low-frequency deterministic contour deformation prevents the rounded
        // endcaps of a distance-to-spine field from reading as repeated ovals.
        // Multiple wavelengths create coves/shoulders without producing noisy
        // one-tile cliff teeth or disconnecting the highland interior.
        let phase_a = unit_from_hash(self.id ^ 0x434f_4e54_4f55_5231)
            * std::f64::consts::TAU;
        let phase_b = unit_from_hash(self.id ^ 0x434f_4e54_4f55_5232)
            * std::f64::consts::TAU;
        let phase_c = unit_from_hash(self.id ^ 0x434f_4e54_4f55_5233)
            * std::f64::consts::TAU;
        let x = x as f64;
        let y = y as f64;
        let amplitude = if core { 0.075 } else { 0.12 };
        let wave = (x * 0.061 + phase_a).sin() * 0.52
            + (y * 0.047 + phase_b).sin() * 0.31
            + ((x + y) * 0.029 + phase_c).sin() * 0.17;
        (1.0 + wave * amplitude).clamp(0.82, 1.18)
    }
}

#[derive(Clone, Copy, Debug)]
struct RidgePoint {
    x: f64,
    y: f64,
}

#[derive(Clone, Copy, Debug)]
struct RidgeBand {
    start: RidgePoint,
    middle: RidgePoint,
    end: RidgePoint,
    start_half_width: f64,
    middle_half_width: f64,
    end_half_width: f64,
}

impl RidgeBand {
    fn new_tapered(
        start: RidgePoint,
        middle: RidgePoint,
        end: RidgePoint,
        start_half_width: f64,
        middle_half_width: f64,
        end_half_width: f64,
    ) -> Self {
        Self {
            start,
            middle,
            end,
            start_half_width: start_half_width.max(5.0),
            middle_half_width: middle_half_width.max(6.0),
            end_half_width: end_half_width.max(5.0),
        }
    }

    fn scaled_width(self, scale: f64) -> Self {
        Self::new_tapered(
            self.start,
            self.middle,
            self.end,
            self.start_half_width * scale,
            self.middle_half_width * scale,
            self.end_half_width * scale,
        )
    }

    fn normalized_distance(self, x: i32, y: i32) -> f64 {
        let point = RidgePoint { x: x as f64, y: y as f64 };
        let (first_distance, first_t) = distance_to_segment_with_t(point, self.start, self.middle);
        let (second_distance, second_t) = distance_to_segment_with_t(point, self.middle, self.end);
        let first_width = lerp(self.start_half_width, self.middle_half_width, first_t);
        let second_width = lerp(self.middle_half_width, self.end_half_width, second_t);
        (first_distance / first_width).min(second_distance / second_width)
    }
}

fn point_toward(from: RidgePoint, toward: RidgePoint, amount: f64) -> RidgePoint {
    RidgePoint {
        x: from.x + (toward.x - from.x) * amount,
        y: from.y + (toward.y - from.y) * amount,
    }
}

fn distance_to_segment_with_t(
    point: RidgePoint,
    start: RidgePoint,
    end: RidgePoint,
) -> (f64, f64) {
    let vx = end.x - start.x;
    let vy = end.y - start.y;
    let length_sq = vx * vx + vy * vy;
    if length_sq <= f64::EPSILON {
        return (
            ((point.x - start.x).powi(2) + (point.y - start.y).powi(2)).sqrt(),
            0.0,
        );
    }
    let t = (((point.x - start.x) * vx + (point.y - start.y) * vy) / length_sq)
        .clamp(0.0, 1.0);
    let closest_x = start.x + vx * t;
    let closest_y = start.y + vy * t;
    (
        ((point.x - closest_x).powi(2) + (point.y - closest_y).powi(2)).sqrt(),
        t,
    )
}

fn lerp(a: f64, b: f64, t: f64) -> f64 {
    a + (b - a) * t.clamp(0.0, 1.0)
}

#[derive(Clone, Copy, Debug)]
struct RotatedEllipse {
    center_x: f64,
    center_y: f64,
    radius_x: f64,
    radius_y: f64,
    cos_angle: f64,
    sin_angle: f64,
}

impl RotatedEllipse {
    fn new(center_x: f64, center_y: f64, radius_x: f64, radius_y: f64, angle: f64) -> Self {
        Self {
            center_x,
            center_y,
            radius_x: radius_x.max(8.0),
            radius_y: radius_y.max(8.0),
            cos_angle: angle.cos(),
            sin_angle: angle.sin(),
        }
    }

    fn normalized_distance(self, x: i32, y: i32) -> f64 {
        let dx = x as f64 - self.center_x;
        let dy = y as f64 - self.center_y;
        let local_x = dx * self.cos_angle + dy * self.sin_angle;
        let local_y = -dx * self.sin_angle + dy * self.cos_angle;
        let nx = local_x / self.radius_x;
        let ny = local_y / self.radius_y;
        nx * nx + ny * ny
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
    fn geographic_landforms_are_deterministic() {
        let a = sample_geographic_landform(77, 481, -209, 0.62);
        let b = sample_geographic_landform(77, 481, -209, 0.62);
        assert_eq!(a, b);
    }

    #[test]
    fn raised_cells_form_broad_neighborhoods_instead_of_single_cell_stripes() {
        let seed = 0x4841_5645_4e57_494c;
        let strength = 0.60;
        let mut raised = 0usize;
        let mut isolated = 0usize;
        for y in -256..256 {
            for x in -256..256 {
                if geographic_structural_level(seed, x, y, strength) == 0 {
                    continue;
                }
                raised += 1;
                let support = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                    .into_iter()
                    .filter(|(ox, oy)| {
                        geographic_structural_level(seed, x + *ox, y + *oy, strength) > 0
                    })
                    .count();
                isolated += usize::from(support == 0);
            }
        }
        assert!(raised > 0);
        assert_eq!(isolated, 0);
    }

    #[test]
    fn forest_habitat_forms_large_patches_with_open_ground() {
        let seed = 0x464f_5245_5354_5445;
        let mut woodland = 0usize;
        let mut open = 0usize;
        for y in -320..320 {
            for x in -320..320 {
                if geographic_forest_habitat(seed, x, y) > 0.30 {
                    woodland += 1;
                } else {
                    open += 1;
                }
            }
        }
        assert!(woodland > 0);
        assert!(open > woodland / 4);
    }
    #[test]
    fn ridge_features_use_tapered_or_branched_geometry() {
        let feature = BentRidgeFeature::from_macro_cell(0xAC20, 0, 0, 0.7);
        assert!(feature.outer.start_half_width != feature.outer.end_half_width
            || feature.branch.is_some());
    }

}
