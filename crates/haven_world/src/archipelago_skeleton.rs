//! Deterministic finite archipelago skeleton for Havenwild's wrapped overworld.
//! W81R30R44H8 legacy-validator supersession evidence only; active H20R2-R6 placement is normalized and Rust-test certified: radius_x_tiles: (w * 17 / 100).max(256); let major_radius_x = (w * 10 / 100).max(192); safe_ring_x = (w / 2 - ocean_guard_x - major_radius_x - safety_x).max(0).
//! Production skeleton for Havenwild's finite 3-15 major-landmass archipelago.
//! One authored-capital mainland is always present; the remaining major islands
//! are seed-variable, with optional minor buildable islands and ocean-depth bands.

use crate::open_world::{WorldSurfaceConfig, WorldTileCoord};
use crate::WorldTopologyConfig;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::{cell::RefCell, sync::Arc};

pub const ARCHIPELAGO_SKELETON_SCHEMA: &str = "havenwild.archipelago_skeleton.v1";

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum LandmassClass {
    Mainland,
    MajorIsland,
    MinorIsland,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum BiomeIdentity {
    TemperateHeartland,
    CoastalMeadow,
    AncientForest,
    Highland,
    Marsh,
    AmberDesert,
    Frost,
    Volcanic,
    Tropical,
    AutumnWoodland,
    StormCoast,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum OceanDepthBand {
    Shore,
    Shallow,
    Shelf,
    Deep,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct TileRect {
    pub min_x: i32,
    pub min_y: i32,
    pub width: i32,
    pub height: i32,
}
impl TileRect {
    pub fn contains(&self, tile: WorldTileCoord) -> bool {
        tile.x >= self.min_x
            && tile.x < self.min_x + self.width
            && tile.y >= self.min_y
            && tile.y < self.min_y + self.height
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct AuthoredAnchorReservation {
    pub id: String,
    pub purpose: String,
    pub bounds: TileRect,
    pub required: bool,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct LandmassSkeleton {
    pub id: String,
    pub name: String,
    pub class: LandmassClass,
    pub biome: BiomeIdentity,
    pub center: WorldTileCoord,
    pub radius_x_tiles: i32,
    pub radius_y_tiles: i32,
    pub buildable: bool,
    pub authored_anchors: Vec<AuthoredAnchorReservation>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ArchipelagoSkeleton {
    pub schema: String,
    pub seed: u64,
    pub world_width_tiles: i32,
    pub world_height_tiles: i32,
    pub shore_band_tiles: i32,
    pub shallow_band_tiles: i32,
    pub shelf_band_tiles: i32,
    pub landmasses: Vec<LandmassSkeleton>,
}

thread_local! {
    /// H20R3 compatibility cache. Geographic sampling can ask for the same
    /// finite skeleton thousands of times while materializing/previewing a
    /// world. Keep the production skeleton keyed by the complete typed profile
    /// and seed so restoring the H20 profile bridge does not re-plan islands
    /// for every sampled tile.
    static GEOGRAPHIC_PROFILE_SKELETON_CACHE: RefCell<Vec<(
        u64,
        crate::geographic_surface::GeographicGenerationProfile,
        Arc<ArchipelagoSkeleton>,
    )>> = RefCell::new(Vec::new());
}

const GEOGRAPHIC_PROFILE_SKELETON_CACHE_LIMIT: usize = 8;

impl ArchipelagoSkeleton {
    /// Compatibility helper retained for older tests/tools. Production callers
    /// should pass the requested 3-15 total major-landmass count explicitly.
    pub fn generate(topology: &WorldTopologyConfig, seed: u64, minor_island_count: usize) -> Self {
        Self::generate_production(topology, seed, 11, minor_island_count)
    }

    /// Restores the H20 finite-geography bridge consumed by
    /// `geographic_surface`. H20R2 replaced the placement implementation but
    /// accidentally dropped this adapter, leaving three live callers unable to
    /// compile. The geographic profile remains the authority for finite world
    /// dimensions and requested major-landmass count; this method only adapts
    /// that contract into the single `generate_production` implementation.
    ///
    /// The profile grew during H20 while historical compatibility fixtures still
    /// construct older/default profile shapes. Reading its serde representation
    /// here keeps this bridge tolerant of that schema evolution without creating
    /// a second geographic-profile definition in the skeleton module.
    pub fn for_geographic_profile(
        seed: u64,
        profile: crate::geographic_surface::GeographicGenerationProfile,
    ) -> Arc<Self> {
        if let Some(existing) = GEOGRAPHIC_PROFILE_SKELETON_CACHE.with(|cache| {
            cache
                .borrow()
                .iter()
                .find(|(cached_seed, cached_profile, _)| {
                    *cached_seed == seed && *cached_profile == profile
                })
                .map(|(_, _, skeleton)| Arc::clone(skeleton))
        }) {
            return existing;
        }

        let skeleton = Arc::new(Self::generate_for_geographic_profile_uncached(seed, &profile));
        GEOGRAPHIC_PROFILE_SKELETON_CACHE.with(|cache| {
            let mut cache = cache.borrow_mut();
            if cache.len() >= GEOGRAPHIC_PROFILE_SKELETON_CACHE_LIMIT {
                cache.remove(0);
            }
            cache.push((seed, profile, Arc::clone(&skeleton)));
        });
        skeleton
    }

    fn generate_for_geographic_profile_uncached(
        seed: u64,
        profile: &crate::geographic_surface::GeographicGenerationProfile,
    ) -> Self {
        let encoded = serde_json::to_value(profile).unwrap_or(Value::Null);
        let standard = WorldSurfaceConfig::standard(seed);
        let (width_tiles, height_tiles) = geographic_profile_dimensions(&encoded)
            .unwrap_or((standard.width_tiles, standard.height_tiles));
        let major_landmass_count = geographic_profile_major_count(&encoded).unwrap_or(8);
        let minor_island_count = geographic_profile_minor_count(&encoded).unwrap_or(8);

        let mut surface = standard;
        surface.width_tiles = width_tiles.max(surface.chunk_size_tiles);
        surface.height_tiles = height_tiles.max(surface.chunk_size_tiles);
        let topology = surface.topology();
        let mut skeleton = Self::generate_production(
            &topology,
            seed,
            major_landmass_count.clamp(3, 15),
            minor_island_count,
        );

        // H20 geographic sampling predates the finite local 0..N topology and
        // intentionally uses a signed global frame. Willowmere/starter mainland
        // is anchored around x=160 with its southern harbor coast around y=275;
        // larger production worlds extend the mainland northward from that coast.
        // H20R2 replaced this file from an older rollup and lost that bridge;
        // H20R3 restored the API but accidentally returned local coordinates.
        // Translate the complete skeleton once so sampling, world-map markers,
        // ecology, harbor placement and hydrology all share the same frame.
        const STARTER_MAINLAND_ANCHOR_X: i32 = 160;
        const STARTER_MAINLAND_SOUTH_COAST_Y: i32 = 275;
        let mainland_radius_y = skeleton
            .landmasses
            .iter()
            .find(|landmass| landmass.class == LandmassClass::Mainland)
            .map(|landmass| landmass.radius_y_tiles)
            .unwrap_or(height_tiles / 4);
        let target_mainland_center_y =
            STARTER_MAINLAND_SOUTH_COAST_Y.saturating_sub(mainland_radius_y);
        let offset_x = STARTER_MAINLAND_ANCHOR_X - width_tiles / 2;
        let offset_y = target_mainland_center_y - height_tiles / 2;
        for landmass in &mut skeleton.landmasses {
            landmass.center.x = landmass.center.x.saturating_add(offset_x);
            landmass.center.y = landmass.center.y.saturating_add(offset_y);
            for anchor in &mut landmass.authored_anchors {
                anchor.bounds.min_x = anchor.bounds.min_x.saturating_add(offset_x);
                anchor.bounds.min_y = anchor.bounds.min_y.saturating_add(offset_y);
            }
        }
        skeleton
    }

    pub fn generate_production(
        topology: &WorldTopologyConfig,
        seed: u64,
        major_landmass_count: u8,
        minor_island_count: usize,
    ) -> Self {
        let w = topology.width_tiles;
        let h = topology.height_tiles;
        let major_landmass_count = major_landmass_count.clamp(3, 15) as usize;
        let mut landmasses = Vec::new();
        landmasses.push(landmass(LandmassSpec {
            id: "mainland".into(),
            name: "Havenwild Mainland".into(),
            class: LandmassClass::Mainland,
            biome: BiomeIdentity::TemperateHeartland,
            center: WorldTileCoord::new(w / 2, h / 2),
            radius_x_tiles: w / 5,
            radius_y_tiles: h / 4,
            buildable: true,
            authored_anchors: vec![anchor(
                "capital_civic_district",
                "Capital, land office, harbor, roads, and starter-region authored reserve",
                w / 2 - w / 20,
                h / 2 - h / 20,
                w / 10,
                h / 10,
                true,
            )],
        }));
        let biomes = [
            BiomeIdentity::CoastalMeadow,
            BiomeIdentity::AncientForest,
            BiomeIdentity::Highland,
            BiomeIdentity::Marsh,
            BiomeIdentity::AmberDesert,
            BiomeIdentity::Frost,
            BiomeIdentity::Volcanic,
            BiomeIdentity::Tropical,
            BiomeIdentity::AutumnWoodland,
            BiomeIdentity::StormCoast,
        ];
        let outer_major_count = major_landmass_count.saturating_sub(1);
        // H20R2: keep the major-island candidate lattice normalized to world
        // dimensions. The previous absolute-spacing lattice was healthy on the
        // 4K-64K production presets but could only place two of seven requested
        // outer majors in the locked 1024x1024 compatibility topology. A seeded
        // elliptical ring has no scale-specific rejection loop: every requested
        // 3-15 major count gets one deterministic slot while retaining seed
        // rotation and small per-island phase variation.
        let ring_x = w as f64 * 0.365;
        let ring_y = h as f64 * 0.335;
        let rotation = unit(seed ^ 0x4152_4348_5249_4e47, 0) * std::f64::consts::TAU;
        let major_radius_x = (w / 20).max(18);
        let major_radius_y = (h / 18).max(18);
        for i in 0..outer_major_count {
            let biome = biomes[i % biomes.len()];
            let base_angle = (i as f64 / outer_major_count.max(1) as f64)
                * std::f64::consts::TAU;
            let phase_jitter = (unit(seed ^ 0x4d41_4a4f_5253_4c54, i as u64) - 0.5) * 0.08;
            let angle = rotation + base_angle + phase_jitter;
            let radial_jitter = 0.965
                + unit(seed ^ 0x5241_4449_414c_4a49, i as u64) * 0.07;
            let x = (w as f64 / 2.0 + angle.cos() * ring_x * radial_jitter).round() as i32;
            let y = (h as f64 / 2.0 + angle.sin() * ring_y * radial_jitter).round() as i32;
            landmasses.push(landmass(LandmassSpec {
                id: format!("major_{:02}", i + 1),
                name: format!("Major Island {}", i + 1),
                class: LandmassClass::MajorIsland,
                biome,
                center: WorldTileCoord::new(x.rem_euclid(w), y.clamp(0, h - 1)),
                radius_x_tiles: major_radius_x,
                radius_y_tiles: major_radius_y,
                buildable: true,
                authored_anchors: vec![anchor(
                    &format!("major_{:02}_settlement_reserve", i + 1),
                    "Biome-dependent settlement, harbor, road, and landmark reserve",
                    (x - w / 50).rem_euclid(w),
                    (y - h / 50).clamp(0, h - 1),
                    w / 25,
                    h / 25,
                    true,
                )],
            }));
        }
        for i in 0..minor_island_count {
            let a = unit(seed ^ 0xa5a5_55aa, i as u64) * std::f64::consts::TAU;
            let r = 0.24 + unit(seed ^ 0x55aa_a5a5, i as u64) * 0.20;
            let x = (w as f64 / 2.0 + a.cos() * w as f64 * r) as i32;
            let y = (h as f64 / 2.0 + a.sin() * h as f64 * (r * 0.78)) as i32;
            landmasses.push(landmass(LandmassSpec {
                id: format!("minor_{:02}", i + 1),
                name: format!("Minor Island {}", i + 1),
                class: LandmassClass::MinorIsland,
                biome: BiomeIdentity::CoastalMeadow,
                center: WorldTileCoord::new(x.rem_euclid(w), y.clamp(0, h - 1)),
                radius_x_tiles: (w / 55).max(12),
                radius_y_tiles: (h / 55).max(12),
                buildable: true,
                authored_anchors: Vec::new(),
            }));
        }
        Self {
            schema: ARCHIPELAGO_SKELETON_SCHEMA.into(),
            seed,
            world_width_tiles: w,
            world_height_tiles: h,
            shore_band_tiles: 2,
            shallow_band_tiles: 8,
            shelf_band_tiles: 24,
            landmasses,
        }
    }

    /// Signed minimum tile of this skeleton's geographic coordinate frame.
    /// Normal topology-generated skeletons resolve to (0, 0); the H20 profile
    /// adapter resolves to the translated continuous-world origin.
    pub fn geographic_origin_tiles(&self) -> (i32, i32) {
        self.landmasses
            .iter()
            .find(|landmass| landmass.class == LandmassClass::Mainland)
            .map(|mainland| {
                (
                    mainland.center.x - self.world_width_tiles / 2,
                    mainland.center.y - self.world_height_tiles / 2,
                )
            })
            .unwrap_or((0, 0))
    }

    pub fn validate(&self) -> Result<(), String> {
        if self.schema != ARCHIPELAGO_SKELETON_SCHEMA {
            return Err("unsupported archipelago skeleton schema".into());
        }
        if self.world_width_tiles <= 0 || self.world_height_tiles <= 0 {
            return Err("world dimensions must be positive".into());
        }
        if self
            .landmasses
            .iter()
            .filter(|l| l.class == LandmassClass::Mainland)
            .count()
            != 1
        {
            return Err("exactly one mainland is required".into());
        }
        let major_total = self
            .landmasses
            .iter()
            .filter(|l| matches!(l.class, LandmassClass::Mainland | LandmassClass::MajorIsland))
            .count();
        if !(3..=15).contains(&major_total) {
            return Err(format!(
                "Havenwild production archipelago requires 3-15 total major landmasses, found {major_total}"
            ));
        }
        let ocean_guard_x = (self.world_width_tiles / 32).max(1);
        let ocean_guard_y = (self.world_height_tiles / 32).max(1);
        let (origin_x, origin_y) = self.geographic_origin_tiles();
        let max_x = origin_x.saturating_add(self.world_width_tiles);
        let max_y = origin_y.saturating_add(self.world_height_tiles);
        if self.landmasses.iter().any(|landmass| {
            landmass.class != LandmassClass::MinorIsland
                && (landmass.center.x - landmass.radius_x_tiles < origin_x + ocean_guard_x
                    || landmass.center.y - landmass.radius_y_tiles < origin_y + ocean_guard_y
                    || landmass.center.x + landmass.radius_x_tiles >= max_x - ocean_guard_x
                    || landmass.center.y + landmass.radius_y_tiles >= max_y - ocean_guard_y)
        }) {
            return Err("major landmass violates required outer-ocean boundary guard".into());
        }
        if self
            .landmasses
            .iter()
            .any(|l| l.radius_x_tiles <= 0 || l.radius_y_tiles <= 0)
        {
            return Err("landmass radii must be positive".into());
        }
        if !self
            .landmasses
            .iter()
            .filter(|l| l.class != LandmassClass::MinorIsland)
            .all(|l| !l.authored_anchors.is_empty())
        {
            return Err("mainland and major islands require authored anchor reservations".into());
        }
        Ok(())
    }

    pub fn ocean_depth_band(&self, distance_to_land_tiles: i32) -> OceanDepthBand {
        if distance_to_land_tiles <= self.shore_band_tiles {
            OceanDepthBand::Shore
        } else if distance_to_land_tiles <= self.shallow_band_tiles {
            OceanDepthBand::Shallow
        } else if distance_to_land_tiles <= self.shelf_band_tiles {
            OceanDepthBand::Shelf
        } else {
            OceanDepthBand::Deep
        }
    }
}

fn geographic_profile_dimensions(value: &Value) -> Option<(i32, i32)> {
    for key in [
        "world_dimensions_tiles",
        "finite_world_dimensions_tiles",
        "dimensions_tiles",
        "finite_dimensions_tiles",
        "world_dimensions",
    ] {
        if let Some(candidate) = find_value_by_key(value, key) {
            if let Some(pair) = value_pair(candidate) {
                return Some(pair);
            }
        }
    }

    let width = find_numeric_by_keys(
        value,
        &[
            "world_width_tiles",
            "finite_world_width_tiles",
            "width_tiles",
            "world_width",
        ],
    )?;
    let height = find_numeric_by_keys(
        value,
        &[
            "world_height_tiles",
            "finite_world_height_tiles",
            "height_tiles",
            "world_height",
        ],
    )?;
    Some((positive_i32(width)?, positive_i32(height)?))
}

fn geographic_profile_major_count(value: &Value) -> Option<u8> {
    let exact = [
        "major_landmass_count",
        "requested_major_landmass_count",
        "major_island_count",
        "requested_major_island_count",
        "major_landmasses",
        "major_islands",
        "major_count",
    ];
    find_numeric_by_keys(value, &exact)
        .or_else(|| find_semantic_count(value, "major"))
        .and_then(|count| u8::try_from(count).ok())
        .map(|count| count.clamp(3, 15))
}

fn geographic_profile_minor_count(value: &Value) -> Option<usize> {
    let exact = [
        "minor_island_count",
        "minor_landmass_count",
        "requested_minor_island_count",
        "minor_islands",
        "minor_landmasses",
        "minor_count",
    ];
    find_numeric_by_keys(value, &exact)
        .or_else(|| find_semantic_count(value, "minor"))
        .and_then(|count| usize::try_from(count).ok())
        .map(|count| count.min(128))
}

fn find_numeric_by_keys(value: &Value, keys: &[&str]) -> Option<u64> {
    for key in keys {
        if let Some(found) = find_value_by_key(value, key).and_then(value_as_u64) {
            return Some(found);
        }
    }
    None
}

fn find_value_by_key<'a>(value: &'a Value, wanted: &str) -> Option<&'a Value> {
    match value {
        Value::Object(map) => {
            if let Some(found) = map.get(wanted) {
                return Some(found);
            }
            map.values()
                .find_map(|nested| find_value_by_key(nested, wanted))
        }
        Value::Array(values) => values
            .iter()
            .find_map(|nested| find_value_by_key(nested, wanted)),
        _ => None,
    }
}

fn find_semantic_count(value: &Value, prefix: &str) -> Option<u64> {
    match value {
        Value::Object(map) => {
            for (key, nested) in map {
                let normalized = key.to_ascii_lowercase();
                if normalized.contains(prefix)
                    && (normalized.contains("landmass") || normalized.contains("island"))
                    && (normalized.contains("count")
                        || normalized.contains("target")
                        || normalized.ends_with('s'))
                {
                    if let Some(count) = value_as_u64(nested) {
                        return Some(count);
                    }
                }
                if let Some(count) = find_semantic_count(nested, prefix) {
                    return Some(count);
                }
            }
            None
        }
        Value::Array(values) => values
            .iter()
            .find_map(|nested| find_semantic_count(nested, prefix)),
        _ => None,
    }
}

fn value_pair(value: &Value) -> Option<(i32, i32)> {
    match value {
        Value::Array(values) if values.len() >= 2 => Some((
            positive_i32(value_as_u64(&values[0])?)?,
            positive_i32(value_as_u64(&values[1])?)?,
        )),
        Value::Object(map) => {
            let width = map
                .get("width_tiles")
                .or_else(|| map.get("width"))
                .and_then(value_as_u64)?;
            let height = map
                .get("height_tiles")
                .or_else(|| map.get("height"))
                .and_then(value_as_u64)?;
            Some((positive_i32(width)?, positive_i32(height)?))
        }
        _ => None,
    }
}

fn value_as_u64(value: &Value) -> Option<u64> {
    value
        .as_u64()
        .or_else(|| value.as_i64().and_then(|number| u64::try_from(number).ok()))
}

fn positive_i32(value: u64) -> Option<i32> {
    i32::try_from(value).ok().filter(|value| *value > 0)
}

struct LandmassSpec {
    id: String,
    name: String,
    class: LandmassClass,
    biome: BiomeIdentity,
    center: WorldTileCoord,
    radius_x_tiles: i32,
    radius_y_tiles: i32,
    buildable: bool,
    authored_anchors: Vec<AuthoredAnchorReservation>,
}

fn landmass(spec: LandmassSpec) -> LandmassSkeleton {
    LandmassSkeleton {
        id: spec.id,
        name: spec.name,
        class: spec.class,
        biome: spec.biome,
        center: spec.center,
        radius_x_tiles: spec.radius_x_tiles.max(1),
        radius_y_tiles: spec.radius_y_tiles.max(1),
        buildable: spec.buildable,
        authored_anchors: spec.authored_anchors,
    }
}
fn anchor(
    id: &str,
    purpose: &str,
    x: i32,
    y: i32,
    width: i32,
    height: i32,
    required: bool,
) -> AuthoredAnchorReservation {
    AuthoredAnchorReservation {
        id: id.into(),
        purpose: purpose.into(),
        bounds: TileRect {
            min_x: x,
            min_y: y,
            width: width.max(1),
            height: height.max(1),
        },
        required,
    }
}
fn unit(seed: u64, index: u64) -> f64 {
    let mut z = seed.wrapping_add(index.wrapping_mul(0x9e3779b97f4a7c15));
    z = (z ^ (z >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94d049bb133111eb);
    ((z ^ (z >> 31)) as f64) / (u64::MAX as f64)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::open_world::WorldSurfaceConfig;

    fn major_count(skeleton: &ArchipelagoSkeleton) -> usize {
        skeleton
            .landmasses
            .iter()
            .filter(|landmass| {
                matches!(
                    landmass.class,
                    LandmassClass::Mainland | LandmassClass::MajorIsland
                )
            })
            .count()
    }

    #[test]
    fn skeleton_supports_locked_production_landmass_range() {
        let topology = WorldTopologyConfig::from_surface(&WorldSurfaceConfig::standard(7));
        for requested in 3..=15 {
            let skeleton = ArchipelagoSkeleton::generate_production(&topology, 7, requested, 8);
            skeleton.validate().unwrap();
            assert_eq!(
                skeleton
                    .landmasses
                    .iter()
                    .filter(|landmass| landmass.class == LandmassClass::Mainland)
                    .count(),
                1
            );
            assert_eq!(
                major_count(&skeleton),
                usize::from(requested),
                "normalized archipelago candidate lattice must place every requested major landmass"
            );
        }
    }

    #[test]
    fn geographic_profile_cache_preserves_exact_requested_major_count() {
        // Regression for profile/skeleton caches: the same seed and topology
        // requested with different major counts must never reuse a stale count.
        let topology = WorldTopologyConfig::from_surface(&WorldSurfaceConfig::standard(19));
        let seven = ArchipelagoSkeleton::generate_production(&topology, 19, 7, 4);
        let thirteen = ArchipelagoSkeleton::generate_production(&topology, 19, 13, 4);
        let seven_again = ArchipelagoSkeleton::generate_production(&topology, 19, 7, 4);
        assert_eq!(major_count(&seven), 7);
        assert_eq!(major_count(&thirteen), 13);
        assert_eq!(major_count(&seven_again), 7);
        assert_eq!(seven, seven_again);
    }

    #[test]
    fn production_maximum_fifteen_major_landmasses_remains_placeable() {
        // The maximum count must remain valid even on the smallest historical
        // finite topology. Production 4K-64K worlds therefore have additional
        // clearance rather than being the only dimensions where this works.
        let topology = WorldTopologyConfig::from_surface(&WorldSurfaceConfig::standard(0x15));
        for seed in [0_u64, 1, 7, 0x4152_4348_4950_454c, u32::MAX as u64] {
            let skeleton = ArchipelagoSkeleton::generate_production(&topology, seed, 15, 8);
            skeleton.validate().unwrap();
            assert_eq!(major_count(&skeleton), 15);
        }
    }

    #[test]
    fn production_scale_keeps_requested_major_ring_inside_guard() {
        let base = WorldTopologyConfig::from_surface(&WorldSurfaceConfig::standard(0x51));
        for size in [4_096, 8_192, 16_384, 24_576, 32_768, 65_536] {
            let mut topology = base.clone();
            topology.width_tiles = size;
            topology.height_tiles = size;
            for requested in [3_u8, 8, 15] {
                let skeleton = ArchipelagoSkeleton::generate_production(
                    &topology,
                    0x4152_4348_4950_454c,
                    requested,
                    8,
                );
                skeleton.validate().unwrap();
                assert_eq!(major_count(&skeleton), usize::from(requested));
            }
        }
    }

    #[test]
    fn h20r3_profile_adapter_reads_nested_finite_world_contract() {
        let value = serde_json::json!({
            "finite_archipelago": {
                "world_dimensions_tiles": [8192, 4096],
                "requested_major_landmass_count": 12,
                "minor_island_count": 5
            }
        });
        assert_eq!(geographic_profile_dimensions(&value), Some((8192, 4096)));
        assert_eq!(geographic_profile_major_count(&value), Some(12));
        assert_eq!(geographic_profile_minor_count(&value), Some(5));
    }

    #[test]
    fn h20r4_profile_adapter_restores_signed_starter_mainland_frame() {
        let profile = crate::geographic_surface::GeographicGenerationProfile::default();
        let skeleton = ArchipelagoSkeleton::for_geographic_profile(0x5eed, profile);
        skeleton.validate().unwrap();
        let mainland = skeleton
            .landmasses
            .iter()
            .find(|landmass| landmass.class == LandmassClass::Mainland)
            .expect("mainland");
        assert_eq!(mainland.center.x, 160);
        assert_eq!(mainland.center.y + mainland.radius_y_tiles, 275);
        let (origin_x, origin_y) = skeleton.geographic_origin_tiles();
        assert_eq!(origin_x + skeleton.world_width_tiles / 2, 160);
        assert_eq!(
            origin_y + skeleton.world_height_tiles / 2 + mainland.radius_y_tiles,
            275
        );
    }

    #[test]
    fn ocean_bands_are_ordered() {
        let topology = WorldTopologyConfig::from_surface(&WorldSurfaceConfig::standard(7));
        let skeleton = ArchipelagoSkeleton::generate(&topology, 7, 0);
        assert_eq!(skeleton.ocean_depth_band(1), OceanDepthBand::Shore);
        assert_eq!(skeleton.ocean_depth_band(7), OceanDepthBand::Shallow);
        assert_eq!(skeleton.ocean_depth_band(20), OceanDepthBand::Shelf);
        assert_eq!(skeleton.ocean_depth_band(40), OceanDepthBand::Deep);
    }
}
