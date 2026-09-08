use super::editor_text::draw_editor_text;

impl EditorApp {
    #[allow(dead_code)]
    pub(crate) fn draw_rectangle_list(&self, rect: Rect) {
        let Some(manifest) = &self.scene_rectangles else {
            draw_editor_text(
                "No world-surface manifest loaded",
                rect.x,
                rect.y,
                18.0,
                WARN,
            );
            return;
        };
        let mut y = rect.y;
        draw_section_header(
            Rect::new(rect.x, y, rect.w, 24.0),
            "Alderreach Partitions",
            Some("diagnostic storage partitions"),
        );
        y += 34.0;
        for (index, rectangle) in manifest.scene_rectangles.iter().enumerate().take(14) {
            let active = index == self.selected_rectangle;
            let row_h = 42.0;
            draw_list_row(
                Rect::new(rect.x, y - 18.0, rect.w, row_h),
                &rectangle.scene_id,
                Some(&format!(
                    "{}  •  {}  •  {}",
                    rectangle.landmass_name,
                    rectangle.kind,
                    self.scene_assignments
                        .assignment_for_rectangle(&rectangle.scene_id)
                        .map(|assignment| format!(
                            "{} ({}, {})",
                            assignment.scene_code, assignment.role, assignment.ownership
                        ))
                        .unwrap_or_else(|| "unassigned".to_string())
                )),
                active,
            );
            y += row_h + 8.0;
        }
    }

    pub(crate) fn draw_scene_map(&mut self, _rect: Rect) {
        if self.game_canvas_ui_active() {
            self.draw_game_canvas_ui_document();
            return;
        }
        if !self.scene_workspace_has_open_document() {
            self.draw_scene_workspace_empty_state();
            return;
        }
        let Some(scene) = self.model.world.scenes.get(self.selected_scene) else {
            let host = self.canvas_host_rect();
            draw_editor_text("No scene loaded", host.x + 16.0, host.y + 36.0, 22.0, WARN);
            return;
        };
        let content_host = self.canvas_workspace_layout().context_toolbar;
        let viewport = self.scene_canvas_viewport_rect();
        let bounds = self.scene_canvas_bounds();
        draw_canvas_toolbar(
            content_host,
            CanvasToolbarKind::SceneMap,
            self.scene_canvas.zoom_percent(),
            false,
            None,
        );
        self.draw_autotile_toolbar(content_host);
        draw_rectangle(
            viewport.x,
            viewport.y,
            viewport.w,
            viewport.h,
            Color::new(0.07, 0.08, 0.08, 1.0),
        );

        let camera = self.scene_canvas.camera(viewport, bounds);
        set_camera(&camera);
        let visible = self.scene_canvas.visible_world_rect(viewport, bounds);
        let visible_cells = self.scene_canvas.visible_grid_bounds(
            viewport,
            bounds,
            Vec2::ZERO,
            1.0,
            MAP_W as i32,
            MAP_H as i32,
        );
        if self.scene_show_grid && scene.kind == SceneKind::Exterior {
            draw_infinite_grid(visible, 1.0, 8, self.scene_canvas.zoom);
        }
        // A14AB2: snapshot semantic layer visibility before borrowing the
        // autotile/structural caches mutably. This keeps render visibility
        // independent from cache ownership and avoids borrowing `self` through
        // both mutable and immutable paths in the same draw submission.
        let scene_visibility = SceneCanvasLayerVisibility {
            terrain: self.canvas_layer_kind_visible(canvas_layers::CanvasLayerKind::Terrain),
            water: self.canvas_layer_kind_visible(canvas_layers::CanvasLayerKind::Water),
            roads_paths: self.canvas_layer_kind_visible(canvas_layers::CanvasLayerKind::RoadsPaths),
            structures: self.canvas_layer_kind_visible(canvas_layers::CanvasLayerKind::Structures),
            objects_props: self.canvas_layer_kind_visible(canvas_layers::CanvasLayerKind::Objects),
            structural_levels: self.canvas_layer_kind_visible(canvas_layers::CanvasLayerKind::StructuralLevels),
            gameplay: self.canvas_layer_kind_visible(canvas_layers::CanvasLayerKind::Zones),
            links: self.canvas_layer_kind_visible(canvas_layers::CanvasLayerKind::Links),
            visual_overrides: self.canvas_layer_kind_visible(canvas_layers::CanvasLayerKind::AuthoredPixels),
        };
        let show_structures = scene_visibility.structures;

        let scene_id = scene.id.clone();
        let cache = self
            .autotile_caches
            .entry(scene_id.clone())
            .or_insert_with(|| LiveAutotileCache::new(scene));
        cache.synchronize(scene);
        let structural_cache = self
            .structural_cliff_caches
            .entry(scene_id)
            .or_default();
        structural_cache.synchronize(scene);
        draw_scene_tilemap(SceneTilemapDraw {
            scene,
            cursor: Some((self.scene_cursor_x, self.scene_cursor_y)),
            layer_mode: self.scene_layer_mode,
            selection: &self.selection,
            layer_states: &self.scene_layers,
            autotile_cache: Some(cache),
            structural_cliff_bridge: structural_cache.bridge(),
            textures: &self.editor_textures,
            autotile_preview_enabled: self.autotile_preview_enabled,
            autotile_dirty_overlay: self.autotile_dirty_overlay,
            visible_cells,
            zoom: self.scene_canvas.zoom,
            visibility: scene_visibility,
            stamp_registry: &self.stamp_registry,
        });
        self.draw_active_scene_semantic_overlay(scene);
        if show_structures {
            self.draw_building_instance_previews(scene);
        }
        if self.scene_layer_mode == SceneLayerMode::Objects
            && self.scene_edit_tool == SceneEditTool::Place
        {
            if let Some(stamp_id) = self.selected_stamp_id.as_deref() {
                if let Some(definition) = self.stamp_registry.entry(stamp_id) {
                    let preview = definition.placed_at(self.scene_cursor_x, self.scene_cursor_y);
                    let issues = scene.map.placement_issues_for_stamp(&preview);
                    let tint = if issues.is_empty() { GOOD } else { WARN };
                    let _ = self.editor_textures.draw_stamp_ghost(
                        stamp_id,
                        self.scene_cursor_x,
                        self.scene_cursor_y,
                        0.58,
                    );
                    let (x, y, w, h) = preview.visual_rect();
                    draw_rectangle_lines(
                        x as f32,
                        y as f32,
                        w as f32,
                        h as f32,
                        0.14 / self.scene_canvas.zoom.max(0.20),
                        tint,
                    );
                }
            }
        }
        self.draw_selected_object_footprints();
        if let Some(preview) = self.scene_paste_preview_rect() {
            draw_rectangle(
                preview.min.x as f32,
                preview.min.y as f32,
                preview.width() as f32,
                preview.height() as f32,
                Color::new(GOOD.r, GOOD.g, GOOD.b, 0.16),
            );
            draw_rectangle_lines(
                preview.min.x as f32,
                preview.min.y as f32,
                preview.width() as f32,
                preview.height() as f32,
                0.18 / self.scene_canvas.zoom.max(0.20),
                GOOD,
            );
        }
        if let Some(preview) = self.scene_drag_preview_rect() {
            let color = match self.scene_drag.map(|drag| drag.kind) {
                Some(SceneCanvasDragKind::Rectangle) => WARN,
                Some(SceneCanvasDragKind::MoveSelection) => GOOD,
                _ => TEXT,
            };
            draw_rectangle(
                preview.min.x as f32,
                preview.min.y as f32,
                preview.width() as f32,
                preview.height() as f32,
                Color::new(color.r, color.g, color.b, 0.14),
            );
            draw_rectangle_lines(
                preview.min.x as f32,
                preview.min.y as f32,
                preview.width() as f32,
                preview.height() as f32,
                0.12 / self.scene_canvas.zoom.max(0.20),
                color,
            );
        }
        if self.scene_show_grid {
            draw_scene_grid_overlay(scene, self.scene_canvas.zoom);
        }
        set_default_camera();
        draw_canvas_rulers(viewport, visible, 1.0, "Tile");

        draw_rectangle_lines(
            viewport.x, viewport.y, viewport.w, viewport.h, 1.0, PANEL_EDGE,
        );
        // A14X: the canvas status/breadcrumb owns the upper-left while zoom/view
        // controls own the upper-right. Clip at the first control so the two
        // chrome surfaces can never overdraw one another on narrow windows.
        let view_controls_left = super::canvas_view::canvas_view_control_rect(viewport, 0).x;
        let status_width = (view_controls_left - viewport.x - 22.0).max(1.0);
        draw_scissored_text(
            &format!(
                "{} | {} | {} | live autotile {} | snapped 1x1 tile grid{}{}",
                scene.name,
                self.scene_layer_mode.label(),
                self.scene_edit_tool.label(),
                if self.autotile_preview_enabled {
                    "on"
                } else {
                    "off"
                },
                self.building_preview_label(scene)
                    .map(|label| format!(" | {label}"))
                    .unwrap_or_default(),
                if self.scene_paste_anchor.is_some() { " | PASTE PREVIEW" } else { "" }
            ),
            viewport.x + 10.0,
            viewport.y + 22.0,
            status_width,
            17.0,
            TEXT,
        );
    }

    pub(crate) fn scene_cell_at_mouse(&self) -> Option<(i32, i32)> {
        let viewport = self.scene_canvas_viewport_rect();
        let (mx, my) = mouse_position();
        let mouse = vec2(mx, my);
        if !viewport.contains(mouse) {
            return None;
        }
        let cell = self
            .scene_canvas
            .screen_to_grid_cell(viewport, self.scene_canvas_bounds(), mouse, 1.0);
        let x = cell.x;
        let y = cell.y;
        (x >= 0 && x < MAP_W as i32 && y >= 0 && y < MAP_H as i32).then_some((x, y))
    }

    pub(crate) fn draw_scene_rectangles(&self, _rect: Rect) {
        let Some(manifest) = &self.scene_rectangles else {
            let host = self.canvas_host_rect();
            draw_editor_text(
                "No world-surface manifest loaded",
                host.x + 16.0,
                host.y + 36.0,
                22.0,
                WARN,
            );
            return;
        };
        let content_host = self.canvas_workspace_layout().context_toolbar;
        let viewport = self.world_canvas_viewport_rect();
        let view_options = WorldSurfaceViewOptions {
            selected_index: self.selected_rectangle,
            selected_landmass_id: self.selected_landmass_id,
            show_entire_world: self.world_show_entire_world,
            show_partitions: self.world_show_partitions,
            show_objects: [
                canvas_layers::CanvasLayerKind::Vegetation,
                canvas_layers::CanvasLayerKind::Resources,
                canvas_layers::CanvasLayerKind::Structures,
                canvas_layers::CanvasLayerKind::Objects,
            ]
            .into_iter()
            .any(|kind| self.canvas_layer_kind_visible(kind)),
            show_terrain: self.canvas_layer_kind_visible(canvas_layers::CanvasLayerKind::Terrain),
            show_water: self.canvas_layer_kind_visible(canvas_layers::CanvasLayerKind::Water),
            show_roads_paths: self.canvas_layer_kind_visible(canvas_layers::CanvasLayerKind::RoadsPaths),
            show_vegetation: self.canvas_layer_kind_visible(canvas_layers::CanvasLayerKind::Vegetation),
            show_resources: self.canvas_layer_kind_visible(canvas_layers::CanvasLayerKind::Resources),
            show_structures: self.canvas_layer_kind_visible(canvas_layers::CanvasLayerKind::Structures),
            show_objects_props: self.canvas_layer_kind_visible(canvas_layers::CanvasLayerKind::Objects),
            show_visual_overrides: self.canvas_layer_kind_visible(canvas_layers::CanvasLayerKind::AuthoredPixels),
            show_zones: self.canvas_layer_kind_visible(canvas_layers::CanvasLayerKind::Zones),
            show_structural_levels: self.canvas_layer_kind_visible(canvas_layers::CanvasLayerKind::StructuralLevels),
            cursor: Some((self.world_cursor_x, self.world_cursor_y)),
            selection: self.world_selection,
            drag_preview: self.world_drag.map(WorldCanvasDrag::rect),
            paste_preview: self.world_paste_preview_rect(),
            asset_place_preview: self.world_asset_place_preview_rect(),
            connector_preview: self.world_structural_connector_preview().ok().map(|plan| plan.footprint),
            edit_tool: self.world_edit_tool,
            layer_mode: self.world_layer_mode,
            brush_radius: self.world_brush_radius,
        };
        draw_canvas_toolbar(
            content_host,
            CanvasToolbarKind::WorldScenes,
            self.world_canvas.zoom_percent(),
            self.world_canvas_pan_tool,
            Some(view_options),
        );
        draw_scene_rectangle_map(
            manifest,
            &self.scene_assignments,
            &self.model.world,
            &self.development_world_settings,
            self.development_world_semantic_bake.as_ref(),
            viewport,
            &self.world_canvas,
            &self.editor_textures,
            view_options,
        );
    }
}
