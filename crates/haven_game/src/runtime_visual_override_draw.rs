use super::*;

impl Game {
    pub(super) fn draw_scene_visual_overrides(&self) {
        if self.active_surface_chunk_coord().is_some() {
            let manifest = haven_world::ContinuousSurfaceManifest::for_world(&self.world);
            for binding in &manifest.exterior_bindings {
                let Some(scene) = self.world.scene_by_id(&binding.scene_id) else { continue; };
                let origin_x = binding.chunk.x * MAP_W as i32;
                let origin_y = binding.chunk.y * MAP_H as i32;
                for entry in &scene.visual_overrides {
                    if entry.is_building_composite() { continue; }
                    let Some(texture) = self.world_visual_override_textures.get(&entry.asset_path) else { continue; };
                    let screen = self.runtime_world_to_screen(vec2(
                        (origin_x + entry.x) as f32 * TILE_SIZE,
                        (origin_y + entry.y) as f32 * TILE_SIZE,
                    ));
                    draw_texture_ex(
                        texture,
                        screen.x,
                        screen.y,
                        WHITE,
                        DrawTextureParams {
                            dest_size: Some(vec2(entry.w as f32 * TILE_SIZE, entry.h as f32 * TILE_SIZE)),
                            ..Default::default()
                        },
                    );
                }
            }
            return;
        }
        for entry in &self.world.active().visual_overrides {
            if entry.is_building_composite() { continue; }
            let Some(texture) = self.world_visual_override_textures.get(&entry.asset_path) else { continue; };
            let screen = self.world_to_screen(vec2(entry.x as f32 * TILE_SIZE, entry.y as f32 * TILE_SIZE));
            draw_texture_ex(
                texture, screen.x, screen.y, WHITE,
                DrawTextureParams {
                    dest_size: Some(vec2(entry.w as f32 * TILE_SIZE, entry.h as f32 * TILE_SIZE)),
                    ..Default::default()
                },
            );
        }
    }
}
