use crate::asset_intake::AssetPromotionState;
use crate::category_metadata::TerrainMatchMode;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

pub const TERRAIN_VARIANT_DRAFT_SCHEMA: &str = "havenwild.terrain_variant_draft.v1";

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum TerrainDraftOrigin {
    BlankTile,
    DerivedVariant,
    AtlasSlice,
    TiledTerrainImport,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct TerrainVariantInheritance {
    pub semantic_identity: bool,
    pub terrain_pattern: bool,
    pub gameplay_properties: bool,
    pub provenance: bool,
    pub pcg_tags: bool,
}

impl Default for TerrainVariantInheritance {
    fn default() -> Self {
        Self {
            semantic_identity: true,
            terrain_pattern: true,
            gameplay_properties: true,
            provenance: true,
            pcg_tags: true,
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct TerrainTransformPolicy {
    #[serde(default)]
    pub allow_flip_horizontal: bool,
    #[serde(default)]
    pub allow_flip_vertical: bool,
    #[serde(default)]
    pub allow_rotate_90: bool,
    #[serde(default = "default_true")]
    pub prefer_untransformed: bool,
}

impl Default for TerrainTransformPolicy {
    fn default() -> Self {
        Self {
            allow_flip_horizontal: false,
            allow_flip_vertical: false,
            allow_rotate_90: false,
            prefer_untransformed: true,
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct TerrainVariantDraft {
    pub schema: String,
    pub draft_id: String,
    pub display_name: String,
    pub origin: TerrainDraftOrigin,
    #[serde(default)]
    pub parent_asset_id: Option<String>,
    pub semantic_terrain_id: String,
    pub terrain_set: String,
    pub match_mode: TerrainMatchMode,
    #[serde(default)]
    pub source_path: Option<String>,
    #[serde(default)]
    pub source_region: Option<[u32; 4]>,
    pub output_path: String,
    /// Relative automatic-selection weight. A value of zero deliberately keeps
    /// the variant topology-aware but manual-only, mirroring professional tile
    /// authoring tools without deleting its terrain metadata.
    pub weight: u16,
    pub promotion_state: AssetPromotionState,
    #[serde(default)]
    pub pcg_approved: bool,
    #[serde(default)]
    pub inheritance: TerrainVariantInheritance,
    #[serde(default)]
    pub transforms: TerrainTransformPolicy,
}

impl TerrainVariantDraft {
    pub fn blank_tile(
        draft_id: impl Into<String>,
        display_name: impl Into<String>,
        semantic_terrain_id: impl Into<String>,
        terrain_set: impl Into<String>,
        match_mode: TerrainMatchMode,
        output_path: impl Into<String>,
    ) -> Self {
        Self {
            schema: TERRAIN_VARIANT_DRAFT_SCHEMA.to_string(),
            draft_id: draft_id.into(),
            display_name: display_name.into(),
            origin: TerrainDraftOrigin::BlankTile,
            parent_asset_id: None,
            semantic_terrain_id: semantic_terrain_id.into(),
            terrain_set: terrain_set.into(),
            match_mode,
            source_path: None,
            source_region: None,
            output_path: output_path.into(),
            weight: 1,
            promotion_state: AssetPromotionState::Draft,
            pcg_approved: false,
            inheritance: TerrainVariantInheritance::default(),
            transforms: TerrainTransformPolicy::default(),
        }
    }

    #[allow(clippy::too_many_arguments)]
    pub fn derived_variant(
        draft_id: impl Into<String>,
        display_name: impl Into<String>,
        parent_asset_id: impl Into<String>,
        semantic_terrain_id: impl Into<String>,
        terrain_set: impl Into<String>,
        match_mode: TerrainMatchMode,
        source_path: impl Into<String>,
        source_region: [u32; 4],
        output_path: impl Into<String>,
    ) -> Self {
        Self {
            schema: TERRAIN_VARIANT_DRAFT_SCHEMA.to_string(),
            draft_id: draft_id.into(),
            display_name: display_name.into(),
            origin: TerrainDraftOrigin::DerivedVariant,
            parent_asset_id: Some(parent_asset_id.into()),
            semantic_terrain_id: semantic_terrain_id.into(),
            terrain_set: terrain_set.into(),
            match_mode,
            source_path: Some(source_path.into()),
            source_region: Some(source_region),
            output_path: output_path.into(),
            weight: 1,
            promotion_state: AssetPromotionState::Draft,
            pcg_approved: false,
            inheritance: TerrainVariantInheritance::default(),
            transforms: TerrainTransformPolicy::default(),
        }
    }

    pub fn automatic_enabled(&self) -> bool {
        self.weight > 0
    }

    pub fn validate(&self) -> Result<(), Vec<String>> {
        let mut errors = Vec::new();
        if self.schema != TERRAIN_VARIANT_DRAFT_SCHEMA {
            errors.push(format!("unsupported terrain variant draft schema {}", self.schema));
        }
        if self.draft_id.trim().is_empty() {
            errors.push("draft_id cannot be empty".to_string());
        }
        if self.display_name.trim().is_empty() {
            errors.push("display_name cannot be empty".to_string());
        }
        if self.semantic_terrain_id.trim().is_empty() || self.terrain_set.trim().is_empty() {
            errors.push("semantic terrain identity and terrain set are required".to_string());
        }
        let normalized_output = self.output_path.replace('\\', "/");
        if !normalized_output.starts_with("assets/source/original/") {
            errors.push("terrain drafts must publish to project-owned assets/source/original".to_string());
        }
        if self.origin == TerrainDraftOrigin::DerivedVariant {
            if self.parent_asset_id.as_deref().map_or(true, str::is_empty) {
                errors.push("derived terrain variants require parent_asset_id".to_string());
            }
            if self.source_path.as_deref().map_or(true, str::is_empty) || self.source_region.is_none() {
                errors.push("derived terrain variants require immutable source provenance".to_string());
            }
        }
        if self.pcg_approved && self.promotion_state != AssetPromotionState::Approved {
            errors.push("PCG approval requires an approved production asset".to_string());
        }
        if errors.is_empty() { Ok(()) } else { Err(errors) }
    }

    pub fn save(&self, path: impl AsRef<Path>) -> Result<(), String> {
        self.validate().map_err(|errors| errors.join("; "))?;
        let path = path.as_ref();
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)
                .map_err(|error| format!("failed to create {}: {error}", parent.display()))?;
        }
        let raw = serde_json::to_string_pretty(self)
            .map_err(|error| format!("failed to serialize terrain variant draft: {error}"))?;
        fs::write(path, format!("{raw}\n"))
            .map_err(|error| format!("failed to save {}: {error}", path.display()))
    }
}

fn default_true() -> bool { true }

#[cfg(test)]
mod tests {
    use super::*;

    fn derived(weight: u16) -> TerrainVariantDraft {
        let mut draft = TerrainVariantDraft::derived_variant(
            "grass_var_001",
            "Grass Variant 001",
            "terrain.grass",
            "Grass",
            "natural_ground",
            TerrainMatchMode::CornersAndSides,
            "WORKSPACE/source/terrain.png",
            [32, 64, 32, 32],
            "assets/source/original/pixel_studio/terrain_variants/grass_var_001.png",
        );
        draft.weight = weight;
        draft
    }

    #[test]
    fn derived_variant_inherits_semantic_and_gameplay_authority_by_default() {
        let draft = derived(1);
        assert!(draft.inheritance.semantic_identity);
        assert!(draft.inheritance.terrain_pattern);
        assert!(draft.inheritance.gameplay_properties);
        assert_eq!(draft.parent_asset_id.as_deref(), Some("terrain.grass"));
        assert!(draft.validate().is_ok());
    }

    #[test]
    fn zero_weight_is_topology_aware_manual_only() {
        let draft = derived(0);
        assert!(!draft.automatic_enabled());
        assert!(draft.validate().is_ok());
    }

    #[test]
    fn draft_cannot_claim_pcg_approval_before_production_promotion() {
        let mut draft = derived(1);
        draft.pcg_approved = true;
        assert!(draft.validate().is_err());
    }

    #[test]
    fn draft_output_must_be_project_owned() {
        let mut draft = derived(1);
        draft.output_path = "WORKSPACE/vendor/lpc/terrain.png".to_string();
        assert!(draft.validate().is_err());
    }
}
