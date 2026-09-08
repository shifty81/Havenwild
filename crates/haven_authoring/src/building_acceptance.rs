use crate::{validate_building, BuildingValidationIssue};
use haven_core::{BuildingDefinition, BuildingSpace};
use haven_world::{generate_building_layout, BuildingGenerationRequest};

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct BuildingAcceptanceCase {
    pub name: &'static str,
    pub building: BuildingDefinition,
}

/// Canonical W55 acceptance set. Sizes are fixtures used to prove variability, not production constants.
pub fn canonical_building_acceptance_cases() -> Vec<BuildingAcceptanceCase> {
    [
        ("cottage", "residence", [7, 7], [6, 6], [11, 11], [9, 9], [1, 1]),
        ("residence", "residence", [11, 11], [8, 8], [14, 14], [12, 12], [2, 2]),
        ("shop", "shop", [9, 9], [7, 7], [13, 13], [10, 10], [1, 1]),
        ("workshop", "workshop", [12, 12], [8, 8], [15, 15], [11, 11], [1, 1]),
        ("tavern", "tavern", [15, 15], [10, 10], [21, 21], [16, 16], [1, 1]),
        ("inn", "inn", [16, 16], [11, 11], [22, 22], [18, 18], [2, 2]),
        ("mixed_use", "mixed_use", [12, 12], [9, 9], [16, 16], [13, 13], [2, 2]),
    ]
    .into_iter()
    .enumerate()
    .map(|(index, (name, archetype, ew, eh, iw, ih, floors))| BuildingAcceptanceCase {
        name,
        building: generate_building_layout(&BuildingGenerationRequest {
            instance_id: format!("acceptance.{name}.{:03}", index + 1),
            archetype: archetype.into(),
            seed: 0x55_09_0000 + index as u64,
            exterior_width: ew,
            exterior_height: eh,
            interior_width: iw,
            interior_height: ih,
            floors,
        })
        .expect("static building acceptance fixture must be valid"),
    })
    .collect()
}

pub fn validate_building_acceptance_case(case: &BuildingAcceptanceCase) -> Vec<BuildingValidationIssue> {
    validate_building(&case.building)
}

#[cfg(test)]
mod tests {
    use super::*;
    use haven_core::{BuildingRuntimeSceneRegistry, BuildingTravelSession};

    #[test]
    fn every_acceptance_archetype_uses_one_valid_layout_authority() {
        let cases = canonical_building_acceptance_cases();
        assert_eq!(cases.len(), 7);
        for case in cases {
            assert!(validate_building_acceptance_case(&case).is_empty(), "{} failed validation", case.name);
            assert!(case.building.layout.interior.width > case.building.layout.exterior.width);
            assert!(case.building.layout.interior.height > case.building.layout.exterior.height);
            assert_eq!(case.building.layout.exterior.floors as usize, case.building.layout.interior.floors.len());
        }
    }

    #[test]
    fn acceptance_cases_materialize_and_round_trip_through_generic_runtime_contracts() {
        for case in canonical_building_acceptance_cases() {
            let mut scenes = BuildingRuntimeSceneRegistry::default();
            let interior = scenes.get_or_materialize(&case.building, BuildingSpace::Interior, 0);
            assert_eq!(interior.dimensions.width as u32, case.building.layout.interior.width);
            assert_eq!(interior.dimensions.height as u32, case.building.layout.interior.height);

            let mut travel = BuildingTravelSession::default();
            let destination = travel.enter(&case.building, "entrance.main").unwrap();
            assert_eq!(destination.space, BuildingSpace::Interior);
            let returned = travel.exit_to_origin().unwrap();
            assert_eq!(returned.scene.space, BuildingSpace::Exterior);
        }
    }

    #[test]
    fn multi_floor_cases_expose_generic_stair_transitions() {
        for case in canonical_building_acceptance_cases().into_iter().filter(|c| c.building.layout.exterior.floors > 1) {
            assert!(case.building.layout.transitions.iter().any(|t| t.id.starts_with("stairs.")), "{} missing stairs", case.name);
        }
    }
}
