use super::*;

impl EditorApp {
    pub(crate) fn paste_clipboard_at_cursor(&mut self) {
        let Some(clipboard) = self.scene_clipboard.as_ref() else {
            self.status_message = "Clipboard is empty".to_string();
            return;
        };
        let active_layer = self.scene_authoring_layer();
        if active_layer != clipboard.layer {
            self.status_message = format!(
                "Clipboard contains {} content; select the {} layer before pasting",
                SceneLayerMode::from_authoring_layer(clipboard.layer).label(),
                SceneLayerMode::from_authoring_layer(clipboard.layer).label()
            );
            return;
        }
        if self.active_layer_state().locked {
            self.status_message = format!("{} layer is locked", self.scene_layer_mode.label());
            return;
        }
        self.scene_paste_anchor = Some(GridPos {
            x: self.scene_cursor_x,
            y: self.scene_cursor_y,
        });
        self.scene_drag = None;
        self.last_painted_cell = None;
        self.status_message = format!(
            "Paste preview armed: {} item{} | move on the tile grid, left-click to place, Esc to cancel",
            clipboard.item_count(),
            if clipboard.item_count() == 1 { "" } else { "s" }
        );
    }

    pub(crate) fn scene_paste_preview_rect(&self) -> Option<GridRect> {
        let anchor = self.scene_paste_anchor?;
        let clipboard = self.scene_clipboard.as_ref()?;
        Some(GridRect::from_points(
            anchor,
            GridPos {
                x: anchor.x + clipboard.width().saturating_sub(1),
                y: anchor.y + clipboard.height().saturating_sub(1),
            },
        ))
    }

    pub(crate) fn update_scene_paste_anchor(&mut self, anchor: GridPos) {
        if self.scene_paste_anchor.is_some() {
            self.scene_paste_anchor = Some(anchor);
            self.scene_cursor_x = anchor.x;
            self.scene_cursor_y = anchor.y;
        }
    }

    pub(crate) fn cancel_scene_paste_preview(&mut self) -> bool {
        if self.scene_paste_anchor.take().is_some() {
            self.status_message = "Cancelled pending paste".to_string();
            true
        } else {
            false
        }
    }

    pub(crate) fn commit_scene_paste_preview(&mut self) -> bool {
        let Some(anchor) = self.scene_paste_anchor else {
            return false;
        };
        let Some(clipboard) = self.scene_clipboard.clone() else {
            self.scene_paste_anchor = None;
            self.status_message = "Clipboard is empty".to_string();
            return true;
        };
        let Some(scene_id) = self.active_scene_id() else {
            self.scene_paste_anchor = None;
            return true;
        };
        if self.scene_authoring_layer() != clipboard.layer {
            self.status_message = format!(
                "Paste cancelled: active layer changed from {}",
                SceneLayerMode::from_authoring_layer(clipboard.layer).label()
            );
            self.scene_paste_anchor = None;
            return true;
        }
        if self.active_layer_state().locked {
            self.status_message = format!("{} layer is locked", self.scene_layer_mode.label());
            return true;
        }
        let result = paste_scene_clipboard(
            &mut self.model.world,
            &mut self.command_bus,
            &self.model.project.project_id,
            EditorCommandSource::MainEditor,
            scene_id.clone(),
            &clipboard,
            anchor,
        );
        match result {
            Ok(outcome) => {
                self.scene_paste_anchor = None;
                self.status_message = format!("{} | pasted selection remains selected", outcome.edit.message);
                self.selection
                    .replace_many(scene_id, outcome.selected_items, outcome.bounds);
            }
            Err(error) => {
                self.status_message = format!("Paste preview remains active: {error}");
            }
        }
        true
    }

    pub(crate) fn duplicate_current_selection(&mut self) {
        let Some(scene) = self.model.world.scenes.get(self.selected_scene) else {
            return;
        };
        let Some(bounds) = self.selection.bounds else {
            self.status_message = "Nothing selected to duplicate".to_string();
            return;
        };
        let clipboard = match copy_scene_selection(
            scene,
            self.scene_authoring_layer(),
            &self.selection.items,
            bounds,
        ) {
            Ok(clipboard) => clipboard,
            Err(error) => {
                self.status_message = error;
                return;
            }
        };
        self.scene_clipboard = Some(clipboard);
        self.scene_cursor_x = bounds.min.x + 1;
        self.scene_cursor_y = bounds.min.y + 1;
        self.paste_clipboard_at_cursor();
    }

    pub(crate) fn delete_current_selection(&mut self) {
        if self.active_layer_state().locked {
            self.status_message = format!("{} layer is locked", self.scene_layer_mode.label());
            return;
        }
        let Some(scene_id) = self.active_scene_id() else {
            return;
        };
        if self.selection.is_empty() {
            self.status_message = "Nothing selected to delete".to_string();
            return;
        }
        let tile = self.selected_tile_kind();
        let result = delete_scene_selection(
            &mut self.model.world,
            &mut self.command_bus,
            &self.model.project.project_id,
            EditorCommandSource::MainEditor,
            scene_id,
            &self.selection.items,
            tile,
        );
        self.finish_bulk_result(result);
        self.selection.clear_items();
    }

    pub(crate) fn frame_current_selection(&mut self) {
        let Some(bounds) = self.selection.bounds else {
            self.status_message = "Nothing selected to frame".to_string();
            return;
        };
        self.scene_canvas.frame_rect(
            self.scene_canvas_viewport_rect(),
            self.scene_canvas_bounds(),
            Rect::new(
                bounds.min.x as f32,
                bounds.min.y as f32,
                bounds.width() as f32,
                bounds.height() as f32,
            ),
        );
        self.status_message = "Framed current selection".to_string();
    }

    pub(crate) fn scene_drag_preview_rect(&self) -> Option<GridRect> {
        let drag = self.scene_drag?;
        match drag.kind {
            SceneCanvasDragKind::MoveSelection => self.selection.bounds.map(|bounds| {
                bounds.translated(GridPos {
                    x: drag.current.x - drag.start.x,
                    y: drag.current.y - drag.start.y,
                })
            }),
            SceneCanvasDragKind::Marquee | SceneCanvasDragKind::Rectangle => Some(drag.rect()),
        }
    }
}
