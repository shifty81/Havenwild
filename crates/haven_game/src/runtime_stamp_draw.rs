use super::*;
use haven_core::PlacedStamp;

#[derive(Clone, Copy)]
struct StampDrawSpace {
    offset: Vec2,
    global_surface: bool,
}

impl StampDrawSpace {
    const LOCAL: Self = Self {
        offset: Vec2::ZERO,
        global_surface: false,
    };
}

impl Game {
    pub(super) fn draw_stamp(&self, stamp: &PlacedStamp) {
        self.draw_stamp_in_space(stamp, StampDrawSpace::LOCAL);
    }

    pub(super) fn draw_surface_stamp(&self, stamp: &PlacedStamp, chunk_x: i32, chunk_y: i32) {
        self.draw_stamp_in_space(
            stamp,
            StampDrawSpace {
                offset: vec2(
                    chunk_x as f32 * MAP_W as f32 * TILE_SIZE,
                    chunk_y as f32 * MAP_H as f32 * TILE_SIZE,
                ),
                global_surface: true,
            },
        );
    }

    fn draw_stamp_in_space(&self, stamp: &PlacedStamp, space: StampDrawSpace) {
        let Some(definition) = self.stamp_registry.entry(&stamp.stamp_key) else {
            self.draw_stamp_fallback(stamp, space);
            return;
        };
        let Some(texture) = self.stamp_textures.get(&definition.sheet) else {
            self.draw_stamp_fallback(stamp, space);
            return;
        };
        let rect = stamp.visual_rect();
        if let Some(expandable) = definition.expandable {
            self.draw_expandable_stamp(texture, expandable, rect, space);
            return;
        }
        let (x, y, w, h) = rect;
        let screen =
            self.stamp_world_to_screen(vec2(x as f32 * TILE_SIZE, y as f32 * TILE_SIZE), space);
        draw_texture_ex(
            texture,
            screen.x,
            screen.y,
            WHITE,
            DrawTextureParams {
                dest_size: Some(vec2(w as f32 * TILE_SIZE, h as f32 * TILE_SIZE)),
                source: Some(atlas_rect(definition.rect)),
                ..Default::default()
            },
        );
    }

    fn draw_expandable_stamp(
        &self,
        texture: &Texture2D,
        definition: haven_assets::stamp_registry::ExpandableStampDefinition,
        rect: (i32, i32, i32, i32),
        space: StampDrawSpace,
    ) {
        let (x, y, width, height) = rect;
        let width = width.max(definition.minimum_w);
        let height = height.max(definition.minimum_h);
        for cell_y in 0..height {
            for cell_x in 0..width {
                let screen = self.stamp_world_to_screen(
                    vec2(
                        (x + cell_x) as f32 * TILE_SIZE,
                        (y + cell_y) as f32 * TILE_SIZE,
                    ),
                    space,
                );
                for source in [
                    definition.base_fill_tile,
                    definition.source_rect_for_rect_cell(cell_x, cell_y, width, height),
                ] {
                    draw_texture_ex(
                        texture,
                        screen.x,
                        screen.y,
                        WHITE,
                        DrawTextureParams {
                            dest_size: Some(vec2(TILE_SIZE, TILE_SIZE)),
                            source: Some(atlas_rect(source)),
                            ..Default::default()
                        },
                    );
                }
            }
        }
    }

    fn draw_stamp_fallback(&self, stamp: &PlacedStamp, space: StampDrawSpace) {
        let (x, y, w, h) = stamp.visual_rect();
        let screen =
            self.stamp_world_to_screen(vec2(x as f32 * TILE_SIZE, y as f32 * TILE_SIZE), space);
        draw_rectangle(
            screen.x,
            screen.y,
            w as f32 * TILE_SIZE,
            h as f32 * TILE_SIZE,
            Color::from_rgba(118, 82, 56, 210),
        );
        draw_rectangle_lines(
            screen.x,
            screen.y,
            w as f32 * TILE_SIZE,
            h as f32 * TILE_SIZE,
            2.0,
            Color::from_rgba(255, 205, 124, 235),
        );
    }

    fn stamp_world_to_screen(&self, local: Vec2, space: StampDrawSpace) -> Vec2 {
        if space.global_surface {
            self.runtime_world_to_screen(local + space.offset)
        } else {
            self.world_to_screen(local)
        }
    }
}
