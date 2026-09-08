use super::canvas_layers::CanvasLayerKind;
use super::tool_registry::UniversalTool;
use super::*;
use haven_assets::asset_intake::repo_root_dir;
use haven_pixel::PixelBrushSettings;
use image::{Rgba, RgbaImage};

const TILE_PIXELS: i32 = 32;

pub(crate) struct DirectVisualCanvasState {
    scene_id: ProjectSceneId,
    asset_path: String,
    image: RgbaImage,
    dirty: bool,
}

fn scene_slug(scene_id: &ProjectSceneId) -> String {
    let mut output = String::new();
    for ch in scene_id.code().chars() {
        if ch.is_ascii_alphanumeric() { output.push(ch.to_ascii_lowercase()); }
        else if !output.ends_with('_') { output.push('_'); }
    }
    output.trim_matches('_').to_string()
}

fn direct_asset_path(scene_id: &ProjectSceneId) -> String {
    format!("assets/source/original/world_overrides/direct_canvas/{}_visual.png", scene_slug(scene_id))
}

impl EditorApp {
    pub(crate) fn direct_visual_authoring_active(&self) -> bool {
        matches!(self.viewport_mode, EditorViewportMode::SceneMap | EditorViewportMode::SceneRectangles)
            && self.active_canvas_layer_kind() == Some(CanvasLayerKind::AuthoredPixels)
            && matches!(self.canvas_active_tool, UniversalTool::Paint | UniversalTool::Erase | UniversalTool::Pick)
    }

    fn ensure_direct_visual_state(&mut self, scene_id: ProjectSceneId) -> Result<(), String> {
        if self.direct_visual_canvas.as_ref().is_some_and(|state| state.scene_id == scene_id) {
            return Ok(());
        }
        let dimensions = self
            .model
            .world
            .scene_by_id(&scene_id)
            .map(|scene| scene.dimensions)
            .ok_or_else(|| format!("scene {} is no longer loaded", scene_id.label()))?;
        self.commit_direct_visual_canvas()?;
        let asset_path = direct_asset_path(&scene_id);
        let path = repo_root_dir().join(&asset_path);
        let width = (dimensions.width as u32) * TILE_PIXELS as u32;
        let height = (dimensions.height as u32) * TILE_PIXELS as u32;
        let image = image::open(&path)
            .ok()
            .map(|image| image.to_rgba8())
            .filter(|image| image.width() == width && image.height() == height)
            .unwrap_or_else(|| RgbaImage::new(width, height));
        self.direct_visual_canvas = Some(DirectVisualCanvasState { scene_id, asset_path, image, dirty: false });
        Ok(())
    }

    fn direct_visual_scene_pixel_at_mouse(&self) -> Option<(ProjectSceneId, i32, i32)> {
        let mouse = vec2(mouse_position().0, mouse_position().1);
        match self.viewport_mode {
            EditorViewportMode::SceneMap => {
                let viewport = self.scene_canvas_viewport_rect();
                if !viewport.contains(mouse) { return None; }
                let world = self.scene_canvas.screen_to_world(viewport, self.scene_canvas_bounds(), mouse);
                let px = (world.x * TILE_PIXELS as f32).floor() as i32;
                let py = (world.y * TILE_PIXELS as f32).floor() as i32;
                let scene_id = self.active_scene_id()?;
                let dimensions = self.model.world.scene_by_id(&scene_id)?.dimensions;
                let max_x = dimensions.width as i32 * TILE_PIXELS;
                let max_y = dimensions.height as i32 * TILE_PIXELS;
                (px >= 0 && py >= 0 && px < max_x && py < max_y).then_some((scene_id, px, py))
            }
            EditorViewportMode::SceneRectangles => {
                let manifest = self.scene_rectangles.as_ref()?;
                let bounds = self.world_canvas_bounds()?;
                let viewport = self.world_canvas_viewport_rect();
                if !viewport.contains(mouse) { return None; }
                let world = self.world_canvas.screen_to_world(viewport, bounds, mouse);
                let gx = world.x.floor() as i32;
                let gy = world.y.floor() as i32;
                let global = GridPos { x: gx, y: gy };
                let address = resolve_world_surface_cell(
                    manifest,
                    &self.scene_assignments,
                    &self.model.world,
                    self.selected_landmass_id,
                    global,
                ).ok()?;
                let frac_x = (world.x - world.x.floor()).clamp(0.0, 0.999_999);
                let frac_y = (world.y - world.y.floor()).clamp(0.0, 0.999_999);
                let px = address.local.x * TILE_PIXELS + (frac_x * TILE_PIXELS as f32).floor() as i32;
                let py = address.local.y * TILE_PIXELS + (frac_y * TILE_PIXELS as f32).floor() as i32;
                Some((address.scene_id, px, py))
            }
            _ => None,
        }
    }

    fn apply_direct_visual_point(&mut self, scene_id: ProjectSceneId, px: i32, py: i32) -> Result<bool, String> {
        self.ensure_direct_visual_state(scene_id)?;
        let tool = self.canvas_active_tool;
        if tool == UniversalTool::Pick {
            if let Some(state) = self.direct_visual_canvas.as_ref() {
                if px >= 0 && py >= 0 && (px as u32) < state.image.width() && (py as u32) < state.image.height() {
                    let color = state.image.get_pixel(px as u32, py as u32).0;
                    if color[3] > 0 {
                        self.pixel_studio.selected_color = color;
                        self.status_message = format!("Sampled visual override color #{:02X}{:02X}{:02X}{:02X}", color[0], color[1], color[2], color[3]);
                    } else {
                        self.status_message = "Sampled transparent visual-override pixel".to_string();
                    }
                }
            }
            return Ok(false);
        }
        let brush = PixelBrushSettings {
            kind: self.pixel_studio.brush_kind,
            size: self.pixel_studio.brush_size,
            opacity: self.pixel_studio.brush_opacity,
            density: self.pixel_studio.brush_density,
            angle_degrees: self.pixel_studio.brush_angle_degrees,
            spacing: 1,
        }.normalized();
        let radius = i32::from(brush.size);
        let color = if tool == UniversalTool::Erase { [0, 0, 0, 0] } else { self.pixel_studio.selected_color };
        let Some(state) = self.direct_visual_canvas.as_mut() else { return Ok(false); };
        let mut changed = false;
        for dy in -radius..=radius {
            for dx in -radius..=radius {
                if !brush.contains_offset((px, py), dx, dy) { continue; }
                let x = px + dx;
                let y = py + dy;
                if x < 0 || y < 0 || x as u32 >= state.image.width() || y as u32 >= state.image.height() { continue; }
                if state.image.get_pixel(x as u32, y as u32).0 != color {
                    state.image.put_pixel(x as u32, y as u32, Rgba(color));
                    changed = true;
                }
            }
        }
        state.dirty |= changed;
        Ok(changed)
    }

    pub(crate) fn update_direct_visual_authoring(&mut self, pointer_consumed: bool, canvas_pointer_consumed: bool) -> bool {
        if !self.direct_visual_authoring_active() { return false; }
        if !pointer_consumed && !canvas_pointer_consumed && is_mouse_button_down(MouseButton::Left) {
            if let Some((scene_id, px, py)) = self.direct_visual_scene_pixel_at_mouse() {
                match self.apply_direct_visual_point(scene_id, px, py) {
                    Ok(true) => self.status_message = format!("Direct visual edit {},{} | semantic terrain/collision unchanged", px, py),
                    Ok(false) => {},
                    Err(error) => self.status_message = format!("Direct visual edit failed: {error}"),
                }
            }
        }
        if is_mouse_button_released(MouseButton::Left) {
            if let Err(error) = self.commit_direct_visual_canvas() {
                self.status_message = format!("Direct visual publish failed: {error}");
            }
        }
        true
    }

    pub(crate) fn commit_direct_visual_canvas(&mut self) -> Result<(), String> {
        let Some(state) = self.direct_visual_canvas.as_mut() else { return Ok(()); };
        if !state.dirty { return Ok(()); }
        let output = repo_root_dir().join(&state.asset_path);
        if let Some(parent) = output.parent() {
            std::fs::create_dir_all(parent).map_err(|error| format!("visual override directory failed: {error}"))?;
        }
        state.image.save(&output).map_err(|error| format!("visual override PNG save failed: {error}"))?;
        let scene_id = state.scene_id.clone();
        let asset_path = state.asset_path.clone();
        let width = state.image.width();
        let height = state.image.height();
        let bytes = state.image.as_raw().clone();
        state.dirty = false;

        let tile_w = (width / TILE_PIXELS as u32) as i32;
        let tile_h = (height / TILE_PIXELS as u32) as i32;
        let override_value = haven_core::SceneVisualOverride::new(0, 0, tile_w, tile_h, asset_path.clone())?;
        let scene = self.model.world.scene_mut_by_id(&scene_id).ok_or_else(|| format!("scene {} is no longer loaded", scene_id.label()))?;
        scene.set_visual_override(override_value);
        self.editor_textures.install_world_visual_override_texture(asset_path.clone(), width, height, &bytes);
        let editor_world_path = development_session::editor_world_path();
        save_world_to_path(&editor_world_path.to_string_lossy(), &self.model.world)
            .map_err(|error| format!("visual override saved but world persistence failed: {error}"))?;
        self.status_message = format!("Published direct visual override for {} | gameplay semantics unchanged", scene_id.label());
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn scene_slug_is_path_safe_and_stable() {
        let id = ProjectSceneId::new("pcg:North Coast/Chunk +1,-2");
        let slug = scene_slug(&id);
        assert!(!slug.is_empty());
        assert!(slug.chars().all(|ch| ch.is_ascii_alphanumeric() || ch == '_'));
        assert!(!slug.contains("__"));
    }
}
