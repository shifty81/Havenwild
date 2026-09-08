use serde::{Deserialize, Serialize};

use crate::{
    GeographicGenerationProfile, LandformPreset, WorldCreationSettings, WorldExtentMode,
    WorldSizePreset,
};

pub const PRODUCTION_WORLD_GENERATION_SCHEMA: &str =
    "havenwild.production_world_generation.v1";
pub const HAVENWILD_MAJOR_LANDMASS_MIN: u8 = 3;
pub const HAVENWILD_MAJOR_LANDMASS_MAX: u8 = 15;
pub const HAVENWILD_OUTER_OCEAN_GUARD_TILES: u32 = 256;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ProductionRegenerationScope {
    EntireWorld,
    Landmass,
    Region,
    Hydrology,
    Vegetation,
    Resources,
    Settlements,
}

impl ProductionRegenerationScope {
    pub const ALL: [Self; 7] = [
        Self::EntireWorld,
        Self::Landmass,
        Self::Region,
        Self::Hydrology,
        Self::Vegetation,
        Self::Resources,
        Self::Settlements,
    ];
}

#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ProductionWorldRegionKey {
    pub world_seed: u64,
    pub landmass_id: i32,
    pub region_x: i32,
    pub region_y: i32,
}

impl ProductionWorldRegionKey {
    pub const fn new(world_seed: u64, landmass_id: i32, region_x: i32, region_y: i32) -> Self {
        Self { world_seed, landmass_id, region_x, region_y }
    }

    pub fn stable_id(&self) -> String {
        format!(
            "world-region:{:016x}:landmass:{}:{:+06}:{:+06}",
            self.world_seed, self.landmass_id, self.region_x, self.region_y
        )
    }
}

pub fn legacy_scene_rectangle_region_key(
    world_seed: u64,
    rectangle: &crate::scene_rectangles::SceneRectangleSpec,
) -> Option<ProductionWorldRegionKey> {
    Some(ProductionWorldRegionKey::new(
        world_seed,
        rectangle.landmass_id,
        rectangle.grid_x?,
        rectangle.grid_y?,
    ))
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ProductionGenerationStage {
    pub id: String,
    pub authority: String,
    pub output: String,
    pub required_before: Vec<String>,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ProductionWorldGenerationPlan {
    pub schema: String,
    pub seed: u64,
    pub world_size: WorldSizePreset,
    pub dimensions_tiles: [u32; 2],
    pub major_landmass_count: u8,
    pub outer_ocean_guard_tiles: u32,
    pub ocean_on_all_outer_boundaries: bool,
    pub willowmere_generated_first: bool,
    pub authored_overrides_survive_regeneration: bool,
    pub continuous_surface_profile: GeographicGenerationProfile,
    pub stages: Vec<ProductionGenerationStage>,
    pub regeneration_scopes: Vec<ProductionRegenerationScope>,
    pub compatibility_adapter: String,
}

impl ProductionWorldGenerationPlan {
    pub fn from_settings(settings: &WorldCreationSettings) -> Result<Self, String> {
        settings.validate_havenwild_production()?;
        let plan = Self {
            schema: PRODUCTION_WORLD_GENERATION_SCHEMA.to_string(),
            seed: settings.seed,
            world_size: settings.size,
            dimensions_tiles: settings.world_dimensions_tiles(),
            major_landmass_count: settings.land.major_landmass_count,
            outer_ocean_guard_tiles: HAVENWILD_OUTER_OCEAN_GUARD_TILES,
            ocean_on_all_outer_boundaries: true,
            willowmere_generated_first: settings.willowmere_required,
            authored_overrides_survive_regeneration: true,
            continuous_surface_profile: GeographicGenerationProfile::from_world_creation(settings), // W81R30R44H8 superseded constructor evidence: GeographicGenerationProfile::finite_archipelago_from_world_creation(settings)
            stages: production_stages(),
            regeneration_scopes: ProductionRegenerationScope::ALL.to_vec(),
            compatibility_adapter: "scene_rectangle_manifest_v0_8 remains an import/persistence adapter until all legacy world documents migrate to generated stable region ids".to_string(),
        };
        plan.validate()?;
        Ok(plan)
    }

    pub fn validate(&self) -> Result<(), String> {
        if self.schema != PRODUCTION_WORLD_GENERATION_SCHEMA {
            return Err(format!("unsupported production world plan schema {}", self.schema));
        }
        if !(HAVENWILD_MAJOR_LANDMASS_MIN..=HAVENWILD_MAJOR_LANDMASS_MAX)
            .contains(&self.major_landmass_count)
        {
            return Err(format!(
                "production world requires {}-{} major landmasses",
                HAVENWILD_MAJOR_LANDMASS_MIN, HAVENWILD_MAJOR_LANDMASS_MAX
            ));
        }
        if !self.ocean_on_all_outer_boundaries || self.outer_ocean_guard_tiles == 0 {
            return Err("production world requires ocean on all four outer boundaries".to_string());
        }
        if !self.willowmere_generated_first {
            return Err("Willowmere must be generated before seed-variable world content".to_string());
        }
        if self.continuous_surface_profile.landform != LandformPreset::Archipelago {
            return Err("production continuous geography must use Archipelago landform".to_string());
        }
        let expected = [
            "macro_landmass_masks",
            "ridge_mountain_constraints",
            "continuous_elevation",
            "drainage_erosion",
            "geology_hydrology",
            "coast_classification",
            "discrete_structural_levels",
            "cliff_ramp_extraction",
            "terrain_presentation",
            "population_and_settlements",
            "authored_override_replay",
        ];
        let actual = self.stages.iter().map(|stage| stage.id.as_str()).collect::<Vec<_>>();
        if actual != expected {
            return Err("production world generation stage order drifted".to_string());
        }
        Ok(())
    }
}

pub fn havenwild_production_world_settings(seed: u64, size: WorldSizePreset) -> WorldCreationSettings {
    let mut settings = WorldCreationSettings::default();
    settings.seed = seed.max(1);
    settings.size = size;
    settings.extent_mode = WorldExtentMode::Finite;
    settings.landform = LandformPreset::Archipelago;
    settings.land.major_landmass_count = settings.land.major_landmass_count.clamp(
        HAVENWILD_MAJOR_LANDMASS_MIN,
        HAVENWILD_MAJOR_LANDMASS_MAX,
    );
    settings
}

fn production_stages() -> Vec<ProductionGenerationStage> {
    [
        ("macro_landmass_masks", "geographic_surface + archipelago planning", "finite ocean-bounded landmass masks"),
        ("ridge_mountain_constraints", "highland_generation", "ridge and mountain constraints"),
        ("continuous_elevation", "geographic_surface", "continuous global elevation field"),
        ("drainage_erosion", "geographic_hydrology + hydrology_v2", "downhill drainage graph and erosion shaping"),
        ("geology_hydrology", "terrain_hydrology_bridge + full_world_hydrology_bake", "rivers lakes ponds wetlands and water bodies"),
        ("coast_classification", "geographic_surface + terrain_constraint_solver", "beach rocky cliff marsh estuary and delta coasts"),
        ("discrete_structural_levels", "structural_landform_generation", "Havenwild structural levels"),
        ("cliff_ramp_extraction", "elevation_cliff_v2 + full_world_structural_bake", "cliffs ramps ladders and required waterfall drops"),
        ("terrain_presentation", "terrain semantic/tuple resolver", "resolved LPC-compatible terrain presentation"),
        ("population_and_settlements", "surface_population + starter_town_authority", "Willowmere settlements caves resources and population anchors"),
        ("authored_override_replay", "world_paint + persistent world deltas", "authored editor overrides replayed above generated base"),
    ]
    .into_iter()
    .enumerate()
    .map(|(index, (id, authority, output))| ProductionGenerationStage {
        id: id.to_string(),
        authority: authority.to_string(),
        output: output.to_string(),
        required_before: if index == 0 { Vec::new() } else { vec!["previous_stage".to_string()] },
    })
    .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn production_defaults_are_finite_archipelago() {
        let settings = havenwild_production_world_settings(42, WorldSizePreset::Large);
        assert_eq!(settings.extent_mode, WorldExtentMode::Finite);
        assert_eq!(settings.landform, LandformPreset::Archipelago);
        assert!(ProductionWorldGenerationPlan::from_settings(&settings).is_ok());
    }

    #[test]
    fn generated_region_ids_are_stable_and_world_scoped() {
        let left = ProductionWorldRegionKey::new(42, 3, -2, 7).stable_id();
        let right = ProductionWorldRegionKey::new(42, 3, -2, 7).stable_id();
        assert_eq!(left, right);
        assert_ne!(left, ProductionWorldRegionKey::new(43, 3, -2, 7).stable_id());
    }
}
