use super::*;
use haven_assets::building_instance::{
    BuildingInstanceDefinition, BuildingInstanceOrigin, BuildingInstanceViewState, BuildingPlacementSpace,
    BUILDING_INSTANCE_SCHEMA,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub(crate) struct BuildingInstanceStateSnapshot {
    pub sequence: u64,
    pub world_id: String,
    pub instance_id: String,
    pub revision: u64,
    pub recipe_id: String,
    pub scene_id: String,
    pub initial_level: i32,
    pub origin: String,
    pub placement_space: String,
    pub authoritative_anchor_tile: [i32; 2],
    pub surface_region_id: Option<String>,
    pub removed: bool,
    pub opening_states: std::collections::BTreeMap<String, String>,
    pub furnishing_states: std::collections::BTreeMap<String, String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub(crate) struct BuildingInstanceStateEnvelope {
    pub snapshot: BuildingInstanceStateSnapshot,
    pub authority: String,
    pub reason: String,
}

impl BuildingInstanceStateEnvelope {
    fn host(snapshot: BuildingInstanceStateSnapshot, reason: &str) -> Self {
        Self {
            snapshot,
            authority: "host_authoritative".to_string(),
            reason: reason.to_string(),
        }
    }

    fn validate_for_client(&self, last_applied_sequence: u64) -> Result<(), String> {
        if self.authority != "host_authoritative" {
            return Err("BuildingInstance replication requires host authority".to_string());
        }
        if self.snapshot.sequence <= last_applied_sequence {
            return Err(format!(
                "stale BuildingInstance replication sequence {} <= {}",
                self.snapshot.sequence, last_applied_sequence
            ));
        }
        if self.snapshot.instance_id.trim().is_empty() || self.snapshot.world_id.trim().is_empty() {
            return Err("BuildingInstance replication identity is incomplete".to_string());
        }
        Ok(())
    }

    pub(crate) fn status_line(&self) -> String {
        format!(
            "BUILDING_REPLICATION seq={} instance={} revision={} reason={}",
            self.snapshot.sequence, self.snapshot.instance_id, self.snapshot.revision, self.reason
        )
    }
}

impl Game {
    pub(super) fn host_building_instance_state_envelope(
        &mut self,
        instance_id: &str,
        reason: &str,
    ) -> Result<BuildingInstanceStateEnvelope, String> {
        let definition = self
            .building_instance_registry
            .entry(instance_id)
            .cloned()
            .ok_or_else(|| format!("unknown BuildingInstance {instance_id}"))?;
        let persistent = self.building_instance_registry.persistent_state(instance_id);
        self.building_state_sequence = self.building_state_sequence.saturating_add(1);
        Ok(BuildingInstanceStateEnvelope::host(
            BuildingInstanceStateSnapshot {
                sequence: self.building_state_sequence,
                world_id: self.world_id.0.clone(),
                instance_id: definition.id.clone(),
                revision: persistent.map_or(0, |state| state.revision),
                recipe_id: definition.recipe_id.clone(),
                scene_id: definition.scene_id.clone(),
                initial_level: definition.initial_level,
                origin: building_origin_label(definition.origin).to_string(),
                placement_space: building_placement_label(definition.placement_space).to_string(),
                authoritative_anchor_tile: definition.authoritative_anchor_tile(),
                surface_region_id: definition.surface_region_id.clone(),
                removed: false,
                opening_states: persistent
                    .map(|state| state.opening_states.clone())
                    .unwrap_or_default(),
                furnishing_states: persistent
                    .map(|state| state.furnishing_states.clone())
                    .unwrap_or_default(),
            },
            reason,
        ))
    }

    /// Listen-server transport is not connected yet, but W46C owns the complete
    /// host->replica apply path so transport cannot invent a second building state
    /// model later. Camera-local floor/cutaway state is intentionally untouched.
    #[expect(dead_code, reason = "listen-server transport adapter is not connected yet")]
    pub(super) fn apply_replicated_building_instance_state(
        &mut self,
        envelope: &BuildingInstanceStateEnvelope,
    ) -> Result<(), String> {
        envelope.validate_for_client(self.last_applied_building_state_sequence)?;
        let snapshot = &envelope.snapshot;
        if snapshot.world_id != self.world_id.0 {
            return Err("building-instance state envelope targets another world".to_string());
        }

        if snapshot.removed {
            self.building_instance_registry
                .remove_world_instance(&snapshot.instance_id, &self.building_recipe_registry)?;
            self.building_instance_views.remove(&snapshot.instance_id);
        } else {
            let placement_space = match snapshot.placement_space.as_str() {
                "scene_local" => BuildingPlacementSpace::SceneLocal,
                "continuous_surface" => BuildingPlacementSpace::ContinuousSurface,
                other => return Err(format!("unsupported building placement space {other}")),
            };
            let origin = match snapshot.origin.as_str() {
                "authored" => BuildingInstanceOrigin::Authored,
                "worldgen" => BuildingInstanceOrigin::Worldgen,
                "player_built" => BuildingInstanceOrigin::PlayerBuilt,
                "diagnostic" => BuildingInstanceOrigin::Diagnostic,
                other => return Err(format!("unsupported building origin {other}")),
            };
            let existing = self.building_instance_registry.entry(&snapshot.instance_id).cloned();
            let anchor_tile = if placement_space == BuildingPlacementSpace::SceneLocal {
                snapshot.authoritative_anchor_tile
            } else {
                existing
                    .as_ref()
                    .map(|definition| definition.anchor_tile)
                    .unwrap_or(snapshot.authoritative_anchor_tile)
            };
            let definition = BuildingInstanceDefinition {
                schema: BUILDING_INSTANCE_SCHEMA.to_string(),
                id: snapshot.instance_id.clone(),
                recipe_id: snapshot.recipe_id.clone(),
                scene_id: snapshot.scene_id.clone(),
                anchor_tile,
                initial_level: snapshot.initial_level,
                diagnostic_only: origin == BuildingInstanceOrigin::Diagnostic,
                origin,
                placement_space,
                surface_region_id: snapshot.surface_region_id.clone(),
                global_anchor_tile: if placement_space == BuildingPlacementSpace::ContinuousSurface {
                    Some(snapshot.authoritative_anchor_tile)
                } else {
                    None
                },
            };
            self.building_instance_registry
                .upsert_world_instance(definition, &self.building_recipe_registry)?;
            let recipe = self
                .building_recipe_registry
                .entry(&snapshot.recipe_id)
                .cloned()
                .ok_or_else(|| format!("unknown replicated BuildingRecipe {}", snapshot.recipe_id))?;
            self.building_instance_registry.apply_replicated_opening_states(
                &snapshot.instance_id,
                &recipe,
                snapshot.revision,
                snapshot.opening_states.clone(),
            )?;
            self.building_instance_registry.apply_replicated_furnishing_states(
                &snapshot.instance_id,
                &recipe,
                snapshot.revision,
                snapshot.furnishing_states.clone(),
            )?;
            self.building_instance_views
                .entry(snapshot.instance_id.clone())
                .or_insert_with(|| BuildingInstanceViewState {
                    active_level: snapshot.initial_level,
                    inside: false,
                });
        }

        self.last_applied_building_state_sequence = snapshot.sequence;
        self.last_replication_status = format!(
            "Applied host BuildingInstance state seq {} ({})",
            snapshot.sequence, envelope.reason
        );
        self.refresh_building_instance_views();
        Ok(())
    }
}

fn building_origin_label(origin: BuildingInstanceOrigin) -> &'static str {
    match origin {
        BuildingInstanceOrigin::Authored => "authored",
        BuildingInstanceOrigin::Worldgen => "worldgen",
        BuildingInstanceOrigin::PlayerBuilt => "player_built",
        BuildingInstanceOrigin::Diagnostic => "diagnostic",
    }
}

fn building_placement_label(space: BuildingPlacementSpace) -> &'static str {
    match space {
        BuildingPlacementSpace::SceneLocal => "scene_local",
        BuildingPlacementSpace::ContinuousSurface => "continuous_surface",
    }
}
