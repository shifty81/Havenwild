// Havenwild V008 Scene Rectangle + Streaming Pseudocode

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum SceneKind {
    MainlandOverworld,
    IslandOverworld,
    HomeTavernMountainBase,
    MainCityDistrict,
    CoastalCity,
    Harbor,
    OwnedLandPlot,
    CaveEntry,
    CaveDepth,
    TavernInterior,
    InnUpstairs,
    Cellar,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum EdgeKind {
    NeighborScene,
    Transition,
    ForestBorder,
    MountainBorder,
    OceanBorder,
    CityWallBorder,
    CliffDropBorder,
    CaveDarknessBorder,
    FogSoftBoundary,
}

#[derive(Clone, Debug)]
pub struct SceneRectangle {
    pub scene_id: String,
    pub landmass_id: u8,
    pub kind: SceneKind,
    pub grid_pos: IVec2,
    pub tile_size: UVec2,
    pub world_origin_tile: IVec2,
    pub edges: [SceneEdge; 4],
    pub transitions: Vec<SceneTransition>,
    pub validation_flags: Vec<SceneValidationFlag>,
}

#[derive(Clone, Debug)]
pub struct SceneEdge {
    pub edge_kind: EdgeKind,
    pub neighbor_scene_id: Option<String>,
    pub seam_signature: SceneSeamSignature,
    pub seam_locked: bool,
    pub border_treatment: Option<BorderTreatment>,
}

#[derive(Clone, Debug)]
pub struct SceneSeamSignature {
    pub height_samples: Vec<f32>,
    pub terrain_samples: Vec<u16>,
    pub water_samples: Vec<u16>,
    pub biome_samples: Vec<u16>,
    pub shore_profile_samples: Vec<u16>,
    pub transition_points: Vec<TransitionPoint>,
    pub hash: u64,
}

#[derive(Clone, Debug)]
pub struct SceneTransition {
    pub transition_id: String,
    pub kind: TransitionKind,
    pub source_scene_id: String,
    pub target_scene_id: String,
    pub source_anchor: IVec2,
    pub target_anchor: IVec2,
    pub facing_direction: Direction,
    pub requirements: Vec<String>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum TransitionKind {
    WalkEdge,
    Door,
    Cave,
    HarborTravel,
    CityDistrict,
    OwnedLand,
    DungeonDepth,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum BorderTreatment {
    ForestWall,
    MountainWall,
    OceanContinuation,
    CityWall,
    CliffDrop,
    CaveDarkness,
    FencePropertyBoundary,
    FogSoftBoundary,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Direction { North, East, South, West }

#[derive(Clone, Debug)]
pub enum SceneValidationFlag {
    RiverExitWithoutNeighbor,
    RoadExitWithoutNeighbor,
    WaterDepthJumpAtEdge,
    ShoreProfileMismatch,
    HeightCliffCutByBoundary,
    LargeObjectInDecorationSafeBand,
    CameraCanSeeVoid,
}

pub fn streaming_set_for_player(
    active_scene_id: &str,
    graph: &SceneAdjacencyGraph,
    player_local_tile: IVec2,
    scene_size: UVec2,
) -> StreamingSet {
    let mut set = StreamingSet::default();
    set.load.insert(active_scene_id.to_string());

    for dir in [Direction::North, Direction::East, Direction::South, Direction::West] {
        if let Some(neighbor) = graph.neighbor(active_scene_id, dir) {
            set.load.insert(neighbor);
        }
    }

    let near_left = player_local_tile.x < 12;
    let near_right = player_local_tile.x > scene_size.x as i32 - 12;
    let near_top = player_local_tile.y < 12;
    let near_bottom = player_local_tile.y > scene_size.y as i32 - 12;

    if near_left && near_top { set.preload_diagonal(active_scene_id, Direction::North, Direction::West, graph); }
    if near_right && near_top { set.preload_diagonal(active_scene_id, Direction::North, Direction::East, graph); }
    if near_left && near_bottom { set.preload_diagonal(active_scene_id, Direction::South, Direction::West, graph); }
    if near_right && near_bottom { set.preload_diagonal(active_scene_id, Direction::South, Direction::East, graph); }

    set
}

// Placeholder project types.
pub struct SceneAdjacencyGraph;
pub struct StreamingSet { pub load: std::collections::HashSet<String> }

impl Default for StreamingSet {
    fn default() -> Self { Self { load: std::collections::HashSet::new() } }
}
impl StreamingSet {
    pub fn preload_diagonal(&mut self, _active: &str, _a: Direction, _b: Direction, _graph: &SceneAdjacencyGraph) {}
}
impl SceneAdjacencyGraph {
    pub fn neighbor(&self, _scene_id: &str, _dir: Direction) -> Option<String> { None }
}

#[derive(Clone, Copy, Debug)]
pub struct IVec2 { pub x: i32, pub y: i32 }
#[derive(Clone, Copy, Debug)]
pub struct UVec2 { pub x: u32, pub y: u32 }
pub struct TransitionPoint;
