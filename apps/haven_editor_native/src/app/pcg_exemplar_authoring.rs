use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::time::{SystemTime, UNIX_EPOCH};

use serde::Serialize;

use super::*;

const PCG_EXEMPLAR_VERSION: u32 = 1;
const PCG_EXEMPLAR_ROOT: &str = "WORKSPACE/world_pcg/exemplars";

#[derive(Clone, Debug, Serialize)]
struct PcgExemplarRect {
    min_x: i32,
    min_y: i32,
    max_x: i32,
    max_y: i32,
    width: i32,
    height: i32,
}

#[derive(Clone, Debug, Serialize)]
struct PcgExemplarCell {
    dx: i32,
    dy: i32,
    global_x: i32,
    global_y: i32,
    partition: String,
    scene_id: String,
    local_x: i32,
    local_y: i32,
    biome: String,
    terrain: String,
    structural_level: Option<u8>,
    zone: String,
}

#[derive(Clone, Debug, Serialize)]
struct PcgExemplarObject {
    dx: i32,
    dy: i32,
    scene_id: String,
    object_id: String,
    kind: String,
}

#[derive(Clone, Debug, Serialize)]
struct PcgExemplarStamp {
    dx: i32,
    dy: i32,
    scene_id: String,
    stamp_id: String,
    stamp_key: String,
}

#[derive(Clone, Debug, Serialize)]
struct PcgExemplarBuilding {
    dx: i32,
    dy: i32,
    scene_id: String,
    instance_id: String,
    recipe_id: String,
    footprint: [u32; 2],
    interior_policy: String,
    separate_scene: bool,
}

#[derive(Clone, Debug, Serialize)]
struct PcgExemplarTransition {
    dx: i32,
    dy: i32,
    scene_id: String,
    transition_id: String,
    width: i32,
    height: i32,
    label: String,
    target: String,
    target_spawn_x: i32,
    target_spawn_y: i32,
}

#[derive(Clone, Debug, Serialize)]
struct PcgExemplarAdaptationPolicy {
    preserve_semantics_not_exact_pixels: bool,
    allow_biome_material_substitution: bool,
    allow_rotation_and_reflection_when_valid: bool,
    allow_spacing_variation: bool,
    preserve_transition_connectivity: bool,
    preserve_structural_relationships: bool,
}

#[derive(Clone, Debug, Serialize)]
struct PcgExemplarDocument {
    schema: String,
    version: u32,
    id: String,
    display_name: String,
    captured_unix_seconds: u64,
    landmass_id: i32,
    source_rect: PcgExemplarRect,
    resolved_cell_count: usize,
    unresolved_cell_count: usize,
    source_partitions: Vec<String>,
    terrain_counts: BTreeMap<String, usize>,
    structural_level_counts: BTreeMap<String, usize>,
    zone_counts: BTreeMap<String, usize>,
    biome_counts: BTreeMap<String, usize>,
    cells: Vec<PcgExemplarCell>,
    objects: Vec<PcgExemplarObject>,
    stamps: Vec<PcgExemplarStamp>,
    buildings: Vec<PcgExemplarBuilding>,
    transitions: Vec<PcgExemplarTransition>,
    enclosed_scene_targets: Vec<String>,
    authored_visual_override_assets: Vec<String>,
    adaptation_policy: PcgExemplarAdaptationPolicy,
    notes: Vec<String>,
}

fn count_label(counts: &mut BTreeMap<String, usize>, label: impl Into<String>) {
    *counts.entry(label.into()).or_insert(0) += 1;
}

fn exemplar_id(landmass_id: i32, selection: GridRect) -> String {
    format!(
        "authored_l{}_{}_{}_{}x{}",
        landmass_id,
        selection.min.x,
        selection.min.y,
        selection.width(),
        selection.height()
    )
}

fn rects_intersect(a_x: i32, a_y: i32, a_w: i32, a_h: i32, b: GridRect) -> bool {
    let a_max_x = a_x.saturating_add(a_w.saturating_sub(1));
    let a_max_y = a_y.saturating_add(a_h.saturating_sub(1));
    a_x <= b.max.x && a_max_x >= b.min.x && a_y <= b.max.y && a_max_y >= b.min.y
}

impl EditorApp {
    /// Capture the currently selected authored world area as semantic PCG reference data.
    /// The exemplar intentionally records terrain/structure/zones/objects/connectivity rather
    /// than baking exact rendered pixels. PCG can therefore adapt the authored design language
    /// to biome, topology, seed, and available space instead of stamping a screenshot.
    pub(crate) fn promote_world_selection_to_pcg_exemplar(&mut self) {
        if self.world_paste_anchor.is_some() {
            self.status_message =
                "Commit or cancel the movable paste preview before promoting a PCG exemplar"
                    .to_string();
            return;
        }
        let Some(selection) = self.world_selection else {
            self.status_message =
                "Select a world region first, then use Promote PCG to capture it as an exemplar"
                    .to_string();
            return;
        };
        let selected_cell_count = i64::from(selection.width()) * i64::from(selection.height());
        if selected_cell_count > 65_536 {
            self.status_message = format!(
                "PCG exemplar selection is too large ({} cells); capture smaller authored reference areas up to 65,536 cells",
                selected_cell_count
            );
            return;
        }
        let Some(manifest) = self.scene_rectangles.as_ref() else {
            self.status_message = "No world-surface manifest loaded".to_string();
            return;
        };

        let mut cells = Vec::new();
        let mut objects = Vec::new();
        let mut stamps = Vec::new();
        let mut buildings = Vec::new();
        let mut seen_buildings = BTreeSet::new();
        let mut transitions = Vec::new();
        let mut enclosed_scene_targets = BTreeSet::new();
        let mut partitions = BTreeSet::new();
        let mut visual_override_assets = BTreeSet::new();
        let mut terrain_counts = BTreeMap::new();
        let mut structural_level_counts = BTreeMap::new();
        let mut zone_counts = BTreeMap::new();
        let mut biome_counts = BTreeMap::new();
        let mut unresolved_cell_count = 0usize;

        for global in selection.cells() {
            let address = match resolve_world_surface_cell(
                manifest,
                &self.scene_assignments,
                &self.model.world,
                self.selected_landmass_id,
                global,
            ) {
                Ok(address) => address,
                Err(_) => {
                    unresolved_cell_count += 1;
                    continue;
                }
            };
            let Some(scene) = self.model.world.scene_by_id(&address.scene_id) else {
                unresolved_cell_count += 1;
                continue;
            };

            let terrain = scene.map.get(address.local.x, address.local.y).label().to_string();
            let structural_level = scene
                .map
                .get_structural_level(address.local.x, address.local.y);
            let zone = scene.zone_at(address.local.x, address.local.y).label().to_string();
            let biome = scene.biome.label().to_string();
            let scene_id = address.scene_id.label().to_string();
            let partition = address.rectangle_id.clone();

            count_label(&mut terrain_counts, terrain.clone());
            count_label(
                &mut structural_level_counts,
                structural_level
                    .map(|level| format!("level_{level}"))
                    .unwrap_or_else(|| "auto".to_string()),
            );
            count_label(&mut zone_counts, zone.clone());
            count_label(&mut biome_counts, biome.clone());
            partitions.insert(partition.clone());

            if let Some(index) = scene.map.object_at(address.local.x, address.local.y) {
                if let Some(object) = scene.map.objects.get(index) {
                    if object.x == address.local.x && object.y == address.local.y {
                        objects.push(PcgExemplarObject {
                            dx: global.x - selection.min.x,
                            dy: global.y - selection.min.y,
                            scene_id: scene_id.clone(),
                            object_id: format!("{:?}", object.id),
                            kind: object.kind.label().to_string(),
                        });
                    }
                }
            }

            if let Some(index) = scene.map.stamp_at(address.local.x, address.local.y) {
                if let Some(stamp) = scene.map.stamps.get(index) {
                    if stamp.x == address.local.x && stamp.y == address.local.y {
                        stamps.push(PcgExemplarStamp {
                            dx: global.x - selection.min.x,
                            dy: global.y - selection.min.y,
                            scene_id: scene_id.clone(),
                            stamp_id: format!("{:?}", stamp.id),
                            stamp_key: stamp.stamp_key.clone(),
                        });
                    }
                }
            }

            for building in self.resolved_building_instances_for_scene(scene) {
                if building.anchor_tile != [address.local.x, address.local.y]
                    || !seen_buildings.insert(building.id.clone())
                {
                    continue;
                }
                if let Some(recipe) = self.building_recipe_registry.entry(&building.recipe_id) {
                    buildings.push(PcgExemplarBuilding {
                        dx: global.x - selection.min.x,
                        dy: global.y - selection.min.y,
                        scene_id: scene_id.clone(),
                        instance_id: building.id.clone(),
                        recipe_id: building.recipe_id.clone(),
                        footprint: recipe.footprint,
                        interior_policy: recipe.persistence.interior_policy.clone(),
                        separate_scene: recipe.persistence.separate_scene,
                    });
                }
            }

            if let Some(transition) = scene.transition_at(address.local.x, address.local.y) {
                if transition.x == address.local.x && transition.y == address.local.y {
                    if self
                        .model
                        .world
                        .scene_by_id(transition.target.project_id())
                        .is_some_and(|target| matches!(target.kind, SceneKind::Interior | SceneKind::Cave))
                    {
                        enclosed_scene_targets.insert(transition.target.as_str().to_string());
                    }
                    transitions.push(PcgExemplarTransition {
                        dx: global.x - selection.min.x,
                        dy: global.y - selection.min.y,
                        scene_id: scene_id.clone(),
                        transition_id: format!("{:?}", transition.id),
                        width: transition.w,
                        height: transition.h,
                        label: transition.label.clone(),
                        target: transition.target.as_str().to_string(),
                        target_spawn_x: transition.spawn_x,
                        target_spawn_y: transition.spawn_y,
                    });
                }
            }

            for visual_override in &scene.visual_overrides {
                if rects_intersect(
                    visual_override.x,
                    visual_override.y,
                    visual_override.w,
                    visual_override.h,
                    GridRect::single(address.local),
                ) {
                    visual_override_assets.insert(visual_override.asset_path.clone());
                }
            }

            cells.push(PcgExemplarCell {
                dx: global.x - selection.min.x,
                dy: global.y - selection.min.y,
                global_x: global.x,
                global_y: global.y,
                partition,
                scene_id,
                local_x: address.local.x,
                local_y: address.local.y,
                biome,
                terrain,
                structural_level,
                zone,
            });
        }

        if cells.is_empty() {
            self.status_message =
                "The selected region does not resolve to any authored world-surface cells"
                    .to_string();
            return;
        }

        let id = exemplar_id(self.selected_landmass_id, selection);
        let captured_unix_seconds = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|duration| duration.as_secs())
            .unwrap_or(0);
        let document = PcgExemplarDocument {
            schema: "havenwild.pcg_exemplar".to_string(),
            version: PCG_EXEMPLAR_VERSION,
            id: id.clone(),
            display_name: format!(
                "Authored Exemplar {},{} ({}x{})",
                selection.min.x,
                selection.min.y,
                selection.width(),
                selection.height()
            ),
            captured_unix_seconds,
            landmass_id: self.selected_landmass_id,
            source_rect: PcgExemplarRect {
                min_x: selection.min.x,
                min_y: selection.min.y,
                max_x: selection.max.x,
                max_y: selection.max.y,
                width: selection.width(),
                height: selection.height(),
            },
            resolved_cell_count: cells.len(),
            unresolved_cell_count,
            source_partitions: partitions.into_iter().collect(),
            terrain_counts,
            structural_level_counts,
            zone_counts,
            biome_counts,
            cells,
            objects,
            stamps,
            buildings,
            transitions,
            enclosed_scene_targets: enclosed_scene_targets.into_iter().collect(),
            authored_visual_override_assets: visual_override_assets.into_iter().collect(),
            adaptation_policy: PcgExemplarAdaptationPolicy {
                preserve_semantics_not_exact_pixels: true,
                allow_biome_material_substitution: true,
                allow_rotation_and_reflection_when_valid: true,
                allow_spacing_variation: true,
                preserve_transition_connectivity: true,
                preserve_structural_relationships: true,
            },
            notes: vec![
                "Semantic reference/template for hybrid Havenwild PCG; exact pixel composition is not a generation stamp.".to_string(),
                "Terrain families, structural relationships, zones, objects, stamps, transitions, and biome context are captured from the in-memory Dev World authoring state.".to_string(),
                "Project-owned visual overrides are referenced for provenance only; downstream PCG should adapt semantic relationships to local biome/topology/seed.".to_string(),
            ],
        };

        let root = haven_assets::asset_intake::repo_root_dir();
        let directory = root.join(PCG_EXEMPLAR_ROOT);
        if let Err(error) = fs::create_dir_all(&directory) {
            self.status_message = format!("PCG exemplar directory creation failed: {error}");
            return;
        }
        let path = directory.join(format!("{id}.json"));
        let serialized = match serde_json::to_string_pretty(&document) {
            Ok(serialized) => serialized,
            Err(error) => {
                self.status_message = format!("PCG exemplar serialization failed: {error}");
                return;
            }
        };
        if let Err(error) = fs::write(&path, format!("{serialized}\n")) {
            self.status_message = format!("PCG exemplar save failed: {error}");
            return;
        }

        self.status_message = format!(
            "Promoted {}x{} authored selection to PCG exemplar {} | {} semantic cells | {} partitions{}",
            selection.width(),
            selection.height(),
            path.strip_prefix(&root).unwrap_or(&path).display(),
            document.resolved_cell_count,
            document.source_partitions.len(),
            if document.unresolved_cell_count > 0 {
                format!(" | {} unresolved cells skipped", document.unresolved_cell_count)
            } else {
                String::new()
            }
        );
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exemplar_id_is_stable_for_a_selection() {
        let selection = GridRect::from_points(GridPos { x: -4, y: 7 }, GridPos { x: 3, y: 10 });
        assert_eq!(exemplar_id(2, selection), "authored_l2_-4_7_8x4");
    }

    #[test]
    fn exemplar_rect_intersection_handles_single_cells() {
        let cell = GridRect::single(GridPos { x: 5, y: 5 });
        assert!(rects_intersect(4, 4, 2, 2, cell));
        assert!(!rects_intersect(6, 6, 2, 2, cell));
    }
}
