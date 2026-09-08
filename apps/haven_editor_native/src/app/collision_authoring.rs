use super::*;
use image::{Rgba, RgbaImage};
use serde::{Deserialize, Serialize};
use std::{fs, path::Path};

pub(crate) const COLLISION_OVERRIDE_REGISTRY_PATH: &str =
    "content/world/collision_overrides_v1.json";

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct CollisionOverrideRegistryFile {
    schema: String,
    entries: Vec<CollisionOverrideRegistryEntry>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct CollisionOverrideRegistryEntry {
    scene_id: String,
    local_rect: [i32; 4],
    revision: String,
    add_mask: String,
    subtract_mask: String,
}

impl EditorApp {
    /// W60E2: rasterize the actual current tile/object/stamp/building blocking truth into
    /// a locked Pixel Studio reference layer. Authored add/subtract masks sit above this.
    pub(crate) fn prepare_scene_collision_reference(
        &self,
        scene_id: &ProjectSceneId,
        local_rect: GridRect,
    ) -> Result<RgbaImage, String> {
        let scene = self
            .model
            .world
            .scene_by_id(scene_id)
            .ok_or_else(|| format!("Scene {} is not loaded", scene_id.code()))?;
        let width_px = (local_rect.width().max(1) as u32) * 32;
        let height_px = (local_rect.height().max(1) as u32) * 32;
        let mut image = RgbaImage::new(width_px, height_px);
        let buildings = self.resolved_building_instances_for_scene(scene);

        for tile in local_rect.cells() {
            let mut blocked = !scene.map.is_cell_walkable(tile.x, tile.y);
            if !blocked {
                for instance in &buildings {
                    let Some(recipe) = self.building_recipe_registry.entry(&instance.recipe_id) else { continue; };
                    let world_tile = [tile.x, tile.y];
                    if !instance.footprint_contains_world_tile(recipe, world_tile) { continue; }
                    let state = self
                        .building_preview_views
                        .get(&instance.id)
                        .copied()
                        .unwrap_or_else(|| super::building_instance_preview::building_preview_state_for_recipe(instance, recipe));
                    if instance.wall_blocks_world_tile(recipe, state.active_level, world_tile) {
                        blocked = true;
                        break;
                    }
                    if let Some(level) = recipe.level(state.active_level) {
                        let local = instance.local_tile(world_tile);
                        for opening in &level.openings {
                            if opening.tile != local || opening.kind != haven_assets::building_recipe::BuildingOpeningKind::Door {
                                continue;
                            }
                            let Some(definition) = self.placeable_registry.resolve_alias(&opening.asset_id) else {
                                blocked = true;
                                break;
                            };
                            let effective_state = self
                                .building_instance_registry
                                .effective_opening_state(&instance.id, opening);
                            if definition.footprint_for_state(effective_state).blocks_movement {
                                blocked = true;
                                break;
                            }
                        }
                    }
                    if blocked { break; }
                    if instance.furnishing_blocks_world_tile(
                        recipe,
                        &self.placeable_registry,
                        state.active_level,
                        world_tile,
                        |furnishing| {
                            self.building_instance_registry
                                .effective_furnishing_state(&instance.id, furnishing)
                                .map(str::to_string)
                        },
                    ) {
                        blocked = true;
                        break;
                    }
                }
            }
            if blocked {
                let start_x = ((tile.x - local_rect.min.x) * 32) as u32;
                let start_y = ((tile.y - local_rect.min.y) * 32) as u32;
                for py in start_y..start_y + 32 {
                    for px in start_x..start_x + 32 {
                        image.put_pixel(px, py, Rgba([255, 56, 72, 112]));
                    }
                }
            }
        }
        Ok(image)
    }
}

pub(crate) fn update_collision_override_registry(
    root: &Path,
    scene_id: &ProjectSceneId,
    local_rect: GridRect,
    revision: &str,
    add_mask: &str,
    subtract_mask: &str,
) -> Result<String, String> {
    let path = root.join(COLLISION_OVERRIDE_REGISTRY_PATH);
    let mut registry = if path.exists() {
        let text = fs::read_to_string(&path)
            .map_err(|error| format!("collision registry read failed: {error}"))?;
        serde_json::from_str::<CollisionOverrideRegistryFile>(&text)
            .map_err(|error| format!("collision registry parse failed: {error}"))?
    } else {
        CollisionOverrideRegistryFile {
            schema: "havenwild.collision_override_registry.v1".to_string(),
            entries: Vec::new(),
        }
    };
    let key = [local_rect.min.x, local_rect.min.y, local_rect.width(), local_rect.height()];
    registry.entries.retain(|entry| !(entry.scene_id == scene_id.code() && entry.local_rect == key));
    registry.entries.push(CollisionOverrideRegistryEntry {
        scene_id: scene_id.code().to_string(),
        local_rect: key,
        revision: revision.to_string(),
        add_mask: add_mask.to_string(),
        subtract_mask: subtract_mask.to_string(),
    });
    registry.entries.sort_by(|a, b| a.scene_id.cmp(&b.scene_id).then(a.local_rect.cmp(&b.local_rect)));
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|error| format!("collision registry directory failed: {error}"))?;
    }
    fs::write(&path, serde_json::to_string_pretty(&registry).map_err(|error| error.to_string())?)
        .map_err(|error| format!("collision registry write failed: {error}"))?;
    Ok(COLLISION_OVERRIDE_REGISTRY_PATH.to_string())
}
