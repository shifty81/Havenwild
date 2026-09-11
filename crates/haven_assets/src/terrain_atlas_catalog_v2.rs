//! Canonical terrain/structure atlas catalog facade for Havenwild.
//!
//! This module does not synthesize art. It binds stable semantic atlas IDs to
//! already-published/source-authored sheets and exposes reviewed source regions
//! that were previously duplicated inside individual renderers. The JSON
//! catalog is embedded so runtime, editor and validators all read the same
//! project-owned authority without depending on the current working directory.

use std::{collections::BTreeMap, sync::OnceLock};

use serde::Deserialize;

pub const TERRAIN_ATLAS_CATALOG_V2_SCHEMA: &str = "havenwild.terrain_atlas_catalog.v2";
pub const TERRAIN_ATLAS_CATALOG_V2_PATH: &str = "content/assets/terrain_atlas_catalog_v2.json";

pub const ATLAS_ID_V7_MAPPED: &str = "surface.v7.mapped";
pub const ATLAS_ID_V7_DIRECT: &str = "surface.v7.direct";
pub const ATLAS_ID_V7_TRANSITION_COMPAT: &str = "surface.v7.transition_compat";
pub const ATLAS_ID_ELIZAWY_CLIFF_SUMMER: &str = "structure.elizawy.cliff.summer";
pub const ATLAS_ID_LPC_CLIFF_RAMP_GRASS: &str = "structure.lpc.cliff_ramp.grass";
pub const ATLAS_ID_ELIZAWY_WATERFALL: &str = "structure.elizawy.waterfall";
pub const ATLAS_ID_ELIZAWY_TERRAIN_SUMMER_REFERENCE: &str = "surface.elizawy.summer.reference";

pub const V7_MAPPED_ATLAS_PATH: &str =
    "assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.png";
pub const V7_MAPPED_MANIFEST_PATH: &str =
    "assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json";
pub const V7_DIRECT_SOURCE_PATH: &str =
    "content/assets/lpc/source/lpc-terrains-v7/terrain-v7.png";
pub const V7_DIRECT_SOURCE_TILESET_PATH: &str =
    "content/assets/lpc/source/lpc-terrains-v7/terrain-v7.tsx";
pub const V7_DIRECT_SOURCE_COLUMNS: u16 = 32;
pub const V7_DIRECT_SOURCE_ROWS: u16 = 64;
/// Reviewed compatibility-transition source blocks currently occupy only this
/// legacy sub-region of terrain-v7.png. Keeping this bound narrower than the
/// whole sheet prevents uncatalogued cells from becoming accidental art.
pub const V7_DIRECT_TRANSITION_REGION_COLUMNS: u16 = 16;
pub const V7_DIRECT_TRANSITION_REGION_ROWS: u16 = 26;
pub const V7_DIRECT_ROLE_CATALOG_PATH: &str =
    "content/worldgen/v7_terrain_role_catalog_v0_1.json";
pub const V7_TRANSITION_COMPAT_ATLAS_PATH: &str =
    "assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.png";
pub const V7_TRANSITION_COMPAT_MANIFEST_PATH: &str =
    "assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.json";
pub const ELIZAWY_CLIFF_SOURCE_PATH: &str =
    "assets/source/licensed/lpc_revised/Terrain/cliff_summer.png";
pub const ELIZAWY_CLIFF_PUBLISHED_PATH: &str =
    "assets/generated/worldgen_v0_1/terrain/elizawy_cliff_runtime_overlay_summer.png";
pub const LPC_CLIFF_RAMP_GRASS_SOURCE_PATH_V2: &str =
    "content/assets/oga_lpc/source/terrain/cliffs_grass_top/LPC_cliffs_grass.png";
pub const LPC_CLIFF_RAMP_DIRT_SOURCE_PATH_V2: &str =
    "content/assets/oga_lpc/source/terrain/cliffs_grass_top/LPC_cliffs_ddirt.png";
pub const LPC_CLIFF_RAMP_SAND_SOURCE_PATH_V2: &str =
    "content/assets/oga_lpc/source/terrain/cliffs_grass_top/LPC_cliffs_sand.png";
pub const LPC_CLIFF_RAMP_SNOW_SOURCE_PATH_V2: &str =
    "content/assets/oga_lpc/source/terrain/cliffs_grass_top/LPC_cliffs_snow.png";
pub const ELIZAWY_WATERFALL_SOURCE_PATH_V2: &str =
    "assets/source/licensed/lpc_revised/Terrain/Waterfall.png";
pub const ELIZAWY_TERRAIN_SUMMER_SOURCE_PATH_V2: &str =
    "assets/source/licensed/lpc_revised/Terrain/terrain_summer.png";

const EMBEDDED_CATALOG: &str = include_str!("../../../content/assets/terrain_atlas_catalog_v2.json");
const EMBEDDED_V7_ROLE_CATALOG: &str =
    include_str!("../../../content/worldgen/v7_terrain_role_catalog_v0_1.json");

static CATALOG: OnceLock<Result<TerrainAtlasCatalogV2, String>> = OnceLock::new();
static V7_ROLE_CATALOG: OnceLock<Result<V7RoleCatalog, String>> = OnceLock::new();

#[derive(Clone, Copy, Debug, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum TerrainAtlasClassV2 {
    SurfaceCornerTuple,
    SurfaceDirectSource,
    TransitionCompatibility,
    StructuralCliff,
    StructuralStamp,
}

#[derive(Clone, Copy, Debug, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum TerrainAtlasAuthorityV2 {
    Production,
    Compatibility,
    SourceReference,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct TerrainAtlasDescriptorV2 {
    pub id: String,
    pub class: TerrainAtlasClassV2,
    pub provider: String,
    pub authority: TerrainAtlasAuthorityV2,
    pub source_path: String,
    pub published_path: String,
    #[serde(default)]
    pub manifest_path: Option<String>,
    pub cell_px: u16,
    #[serde(default)]
    pub roles: Vec<String>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct DirectLpcTransitionBlockV2 {
    pub outer_col: u8,
    pub outer_row: u8,
    pub inner: Option<(u8, u8)>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct DirectTransitionBlockFile {
    group: String,
    outer_origin: [u8; 2],
    #[serde(default)]
    inner_origin: Option<[u8; 2]>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct TerrainAtlasCatalogFile {
    schema: String,
    version: String,
    tile_size: [u16; 2],
    atlases: Vec<TerrainAtlasDescriptorV2>,
    direct_transition_blocks: Vec<DirectTransitionBlockFile>,
}

#[derive(Clone, Debug)]
pub struct TerrainAtlasCatalogV2 {
    schema: String,
    version: String,
    tile_size: [u16; 2],
    atlases: Vec<TerrainAtlasDescriptorV2>,
    atlas_index: BTreeMap<String, usize>,
    direct_transition_blocks: BTreeMap<String, DirectLpcTransitionBlockV2>,
}

impl TerrainAtlasCatalogV2 {
    fn load_embedded() -> Result<Self, String> {
        let file: TerrainAtlasCatalogFile = serde_json::from_str(EMBEDDED_CATALOG)
            .map_err(|error| format!("{TERRAIN_ATLAS_CATALOG_V2_PATH}: {error}"))?;
        if file.schema != TERRAIN_ATLAS_CATALOG_V2_SCHEMA {
            return Err(format!(
                "{TERRAIN_ATLAS_CATALOG_V2_PATH}: unsupported schema {}",
                file.schema
            ));
        }
        if file.tile_size != [32, 32] {
            return Err(format!(
                "{TERRAIN_ATLAS_CATALOG_V2_PATH}: terrain source cell must remain 32x32"
            ));
        }

        let mut atlas_index = BTreeMap::new();
        for (index, atlas) in file.atlases.iter().enumerate() {
            if atlas.cell_px != 32 {
                return Err(format!("atlas {} must use 32px source cells", atlas.id));
            }
            if atlas.id.trim().is_empty()
                || atlas.source_path.trim().is_empty()
                || atlas.published_path.trim().is_empty()
            {
                return Err("terrain atlas descriptor contains an empty authority field".to_string());
            }
            if atlas_index.insert(atlas.id.clone(), index).is_some() {
                return Err(format!("duplicate terrain atlas id {}", atlas.id));
            }
        }

        let mut direct_transition_blocks = BTreeMap::new();
        for block in file.direct_transition_blocks {
            if block.group.trim().is_empty() {
                return Err("direct transition group id cannot be empty".to_string());
            }
            let reviewed = DirectLpcTransitionBlockV2 {
                outer_col: block.outer_origin[0],
                outer_row: block.outer_origin[1],
                inner: block.inner_origin.map(|origin| (origin[0], origin[1])),
            };
            Self::validate_direct_transition_block(&block.group, reviewed)?;
            if direct_transition_blocks
                .insert(block.group.clone(), reviewed)
                .is_some()
            {
                return Err(format!("duplicate direct transition group {}", block.group));
            }
        }

        let catalog = Self {
            schema: file.schema,
            version: file.version,
            tile_size: file.tile_size,
            atlases: file.atlases,
            atlas_index,
            direct_transition_blocks,
        };
        catalog.validate_locked_authorities()?;
        Ok(catalog)
    }

    fn validate_direct_transition_block(
        group: &str,
        block: DirectLpcTransitionBlockV2,
    ) -> Result<(), String> {
        let outer_fits = u16::from(block.outer_col) + 2 < V7_DIRECT_TRANSITION_REGION_COLUMNS
            && u16::from(block.outer_row) + 2 < V7_DIRECT_TRANSITION_REGION_ROWS;
        if !outer_fits {
            return Err(format!(
                "direct transition group {group} escapes reviewed V7 transition region"
            ));
        }
        if let Some((column, row)) = block.inner {
            let inner_fits = u16::from(column) + 1 < V7_DIRECT_TRANSITION_REGION_COLUMNS
                && u16::from(row) + 1 < V7_DIRECT_TRANSITION_REGION_ROWS;
            if !inner_fits {
                return Err(format!(
                    "direct transition group {group} inner block escapes reviewed V7 transition region"
                ));
            }
        }
        Ok(())
    }

    fn validate_locked_authorities(&self) -> Result<(), String> {
        let locked = [
            (ATLAS_ID_V7_MAPPED, V7_MAPPED_ATLAS_PATH, V7_MAPPED_MANIFEST_PATH),
            (
                ATLAS_ID_V7_TRANSITION_COMPAT,
                V7_TRANSITION_COMPAT_ATLAS_PATH,
                V7_TRANSITION_COMPAT_MANIFEST_PATH,
            ),
        ];
        for (id, published, manifest) in locked {
            let descriptor = self
                .atlas(id)
                .ok_or_else(|| format!("missing locked terrain atlas {id}"))?;
            if descriptor.published_path != published {
                return Err(format!(
                    "terrain atlas {id} published path drift: {} != {published}",
                    descriptor.published_path
                ));
            }
            if descriptor.manifest_path.as_deref() != Some(manifest) {
                return Err(format!("terrain atlas {id} manifest path drift"));
            }
        }

        let v7_direct = self
            .atlas(ATLAS_ID_V7_DIRECT)
            .ok_or_else(|| "missing V7 direct source atlas".to_string())?;
        if v7_direct.source_path != V7_DIRECT_SOURCE_PATH
            || v7_direct.published_path != V7_DIRECT_SOURCE_PATH
        {
            return Err("V7 direct source path drift".to_string());
        }

        let cliff = self
            .atlas(ATLAS_ID_ELIZAWY_CLIFF_SUMMER)
            .ok_or_else(|| "missing ElizaWy cliff atlas".to_string())?;
        if cliff.source_path != ELIZAWY_CLIFF_SOURCE_PATH
            || cliff.published_path != ELIZAWY_CLIFF_PUBLISHED_PATH
        {
            return Err("ElizaWy cliff source/publication path drift".to_string());
        }

        let ramp = self
            .atlas(ATLAS_ID_LPC_CLIFF_RAMP_GRASS)
            .ok_or_else(|| "missing LPC cliff ramp atlas".to_string())?;
        if ramp.source_path != LPC_CLIFF_RAMP_GRASS_SOURCE_PATH_V2
            || ramp.published_path != LPC_CLIFF_RAMP_GRASS_SOURCE_PATH_V2
        {
            return Err("LPC cliff ramp source path drift".to_string());
        }
        Ok(())
    }

    pub fn schema(&self) -> &str {
        &self.schema
    }

    pub fn version(&self) -> &str {
        &self.version
    }

    pub const fn tile_size(&self) -> [u16; 2] {
        self.tile_size
    }

    pub fn atlases(&self) -> &[TerrainAtlasDescriptorV2] {
        &self.atlases
    }

    pub fn atlas(&self, id: &str) -> Option<&TerrainAtlasDescriptorV2> {
        self.atlas_index
            .get(id)
            .and_then(|index| self.atlases.get(*index))
    }

    pub fn direct_transition_block(&self, group: &str) -> Option<DirectLpcTransitionBlockV2> {
        self.direct_transition_blocks.get(group).copied()
    }

    pub fn direct_transition_group_ids(&self) -> impl Iterator<Item = &str> {
        self.direct_transition_blocks.keys().map(String::as_str)
    }
}

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct V7RoleCatalogFile {
    schema: String,
    materials: Vec<V7MaterialFile>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct V7MaterialFile {
    material_id: String,
    source_tile_id: u16,
    source_cell: [u16; 2],
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct V7SourceCellV2 {
    pub source_tile_id: u16,
    pub column: u16,
    pub row: u16,
}

#[derive(Clone, Debug)]
struct V7RoleCatalog {
    materials: BTreeMap<String, (u16, [u16; 2])>,
}

impl V7RoleCatalog {
    fn load_embedded() -> Result<Self, String> {
        let file: V7RoleCatalogFile = serde_json::from_str(EMBEDDED_V7_ROLE_CATALOG)
            .map_err(|error| format!("{V7_DIRECT_ROLE_CATALOG_PATH}: {error}"))?;
        if file.schema != "havenwild.worldgen.v7_terrain_role_catalog.v0_1" {
            return Err(format!(
                "{V7_DIRECT_ROLE_CATALOG_PATH}: unsupported schema {}",
                file.schema
            ));
        }
        let mut materials = BTreeMap::new();
        for material in file.materials {
            let expected_col = material.source_tile_id % V7_DIRECT_SOURCE_COLUMNS;
            let expected_row = material.source_tile_id / V7_DIRECT_SOURCE_COLUMNS;
            if material.source_cell != [expected_col, expected_row] {
                return Err(format!(
                    "V7 role {} source cell {:?} disagrees with tile id {}",
                    material.material_id, material.source_cell, material.source_tile_id
                ));
            }
            if expected_col >= V7_DIRECT_SOURCE_COLUMNS || expected_row >= V7_DIRECT_SOURCE_ROWS {
                return Err(format!(
                    "V7 role {} source cell {:?} escapes the 32x64 source grid",
                    material.material_id, material.source_cell
                ));
            }
            if materials
                .insert(
                    material.material_id.clone(),
                    (material.source_tile_id, material.source_cell),
                )
                .is_some()
            {
                return Err(format!("duplicate V7 material {}", material.material_id));
            }
        }
        Ok(Self { materials })
    }
}

pub fn terrain_atlas_catalog_v2() -> Result<&'static TerrainAtlasCatalogV2, &'static str> {
    CATALOG
        .get_or_init(TerrainAtlasCatalogV2::load_embedded)
        .as_ref()
        .map_err(|_| "terrain atlas catalog v2 unavailable")
}

pub fn terrain_atlas_descriptor_v2(id: &str) -> Option<&'static TerrainAtlasDescriptorV2> {
    terrain_atlas_catalog_v2().ok()?.atlas(id)
}

pub fn direct_lpc_transition_block_v2(group: &str) -> Option<DirectLpcTransitionBlockV2> {
    terrain_atlas_catalog_v2().ok()?.direct_transition_block(group)
}

pub fn v7_source_cell_v2(material_id: &str) -> Option<V7SourceCellV2> {
    let catalog = V7_ROLE_CATALOG
        .get_or_init(V7RoleCatalog::load_embedded)
        .as_ref()
        .ok()?;
    let (source_tile_id, source_cell) = *catalog.materials.get(material_id)?;
    Some(V7SourceCellV2 {
        source_tile_id,
        column: source_cell[0],
        row: source_cell[1],
    })
}

pub fn v7_source_tile_id_v2(material_id: &str) -> Option<u16> {
    v7_source_cell_v2(material_id).map(|cell| cell.source_tile_id)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn catalog_loads_locked_production_sources() {
        let catalog = terrain_atlas_catalog_v2().expect("catalog");
        assert_eq!(catalog.schema(), TERRAIN_ATLAS_CATALOG_V2_SCHEMA);
        assert_eq!(catalog.tile_size(), [32, 32]);
        assert_eq!(
            catalog
                .atlas(ATLAS_ID_V7_MAPPED)
                .expect("mapped V7")
                .published_path,
            V7_MAPPED_ATLAS_PATH
        );
        assert_eq!(
            catalog
                .atlas(ATLAS_ID_ELIZAWY_CLIFF_SUMMER)
                .expect("cliff")
                .published_path,
            ELIZAWY_CLIFF_PUBLISHED_PATH
        );
    }

    #[test]
    fn v7_material_source_cells_come_from_existing_role_catalog() {
        let grass = v7_source_cell_v2("Grass").expect("Grass");
        assert_eq!(grass.source_tile_id, 321);
        assert_eq!([grass.column, grass.row], [1, 10]);
        let stone = v7_source_cell_v2("Stone_Tan").expect("Stone_Tan");
        assert_eq!(stone.source_tile_id, 790);
    }

    #[test]
    fn direct_transition_blocks_are_data_driven() {
        let depth = direct_lpc_transition_block_v2("shallow_rim_over_deep").expect("depth");
        assert_eq!((depth.outer_col, depth.outer_row), (0, 23));
        assert_eq!(depth.inner, Some((3, 23)));
        assert!(direct_lpc_transition_block_v2("riverbank_mud").is_none());
    }

    #[test]
    fn direct_transition_blocks_stay_inside_v7_source_grid() {
        let catalog = terrain_atlas_catalog_v2().expect("catalog");
        for group in [
            "grass_over_dirt",
            "grass_over_sand",
            "grass_bank_over_shallow",
            "dirt_bank_over_shallow",
            "sand_bank_over_shallow",
            "shallow_rim_over_deep",
            "sand_over_wet_sand",
            "pebble_path_over_dirt",
        ] {
            let block = catalog
                .direct_transition_block(group)
                .unwrap_or_else(|| panic!("missing direct transition block {group}"));
            assert!(u16::from(block.outer_col) + 2 < V7_DIRECT_TRANSITION_REGION_COLUMNS);
            assert!(u16::from(block.outer_row) + 2 < V7_DIRECT_TRANSITION_REGION_ROWS);
            if let Some((column, row)) = block.inner {
                assert!(u16::from(column) + 1 < V7_DIRECT_TRANSITION_REGION_COLUMNS);
                assert!(u16::from(row) + 1 < V7_DIRECT_TRANSITION_REGION_ROWS);
            }
        }
    }
}
