use crate::chunk_render_contract::{ChunkRenderCapability, ChunkSurfaceLifecycleReport};
use haven_assets::{
    authored_terrain_provider::resolve_authored_v7_surface_for_map,
    lpc_mapped_terrain::LpcMappedTerrainEntry,
};
use haven_core::{SceneBiome, TavernMap, TileAutoGroup, TileKind, MAP_H, MAP_W};
use haven_world::autotile::{
    resolve_terrain_transitions, LiveAutotileCache, ResolvedTerrainTransitions,
};
use haven_world::terrain_material::{TerrainMaterialId, TerrainShape};
use haven_world::resolve_surface_presentation_recipe_v1;
use std::collections::BTreeSet;

pub(crate) const BASE_TERRAIN_CHUNK_SIZE: i32 = 16;

#[derive(Clone, Debug)]
pub(crate) struct BaseTerrainRecord {
    pub tile: TileKind,
    pub resolved_group: Option<TileAutoGroup>,
    pub resolved_mask: u8,
    pub transitions: Option<ResolvedTerrainTransitions>,
    pub mapped_entry: Option<LpcMappedTerrainEntry>,
    pub mapped_transition_entry: Option<LpcMappedTerrainEntry>,
    // Retained by the staged chunk-mesh lane; consumed when that backend is activated.
    #[allow(dead_code)]
    pub shape: TerrainShape,
    #[allow(dead_code)]
    pub material: TerrainMaterialId,
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub(crate) struct BaseTerrainCacheReport {
    pub rebuilt_chunks: usize,
    pub rebuilt_cells: usize,
}

#[derive(Debug)]
pub(crate) struct BaseTerrainChunkCache {
    records: Vec<Option<BaseTerrainRecord>>,
    source_revision: u64,
    initialized: bool,
    last_report: BaseTerrainCacheReport,
    visible_bounds: Option<(i32, i32, i32, i32)>,
    visible_indices: Vec<(i32, i32, usize)>,
    visible_chunk_count: usize,
    visible_cache_hits: u64,
    visible_cache_rebuilds: u64,
    visible_cache_last_reason: &'static str,
    render_capability: ChunkRenderCapability,
    surface_lifecycle: ChunkSurfaceLifecycleReport,
    last_dirty_chunks: Vec<(i32, i32)>,
}

impl Default for BaseTerrainChunkCache {
    fn default() -> Self {
        Self {
            records: vec![None; MAP_W * MAP_H],
            source_revision: 0,
            initialized: false,
            last_report: BaseTerrainCacheReport::default(),
            visible_bounds: None,
            visible_indices: Vec::new(),
            visible_chunk_count: 0,
            visible_cache_hits: 0,
            visible_cache_rebuilds: 0,
            visible_cache_last_reason: "cold",
            render_capability: ChunkRenderCapability::default(),
            surface_lifecycle: ChunkSurfaceLifecycleReport::default(),
            last_dirty_chunks: Vec::new(),
        }
    }
}

pub(crate) fn affected_terrain_chunks(changed_cells: &[(i32, i32)]) -> BTreeSet<(i32, i32)> {
    let mut chunks = BTreeSet::new();
    for &(x, y) in changed_cells {
        // A corner tuple reads a 2x2 semantic neighborhood, so changing one
        // cell invalidates its complete 3x3 presentation neighborhood. This
        // also marks adjacent chunks when the edit lies on a chunk boundary.
        for ny in y - 1..=y + 1 {
            for nx in x - 1..=x + 1 {
                if nx < 0 || ny < 0 || nx >= MAP_W as i32 || ny >= MAP_H as i32 {
                    continue;
                }
                chunks.insert((
                    nx.div_euclid(BASE_TERRAIN_CHUNK_SIZE),
                    ny.div_euclid(BASE_TERRAIN_CHUNK_SIZE),
                ));
            }
        }
    }
    chunks
}

impl BaseTerrainChunkCache {
    pub fn synchronize(
        &mut self,
        map: &TavernMap,
        autotile: &LiveAutotileCache,
        biome: SceneBiome,
    ) -> BaseTerrainCacheReport {
        if self.initialized && self.source_revision == autotile.revision() {
            self.last_report = BaseTerrainCacheReport::default();
            self.last_dirty_chunks.clear();
            self.surface_lifecycle =
                ChunkSurfaceLifecycleReport::from_base_cache(self.last_report, self.initialized);
            return self.last_report;
        }

        let was_initialized = self.initialized;
        let mut dirty_chunks = if self.initialized {
            affected_terrain_chunks(autotile.last_dirty_cells())
        } else {
            BTreeSet::new()
        };
        if !self.initialized {
            let chunks_x = (MAP_W as i32 + BASE_TERRAIN_CHUNK_SIZE - 1) / BASE_TERRAIN_CHUNK_SIZE;
            let chunks_y = (MAP_H as i32 + BASE_TERRAIN_CHUNK_SIZE - 1) / BASE_TERRAIN_CHUNK_SIZE;
            for chunk_y in 0..chunks_y {
                for chunk_x in 0..chunks_x {
                    dirty_chunks.insert((chunk_x, chunk_y));
                }
            }
        }

        let mut rebuilt_cells = 0;
        for (chunk_x, chunk_y) in &dirty_chunks {
            let min_x = chunk_x * BASE_TERRAIN_CHUNK_SIZE;
            let min_y = chunk_y * BASE_TERRAIN_CHUNK_SIZE;
            let max_x = (min_x + BASE_TERRAIN_CHUNK_SIZE).min(MAP_W as i32);
            let max_y = (min_y + BASE_TERRAIN_CHUNK_SIZE).min(MAP_H as i32);
            for y in min_y..max_y {
                for x in min_x..max_x {
                    let slot = y as usize * MAP_W + x as usize;
                    let resolved = autotile.resolved_at(x, y);
                    // Grass, dirt, sand, farm, and mud-bank cells do not all
                    // participate in same-family autotiling, but they still own
                    // authored LPC boundaries. Preserve transitions for every
                    // terrain cell instead of dropping them when `resolved` is None.
                    let transitions = resolved
                        .map(|cell| cell.transitions.clone())
                        .unwrap_or_else(|| resolve_terrain_transitions(map, x, y));
                    let transitions = transitions.has_any().then_some(transitions);
                    let tile = map.get(x, y);
                    let resolved_group = resolved.map(|cell| cell.group);
                    let resolved_mask = resolved.map_or(0, |cell| cell.mask);
                    let presentation = resolve_surface_presentation_recipe_v1(
                        tile,
                        biome,
                        resolved_group,
                        resolved_mask,
                    );
                    let authored = resolve_authored_v7_surface_for_map(map, x, y);
                    self.records[slot] = Some(BaseTerrainRecord {
                        tile,
                        resolved_group,
                        resolved_mask,
                        transitions,
                        // terrain-map-v7 is a literal authored four-corner provider:
                        // semantics/topology select existing source cells; runtime does
                        // not synthesize terrain pixels or manufacture missing shapes.
                        mapped_entry: authored.base,
                        mapped_transition_entry: authored.transition,
                        shape: presentation.shape,
                        material: presentation.material,
                    });
                    rebuilt_cells += 1;
                }
            }
        }

        self.initialized = true;
        self.source_revision = autotile.revision();
        self.visible_bounds = None;
        self.visible_indices.clear();
        self.visible_chunk_count = 0;
        self.visible_cache_last_reason = "terrain-revision";
        self.last_dirty_chunks = dirty_chunks.iter().copied().collect();
        self.last_report = BaseTerrainCacheReport {
            rebuilt_chunks: self.last_dirty_chunks.len(),
            rebuilt_cells,
        };
        self.surface_lifecycle =
            ChunkSurfaceLifecycleReport::from_base_cache(self.last_report, was_initialized);
        self.last_report
    }

    pub fn record_at(&self, x: i32, y: i32) -> Option<&BaseTerrainRecord> {
        if x < 0 || y < 0 || x >= MAP_W as i32 || y >= MAP_H as i32 {
            return None;
        }
        self.records[y as usize * MAP_W + x as usize].as_ref()
    }

    pub fn for_each_visible_record<'a>(
        &'a mut self,
        bounds: (i32, i32, i32, i32),
        mut visit: impl FnMut(i32, i32, &'a BaseTerrainRecord),
    ) -> usize {
        if self.visible_bounds != Some(bounds) {
            self.visible_cache_rebuilds = self.visible_cache_rebuilds.saturating_add(1);
            self.visible_cache_last_reason = if self.visible_bounds.is_some() {
                "camera-bounds"
            } else {
                self.visible_cache_last_reason
            };
            self.rebuild_visible_indices(bounds);
        } else {
            self.visible_cache_hits = self.visible_cache_hits.saturating_add(1);
            self.visible_cache_last_reason = "hit";
        }
        for &(x, y, slot) in &self.visible_indices {
            if let Some(record) = self.records[slot].as_ref() {
                visit(x, y, record);
            }
        }
        self.visible_chunk_count
    }

    fn rebuild_visible_indices(&mut self, bounds: (i32, i32, i32, i32)) {
        self.visible_bounds = Some(bounds);
        self.visible_indices.clear();
        self.visible_chunk_count = 0;
        let (min_x, min_y, max_x, max_y) = bounds;
        if min_x > max_x || min_y > max_y {
            return;
        }
        let min_chunk_x = min_x.div_euclid(BASE_TERRAIN_CHUNK_SIZE);
        let min_chunk_y = min_y.div_euclid(BASE_TERRAIN_CHUNK_SIZE);
        let max_chunk_x = max_x.div_euclid(BASE_TERRAIN_CHUNK_SIZE);
        let max_chunk_y = max_y.div_euclid(BASE_TERRAIN_CHUNK_SIZE);
        for chunk_y in min_chunk_y..=max_chunk_y {
            for chunk_x in min_chunk_x..=max_chunk_x {
                self.visible_chunk_count += 1;
                let chunk_min_x = (chunk_x * BASE_TERRAIN_CHUNK_SIZE).max(min_x);
                let chunk_min_y = (chunk_y * BASE_TERRAIN_CHUNK_SIZE).max(min_y);
                let chunk_max_x = ((chunk_x + 1) * BASE_TERRAIN_CHUNK_SIZE - 1).min(max_x);
                let chunk_max_y = ((chunk_y + 1) * BASE_TERRAIN_CHUNK_SIZE - 1).min(max_y);
                for y in chunk_min_y..=chunk_max_y {
                    for x in chunk_min_x..=chunk_max_x {
                        if x < 0 || y < 0 || x >= MAP_W as i32 || y >= MAP_H as i32 {
                            continue;
                        }
                        let slot = y as usize * MAP_W + x as usize;
                        self.visible_indices.push((x, y, slot));
                    }
                }
            }
        }
    }

    pub fn visible_cache_hits(&self) -> u64 {
        self.visible_cache_hits
    }

    pub fn visible_cache_rebuilds(&self) -> u64 {
        self.visible_cache_rebuilds
    }

    pub fn visible_cache_last_reason(&self) -> &'static str {
        self.visible_cache_last_reason
    }

    pub fn visible_cached_cells(&self) -> usize {
        self.visible_indices.len()
    }

    pub fn retained_chunk_count(&self) -> usize {
        let chunks_x = (MAP_W as i32 + BASE_TERRAIN_CHUNK_SIZE - 1) / BASE_TERRAIN_CHUNK_SIZE;
        let chunks_y = (MAP_H as i32 + BASE_TERRAIN_CHUNK_SIZE - 1) / BASE_TERRAIN_CHUNK_SIZE;
        (chunks_x * chunks_y).max(0) as usize
    }

    // Kept for the retained-render diagnostics API that is not active by default yet.
    #[allow(dead_code)]
    pub fn last_report(&self) -> BaseTerrainCacheReport {
        self.last_report
    }

    pub fn render_capability(&self) -> ChunkRenderCapability {
        self.render_capability
    }

    pub fn surface_lifecycle_report(&self) -> ChunkSurfaceLifecycleReport {
        self.surface_lifecycle
    }

    pub fn last_dirty_chunks(&self) -> &[(i32, i32)] {
        &self.last_dirty_chunks
    }
}

#[cfg(test)]
mod pass161d_invalidation_tests {
    use super::*;

    #[test]
    fn edit_on_chunk_edge_invalidates_both_chunks() {
        let chunks = affected_terrain_chunks(&[(BASE_TERRAIN_CHUNK_SIZE - 1, 8)]);
        assert!(chunks.contains(&(0, 0)));
        assert!(chunks.contains(&(1, 0)));
    }

    #[test]
    fn edit_on_chunk_corner_invalidates_four_chunks() {
        let edge = BASE_TERRAIN_CHUNK_SIZE - 1;
        let chunks = affected_terrain_chunks(&[(edge, edge)]);
        assert!(chunks.contains(&(0, 0)));
        assert!(chunks.contains(&(1, 0)));
        assert!(chunks.contains(&(0, 1)));
        assert!(chunks.contains(&(1, 1)));
    }

    #[test]
    fn mixed_water_depth_cache_uses_owner_fill_and_keeps_rounded_overlay() {
        use haven_core::{SceneKind, SceneMap};

        let mut scene = SceneMap::blank(
            "mixed-water-depth-cache-test",
            "Mixed Water Depth Cache Test",
            SceneKind::Exterior,
            SceneBiome::Temperate,
        );
        for y in 4..=5 {
            scene.map.set(4, y, TileKind::DeepWater);
            scene.map.set(5, y, TileKind::ShallowWater);
        }

        let mut autotile = LiveAutotileCache::new(&scene);
        autotile.synchronize(&scene);
        let mut cache = BaseTerrainChunkCache::default();
        cache.synchronize(&scene.map, &autotile, scene.biome);

        let record = cache.record_at(4, 4).expect("deep-water cache record");
        assert!(
            record.mapped_entry.is_some_and(|entry| !entry.is_mixed),
            "mixed depth tuple must cache the owning pure-water fill"
        );
        assert!(
            record
                .transitions
                .as_ref()
                .is_some_and(ResolvedTerrainTransitions::has_any),
            "the dedicated shallow/deep LPC overlay must remain available"
        );
    }

    #[test]
    fn non_autotiled_grass_retains_road_boundary_transition() {
        use haven_core::{SceneKind, SceneMap};

        let mut scene = SceneMap::blank(
            "direct-lpc-boundary-test",
            "Direct LPC Boundary Test",
            SceneKind::Exterior,
            SceneBiome::Temperate,
        );
        scene.map.set(4, 4, TileKind::Grass);
        scene.map.set(5, 4, TileKind::Road);

        let mut autotile = LiveAutotileCache::new(&scene);
        autotile.synchronize(&scene);
        assert!(
            autotile.resolved_at(4, 4).is_none(),
            "grass intentionally has no same-family autotile group"
        );

        let mut cache = BaseTerrainChunkCache::default();
        cache.synchronize(&scene.map, &autotile, scene.biome);
        assert!(
            cache
                .record_at(4, 4)
                .and_then(|record| record.transitions.as_ref())
                .is_some_and(ResolvedTerrainTransitions::has_any),
            "grass-owned LPC road fringe must survive the base cache"
        );
    }
}
