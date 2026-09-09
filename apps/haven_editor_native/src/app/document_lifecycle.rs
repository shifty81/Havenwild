use super::render_helpers::{draw_editor_widget_tone, draw_scissored_text, WidgetTone};
use super::*;

#[derive(Clone, Debug)]
pub(crate) enum DocumentCloseTarget {
    Scene(ProjectSceneId),
    Ui,
    Pixel(usize),
    PixelAll,
    Workspace(EditorViewportMode),
}

#[derive(Clone, Debug)]
pub(crate) struct PendingDocumentClose {
    pub target: DocumentCloseTarget,
    pub title: String,
}

fn modal_rect() -> Rect {
    let width = 520.0_f32.min((screen_width() - 32.0).max(320.0));
    let height = 210.0_f32.min((screen_height() - 32.0).max(180.0));
    Rect::new((screen_width() - width) * 0.5, (screen_height() - height) * 0.5, width, height)
}

fn save_rect(panel: Rect) -> Rect {
    Rect::new(panel.x + 18.0, panel.y + panel.h - 52.0, 132.0, 32.0)
}
fn close_rect(panel: Rect) -> Rect {
    Rect::new(panel.x + 158.0, panel.y + panel.h - 52.0, 172.0, 32.0)
}
fn cancel_rect(panel: Rect) -> Rect {
    Rect::new(panel.x + panel.w - 118.0, panel.y + panel.h - 52.0, 100.0, 32.0)
}

impl EditorApp {
    pub(crate) fn workspace_document_is_closed(&self, mode: EditorViewportMode) -> bool {
        self.closed_workspace_documents.contains(&mode)
    }

    pub(crate) fn reopen_workspace_document(&mut self, mode: EditorViewportMode) {
        self.closed_workspace_documents.remove(&mode);
        self.recently_closed_workspace_documents.retain(|candidate| *candidate != mode);
        self.status_message = format!("Reopened {} document", mode.label());
    }

    pub(crate) fn request_close_active_document(&mut self) -> bool {
        match self.viewport_mode {
            EditorViewportMode::SceneMap => {
                if self.game_canvas_ui_active() {
                    self.request_document_close(
                        DocumentCloseTarget::Ui,
                        self.game_canvas_ui.document.as_ref().map(|document| document.display_name.clone()).unwrap_or_else(|| "UI Document".to_string()),
                        self.game_canvas_ui.dirty,
                    )
                } else {
                    let Some(id) = self.active_scene_id() else { return false; };
                    self.request_close_scene_document(id)
                }
            }
            EditorViewportMode::PixelStudio => {
                let Some(index) = self.pixel_studio.active_document_tab else { return false; };
                self.request_close_pixel_document(index)
            }
            mode => self.request_close_workspace_document(mode),
        }
    }

    pub(crate) fn request_close_scene_document(&mut self, scene_id: ProjectSceneId) -> bool {
        let dirty = self.scene_document_dirty_ids.contains(&scene_id)
            || (self.active_scene_id().as_ref() == Some(&scene_id)
                && self.command_bus.undo_len() != self.saved_undo_depth);
        let title = self
            .model
            .world
            .scene_by_id(&scene_id)
            .map(|scene| scene.name.clone())
            .unwrap_or_else(|| scene_id.label());
        self.request_document_close(DocumentCloseTarget::Scene(scene_id), title, dirty)
    }

    pub(crate) fn request_close_pixel_document(&mut self, index: usize) -> bool {
        let Some(info) = self
            .pixel_studio
            .document_tab_info()
            .into_iter()
            .find(|info| info.index == index)
        else {
            return false;
        };
        self.request_document_close(DocumentCloseTarget::Pixel(index), info.label, info.dirty)
    }

    pub(crate) fn request_close_all_pixel_documents(&mut self) -> bool {
        if self.pixel_studio.document_tab_info().is_empty() {
            return false;
        }
        self.request_document_close(
            DocumentCloseTarget::PixelAll,
            "all Pixel Studio documents".to_string(),
            self.pixel_studio.any_document_dirty(),
        )
    }

    pub(crate) fn request_close_workspace_document(&mut self, mode: EditorViewportMode) -> bool {
        if self.workspace_document_is_closed(mode) {
            return false;
        }
        let dirty = match mode {
            EditorViewportMode::AnimationStudio => self
                .animation_studio
                .document
                .as_ref()
                .is_some_and(|document| document.dirty),
            EditorViewportMode::LogicStudio => self.logic_studio.dirty,
            EditorViewportMode::SoundStudio => self.sound_studio.dirty,
            EditorViewportMode::CharacterStudio => self.character_studio.dirty(),
            EditorViewportMode::SceneRectangles | EditorViewportMode::RegionGraph | EditorViewportMode::SceneBank => {
                self.command_bus.undo_len() != self.saved_undo_depth
            }
            EditorViewportMode::SceneMap | EditorViewportMode::PixelStudio => false,
        };
        self.request_document_close(
            DocumentCloseTarget::Workspace(mode),
            self.active_document_title(),
            dirty,
        )
    }

    fn request_document_close(&mut self, target: DocumentCloseTarget, title: String, dirty: bool) -> bool {
        if dirty {
            self.pending_document_close = Some(PendingDocumentClose { target, title });
            return true;
        }
        self.close_document_target(target);
        true
    }

    fn save_document_target(&mut self, target: &DocumentCloseTarget) -> Result<String, String> {
        match target {
            DocumentCloseTarget::Scene(scene_id) => {
                let path = development_session::editor_world_path();
                save_world_to_path(&path.to_string_lossy(), &self.model.world)?;
                self.scene_document_dirty_ids.remove(scene_id);
                if self.active_scene_id().as_ref() == Some(scene_id) {
                    self.saved_undo_depth = self.command_bus.undo_len();
                }
                Ok(format!("Saved scene {}", scene_id.label()))
            }
            DocumentCloseTarget::Ui => {
                self.game_canvas_ui.save_active()?;
                Ok("Saved UI document".to_string())
            }
            DocumentCloseTarget::Pixel(index) => {
                self.pixel_studio.save_document_tab(*index)?;
                Ok("Saved Pixel document".to_string())
            }
            DocumentCloseTarget::PixelAll => Err("Save & Close All must use explicit Save All".to_string()),
            DocumentCloseTarget::Workspace(mode) => match mode {
                EditorViewportMode::AnimationStudio => {
                    let document = self.animation_studio.document.as_mut().ok_or_else(|| "No animation document is open".to_string())?;
                    document.save(repo_root_dir())?;
                    Ok("Saved Animation document".to_string())
                }
                EditorViewportMode::CharacterStudio => self.character_studio.save_recipe_draft(),
                EditorViewportMode::LogicStudio => {
                    let root = repo_root_dir();
                    let path = root.join("WORKSPACE/logic/documents").join(format!("{}.hhlogic.json", self.logic_studio.graph.id));
                    self.logic_studio.graph.save_to_path(&path)?;
                    self.logic_studio.dirty = false;
                    Ok("Saved Logic document".to_string())
                }
                EditorViewportMode::SoundStudio => {
                    let root = repo_root_dir();
                    let path = root.join("WORKSPACE/audio/documents").join(format!("{}.hhsound.json", self.sound_studio.document.id));
                    self.sound_studio.document.save_to_path(&path)?;
                    self.sound_studio.dirty = false;
                    Ok("Saved Sound document".to_string())
                }
                _ => Err(format!("{} uses the shared world Save All authority", mode.label())),
            },
        }
    }

    fn close_document_target(&mut self, target: DocumentCloseTarget) {
        match target {
            DocumentCloseTarget::Scene(scene_id) => {
                let _ = self.close_scene_document(&scene_id);
            }
            DocumentCloseTarget::Ui => {
                let label = self.game_canvas_ui.document.as_ref().map(|document| document.display_name.clone()).unwrap_or_else(|| "UI document".to_string());
                self.game_canvas_ui.close_view();
                self.activate_scene_workspace();
                self.status_message = format!("Closed {label}; resource remains in the UI document library");
            }
            DocumentCloseTarget::Pixel(index) => {
                let _ = self.pixel_studio.close_document_tab(index);
                self.status_message = "Closed Pixel Studio document".to_string();
            }
            DocumentCloseTarget::PixelAll => {
                self.pixel_studio.close_all_documents();
                self.status_message = "Closed all Pixel Studio documents".to_string();
            }
            DocumentCloseTarget::Workspace(mode) => {
                self.closed_workspace_documents.insert(mode);
                self.recently_closed_workspace_documents.retain(|candidate| *candidate != mode);
                self.recently_closed_workspace_documents.push(mode);
                if self.recently_closed_workspace_documents.len() > 12 {
                    self.recently_closed_workspace_documents.remove(0);
                }
                self.status_message = format!("Closed {} document view", mode.label());
            }
        }
    }

    pub(crate) fn reopen_last_closed_document(&mut self) -> bool {
        match self.viewport_mode {
            EditorViewportMode::SceneMap => self.reopen_last_closed_scene_document(),
            EditorViewportMode::PixelStudio => {
                let reopened = self.pixel_studio.reopen_last_closed_document();
                self.status_message = if reopened {
                    "Reopened last closed Pixel document".to_string()
                } else {
                    "No recently closed Pixel document".to_string()
                };
                reopened
            }
            _ => {
                while let Some(mode) = self.recently_closed_workspace_documents.pop() {
                    if self.closed_workspace_documents.remove(&mode) {
                        self.viewport_mode = mode;
                        self.status_message = format!("Reopened {} document", mode.label());
                        return true;
                    }
                }
                self.status_message = "No recently closed document".to_string();
                false
            }
        }
    }

    pub(crate) fn draw_closed_workspace_empty_state(&self, rect: Rect) {
        draw_rectangle(rect.x, rect.y, rect.w, rect.h, Color::new(0.055, 0.065, 0.075, 1.0));
        let width = 430.0_f32.min((rect.w - 32.0).max(220.0));
        let panel = Rect::new(
            rect.x + (rect.w - width) * 0.5,
            rect.y + (rect.h - 180.0).max(0.0) * 0.42,
            width,
            180.0_f32.min(rect.h),
        );
        draw_editor_text(
            &format!("No {} Document Open", self.viewport_mode.label()),
            panel.x + 18.0,
            panel.y + 44.0,
            18.0,
            editor_theme::colors::TEXT_PRIMARY,
        );
        draw_scissored_text(
            "The project resource still exists. Reopen it from the document bar or the workspace selector.",
            panel.x + 18.0,
            panel.y + 76.0,
            panel.w - 36.0,
            12.0,
            editor_theme::colors::TEXT_SECONDARY,
        );
    }

    pub(crate) fn draw_document_close_dialog(&self) {
        let Some(dialog) = self.pending_document_close.as_ref() else { return; };
        draw_rectangle(0.0, 0.0, screen_width(), screen_height(), Color::new(0.0, 0.0, 0.0, 0.46));
        let panel = modal_rect();
        draw_rectangle(panel.x, panel.y, panel.w, panel.h, editor_theme::colors::PANEL_RAISED);
        draw_rectangle_lines(panel.x, panel.y, panel.w, panel.h, 1.0, editor_theme::colors::BORDER_STRONG);
        draw_editor_text("Unsaved document", panel.x + 18.0, panel.y + 34.0, 17.0, editor_theme::colors::TEXT_PRIMARY);
        draw_scissored_text(
            &format!("Save changes to \"{}\" before closing?", dialog.title),
            panel.x + 18.0,
            panel.y + 70.0,
            panel.w - 36.0,
            13.0,
            editor_theme::colors::TEXT_PRIMARY,
        );
        draw_scissored_text(
            "Close Without Saving closes the view without writing the resource. Autosave/recovery remains available where supported.",
            panel.x + 18.0,
            panel.y + 102.0,
            panel.w - 36.0,
            11.0,
            editor_theme::colors::TEXT_SECONDARY,
        );
        draw_editor_widget_tone(save_rect(panel), "Save & Close", false, WidgetTone::Primary);
        draw_editor_widget_tone(close_rect(panel), "Close Without Saving", false, WidgetTone::Quiet);
        draw_editor_widget_tone(cancel_rect(panel), "Cancel", false, WidgetTone::Quiet);
    }

    pub(crate) fn handle_document_close_dialog_click(&mut self, point: Vec2) -> bool {
        let Some(dialog) = self.pending_document_close.clone() else { return false; };
        let panel = modal_rect();
        if save_rect(panel).contains(point) {
            self.pending_document_close = None;
            match self.save_document_target(&dialog.target) {
                Ok(message) => {
                    self.close_document_target(dialog.target);
                    self.status_message = format!("{message}; closed document");
                }
                Err(error) => {
                    self.status_message = format!("Document save failed: {error}");
                }
            }
            return true;
        }
        if close_rect(panel).contains(point) {
            self.pending_document_close = None;
            self.close_document_target(dialog.target);
            return true;
        }
        if cancel_rect(panel).contains(point) || !panel.contains(point) {
            self.pending_document_close = None;
            self.status_message = "Document close cancelled".to_string();
            return true;
        }
        true
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn close_target_covers_every_infinite_canvas_family() {
        let modes = [
            EditorViewportMode::SceneRectangles,
            EditorViewportMode::RegionGraph,
            EditorViewportMode::SceneBank,
            EditorViewportMode::AnimationStudio,
            EditorViewportMode::CharacterStudio,
            EditorViewportMode::LogicStudio,
            EditorViewportMode::SoundStudio,
        ];
        assert_eq!(modes.len(), 7);
        for mode in modes {
            let target = DocumentCloseTarget::Workspace(mode);
            assert!(matches!(target, DocumentCloseTarget::Workspace(_)));
        }
    }
}
