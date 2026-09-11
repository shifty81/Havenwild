use haven_core::{TavernMap, TileKind};
use serde::Deserialize;
use std::{fs::read_to_string, path::Path, sync::OnceLock};

use crate::terrain_material_bindings::canonical_corner_tuple_material;

const LPC_MAPPED_TERRAIN_MANIFEST_PATH: &str =
    "assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json";

static MATERIAL_TUPLES: OnceLock<Result<Vec<[String; 4]>, String>> = OnceLock::new();

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct LpcAuthoredContactRepairReport {
    /// Legacy counter retained for API/report compatibility.
    ///
    /// HW-VISUAL-WORLD-RESET-01R2 requires this to remain zero: an unsupported
    /// authored visual pair is diagnostic information, never permission to
    /// rewrite the semantic world.
    pub mountain_path_shore_shoulders: usize,
}

impl LpcAuthoredContactRepairReport {
    pub const fn total_mutations(self) -> usize {
        self.mountain_path_shore_shoulders
    }
}

pub fn lpc_mapped_terrain_supports_tile_pair(first: TileKind, second: TileKind) -> bool {
    if first == second || (is_water_tile(first) && is_water_tile(second)) {
        return true;
    }
    let Some(first_material) = canonical_corner_tuple_material(first) else {
        return true;
    };
    let Some(second_material) = canonical_corner_tuple_material(second) else {
        return true;
    };
    material_tuples().is_some_and(|tuples| {
        tuples.iter().any(|corners| {
            let has_first = corners.iter().any(|corner| corner == first_material);
            let has_second = corners.iter().any(|corner| corner == second_material);
            has_first && has_second
        })
    })
}

/// Legacy compatibility entry point.
///
/// Previous behavior changed `MountainPath` into `Road` beside sand because the
/// current V7 tuple catalog did not contain the requested visual combination.
/// That made renderer/asset coverage authoritative over gameplay semantics.
///
/// The reset retires that policy. Callers may keep invoking this function while
/// the old API is unwound, but it performs no semantic mutation. Unsupported
/// contacts are surfaced by the existing pair-support/audit path instead.
pub fn normalize_lpc_authored_material_contacts_region(
    _map: &mut TavernMap,
    _min_x: i32,
    _min_y: i32,
    _max_x: i32,
    _max_y: i32,
) -> LpcAuthoredContactRepairReport {
    LpcAuthoredContactRepairReport::default()
}

fn material_tuples() -> Option<&'static [[String; 4]]> {
    MATERIAL_TUPLES
        .get_or_init(load_material_tuples)
        .as_ref()
        .ok()
        .map(Vec::as_slice)
}

fn load_material_tuples() -> Result<Vec<[String; 4]>, String> {
    let path = repo_root_dir().join(LPC_MAPPED_TERRAIN_MANIFEST_PATH);
    let raw = read_to_string(&path).map_err(|error| format!("{}: {error}", path.display()))?;
    let manifest: Manifest =
        serde_json::from_str(&raw).map_err(|error| format!("{}: {error}", path.display()))?;
    Ok(manifest
        .entries
        .into_iter()
        .map(|entry| {
            [
                entry.corners.top_left,
                entry.corners.top_right,
                entry.corners.bottom_left,
                entry.corners.bottom_right,
            ]
        })
        .collect())
}

fn repo_root_dir() -> std::path::PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("..")
        .canonicalize()
        .expect("workspace root should be reachable from haven_assets")
}

fn is_water_tile(tile: TileKind) -> bool {
    matches!(
        tile,
        TileKind::Water
            | TileKind::ShallowWater
            | TileKind::DeepWater
            | TileKind::OceanDeep
            | TileKind::OceanShallow
            | TileKind::RiverWater
            | TileKind::RiverMouthBlend
            | TileKind::ShoreFoam
    )
}

#[derive(Deserialize)]
struct Manifest {
    entries: Vec<ManifestEntry>,
}

#[derive(Deserialize)]
struct ManifestEntry {
    corners: ManifestCorners,
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct ManifestCorners {
    top_left: String,
    top_right: String,
    bottom_left: String,
    bottom_right: String,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn unsupported_mountain_path_and_sand_pair_is_detectable() {
        assert!(!lpc_mapped_terrain_supports_tile_pair(
            TileKind::MountainPath,
            TileKind::Sand,
        ));
        assert!(lpc_mapped_terrain_supports_tile_pair(
            TileKind::Road,
            TileKind::Sand,
        ));
        assert!(lpc_mapped_terrain_supports_tile_pair(
            TileKind::MountainPath,
            TileKind::Road,
        ));
    }

    #[test]
    fn unsupported_mountain_path_and_sand_are_not_semantically_rewritten() {
        let mut map = TavernMap::empty_with(TileKind::Grass);
        map.set(10, 10, TileKind::MountainPath);
        map.set(11, 10, TileKind::Sand);

        let report =
            normalize_lpc_authored_material_contacts_region(&mut map, 10, 10, 11, 10);

        assert_eq!(report.total_mutations(), 0);
        assert_eq!(map.get(10, 10), TileKind::MountainPath);
        assert_eq!(map.get(11, 10), TileKind::Sand);
    }

    #[test]
    fn supported_contacts_remain_unchanged() {
        let mut map = TavernMap::empty_with(TileKind::Grass);
        map.set(10, 10, TileKind::MountainPath);
        map.set(11, 10, TileKind::PebbleShore);
        let before = map.tiles.clone();

        let report =
            normalize_lpc_authored_material_contacts_region(&mut map, 10, 10, 11, 10);

        assert_eq!(report.total_mutations(), 0);
        assert_eq!(map.tiles, before);
    }
}
