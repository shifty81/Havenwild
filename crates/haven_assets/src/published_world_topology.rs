//! Published asset vocabulary for asset-driven terrain/water/cliff generation.
//!
//! This registry is deliberately small. Mechanical LPC source indexing remains
//! useful for inspection, but runtime/worldgen authority begins only after a
//! component has a stable semantic ID and certification.

use std::{collections::BTreeMap, sync::OnceLock};

use serde::Deserialize;

use crate::terrain_atlas_catalog_v2::terrain_atlas_catalog_v2;

pub const PUBLISHED_WORLD_TOPOLOGY_REGISTRY_V1_PATH: &str =
    "content/assets/published_world_topology_registry_v1.json";
pub const PUBLISHED_WORLD_TOPOLOGY_REGISTRY_V1_SCHEMA: &str =
    "havenwild.published_world_topology_registry.v1";

const EMBEDDED_REGISTRY: &str =
    include_str!("../../../content/assets/published_world_topology_registry_v1.json");

static REGISTRY: OnceLock<Result<PublishedWorldTopologyRegistry, String>> = OnceLock::new();

#[derive(Clone, Copy, Debug, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
#[serde(rename_all = "snake_case")]
pub enum PublishedWorldDomain {
    Terrain,
    Water,
    Cliff,
}

#[derive(Clone, Copy, Debug, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum PublishedWorldAssetKind {
    SourceCell,
    SourceStamp,
}

#[derive(Clone, Copy, Debug, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum PublishedWorldUsageLane {
    SemanticSource,
    StructuralRuntime,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct PublishedWorldTopologyEntry {
    pub id: String,
    pub domain: PublishedWorldDomain,
    pub kind: PublishedWorldAssetKind,
    pub semantic_role: String,
    pub usage_lane: PublishedWorldUsageLane,
    pub atlas_id: String,
    pub source_path: String,
    pub source_rect_cells: [u16; 4],
    #[serde(default)]
    pub anchor_offset_cells: Option<[i16; 2]>,
    #[serde(default)]
    pub repeatable_y: bool,
    #[serde(default)]
    pub tags: Vec<String>,
    pub certification: String,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct PublishedWorldTopologyFile {
    schema: String,
    version: String,
    tile_size_px: u16,
    entries: Vec<PublishedWorldTopologyEntry>,
}

#[derive(Clone, Debug)]
pub struct PublishedWorldTopologyRegistry {
    schema: String,
    version: String,
    tile_size_px: u16,
    entries: Vec<PublishedWorldTopologyEntry>,
    index: BTreeMap<String, usize>,
}

impl PublishedWorldTopologyRegistry {
    fn load_embedded() -> Result<Self, String> {
        let file: PublishedWorldTopologyFile = serde_json::from_str(EMBEDDED_REGISTRY)
            .map_err(|error| format!("{PUBLISHED_WORLD_TOPOLOGY_REGISTRY_V1_PATH}: {error}"))?;

        if file.schema != PUBLISHED_WORLD_TOPOLOGY_REGISTRY_V1_SCHEMA {
            return Err(format!(
                "{PUBLISHED_WORLD_TOPOLOGY_REGISTRY_V1_PATH}: unsupported schema {}",
                file.schema
            ));
        }
        if file.tile_size_px != 32 {
            return Err("published world topology source cell must remain 32px".to_string());
        }

        let atlas_catalog = terrain_atlas_catalog_v2()
            .map_err(|error| format!("terrain atlas catalog unavailable: {error}"))?;

        let mut index = BTreeMap::new();
        let mut domain_counts = BTreeMap::<PublishedWorldDomain, usize>::new();

        for (entry_index, entry) in file.entries.iter().enumerate() {
            if entry.id.trim().is_empty()
                || entry.semantic_role.trim().is_empty()
                || entry.source_path.trim().is_empty()
                || entry.atlas_id.trim().is_empty()
            {
                return Err(
                    "published world topology entry contains an empty authority field".to_string()
                );
            }
            if entry.certification != "runtime_certified" {
                return Err(format!(
                    "{} is in the published registry without runtime certification",
                    entry.id
                ));
            }

            let [_, _, width, height] = entry.source_rect_cells;
            if width == 0 || height == 0 {
                return Err(format!("{} has an empty source rectangle", entry.id));
            }
            match entry.kind {
                PublishedWorldAssetKind::SourceCell if [width, height] != [1, 1] => {
                    return Err(format!(
                        "{} is declared as a source cell but spans {}x{} cells",
                        entry.id, width, height
                    ));
                }
                PublishedWorldAssetKind::SourceStamp if width == 1 && height == 1 => {
                    return Err(format!(
                        "{} is declared as a source stamp but is only one cell",
                        entry.id
                    ));
                }
                _ => {}
            }

            let atlas = atlas_catalog
                .atlas(&entry.atlas_id)
                .ok_or_else(|| format!("{} references unknown atlas {}", entry.id, entry.atlas_id))?;
            if atlas.source_path != entry.source_path {
                return Err(format!(
                    "{} source path {} disagrees with atlas {} source {}",
                    entry.id, entry.source_path, entry.atlas_id, atlas.source_path
                ));
            }

            if index.insert(entry.id.clone(), entry_index).is_some() {
                return Err(format!("duplicate published world topology id {}", entry.id));
            }
            *domain_counts.entry(entry.domain).or_insert(0) += 1;
        }

        for required in [
            PublishedWorldDomain::Terrain,
            PublishedWorldDomain::Water,
            PublishedWorldDomain::Cliff,
        ] {
            if domain_counts.get(&required).copied().unwrap_or(0) == 0 {
                return Err(format!("published world topology is missing {required:?}"));
            }
        }

        Ok(Self {
            schema: file.schema,
            version: file.version,
            tile_size_px: file.tile_size_px,
            entries: file.entries,
            index,
        })
    }

    pub fn schema(&self) -> &str {
        &self.schema
    }

    pub fn version(&self) -> &str {
        &self.version
    }

    pub const fn tile_size_px(&self) -> u16 {
        self.tile_size_px
    }

    pub fn entries(&self) -> &[PublishedWorldTopologyEntry] {
        &self.entries
    }

    pub fn entry(&self, id: &str) -> Option<&PublishedWorldTopologyEntry> {
        self.index
            .get(id)
            .and_then(|entry_index| self.entries.get(*entry_index))
    }

    pub fn entries_for_domain(
        &self,
        domain: PublishedWorldDomain,
    ) -> impl Iterator<Item = &PublishedWorldTopologyEntry> {
        self.entries.iter().filter(move |entry| entry.domain == domain)
    }
}

pub fn published_world_topology_registry_v1(
) -> Result<&'static PublishedWorldTopologyRegistry, &'static str> {
    REGISTRY
        .get_or_init(PublishedWorldTopologyRegistry::load_embedded)
        .as_ref()
        .map_err(String::as_str)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn registry_is_small_published_authority_not_raw_slice_inventory() {
        let registry =
            published_world_topology_registry_v1().expect("published topology registry should load");
        assert_eq!(registry.schema(), PUBLISHED_WORLD_TOPOLOGY_REGISTRY_V1_SCHEMA);
        assert_eq!(registry.tile_size_px(), 32);
        assert!(registry.entries().len() >= 20);
        assert!(registry.entries().len() < 256);
    }

    #[test]
    fn first_certification_domains_are_present() {
        let registry =
            published_world_topology_registry_v1().expect("published topology registry should load");
        for domain in [
            PublishedWorldDomain::Terrain,
            PublishedWorldDomain::Water,
            PublishedWorldDomain::Cliff,
        ] {
            assert!(registry.entries_for_domain(domain).next().is_some());
        }
    }

    #[test]
    fn directional_ramps_preserve_complete_authored_stamps_and_anchor() {
        let registry =
            published_world_topology_registry_v1().expect("published topology registry should load");
        let right = registry.entry("cliff.ramp.rise_right.grass").unwrap();
        let left = registry.entry("cliff.ramp.rise_left.grass").unwrap();
        assert_eq!(right.source_rect_cells, [3, 5, 3, 4]);
        assert_eq!(left.source_rect_cells, [6, 5, 3, 4]);
        assert_eq!(right.anchor_offset_cells, Some([-1, 0]));
        assert_eq!(left.anchor_offset_cells, Some([-1, 0]));
    }

    #[test]
    fn straight_cliff_face_is_explicit_crest_body_foot() {
        let registry =
            published_world_topology_registry_v1().expect("published topology registry should load");
        let crest = registry.entry("cliff.south.straight.crest").unwrap();
        let body = registry.entry("cliff.south.straight.body").unwrap();
        let foot = registry.entry("cliff.south.straight.foot").unwrap();
        assert_eq!(crest.source_rect_cells, [2, 7, 1, 1]);
        assert_eq!(body.source_rect_cells, [2, 3, 1, 1]);
        assert!(body.repeatable_y);
        assert_eq!(foot.source_rect_cells, [2, 8, 1, 1]);
    }

    #[test]
    fn reviewed_v7_water_roles_remain_distinct() {
        let registry =
            published_world_topology_registry_v1().expect("published topology registry should load");
        let shallow = registry.entry("water.shallow.dirt.v7").unwrap();
        let deep = registry.entry("water.deep.v7").unwrap();
        assert_ne!(shallow.source_rect_cells, deep.source_rect_cells);
        assert_ne!(shallow.semantic_role, deep.semantic_role);
    }
}
