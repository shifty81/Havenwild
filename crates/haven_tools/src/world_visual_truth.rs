use haven_core::{GameWorld, ObjectKind, SceneKind, SceneMap};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

pub const WORLD_VISUAL_TRUTH_SCHEMA: &str = "havenwild.world_visual_truth_report.v2";

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SceneVisualTruthEntry {
    pub scene_id: String,
    pub kind: String,
    pub biome: String,
    pub dimensions: [usize; 2],
    pub terrain_signature: String,
    pub object_signature: String,
    pub tile_counts: BTreeMap<String, usize>,
    pub object_counts: BTreeMap<String, usize>,
    /// Exact authored/published asset identities where available; coarse ObjectKind is fallback only.
    pub semantic_asset_counts: BTreeMap<String, usize>,
    pub natural_object_count: usize,
    pub grass_tiles: usize,
    pub transition_count: usize,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct WorldVisualTruthReport {
    pub schema: String,
    pub scenes: Vec<SceneVisualTruthEntry>,
    /// Different scene identities sharing an exact spatial terrain signature.
    pub duplicate_terrain_groups: Vec<Vec<String>>,
    /// Exterior scenes with substantial grass but no tree/rock/forage population.
    pub natural_population_gaps: Vec<String>,
}

impl WorldVisualTruthReport {
    pub fn has_duplicate_world_composition(&self) -> bool {
        !self.duplicate_terrain_groups.is_empty()
    }

    pub fn has_population_gaps(&self) -> bool {
        !self.natural_population_gaps.is_empty()
    }

    pub fn status_lines(&self) -> Vec<String> {
        let mut lines = self
            .scenes
            .iter()
            .map(|scene| {
                format!(
                    "{} [{} / {}] {}x{} natural={} transitions={}",
                    scene.scene_id,
                    scene.kind,
                    scene.biome,
                    scene.dimensions[0],
                    scene.dimensions[1],
                    scene.natural_object_count,
                    scene.transition_count,
                )
            })
            .collect::<Vec<_>>();
        if !self.duplicate_terrain_groups.is_empty() {
            lines.push(format!(
                "Duplicate terrain composition groups: {}",
                self.duplicate_terrain_groups.len()
            ));
        }
        if !self.natural_population_gaps.is_empty() {
            lines.push(format!(
                "Natural population gaps: {}",
                self.natural_population_gaps.join(", ")
            ));
        }
        lines
    }
}

pub fn analyze_scene_visual_truth(scene: &SceneMap) -> SceneVisualTruthEntry {
    let mut tile_counts = BTreeMap::<String, usize>::new();
    let mut terrain_hash = Fnv64::new();
    terrain_hash.write(scene.id.as_str().as_bytes());
    terrain_hash.write(&(scene.dimensions.width as u64).to_le_bytes());
    terrain_hash.write(&(scene.dimensions.height as u64).to_le_bytes());

    for y in 0..scene.dimensions.height as i32 {
        for x in 0..scene.dimensions.width as i32 {
            let tile = scene.map.get(x, y);
            *tile_counts.entry(tile.code().to_string()).or_default() += 1;
            // Do not include the scene id in the comparison payload. It was mixed above only
            // for object-signature namespace stability; terrain comparison uses a second hash.
        }
    }

    let mut comparison_hash = Fnv64::new();
    comparison_hash.write(&(scene.dimensions.width as u64).to_le_bytes());
    comparison_hash.write(&(scene.dimensions.height as u64).to_le_bytes());
    for y in 0..scene.dimensions.height as i32 {
        for x in 0..scene.dimensions.width as i32 {
            comparison_hash.write(scene.map.get(x, y).code().as_bytes());
            comparison_hash.write(&[0]);
        }
    }

    let mut object_counts = BTreeMap::<String, usize>::new();
    let mut semantic_asset_counts = BTreeMap::<String, usize>::new();
    let mut natural_object_count = 0usize;
    let mut objects = scene
        .map
        .objects
        .iter()
        .map(|object| {
            let semantic_asset = scene
                .map
                .object_asset_ref(object.id)
                .map(|asset_ref| {
                    asset_ref
                        .scene_asset_alias_id()
                        .unwrap_or(asset_ref.asset_id.as_str())
                        .to_string()
                })
                .unwrap_or_else(|| object.kind.code().to_string());
            (
                object.x,
                object.y,
                object.kind.code().to_string(),
                semantic_asset,
            )
        })
        .collect::<Vec<_>>();
    objects.sort_unstable();
    for (x, y, kind, semantic_asset) in objects {
        *object_counts.entry(kind.clone()).or_default() += 1;
        *semantic_asset_counts
            .entry(semantic_asset.clone())
            .or_default() += 1;
        if is_natural_object_code(&kind) {
            natural_object_count += 1;
        }
        terrain_hash.write(&x.to_le_bytes());
        terrain_hash.write(&y.to_le_bytes());
        terrain_hash.write(kind.as_bytes());
        terrain_hash.write(&[0]);
        terrain_hash.write(semantic_asset.as_bytes());
        terrain_hash.write(&[0]);
    }

    SceneVisualTruthEntry {
        scene_id: scene.id.as_str().to_string(),
        kind: match scene.kind {
            SceneKind::Exterior => "exterior",
            SceneKind::Interior => "interior",
            SceneKind::Cave => "cave",
        }
        .to_string(),
        biome: scene.biome.code().to_string(),
        dimensions: [scene.dimensions.width, scene.dimensions.height],
        terrain_signature: comparison_hash.finish_hex(),
        object_signature: terrain_hash.finish_hex(),
        grass_tiles: tile_counts.get("grass").copied().unwrap_or(0),
        tile_counts,
        object_counts,
        semantic_asset_counts,
        natural_object_count,
        transition_count: scene.transitions.len(),
    }
}

pub fn analyze_world_visual_truth(world: &GameWorld) -> WorldVisualTruthReport {
    let scenes = world
        .scenes
        .iter()
        .map(analyze_scene_visual_truth)
        .collect::<Vec<_>>();

    let mut terrain_groups = BTreeMap::<String, Vec<String>>::new();
    for scene in &scenes {
        terrain_groups
            .entry(scene.terrain_signature.clone())
            .or_default()
            .push(scene.scene_id.clone());
    }
    let duplicate_terrain_groups = terrain_groups
        .into_values()
        .filter(|group| group.len() > 1)
        .collect::<Vec<_>>();

    let natural_population_gaps = scenes
        .iter()
        .filter(|scene| {
            scene.kind == "exterior"
                && scene.grass_tiles >= 64
                && scene.natural_object_count == 0
        })
        .map(|scene| scene.scene_id.clone())
        .collect::<Vec<_>>();

    WorldVisualTruthReport {
        schema: WORLD_VISUAL_TRUTH_SCHEMA.to_string(),
        scenes,
        duplicate_terrain_groups,
        natural_population_gaps,
    }
}

pub fn natural_object_codes() -> BTreeSet<&'static str> {
    [
        ObjectKind::Tree,
        ObjectKind::Bush,
        ObjectKind::Boulder,
        ObjectKind::OreNode,
        ObjectKind::Mushroom,
        ObjectKind::Herb,
        ObjectKind::Stump,
        ObjectKind::Log,
    ]
    .into_iter()
    .map(ObjectKind::code)
    .collect()
}

fn is_natural_object_code(code: &str) -> bool {
    natural_object_codes().contains(code)
}

#[derive(Clone, Copy)]
struct Fnv64(u64);
impl Fnv64 {
    fn new() -> Self {
        Self(0xcbf29ce484222325)
    }
    fn write(&mut self, bytes: &[u8]) {
        for byte in bytes {
            self.0 ^= u64::from(*byte);
            self.0 = self.0.wrapping_mul(0x100000001b3);
        }
    }
    fn finish_hex(self) -> String {
        format!("{:016x}", self.0)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use haven_core::{SceneBiome, SceneDimensions, StablePlaceableAssetRef, TileKind};

    #[test]
    fn identical_terrain_gets_same_signature_and_one_changed_tile_breaks_it() {
        let mut a = SceneMap::blank_sized(
            "visual_a",
            "A",
            SceneKind::Exterior,
            SceneBiome::Temperate,
            SceneDimensions::new(12, 10),
        )
        .unwrap();
        let mut b = SceneMap::blank_sized(
            "visual_b",
            "B",
            SceneKind::Exterior,
            SceneBiome::Temperate,
            SceneDimensions::new(12, 10),
        )
        .unwrap();
        assert_eq!(
            analyze_scene_visual_truth(&a).terrain_signature,
            analyze_scene_visual_truth(&b).terrain_signature
        );
        b.map.set(3, 4, TileKind::Dirt);
        assert_ne!(
            analyze_scene_visual_truth(&a).terrain_signature,
            analyze_scene_visual_truth(&b).terrain_signature
        );
        assert!(
            a.map.place_object(ObjectKind::Tree, 5, 5).is_some(),
            "tree acceptance fixture must place inside its complete 3x4 visual footprint",
        );
        assert_eq!(analyze_scene_visual_truth(&a).natural_object_count, 1);
    }

    #[test]
    fn exact_authored_asset_identity_changes_object_signature_without_changing_kind() {
        let mut a = SceneMap::blank_sized(
            "semantic_a",
            "A",
            SceneKind::Exterior,
            SceneBiome::Temperate,
            SceneDimensions::new(12, 10),
        )
        .unwrap();
        let mut b = SceneMap::blank_sized(
            "semantic_b",
            "B",
            SceneKind::Exterior,
            SceneBiome::Temperate,
            SceneDimensions::new(12, 10),
        )
        .unwrap();
        let a_id = a.map.place_object(ObjectKind::Tree, 5, 5).unwrap();
        let b_id = b.map.place_object(ObjectKind::Tree, 5, 5).unwrap();
        a.map.set_object_asset_ref(
            a_id,
            StablePlaceableAssetRef::from_scene_asset_alias("tree_oak_mature_01"),
        );
        b.map.set_object_asset_ref(
            b_id,
            StablePlaceableAssetRef::from_scene_asset_alias("tree_oak_mature_02"),
        );

        let a_truth = analyze_scene_visual_truth(&a);
        let b_truth = analyze_scene_visual_truth(&b);
        assert_eq!(a_truth.object_counts.get("tree"), Some(&1));
        assert_eq!(b_truth.object_counts.get("tree"), Some(&1));
        assert_eq!(
            a_truth.semantic_asset_counts.get("tree_oak_mature_01"),
            Some(&1)
        );
        assert_eq!(
            b_truth.semantic_asset_counts.get("tree_oak_mature_02"),
            Some(&1)
        );
        assert_ne!(a_truth.object_signature, b_truth.object_signature);
    }
}
