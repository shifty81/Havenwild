use std::collections::BTreeSet as WorkerBTreeSet;
use std::sync::mpsc::{self, Receiver, Sender, TryRecvError};
use std::thread;

#[derive(Clone, Debug)]
struct SurfacePrepareRequest {
    world_seed: u64,
    chunk: ChunkCoord,
    profile: GeographicGenerationProfile,
    pcg_region: Option<String>,
    target_scene_id: haven_core::ProjectSceneId,
    chunks_root: String,
}

#[derive(Debug)]
struct SurfacePrepareResult {
    request: SurfacePrepareRequest,
    scene: haven_core::SceneMap,
    loaded_from_cache: bool,
    baseline_persisted: bool,
}

struct SurfacePrepareQueue {
    request_tx: Sender<SurfacePrepareRequest>,
    result_rx: Receiver<SurfacePrepareResult>,
    pending: WorkerBTreeSet<(i32, i32)>,
}

impl SurfacePrepareQueue {
    fn new() -> Self {
        let (request_tx, request_rx) = mpsc::channel::<SurfacePrepareRequest>();
        let (result_tx, result_rx) = mpsc::channel::<SurfacePrepareResult>();
        thread::Builder::new()
            .name("havenwild-surface-prepare".to_owned())
            .spawn(move || {
                while let Ok(request) = request_rx.recv() {
                    let has_player_delta = haven_save::surface_chunk_delta_path(
                        &request.chunks_root,
                        request.chunk,
                    )
                    .is_file();
                    let cached = haven_save::load_surface_chunk(&request.chunks_root, request.chunk)
                        .ok()
                        .flatten()
                        .filter(|scene| scene.id == request.target_scene_id);
                    let loaded_from_cache = cached.is_some();
                    let mut scene = cached.unwrap_or_else(|| {
                        if let Some(region) = request.pcg_region.as_deref() {
                            generate_streamed_surface_pcg_partition_with_profile(
                                request.world_seed,
                                region,
                                request.chunk,
                                request.profile,
                            )
                        } else {
                            generate_streamed_surface_chunk_with_profile(
                                request.world_seed,
                                request.chunk,
                                request.profile,
                            )
                        }
                    });
                    // AC3R4F: a cached generated baseline is still procedural
                    // authority and may receive an idempotent ecology top-up. A
                    // player delta is never reconciled here: chopping/removing a
                    // tree must remain persistent gameplay rather than respawn.
                    if !has_player_delta {
                        let _ = haven_world::reconcile_streamed_surface_natural_population(
                            &mut scene,
                            request.world_seed,
                            request.chunk,
                            request.pcg_region.as_deref(),
                        );
                    }
                    // Persist generated baseline reconciliation in the worker.
                    // Delta snapshots are already authoritative and must not be
                    // rewritten as a generated baseline.
                    let baseline_persisted = if has_player_delta {
                        true
                    } else {
                        haven_save::save_surface_chunk_baseline(
                            &request.chunks_root,
                            request.chunk,
                            &scene,
                        )
                        .is_ok()
                    };
                    if result_tx
                        .send(SurfacePrepareResult {
                            request,
                            scene,
                            loaded_from_cache,
                            baseline_persisted,
                        })
                        .is_err()
                    {
                        break;
                    }
                }
            })
            .expect("surface prepare worker should start");
        Self { request_tx, result_rx, pending: WorkerBTreeSet::new() }
    }

    fn request(
        &mut self,
        world_seed: u64,
        chunk: ChunkCoord,
        profile: GeographicGenerationProfile,
        pcg_region: Option<&str>,
        target_scene_id: haven_core::ProjectSceneId,
        chunks_root: &str,
    ) -> bool {
        let key = (chunk.x, chunk.y);
        if !self.pending.insert(key) {
            return false;
        }
        let request = SurfacePrepareRequest {
            world_seed,
            chunk,
            profile,
            pcg_region: pcg_region.map(ToOwned::to_owned),
            target_scene_id,
            chunks_root: chunks_root.to_owned(),
        };
        if self.request_tx.send(request).is_err() {
            self.pending.remove(&key);
            return false;
        }
        true
    }

    fn try_receive(&mut self) -> Option<SurfacePrepareResult> {
        match self.result_rx.try_recv() {
            Ok(result) => {
                self.pending.remove(&(result.request.chunk.x, result.request.chunk.y));
                Some(result)
            }
            Err(TryRecvError::Empty | TryRecvError::Disconnected) => None,
        }
    }

    fn pending_count(&self) -> usize { self.pending.len() }
}

impl Default for SurfacePrepareQueue {
    fn default() -> Self { Self::new() }
}

#[derive(Clone, Debug)]
enum SurfacePersistenceRequest {
    Baseline { root: String, chunk: ChunkCoord, scene: haven_core::SceneMap },
    Delta { root: String, chunk: ChunkCoord, scene: haven_core::SceneMap },
    Bytes { path: std::path::PathBuf, bytes: Vec<u8> },
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum SurfacePersistenceKind { Baseline, Delta, Bytes }

#[derive(Clone, Debug)]
struct SurfacePersistenceResult { kind: SurfacePersistenceKind, ok: bool }

struct SurfacePersistenceQueue {
    request_tx: Sender<SurfacePersistenceRequest>,
    result_rx: Receiver<SurfacePersistenceResult>,
    pending: usize,
}

impl SurfacePersistenceQueue {
    fn new() -> Self {
        let (request_tx, request_rx) = mpsc::channel::<SurfacePersistenceRequest>();
        let (result_tx, result_rx) = mpsc::channel::<SurfacePersistenceResult>();
        thread::Builder::new()
            .name("havenwild-surface-persistence".to_owned())
            .spawn(move || {
                while let Ok(request) = request_rx.recv() {
                    let (kind, ok) = match request {
                        SurfacePersistenceRequest::Baseline { root, chunk, scene } => (
                            SurfacePersistenceKind::Baseline,
                            haven_save::save_surface_chunk_baseline(&root, chunk, &scene).is_ok(),
                        ),
                        SurfacePersistenceRequest::Delta { root, chunk, scene } => (
                            SurfacePersistenceKind::Delta,
                            haven_save::save_surface_chunk_delta(&root, chunk, &scene).is_ok(),
                        ),
                        SurfacePersistenceRequest::Bytes { path, bytes } => {
                            let ok = path.parent().map_or(true, |parent| std::fs::create_dir_all(parent).is_ok())
                                && std::fs::write(path, bytes).is_ok();
                            (SurfacePersistenceKind::Bytes, ok)
                        }
                    };
                    if result_tx.send(SurfacePersistenceResult { kind, ok }).is_err() { break; }
                }
            })
            .expect("surface persistence worker should start");
        Self { request_tx, result_rx, pending: 0 }
    }

    fn send(&mut self, request: SurfacePersistenceRequest) -> bool {
        if self.request_tx.send(request).is_ok() {
            self.pending = self.pending.saturating_add(1);
            true
        } else { false }
    }

    fn drain(&mut self) -> Vec<SurfacePersistenceResult> {
        let mut out = Vec::new();
        loop {
            match self.result_rx.try_recv() {
                Ok(result) => {
                    self.pending = self.pending.saturating_sub(1);
                    out.push(result);
                }
                Err(TryRecvError::Empty | TryRecvError::Disconnected) => break,
            }
        }
        out
    }

    fn pending_count(&self) -> usize { self.pending }
}

impl Default for SurfacePersistenceQueue {
    fn default() -> Self { Self::new() }
}

#[derive(Clone, Debug)]
struct HydrologyJobRequest {
    token: u64,
    scene_ids: Vec<(ChunkCoord, haven_core::ProjectSceneId)>,
    window: ChunkHydrologyWindowV2,
}

#[derive(Clone, Debug)]
struct HydrologyJobResult {
    token: u64,
    scene_ids: Vec<(ChunkCoord, haven_core::ProjectSceneId)>,
    chunks: Vec<haven_core::TavernMap>,
    applied_cells: u32,
}

struct HydrologyJobQueue {
    request_tx: Sender<HydrologyJobRequest>,
    result_rx: Receiver<HydrologyJobResult>,
    pending: bool,
}

impl HydrologyJobQueue {
    fn new() -> Self {
        let (request_tx, request_rx) = mpsc::channel::<HydrologyJobRequest>();
        let (result_tx, result_rx) = mpsc::channel::<HydrologyJobResult>();
        thread::Builder::new()
            .name("havenwild-hydrology".to_owned())
            .spawn(move || {
                while let Ok(mut request) = request_rx.recv() {
                    let applied_cells = reconcile_chunk_hydrology_v2(
                        &mut request.window,
                        HydrologySettingsV2::default(),
                    ).map(|report| report.applied_cells).unwrap_or(0);
                    let result = HydrologyJobResult {
                        token: request.token,
                        scene_ids: request.scene_ids,
                        chunks: request.window.chunks,
                        applied_cells,
                    };
                    if result_tx.send(result).is_err() { break; }
                }
            })
            .expect("hydrology worker should start");
        Self { request_tx, result_rx, pending: false }
    }

    fn request(&mut self, request: HydrologyJobRequest) -> bool {
        if self.pending { return false; }
        if self.request_tx.send(request).is_ok() { self.pending = true; true } else { false }
    }

    fn try_receive(&mut self) -> Option<HydrologyJobResult> {
        match self.result_rx.try_recv() {
            Ok(result) => { self.pending = false; Some(result) }
            Err(TryRecvError::Empty | TryRecvError::Disconnected) => None,
        }
    }

    fn pending(&self) -> bool { self.pending }
}

impl Default for HydrologyJobQueue {
    fn default() -> Self { Self::new() }
}

#[derive(Clone, Debug)]
struct StructuralJobRequest {
    token: u64,
    partitions: Vec<(ChunkCoord, haven_core::TavernMap)>,
}

#[derive(Clone, Debug)]
struct StructuralJobResult {
    token: u64,
    normalized_levels: Vec<(ChunkCoord, Vec<u8>)>,
    bake: Result<haven_world::PartitionedSurfaceStructuralBakeV2, String>,
}

struct StructuralJobQueue {
    request_tx: Sender<StructuralJobRequest>,
    result_rx: Receiver<StructuralJobResult>,
    pending: bool,
}

impl StructuralJobQueue {
    fn new() -> Self {
        let (request_tx, request_rx) = mpsc::channel::<StructuralJobRequest>();
        let (result_tx, result_rx) = mpsc::channel::<StructuralJobResult>();
        thread::Builder::new()
            .name("havenwild-structural-surface".to_owned())
            .spawn(move || {
                while let Ok(mut request) = request_rx.recv() {
                    // AC2: normalization is part of the structural worker job.
                    // It previously ran synchronously after each residency shift,
                    // immediately before the background bake was requested.
                    let _normalization = haven_world::normalize_partitioned_structural_elevation_v1(
                        &mut request.partitions,
                    );
                    let normalized_levels = request
                        .partitions
                        .iter()
                        .map(|(chunk, map)| (*chunk, map.structural_levels.clone()))
                        .collect::<Vec<_>>();
                    let bake = haven_world::bake_partitioned_surface_structural_terrain_v2(
                        &request.partitions,
                        false,
                        haven_world::ElevationCliffSettingsV2::default(),
                    );
                    if result_tx
                        .send(StructuralJobResult {
                            token: request.token,
                            normalized_levels,
                            bake,
                        })
                        .is_err()
                    {
                        break;
                    }
                }
            })
            .expect("structural surface worker should start");
        Self { request_tx, result_rx, pending: false }
    }

    fn request(&mut self, request: StructuralJobRequest) -> bool {
        if self.pending { return false; }
        if self.request_tx.send(request).is_ok() { self.pending = true; true } else { false }
    }

    fn try_receive(&mut self) -> Option<StructuralJobResult> {
        match self.result_rx.try_recv() {
            Ok(result) => { self.pending = false; Some(result) }
            Err(TryRecvError::Empty | TryRecvError::Disconnected) => None,
        }
    }

    fn pending(&self) -> bool { self.pending }
}

impl Default for StructuralJobQueue {
    fn default() -> Self { Self::new() }
}
