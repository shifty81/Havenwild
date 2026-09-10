use super::render_helpers::*;
use super::*;

impl EditorApp {
    pub(crate) fn draw(&mut self) {
        set_default_camera();
        gl_use_default_material();
        clear_background(editor_theme::colors::WINDOW_BG);

        let w = screen_width();
        let validation = self.model.validation_report();
        let layout = self.shell_layout();
        let graph_rect = layout.workspace_content;
        let active_title = self.active_document_title();

        draw_top_bar(
            w,
            self.viewport_mode,
            &active_title,
            self.active_document_dirty(),
            self.asset_studio_open,
        );
        // W63-W70 GUI closure: the permanent left project/library panel is retired.
        // Project hierarchy and every asset browser now live in the one canonical
        // right-side dock, leaving the center as the dominant infinite canvas.
        if self.workspace_shell.right_panel_visible {
            draw_panel(layout.right_panel, "Workspace Dock");
        }
        // W72C: the center is the CanvasWorkspace surface itself. Do not draw
        // a titled/sectioned panel here: that recreates a visual gutter and makes
        // Tool Rail and Layers are deliberate sibling panels; the authored canvas
        // owns the remaining center surface without another titled outer container.
        draw_rectangle(
            layout.center_panel.x,
            layout.center_panel.y,
            layout.center_panel.w,
            layout.center_panel.h,
            Color::new(0.055, 0.065, 0.075, 1.0),
        );
        draw_rectangle_lines(
            layout.center_panel.x,
            layout.center_panel.y,
            layout.center_panel.w,
            layout.center_panel.h,
            1.0,
            PANEL_EDGE,
        );

        // Reassert the native UI render state before entering a workspace.
        // Macroquad 0.4.14 does not expose QuadGl::flush; material and camera
        // ownership must therefore be normalized explicitly at each boundary.
        set_default_camera();
        gl_use_default_material();

        // W76I-W76N: DocumentTabBar is editor chrome inside the canonical
        // CanvasWorkspace. Pixel Studio draws its richer multi-document tabs itself;
        // every other studio consumes this shared row and therefore cannot be
        // overdrawn by rulers/canvas-local chrome.
        if !self.asset_studio_open { self.draw_workspace_document_tabs(); }

        if self.asset_studio_open {
            self.draw_assets_workspace(graph_rect);
        } else if !matches!(self.viewport_mode, EditorViewportMode::SceneMap | EditorViewportMode::PixelStudio)
            && self.workspace_document_is_closed(self.viewport_mode)
        {
            self.draw_closed_workspace_empty_state(graph_rect);
        } else {
        match self.viewport_mode {
            EditorViewportMode::RegionGraph => {
                self.draw_world_routes_workspace(graph_rect);
            }
            EditorViewportMode::SceneRectangles => {
                self.draw_scene_rectangles(graph_rect);
            }
            EditorViewportMode::SceneBank => {
                self.draw_scene_bank_workspace();
            }
            EditorViewportMode::SceneMap => {
                self.draw_scene_map(graph_rect);
            }
            EditorViewportMode::PixelStudio => {
                self.draw_pixel_canvas(graph_rect);
            }
            EditorViewportMode::AnimationStudio => {
                self.draw_animation_workspace(graph_rect);
            }
            EditorViewportMode::CharacterStudio => {
                self.draw_character_studio_workspace(graph_rect);
            }
            EditorViewportMode::LogicStudio => {
                self.draw_logic_workspace(graph_rect);
            }
            EditorViewportMode::SoundStudio => {
                self.draw_sound_workspace(graph_rect);
            }
        }
        }

        // W58/W79 universal canvas chrome only exists while the current workspace
        // owns an open document. A closed document view must not leave ghost tools
        // active over the explicit empty state.
        let canvas_document_open = !self.asset_studio_open && (matches!(self.viewport_mode, EditorViewportMode::SceneMap | EditorViewportMode::PixelStudio)
            || !self.workspace_document_is_closed(self.viewport_mode));
        if canvas_document_open {
            set_default_camera();
            gl_use_default_material();
            self.draw_canvas_tool_rack();
            self.draw_canvas_layer_rail();
            self.draw_canvas_tool_overlays();
            self.draw_canvas_view_controls_overlay();
            self.draw_shared_palette_overlay();
        }

        // Workspaces may use custom cameras/materials. Restore the shared UI
        // state before inspector and text rendering so tab switches cannot
        // leak dark/black text state into the surrounding editor chrome.
        set_default_camera();
        gl_use_default_material();
        self.draw_right_dock(&validation);
        // W76V GameMaker-style document chrome: floating tab overflow/recent
        // menus draw above the workspace and docks instead of being clipped by
        // the canvas they control.
        if !self.asset_studio_open { self.draw_workspace_document_tab_overlay(); }

        self.draw_workspace_bottom_dock(&layout, &validation);
        self.draw_workspace_splitters(&layout);
        self.draw_workspace_status_bar(&layout, &validation);

        // Floating workspace panels are true overlays. Draw them only after the
        // regular workspace, inspector, and status surfaces have finished so
        // they cannot be overdrawn by a later dock or leak primitive state into
        // surrounding editor text.
        set_default_camera();
        gl_use_default_material();
        if self.viewport_mode == EditorViewportMode::PixelStudio || self.canvas_supports_shared_palette() {
            super::pixel_color_panel::draw_pixel_color_popup(self);
        }

        set_default_camera();
        gl_use_default_material();
        if let Some(menu) = self.world_canvas_context_menu {
            world_canvas_context::draw_world_canvas_context_menu(menu);
        }
        if let Some(menu) = self.scene_asset_context_menu {
            scene_asset_context::draw(menu);
        }
        self.draw_editor_menus(w);
        self.draw_help_center();
        self.draw_asset_drag_preview();
        if let Some(dialog) = self.pixel_studio.new_dialog.as_ref() {
            pixel_new_document::draw_new_pixel_dialog(dialog);
        }
        self.draw_authoring_publish_panel();
        self.draw_world_terrain_material_browser();
        self.draw_editor_settings();
        self.draw_document_close_dialog();
        // W81: tooltip help is always the final non-modal overlay so Layers/Inspector cannot cover it.
        self.draw_global_tooltip_overlay();
    }

    #[allow(dead_code)]
    pub(crate) fn draw_node_list(&self, rect: Rect) {
        let mut y = rect.y;
        draw_editor_text("Click a node to select it", rect.x, y, 18.0, MUTED);
        y += 28.0;
        for node in &self.model.region_graph.nodes {
            let active = self.selection.primary_region_node_id() == Some(&node.id);
            let row_h = 42.0;
            let bg = if active { ACCENT } else { CONTROL_BG };
            draw_rectangle(rect.x, y - 18.0, rect.w, row_h, bg);
            draw_rectangle_lines(rect.x, y - 18.0, rect.w, row_h, 1.0, PANEL_EDGE);
            draw_editor_text(&node.label, rect.x + 10.0, y + 2.0, 20.0, TEXT);
            let scene = node
                .scene_id
                .as_ref()
                .map(ProjectSceneId::label)
                .unwrap_or_else(|| "future scene".to_string());
            draw_editor_text(
                &format!("{} | {}", node.kind.code(), scene),
                rect.x + 10.0,
                y + 20.0,
                14.0,
                MUTED,
            );
            y += row_h + 8.0;
        }
    }

}

include!("draw_scene_views.rs");
