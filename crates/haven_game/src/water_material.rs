use haven_core::{TileKind, TILE_SIZE};
use macroquad::material::{
    gl_use_default_material, gl_use_material, load_material, Material, MaterialParams,
};
use macroquad::prelude::{draw_rectangle, Color, ShaderSource, UniformDesc, UniformType, WHITE};
use haven_world::water_render_mask::WaterRenderMask;
use haven_world::water_surface::resolve_water_surface_sample;

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
    // Pass 160D: pure shallow-water interiors only. Mixed shoreline cells are
    // rendered by the exact authored tuple atlas before this pass, so this
    // shader must never generate, clip, feather, or reinterpret a coastline.
    vec3 water = vec3(0.055, 0.285, 0.390);

    // Compatibility shader follows the same bounded world-space animation
    // contract as the LPC overlay. It never synthesizes shoreline topology.
    vec2 world = vec2(u_world_x, u_world_y) + uv * vec2(u_extent_x, u_extent_y);
    float variation = sin(world.x * 0.0021 + world.y * 0.0017 + u_time * 0.82) * 0.009;
    water += vec3(variation, variation * 1.15, variation * 1.25);
    gl_FragColor = vec4(water, 1.0);
}
"#;


#[derive(Clone, Copy, Debug, PartialEq)]
struct AnimatedWaterOverlayProfile {
    primary_offset: [f32; 2],
    secondary_offset: [f32; 2],
    primary_extent: [f32; 2],
    secondary_extent: [f32; 2],
    alpha: f32,
    caustic_alpha: f32,
    river_flow: bool,
}

fn animated_water_overlay_profile(
    tile: TileKind,
    world_x: i32,
    world_y: i32,
    time: f32,
    mask: WaterRenderMask,
) -> Option<AnimatedWaterOverlayProfile> {
    let sample = resolve_water_surface_sample(tile, world_x, world_y, time, mask)?;
    let river_flow = matches!(tile, TileKind::RiverWater | TileKind::RiverMouthBlend);
    let wave = sample.wave_phase.sin() * 0.5 + 0.5;
    let foam = sample.foam_phase.cos() * 0.5 + 0.5;
    let primary_x = 3.0 + wave * 17.0;
    let primary_y = 6.0 + foam * 13.0;
    let secondary_x = 6.0 + foam * 15.0;
    let secondary_y = 17.0 + wave * 8.0;
    let shallow_boost = (1.0 - sample.depth01) * 0.10;
    Some(AnimatedWaterOverlayProfile {
        primary_offset: [primary_x, primary_y],
        secondary_offset: [secondary_x, secondary_y],
        primary_extent: if river_flow { [1.0, 8.0] } else { [8.0, 1.0] },
        secondary_extent: if river_flow { [1.0, 5.0] } else { [5.0, 1.0] },
        alpha: (0.055 + sample.reflection_strength * 0.08 + shallow_boost).clamp(0.05, 0.17),
        caustic_alpha: (sample.caustic_strength * 0.10).clamp(0.01, 0.07),
        river_flow,
    })
}

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
                status: "shader-active",
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
        if tile_count == 0 {
            return false;
        }
        if !tile.is_water() {
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

    /// Pixel-art water motion layered over the authoritative LPC/V7 base.
    /// This never changes shoreline/depth semantics; it only consumes the
    /// existing renderer-neutral WaterSurfaceSample phases to add restrained
    /// world-space highlights/caustics. River water uses vertical flow streaks
    /// while ocean/pond water uses horizontal wavelets.
    pub(crate) fn draw_animation_overlay_tile(
        &self,
        tile: TileKind,
        world_x: i32,
        world_y: i32,
        px: f32,
        py: f32,
        time: f32,
        mask: WaterRenderMask,
        blend_layers: u8,
    ) {
        let Some(profile) = animated_water_overlay_profile(tile, world_x, world_y, time, mask) else {
            return;
        };
        let glint = if profile.river_flow {
            Color::new(0.62, 0.90, 0.94, profile.alpha)
        } else {
            Color::new(0.72, 0.93, 0.98, profile.alpha)
        };
        draw_rectangle(
            px + profile.primary_offset[0],
            py + profile.primary_offset[1],
            profile.primary_extent[0],
            profile.primary_extent[1],
            glint,
        );
        if blend_layers > 1 {
            draw_rectangle(
                px + profile.secondary_offset[0],
                py + profile.secondary_offset[1],
                profile.secondary_extent[0],
                profile.secondary_extent[1],
                Color::new(0.56, 0.86, 0.90, profile.caustic_alpha),
            );
        }
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


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn water_overlay_is_time_animated_without_changing_tile_semantics() {
        let mask = WaterRenderMask::default();
        let a = animated_water_overlay_profile(TileKind::OceanShallow, 10, 12, 1.0, mask).unwrap();
        let b = animated_water_overlay_profile(TileKind::OceanShallow, 10, 12, 2.0, mask).unwrap();
        assert_ne!(a.primary_offset, b.primary_offset);
        assert!(!a.river_flow);
    }

    #[test]
    fn river_overlay_uses_directional_flow_streaks() {
        let profile = animated_water_overlay_profile(
            TileKind::RiverWater,
            4,
            8,
            1.0,
            WaterRenderMask::default(),
        )
        .unwrap();
        assert!(profile.river_flow);
        assert!(profile.primary_extent[1] > profile.primary_extent[0]);
    }
}
