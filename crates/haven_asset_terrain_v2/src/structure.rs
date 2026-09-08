use crate::{ConnectionKey, RecipeCatalog, ResolveError, ResolvedRecipe, SemanticId};

#[derive(Debug,Clone,Copy,PartialEq,Eq)]
pub struct ContourConnections { pub n:bool,pub ne:bool,pub e:bool,pub se:bool,pub s:bool,pub sw:bool,pub w:bool,pub nw:bool }
pub fn structural_key(family:SemanticId,c:ContourConnections,mut context:Vec<(String,String)>)->ConnectionKey{
    context.sort();
    ConnectionKey{center:family,connected:[c.n,c.ne,c.e,c.se,c.s,c.sw,c.w,c.nw],context}
}
pub fn resolve_structure<C:RecipeCatalog>(catalog:&C,key:&ConnectionKey)->Result<ResolvedRecipe,ResolveError>{
    catalog.resolve_exact("structure",key)
}
