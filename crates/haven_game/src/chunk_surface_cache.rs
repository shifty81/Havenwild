use crate::base_terrain_cache::{BaseTerrainChunkCache, BaseTerrainRecord};
use std::collections::{BTreeMap, BTreeSet};

fn retained_execution_requested_from_value(value: Option<&str>) -> bool {
    value.is_some_and(|value| {
        matches!(
            value.trim(),
            "1" | "true" | "TRUE" | "on" | "ON" | "yes" | "YES"
        )
    })
}

#[derive(Clone, Debug)]
pub(crate) struct ChunkSurfaceTileCommand {
    pub world_x: i32,
    pub world_y: i32,
    // Local coordinates are retained for the staged retained-surface backend.
    #[allow(dead_code)]
    pub local_x: u8,
    #[allow(dead_code)]
    pub local_y: u8,
    pub terrain: BaseTerrainRecord,
}

#[derive(Clone, Debug, Default)]
pub(crate) struct ChunkSurfaceCommandBuffer {
    #[allow(dead_code)]
    pub generation: u64,
    pub commands: Vec<ChunkSurfaceTileCommand>,
    pub ready: bool,
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub(crate) struct ChunkSurfaceCacheReport {
    pub prepared_surfaces: usize,
    pub reused_surfaces: usize,
    pub pending_surfaces: usize,
    pub total_surfaces: usize,
    pub prepared_commands: usize,
    pub retained_commands: usize,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct ChunkSurfaceExecutionReport {
    pub requested: bool,
    pub active: bool,
    pub visible_surfaces: usize,
    pub executed_commands: usize,
    pub fallback_count: u64,
    pub expected_commands: usize,
    pub parity_mismatches: u64,
    pub parity_ok: bool,
    pub unique_commands: usize,
    pub duplicate_commands: usize,
    pub missing_coordinates: usize,
    pub unexpected_coordinates: usize,
    pub reason: &'static str,
}

impl Default for ChunkSurfaceExecutionReport {
    fn default() -> Self {
        Self {
            requested: false,
            active: false,
            visible_surfaces: 0,
            executed_commands: 0,
            fallback_count: 0,
            expected_commands: 0,
            parity_mismatches: 0,
            parity_ok: true,
            unique_commands: 0,
            duplicate_commands: 0,
            missing_coordinates: 0,
            unexpected_coordinates: 0,
            reason: "not-requested",
        }
    }
}

#[derive(Debug)]
pub(crate) struct ChunkSurfaceDescriptorCache {
    buffers: BTreeMap<(i32, i32), ChunkSurfaceCommandBuffer>,
    generation: u64,
    retained_execution_requested: bool,
    fallback_count: u64,
    parity_mismatches: u64,
    last_report: ChunkSurfaceCacheReport,
    last_execution: ChunkSurfaceExecutionReport,
    validated_bounds: Option<(i32, i32, i32, i32)>,
    validated_generation: u64,
    validated_expected_commands: usize,
}

impl Default for ChunkSurfaceDescriptorCache {
    fn default() -> Self {
        // This cache currently retains CPU-side draw descriptors, not GPU
        // chunk textures. The old HAVENWILD_RETAINED_CHUNK_COMMANDS switch could
        // remain set on a developer machine and force a slower duplicate lane at
        // every zoom. Ignore that legacy switch; the CPU descriptor executor is
        // now available only through the explicitly experimental variable below
        // until the backend owns actual retained GPU surfaces.
        let retained_value =
            std::env::var("HAVENWILD_EXPERIMENTAL_CPU_RETAINED_CHUNK_COMMANDS").ok();
        let retained_execution_requested =
            retained_execution_requested_from_value(retained_value.as_deref());
        Self {
            buffers: BTreeMap::new(),
            generation: 0,
            retained_execution_requested,
            fallback_count: 0,
            parity_mismatches: 0,
            last_report: ChunkSurfaceCacheReport::default(),
            last_execution: ChunkSurfaceExecutionReport {
                requested: retained_execution_requested,
                ..ChunkSurfaceExecutionReport::default()
            },
            validated_bounds: None,
            validated_generation: 0,
            validated_expected_commands: 0,
        }
    }
}

impl ChunkSurfaceDescriptorCache {
    pub(crate) fn synchronize(
        &mut self,
        dirty_chunks: &[(i32, i32)],
        chunk_size: i32,
        map_width: usize,
        map_height: usize,
        base_cache: &BaseTerrainChunkCache,
    ) -> ChunkSurfaceCacheReport {
        self.generation = self
            .generation
            .saturating_add(u64::from(!dirty_chunks.is_empty()));
        if !dirty_chunks.is_empty() {
            self.validated_bounds = None;
        }
        let mut prepared_surfaces = 0;
        let mut prepared_commands = 0;
        for &(chunk_x, chunk_y) in dirty_chunks {
            let min_x = chunk_x * chunk_size;
            let min_y = chunk_y * chunk_size;
            let max_x = (min_x + chunk_size).min(map_width as i32);
            let max_y = (min_y + chunk_size).min(map_height as i32);
            let mut commands =
                Vec::with_capacity(((max_x - min_x).max(0) * (max_y - min_y).max(0)) as usize);
            for world_y in min_y..max_y {
                for world_x in min_x..max_x {
                    if let Some(record) = base_cache.record_at(world_x, world_y) {
                        commands.push(ChunkSurfaceTileCommand {
                            world_x,
                            world_y,
                            local_x: (world_x - min_x) as u8,
                            local_y: (world_y - min_y) as u8,
                            terrain: record.clone(),
                        });
                    }
                }
            }
            prepared_commands += commands.len();
            self.buffers.insert(
                (chunk_x, chunk_y),
                ChunkSurfaceCommandBuffer {
                    generation: self.generation,
                    commands,
                    ready: true,
                },
            );
            prepared_surfaces += 1;
        }
        let total_surfaces = self.buffers.len();
        let retained_commands = self
            .buffers
            .values()
            .map(|buffer| buffer.commands.len())
            .sum();
        self.last_report = ChunkSurfaceCacheReport {
            prepared_surfaces,
            reused_surfaces: total_surfaces.saturating_sub(prepared_surfaces),
            pending_surfaces: self.buffers.values().filter(|buffer| !buffer.ready).count(),
            total_surfaces,
            prepared_commands,
            retained_commands,
        };
        self.last_report
    }

    pub(crate) fn retained_execution_requested(&self) -> bool {
        self.retained_execution_requested
    }

    pub(crate) fn for_each_visible_command<'a>(
        &'a mut self,
        bounds: (i32, i32, i32, i32),
        chunk_size: i32,
        expected_coordinates: &[(i32, i32)],
        mut visit: impl FnMut(&'a ChunkSurfaceTileCommand),
    ) -> ChunkSurfaceExecutionReport {
        let mut report = ChunkSurfaceExecutionReport {
            requested: self.retained_execution_requested,
            fallback_count: self.fallback_count,
            expected_commands: expected_coordinates.len(),
            parity_mismatches: self.parity_mismatches,
            ..ChunkSurfaceExecutionReport::default()
        };
        if !self.retained_execution_requested {
            report.reason = "not-requested";
            self.last_execution = report;
            return report;
        }
        let (min_x, min_y, max_x, max_y) = bounds;
        let min_chunk_x = min_x.div_euclid(chunk_size);
        let min_chunk_y = min_y.div_euclid(chunk_size);
        let max_chunk_x = max_x.div_euclid(chunk_size);
        let max_chunk_y = max_y.div_euclid(chunk_size);
        for chunk_y in min_chunk_y..=max_chunk_y {
            for chunk_x in min_chunk_x..=max_chunk_x {
                let Some(buffer) = self.buffers.get(&(chunk_x, chunk_y)) else {
                    self.fallback_count = self.fallback_count.saturating_add(1);
                    report.fallback_count = self.fallback_count;
                    report.reason = "missing-surface";
                    self.last_execution = report;
                    return report;
                };
                if !buffer.ready {
                    self.fallback_count = self.fallback_count.saturating_add(1);
                    report.fallback_count = self.fallback_count;
                    report.reason = "surface-pending";
                    self.last_execution = report;
                    return report;
                }
            }
        }
        let parity_cache_hit = self.validated_bounds == Some(bounds)
            && self.validated_generation == self.generation
            && self.validated_expected_commands == expected_coordinates.len()
            && self.last_execution.parity_ok;
        if parity_cache_hit {
            report.unique_commands = expected_coordinates.len();
            report.reason = "retained-parity-cache-hit";
        } else {
            let expected_set: BTreeSet<(i32, i32)> = expected_coordinates.iter().copied().collect();
            let mut actual_set = BTreeSet::new();
            let mut visible_command_count = 0usize;
            let mut duplicate_commands = 0usize;
            for chunk_y in min_chunk_y..=max_chunk_y {
                for chunk_x in min_chunk_x..=max_chunk_x {
                    let buffer = &self.buffers[&(chunk_x, chunk_y)];
                    for command in &buffer.commands {
                        if command.world_x < min_x
                            || command.world_y < min_y
                            || command.world_x > max_x
                            || command.world_y > max_y
                        {
                            continue;
                        }
                        visible_command_count += 1;
                        if !actual_set.insert((command.world_x, command.world_y)) {
                            duplicate_commands += 1;
                        }
                    }
                }
            }
            let missing_coordinates = expected_set.difference(&actual_set).count();
            let unexpected_coordinates = actual_set.difference(&expected_set).count();
            report.unique_commands = actual_set.len();
            report.duplicate_commands = duplicate_commands;
            report.missing_coordinates = missing_coordinates;
            report.unexpected_coordinates = unexpected_coordinates;
            let parity_failed = visible_command_count != expected_coordinates.len()
                || expected_set.len() != expected_coordinates.len()
                || duplicate_commands != 0
                || missing_coordinates != 0
                || unexpected_coordinates != 0;
            if parity_failed {
                self.fallback_count = self.fallback_count.saturating_add(1);
                self.parity_mismatches = self.parity_mismatches.saturating_add(1);
                report.fallback_count = self.fallback_count;
                report.parity_mismatches = self.parity_mismatches;
                report.parity_ok = false;
                report.reason = if duplicate_commands != 0 {
                    "parity-duplicate-command"
                } else if missing_coordinates != 0 || unexpected_coordinates != 0 {
                    "parity-coordinate-mismatch"
                } else {
                    "parity-count-mismatch"
                };
                self.validated_bounds = None;
                self.last_execution = report;
                return report;
            }
            self.validated_bounds = Some(bounds);
            self.validated_generation = self.generation;
            self.validated_expected_commands = expected_coordinates.len();
            report.reason = "retained-command-parity";
        }
        report.active = true;
        report.parity_ok = true;
        for chunk_y in min_chunk_y..=max_chunk_y {
            for chunk_x in min_chunk_x..=max_chunk_x {
                let buffer = &self.buffers[&(chunk_x, chunk_y)];
                report.visible_surfaces += 1;
                for command in &buffer.commands {
                    if command.world_x < min_x
                        || command.world_y < min_y
                        || command.world_x > max_x
                        || command.world_y > max_y
                    {
                        continue;
                    }
                    report.executed_commands += 1;
                    visit(command);
                }
            }
        }
        self.last_execution = report;
        report
    }

    #[allow(dead_code)]
    pub(crate) fn command_buffer(&self, chunk: (i32, i32)) -> Option<&ChunkSurfaceCommandBuffer> {
        self.buffers.get(&chunk)
    }

    pub(crate) fn last_report(&self) -> ChunkSurfaceCacheReport {
        self.last_report
    }

    pub(crate) fn last_execution(&self) -> ChunkSurfaceExecutionReport {
        self.last_execution
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn retained_descriptor_execution_is_explicitly_opt_in() {
        assert!(!retained_execution_requested_from_value(None));
        assert!(!retained_execution_requested_from_value(Some("0")));
        assert!(!retained_execution_requested_from_value(Some("false")));
        assert!(retained_execution_requested_from_value(Some("1")));
        assert!(retained_execution_requested_from_value(Some("true")));
        assert!(retained_execution_requested_from_value(Some("on")));
    }
    use haven_core::{SceneBiome, SceneKind, SceneMap};
    use haven_world::autotile::LiveAutotileCache;

    fn synchronized_base_cache() -> BaseTerrainChunkCache {
        let scene = SceneMap::blank(
            "pass154f-test",
            "Pass 154F",
            SceneKind::Exterior,
            SceneBiome::Temperate,
        );
        let mut autotile = LiveAutotileCache::new(&scene);
        autotile.synchronize(&scene);
        let mut base = BaseTerrainChunkCache::default();
        base.synchronize(&scene.map, &autotile, scene.biome);
        base
    }

    #[test]
    fn dirty_chunks_prepare_render_ready_commands() {
        let base = synchronized_base_cache();
        let mut cache = ChunkSurfaceDescriptorCache::default();
        let first = cache.synchronize(&[(0, 0)], 16, 32, 16, &base);
        assert_eq!(first.prepared_surfaces, 1);
        assert_eq!(first.prepared_commands, 256);
        let buffer = cache.command_buffer((0, 0)).unwrap();
        assert!(buffer.ready);
        assert_eq!(buffer.commands[0].local_x, 0);
        assert_eq!(buffer.commands[0].local_y, 0);
    }

    #[test]
    fn stable_sync_reuses_existing_command_buffers() {
        let base = synchronized_base_cache();
        let mut cache = ChunkSurfaceDescriptorCache::default();
        cache.synchronize(&[(0, 0), (1, 0)], 16, 32, 16, &base);
        let second = cache.synchronize(&[], 16, 32, 16, &base);
        assert_eq!(second.prepared_surfaces, 0);
        assert_eq!(second.reused_surfaces, 2);
        assert_eq!(second.retained_commands, 512);
    }

    #[test]
    fn edge_chunk_uses_clipped_command_count() {
        let base = synchronized_base_cache();
        let mut cache = ChunkSurfaceDescriptorCache::default();
        cache.synchronize(&[(1, 0)], 16, 20, 10, &base);
        assert_eq!(cache.command_buffer((1, 0)).unwrap().commands.len(), 40);
    }
    #[test]
    fn missing_expected_coordinate_forces_safe_fallback() {
        let base = synchronized_base_cache();
        let mut cache = ChunkSurfaceDescriptorCache {
            retained_execution_requested: true,
            ..ChunkSurfaceDescriptorCache::default()
        };
        cache.synchronize(&[(0, 0)], 16, 16, 16, &base);
        let expected = (0..255)
            .map(|index| (index % 16, index / 16))
            .collect::<Vec<_>>();
        let report = cache.for_each_visible_command((0, 0, 15, 15), 16, &expected, |_| {});
        assert!(!report.active);
        assert!(!report.parity_ok);
        assert_eq!(report.reason, "parity-coordinate-mismatch");
        assert_eq!(report.parity_mismatches, 1);
    }

    #[test]
    fn matching_visible_command_count_activates_retained_lane() {
        let base = synchronized_base_cache();
        let mut cache = ChunkSurfaceDescriptorCache {
            retained_execution_requested: true,
            ..ChunkSurfaceDescriptorCache::default()
        };
        cache.synchronize(&[(0, 0)], 16, 16, 16, &base);
        let mut visited = 0;
        let report = cache.for_each_visible_command(
            (0, 0, 15, 15),
            16,
            &(0..16)
                .flat_map(|y| (0..16).map(move |x| (x, y)))
                .collect::<Vec<_>>(),
            |_| visited += 1,
        );
        assert!(report.active);
        assert!(report.parity_ok);
        assert_eq!(visited, 256);
        assert_eq!(report.reason, "retained-command-parity");
    }

    #[test]
    fn duplicate_coordinate_forces_safe_fallback_even_when_count_matches() {
        let base = synchronized_base_cache();
        let mut cache = ChunkSurfaceDescriptorCache {
            retained_execution_requested: true,
            ..ChunkSurfaceDescriptorCache::default()
        };
        cache.synchronize(&[(0, 0)], 16, 16, 16, &base);
        let buffer = cache.buffers.get_mut(&(0, 0)).unwrap();
        buffer.commands[255].world_x = 0;
        buffer.commands[255].world_y = 0;
        let expected = (0..16)
            .flat_map(|y| (0..16).map(move |x| (x, y)))
            .collect::<Vec<_>>();
        let report = cache.for_each_visible_command((0, 0, 15, 15), 16, &expected, |_| {});
        assert!(!report.active);
        assert_eq!(report.duplicate_commands, 1);
        assert_eq!(report.missing_coordinates, 1);
        assert_eq!(report.reason, "parity-duplicate-command");
    }

    #[test]
    fn shifted_coordinate_forces_coordinate_fallback() {
        let base = synchronized_base_cache();
        let mut cache = ChunkSurfaceDescriptorCache {
            retained_execution_requested: true,
            ..ChunkSurfaceDescriptorCache::default()
        };
        cache.synchronize(&[(0, 0)], 16, 16, 16, &base);
        let expected = (0..16)
            .flat_map(|y| (0..16).map(move |x| (x + 1, y)))
            .collect::<Vec<_>>();
        let report = cache.for_each_visible_command((0, 0, 15, 15), 16, &expected, |_| {});
        assert!(!report.active);
        assert_eq!(report.missing_coordinates, 16);
        assert_eq!(report.unexpected_coordinates, 16);
        assert_eq!(report.reason, "parity-coordinate-mismatch");
    }
}
