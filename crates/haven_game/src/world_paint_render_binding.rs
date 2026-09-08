use super::*;
use std::collections::BTreeMap;

// Pass 38: refresh_world_paint_render_cache_scene wraps resolve_world_paint_scene_transition_tile_details and persists the derived cache.

#[derive(Clone, Debug, Default)]
pub(crate) struct WorldPaintRenderBindingCache {
    pub scene_id: String,
    pub entries: BTreeMap<(i32, i32), Vec<WorldPaintTransitionTileResolution>>,
    pub status: String,
}

impl WorldPaintRenderBindingCache {
    pub fn empty() -> Self {
        Self {
            scene_id: String::new(),
            entries: BTreeMap::new(),
            status: "World paint render bindings idle".to_string(),
        }
    }

    pub fn get_layers(
        &self,
        scene_id: &str,
        x: i32,
        y: i32,
    ) -> Option<&Vec<WorldPaintTransitionTileResolution>> {
        if self.scene_id == scene_id {
            self.entries.get(&(x, y))
        } else {
            None
        }
    }

    pub fn has_drawable_scene_layers(&self, scene_id: &str) -> bool {
        self.scene_id == scene_id && !self.entries.is_empty()
    }

    pub fn has_drawable_layers(&self, scene_id: &str, x: i32, y: i32) -> bool {
        self.get_layers(scene_id, x, y).is_some_and(|layers| {
            layers.iter().any(|binding| {
                binding.selected_atlas_rect[2] > 0 && binding.selected_atlas_rect[3] > 0
            })
        })
    }

    pub fn cell_count(&self) -> usize {
        self.entries.len()
    }

    pub fn len(&self) -> usize {
        self.entries.values().map(|layers| layers.len()).sum()
    }
}


fn is_streamed_runtime_paint_refresh(reason: &str) -> bool {
    reason.starts_with("Startup paint render binding refresh")
        || reason.starts_with("Surface chunk render binding refresh")
        || reason.starts_with("Transition paint render binding refresh")
        || reason.starts_with("Scene jump paint render binding refresh")
}

#[cfg(test)]
mod h21a14ab6_tests {
    use super::is_streamed_runtime_paint_refresh;

    #[test]
    fn traversal_refreshes_are_classified_as_runtime_only() {
        for reason in [
            "Startup paint render binding refresh",
            "Surface chunk render binding refresh",
            "Transition paint render binding refresh",
            "Scene jump paint render binding refresh",
        ] {
            assert!(is_streamed_runtime_paint_refresh(reason), "{reason}");
        }
    }

    #[test]
    fn explicit_authoring_refreshes_remain_rebuild_capable() {
        for reason in [
            "Hotkey paint render binding refresh",
            "Before-save paint render binding refresh",
            "Post-load paint render binding refresh",
            "Development bridge paint refresh",
        ] {
            assert!(!is_streamed_runtime_paint_refresh(reason), "{reason}");
        }
    }
}

impl Game {
    pub(super) fn refresh_world_paint_render_bindings_for_active_scene(&mut self, reason: &str) {
        let scene_id = self.world.active_scene.code().to_string();

        // H21A14AB6: streamed exterior traversal must never enter the legacy
        // authoring cache rebuild/persist path. That path resolves paint
        // details, reloads the complete cache document, pretty-serializes it,
        // and writes it synchronously. Keeping it on a chunk boundary can turn
        // an otherwise cheap scene switch into a multi-frame hitch or apparent
        // freeze as the development world/cache grows. Explicit paint/editor
        // refreshes still use the authoring path below.
        let streamed_surface = haven_world::parse_generated_chunk_scene_id(
            self.world.active_scene.project_id(),
        )
        .is_some()
            || haven_world::parse_pcg_surface_scene_id(self.world.active_scene.project_id())
                .is_some();
        let traversal_refresh = is_streamed_runtime_paint_refresh(reason);
        if streamed_surface && traversal_refresh {
            self.world_paint_render_bindings = WorldPaintRenderBindingCache {
                scene_id: scene_id.clone(),
                entries: BTreeMap::new(),
                status: format!(
                    "{reason}: streamed runtime surface uses semantic terrain; synchronous world-paint cache rebuild skipped for {scene_id}"
                ),
            };
            self.world_paint_render_status = self.world_paint_render_bindings.status.clone();
            self.log.event(&self.world_paint_render_status);
            return;
        }

        let repo_root = runtime_root();
        match refresh_world_paint_render_cache_scene(
            repo_root,
            &self.save_paths.world_paint_material_state,
            &self.save_paths.world_paint_render_cache,
            &scene_id,
        ) {
            Ok(cache_scene) => {
                let mut entries = BTreeMap::new();
                let details = cache_scene.to_details();
                for resolution in details.resolutions {
                    entries
                        .entry((resolution.x, resolution.y))
                        .or_insert_with(Vec::new)
                        .push(resolution);
                }
                sort_binding_layers(&mut entries);
                let count = entries.len();
                self.world_paint_render_bindings = WorldPaintRenderBindingCache {
                    scene_id: scene_id.clone(),
                    entries,
                    status: format!(
                        "{reason}: {count} atlas-backed paint tile(s) bound for {scene_id}; cache persisted"
                    ),
                };
                self.world_paint_render_status = self.world_paint_render_bindings.status.clone();
                self.log.event(&self.world_paint_render_status);
            }
            Err(err) => {
                self.world_paint_render_bindings = WorldPaintRenderBindingCache {
                    scene_id,
                    entries: BTreeMap::new(),
                    status: format!(
                        "{reason}: paint render binding skipped; root={}, material_state={}, cache={} ({err})",
                        repo_root.display(),
                        self.save_paths.world_paint_material_state,
                        self.save_paths.world_paint_render_cache
                    ),
                };
                self.world_paint_render_status = self.world_paint_render_bindings.status.clone();
                self.log.event(&self.world_paint_render_status);
            }
        }
    }

    pub(super) fn draw_world_paint_atlas_layers_if_bound(
        &self,
        scene_id: &str,
        x: i32,
        y: i32,
        px: f32,
        py: f32,
    ) -> bool {
        let Some(texture) = &self.world_tile_atlas else {
            return false;
        };
        let Some(bindings) = self.world_paint_render_bindings.get_layers(scene_id, x, y) else {
            return false;
        };
        let mut drew_any = false;
        for binding in bindings {
            if binding.selected_atlas_rect[2] == 0 || binding.selected_atlas_rect[3] == 0 {
                continue;
            }
            draw_texture_ex(
                texture,
                px,
                py,
                WHITE,
                DrawTextureParams {
                    dest_size: Some(vec2(TILE_SIZE, TILE_SIZE)),
                    source: Some(Rect::new(
                        binding.selected_atlas_rect[0] as f32,
                        binding.selected_atlas_rect[1] as f32,
                        binding.selected_atlas_rect[2] as f32,
                        binding.selected_atlas_rect[3] as f32,
                    )),
                    ..Default::default()
                },
            );
            drew_any = true;
        }
        drew_any
    }
}

fn sort_binding_layers(
    entries: &mut BTreeMap<(i32, i32), Vec<WorldPaintTransitionTileResolution>>,
) {
    for layers in entries.values_mut() {
        layers.sort_by(|a, b| {
            world_paint_layer_render_order(&a.layer)
                .cmp(&world_paint_layer_render_order(&b.layer))
                .then(a.selected_tile_id.cmp(&b.selected_tile_id))
        });
    }
}
