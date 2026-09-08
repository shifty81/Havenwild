use super::*;
use haven_assets::asset_intake::repo_root_dir;
use haven_pixel::{PixelDocument, PixelLicense};
use std::path::PathBuf;

const WORKBENCH_ROOT: &str = "content/editor/terrain_transition_workbench";

fn slug(value: &str) -> String {
    value
        .chars()
        .map(|ch| if ch.is_ascii_alphanumeric() { ch.to_ascii_lowercase() } else { '_' })
        .collect::<String>()
        .split('_')
        .filter(|part| !part.is_empty())
        .collect::<Vec<_>>()
        .join("_")
}

pub(crate) fn terrain_repair_button_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + 364.0, (rect.w - 6.0) * 0.62, 26.0)
}

pub(crate) fn terrain_lab_button_rect(rect: Rect) -> Rect {
    let left = terrain_repair_button_rect(rect);
    Rect::new(left.x + left.w + 6.0, left.y, rect.w - left.w - 6.0, 26.0)
}

impl EditorApp {
    pub(crate) fn current_terrain_transition_material_pair(&self) -> Option<(String, String)> {
        let scene = self.model.world.scenes.get(self.selected_scene)?;
        let tuple = haven_world::semantic_tuple_at(&scene.map, self.scene_cursor_x, self.scene_cursor_y);
        let resolver = haven_world::embedded_terrain_tuple_resolver().ok()?;
        let mut materials = Vec::<String>::new();
        for ordinal in [tuple.top_left, tuple.top_right, tuple.bottom_left, tuple.bottom_right].into_iter().flatten() {
            let code = resolver.terrain_code(ordinal)?.to_string();
            if !materials.contains(&code) { materials.push(code); }
        }
        if materials.len() != 2 { return None; }
        materials.sort();
        Some((materials.remove(0), materials.remove(0)))
    }

    pub(crate) fn terrain_transition_repair_document_path(&self) -> Option<PathBuf> {
        let (a, b) = self.current_terrain_transition_material_pair()?;
        let path = repo_root_dir().join(WORKBENCH_ROOT).join("documents").join(format!("{}__{}.png", slug(&a), slug(&b)));
        path.is_file().then_some(path)
    }

    pub(crate) fn open_current_terrain_transition_repair_document(&mut self) -> bool {
        let Some(path) = self.terrain_transition_repair_document_path() else {
            self.status_message = "This exact material pair already has authored coverage or is not a two-material repair pair".to_string();
            return false;
        };
        let label = path.file_stem().and_then(|v| v.to_str()).unwrap_or("terrain transition repair").replace("__", " ↔ ");
        let document = match PixelDocument::load(&path, label, PixelLicense::default()) {
            Ok(document) => document,
            Err(error) => {
                self.status_message = format!("Unable to open transition repair document: {error}");
                return false;
            }
        };
        self.pixel_studio.open_document_session(document);
        self.pixel_studio.reset_authoring_defaults();
        self.pixel_studio.world_asset_context = None;
        self.pixel_studio.animation_context = None;
        self.pixel_studio.refresh_texture();
        self.viewport_mode = EditorViewportMode::PixelStudio;
        self.pixel_studio.frame_document(self.pixel_canvas_rect());
        self.status_message = format!("Opened W77 transition repair document {}. Locked layers are trace/reference examples; paint only author layers.", path.file_name().and_then(|v| v.to_str()).unwrap_or_default());
        true
    }

    pub(crate) fn reveal_terrain_transition_lab(&mut self) {
        self.status_message = "Terrain Transition Authoring Lab: content/worldgen/scenes/terrain_acceptance/terrain_transition_authoring_lab_w77.json (57 repair boards)".to_string();
    }
}
