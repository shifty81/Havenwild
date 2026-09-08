//! Persisted low-LOD authority for a finite Havenwild world.
//!
//! H20V2B1 separates world *planning* from partition materialization. New Game
//! resolves the complete finite archipelago, drainage network and semantic map
//! before play, then stores that compact truth under `worldgen/`. Streaming is
//! still free to materialize detailed 96x96 partitions on demand, but it is no
//! longer the first time the world is conceptually decided.

use crate::{
    drainage_features_for_bounds, sample_generated_surface_map_code_with_drainage,
    ArchipelagoSkeleton, DrainageFeature, GeographicGenerationProfile, LandmassClass,
};
use serde::{Deserialize, Serialize};
use std::{fs, path::Path};

pub const SEMANTIC_WORLD_BAKE_SCHEMA: &str = "havenwild.semantic_world_bake.v1";
pub const SEMANTIC_WORLD_BAKE_RELATIVE_PATH: &str = "worldgen/semantic_world_bake_v1.json";
pub const SEMANTIC_WORLD_BAKE_MAX_AXIS_CELLS: usize = 192;

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct SemanticWorldBakeLandmarkV1 {
    pub world_x: i32,
    pub world_y: i32,
    pub label: String,
    pub capital: bool,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct SemanticWorldBakeV1 {
    pub schema: String,
    pub seed: u64,
    pub profile: GeographicGenerationProfile,
    pub origin_x: i32,
    pub origin_y: i32,
    pub span_w: i32,
    pub span_h: i32,
    pub cols: usize,
    pub rows: usize,
    /// Production semantic map codes. These are the same numeric roles consumed
    /// by the development world map, including freshwater, cliffs and forests.
    pub cells: Vec<u8>,
    /// Globally planned drainage features for the complete finite world. This
    /// persists river/source/sink identities even when no detailed chunk is in
    /// memory yet and gives future cache/materialization stages one canonical
    /// feature graph to consume.
    pub drainage_features: Vec<DrainageFeature>,
    pub landmarks: Vec<SemanticWorldBakeLandmarkV1>,
}

impl SemanticWorldBakeV1 {
    pub fn validate(&self) -> Result<(), String> {
        if self.schema != SEMANTIC_WORLD_BAKE_SCHEMA {
            return Err(format!(
                "semantic world bake schema mismatch: expected {}, got {}",
                SEMANTIC_WORLD_BAKE_SCHEMA, self.schema
            ));
        }
        if !self.profile.finite_world {
            return Err("semantic world bake requires a finite-world profile".to_string());
        }
        if self.span_w <= 0 || self.span_h <= 0 || self.cols == 0 || self.rows == 0 {
            return Err("semantic world bake has invalid dimensions".to_string());
        }
        if self.cols > SEMANTIC_WORLD_BAKE_MAX_AXIS_CELLS
            || self.rows > SEMANTIC_WORLD_BAKE_MAX_AXIS_CELLS
        {
            return Err("semantic world bake exceeds the certified LOD dimensions".to_string());
        }
        let expected = self.cols.saturating_mul(self.rows);
        if self.cells.len() != expected {
            return Err(format!(
                "semantic world bake cell count mismatch: expected {expected}, got {}",
                self.cells.len()
            ));
        }
        Ok(())
    }

    pub fn matches(&self, seed: u64, profile: GeographicGenerationProfile) -> bool {
        self.seed == seed && self.profile == profile && self.validate().is_ok()
    }
}

/// Builds the complete low-LOD semantic authority for a finite world.
/// Endless worlds intentionally return `None`: they cannot be globally baked.
pub fn build_semantic_world_bake_v1(
    seed: u64,
    profile: GeographicGenerationProfile,
) -> Option<SemanticWorldBakeV1> {
    if !profile.finite_world {
        return None;
    }
    let skeleton = ArchipelagoSkeleton::for_geographic_profile(seed, profile);
    let (origin_x, origin_y) = skeleton.geographic_origin_tiles();
    let span_w = skeleton.world_width_tiles.max(1);
    let span_h = skeleton.world_height_tiles.max(1);
    let longest = span_w.max(span_h) as f32;
    let cols = ((span_w as f32 / longest) * SEMANTIC_WORLD_BAKE_MAX_AXIS_CELLS as f32)
        .round()
        .clamp(1.0, SEMANTIC_WORLD_BAKE_MAX_AXIS_CELLS as f32) as usize;
    let rows = ((span_h as f32 / longest) * SEMANTIC_WORLD_BAKE_MAX_AXIS_CELLS as f32)
        .round()
        .clamp(1.0, SEMANTIC_WORLD_BAKE_MAX_AXIS_CELLS as f32) as usize;

    let drainage_features = drainage_features_for_bounds(
        seed,
        origin_x,
        origin_y,
        origin_x + span_w - 1,
        origin_y + span_h - 1,
        profile,
    );
    let mut cells = Vec::with_capacity(cols.saturating_mul(rows));
    for row in 0..rows {
        let sample_y = origin_y
            + (((row as f64 + 0.5) * span_h as f64 / rows as f64).floor() as i32)
                .clamp(0, span_h - 1);
        for col in 0..cols {
            let sample_x = origin_x
                + (((col as f64 + 0.5) * span_w as f64 / cols as f64).floor() as i32)
                    .clamp(0, span_w - 1);
            cells.push(sample_generated_surface_map_code_with_drainage(
                seed,
                sample_x,
                sample_y,
                profile,
                &drainage_features,
            ));
        }
    }

    let landmarks = skeleton
        .landmasses
        .iter()
        .filter(|landmass| {
            matches!(landmass.class, LandmassClass::Mainland | LandmassClass::MajorIsland)
        })
        .map(|landmass| SemanticWorldBakeLandmarkV1 {
            world_x: landmass.center.x,
            world_y: landmass.center.y,
            label: landmass.name.clone(),
            capital: landmass.class == LandmassClass::Mainland,
        })
        .collect();

    let bake = SemanticWorldBakeV1 {
        schema: SEMANTIC_WORLD_BAKE_SCHEMA.to_string(),
        seed,
        profile,
        origin_x,
        origin_y,
        span_w,
        span_h,
        cols,
        rows,
        cells,
        drainage_features,
        landmarks,
    };
    bake.validate().ok()?;
    Some(bake)
}

pub fn save_semantic_world_bake_v1_to_path(
    path: impl AsRef<Path>,
    bake: &SemanticWorldBakeV1,
) -> Result<(), String> {
    bake.validate()?;
    let path = path.as_ref();
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|error| error.to_string())?;
    }
    let bytes = serde_json::to_vec_pretty(bake).map_err(|error| error.to_string())?;
    fs::write(path, bytes).map_err(|error| error.to_string())
}

pub fn load_semantic_world_bake_v1_from_path(
    path: impl AsRef<Path>,
) -> Result<SemanticWorldBakeV1, String> {
    let bytes = fs::read(path.as_ref()).map_err(|error| error.to_string())?;
    let bake: SemanticWorldBakeV1 =
        serde_json::from_slice(&bytes).map_err(|error| error.to_string())?;
    bake.validate()?;
    Ok(bake)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn finite_bake_is_complete_and_seed_stable() {
        let profile = GeographicGenerationProfile {
            finite_world_dimensions_tiles: [2_048, 1_536],
            major_landmass_count: 3,
            minor_island_count: 1,
            ..Default::default()
        };
        let a = build_semantic_world_bake_v1(0x20b1, profile).expect("finite bake");
        let b = build_semantic_world_bake_v1(0x20b1, profile).expect("finite bake");
        assert_eq!(a, b);
        assert_eq!(a.cells.len(), a.cols * a.rows);
        assert!(!a.drainage_features.is_empty() || a.cells.iter().any(|code| *code != 0));
    }

    #[test]
    fn endless_world_does_not_claim_global_bake() {
        let profile = GeographicGenerationProfile {
            finite_world: false,
            ..Default::default()
        };
        assert!(build_semantic_world_bake_v1(7, profile).is_none());
    }
}
