use std::collections::BTreeMap;

use haven_assets::asset_pack::StableAssetRef;

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub(crate) enum RenderTextureRole {
    BaseTerrain,
    TerrainTransition,
    MappedTerrain,
    LiveAutotile,
    RuntimeObjects,
    WorldPaintCompatibility,
    PlayerWalk,
}

#[derive(Clone, Debug)]
pub(crate) struct StableRenderBinding {
    pub semantic_id: String,
    pub stable_ref: Option<StableAssetRef>,
    pub legacy_fallback: bool,
}

#[derive(Default)]
pub(crate) struct StableRenderBindingRegistry {
    bindings: BTreeMap<RenderTextureRole, StableRenderBinding>,
}

impl StableRenderBindingRegistry {
    pub(crate) fn record(
        &mut self,
        role: RenderTextureRole,
        semantic_id: impl Into<String>,
        stable_ref: Option<StableAssetRef>,
    ) {
        self.bindings.insert(
            role,
            StableRenderBinding {
                semantic_id: semantic_id.into(),
                legacy_fallback: stable_ref.is_none(),
                stable_ref,
            },
        );
    }

    pub(crate) fn len(&self) -> usize {
        self.bindings.len()
    }

    pub(crate) fn fallback_count(&self) -> usize {
        self.bindings
            .values()
            .filter(|binding| binding.legacy_fallback)
            .count()
    }

    pub(crate) fn resolved_count(&self) -> usize {
        self.bindings
            .values()
            .filter(|binding| binding.stable_ref.is_some())
            .count()
    }

    pub(crate) fn semantic_ids(&self) -> impl Iterator<Item = &str> {
        self.bindings
            .values()
            .map(|binding| binding.semantic_id.as_str())
    }
}
