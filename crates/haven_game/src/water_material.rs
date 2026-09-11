use haven_core::{TileKind, TILE_SIZE};
use haven_world::water_render_mask::WaterRenderMask;
use macroquad::material::{
    gl_use_default_material, gl_use_material, load_material, Material, MaterialParams,
};
use macroquad::prelude::{draw_rectangle, ShaderSource, UniformDesc, UniformType, WHITE};

const WATER_VERTEX: &str = r#"#version 100
attribute vec3 position;
attribute vec2 texcoord;
attribute vec4 color0;
uniform mat4 Model;
uniform mat4 Projection;
varying lowp vec2 uv;
void main() {
    gl_Position = Projection * Model * vec4(position, 1.0);
    uv = texcoord;
}
"#;

const WATER_FRAGMENT: &str = r#"#version 100
precision lowp float;
varying lowp vec2 uv;
uniform float u_world_x;
uniform float u_world_y;
uniform float u_extent_x;
uniform float u_extent_y;
uniform float u_time;

void main() {
    vec3 water = vec3(0.055, 0.285, 0.390);
    vec2 world = vec2(u_world_x, u_world_y) + uv * vec2(u_extent_x, u_extent_y);
    float variation = sin(world.x * 0.0021 + world.y * 0.0017 + u_time * 0.82) * 0.009;
    water += vec3(variation, variation * 1.15, variation * 1.25);
    gl_FragColor = vec4(water, 1.0);
}
"#;

/// Water presentation runtime.
///
/// HW-VISUAL-WORLD-RESET-01 keeps the span-based material pass but retires the
/// old CPU per-water-tile glint/caustic rectangles. Those extra draw calls scaled
/// directly with visible water area and were observed to cause severe frame-time
/// degradation whenever water entered the camera.
pub(crate) struct WaterMaterialRuntime {
    material: Option<Material>,
    status: &'static str,
}

impl WaterMaterialRuntime {
    pub(crate) fn load() -> Self {
        let params = MaterialParams {
            uniforms: vec![
                UniformDesc::new("u_world_x", UniformType::Float1),
                UniformDesc::new("u_world_y", UniformType::Float1),
                UniformDesc::new("u_extent_x", UniformType::Float1),
                UniformDesc::new("u_extent_y", UniformType::Float1),
                UniformDesc::new("u_time", UniformType::Float1),
            ],
            ..Default::default()
        };
        match load_material(
            ShaderSource::Glsl {
                vertex: WATER_VERTEX,
                fragment: WATER_FRAGMENT,
            },
            params,
        ) {
            Ok(material) => Self {
                material: Some(material),
                status: "shader-active-span-only",
            },
            Err(_) => Self {
                material: None,
                status: "cpu-fallback-material-load",
            },
        }
    }

    pub(crate) const fn status(&self) -> &'static str {
        self.status
    }

    pub(crate) fn draw_interior_span(
        &self,
        tile: TileKind,
        world_x: i32,
        world_y: i32,
        px: f32,
        py: f32,
        tile_count: usize,
        animation_time: f32,
    ) -> bool {
        if tile_count == 0 || !tile.is_water() {
            return false;
        }
        let Some(material) = self.material.as_ref() else {
            return false;
        };
        self.draw_sample(
            material,
            (world_x, world_y),
            (px, py),
            (TILE_SIZE * tile_count as f32 + 0.20, TILE_SIZE + 0.20),
            animation_time,
        );
        true
    }

    /// Compatibility call retained for existing renderer call sites.
    ///
    /// Intentionally no-op: decorative water motion must be batched/retained in
    /// a later renderer pass, never emitted as one or two CPU rectangles per
    /// visible water tile.
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn draw_animation_overlay_tile(
        &self,
        _tile: TileKind,
        _world_x: i32,
        _world_y: i32,
        _px: f32,
        _py: f32,
        _time: f32,
        _mask: WaterRenderMask,
        _blend_layers: u8,
    ) {
    }

    fn draw_sample(
        &self,
        material: &Material,
        world: (i32, i32),
        screen: (f32, f32),
        size: (f32, f32),
        animation_time: f32,
    ) {
        let (world_x, world_y) = world;
        let (px, py) = screen;
        let (width, height) = size;
        material.set_uniform("u_world_x", world_x as f32 * TILE_SIZE);
        material.set_uniform("u_world_y", world_y as f32 * TILE_SIZE);
        material.set_uniform("u_extent_x", width);
        material.set_uniform("u_extent_y", height);
        material.set_uniform("u_time", animation_time);
        gl_use_material(material);
        draw_rectangle(px, py, width, height, WHITE);
        gl_use_default_material();
    }
}
