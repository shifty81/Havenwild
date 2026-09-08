use super::*;
use haven_world::open_world::{ChunkCoord, WorldTileCoord};
use haven_world::scene_rectangles::{
    SceneRectangleManifest, SceneRectangleSpec, SCENE_RECTANGLE_MANIFEST_PATH,
};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};


const WORLD_MAP_EXPLORATION_SCHEMA: &str = "havenwild.world_map_exploration.v0_2";
const WORLD_MAP_SAMPLE_STEP: i32 = 2;
const WORLD_MAP_UNEXPLORED: u8 = u8::MAX;
const WORLD_MAP_REVEAL_RADIUS_TILES: i32 = 20;
const WORLD_MAP_CHUNK_COLS: usize = MAP_W / WORLD_MAP_SAMPLE_STEP as usize;
const WORLD_MAP_CHUNK_ROWS: usize = MAP_H / WORLD_MAP_SAMPLE_STEP as usize;

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
struct WorldMapChunkSnapshot {
    chunk_x: i32,
    chunk_y: i32,
    cols: usize,
    rows: usize,
    cells: Vec<u8>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct PersistedWorldMapExploration {
    schema: String,
    chunks: Vec<WorldMapChunkSnapshot>,
}

#[derive(Clone, Debug)]
pub(crate) struct WorldMapLandmark {
    pub world_x: i32,
    pub world_y: i32,
    pub label: String,
    pub capital: bool,
}

#[derive(Clone, Debug)]
pub(crate) struct WorldMapOverview {
    pub origin_x: i32,
    pub origin_y: i32,
    pub span_w: i32,
    pub span_h: i32,
    pub cols: usize,
    pub rows: usize,
    pub cells: Vec<u8>,
    pub landmarks: Vec<WorldMapLandmark>,
}

#[derive(Clone, Debug)]
pub(crate) struct WorldMapState {
    pub open: bool,
    pub center: Vec2,
    pub zoom: f32,
    pub drag_last: Option<Vec2>,
    pub manifest: Option<SceneRectangleManifest>,
    pub overview: Option<WorldMapOverview>,
    pub(crate) development_reveal_all: bool,
    explored_chunks: BTreeMap<(i32, i32), WorldMapChunkSnapshot>,
    exploration_path: PathBuf,
    last_capture_sample: Option<(i32, i32)>,
}

impl WorldMapState {
    pub fn load(save_manifest_path: &str) -> Self {
        let manifest = SceneRectangleManifest::load_from_path(save_manifest_path)
            .or_else(|_| {
                let fallback = runtime_root().join(SCENE_RECTANGLE_MANIFEST_PATH);
                SceneRectangleManifest::load_from_path(&fallback.to_string_lossy())
            })
            .ok();
        let exploration_path = world_map_exploration_path(save_manifest_path);
        let explored_chunks = load_world_map_exploration(&exploration_path);
        Self {
            open: false,
            center: Vec2::ZERO,
            zoom: 1.0,
            drag_last: None,
            manifest,
            overview: None,
            // Development acceptance mode: expose the complete generated macro map
            // by default so worldgen can be inspected before release fog is restored.
            development_reveal_all: true,
            explored_chunks,
            exploration_path,
            last_capture_sample: None,
        }
    }
}


// Pass167Z109Q: behavior-preserving source extraction. These files are
// included into this module so privacy and runtime behavior remain unchanged
// while the oversized coordinator is reduced to focused source units.
include!("runtime_world_map_development.rs");
include!("runtime_world_map_bake.rs");
include!("runtime_world_map_game.rs");
include!("runtime_world_map_helpers.rs");
include!("runtime_world_map_tests.rs");
