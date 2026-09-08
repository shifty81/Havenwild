use std::fmt;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Direction8 { N, NE, E, SE, S, SW, W, NW }

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct SemanticId(pub String);

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct ConnectionKey {
    pub center: SemanticId,
    pub connected: [bool; 8],
    pub context: Vec<(String, String)>,
}
impl ConnectionKey {
    pub fn cardinal_mask(&self) -> u8 {
        (self.connected[0] as u8)
            | ((self.connected[2] as u8) << 1)
            | ((self.connected[4] as u8) << 2)
            | ((self.connected[6] as u8) << 3)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ResourceKind {
    SingleTile, MultiTileRegion, IrregularRegion, Animation, ConnectedFamily,
    StructuralRecipe, AtomicPrefab, CompositePrefab,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SourceRegion {
    pub sheet: String,
    pub x: u32, pub y: u32, pub width: u32, pub height: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Footprint {
    pub width_cells: u16,
    pub height_cells: u16,
    pub occupied: Vec<(u16,u16)>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PublishedResource {
    pub semantic_id: SemanticId,
    pub kind: ResourceKind,
    pub regions: Vec<SourceRegion>,
    pub visual: Footprint,
    pub collision: Option<Footprint>,
    pub interaction: Option<Footprint>,
    pub provider: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ResolvedRecipe {
    pub recipe_id: SemanticId,
    pub resources: Vec<SemanticId>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ResolveError { MissingExactRecipe(String), AmbiguousRecipe(String) }
impl fmt::Display for ResolveError {
    fn fmt(&self, f:&mut fmt::Formatter<'_>)->fmt::Result {
        match self {
            Self::MissingExactRecipe(x)=>write!(f,"missing exact authored recipe: {x}"),
            Self::AmbiguousRecipe(x)=>write!(f,"ambiguous authored recipe: {x}"),
        }
    }
}

pub trait RecipeCatalog {
    fn resolve_exact(&self, domain:&str, key:&ConnectionKey) -> Result<ResolvedRecipe, ResolveError>;
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DrawCommand {
    pub resource: SemanticId,
    pub world_x: i32,
    pub world_y: i32,
    pub depth_key: i64,
}
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct ResolvedDrawPlan { pub commands: Vec<DrawCommand> }

#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn cardinal_mask_is_stable() {
        let k=ConnectionKey{center:SemanticId("terrain.grass".into()),connected:[true,false,true,false,false,false,true,false],context:vec![]};
        assert_eq!(k.cardinal_mask(), 0b1011);
    }
    #[test] fn footprint_is_independent_of_source_region_size() {
        let r=PublishedResource{
            semantic_id:SemanticId("tree.oak.mature".into()),kind:ResourceKind::MultiTileRegion,
            regions:vec![SourceRegion{sheet:"oak.png".into(),x:0,y:0,width:96,height:160}],
            visual:Footprint{width_cells:3,height_cells:5,occupied:vec![]},
            collision:Some(Footprint{width_cells:1,height_cells:1,occupied:vec![(0,0)]}),
            interaction:None,provider:"Havenwild".into()
        };
        assert_ne!(r.visual.width_cells, r.collision.unwrap().width_cells);
    }
}

pub mod surface;
pub mod structure;
pub mod pie;
