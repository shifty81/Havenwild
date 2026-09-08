use haven_core::{
    enter_building_runtime, exit_building_runtime, BuildingRuntimeSceneRegistry,
    BuildingTravelSession,
};
use serde::{Deserialize, Serialize};

pub const BUILDING_AUTHORITY_CERTIFICATION_SCHEMA: &str =
    "havenwild.building_authority_certification.v1";

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct BuildingAcceptanceResult {
    pub instance_id: String,
    pub archetype: String,
    pub exterior_dimensions: [u32; 2],
    pub interior_dimensions: [u32; 2],
    pub floor_count: usize,
    pub validation_pass: bool,
    pub runtime_round_trip_pass: bool,
    pub persistence_round_trip_pass: bool,
    pub editor_parity_pass: bool,
    #[serde(default)]
    pub failures: Vec<String>,
}

impl BuildingAcceptanceResult {
    pub fn passed(&self) -> bool {
        self.validation_pass
            && self.runtime_round_trip_pass
            && self.persistence_round_trip_pass
            && self.editor_parity_pass
            && self.failures.is_empty()
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct BuildingAuthorityCertification {
    pub schema: String,
    pub authority: String,
    pub results: Vec<BuildingAcceptanceResult>,
}

impl BuildingAuthorityCertification {
    pub fn passed(&self) -> bool {
        !self.results.is_empty() && self.results.iter().all(BuildingAcceptanceResult::passed)
    }

    pub fn status_lines(&self) -> Vec<String> {
        let mut lines = self
            .results
            .iter()
            .map(|result| {
                format!(
                    "{} [{}] exterior {}x{} interior {}x{} floors {}: {}",
                    result.instance_id,
                    result.archetype,
                    result.exterior_dimensions[0],
                    result.exterior_dimensions[1],
                    result.interior_dimensions[0],
                    result.interior_dimensions[1],
                    result.floor_count,
                    if result.passed() { "PASS" } else { "FAIL" },
                )
            })
            .collect::<Vec<_>>();
        lines.push(format!(
            "BUILDING AUTHORITY CERTIFICATION: {}",
            if self.passed() { "PASS" } else { "FAIL" }
        ));
        lines
    }
}

/// Runs one consolidated acceptance path across the canonical layout, runtime travel,
/// save round-trip, and editor read-model boundaries. The generated building is never
/// converted into a second PCG/runtime building type.
pub fn certify_w55_building_acceptance() -> BuildingAuthorityCertification {
    let results = haven_world::building_acceptance_requests()
        .into_iter()
        .map(|request| {
            let mut failures = Vec::new();
            let building = match haven_world::generate_building_layout(&request) {
                Ok(building) => building,
                Err(error) => {
                    return BuildingAcceptanceResult {
                        instance_id: request.instance_id,
                        archetype: request.archetype,
                        exterior_dimensions: [0, 0],
                        interior_dimensions: [0, 0],
                        floor_count: 0,
                        validation_pass: false,
                        runtime_round_trip_pass: false,
                        persistence_round_trip_pass: false,
                        editor_parity_pass: false,
                        failures: vec![error],
                    };
                }
            };

            let validation_issues = haven_authoring::validate_building(&building);
            let validation_pass = validation_issues.is_empty();
            failures.extend(
                validation_issues
                    .into_iter()
                    .map(|issue| format!("{}: {}", issue.code, issue.message)),
            );

            let mut travel = BuildingTravelSession::default();
            let mut scenes = BuildingRuntimeSceneRegistry::default();
            let runtime_round_trip_pass = match enter_building_runtime(
                &building,
                "entrance.main",
                &mut travel,
                &mut scenes,
            ) {
                Ok(entered) => {
                    let interior_matches = scenes
                        .get(&entered.building_scene)
                        .is_some_and(|scene| {
                            scene.width == building.layout.interior.width
                                && scene.height == building.layout.interior.height
                        });
                    match exit_building_runtime(&mut travel, &mut scenes, &building) {
                        Ok(exited) => {
                            interior_matches
                                && exited.building_scene.building == building.id
                                && exited.building_scene.floor == 0
                        }
                        Err(error) => {
                            failures.push(format!("runtime exit failed: {error}"));
                            false
                        }
                    }
                }
                Err(error) => {
                    failures.push(format!("runtime entry failed: {error}"));
                    false
                }
            };

            let save = haven_save::BuildingWorldStateFile {
                schema: haven_save::BUILDING_WORLD_STATE_SCHEMA.to_string(),
                buildings: vec![haven_save::BuildingSaveRecord {
                    building: building.clone(),
                    generation_seed: Some(request.seed),
                    mutable_state: Default::default(),
                }],
            };
            let persistence_round_trip_pass = save
                .to_pretty_json()
                .and_then(|json| haven_save::BuildingWorldStateFile::from_json(&json))
                .map(|restored| restored.buildings[0].building == building)
                .unwrap_or_else(|error| {
                    failures.push(error);
                    false
                });

            let inspector = haven_editor::inspect_building_layout(&building);
            let editor_parity_pass = inspector.exterior_dimensions
                == [building.layout.exterior.width, building.layout.exterior.height]
                && inspector.interior_dimensions
                    == [building.layout.interior.width, building.layout.interior.height]
                && inspector.floors.len() == building.layout.interior.floors.len()
                && inspector.validation_issues.is_empty();
            if !editor_parity_pass {
                failures.push("editor layout inspector diverged from canonical BuildingLayout".to_string());
            }

            BuildingAcceptanceResult {
                instance_id: building.id.as_str().to_string(),
                archetype: building.archetype.clone(),
                exterior_dimensions: [building.layout.exterior.width, building.layout.exterior.height],
                interior_dimensions: [building.layout.interior.width, building.layout.interior.height],
                floor_count: building.layout.interior.floors.len(),
                validation_pass,
                runtime_round_trip_pass,
                persistence_round_trip_pass,
                editor_parity_pass,
                failures,
            }
        })
        .collect();

    BuildingAuthorityCertification {
        schema: BUILDING_AUTHORITY_CERTIFICATION_SCHEMA.to_string(),
        authority: "BuildingLayout".to_string(),
        results,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn all_w55_acceptance_buildings_pass_consolidated_certification() {
        let report = certify_w55_building_acceptance();
        assert_eq!(report.results.len(), 7);
        assert!(report.passed(), "{}", report.status_lines().join("\n"));
    }
}
