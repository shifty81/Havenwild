use std::fs::create_dir_all;
use std::path::Path;

use haven_assets::asset_intake::repo_root_dir;
use image::{Rgba, RgbaImage};

use super::command_registry::{
    EditorCommandId, MenuCommand, ASSET_COMMANDS, BUILD_COMMANDS, EDIT_COMMANDS, FILE_COMMANDS,
    HELP_COMMANDS, SCENE_COMMANDS, TOOLS_COMMANDS, VIEW_COMMANDS, WORLD_COMMANDS,
};
use super::render_helpers::{draw_editor_widget, draw_editor_widget_tone, WidgetTone};
use super::ui_shell::EditorShellLayout;
use super::*;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum EditorMenuKind {
    File,
    Edit,
    View,
    World,
    Scene,
    Asset,
    Build,
    Tools,
    Help,
}

impl EditorMenuKind {
    const ALL: [Self; 9] = [
        Self::File, Self::Edit, Self::View, Self::World, Self::Scene,
        Self::Asset, Self::Build, Self::Tools, Self::Help,
    ];

    fn label(self) -> &'static str {
        match self {
            Self::File => "File",
            Self::Edit => "Edit",
            Self::View => "View",
            Self::World => "World",
            Self::Scene => "Scene",
            Self::Asset => "Asset",
            Self::Build => "Build",
            Self::Tools => "Tools",
            Self::Help => "Help",
        }
    }

    fn commands(self) -> &'static [MenuCommand] {
        match self {
            Self::File => FILE_COMMANDS,
            Self::Edit => EDIT_COMMANDS,
            Self::View => VIEW_COMMANDS,
            Self::World => WORLD_COMMANDS,
            Self::Scene => SCENE_COMMANDS,
            Self::Asset => ASSET_COMMANDS,
            Self::Build => BUILD_COMMANDS,
            Self::Tools => TOOLS_COMMANDS,
            Self::Help => HELP_COMMANDS,
        }
    }

    fn index(self) -> usize {
        Self::ALL.iter().position(|candidate| *candidate == self).unwrap_or(0)
    }
}

pub(crate) fn menu_item_rect(index: usize) -> Rect {
    Rect::new(8.0 + index as f32 * 58.0, 7.0, 54.0, 30.0)
}

pub(crate) fn save_all_button_rect(width: f32) -> Rect { Rect::new(width - 130.0, 7.0, 82.0, 30.0) }

fn development_play_rect(width: f32) -> Rect { Rect::new(width - 472.0, 7.0, 70.0, 30.0) }
fn development_here_rect(width: f32) -> Rect { Rect::new(width - 398.0, 7.0, 102.0, 30.0) }
fn development_stop_rect(width: f32) -> Rect { Rect::new(width - 292.0, 7.0, 58.0, 30.0) }
fn development_restart_rect(width: f32) -> Rect { Rect::new(width - 230.0, 7.0, 58.0, 30.0) }

fn dropdown_rect(kind: EditorMenuKind) -> Rect {
    let origin = menu_item_rect(kind.index());
    Rect::new(origin.x, 39.0, 304.0, kind.commands().len() as f32 * 30.0 + 8.0)
}

impl EditorApp {
    pub(crate) fn draw_editor_menus(&self, width: f32) {
        for (index, kind) in EditorMenuKind::ALL.into_iter().enumerate() {
            draw_editor_widget(menu_item_rect(index), kind.label(), self.open_menu == Some(kind));
        }
        let dev_running = self.development_client.is_some();
        draw_editor_widget_tone(development_play_rect(width), "Play", dev_running, WidgetTone::Primary);
        draw_editor_widget_tone(development_here_rect(width), "Play From Here", false, WidgetTone::Quiet);
        draw_editor_widget_tone(development_stop_rect(width), "Stop", false, WidgetTone::Quiet);
        draw_editor_widget_tone(development_restart_rect(width), "Restart", false, WidgetTone::Quiet);
        draw_editor_widget_tone(save_all_button_rect(width), "Save", false, WidgetTone::Primary);
        draw_editor_widget_tone(editor_settings::settings_button_rect(width), "⚙", self.editor_settings.open, WidgetTone::Quiet);

        let Some(kind) = self.open_menu else { return; };
        let dropdown = dropdown_rect(kind);
        draw_rectangle(dropdown.x, dropdown.y, dropdown.w, dropdown.h, Color::new(0.035, 0.045, 0.058, 0.99));
        draw_rectangle_lines(dropdown.x, dropdown.y, dropdown.w, dropdown.h, 1.0, PANEL_EDGE);
        for (index, command) in kind.commands().iter().enumerate() {
            let row = Rect::new(dropdown.x + 4.0, dropdown.y + 4.0 + index as f32 * 30.0, dropdown.w - 8.0, 28.0);
            draw_editor_widget_tone(row, command.label, false, WidgetTone::Quiet);
        }
    }

    pub(crate) fn handle_editor_menu_click(&mut self, mx: f32, my: f32) -> bool {
        let point = vec2(mx, my);
        let width = screen_width();
        if development_play_rect(width).contains(point) { self.open_menu=None; self.execute_editor_command(EditorCommandId::Play); return true; }
        if development_here_rect(width).contains(point) { self.open_menu=None; self.execute_editor_command(EditorCommandId::PlayFromHere); return true; }
        if development_stop_rect(width).contains(point) { self.open_menu=None; self.execute_editor_command(EditorCommandId::Stop); return true; }
        if development_restart_rect(width).contains(point) { self.open_menu=None; self.execute_editor_command(EditorCommandId::Restart); return true; }
        if editor_settings::settings_button_rect(width).contains(point) { self.open_editor_settings(); return true; }
        if save_all_button_rect(width).contains(point) { self.open_menu=None; self.execute_editor_command(EditorCommandId::SaveAll); return true; }
        for (index, kind) in EditorMenuKind::ALL.into_iter().enumerate() {
            if menu_item_rect(index).contains(point) {
                self.open_menu = (self.open_menu != Some(kind)).then_some(kind);
                return true;
            }
        }
        let Some(kind) = self.open_menu else { return false; };
        let dropdown = dropdown_rect(kind);
        if !dropdown.contains(point) { self.open_menu = None; return true; }
        let index = ((my - dropdown.y - 4.0) / 30.0).floor().max(0.0) as usize;
        let command = kind.commands().get(index).map(|item| item.id);
        self.open_menu = None;
        if let Some(command) = command { self.execute_editor_command(command); }
        true
    }

    /// One implementation per editor command. Menus are only one presentation
    /// surface; context menus, shortcuts, and future command-palette search should
    /// invoke this same command vocabulary rather than duplicating workflows.
    pub(crate) fn execute_editor_command(&mut self, command: EditorCommandId) {
        let scene_command_context = if self.viewport_mode == EditorViewportMode::SceneMap
            && self.scene_workspace_has_open_document()
        {
            self.active_scene_id().map(|id| (id, self.command_bus.undo_len()))
        } else {
            None
        };
        match command {
            EditorCommandId::SaveAll => self.save_all_editor_documents(),
            EditorCommandId::ReloadSaved => self.reload_all_editor_documents(),
            EditorCommandId::CloseActiveDocument => { let _ = self.request_close_active_document(); },
            EditorCommandId::ReopenClosedDocument => { let _ = self.reopen_last_closed_document(); },
            EditorCommandId::NewSceneDocument => self.begin_new_scene_from_document_bar(),
            EditorCommandId::BrowseProjectScenes => self.browse_project_scenes(),
            EditorCommandId::CloseSceneDocument => {
                if !self.request_close_active_document() {
                    self.status_message = "No Scene document is open".to_string();
                }
            }
            EditorCommandId::ReopenClosedSceneDocument => {
                self.reopen_last_closed_document();
            }
            EditorCommandId::CloseAllPixelDocuments => {
                if !self.request_close_all_pixel_documents() {
                    self.status_message = "No Pixel Studio documents are open".to_string();
                }
            }
            EditorCommandId::Undo => self.undo_contextual_edit(),
            EditorCommandId::Redo => self.redo_contextual_edit(),
            EditorCommandId::Cut => self.cut_contextual_selection(),
            EditorCommandId::Copy => self.copy_contextual_selection(false),
            EditorCommandId::CopyMerged => self.copy_contextual_selection(true),
            EditorCommandId::Paste => self.paste_contextual_selection(),
            EditorCommandId::Duplicate => self.duplicate_contextual_selection(),
            EditorCommandId::MirrorHorizontal => self.mirror_contextual_selection(true),
            EditorCommandId::MirrorVertical => self.mirror_contextual_selection(false),
            EditorCommandId::PromoteSelection => self.promote_contextual_selection(),
            EditorCommandId::OpenWorld => {
                self.viewport_mode = EditorViewportMode::SceneRectangles;
                self.reopen_workspace_document(EditorViewportMode::SceneRectangles);
                self.frame_entire_world();
            },
            EditorCommandId::OpenScene => self.activate_scene_workspace(),
            EditorCommandId::OpenPixel => self.viewport_mode = EditorViewportMode::PixelStudio,
            EditorCommandId::OpenAnimation => { self.viewport_mode = EditorViewportMode::AnimationStudio; self.reopen_workspace_document(EditorViewportMode::AnimationStudio); },
            EditorCommandId::OpenCharacter => { self.viewport_mode = EditorViewportMode::CharacterStudio; self.reopen_workspace_document(EditorViewportMode::CharacterStudio); },
            EditorCommandId::OpenLogic => { self.viewport_mode = EditorViewportMode::LogicStudio; self.reopen_workspace_document(EditorViewportMode::LogicStudio); },
            EditorCommandId::OpenSound => { self.viewport_mode = EditorViewportMode::SoundStudio; self.reopen_workspace_document(EditorViewportMode::SoundStudio); },
            EditorCommandId::OpenWorldRoutes => { self.viewport_mode = EditorViewportMode::RegionGraph; self.reopen_workspace_document(EditorViewportMode::RegionGraph); },
            EditorCommandId::OpenSceneBank => { self.viewport_mode = EditorViewportMode::SceneBank; self.reopen_workspace_document(EditorViewportMode::SceneBank); },
            EditorCommandId::OpenUiDocuments => self.open_game_canvas_ui_documents(),
            EditorCommandId::ToggleRightDock => self.toggle_right_workspace_panel(),
            EditorCommandId::ToggleBottomDock => self.toggle_bottom_workspace_panel(),
            EditorCommandId::DockProperties => self.focus_right_dock(RightDockTab::Properties),
            EditorCommandId::DockAssets => self.focus_right_dock(RightDockTab::Assets),
            EditorCommandId::DockOutliner => self.focus_right_dock(RightDockTab::Outliner),
            EditorCommandId::DockValidation => self.focus_right_dock(RightDockTab::Validation),
            EditorCommandId::ToggleLayoutAudit => {
                self.layout_audit_overlay = !self.layout_audit_overlay;
                let layout = self.shell_layout();
                let issues = shell_layout_audit_issues(&layout, screen_width(), screen_height());
                self.status_message = if issues.is_empty() {
                    format!("Layout audit {} | no shell overlaps detected", if self.layout_audit_overlay { "enabled" } else { "disabled" })
                } else {
                    format!("Layout audit {} | {}", if self.layout_audit_overlay { "enabled" } else { "disabled" }, issues.join(" | "))
                };
            }
            EditorCommandId::ResetLayout => self.reset_workspace_layout(),
            EditorCommandId::ToggleToolRail => {
                self.workspace_shell.canvas_tool_rail_collapsed = !self.workspace_shell.canvas_tool_rail_collapsed;
                let _ = self.workspace_shell.save_default();
            }
            EditorCommandId::ToggleLayerRail => {
                self.workspace_shell.canvas_layer_rail_collapsed = !self.workspace_shell.canvas_layer_rail_collapsed;
                let _ = self.workspace_shell.save_default();
            }
            EditorCommandId::TogglePalette => {
                self.workspace_shell.shared_palette_visible = !self.workspace_shell.shared_palette_visible;
                let _ = self.workspace_shell.save_default();
                self.status_message = format!("Shared palette {}", if self.workspace_shell.shared_palette_visible { "visible" } else { "hidden" });
            }
            EditorCommandId::FrameCanvas => self.frame_active_canvas(),
            EditorCommandId::RegenerateSeed => self.regenerate_current_archipelago_seed(),
            EditorCommandId::RerollArchipelago => self.reroll_structural_archipelago(),
            EditorCommandId::ExportIslandPngs => self.export_island_preview_pngs_with_status(),
            EditorCommandId::PixelEditSelection => match self.viewport_mode {
                EditorViewportMode::SceneMap => self.open_scene_selection_in_pixel_studio(),
                EditorViewportMode::SceneRectangles => self.open_world_selection_in_pixel_studio(),
                _ => self.viewport_mode = EditorViewportMode::PixelStudio,
            },
            EditorCommandId::Play => self.play_development_world(false),
            EditorCommandId::PlayFromHere => self.play_development_world(true),
            EditorCommandId::Restart => { self.stop_development_client(); self.play_development_world(false); }
            EditorCommandId::Stop => self.stop_development_client(),
            EditorCommandId::PublishComposition => self.begin_authoring_publish(),
            EditorCommandId::OpenAssetBrowser => self.focus_right_dock(RightDockTab::Assets),
            EditorCommandId::CreatePcgExemplar => self.promote_world_selection_to_pcg_exemplar(),
            EditorCommandId::RefreshAssetCatalog => {
                self.asset_hot_reload_requested = true;
                self.focus_right_dock(RightDockTab::Assets);
                self.status_message = "Asset catalog refresh requested".to_string();
            }
            EditorCommandId::HelpWelcome => self.open_help_center(editor_help::HelpPage::Welcome),
            EditorCommandId::HelpShortcuts => self.open_help_center(editor_help::HelpPage::Shortcuts),
            EditorCommandId::HelpCanvas => self.open_help_center(editor_help::HelpPage::Canvas),
            EditorCommandId::HelpAssets => self.open_help_center(editor_help::HelpPage::AssetBrowser),
            EditorCommandId::HelpPixel => self.open_help_center(editor_help::HelpPage::PixelAuthoring),
            EditorCommandId::HelpColor => self.open_help_center(editor_help::HelpPage::ColorPalette),
        }
        if let Some((scene_id, undo_before)) = scene_command_context {
            if self.command_bus.undo_len() != undo_before {
                self.scene_document_dirty_ids.insert(scene_id);
            }
        }
    }

    fn frame_active_canvas(&mut self) {
        match self.viewport_mode {
            EditorViewportMode::SceneMap => {
                let viewport = self.scene_canvas_viewport_rect();
                let bounds = self.scene_canvas_bounds();
                self.scene_canvas.frame_rect(viewport, bounds, bounds);
            }
            EditorViewportMode::SceneRectangles => {
                if let Some(bounds) = self.world_canvas_bounds() {
                    let viewport = self.world_canvas_viewport_rect();
                    self.world_canvas.frame_rect(viewport, bounds, bounds);
                }
            }
            EditorViewportMode::SceneBank => {
                self.status_message = "Scene Library uses an adaptive fixed-card layout; framing is not required".to_string();
                return;
            }
            EditorViewportMode::PixelStudio => self.pixel_studio.frame_document(self.pixel_canvas_rect()),
            _ => {}
        }
        self.status_message = format!("Framed {} canvas", self.viewport_mode.label());
    }

    fn undo_contextual_edit(&mut self) {
        if self.viewport_mode == EditorViewportMode::PixelStudio {
            if self.pixel_studio.document.as_mut().is_some_and(|document| document.undo()) {
                self.pixel_studio.refresh_texture();
                self.status_message = "Pixel edit undone".to_string();
            } else {
                self.status_message = "Pixel Studio has nothing to undo".to_string();
            }
        } else {
            self.undo_world_edit();
        }
    }

    fn redo_contextual_edit(&mut self) {
        if self.viewport_mode == EditorViewportMode::PixelStudio {
            if self.pixel_studio.document.as_mut().is_some_and(|document| document.redo()) {
                self.pixel_studio.refresh_texture();
                self.status_message = "Pixel edit redone".to_string();
            } else {
                self.status_message = "Pixel Studio has nothing to redo".to_string();
            }
        } else {
            self.redo_world_edit();
        }
    }

    fn copy_contextual_selection(&mut self, merged_visible: bool) {
        match self.viewport_mode {
            EditorViewportMode::PixelStudio => {
                self.status_message = match self.pixel_studio.copy_selection_to_clipboard(merged_visible) {
                    Ok(message) => message,
                    Err(error) => format!("Copy failed: {error}"),
                };
            }
            EditorViewportMode::SceneMap if !merged_visible => self.copy_selection_to_clipboard(),
            EditorViewportMode::SceneRectangles if !merged_visible => self.copy_world_selection(),
            EditorViewportMode::SceneMap | EditorViewportMode::SceneRectangles => {
                self.status_message = "Copy Merged is a Pixel Studio raster operation; scene/world copy preserves semantic content instead".to_string();
            }
            _ => {
                self.status_message = format!("Copy Selection is not yet available in {}", self.viewport_mode.label());
            }
        }
    }

    fn cut_contextual_selection(&mut self) {
        match self.viewport_mode {
            EditorViewportMode::PixelStudio => {
                self.status_message = match self.pixel_studio.cut_selection_to_clipboard() {
                    Ok(message) => message,
                    Err(error) => format!("Cut failed: {error}"),
                };
            }
            EditorViewportMode::SceneMap => self.cut_current_selection(),
            EditorViewportMode::SceneRectangles => {
                self.status_message = "World Editor Cut remains gated until every semantic world layer has a lossless delete adapter; Copy/Paste/Duplicate are available".to_string();
            }
            _ => {
                self.status_message = format!("Cut Selection is not yet available in {}", self.viewport_mode.label());
            }
        }
    }

    fn paste_contextual_selection(&mut self) {
        match self.viewport_mode {
            EditorViewportMode::PixelStudio => {
                self.status_message = match self.pixel_studio.paste_clipboard_into_selection() {
                    Ok(message) => format!("{message} | use the Transform Gizmo to reposition"),
                    Err(error) => format!("Paste failed: {error}"),
                };
            }
            EditorViewportMode::SceneMap => self.paste_clipboard_at_cursor(),
            EditorViewportMode::SceneRectangles => self.paste_world_selection(),
            _ => {
                self.status_message = format!("Paste is not yet available in {}", self.viewport_mode.label());
            }
        }
    }

    fn duplicate_contextual_selection(&mut self) {
        match self.viewport_mode {
            EditorViewportMode::PixelStudio => {
                self.status_message = match self.pixel_studio.duplicate_selection() {
                    Ok(message) => message,
                    Err(error) => format!("Duplicate failed: {error}"),
                };
            }
            EditorViewportMode::SceneMap => self.duplicate_current_selection(),
            EditorViewportMode::SceneRectangles => self.duplicate_world_selection(),
            _ => {
                self.status_message = format!("Duplicate Selection is not yet available in {}", self.viewport_mode.label());
            }
        }
    }

    fn mirror_contextual_selection(&mut self, horizontal: bool) {
        if self.viewport_mode != EditorViewportMode::PixelStudio {
            self.status_message = "Selection mirroring currently requires Pixel Studio raster selection authority".to_string();
            return;
        }
        let Some(document) = self.pixel_studio.document.as_mut() else {
            self.status_message = "Open a Pixel Studio document before mirroring a selection".to_string();
            return;
        };
        if horizontal {
            document.flip_selection_horizontal();
            self.status_message = "Mirrored Pixel selection horizontally".to_string();
        } else {
            document.flip_selection_vertical();
            self.status_message = "Mirrored Pixel selection vertically".to_string();
        }
        self.pixel_studio.refresh_texture();
    }

    fn promote_contextual_selection(&mut self) {
        if self.viewport_mode != EditorViewportMode::PixelStudio {
            self.status_message = "Promote Selection to Asset currently operates on an exact Pixel Studio selection; use Edit Selected Region first for live world composition".to_string();
            return;
        }
        self.status_message = match self.pixel_studio.open_promote_selection_wizard() {
            Ok(message) => message,
            Err(error) => format!("Promote Selection failed: {error}"),
        };
    }

    pub(crate) fn save_all_editor_documents(&mut self) {
        let root = repo_root_dir();
        let project_path = root.join(STARTER_PROJECT_FILE_PATH);
        let scene_manifest_path = root.join(SCENE_RECTANGLE_MANIFEST_PATH);
        let scene_assignments_path = root.join(SCENE_RECTANGLE_ASSIGNMENTS_PATH);
        let harbor_route_path = root.join(HARBOR_ROUTE_CATALOG_PATH);
        let project_result = self.model.project.save_to_path(&project_path.to_string_lossy());
        let manifest_result = self
            .scene_rectangles
            .as_ref()
            .ok_or_else(|| "scene rectangle manifest is unavailable".to_string())
            .and_then(|manifest| manifest.save_to_path(&scene_manifest_path.to_string_lossy()));
        let assignment_result = self
            .scene_assignments
            .save_to_path(&scene_assignments_path.to_string_lossy());
        let route_result = self.harbor_routes.save_to_path(&harbor_route_path.to_string_lossy());
        let editor_world_path = development_session::editor_world_path();
        let world_result = save_world_to_path(&editor_world_path.to_string_lossy(), &self.model.world);
        let preview_result = self.export_island_preview_pngs();
        let pixel_result = if self.pixel_studio.world_region_context.is_some() {
            self.persist_active_world_region_pixels().map(|_| ())
        } else {
            self.pixel_studio
                .document
                .as_mut()
                .map_or(Ok(()), |document| document.save(repo_root_dir()))
        };
        let pixel_result = pixel_result.and_then(|_| {
            self.pixel_studio.save_inactive_documents().map(|_| ())
        });
        let animation_result = self
            .animation_studio
            .document
            .as_mut()
            .map_or(Ok(()), |document| document.save(repo_root_dir()));
        let sound_path = root.join("WORKSPACE/audio/documents").join(format!("{}.hhsound.json", self.sound_studio.document.id));
        let sound_result = self.sound_studio.document.save_to_path(&sound_path);
        let logic_path = root.join("WORKSPACE/logic/documents").join(format!("{}.hhlogic.json", self.logic_studio.graph.id));
        let logic_result = self.logic_studio.graph.save_to_path(&logic_path);
        let ui_result = if self.game_canvas_ui.active() && self.game_canvas_ui.dirty {
            self.game_canvas_ui.save_active()
        } else {
            Ok(())
        };
        match (
            project_result,
            manifest_result,
            assignment_result,
            route_result,
            world_result,
            preview_result,
            pixel_result,
            animation_result,
            sound_result,
            logic_result,
            ui_result,
        ) {
            (Ok(()), Ok(()), Ok(()), Ok(()), Ok(()), Ok(count), Ok(()), Ok(()), Ok(()), Ok(()), Ok(())) => {
                if let Err(error) = self.character_studio.save_recipe_draft() {
                    self.status_message = format!("Save failed: {error}");
                    return;
                }
                self.saved_undo_depth = self.command_bus.undo_len();
                self.clear_scene_document_dirty_state();
                self.sound_studio.dirty = false;
                self.logic_studio.dirty = false;
                let _ = self.workspace_shell.save_default();
                self.status_message = format!(
                    "Saved project, island layout, assignments, harbor routes, editable world, pixel/animation/logic/sound/UI documents, and {count} assembled island PNG previews"
                );
                self.command_bus.record_event(
                    self.app_command(EditorCommandKind::SaveWorld, self.status_message.clone()),
                );
            }
            (Err(error), _, _, _, _, _, _, _, _, _, _)
            | (_, Err(error), _, _, _, _, _, _, _, _, _)
            | (_, _, Err(error), _, _, _, _, _, _, _, _)
            | (_, _, _, Err(error), _, _, _, _, _, _, _)
            | (_, _, _, _, Err(error), _, _, _, _, _, _)
            | (_, _, _, _, _, Err(error), _, _, _, _, _)
            | (_, _, _, _, _, _, Err(error), _, _, _, _)
            | (_, _, _, _, _, _, _, Err(error), _, _, _)
            | (_, _, _, _, _, _, _, _, Err(error), _, _)
            | (_, _, _, _, _, _, _, _, _, Err(error), _)
            | (_, _, _, _, _, _, _, _, _, _, Err(error)) => {
                self.status_message = format!("Save failed: {error}")
            }
        }
    }

    pub(crate) fn play_development_world(&mut self, from_here: bool) {
        // Editor-owned development play must launch the authored state the
        // editor is showing, not an older on-disk scene.
        self.save_all_editor_documents();
        if self.status_message.starts_with("Save failed:") {
            return;
        }
        self.stop_development_client();
        let descriptor = match development_session::DevelopmentWorldDescriptor::load() {
            Ok(descriptor) => descriptor,
            Err(error) => {
                self.status_message = format!("Development world unavailable: {error}");
                return;
            }
        };
        // Play From Here follows the active authoring surface. Continuous World
        // Editor coordinates are global, so resolve them back to the owning scene
        // partition/local cell before launching the client. Scene Editor coordinates
        // are already local. This keeps the authoring cursor and runtime spawn exact.
        let world_surface_target = if self.viewport_mode == EditorViewportMode::SceneRectangles {
            self.scene_rectangles.as_ref().and_then(|manifest| {
                resolve_world_surface_cell(
                    manifest,
                    &self.scene_assignments,
                    &self.model.world,
                    self.selected_landmass_id,
                    GridPos { x: self.world_cursor_x, y: self.world_cursor_y },
                ).ok()
            })
        } else {
            None
        };
        let active_scene_id = world_surface_target.as_ref().map(|address| address.scene_id.clone()).or_else(|| self.active_scene_id());
        let Some(active_scene_id) = active_scene_id else {
            self.status_message = "Play requires an open World or Scene authoring target".to_string();
            return;
        };
        let active_scene = active_scene_id.to_string();
        let selected_scene_spawn = self.model.world.scene_by_id(&active_scene_id)
            .map(|scene| [scene.spawn_x, scene.spawn_y])
            .unwrap_or([descriptor.spawn.x, descriptor.spawn.y]);
        let from_here_spawn = world_surface_target
            .as_ref()
            .map(|address| [address.local.x, address.local.y])
            .unwrap_or([self.scene_cursor_x, self.scene_cursor_y]);
        let mut published_world = self.model.world.clone();
        if let Err(error) = published_world
            .set_active_scene(haven_core::ProjectSceneId::new(active_scene.clone()))
        {
            self.status_message = format!(
                "Development publish failed to activate editor scene {active_scene}: {error}"
            );
            return;
        }
        if let Some(parent) = descriptor.world_path().parent() {
            if let Err(error) = std::fs::create_dir_all(parent) {
                self.status_message = format!("Development publish failed: {error}");
                return;
            }
        }
        let development_world_path = descriptor.world_path();
        let editor_sync = haven_core::format_world_sync(
            "EDITOR",
            &published_world,
            Some(&haven_core::ProjectSceneId::new(active_scene.clone())),
        );
        eprintln!("{editor_sync}");
        crate::append_editor_log(&editor_sync);
        if let Err(error) = haven_save::save_world_to_path(
            &development_world_path.to_string_lossy(),
            &published_world,
        ) {
            self.status_message = format!("Development publish failed: {error}");
            return;
        }
        let published_sync = haven_core::format_world_sync(
            "PUBLISHED",
            &published_world,
            Some(&haven_core::ProjectSceneId::new(active_scene.clone())),
        );
        eprintln!("{published_sync}");
        crate::append_editor_log(&published_sync);
        match haven_save::load_world_from_path(&development_world_path.to_string_lossy()) {
            Ok(roundtrip) => {
                let roundtrip_sync = haven_core::format_world_sync(
                    "ROUNDTRIP",
                    &roundtrip,
                    Some(&haven_core::ProjectSceneId::new(active_scene.clone())),
                );
                eprintln!("{roundtrip_sync}");
                crate::append_editor_log(&roundtrip_sync);
            }
            Err(error) => {
                self.status_message = format!("Development round-trip verification failed: {error}");
                return;
            }
        }
        if let Err(error) = development_session::persist_development_world_authority(
            &self.development_world_settings,
            self.development_world_semantic_bake.as_ref(),
        ) {
            self.status_message = format!("Development world authority publish failed: {error}");
            return;
        }
        // A development publish is an authored snapshot, not an old procedural
        // save. Publish current-generation metadata with it so startup never
        // runs PCG migration/population over the editor-authored scene.
        let metadata_path = development_world_path
            .parent()
            .unwrap_or_else(|| std::path::Path::new("."))
            .join("world.json");
        let world_id = haven_save::WorldSaveId(descriptor.world_id.clone());
        let mut metadata = haven_save::WorldSaveMetadata::new(
            world_id,
            "Havenwild Editor Development World",
            self.development_world_settings.seed,
            published_world.scenes.len().max(1),
        );
        metadata.generated_exterior_scene_count = published_world
            .scenes
            .iter()
            .filter(|scene| scene.kind == SceneKind::Exterior)
            .count();
        metadata.starting_scene_code = active_scene.clone();
        if let Err(error) = haven_save::save_world_save_metadata(
            &metadata_path.to_string_lossy(),
            &metadata,
        ) {
            self.status_message = format!("Development metadata publish failed: {error}");
            return;
        }
        let scene = Some(active_scene.as_str());
        let spawn = if from_here {
            Some(from_here_spawn)
        } else {
            Some(selected_scene_spawn)
        };
        crate::append_editor_log(&format!(
            "Development Play launch: world={} scene={} spawn={},{} mode={}",
            descriptor.world_id,
            active_scene,
            spawn.map(|value| value[0]).unwrap_or(selected_scene_spawn[0]),
            spawn.map(|value| value[1]).unwrap_or(selected_scene_spawn[1]),
            if from_here { "from-here" } else { "scene-default" }
        ));
        match development_session::launch(&descriptor, scene, spawn) {
            Ok(child) => {
                self.development_client = Some(child);
                self.status_message = if from_here {
                    format!("Play From Here: {} at {}, {}", scene.unwrap_or("active scene"), from_here_spawn[0], from_here_spawn[1])
                } else {
                    format!("Playing editor scene {} in development world {}", active_scene, descriptor.world_id)
                };
            }
            Err(error) => self.status_message = format!("Development client launch failed: {error}"),
        }
    }

    pub(crate) fn poll_development_client(&mut self) {
        let Some(child) = self.development_client.as_mut() else { return; };
        match child.try_wait() {
            Ok(Some(status)) => {
                self.development_client = None;
                crate::append_editor_log(&format!(
                    "Development client exited ({status}); shared editor UI authority retained"
                ));
                self.status_message = format!("Development client exited ({status}); editor UI retained");
            }
            Ok(None) => {}
            Err(error) => {
                self.development_client = None;
                crate::append_editor_log(&format!(
                    "Development client status failed: {error}; shared editor UI authority retained"
                ));
                self.status_message = format!("Development client status failed: {error}");
            }
        }
    }

    pub(crate) fn stop_development_client(&mut self) {
        let Some(mut child) = self.development_client.take() else {
            return;
        };
        self.status_message = match development_session::stop(&mut child) {
            Ok(()) => {
                crate::append_editor_log(
                    "Development client stopped; shared editor UI authority retained"
                );
                "Development client stopped; editor UI retained".to_string()
            }
            Err(error) => format!("Unable to stop development client: {error}"),
        };
    }

    pub(crate) fn reload_all_editor_documents(&mut self) {
        match (
            load_editor_project_file_from_path(STARTER_PROJECT_FILE_PATH),
            load_active_scene_rectangle_manifest(),
            load_active_scene_rectangle_assignments(),
            HarborRouteCatalog::load_from_path(HARBOR_ROUTE_CATALOG_PATH),
            load_world_from_path(&development_session::editor_world_path().to_string_lossy()),
        ) {
            (Ok(project), Ok(manifest), Ok(assignments), Ok(routes), Ok(world)) => {
                self.model.project = project;
                self.scene_rectangles = Some(manifest);
                self.scene_assignments = assignments;
                self.harbor_routes = routes;
                self.model.world = world;
                self.model.region_graph = haven_world::region_graph::starter_island_region_graph();
                self.restore_generated_harbor_routes();
                let existing_scene_ids = self
                    .model
                    .world
                    .scenes
                    .iter()
                    .map(|scene| scene.id.clone())
                    .collect::<std::collections::HashSet<_>>();
                self.open_scene_documents
                    .retain(|id| existing_scene_ids.contains(id));
                self.recently_closed_scene_documents
                    .retain(|id| existing_scene_ids.contains(id));
                self.scene_document_dirty_ids.clear();
                if self.last_active_scene_document.as_ref().is_some_and(|id| {
                    !existing_scene_ids.contains(id)
                        || !self.open_scene_documents.iter().any(|open_id| open_id == id)
                }) {
                    self.last_active_scene_document = self.open_scene_documents.first().cloned();
                }
                self.selected_scene = self
                    .selected_scene
                    .min(self.model.world.scenes.len().saturating_sub(1));
                self.selection.clear();
                self.command_bus.clear_history();
                self.saved_undo_depth = 0;
                if self.game_canvas_ui.active() {
                    if let Err(error) = self.game_canvas_ui.reload_active() {
                        self.status_message = format!("Reloaded project/world, but UI document reload failed: {error}");
                        return;
                    }
                } else if self.viewport_mode == EditorViewportMode::SceneMap {
                    self.activate_scene_workspace();
                }
                self.status_message = format!(
                    "Reloaded project, assignments, and development world from {}",
                    development_session::path_label(&development_session::editor_world_path())
                );
            }
            (Err(error), _, _, _, _)
            | (_, Err(error), _, _, _)
            | (_, _, Err(error), _, _)
            | (_, _, _, Err(error), _)
            | (_, _, _, _, Err(error)) => {
                self.status_message = format!("Reload failed: {error}");
            }
        }
    }

    fn export_island_preview_pngs_with_status(&mut self) {
        self.status_message = match self.export_island_preview_pngs() {
            Ok(count) => format!("Exported {count} assembled island PNG previews"),
            Err(error) => format!("Island preview export failed: {error}"),
        };
    }

    fn export_island_preview_pngs(&self) -> Result<usize, String> {
        let Some(manifest) = &self.scene_rectangles else {
            return Err("scene rectangle manifest is unavailable".to_string());
        };
        let output_dir = Path::new("content/worldgen/island_previews");
        create_dir_all(output_dir).map_err(|error| error.to_string())?;
        let mut exported = 0usize;
        for summary in super::island_workspace::landmass_summaries(manifest) {
            let rectangles: Vec<_> = summary
                .rectangle_indices
                .iter()
                .map(|index| &manifest.scene_rectangles[*index])
                .collect();
            let min_x = rectangles
                .iter()
                .filter_map(|entry| entry.grid_x)
                .min()
                .unwrap_or(0);
            let max_x = rectangles
                .iter()
                .filter_map(|entry| entry.grid_x)
                .max()
                .unwrap_or(0);
            let min_y = rectangles
                .iter()
                .filter_map(|entry| entry.grid_y)
                .min()
                .unwrap_or(0);
            let max_y = rectangles
                .iter()
                .filter_map(|entry| entry.grid_y)
                .max()
                .unwrap_or(0);
            let width = (max_x - min_x + 1).max(1) as u32 * MAP_W as u32;
            let height = (max_y - min_y + 1).max(1) as u32 * MAP_H as u32;
            let mut image = RgbaImage::from_pixel(width, height, Rgba([9, 42, 70, 255]));
            for rectangle in rectangles {
                let Some(assignment) = self
                    .scene_assignments
                    .assignment_for_rectangle(&rectangle.scene_id)
                else {
                    continue;
                };
                let Some(scene) = self
                    .model
                    .world
                    .scene_by_id(&ProjectSceneId::new(assignment.scene_code.as_str()))
                else {
                    continue;
                };
                let origin_x = (rectangle.grid_x.unwrap_or(min_x) - min_x) as u32 * MAP_W as u32;
                let origin_y = (rectangle.grid_y.unwrap_or(min_y) - min_y) as u32 * MAP_H as u32;
                for y in 0..MAP_H as i32 {
                    for x in 0..MAP_W as i32 {
                        image.put_pixel(
                            origin_x + x as u32,
                            origin_y + y as u32,
                            tile_preview_color(scene.map.get(x, y)),
                        );
                    }
                }
            }
            let path = output_dir.join(format!("{}.png", slug(&summary.name)));
            image
                .save(&path)
                .map_err(|error| format!("{}: {error}", path.display()))?;
            exported += 1;
        }
        let surface_rectangles: Vec<_> = manifest
            .scene_rectangles
            .iter()
            .filter(|rectangle| rectangle_is_overworld_surface(rectangle))
            .collect();
        if !surface_rectangles.is_empty() {
            let min_x = surface_rectangles
                .iter()
                .map(|rectangle| rectangle.world_rect_preview_px[0])
                .min()
                .unwrap_or(0);
            let min_y = surface_rectangles
                .iter()
                .map(|rectangle| rectangle.world_rect_preview_px[1])
                .min()
                .unwrap_or(0);
            let max_x = surface_rectangles
                .iter()
                .map(|rectangle| {
                    rectangle.world_rect_preview_px[0] + rectangle.world_rect_preview_px[2]
                })
                .max()
                .unwrap_or(min_x + 1);
            let max_y = surface_rectangles
                .iter()
                .map(|rectangle| {
                    rectangle.world_rect_preview_px[1] + rectangle.world_rect_preview_px[3]
                })
                .max()
                .unwrap_or(min_y + 1);
            let width = (max_x - min_x).max(1) as u32;
            let height = (max_y - min_y).max(1) as u32;
            let mut archipelago = RgbaImage::from_pixel(width, height, Rgba([9, 42, 70, 255]));
            for link in self
                .model
                .region_graph
                .links
                .iter()
                .filter(|link| link.kind == RegionLinkKind::SeaRoute)
            {
                let Some(from) = self.model.region_graph.node(&link.from) else {
                    continue;
                };
                let Some(to) = self.model.region_graph.node(&link.to) else {
                    continue;
                };
                draw_preview_line(
                    &mut archipelago,
                    (from.position.x * (width.saturating_sub(1)) as f32) as i32,
                    (from.position.y * (height.saturating_sub(1)) as f32) as i32,
                    (to.position.x * (width.saturating_sub(1)) as f32) as i32,
                    (to.position.y * (height.saturating_sub(1)) as f32) as i32,
                    Rgba([72, 190, 235, 255]),
                );
            }
            for rectangle in surface_rectangles {
                let Some(assignment) = self
                    .scene_assignments
                    .assignment_for_rectangle(&rectangle.scene_id)
                else {
                    continue;
                };
                let Some(scene) = self
                    .model
                    .world
                    .scene_by_id(&ProjectSceneId::new(assignment.scene_code.as_str()))
                else {
                    continue;
                };
                let [preview_x, preview_y, preview_w, preview_h] = rectangle.world_rect_preview_px;
                for pixel_y in 0..preview_h.max(1) as u32 {
                    for pixel_x in 0..preview_w.max(1) as u32 {
                        let scene_x = (pixel_x * MAP_W as u32 / preview_w.max(1) as u32)
                            .min(MAP_W as u32 - 1) as i32;
                        let scene_y = (pixel_y * MAP_H as u32 / preview_h.max(1) as u32)
                            .min(MAP_H as u32 - 1) as i32;
                        let target_x = (preview_x - min_x) as u32 + pixel_x;
                        let target_y = (preview_y - min_y) as u32 + pixel_y;
                        if target_x < width && target_y < height {
                            archipelago.put_pixel(
                                target_x,
                                target_y,
                                tile_preview_color(scene.map.get(scene_x, scene_y)),
                            );
                        }
                    }
                }
            }
            let path = output_dir.join("archipelago.png");
            archipelago
                .save(&path)
                .map_err(|error| format!("{}: {error}", path.display()))?;
            exported += 1;
        }
        Ok(exported)
    }
}

fn draw_preview_line(
    image: &mut RgbaImage,
    mut x0: i32,
    mut y0: i32,
    x1: i32,
    y1: i32,
    color: Rgba<u8>,
) {
    let delta_x = (x1 - x0).abs();
    let step_x = if x0 < x1 { 1 } else { -1 };
    let delta_y = -(y1 - y0).abs();
    let step_y = if y0 < y1 { 1 } else { -1 };
    let mut error = delta_x + delta_y;
    loop {
        for offset_y in -1..=1 {
            for offset_x in -1..=1 {
                let x = x0 + offset_x;
                let y = y0 + offset_y;
                if x >= 0 && y >= 0 && x < image.width() as i32 && y < image.height() as i32 {
                    image.put_pixel(x as u32, y as u32, color);
                }
            }
        }
        if x0 == x1 && y0 == y1 {
            break;
        }
        let doubled = 2 * error;
        if doubled >= delta_y {
            error += delta_y;
            x0 += step_x;
        }
        if doubled <= delta_x {
            error += delta_x;
            y0 += step_y;
        }
    }
}

fn tile_preview_color(tile: TileKind) -> Rgba<u8> {
    let rgba = match tile.code() {
        "deep_water" => [10, 48, 82, 255],
        "shallow_water" | "water" => [31, 102, 135, 255],
        "sand" => [201, 180, 121, 255],
        "wet_sand" | "pebble_shore" => [156, 139, 103, 255],
        "grass" => [80, 137, 76, 255],
        "tall_grass" => [66, 122, 64, 255],
        "cliff" | "mountain_rock" => [91, 91, 88, 255],
        "road" | "dirt" => [125, 94, 63, 255],
        _ => [96, 136, 86, 255],
    };
    Rgba(rgba)
}

fn shell_layout_audit_issues(
    layout: &EditorShellLayout,
    width: f32,
    height: f32,
) -> Vec<String> {
    let mut issues = Vec::new();
    let right = |rect: Rect| rect.x + rect.w;
    let bottom = |rect: Rect| rect.y + rect.h;

    if layout.left_panel.w > 0.0 && right(layout.left_panel) > layout.center_panel.x + 0.01 {
        issues.push("left panel overlaps center".to_string());
    }
    if layout.right_panel.w > 0.0 && right(layout.center_panel) > layout.right_panel.x + 0.01 {
        issues.push("center overlaps inspector".to_string());
    }

    for (name, rect) in [
        ("left", layout.left_panel),
        ("center", layout.center_panel),
        ("right", layout.right_panel),
        ("bottom", layout.bottom_dock),
        ("status", layout.status_bar),
    ] {
        if rect.x < -0.01
            || rect.y < -0.01
            || right(rect) > width + 0.01
            || bottom(rect) > height + 0.01
        {
            issues.push(format!("{name} panel escapes window"));
        }
    }

    issues
}

fn slug(value: &str) -> String {
    let mut output = String::new();
    for character in value.chars() {
        if character.is_ascii_alphanumeric() {
            output.push(character.to_ascii_lowercase());
        } else if !output.ends_with('_') {
            output.push('_');
        }
    }
    output.trim_matches('_').to_string()
}
