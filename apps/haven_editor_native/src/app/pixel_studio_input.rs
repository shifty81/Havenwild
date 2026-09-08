use super::pixel_color_panel::*;
use super::pixel_context_layout::{
    pixel_animation_cancel_return_rect, pixel_animation_focus_rect, pixel_animation_onion_rect,
    pixel_animation_save_return_rect, pixel_animation_tab_rect, pixel_asset_tab_rect,
};
use super::pixel_new_document::*;
use super::pixel_studio::*;
use super::pixel_studio_layout::*;
use super::render_helpers::cycle_index;
use super::*;
use haven_assets::asset_intake::{repo_root_dir, AssetIntakeTargetKind};
use haven_pixel::{PixelDocumentKind, PixelSelection, PixelTool};

impl EditorApp {
    pub(crate) fn update_pixel_studio_navigation(&mut self) -> bool {
        if self.viewport_mode != EditorViewportMode::PixelStudio {
            return false;
        }
        if self.pixel_studio.new_dialog.is_some() {
            return true;
        }
        let canvas = self.pixel_canvas_rect();
        let mouse = vec2(mouse_position().0, mouse_position().1);
        let library_rect = self.contextual_asset_browser_rect();
        if self.update_pixel_library_navigation(library_rect, mouse) {
            return true;
        }
        let control_down = is_key_down(KeyCode::LeftControl) || is_key_down(KeyCode::RightControl);
        let shift_down = is_key_down(KeyCode::LeftShift) || is_key_down(KeyCode::RightShift);
        if !control_down && !shift_down && is_key_pressed(KeyCode::X) {
            std::mem::swap(
                &mut self.pixel_studio.selected_color,
                &mut self.pixel_studio.background_color,
            );
            self.status_message = "Swapped foreground and background colors".to_string();
            return true;
        }
        if !control_down && !shift_down && is_key_pressed(KeyCode::D) {
            self.pixel_studio.selected_color = [0, 0, 0, 255];
            self.pixel_studio.background_color = [255, 255, 255, 255];
            self.status_message = "Reset foreground/background colors".to_string();
            return true;
        }
        if shift_down && is_key_pressed(KeyCode::F) {
            self.pixel_studio.frame_document(canvas);
            self.status_message = "Framed active pixel document".to_string();
            return true;
        }
        if canvas.contains(mouse) {
            let wheel = mouse_wheel().1;
            if wheel.abs() > 0.05 {
                let before = self.pixel_studio.screen_to_pixel(canvas, mouse);
                if wheel > 0.0 {
                    self.pixel_studio.zoom_in();
                } else {
                    self.pixel_studio.zoom_out();
                }
                if let (Some(pixel), Some(image)) = (before, self.pixel_studio.image_rect(canvas)) {
                    let after_screen = vec2(
                        image.x + (pixel.0 as f32 + 0.5) * self.pixel_studio.zoom(),
                        image.y + (pixel.1 as f32 + 0.5) * self.pixel_studio.zoom(),
                    );
                    self.pixel_studio.pan += mouse - after_screen;
                }
                self.status_message = format!("Pixel canvas zoom {:.3}x", self.pixel_studio.zoom());
                return true;
            }
            let pan_down = is_mouse_button_down(MouseButton::Middle)
                || (is_key_down(KeyCode::Space) && is_mouse_button_down(MouseButton::Left));
            if pan_down {
                let previous = self.pixel_studio.pan_drag.unwrap_or(mouse);
                self.pixel_studio.pan += mouse - previous;
                self.pixel_studio.pan_drag = Some(mouse);
                return true;
            }
        }
        if !(is_mouse_button_down(MouseButton::Middle)
            || is_key_down(KeyCode::Space) && is_mouse_button_down(MouseButton::Left))
        {
            self.pixel_studio.pan_drag = None;
        }
        false
    }

    pub(crate) fn update_pixel_studio_input(&mut self) {
        if self.viewport_mode != EditorViewportMode::PixelStudio {
            return;
        }
        if !self.pixel_studio.library_loaded {
            self.status_message = match self.pixel_studio.refresh_library() {
                Ok(count) => format!("Pixel Studio indexed {count} project assets"),
                Err(error) => format!("Pixel Studio library scan failed: {error}"),
            };
        }
        if self.handle_new_pixel_dialog_input() {
            return;
        }
        if self.handle_pixel_layer_rename_input() {
            return;
        }
        if let Some(Err(error)) = self.pixel_studio.update_autosave() {
            self.pixel_studio.autosave_status = format!("Autosave failed: {error}");
            self.status_message = self.pixel_studio.autosave_status.clone();
        }
        let control = is_key_down(KeyCode::LeftControl) || is_key_down(KeyCode::RightControl);
        let shift = is_key_down(KeyCode::LeftShift) || is_key_down(KeyCode::RightShift);
        if control && shift && is_key_pressed(KeyCode::C) {
            self.status_message = match self.pixel_studio.copy_selection_to_clipboard(true) {
                Ok(message) => format!("{message} | merged visible selection"),
                Err(error) => format!("Copy merged failed: {error}"),
            };
            return;
        }
        if control && shift && is_key_pressed(KeyCode::P) {
            self.status_message = match self.pixel_studio.open_promote_selection_wizard() {
                Ok(message) => message,
                Err(error) => format!("Promote Selection failed: {error}"),
            };
            return;
        }
        if control && !shift && is_key_pressed(KeyCode::C) {
            self.status_message = match self.pixel_studio.copy_selection_to_clipboard(false) {
                Ok(message) => message,
                Err(error) => format!("Copy failed: {error}"),
            };
            return;
        }
        if control && !shift && is_key_pressed(KeyCode::X) {
            self.status_message = match self.pixel_studio.cut_selection_to_clipboard() {
                Ok(message) => message,
                Err(error) => format!("Cut failed: {error}"),
            };
            return;
        }
        if control && !shift && is_key_pressed(KeyCode::V) {
            self.status_message = match self.pixel_studio.paste_clipboard_into_selection() {
                Ok(message) => format!("{message} | use the Transform Gizmo to reposition"),
                Err(error) => format!("Paste failed: {error}"),
            };
            return;
        }
        if control && !shift && is_key_pressed(KeyCode::D) {
            self.status_message = match self.pixel_studio.duplicate_selection() {
                Ok(message) => message,
                Err(error) => format!("Duplicate failed: {error}"),
            };
            return;
        }
        if control && shift && is_key_pressed(KeyCode::H) {
            if let Some(document) = self.pixel_studio.document.as_mut() { document.flip_selection_horizontal(); }
            self.pixel_studio.refresh_texture();
            self.status_message = "Flipped marquee horizontally".to_string();
            return;
        }
        if control && shift && is_key_pressed(KeyCode::V) {
            if let Some(document) = self.pixel_studio.document.as_mut() { document.flip_selection_vertical(); }
            self.pixel_studio.refresh_texture();
            self.status_message = "Flipped marquee vertically".to_string();
            return;
        }
        if control && shift && is_key_pressed(KeyCode::R) {
            let changed = self.pixel_studio.document.as_mut().is_some_and(|d| d.rotate_selection_clockwise());
            if changed { self.pixel_studio.refresh_texture(); self.status_message = "Rotated marquee 90 degrees clockwise".to_string(); }
            return;
        }
        if !control && shift && is_key_pressed(KeyCode::O) {
            let changed = self.pixel_studio.document.as_mut().is_some_and(|d| d.select_opaque_bounds());
            if changed { self.status_message = "Selected opaque bounds on active layer".to_string(); }
            return;
        }
        if !control && shift && is_key_pressed(KeyCode::C) {
            let color = self.pixel_studio.selected_color;
            let changed = self.pixel_studio.document.as_mut().is_some_and(|d| d.select_color_bounds(color));
            if changed { self.status_message = "Selected bounds of foreground color".to_string(); }
            return;
        }
        if !control && shift && is_key_pressed(KeyCode::T) {
            self.pixel_studio.repeat_preview_mode = self.pixel_studio.repeat_preview_mode.next();
            self.pixel_studio.show_repeat_preview = self.pixel_studio.repeat_preview_mode != RepeatPreviewMode::Off;
            self.status_message = format!("Repeat preview: {}", self.pixel_studio.repeat_preview_mode.label());
            return;
        }
        if !control && shift && is_key_pressed(KeyCode::A) {
            if let (Some(point), Some(document)) = (self.pixel_studio.screen_to_pixel(self.pixel_canvas_rect(), vec2(mouse_position().0, mouse_position().1)), self.pixel_studio.document.as_ref()) {
                self.pixel_studio.symmetry_axis_x = Some(point.0.min(document.width().saturating_sub(1)));
                self.pixel_studio.symmetry_axis_y = Some(point.1.min(document.height().saturating_sub(1)));
                self.status_message = format!("Symmetry axes moved to {}, {}", point.0, point.1);
            }
            return;
        }
        if !control && shift && (is_key_pressed(KeyCode::Left) || is_key_pressed(KeyCode::Right) || is_key_pressed(KeyCode::Up) || is_key_pressed(KeyCode::Down)) {
            let dx = if is_key_pressed(KeyCode::Left) { -1 } else if is_key_pressed(KeyCode::Right) { 1 } else { 0 };
            let dy = if is_key_pressed(KeyCode::Up) { -1 } else if is_key_pressed(KeyCode::Down) { 1 } else { 0 };
            let changed = self.pixel_studio.document.as_mut().is_some_and(|d| d.nudge_selection(dx, dy));
            if changed { self.pixel_studio.refresh_texture(); self.status_message = format!("Nudged marquee by {}, {}", dx, dy); }
            return;
        }
        if !control && shift && is_key_pressed(KeyCode::H) {
            self.pixel_studio.symmetry_horizontal = !self.pixel_studio.symmetry_horizontal;
            self.status_message = format!("Horizontal symmetry {}", if self.pixel_studio.symmetry_horizontal { "on" } else { "off" });
        }
        if !control && shift && is_key_pressed(KeyCode::V) {
            self.pixel_studio.symmetry_vertical = !self.pixel_studio.symmetry_vertical;
            self.status_message = format!("Vertical symmetry {}", if self.pixel_studio.symmetry_vertical { "on" } else { "off" });
        }
        if shift && is_key_pressed(KeyCode::LeftBracket) {
            self.pixel_studio.adjust_brush_size(-1);
            self.status_message = format!("Pixel pencil size: {}px", self.pixel_studio.brush_size);
        }
        if shift && is_key_pressed(KeyCode::RightBracket) {
            self.pixel_studio.adjust_brush_size(1);
            self.status_message = format!("Pixel pencil size: {}px", self.pixel_studio.brush_size);
        }
        if control && is_key_pressed(KeyCode::N) {
            self.pixel_studio.open_new_dialog();
            self.status_message = "New Pixel Studio asset".to_string();
            return;
        }
        if control && is_key_pressed(KeyCode::O) {
            self.status_message = match self.pixel_studio.refresh_library() {
                Ok(count) if count > 0 => {
                    format!("Choose an asset from the right Assets dock ({count} available)")
                }
                Ok(_) => "No editable project assets were found".to_string(),
                Err(error) => format!("Pixel Studio open scan failed: {error}"),
            };
            return;
        }
        if control && is_key_pressed(KeyCode::S) {
            if self.pixel_studio.world_region_context.is_some() {
                self.save_world_region_pixels(false);
            } else {
                self.save_pixel_document();
            }
            return;
        }
        if control && is_key_pressed(KeyCode::Enter) {
            if self.pixel_studio.world_region_context.is_some() {
                self.save_world_region_pixels(true);
                return;
            }
            if self.pixel_studio.world_asset_context.is_some() {
                self.save_world_asset_pixels_and_return();
                return;
            }
            if self.pixel_studio.animation_context.is_some() {
                self.save_animation_pixels_and_return();
                return;
            }
        }
        if control
            && is_key_pressed(KeyCode::Z)
            && self
                .pixel_studio
                .document
                .as_mut()
                .is_some_and(|document| document.undo())
        {
            self.pixel_studio.refresh_texture();
            self.status_message = "Pixel edit undone".to_string();
        }
        if control
            && (is_key_pressed(KeyCode::Y)
                || (is_key_down(KeyCode::LeftShift) && is_key_pressed(KeyCode::Z)))
            && self
                .pixel_studio
                .document
                .as_mut()
                .is_some_and(|document| document.redo())
        {
            self.pixel_studio.refresh_texture();
            self.status_message = "Pixel edit redone".to_string();
        }
        if is_key_pressed(KeyCode::Escape) {
            self.transform_gizmo_drag = None;
            self.pixel_studio.grid_realign_armed = false;
            self.pixel_studio.grid_realign_enabled = false;
            self.pixel_studio.drag_start = None;
            self.pixel_studio.drag_current = None;
            self.pixel_studio.stroke_started = false;
            self.pixel_studio.tool = haven_pixel::PixelTool::Selection;
            self.status_message = "Cancelled Pixel Studio gesture; Select is active".to_string();
        }
        if !shift && is_key_pressed(KeyCode::LeftBracket) {
            self.pixel_studio.zoom_out();
        }
        if !shift && is_key_pressed(KeyCode::RightBracket) {
            self.pixel_studio.zoom_in();
        }
        if is_key_pressed(KeyCode::Up) {
            self.cycle_pixel_library(-1);
        }
        if is_key_pressed(KeyCode::Down) {
            self.cycle_pixel_library(1);
        }
        if is_key_pressed(KeyCode::Enter) && self.pixel_studio.document.is_none() {
            self.open_selected_pixel_library_entry();
        }

        let canvas = self.pixel_canvas_rect();
        let mouse = vec2(mouse_position().0, mouse_position().1);
        if self.transform_gizmo_drag.is_some() {
            let document_size = self
                .pixel_studio
                .document
                .as_ref()
                .map(|document| [document.width(), document.height()])
                .unwrap_or([1, 1]);
            if is_mouse_button_down(MouseButton::Left) {
                if let Some(drag) = self.transform_gizmo_drag.as_mut() {
                    transform_gizmo::update_pixel_transform_drag(
                        drag,
                        mouse,
                        self.pixel_studio.zoom(),
                        document_size,
                        shift,
                    );
                    if drag.handle.label() == "Rotate" && shift {
                        drag.preview_rotation_degrees =
                            (drag.preview_rotation_degrees / 15.0).round() * 15.0;
                    }
                    self.status_message = format!(
                        "{} | {}x{} at {}, {} | pivot {:.1}, {:.1} | rotation {:.1}°",
                        drag.handle.label(),
                        drag.preview_selection.width,
                        drag.preview_selection.height,
                        drag.preview_selection.x,
                        drag.preview_selection.y,
                        drag.preview_pivot[0],
                        drag.preview_pivot[1],
                        drag.preview_rotation_degrees,
                    );
                }
                return;
            }
            if is_mouse_button_released(MouseButton::Left) {
                if let Some(drag) = self.transform_gizmo_drag.take() {
                    let mut changed = false;
                    if let Some(document) = self.pixel_studio.document.as_mut() {
                        match drag.handle {
                            transform_gizmo::TransformGizmoHandle::Pivot => {
                                let next = [
                                    drag.preview_pivot[0].round() as i32,
                                    drag.preview_pivot[1].round() as i32,
                                ];
                                if document.metadata.pivot != next {
                                    document.begin_edit();
                                    document.metadata.pivot = next;
                                    document.dirty = true;
                                    changed = true;
                                }
                            }
                            transform_gizmo::TransformGizmoHandle::RotateTopLeft
                            | transform_gizmo::TransformGizmoHandle::RotateTopRight
                            | transform_gizmo::TransformGizmoHandle::RotateBottomLeft
                            | transform_gizmo::TransformGizmoHandle::RotateBottomRight => {
                                changed = document.rotate_selection_degrees(
                                    drag.preview_rotation_degrees,
                                    drag.preview_pivot,
                                );
                            }
                            _ => {
                                changed = document.transform_selection_nearest(drag.preview_selection);
                                if changed && drag.handle == transform_gizmo::TransformGizmoHandle::Move {
                                    let dx = drag.preview_selection.x as i32 - drag.start_selection.x as i32;
                                    let dy = drag.preview_selection.y as i32 - drag.start_selection.y as i32;
                                    document.metadata.pivot[0] += dx;
                                    document.metadata.pivot[1] += dy;
                                }
                            }
                        }
                    }
                    if changed {
                        self.pixel_studio.refresh_texture();
                        self.status_message = format!("Committed {} transform", drag.handle.label());
                    } else {
                        self.status_message = format!("{} transform unchanged", drag.handle.label());
                    }
                }
                return;
            }
        }
        let current = self.pixel_studio.screen_to_pixel(canvas, mouse);
        if (is_mouse_button_down(MouseButton::Left) || is_mouse_button_down(MouseButton::Right))
            && self.pixel_studio.stroke_started
            && !is_key_down(KeyCode::Space)
        {
            if let Some(pixel) = current {
                if self.pixel_studio.grid_realign_enabled {
                    if let (Some(start), Some(origin), Some(document)) = (
                        self.pixel_studio.drag_start,
                        self.pixel_studio.grid_drag_origin,
                        self.pixel_studio.document.as_mut(),
                    ) {
                        document.metadata.grid.offset_x =
                            origin.0 + pixel.0 as i32 - start.0 as i32;
                        document.metadata.grid.offset_y =
                            origin.1 + pixel.1 as i32 - start.1 as i32;
                        document.dirty = true;
                    }
                } else {
                    let active_tool = self.pixel_studio.tool;
                    match active_tool {
                        PixelTool::Pencil | PixelTool::Eraser | PixelTool::Smudge => {
                            let previous = self.pixel_studio.drag_current.unwrap_or(pixel);
                            if previous != pixel {
                                self.apply_pixel_brush_segment(previous, pixel);
                                self.pixel_studio.drag_current = Some(pixel);
                            }
                        }
                        PixelTool::Selection | PixelTool::Line | PixelTool::Rectangle
                        | PixelTool::Ellipse | PixelTool::Gradient => {
                            self.pixel_studio.drag_current = Some(pixel);
                        }
                        _ => {}
                    }
                }
            }
        }
        if (is_mouse_button_released(MouseButton::Left)
            || is_mouse_button_released(MouseButton::Right))
            && self.pixel_studio.stroke_started
        {
            self.finish_pixel_gesture(current);
        }
    }

    pub(crate) fn handle_pixel_studio_click(&mut self, mx: f32, my: f32) -> bool {
        if self.viewport_mode != EditorViewportMode::PixelStudio {
            return false;
        }
        let mouse = vec2(mx, my);
        if self.pixel_studio.new_dialog.is_some() {
            return self.handle_new_pixel_dialog_click(mouse);
        }
        if self.pixel_color_popup_open {
            let panel = pixel_color_popup_panel(self);
            if pixel_color_popup_close_rect(panel).contains(mouse) {
                self.close_pixel_color_tray();
                return true;
            }
            if panel.contains(mouse) {
                let content = pixel_color_popup_content(panel);
                if super::pixel_color_panel::update_color_from_pointer(self, mouse, content) {
                    self.begin_color_picker_drag(content);
                } else {
                    let _ = handle_pixel_color_controls(self, mouse, content);
                }
                return true;
            }
            self.close_pixel_color_tray();
            return true;
        }
        let list = self.contextual_asset_browser_rect();
        if list.contains(mouse) {
            return self.handle_pixel_library_click(mouse, list);
        }

        let canvas = self.pixel_canvas_rect();
        let document_tabs = self.pixel_studio.document_tab_info();
        let document_bar = self.canvas_workspace_layout().document_tabs;
        if document_bar.contains(mouse) {
            if pixel_document_new_rect(document_bar).contains(mouse) {
                self.pixel_studio.open_new_dialog();
                self.status_message = "New Pixel document".to_string();
                return true;
            }
            for mode in [DocumentSplitMode::Single, DocumentSplitMode::Vertical] {
                if pixel_document_split_rect(document_bar, mode).contains(mouse) {
                    self.workspace_shell.document_split_mode = mode;
                    self.pixel_studio.ensure_secondary_document();
                    self.persist_workspace_shell(&format!("Document view: {}", mode.label()));
                    return true;
                }
            }
            for (visual_index, tab) in document_tabs.iter().enumerate() {
                let tab_rect = pixel_document_tab_rect(document_bar, visual_index, document_tabs.len());
                if tab_rect.contains(mouse) {
                    if pixel_document_tab_close_rect(tab_rect).contains(mouse) {
                        self.request_close_pixel_document(tab.index);
                        return true;
                    }
                    if self.pixel_studio.activate_document_tab(tab.index) {
                        self.pixel_studio.ensure_secondary_document();
                        self.status_message = format!("Focused Pixel document: {}", tab.label);
                    }
                    return true;
                }
            }
            return true;
        }
        if self.pixel_secondary_canvas_rect().is_some_and(|rect| rect.contains(mouse)) {
            if self.pixel_studio.activate_secondary_document() {
                self.status_message = "Editing companion Pixel document in-place".to_string();
            }
            return true;
        }
        let toolbar = self.pixel_context_toolbar_rect();
        if toolbar.contains(mouse) {
            if pixel_selection_mode_rect(toolbar).contains(mouse) {
                self.pixel_studio.selection_mode = self.pixel_studio.selection_mode.cycle();
                self.pixel_studio.tool = PixelTool::Selection;
                self.status_message = format!(
                    "Selection mode: {}",
                    self.pixel_studio.selection_mode.label()
                );
                return true;
            }
            if Rect::new(toolbar.x + 82.0, toolbar.y + 2.0, 78.0, 24.0).contains(mouse) {
                self.pixel_studio.show_atlas_grid = !self.pixel_studio.show_atlas_grid;
                self.status_message = format!(
                    "Frame grid {}",
                    if self.pixel_studio.show_atlas_grid {
                        "visible"
                    } else {
                        "hidden"
                    }
                );
                return true;
            }
            if Rect::new(toolbar.x + 164.0, toolbar.y + 2.0, 72.0, 24.0).contains(mouse) {
                self.pixel_studio.show_pixel_grid = !self.pixel_studio.show_pixel_grid;
                return true;
            }
        }

        let inspector = self.inspector_content_rect();
        if inspector.contains(mouse) && self.handle_pixel_inspector_click(mouse, inspector) {
            return true;
        }

        // H21-A14Y: Palette input is owned once by shared_palette.rs before
        // Pixel Studio canvas routing. Keeping a second hit-test surface here
        // caused FG/BG/add-color behavior to diverge from World direct-visual use.

        if canvas.contains(mouse) {
            if is_mouse_button_down(MouseButton::Left)
                && self.pixel_studio.tool == PixelTool::Selection
                && self.pixel_studio.selection_mode == PixelSelectionMode::Pixels
            {
                if let (Some(document), Some(transform)) = (
                    self.pixel_studio.document.as_ref(),
                    self.pixel_studio.canvas_transform(canvas),
                ) {
                    let pivot = [
                        document.metadata.pivot[0] as f32,
                        document.metadata.pivot[1] as f32,
                    ];
                    if let Some(drag) = transform_gizmo::begin_pixel_transform_drag(
                        document.metadata.selection,
                        pivot,
                        transform,
                        mouse,
                    ) {
                        self.status_message = format!("{} transform started", drag.handle.label());
                        self.transform_gizmo_drag = Some(drag);
                        self.pixel_studio.stroke_started = false;
                        return true;
                    }
                }
            }
            let Some(pixel) = self.pixel_studio.screen_to_pixel(canvas, mouse) else {
                return true;
            };
            let alt_down = is_key_down(KeyCode::LeftAlt) || is_key_down(KeyCode::RightAlt);
            if alt_down {
                if let Some(document) = self.pixel_studio.document.as_mut() {
                    document.begin_edit();
                    document.metadata.pivot = [pixel.0 as i32, pixel.1 as i32];
                    document.dirty = true;
                    self.status_message = format!("Pivot set to {}, {}", pixel.0, pixel.1);
                }
                return true;
            }
            let active_tool = self.pixel_studio.tool;
            self.pixel_studio.stroke_uses_background = is_mouse_button_down(MouseButton::Right);
            if active_tool == PixelTool::Selection
                && self.pixel_studio.selection_mode == PixelSelectionMode::Frame
            {
                if let Some(document) = self.pixel_studio.document.as_mut() {
                    let selection = grid_cell_selection(document, pixel);
                    document.begin_edit();
                    document.metadata.selection = selection;
                    document.dirty = true;
                    self.status_message = format!(
                        "Selected frame {}x{} at {}, {}",
                        selection.width, selection.height, selection.x, selection.y
                    );
                }
                return true;
            }
            if self.pixel_studio.grid_realign_enabled {
                if let Some(document) = self.pixel_studio.document.as_mut() {
                    document.begin_edit();
                }
                self.pixel_studio.drag_start = Some(pixel);
                self.pixel_studio.drag_current = Some(pixel);
                self.pixel_studio.grid_drag_origin =
                    self.pixel_studio.document.as_ref().map(|document| {
                        (
                            document.metadata.grid.offset_x,
                            document.metadata.grid.offset_y,
                        )
                    });
                self.pixel_studio.stroke_started = true;
                return true;
            }
            match active_tool {
                PixelTool::Pencil | PixelTool::Eraser | PixelTool::Smudge => {
                    if let Some(document) = self.pixel_studio.document.as_mut() {
                        document.begin_edit();
                    }
                    self.pixel_studio.drag_start = Some(pixel);
                    self.pixel_studio.drag_current = Some(pixel);
                    self.pixel_studio.stroke_started = true;
                    if active_tool != PixelTool::Smudge {
                        self.apply_pixel_brush_segment(pixel, pixel);
                    }
                }
                PixelTool::Fill => {
                    let color = if is_mouse_button_down(MouseButton::Right) {
                        self.pixel_studio.background_color
                    } else {
                        self.pixel_studio.selected_color
                    };
                    if let Some(document) = self.pixel_studio.document.as_mut() {
                        document.begin_edit();
                        let changed = document.flood_fill(pixel.0, pixel.1, color);
                        self.status_message = format!("Filled {changed} pixels");
                    }
                    self.pixel_studio.refresh_texture();
                }
                PixelTool::Eyedropper => {
                    if let Some(document) = self.pixel_studio.document.as_ref() {
                        let color = document.color_at(pixel.0, pixel.1);
                        if self.pixel_studio.stroke_uses_background {
                            self.pixel_studio.background_color = color;
                            self.pixel_color_edit_background = true;
                            self.status_message = format!("Picked background color at {}, {}", pixel.0, pixel.1);
                        } else {
                            self.pixel_studio.selected_color = color;
                            self.pixel_color_edit_background = false;
                            self.status_message = format!("Picked foreground color at {}, {}", pixel.0, pixel.1);
                        }
                    }
                }
                PixelTool::MagicSelect => {
                    if let Some(document) = self.pixel_studio.document.as_mut() {
                        document.begin_edit();
                        let selection = document.magic_select_contiguous(pixel.0, pixel.1);
                        self.status_message = format!(
                            "Magic selected {}x{} contiguous color region",
                            selection.width, selection.height
                        );
                    }
                }
                PixelTool::Blur | PixelTool::Lighten | PixelTool::Darken => {
                    if let Some(document) = self.pixel_studio.document.as_mut() {
                        document.begin_edit();
                        let selection = pixel_effect_region(document, pixel);
                        let changed = match active_tool {
                            PixelTool::Blur => document.blur_region(selection),
                            PixelTool::Lighten => document.adjust_luma_region(selection, 18),
                            PixelTool::Darken => document.adjust_luma_region(selection, -18),
                            _ => 0,
                        };
                        self.status_message = format!("{} changed {changed} pixels", active_tool.label());
                    }
                    self.pixel_studio.refresh_texture();
                }
                PixelTool::Selection | PixelTool::Line | PixelTool::Rectangle
                | PixelTool::Ellipse | PixelTool::Gradient => {
                    if let Some(document) = self.pixel_studio.document.as_mut() {
                        document.begin_edit();
                    }
                    self.pixel_studio.drag_start = Some(pixel);
                    self.pixel_studio.drag_current = Some(pixel);
                    self.pixel_studio.stroke_started = true;
                }
            }
            return true;
        }
        false
    }

    fn handle_pixel_inspector_click(&mut self, mouse: Vec2, rect: Rect) -> bool {
        if self.pixel_studio.document.is_none() {
            return false;
        }
        if pixel_asset_tab_rect(rect).contains(mouse) {
            self.pixel_studio.inspector_tab = PixelInspectorTab::Asset;
            return true;
        }
        if pixel_animation_tab_rect(rect).contains(mouse) {
            self.pixel_studio.inspector_tab = PixelInspectorTab::Animation;
            return true;
        }
        if self.pixel_studio.inspector_tab == PixelInspectorTab::Animation {
            if pixel_animation_onion_rect(rect).contains(mouse) {
                if let Some(context) = self.pixel_studio.animation_context.as_mut() {
                    context.onion_skin = !context.onion_skin;
                    self.status_message = format!(
                        "Animation onion skin {}",
                        if context.onion_skin {
                            "enabled"
                        } else {
                            "disabled"
                        }
                    );
                }
                return true;
            }
            if pixel_animation_focus_rect(rect).contains(mouse) {
                let canvas = self.pixel_canvas_rect();
                self.pixel_studio.frame_selection(canvas);
                self.status_message = "Focused the active animation frame".to_string();
                return true;
            }
            if pixel_animation_save_return_rect(rect).contains(mouse) {
                self.save_animation_pixels_and_return();
                return true;
            }
            if pixel_animation_cancel_return_rect(rect).contains(mouse) {
                self.return_to_animation_without_pixel_save();
                return true;
            }
            return true;
        }
        if pixel_grid_toggle_rect(rect).contains(mouse) {
            self.pixel_studio.show_atlas_grid = !self.pixel_studio.show_atlas_grid;
            return true;
        }
        if pixel_realign_rect(rect).contains(mouse) {
            if self.pixel_studio.grid_realign_enabled {
                self.pixel_studio.grid_realign_enabled = false;
                self.pixel_studio.grid_realign_armed = false;
                self.status_message = "Atlas Grid Realignment Mode disabled".to_string();
            } else if self.pixel_studio.grid_realign_armed {
                self.pixel_studio.grid_realign_enabled = true;
                self.pixel_studio.grid_realign_armed = false;
                self.status_message = "Atlas Grid Realignment Mode enabled. Drag the logical grid; pixels will not move. Esc cancels.".to_string();
            } else {
                self.pixel_studio.grid_realign_armed = true;
                self.status_message = "Grid realignment is non-destructive metadata editing. Click Confirm Realign to enable.".to_string();
            }
            return true;
        }
        for row in 0..6 {
            if pixel_value_minus_rect(rect, row).contains(mouse) {
                self.adjust_pixel_grid(row, -1);
                return true;
            }
            if pixel_value_plus_rect(rect, row).contains(mouse) {
                self.adjust_pixel_grid(row, 1);
                return true;
            }
        }
        if pixel_flip_h_rect(rect).contains(mouse) {
            if let Some(document) = self.pixel_studio.document.as_mut() {
                document.flip_selection_horizontal();
            }
            self.pixel_studio.refresh_texture();
            return true;
        }
        if pixel_flip_v_rect(rect).contains(mouse) {
            if let Some(document) = self.pixel_studio.document.as_mut() {
                document.flip_selection_vertical();
            }
            self.pixel_studio.refresh_texture();
            return true;
        }
        if pixel_pivot_bottom_rect(rect).contains(mouse) {
            if let Some(document) = self.pixel_studio.document.as_mut() {
                let selection = document.metadata.selection;
                document.begin_edit();
                document.metadata.pivot = [
                    selection.x as i32 + selection.width as i32 / 2,
                    selection.y as i32 + selection.height.saturating_sub(1) as i32,
                ];
                document.dirty = true;
                self.status_message = "Pivot moved to selected slice bottom-center".to_string();
            }
            return true;
        }
        if pixel_fit_visual_rect(rect).contains(mouse) {
            let reset_source = self.pixel_studio.world_asset_context.is_some()
                && self
                    .pixel_studio
                    .document
                    .as_ref()
                    .and_then(|document| document.metadata.source_region)
                    .is_some();
            if reset_source {
                let result = self
                    .pixel_studio
                    .document
                    .as_mut()
                    .expect("pixel document checked above")
                    .reset_to_source_region(repo_root_dir());
                self.status_message = match result {
                    Ok(()) => {
                        self.pixel_studio.refresh_texture();
                        self.pixel_studio.frame_document(self.pixel_canvas_rect());
                        "Reset derived working copy to the exact upstream source region".to_string()
                    }
                    Err(error) => format!("Reset to source failed: {error}"),
                };
            } else if let Some(document) = self.pixel_studio.document.as_mut() {
                let selection = document.metadata.selection;
                let tile_w = document.metadata.grid.cell_width.max(1);
                let tile_h = document.metadata.grid.cell_height.max(1);
                let width = selection.width.max(1).div_ceil(tile_w) as i32;
                let height = selection.height.max(1).div_ceil(tile_h) as i32;
                document.begin_edit();
                document.metadata.visual_footprint = [0, 1 - height, width.max(1), height.max(1)];
                document.dirty = true;
                self.status_message = format!(
                    "Visual footprint fitted to {}x{} atlas cells",
                    width.max(1),
                    height.max(1)
                );
            }
            return true;
        }
        if pixel_target_kind_rect(rect).contains(mouse) {
            self.pixel_studio.target_kind = match self.pixel_studio.target_kind {
                AssetIntakeTargetKind::Tile => AssetIntakeTargetKind::Object,
                AssetIntakeTargetKind::Object => AssetIntakeTargetKind::Tile,
            };
            self.pixel_studio.target_index = 0;
            return true;
        }
        if pixel_target_prev_rect(rect).contains(mouse) {
            self.cycle_pixel_target(-1);
            return true;
        }
        if pixel_target_next_rect(rect).contains(mouse) {
            self.cycle_pixel_target(1);
            return true;
        }
        if pixel_save_rect(rect).contains(mouse) {
            self.save_pixel_document();
            return true;
        }
        if pixel_publish_rect(rect).contains(mouse) {
            self.publish_pixel_document();
            return true;
        }
        false
    }

    fn apply_pixel_brush_segment(&mut self, start: (u32, u32), end: (u32, u32)) {
        let active_tool = self.pixel_studio.tool;
        if active_tool == PixelTool::Smudge {
            let changed = if let Some(document) = self.pixel_studio.document.as_mut() {
                let mut previous = start;
                let mut changed = false;
                for point in pixel_line_points(start, end) {
                    if point != previous {
                        changed |= document.smudge_pixel(previous, point);
                        previous = point;
                    }
                }
                changed
            } else { false };
            if changed { self.pixel_studio.refresh_texture(); }
            return;
        }
        let use_background = is_mouse_button_down(MouseButton::Right)
            || (!is_mouse_button_down(MouseButton::Left) && self.pixel_studio.stroke_uses_background);
        let mut color = if active_tool == PixelTool::Eraser {
            [0, 0, 0, 0]
        } else if use_background {
            self.pixel_studio.background_color
        } else {
            self.pixel_studio.selected_color
        };
        if active_tool != PixelTool::Eraser {
            color[3] = ((color[3] as u16 * self.pixel_studio.brush_opacity as u16) / 255) as u8;
        }
        let brush_settings = haven_pixel::PixelBrushSettings {
            kind: self.pixel_studio.brush_kind,
            size: self.pixel_studio.brush_size.max(1),
            opacity: self.pixel_studio.brush_opacity,
            density: self.pixel_studio.brush_density,
            angle_degrees: self.pixel_studio.brush_angle_degrees,
            spacing: 1,
        };
        let symmetry_horizontal = self.pixel_studio.symmetry_horizontal;
        let symmetry_vertical = self.pixel_studio.symmetry_vertical;
        let symmetry_axis_x = self.pixel_studio.symmetry_axis_x;
        let symmetry_axis_y = self.pixel_studio.symmetry_axis_y;
        let changed = if let Some(document) = self.pixel_studio.document.as_mut() {
            let width = document.width();
            let height = document.height();
            let mut changed = false;
            for point in pixel_line_points(start, end) {
                for center in mirrored_pixel_points(point, width, height, symmetry_horizontal, symmetry_vertical, symmetry_axis_x, symmetry_axis_y) {
                    changed |= stamp_pixel_brush(document, center, brush_settings, color);
                }
            }
            changed
        } else {
            false
        };
        if changed {
            // Keep the visible canvas synchronized while the mouse is held.
            self.pixel_studio.refresh_texture();
        }
    }

    fn finish_pixel_gesture(&mut self, current: Option<(u32, u32)>) {
        let start = self.pixel_studio.drag_start;
        let end = current.or(self.pixel_studio.drag_current);
        if !self.pixel_studio.grid_realign_enabled {
            if let (Some(start), Some(end), Some(document)) =
                (start, end, self.pixel_studio.document.as_mut())
            {
                match self.pixel_studio.tool {
                    PixelTool::Selection => {
                        document.metadata.selection =
                            PixelSelection::from_points(start.0, start.1, end.0, end.1);
                        document.dirty = true;
                    }
                    PixelTool::Line => {
                        let color = if self.pixel_studio.stroke_uses_background { self.pixel_studio.background_color } else { self.pixel_studio.selected_color };
                        document.draw_line(start, end, color)
                    }
                    PixelTool::Rectangle => {
                        let color = if self.pixel_studio.stroke_uses_background { self.pixel_studio.background_color } else { self.pixel_studio.selected_color };
                        document.draw_rectangle(
                            PixelSelection::from_points(start.0, start.1, end.0, end.1),
                            color,
                            is_key_down(KeyCode::LeftShift) || is_key_down(KeyCode::RightShift),
                        )
                    },
                    PixelTool::Ellipse => {
                        let color = if self.pixel_studio.stroke_uses_background { self.pixel_studio.background_color } else { self.pixel_studio.selected_color };
                        document.draw_ellipse(
                            PixelSelection::from_points(start.0, start.1, end.0, end.1),
                            color,
                            is_key_down(KeyCode::LeftShift) || is_key_down(KeyCode::RightShift),
                        )
                    },
                    PixelTool::Gradient => {
                        let selection = if document.metadata.selection.is_empty() {
                            PixelSelection { x: 0, y: 0, width: document.width(), height: document.height() }
                        } else { document.metadata.selection };
                        let _ = document.draw_gradient(
                            selection, start, end,
                            self.pixel_studio.selected_color,
                            self.pixel_studio.background_color,
                        );
                    },
                    _ => {}
                }
            }
        }
        self.pixel_studio.stroke_started = false;
        self.pixel_studio.drag_start = None;
        self.pixel_studio.drag_current = None;
        self.pixel_studio.grid_drag_origin = None;
        self.pixel_studio.refresh_texture();
    }

    fn cycle_pixel_target(&mut self, delta: i32) {
        let len = match self.pixel_studio.target_kind {
            AssetIntakeTargetKind::Tile => TileKind::ALL.len(),
            AssetIntakeTargetKind::Object => OBJECT_BRUSHES.len(),
        };
        self.pixel_studio.target_index = cycle_index(self.pixel_studio.target_index, len, delta);
    }

    fn adjust_pixel_grid(&mut self, row: usize, delta: i32) {
        let Some(document) = self.pixel_studio.document.as_mut() else {
            return;
        };
        document.begin_edit();
        match row {
            0 => {
                document.metadata.grid.cell_width =
                    (document.metadata.grid.cell_width as i32 + delta).clamp(1, 512) as u32
            }
            1 => {
                document.metadata.grid.cell_height =
                    (document.metadata.grid.cell_height as i32 + delta).clamp(1, 512) as u32
            }
            2 => {
                document.metadata.grid.offset_x =
                    (document.metadata.grid.offset_x + delta).clamp(-512, 512)
            }
            3 => {
                document.metadata.grid.offset_y =
                    (document.metadata.grid.offset_y + delta).clamp(-512, 512)
            }
            4 => {
                document.metadata.grid.spacing_x =
                    (document.metadata.grid.spacing_x as i32 + delta).clamp(0, 128) as u32
            }
            5 => {
                document.metadata.grid.spacing_y =
                    (document.metadata.grid.spacing_y as i32 + delta).clamp(0, 128) as u32
            }
            _ => return,
        }
        let selection = document.metadata.selection;
        document.metadata.selection = PixelSelection {
            x: selection.x.min(document.width().saturating_sub(1)),
            y: selection.y.min(document.height().saturating_sub(1)),
            width: selection.width.min(document.width()).max(1),
            height: selection.height.min(document.height()).max(1),
        };
        document.dirty = true;
    }
}

fn pixel_effect_region(document: &haven_pixel::PixelDocument, pixel: (u32, u32)) -> PixelSelection {
    let selection = document.metadata.selection;
    let contains = !selection.is_empty()
        && pixel.0 >= selection.x
        && pixel.1 >= selection.y
        && pixel.0 < selection.x.saturating_add(selection.width)
        && pixel.1 < selection.y.saturating_add(selection.height);
    if contains {
        selection
    } else {
        let radius = 1u32;
        let x = pixel.0.saturating_sub(radius);
        let y = pixel.1.saturating_sub(radius);
        PixelSelection {
            x,
            y,
            width: (radius * 2 + 1).min(document.width().saturating_sub(x)).max(1),
            height: (radius * 2 + 1).min(document.height().saturating_sub(y)).max(1),
        }
    }
}

fn pixel_line_points(start: (u32, u32), end: (u32, u32)) -> Vec<(u32, u32)> {
    let (mut x0, mut y0) = (start.0 as i32, start.1 as i32);
    let (x1, y1) = (end.0 as i32, end.1 as i32);
    let dx = (x1 - x0).abs();
    let sx = if x0 < x1 { 1 } else { -1 };
    let dy = -(y1 - y0).abs();
    let sy = if y0 < y1 { 1 } else { -1 };
    let mut error = dx + dy;
    let mut points = Vec::new();
    loop {
        if x0 >= 0 && y0 >= 0 { points.push((x0 as u32, y0 as u32)); }
        if x0 == x1 && y0 == y1 { break; }
        let doubled = error * 2;
        if doubled >= dy { error += dy; x0 += sx; }
        if doubled <= dx { error += dx; y0 += sy; }
    }
    points
}

fn mirrored_pixel_points(point: (u32, u32), width: u32, height: u32, horizontal: bool, vertical: bool, axis_x: Option<u32>, axis_y: Option<u32>) -> Vec<(u32, u32)> {
    let mut points = vec![point];
    let ax = axis_x.unwrap_or_else(|| width.saturating_sub(1) / 2) as i64;
    let ay = axis_y.unwrap_or_else(|| height.saturating_sub(1) / 2) as i64;
    let mx = (ax * 2 - point.0 as i64).clamp(0, width.saturating_sub(1) as i64) as u32;
    let my = (ay * 2 - point.1 as i64).clamp(0, height.saturating_sub(1) as i64) as u32;
    if vertical && width > 0 { points.push((mx, point.1)); }
    if horizontal && height > 0 { points.push((point.0, my)); }
    if horizontal && vertical && width > 0 && height > 0 { points.push((mx, my)); }
    points.sort_unstable();
    points.dedup();
    points
}

fn stamp_pixel_brush(
    document: &mut haven_pixel::PixelDocument,
    center: (u32, u32),
    settings: haven_pixel::PixelBrushSettings,
    color: [u8; 4],
) -> bool {
    let settings = settings.normalized();
    let size = i32::from(settings.size.max(1));
    let left = (size - 1) / 2;
    let right = size / 2;
    let center_i32 = (center.0 as i32, center.1 as i32);
    let mut changed = false;
    for dy in -left..=right {
        for dx in -left..=right {
            if !settings.contains_offset(center_i32, dx, dy) {
                continue;
            }
            let x = center_i32.0 + dx;
            let y = center_i32.1 + dy;
            if x >= 0 && y >= 0 {
                changed |= document.set_pixel(x as u32, y as u32, color);
            }
        }
    }
    changed
}

fn grid_cell_selection(document: &haven_pixel::PixelDocument, pixel: (u32, u32)) -> PixelSelection {
    let grid = document.metadata.grid;
    let stride_x = (grid.cell_width + grid.spacing_x).max(1) as i32;
    let stride_y = (grid.cell_height + grid.spacing_y).max(1) as i32;
    let x = grid.offset_x + (pixel.0 as i32 - grid.offset_x).div_euclid(stride_x) * stride_x;
    let y = grid.offset_y + (pixel.1 as i32 - grid.offset_y).div_euclid(stride_y) * stride_y;
    let x = x.clamp(0, document.width().saturating_sub(1) as i32) as u32;
    let y = y.clamp(0, document.height().saturating_sub(1) as i32) as u32;
    PixelSelection {
        x,
        y,
        width: grid.cell_width.min(document.width() - x).max(1),
        height: grid.cell_height.min(document.height() - y).max(1),
    }
}

include!("pixel_new_document_input.rs");
