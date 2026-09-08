#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum CachePersistence {
    RuntimeTransient,
    RebuildableSaveSidecar,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct RuntimeCacheOwnership {
    pub(crate) name: &'static str,
    pub(crate) owner: &'static str,
    pub(crate) persistence: CachePersistence,
    pub(crate) invalidated_by: &'static str,
}

/// Explicit inventory of retained caches that are allowed to survive across
/// frames. None of these are gameplay/world authority. The only disk-resident
/// entry is a rebuildable authoring sidecar derived from material state.
pub(crate) const RETAINED_CACHE_OWNERSHIP: &[RuntimeCacheOwnership] = &[
    RuntimeCacheOwnership {
        name: "base_terrain_chunk_cache",
        owner: "terrain/runtime presentation",
        persistence: CachePersistence::RuntimeTransient,
        invalidated_by: "scene or terrain revision",
    },
    RuntimeCacheOwnership {
        name: "visible_terrain_plan_cache",
        owner: "runtime presentation",
        persistence: CachePersistence::RuntimeTransient,
        invalidated_by: "camera tile bounds, scene, terrain or paint revision",
    },
    RuntimeCacheOwnership {
        name: "terrain_scene_surface_cache",
        owner: "terrain/runtime presentation",
        persistence: CachePersistence::RuntimeTransient,
        invalidated_by: "scene or terrain revision",
    },
    RuntimeCacheOwnership {
        name: "chunk_surface_descriptor_cache",
        owner: "runtime presentation",
        persistence: CachePersistence::RuntimeTransient,
        invalidated_by: "dirty base-terrain chunks",
    },
    RuntimeCacheOwnership {
        name: "scene_backdrop_height_cache",
        owner: "runtime presentation",
        persistence: CachePersistence::RuntimeTransient,
        invalidated_by: "scene or timed refresh",
    },
    RuntimeCacheOwnership {
        name: "stable_asset_source_cache",
        owner: "assets",
        persistence: CachePersistence::RuntimeTransient,
        invalidated_by: "asset-pack discovery/session rebuild",
    },
    RuntimeCacheOwnership {
        name: "stable_texture_cache",
        owner: "assets/runtime presentation",
        persistence: CachePersistence::RuntimeTransient,
        invalidated_by: "runtime asset session restart",
    },
    RuntimeCacheOwnership {
        name: "world_paint_render_cache",
        owner: "authoring/terrain presentation",
        persistence: CachePersistence::RebuildableSaveSidecar,
        invalidated_by: "world-paint material state or atlas manifest change",
    },
];

pub(crate) fn runtime_cache_ownership_summary() -> String {
    let transient = RETAINED_CACHE_OWNERSHIP
        .iter()
        .filter(|entry| entry.persistence == CachePersistence::RuntimeTransient)
        .count();
    let sidecars = RETAINED_CACHE_OWNERSHIP.len().saturating_sub(transient);
    format!(
        "Retained cache ownership: {} transient + {} rebuildable save sidecar; no cache is gameplay authority",
        transient, sidecars
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::BTreeSet;

    #[test]
    fn retained_cache_registry_is_unique_and_non_authoritative() {
        let names = RETAINED_CACHE_OWNERSHIP
            .iter()
            .map(|entry| entry.name)
            .collect::<BTreeSet<_>>();
        assert_eq!(names.len(), RETAINED_CACHE_OWNERSHIP.len());
        assert_eq!(
            RETAINED_CACHE_OWNERSHIP
                .iter()
                .filter(|entry| entry.persistence == CachePersistence::RebuildableSaveSidecar)
                .map(|entry| entry.name)
                .collect::<Vec<_>>(),
            vec!["world_paint_render_cache"]
        );
        assert!(RETAINED_CACHE_OWNERSHIP
            .iter()
            .all(|entry| !entry.owner.is_empty() && !entry.invalidated_by.is_empty()));
    }
}
