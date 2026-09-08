#[derive(Clone, Copy)]
pub(crate) enum RenderCommand {
    Stamp(usize),
    Object(usize),
    SurfaceStamp {
        scene_index: usize,
        stamp_index: usize,
        chunk_x: i32,
        chunk_y: i32,
    },
    SurfaceObject {
        scene_index: usize,
        object_index: usize,
        chunk_x: i32,
        chunk_y: i32,
    },
    Customer(usize),
    BuildingPiece(usize),
    /// Perspective-visible south cliff face re-submitted at its projected foot
    /// depth so actors on lower ground are occluded correctly while actors in
    /// front of the cliff remain visible.
    SurfaceCliffFace {
        global_x: i32,
        global_y: i32,
    },
    Player,
}
