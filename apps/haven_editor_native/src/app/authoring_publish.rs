use super::render_helpers::*;
use super::*;
use haven_authoring::{AuthoringSession, AuthoringSource, AuthoringSourceKind, PublishPreview, PublishTarget};
use std::fs;
use std::path::Path;

const PANEL_W: f32 = 430.0;
const ROW_H: f32 = 32.0;

fn publish_panel_rect() -> Rect {
    let w = screen_width();
    let h = screen_height();
    let height = 150.0 + ROW_H * PublishTarget::ALL.len() as f32;
    Rect::new((w - PANEL_W) * 0.5, (h - height) * 0.5, PANEL_W, height)
}

fn target_rect(panel: Rect, index: usize) -> Rect {
    Rect::new(panel.x + 18.0, panel.y + 74.0 + index as f32 * ROW_H, panel.w - 36.0, ROW_H - 4.0)
}

fn everywhere_rect(panel: Rect) -> Rect {
    Rect::new(panel.x + 18.0, panel.y + panel.h - 60.0, 126.0, 34.0)
}

fn publish_rect(panel: Rect) -> Rect {
    Rect::new(panel.x + panel.w - 214.0, panel.y + panel.h - 60.0, 96.0, 34.0)
}

fn cancel_rect(panel: Rect) -> Rect {
    Rect::new(panel.x + panel.w - 110.0, panel.y + panel.h - 60.0, 92.0, 34.0)
}

impl EditorApp {
    pub(crate) fn begin_authoring_publish(&mut self) {
        let source = match self.viewport_mode {
            EditorViewportMode::SceneRectangles => self.world_selection.map(|selection| AuthoringSource {
                kind: AuthoringSourceKind::WorldSelection,
                label: format!("World selection {}x{} at {},{}", selection.width(), selection.height(), selection.min.x, selection.min.y),
                scene_id: None,
                world_rect: Some([selection.min.x, selection.min.y, selection.width(), selection.height()]),
                asset_ids: Vec::new(),
            }),
            EditorViewportMode::SceneMap => self.selection.bounds.map(|selection| AuthoringSource {
                kind: AuthoringSourceKind::SceneSelection,
                label: format!("Scene selection {}x{} at {},{}", selection.width(), selection.height(), selection.min.x, selection.min.y),
                scene_id: self.model.world.scenes.get(self.selected_scene).map(|scene| scene.id.code().to_string()),
                world_rect: Some([selection.min.x, selection.min.y, selection.width(), selection.height()]),
                asset_ids: Vec::new(),
            }),
            EditorViewportMode::PixelStudio => self.pixel_studio.document.as_ref().map(|document| AuthoringSource {
                kind: if self.pixel_studio.world_region_context.as_ref().is_some_and(|context| context.scope_kind == "building_composite") {
                    AuthoringSourceKind::BuildingComposite
                } else {
                    AuthoringSourceKind::Asset
                },
                label: document.metadata.display_name.clone(),
                scene_id: self.pixel_studio.world_region_context.as_ref().map(|context| context.scene_id.code().to_string()),
                world_rect: self.pixel_studio.world_region_context.as_ref().map(|context| [context.global_rect.min.x, context.global_rect.min.y, context.global_rect.width(), context.global_rect.height()]),
                asset_ids: vec![document.metadata.asset_id.clone()],
            }),
            EditorViewportMode::AnimationStudio => self.animation_studio.document.as_ref().map(|document| AuthoringSource {
                kind: AuthoringSourceKind::Animation,
                label: document.metadata.display_name.clone(),
                scene_id: None,
                world_rect: None,
                asset_ids: vec![document.metadata.asset_id.clone()],
            }),
            EditorViewportMode::CharacterStudio => Some(AuthoringSource {
                kind: AuthoringSourceKind::Character,
                label: "Character Studio working composition".to_string(),
                scene_id: None,
                world_rect: None,
                asset_ids: Vec::new(),
            }),
            EditorViewportMode::SoundStudio => Some(AuthoringSource {
                kind: AuthoringSourceKind::Sound,
                label: self.sound_studio.document.display_name.clone(),
                scene_id: None,
                world_rect: None,
                asset_ids: vec![self.sound_studio.document.id.to_string()],
            }),
            EditorViewportMode::LogicStudio => Some(AuthoringSource {
                kind: AuthoringSourceKind::Logic,
                label: self.logic_studio.graph.display_name.clone(),
                scene_id: None,
                world_rect: None,
                asset_ids: vec![self.logic_studio.graph.id.to_string()],
            }),
            EditorViewportMode::RegionGraph | EditorViewportMode::SceneBank => None,
        };
        let Some(source) = source else {
            self.status_message = "Select/open an authoring scope before publishing".to_string();
            return;
        };
        self.authoring_session = Some(AuthoringSession::new(source));
        self.status_message = "Publish Authored Composition opened".to_string();
    }

    pub(crate) fn draw_authoring_publish_panel(&self) {
        let Some(session) = self.authoring_session.as_ref() else { return; };
        let panel = publish_panel_rect();
        draw_rectangle(0.0, 0.0, screen_width(), screen_height(), Color::new(0.0, 0.0, 0.0, 0.38));
        draw_rectangle(panel.x, panel.y, panel.w, panel.h, Color::new(0.075, 0.075, 0.075, 1.0));
        draw_rectangle_lines(panel.x, panel.y, panel.w, panel.h, 1.0, editor_theme::colors::BORDER_STRONG);
        draw_editor_text("Publish Authored Composition", panel.x + 18.0, panel.y + 28.0, 18.0, editor_theme::colors::TEXT_PRIMARY);
        draw_scissored_text(&session.source.label, panel.x + 18.0, panel.y + 51.0, panel.w - 36.0, 12.0, editor_theme::colors::TEXT_SECONDARY);
        for (index, target) in PublishTarget::ALL.into_iter().enumerate() {
            let rect = target_rect(panel, index);
            let selected = session.publish_targets.contains(&target);
            draw_editor_widget_tone(
                rect,
                &format!("{}  {}", if selected { "●" } else { "○" }, target.label()),
                selected,
                WidgetTone::Quiet,
            );
        }
        draw_editor_widget_tone(everywhere_rect(panel), "Publish Everywhere", false, WidgetTone::Quiet);
        draw_editor_widget_tone(publish_rect(panel), "Publish", session.can_publish(), if session.can_publish() { WidgetTone::Primary } else { WidgetTone::Disabled });
        draw_editor_widget_tone(cancel_rect(panel), "Cancel", false, WidgetTone::Quiet);
    }

    pub(crate) fn handle_authoring_publish_click(&mut self, mx: f32, my: f32) -> bool {
        let Some(session) = self.authoring_session.as_mut() else { return false; };
        let panel = publish_panel_rect();
        let point = vec2(mx, my);
        if !panel.contains(point) {
            return true;
        }
        for (index, target) in PublishTarget::ALL.into_iter().enumerate() {
            if target_rect(panel, index).contains(point) {
                session.toggle_target(target);
                return true;
            }
        }
        if everywhere_rect(panel).contains(point) {
            session.enable_publish_everywhere();
            return true;
        }
        if cancel_rect(panel).contains(point) {
            self.authoring_session = None;
            self.status_message = "Publish cancelled".to_string();
            return true;
        }
        if publish_rect(panel).contains(point) {
            let session = session.clone();
            self.status_message = match self.execute_authoring_publish(&session) {
                Ok(outputs) => format!("Published authoring revision {} to {} destination{}", session.revision, outputs.len(), if outputs.len() == 1 { "" } else { "s" }),
                Err(error) => format!("Publish failed: {error}"),
            };
            if !self.status_message.starts_with("Publish failed") {
                self.authoring_session = None;
            }
            return true;
        }
        true
    }

    fn execute_authoring_publish(&mut self, session: &AuthoringSession) -> Result<Vec<String>, String> {
        if !session.can_publish() {
            return Err("authoring session is not publishable".to_string());
        }
        let root = repo_root_dir();
        let transaction_root = root.join("WORKSPACE/authoring_publish");
        let staging = transaction_root.join("staging").join(session.revision.as_str());
        let committed = transaction_root.join("revisions").join(session.revision.as_str());
        if staging.exists() {
            fs::remove_dir_all(&staging).map_err(|error| error.to_string())?;
        }
        fs::create_dir_all(&staging).map_err(|error| error.to_string())?;
        let preview = PublishPreview::from(session);
        write_json(&staging.join("publish_preview.json"), &preview)?;
        write_json(&staging.join("authoring_session.json"), session)?;

        let mut generated = Vec::new();
        for target in &session.publish_targets {
            let file = match target {
                PublishTarget::ApplyHere => "apply_here.json",
                PublishTarget::Variation => "variation.json",
                PublishTarget::Asset => "asset_promotion.json",
                PublishTarget::StampMotif => "stamp_motif.json",
                PublishTarget::Template => "template.json",
                PublishTarget::PresentationSet => "presentation_set.json",
                PublishTarget::PcgExemplar => "pcg_exemplar.json",
                PublishTarget::PcgMotifs => "pcg_motifs.json",
            };
            let value = serde_json::json!({
                "schema": "havenwild.authoring_publish_product.v1",
                "sessionId": session.id.to_string(),
                "revisionId": session.revision.to_string(),
                "target": target,
                "source": &session.source,
                "status": "committed_metadata",
                "notes": "Semantic product metadata is committed atomically with sibling targets. Domain-specific promotion/baking may add runtime bindings in later passes without changing this revision identity."
            });
            write_json(&staging.join(file), &value)?;
            generated.push(file.to_string());
        }

        if committed.exists() {
            fs::remove_dir_all(&committed).map_err(|error| error.to_string())?;
        }
        if let Some(parent) = committed.parent() {
            fs::create_dir_all(parent).map_err(|error| error.to_string())?;
        }
        fs::rename(&staging, &committed).map_err(|error| format!("publish commit failed: {error}"))?;

        if session.publish_targets.contains(&PublishTarget::ApplyHere)
            && matches!(&session.source.kind, AuthoringSourceKind::WorldSelection | AuthoringSourceKind::SceneSelection | AuthoringSourceKind::BuildingComposite)
        {
            let editor_world_path = development_session::editor_world_path();
            save_world_to_path(&editor_world_path.to_string_lossy(), &self.model.world)
                .map_err(|error| format!("authoring metadata committed but world persistence failed: {error}"))?;
        }
        if session.publish_targets.contains(&PublishTarget::PcgExemplar)
            && session.source.kind == AuthoringSourceKind::WorldSelection
        {
            self.promote_world_selection_to_pcg_exemplar();
        }

        let relative = committed.strip_prefix(&root).unwrap_or(&committed).display().to_string();
        generated.push(relative);
        Ok(generated)
    }
}

fn write_json(path: &Path, value: &impl serde::Serialize) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|error| error.to_string())?;
    }
    let text = serde_json::to_string_pretty(value).map_err(|error| error.to_string())?;
    fs::write(path, format!("{text}\n")).map_err(|error| error.to_string())
}
