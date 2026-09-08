#![allow(dead_code)]

use crate::base_terrain_cache::{BaseTerrainChunkCache, BASE_TERRAIN_CHUNK_SIZE};
use haven_world::terrain_material::{TerrainMaterialId, TerrainShape};
use std::collections::BTreeMap;

/// CPU-side, renderer-independent quad description. Runtime and World Builder
/// can consume the same records before a backend turns them into Macroquad
/// meshes, render targets, or the established tile fallback.
#[derive(Clone, Copy, Debug, PartialEq)]
pub(crate) struct TerrainMeshQuad {
    pub world_x: i32,
    pub world_y: i32,
    pub local_x: u8,
    pub local_y: u8,
    pub shape: TerrainShape,
    pub material: TerrainMaterialId,
    pub atlas_mask: u8,
}

#[derive(Clone, Debug, Default)]
pub(crate) struct TerrainChunkMeshData {
    pub chunk_x: i32,
    pub chunk_y: i32,
    pub generation: u64,
    pub material_batches: BTreeMap<&'static str, Vec<TerrainMeshQuad>>,
    pub base_quads: usize,
    pub water_quads: usize,
}

impl TerrainChunkMeshData {
    pub(crate) fn rebuild(
        chunk_x: i32,
        chunk_y: i32,
        generation: u64,
        cache: &BaseTerrainChunkCache,
    ) -> Self {
        let mut mesh = Self {
            chunk_x,
            chunk_y,
            generation,
            ..Self::default()
        };
        let min_x = chunk_x * BASE_TERRAIN_CHUNK_SIZE;
        let min_y = chunk_y * BASE_TERRAIN_CHUNK_SIZE;
        for local_y in 0..BASE_TERRAIN_CHUNK_SIZE {
            for local_x in 0..BASE_TERRAIN_CHUNK_SIZE {
                let world_x = min_x + local_x;
                let world_y = min_y + local_y;
                let Some(record) = cache.record_at(world_x, world_y) else {
                    continue;
                };
                let profile =
                    haven_world::terrain_material::TerrainMaterialProfile::for_id(record.material);
                let quad = TerrainMeshQuad {
                    world_x,
                    world_y,
                    local_x: local_x as u8,
                    local_y: local_y as u8,
                    shape: record.shape,
                    material: record.material,
                    atlas_mask: record.resolved_mask,
                };
                mesh.material_batches
                    .entry(profile.code)
                    .or_default()
                    .push(quad);
                if record.tile.is_water() {
                    mesh.water_quads += 1;
                } else {
                    mesh.base_quads += 1;
                }
            }
        }
        mesh
    }

    pub(crate) fn total_quads(&self) -> usize {
        self.base_quads + self.water_quads
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_mesh_reports_no_quads() {
        let mesh = TerrainChunkMeshData::default();
        assert_eq!(mesh.total_quads(), 0);
    }
}
