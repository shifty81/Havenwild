use super::*;
use haven_world::open_world::{ChunkCoord, WorldTileCoord};
use haven_world::{
    generate_streamed_surface_chunk_with_profile,
    generate_streamed_surface_pcg_partition_with_profile,
    parse_generated_chunk_scene_id, parse_pcg_surface_scene_id, reconcile_chunk_hydrology_v2,
    ChunkHydrologyWindowV2, GeographicGenerationProfile, HydrologySettingsV2,
    SurfaceResidencyWindow,
};
use std::collections::{BTreeMap, BTreeSet, VecDeque};

const SURFACE_MAINTENANCE_INTERVAL_SECONDS: f64 = 0.25;
// H21A14AB4: completed worker results must not monopolize a movement frame.
// Publish one partition at a time under a sub-millisecond target; preload
// distance provides enough headroom for the remaining queue to drain.
const SURFACE_PUBLISH_BUDGET_SECONDS: f64 = 0.00075;
const SURFACE_MAX_PUBLISH_PER_FRAME: usize = 1;

#[derive(Clone, Debug, PartialEq, Eq)]
pub(crate) struct SurfaceCellTarget {
    pub scene_id: haven_core::ProjectSceneId,
    pub chunk: ChunkCoord,
    pub local_x: i32,
    pub local_y: i32,
    pub global_x: i32,
    pub global_y: i32,
}

fn surface_maintenance_due(now: f64, next_maintenance_at: f64, active_changed: bool) -> bool {
    active_changed || now >= next_maintenance_at
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct HydrologyResidencySignature {
    active_x: i32,
    active_y: i32,
    preload_count: usize,
    loaded_count: usize,
}

// Pass167Z109W81R30R44H7-H20S-R1: the residency/structural coordinators use
// dedicated background prepare, persistence, hydrology, and structural workers.
// Keep those worker contracts in this parent module so the included coordinator
// units share the same private runtime types without falling back to the older
// synchronous haven_world::SurfaceChunkJobQueue contract.
include!("runtime_surface_streaming_workers.rs");

pub(crate) struct SurfaceChunkRuntime {
    jobs: SurfacePrepareQueue,
    persistence: SurfacePersistenceQueue,
    hydrology_jobs: HydrologyJobQueue,
    structural_jobs: StructuralJobQueue,
    cache_writes: u64,
    delta_writes: u64,
    hydrology_reconciles: u64,
    structural_rebuilds: u64,
    streaming_generation: u64,
    latest_hydrology_token: u64,
    latest_structural_token: u64,
    last_stream_cost_ms: f64,
    // H20V2B4: worker completion is not the same as frame-safe publication.
    // Hydrology maps and structural caches are integrated a few partitions at
    // a time so a completed preload window cannot stall movement in one frame.
    pending_hydrology_publish: VecDeque<(ChunkCoord, haven_core::ProjectSceneId, haven_core::TavernMap)>,
    pending_structural_publish: VecDeque<haven_world::PartitionStructuralCacheV2>,
    pending_structural_levels_publish: VecDeque<(ChunkCoord, Vec<u8>)>,
    pending_structural_report: Option<haven_world::ElevationCliffResolveReportV2>,
    structural_rebuild_needed: bool,
    structural_cache: BTreeMap<String, haven_world::LegacyCliffBridgeResultV2>,
    // H20V1R8/H20S: authored LPC connector ramps are semantic structural
    // attachments. Cache complete world-space ownership once per structural
    // rebuild so render/collision never rediscover topology every frame.
    authored_ramp_owner_by_cell: BTreeMap<(i32, i32), (i32, i32)>,
    next_maintenance_at: f64,
    last_active_chunk: Option<(i32, i32)>,
    last_hydrology_signature: Option<HydrologyResidencySignature>,
    pinned_surface_scenes: BTreeSet<String>,
    pins_initialized: bool,
}

impl Default for SurfaceChunkRuntime {
    fn default() -> Self {
        Self {
            jobs: SurfacePrepareQueue::new(),
            persistence: SurfacePersistenceQueue::new(),
            hydrology_jobs: HydrologyJobQueue::new(),
            structural_jobs: StructuralJobQueue::new(),
            cache_writes: 0,
            delta_writes: 0,
            hydrology_reconciles: 0,
            structural_rebuilds: 0,
            streaming_generation: 0,
            latest_hydrology_token: 0,
            latest_structural_token: 0,
            last_stream_cost_ms: 0.0,
            pending_hydrology_publish: VecDeque::new(),
            pending_structural_publish: VecDeque::new(),
            pending_structural_levels_publish: VecDeque::new(),
            pending_structural_report: None,
            structural_rebuild_needed: false,
            structural_cache: BTreeMap::new(),
            authored_ramp_owner_by_cell: BTreeMap::new(),
            next_maintenance_at: 0.0,
            last_active_chunk: None,
            last_hydrology_signature: None,
            pinned_surface_scenes: BTreeSet::new(),
            pins_initialized: false,
        }
    }
}

// Pass167Z109Q: behavior-preserving source extraction. These files are
// included into this module so privacy and runtime behavior remain unchanged
// while the oversized coordinator is reduced to focused source units.
include!("runtime_surface_streaming_residency.rs");
include!("runtime_surface_streaming_structural.rs");
include!("runtime_surface_streaming_tests.rs");
