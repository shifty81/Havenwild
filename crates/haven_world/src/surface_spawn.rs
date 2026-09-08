//! Shared safe-spawn selection for continuous exterior surface partitions.
//!
//! Spawn coordinates are derived from the final semantic scene surface, never
//! from storage-chunk geometry. This is important for irregular coastlines:
//! a legacy "harbor" rectangle may now contain mostly or entirely marine water.

use haven_core::{SceneMap, MAP_H, MAP_W};

/// Returns the nearest dry, walkable cell to the center of a scene.
///
/// Stable cells with a small local neighborhood of dry walkable ground are
/// preferred so a player is not placed on a one-cell sand/grass sliver. If a
/// scene contains dry ground but no candidate meets that neighborhood test, the
/// nearest dry walkable cell remains a deterministic fallback.
pub fn nearest_stable_walkable_cell(scene: &SceneMap) -> Option<(i32, i32)> {
    let center_x = MAP_W as i32 / 2;
    let center_y = MAP_H as i32 / 2;
    let max_radius = MAP_W.max(MAP_H) as i32;
    let mut fallback = None;

    for radius in 0..=max_radius {
        for y in center_y - radius..=center_y + radius {
            for x in center_x - radius..=center_x + radius {
                if radius > 0
                    && x != center_x - radius
                    && x != center_x + radius
                    && y != center_y - radius
                    && y != center_y + radius
                {
                    continue;
                }
                if x < 0 || y < 0 || x >= MAP_W as i32 || y >= MAP_H as i32 {
                    continue;
                }
                let tile = scene.map.get(x, y);
                if tile.is_water() || !scene.is_cell_walkable(x, y) {
                    continue;
                }
                fallback.get_or_insert((x, y));
                if stable_walkable_neighborhood(scene, x, y) {
                    return Some((x, y));
                }
            }
        }
    }

    fallback
}

/// Assigns a safe scene-local spawn when dry walkable ground exists.
pub fn assign_nearest_stable_walkable_spawn(scene: &mut SceneMap) -> bool {
    let Some((x, y)) = nearest_stable_walkable_cell(scene) else {
        return false;
    };
    scene.spawn_x = x;
    scene.spawn_y = y;
    true
}

/// Whether a cell has enough nearby dry walkable support to be a comfortable
/// player start instead of an isolated shoreline pixel/sliver.
pub fn stable_walkable_neighborhood(scene: &SceneMap, x: i32, y: i32) -> bool {
    if x < 0 || y < 0 || x >= MAP_W as i32 || y >= MAP_H as i32 {
        return false;
    }
    let tile = scene.map.get(x, y);
    if tile.is_water() || !scene.is_cell_walkable(x, y) {
        return false;
    }

    let mut dry_walkable = 0usize;
    let mut sampled = 0usize;
    for ny in y - 1..=y + 1 {
        for nx in x - 1..=x + 1 {
            if nx < 0 || ny < 0 || nx >= MAP_W as i32 || ny >= MAP_H as i32 {
                continue;
            }
            sampled += 1;
            let neighbor = scene.map.get(nx, ny);
            if !neighbor.is_water() && scene.is_cell_walkable(nx, ny) {
                dry_walkable += 1;
            }
        }
    }
    dry_walkable >= sampled.min(5)
}

#[cfg(test)]
mod tests {
    use super::*;
    use haven_core::{ProjectSceneId, SceneBiome, SceneKind, SceneMap, TileKind};

    #[test]
    fn ocean_scene_with_supported_land_patch_gets_dry_spawn() {
        let mut scene = SceneMap::blank(
            ProjectSceneId::new("spawn_test"),
            "Spawn Test",
            SceneKind::Exterior,
            SceneBiome::Coastal,
        );
        for y in 0..MAP_H as i32 {
            for x in 0..MAP_W as i32 {
                scene.map.set(x, y, TileKind::OceanDeep);
            }
        }
        for y in 8..=10 {
            for x in 12..=14 {
                scene.map.set(x, y, TileKind::Grass);
            }
        }

        assert!(assign_nearest_stable_walkable_spawn(&mut scene));
        assert!(!scene.map.get(scene.spawn_x, scene.spawn_y).is_water());
        assert!(stable_walkable_neighborhood(
            &scene,
            scene.spawn_x,
            scene.spawn_y
        ));
    }

    #[test]
    fn all_ocean_scene_reports_no_safe_spawn() {
        let mut scene = SceneMap::blank(
            ProjectSceneId::new("ocean_spawn_test"),
            "Ocean Spawn Test",
            SceneKind::Exterior,
            SceneBiome::Coastal,
        );
        for y in 0..MAP_H as i32 {
            for x in 0..MAP_W as i32 {
                scene.map.set(x, y, TileKind::OceanDeep);
            }
        }
        assert!(!assign_nearest_stable_walkable_spawn(&mut scene));
    }
}
