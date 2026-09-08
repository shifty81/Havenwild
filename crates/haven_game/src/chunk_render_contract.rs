use crate::base_terrain_cache::BaseTerrainCacheReport;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum ChunkRenderBackend {
    #[allow(dead_code)]
    PerTileFallback,
    #[allow(dead_code)]
    RetainedChunkSurface,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum ChunkSurfaceInvalidation {
    ColdStart,
    TerrainRevision,
    #[allow(dead_code)]
    CameraOnly,
    Stable,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct ChunkRenderCapability {
    pub backend: ChunkRenderBackend,
    pub retained_surface_supported: bool,
    pub fallback_available: bool,
}

impl Default for ChunkRenderCapability {
    fn default() -> Self {
        Self {
            backend: ChunkRenderBackend::RetainedChunkSurface,
            retained_surface_supported: true,
            fallback_available: true,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub(crate) struct ChunkSurfaceLifecycleReport {
    pub dirty_surfaces: usize,
    pub invalidation: Option<ChunkSurfaceInvalidation>,
}

impl ChunkSurfaceLifecycleReport {
    pub(crate) fn from_base_cache(report: BaseTerrainCacheReport, initialized: bool) -> Self {
        let invalidation = if !initialized && report.rebuilt_chunks > 0 {
            Some(ChunkSurfaceInvalidation::ColdStart)
        } else if report.rebuilt_chunks > 0 {
            Some(ChunkSurfaceInvalidation::TerrainRevision)
        } else {
            Some(ChunkSurfaceInvalidation::Stable)
        };
        Self {
            dirty_surfaces: report.rebuilt_chunks,
            invalidation,
        }
    }

    pub(crate) fn reason_label(self) -> &'static str {
        match self
            .invalidation
            .unwrap_or(ChunkSurfaceInvalidation::Stable)
        {
            ChunkSurfaceInvalidation::ColdStart => "cold-start",
            ChunkSurfaceInvalidation::TerrainRevision => "terrain-revision",
            ChunkSurfaceInvalidation::CameraOnly => "camera-only",
            ChunkSurfaceInvalidation::Stable => "stable",
        }
    }
}

impl ChunkRenderCapability {
    pub(crate) fn backend_label(self) -> &'static str {
        match self.backend {
            ChunkRenderBackend::PerTileFallback => "per-tile-fallback",
            ChunkRenderBackend::RetainedChunkSurface => "retained-chunk-surface",
        }
    }

    pub(crate) fn capability_label(self) -> &'static str {
        if self.retained_surface_supported {
            "retained-ready"
        } else {
            "descriptor-ready"
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_prefers_retained_surface_with_safe_fallback_available() {
        let capability = ChunkRenderCapability::default();
        assert_eq!(capability.backend, ChunkRenderBackend::RetainedChunkSurface);
        assert!(capability.fallback_available);
        assert!(capability.retained_surface_supported);
    }

    #[test]
    fn terrain_rebuild_invalidates_matching_chunk_surfaces() {
        let report = ChunkSurfaceLifecycleReport::from_base_cache(
            BaseTerrainCacheReport {
                rebuilt_chunks: 3,
                rebuilt_cells: 768,
            },
            true,
        );
        assert_eq!(report.dirty_surfaces, 3);
        assert_eq!(report.reason_label(), "terrain-revision");
    }
}
