use crate::{ConnectionKey, RecipeCatalog, ResolveError, ResolvedRecipe, SemanticId};

pub fn surface_key(center: SemanticId, neighbors: [SemanticId;8], context: Vec<(String,String)>) -> ConnectionKey {
    let connected = neighbors.map(|n| n == center);
    ConnectionKey { center, connected, context }
}
pub fn resolve_surface<C:RecipeCatalog>(catalog:&C,key:&ConnectionKey)->Result<ResolvedRecipe,ResolveError>{
    catalog.resolve_exact("surface",key)
}
