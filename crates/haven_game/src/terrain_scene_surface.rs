use macroquad::prelude::*;

use crate::base_terrain_cache::BaseTerrainChunkCache;
use crate::runtime_terrain_base_draw::TerrainBaseDrawRequest;
use crate::{Game, MAP_H, MAP_W, TILE_SIZE};
use haven_core::TavernMap;

/// GPU-owned terrain surface for the static semantic terrain layer.
///
/// The direct LPC path is baked once at native 32 px resolution and submitted
/// as one texture per frame. This removes thousands of per-cell submissions,
/// keeps all internal tile boundaries inside one texture, and is invalidated by
/// scene or semantic terrain revision changes. F3 itself does not disable the
/// retained surface; only tools that require live per-cell terrain inspection
/// (paint, zones, elevation/debug) fall back to the editable cell path.
#[derive(Debug, Default)]
pub(crate) struct TerrainSceneSurfaceCache {
    target: Option<RenderTarget>,
    scene_code: String,
    terrain_revision: u64,
    rebuilds: u64,
    draws: u64,
}

impl TerrainSceneSurfaceCache {
    fn needs_rebuild(&self, scene_code: &str, terrain_revision: u64) -> bool {
        self.target.is_none()
            || self.scene_code != scene_code
            || self.terrain_revision != terrain_revision
    }

    pub(crate) fn telemetry(&self) -> (bool, u64, u64) {
        (self.target.is_some(), self.rebuilds, self.draws)
    }

    fn ensure_target(&mut self) -> RenderTarget {
        if self.target.is_none() {
            let width = (MAP_W as f32 * TILE_SIZE).round() as u32;
            let height = (MAP_H as f32 * TILE_SIZE).round() as u32;
            let target = render_target(width, height);
            target.texture.set_filter(FilterMode::Nearest);
            self.target = Some(target);
        }
        self.target.as_ref().expect("terrain render target").clone()
    }
}

fn retained_surface_eligible(has_direct_lpc_source: bool, live_cell_editor_required: bool) -> bool {
    has_direct_lpc_source && !live_cell_editor_required
}

impl Game {
    pub(crate) fn draw_retained_terrain_scene_surface(
        &self,
        map: &TavernMap,
        base_cache: &BaseTerrainChunkCache,
        scene_code: &str,
        terrain_revision: u64,
        screen_origin: Vec2,
        live_cell_editor_required: bool,
    ) -> bool {
        // The retained surface remains valid while the lightweight F3 shell is
        // open. Only editor tools that need live per-cell terrain state request
        // the slower editable path.
        if !retained_surface_eligible(
            self.lpc_mapped_terrain_atlas.is_some(),
            live_cell_editor_required,
        ) {
            return false;
        }

        let (target, rebuild) = {
            let mut cache = self.terrain_scene_surface.borrow_mut();
            let rebuild = cache.needs_rebuild(scene_code, terrain_revision);
            (cache.ensure_target(), rebuild)
        };

        if rebuild {
            let scene = self.world.active();
            let width = MAP_W as f32 * TILE_SIZE;
            let height = MAP_H as f32 * TILE_SIZE;
            let mut target_camera = Camera2D::from_display_rect(Rect::new(0.0, 0.0, width, height));
            target_camera.render_target = Some(target.clone());
            set_camera(&target_camera);
            clear_background(Color::from_rgba(0, 0, 0, 0));

            for y in 0..MAP_H as i32 {
                for x in 0..MAP_W as i32 {
                    if !scene.is_renderable_cell(x, y) {
                        continue;
                    }
                    let tile = map.get(x, y);
                    let record = base_cache.record_at(x, y);
                    self.draw_tile_base(TerrainBaseDrawRequest {
                        map,
                        tile,
                        x,
                        y,
                        global: None,
                        screen: vec2(x as f32 * TILE_SIZE, y as f32 * TILE_SIZE),
                        resolved_base: record.and_then(|record| {
                            record
                                .resolved_group
                                .map(|group| (group, record.resolved_mask))
                        }),
                        mapped_entry: record.and_then(|record| record.mapped_entry),
                    });
                }
            }

            for y in 0..MAP_H as i32 {
                for x in 0..MAP_W as i32 {
                    if !scene.is_renderable_cell(x, y) {
                        continue;
                    }
                    let Some(entry) = base_cache
                        .record_at(x, y)
                        .and_then(|record| record.mapped_transition_entry)
                    else {
                        continue;
                    };
                    self.draw_mapped_terrain_tuple_overlay(
                        entry,
                        vec2(x as f32 * TILE_SIZE, y as f32 * TILE_SIZE),
                    );
                }
            }

            // The source-pure V7 mapped tuple atlas is the only terrain
            // transition authority in this retained surface. Generic and
            // ElizaWy overlays are deliberately excluded.

            for y in 0..MAP_H as i32 {
                for x in 0..MAP_W as i32 {
                    if !scene.is_renderable_cell(x, y)
                        || map.get(x, y) != haven_core::TileKind::GreenhouseZone
                    {
                        continue;
                    }
                    draw_rectangle_lines(
                        x as f32 * TILE_SIZE + 3.0,
                        y as f32 * TILE_SIZE + 3.0,
                        TILE_SIZE - 6.0,
                        TILE_SIZE - 6.0,
                        2.0,
                        Color::from_rgba(143, 239, 132, 220),
                    );
                }
            }

            // Restore the game camera before submitting the retained surface.
            set_camera(&self.game_camera());
            let mut cache = self.terrain_scene_surface.borrow_mut();
            cache.rebuilds = cache.rebuilds.saturating_add(1);
            cache.scene_code.clear();
            cache.scene_code.push_str(scene_code);
            cache.terrain_revision = terrain_revision;
        }

        {
            let mut cache = self.terrain_scene_surface.borrow_mut();
            cache.draws = cache.draws.saturating_add(1);
        }

        draw_texture_ex(
            &target.texture,
            screen_origin.x,
            screen_origin.y,
            WHITE,
            DrawTextureParams {
                dest_size: Some(vec2(MAP_W as f32 * TILE_SIZE, MAP_H as f32 * TILE_SIZE)),
                flip_y: true,
                ..Default::default()
            },
        );
        true
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn normal_gameplay_retains_terrain_even_when_editor_paint_cache_exists() {
        assert!(retained_surface_eligible(true, false));
        assert!(!retained_surface_eligible(true, true));
        assert!(!retained_surface_eligible(false, false));
    }

    #[test]
    fn cache_rebuild_contract_tracks_scene_and_revision() {
        let mut cache = TerrainSceneSurfaceCache::default();
        assert!(cache.needs_rebuild("a", 1));
        cache.scene_code = "a".to_string();
        cache.terrain_revision = 1;
        // No target still means cold.
        assert!(cache.needs_rebuild("a", 1));
        assert!(cache.needs_rebuild("b", 1));
        assert!(cache.needs_rebuild("a", 2));
    }
}
