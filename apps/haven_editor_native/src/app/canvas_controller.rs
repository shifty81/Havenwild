use super::*;
use super::canvas_view::{canvas_view_control_rect, draw_canvas_view_controls};

impl EditorApp {
    pub(crate) fn select_world_cell(&mut self, global: GridPos) -> bool {
        if self.world_show_entire_world {
            let landmass = self.scene_rectangles.as_ref()
                .and_then(|manifest| world_landmass_at_global_cell(manifest, global));
            if let Some(landmass_id) = landmass {
                self.selected_landmass_id = landmass_id;
            }
        }
        let Some(manifest) = &self.scene_rectangles else {
            return false;
        };
        for (index, rectangle) in manifest.scene_rectangles.iter().enumerate().rev() {
            if !rectangle_is_overworld_surface(rectangle)
                || rectangle.landmass_id != self.selected_landmass_id
            {
                continue;
            }
            let partition_rect = world_scene_grid_rect(manifest, rectangle);
            if !partition_rect.contains(vec2(global.x as f32 + 0.5, global.y as f32 + 0.5)) {
                continue;
            }
            let rectangle_id = rectangle.scene_id.clone();
            let local_x = global.x - partition_rect.x.floor() as i32;
            let local_y = global.y - partition_rect.y.floor() as i32;
            self.selected_rectangle = index;
            self.world_cursor_x = global.x;
            self.world_cursor_y = global.y;
            self.sync_assignment_cycles_to_selected_rectangle();
            let selected_scene_id = self
                .scene_assignments
                .assignment_for_rectangle(&rectangle_id)
                .and_then(|assignment| {
                    self.model
                        .world
                        .scene_by_id(&ProjectSceneId::new(assignment.scene_code.as_str()))
                        .map(|scene| scene.id.clone())
                });
            if let Some(scene_id) = selected_scene_id {
                self.selection.replace(
                    scene_id,
                    SelectionItem::Tile(GridPos {
                        x: local_x,
                        y: local_y,
                    }),
                );
            } else {
                self.selection.clear();
            }
            self.status_message = format!(
                "Global tile {}, {} | partition {} | local {}, {}",
                global.x, global.y, rectangle_id, local_x, local_y
            );
            return true;
        }
        false
    }


    pub(crate) fn main_viewport_rect(&self) -> Rect {
        self.shell_layout().workspace_content
    }

    pub(crate) fn inspector_content_rect(&self) -> Rect {
        super::right_dock::right_dock_content_rect(self.shell_layout().inspector_content)
    }

    pub(crate) fn canvas_host_rect(&self) -> Rect {
        let rect = self.main_viewport_rect();
        // W72D locked GUI geometry: Tool Rail and Layers are dedicated sibling
        // columns to the left. Only the authored canvas starts after those
        // columns. All three surfaces share identical top/bottom edges.
        let left = self.canvas_authoring_left_inset();
        Rect::new(
            rect.x + left,
            rect.y,
            (rect.w - left).max(1.0),
            rect.h,
        )
    }

    pub(crate) fn canvas_workspace_layout(&self) -> super::canvas_workspace::CanvasWorkspaceLayout {
        // H21-A14Y: Palette is a first-class bottom Canvas panel. Reserve its
        // height in the same layout calculation that owns tabs/toolbars/rulers so
        // it can never cover authored pixels, terrain, or canvas input.
        super::canvas_workspace::CanvasWorkspaceLayout::calculate(
            self.canvas_host_rect(),
            super::shared_palette::shared_palette_height(self),
        )
    }

    pub(crate) fn scene_canvas_viewport_rect(&self) -> Rect {
        self.canvas_workspace_layout().viewport
    }

    pub(crate) fn world_canvas_viewport_rect(&self) -> Rect {
        self.canvas_workspace_layout().viewport
    }

    pub(crate) fn scene_canvas_bounds(&self) -> Rect {
        Rect::new(0.0, 0.0, MAP_W as f32, MAP_H as f32)
    }

    pub(crate) fn world_canvas_bounds(&self) -> Option<Rect> {
        let manifest = self.scene_rectangles.as_ref()?;
        if self.world_show_entire_world {
            world_archipelago_overview_bounds(self.development_world_semantic_bake.as_ref()?)
        } else {
            world_scene_grid_bounds_for_landmass(manifest, self.selected_landmass_id)
        }
    }

    pub(crate) fn update_canvas_navigation(&mut self) -> bool {
        if self.game_canvas_ui_active() {
            return false;
        }
        let control = is_key_down(KeyCode::LeftControl) || is_key_down(KeyCode::RightControl);
        if control && is_key_pressed(KeyCode::Equal) {
            match self.viewport_mode {
                EditorViewportMode::SceneMap => self.scene_canvas.zoom_in_step(),
                EditorViewportMode::SceneRectangles => self.world_canvas.zoom_in_step(),
                EditorViewportMode::PixelStudio => self.pixel_studio.zoom_in(),
                _ => {}
            }
        }
        if control && is_key_pressed(KeyCode::Minus) {
            match self.viewport_mode {
                EditorViewportMode::SceneMap => self.scene_canvas.zoom_out_step(),
                EditorViewportMode::SceneRectangles => self.world_canvas.zoom_out_step(),
                EditorViewportMode::PixelStudio => self.pixel_studio.zoom_out(),
                _ => {}
            }
        }
        if control && is_key_pressed(KeyCode::Key0) {
            match self.viewport_mode {
                EditorViewportMode::SceneMap => self.scene_canvas.actual_size(),
                EditorViewportMode::SceneRectangles => self.world_canvas.actual_size(),
                EditorViewportMode::PixelStudio => {
                    self.pixel_studio.frame_document(self.pixel_canvas_rect())
                }
                _ => {}
            }
        }
        // W60E7: plain F belongs to the contextual Fill tool. Framing is
        // intentionally modifier-based (Shift+F for the current selection or
        // Pixel document, Ctrl+0 for the canvas scale reset) so navigation can
        // never fire in the same frame as a mutating Fill shortcut.

        let pointer = vec2(mouse_position().0, mouse_position().1);
        let shell_layout = self.shell_layout();
        if self.workspace_shell.bottom_dock_open && shell_layout.bottom_dock.contains(pointer) {
            return true;
        }

        match self.viewport_mode {
            EditorViewportMode::SceneMap => {
                let viewport = self.scene_canvas_viewport_rect();
                let bounds = self.scene_canvas_bounds();
                let consumed = self.scene_canvas.handle_navigation(
                    viewport,
                    bounds,
                    self.scene_edit_tool == SceneEditTool::Pan,
                );
                if consumed && mouse_wheel().1.abs() > f32::EPSILON {
                    self.status_message =
                        format!("Scene canvas zoom {:.0}%", self.scene_canvas.zoom_percent());
                }
                consumed
            }
            EditorViewportMode::SceneRectangles => {
                let Some(bounds) = self.world_canvas_bounds() else {
                    return false;
                };
                let viewport = self.world_canvas_viewport_rect();
                let consumed = self.world_canvas.handle_navigation(
                    viewport,
                    bounds,
                    self.world_canvas_pan_tool,
                );
                if consumed && mouse_wheel().1.abs() > f32::EPSILON {
                    self.status_message =
                        format!("World canvas zoom {:.0}%", self.world_canvas.zoom_percent());
                }
                consumed
            }
            // Scene Library is an adaptive screen-space collection, not a camera canvas.
            EditorViewportMode::SceneBank => false,
            EditorViewportMode::RegionGraph => false,
            EditorViewportMode::PixelStudio => self.update_pixel_studio_navigation(),
            EditorViewportMode::AnimationStudio => false,
            EditorViewportMode::CharacterStudio => false,
            EditorViewportMode::LogicStudio => false,
            EditorViewportMode::SoundStudio => false,
        }
    }

    pub(crate) fn draw_canvas_view_controls_overlay(&self) {
        if self.game_canvas_ui_active() { return; }
        let (viewport, zoom_percent) = match self.viewport_mode {
            EditorViewportMode::SceneMap => (self.scene_canvas_viewport_rect(), self.scene_canvas.zoom_percent()),
            EditorViewportMode::SceneRectangles => (self.world_canvas_viewport_rect(), self.world_canvas.zoom_percent()),
            EditorViewportMode::PixelStudio => (self.pixel_canvas_rect(), self.pixel_studio.zoom() * 100.0),
            _ => return,
        };
        draw_canvas_view_controls(viewport, zoom_percent);
    }

    pub(crate) fn handle_canvas_view_controls_click(&mut self, mx: f32, my: f32) -> bool {
        if self.game_canvas_ui_active() { return false; }
        let viewport = match self.viewport_mode {
            EditorViewportMode::SceneMap => self.scene_canvas_viewport_rect(),
            EditorViewportMode::SceneRectangles => self.world_canvas_viewport_rect(),
            EditorViewportMode::PixelStudio => self.pixel_canvas_rect(),
            _ => return false,
        };
        let point = vec2(mx, my);
        if !(0..5).any(|index| canvas_view_control_rect(viewport, index).contains(point)) {
            return false;
        }
        // Index 1 is the read-only zoom percentage label. It still owns the
        // click so authoring beneath the overlay can never receive it.
        let action = (0..5).find(|index| canvas_view_control_rect(viewport, *index).contains(point));
        match (self.viewport_mode, action) {
            (_, Some(1)) => {}
            (EditorViewportMode::SceneMap, Some(0)) => self.scene_canvas.zoom_out_step(),
            (EditorViewportMode::SceneMap, Some(2)) => self.scene_canvas.zoom_in_step(),
            (EditorViewportMode::SceneMap, Some(3)) => self.scene_canvas.actual_size(),
            (EditorViewportMode::SceneMap, Some(4)) => self.scene_canvas.reset(),
            (EditorViewportMode::SceneRectangles, Some(0)) => self.world_canvas.zoom_out_step(),
            (EditorViewportMode::SceneRectangles, Some(2)) => self.world_canvas.zoom_in_step(),
            (EditorViewportMode::SceneRectangles, Some(3)) => self.world_canvas.actual_size(),
            (EditorViewportMode::SceneRectangles, Some(4)) => self.world_canvas.reset(),
            (EditorViewportMode::PixelStudio, Some(0)) => self.pixel_studio.zoom_out(),
            (EditorViewportMode::PixelStudio, Some(2)) => self.pixel_studio.zoom_in(),
            (EditorViewportMode::PixelStudio, Some(3)) => self.pixel_studio.zoom_one_to_one(),
            (EditorViewportMode::PixelStudio, Some(4)) => self.pixel_studio.frame_document(viewport),
            _ => {}
        }
        self.status_message = match self.viewport_mode {
            EditorViewportMode::SceneMap => format!("Scene canvas zoom {:.0}%", self.scene_canvas.zoom_percent()),
            EditorViewportMode::SceneRectangles => format!("World canvas zoom {:.0}%", self.world_canvas.zoom_percent()),
            EditorViewportMode::PixelStudio => format!("Pixel canvas zoom {:.0}%", self.pixel_studio.zoom() * 100.0),
            _ => self.status_message.clone(),
        };
        true
    }

    pub(crate) fn handle_canvas_toolbar_click(&mut self, mx: f32, my: f32) -> bool {
        // W72A retires the full-width legacy canvas toolbar. Scene autotile
        // controls survive as a contextual bottom tray overlay. World view
        // toggles live in the canonical right Properties dock.
        self.viewport_mode == EditorViewportMode::SceneMap
            && !self.game_canvas_ui_active()
            && self.handle_autotile_toolbar_click(mx, my)
    }

}
