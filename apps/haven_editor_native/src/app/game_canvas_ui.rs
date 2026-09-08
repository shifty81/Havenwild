use super::editor_text::draw_editor_text;
use super::render_helpers::{draw_editor_widget_tone, draw_list_row, draw_scissored_text, draw_section_header, WidgetTone};
use super::*;
use haven_authoring::{ResourceContextKind, ResourceContextNode, UiAuthoringLane, UiDocument, UiRect as AuthoringUiRect};
use haven_pixel::{PixelDocument, PixelLicense};
use std::path::{Path, PathBuf};

const UI_DOCUMENT_ROOT: &str = "content/ui/documents";

#[derive(Clone, Debug)]
pub(crate) struct GameCanvasUiCatalogEntry {
    pub path: PathBuf,
    pub id: String,
    pub display_name: String,
    pub kind_label: String,
}

#[derive(Clone, Copy, Debug)]
struct UiWidgetDrag {
    index: usize,
    pointer_start: Vec2,
    original: AuthoringUiRect,
}

#[derive(Clone, Debug)]
pub(crate) struct GameCanvasUiState {
    pub catalog: Vec<GameCanvasUiCatalogEntry>,
    pub catalog_index: usize,
    pub document: Option<UiDocument>,
    pub source_path: Option<PathBuf>,
    pub selected_widget: Option<usize>,
    pub active_lane: UiAuthoringLane,
    pub dirty: bool,
    drag: Option<UiWidgetDrag>,
}

impl GameCanvasUiState {
    pub(crate) fn load_default() -> Self {
        Self {
            catalog: scan_ui_document_catalog(&repo_root_dir()),
            catalog_index: 0,
            document: None,
            source_path: None,
            selected_widget: None,
            active_lane: UiAuthoringLane::Layout,
            dirty: false,
            drag: None,
        }
    }

    pub(crate) fn active(&self) -> bool { self.document.is_some() }

    pub(crate) fn open_index(&mut self, index: usize) -> Result<String, String> {
        let entry = self
            .catalog
            .get(index)
            .cloned()
            .ok_or_else(|| "UI document catalog is empty".to_string())?;
        let document = UiDocument::load(&entry.path)?;
        self.catalog_index = index;
        self.source_path = Some(entry.path);
        self.document = Some(document);
        self.selected_widget = None;
        self.active_lane = UiAuthoringLane::Layout;
        self.dirty = false;
        self.drag = None;
        Ok(format!("Opened {} in Game Canvas", entry.display_name))
    }

    pub(crate) fn open_first(&mut self) -> Result<String, String> {
        self.open_index(self.catalog_index.min(self.catalog.len().saturating_sub(1)))
    }

    pub(crate) fn close_view(&mut self) {
        self.document = None;
        self.source_path = None;
        self.selected_widget = None;
        self.dirty = false;
        self.drag = None;
    }

    pub(crate) fn save_active(&mut self) -> Result<(), String> {
        let document = self.document.as_ref().ok_or_else(|| "no UI document is open".to_string())?;
        let path = self.source_path.as_ref().ok_or_else(|| "UI document has no source path".to_string())?;
        document.save(path)?;
        self.dirty = false;
        Ok(())
    }

    pub(crate) fn reload_active(&mut self) -> Result<(), String> {
        let path = self.source_path.clone().ok_or_else(|| "UI document has no source path".to_string())?;
        self.document = Some(UiDocument::load(&path)?);
        self.selected_widget = None;
        self.dirty = false;
        self.drag = None;
        Ok(())
    }
}

impl EditorApp {
    pub(crate) fn game_canvas_ui_active(&self) -> bool {
        self.viewport_mode == EditorViewportMode::SceneMap && self.game_canvas_ui.active()
    }

    pub(crate) fn open_game_canvas_ui_documents(&mut self) {
        match self.game_canvas_ui.open_first() {
            Ok(message) => {
                self.viewport_mode = EditorViewportMode::SceneMap;
                self.scene_tab_overflow_open = false;
                self.focus_right_dock(super::workspace_shell::RightDockTab::Outliner);
                self.sync_resource_context_to_ui_document();
                self.status_message = message;
            }
            Err(error) => self.status_message = format!("Unable to open Game Canvas UI document: {error}"),
        }
    }

    pub(crate) fn open_game_canvas_ui_document_by_id(&mut self, document_id: &str) -> bool {
        let Some(index) = self
            .game_canvas_ui
            .catalog
            .iter()
            .position(|entry| entry.id == document_id)
        else {
            self.status_message = format!("Runtime UI document is not in the Game Canvas catalog: {document_id}");
            return false;
        };
        self.open_game_canvas_ui_document_index(index)
    }

    pub(crate) fn open_game_canvas_ui_document_index(&mut self, index: usize) -> bool {
        match self.game_canvas_ui.open_index(index) {
            Ok(message) => {
                self.viewport_mode = EditorViewportMode::SceneMap;
                self.sync_resource_context_to_ui_document();
                self.status_message = message;
                true
            }
            Err(error) => {
                self.status_message = format!("Unable to open UI document: {error}");
                false
            }
        }
    }

    fn sync_resource_context_to_ui_document(&mut self) {
        let Some(document) = self.game_canvas_ui.document.as_ref() else { return; };
        let mut context = self.resource_context.clone().unwrap_or_else(|| haven_authoring::ResourceContext::new(0));
        context.chain.retain(|node| !matches!(node.kind, ResourceContextKind::Ui));
        context.chain.push(ResourceContextNode::new(
            ResourceContextKind::Ui,
            document.id.clone(),
            document.display_name.clone(),
        ));
        self.resource_context = Some(context);
    }

    pub(crate) fn draw_game_canvas_ui_document(&self) {
        let viewport = self.scene_canvas_viewport_rect();
        draw_rectangle(viewport.x, viewport.y, viewport.w, viewport.h, Color::new(0.035, 0.04, 0.05, 1.0));
        let Some(document) = self.game_canvas_ui.document.as_ref() else { return; };
        let canvas = ui_reference_canvas_rect(viewport, document.reference_size);
        draw_rectangle(canvas.x, canvas.y, canvas.w, canvas.h, Color::new(0.075, 0.082, 0.092, 1.0));
        draw_rectangle_lines(canvas.x, canvas.y, canvas.w, canvas.h, 1.0, editor_theme::colors::BORDER_STRONG);
        let scale = ui_reference_scale(canvas, document.reference_size);
        let safe = document.safe_area;
        let safe_rect = Rect::new(
            canvas.x + safe[0] as f32 * scale,
            canvas.y + safe[1] as f32 * scale,
            (canvas.w - (safe[0] + safe[2]) as f32 * scale).max(1.0),
            (canvas.h - (safe[1] + safe[3]) as f32 * scale).max(1.0),
        );
        draw_rectangle_lines(safe_rect.x, safe_rect.y, safe_rect.w, safe_rect.h, 1.0, Color::new(0.25, 0.62, 0.44, 0.72));

        for (index, widget) in document.widgets.iter().enumerate() {
            if !widget.visible { continue; }
            let rect = ui_widget_screen_rect(canvas, document.reference_size, widget.rect);
            let selected = self.game_canvas_ui.selected_widget == Some(index);
            let fill = if selected { Color::new(0.18, 0.34, 0.46, 0.76) } else { Color::new(0.13, 0.15, 0.18, 0.78) };
            draw_rectangle(rect.x, rect.y, rect.w, rect.h, fill);
            draw_rectangle_lines(
                rect.x, rect.y, rect.w, rect.h,
                if selected { 2.0 } else { 1.0 },
                if widget.locked { editor_theme::colors::TEXT_DISABLED } else if selected { editor_theme::colors::ACCENT } else { editor_theme::colors::BORDER_SUBTLE },
            );
            let label = widget.label.as_deref().unwrap_or(widget.id.as_str());
            draw_scissored_text(label, rect.x + 5.0, rect.y + 15.0, (rect.w - 10.0).max(1.0), 11.0, editor_theme::colors::TEXT_PRIMARY);
        }

        let title = format!(
            "UI · {} · {} × {} · {} px snap{}",
            document.display_name,
            document.reference_size[0],
            document.reference_size[1],
            document.snap_px,
            if self.game_canvas_ui.dirty { " · modified" } else { "" },
        );
        draw_editor_text(&title, viewport.x + 14.0, viewport.y + 24.0, 14.0, editor_theme::colors::TEXT_PRIMARY);
        if let Some(breadcrumb) = self.resource_context_breadcrumb() {
            draw_scissored_text(&breadcrumb, viewport.x + 14.0, viewport.y + 43.0, (viewport.w - 28.0).max(1.0), 10.5, editor_theme::colors::TEXT_SECONDARY);
        }
    }

    pub(crate) fn update_game_canvas_ui_input(&mut self, pointer_consumed: bool, canvas_pointer_consumed: bool) -> bool {
        if !self.game_canvas_ui_active() { return false; }
        let viewport = self.scene_canvas_viewport_rect();
        let point = vec2(mouse_position().0, mouse_position().1);
        let reference_size = self
            .game_canvas_ui
            .document
            .as_ref()
            .map(|document| document.reference_size)
            .unwrap_or([1920, 1080]);
        let canvas = ui_reference_canvas_rect(viewport, reference_size);

        if !pointer_consumed
            && !canvas_pointer_consumed
            && is_mouse_button_pressed(MouseButton::Left)
            && canvas.contains(point)
        {
            let hit = self.game_canvas_ui.document.as_ref().and_then(|document| {
                document.widgets.iter().enumerate().rev().find_map(|(index, widget)| {
                    (widget.visible
                        && ui_widget_screen_rect(canvas, document.reference_size, widget.rect).contains(point))
                    .then_some((index, widget.locked, widget.rect))
                })
            });
            self.game_canvas_ui.selected_widget = hit.map(|(index, _, _)| index);
            self.game_canvas_ui.drag = hit.and_then(|(index, locked, original)| {
                (!locked).then_some(UiWidgetDrag { index, pointer_start: point, original })
            });
        }

        if is_mouse_button_down(MouseButton::Left) {
            if let Some(drag) = self.game_canvas_ui.drag {
                let scale = ui_reference_scale(canvas, reference_size).max(0.0001);
                let delta = (point - drag.pointer_start) / scale;
                if let Some(document) = self.game_canvas_ui.document.as_mut() {
                    let snap = document.snap_px.max(1) as f32;
                    let document_size = document.reference_size;
                    if let Some(widget) = document.widgets.get_mut(drag.index) {
                        let x = ((drag.original.x + delta.x) / snap).round() * snap;
                        let y = ((drag.original.y + delta.y) / snap).round() * snap;
                        let max_x = (document_size[0] as f32 - widget.rect.width).max(0.0);
                        let max_y = (document_size[1] as f32 - widget.rect.height).max(0.0);
                        widget.rect.x = x.clamp(0.0, max_x);
                        widget.rect.y = y.clamp(0.0, max_y);
                        self.game_canvas_ui.dirty = true;
                    }
                }
            }
        } else {
            self.game_canvas_ui.drag = None;
        }

        if let Some(index) = self.game_canvas_ui.selected_widget {
            let step = self.game_canvas_ui.document.as_ref().map_or(8.0, |doc| doc.snap_px.max(1) as f32);
            let mut dx = 0.0;
            let mut dy = 0.0;
            if is_key_pressed(KeyCode::Left) { dx -= step; }
            if is_key_pressed(KeyCode::Right) { dx += step; }
            if is_key_pressed(KeyCode::Up) { dy -= step; }
            if is_key_pressed(KeyCode::Down) { dy += step; }
            if dx != 0.0 || dy != 0.0 {
                if let Some(document) = self.game_canvas_ui.document.as_mut() {
                    let document_size = document.reference_size;
                    if let Some(widget) = document.widgets.get_mut(index) {
                        if !widget.locked {
                            let max_x = (document_size[0] as f32 - widget.rect.width).max(0.0);
                            let max_y = (document_size[1] as f32 - widget.rect.height).max(0.0);
                            widget.rect.x = (widget.rect.x + dx).clamp(0.0, max_x);
                            widget.rect.y = (widget.rect.y + dy).clamp(0.0, max_y);
                            self.game_canvas_ui.dirty = true;
                        }
                    }
                }
            }
        }
        true
    }

    pub(crate) fn draw_game_canvas_ui_properties(&self, rect: Rect) {
        let Some(document) = self.game_canvas_ui.document.as_ref() else { return; };
        let mut y = rect.y;
        draw_section_header(Rect::new(rect.x, y, rect.w, 26.0), "UI Document", Some(document.kind.label()));
        y += 34.0;
        draw_scissored_text(&document.display_name, rect.x, y + 14.0, rect.w, 14.0, editor_theme::colors::TEXT_PRIMARY);
        y += 24.0;
        draw_scissored_text(&format!("{} × {} · snap {} px", document.reference_size[0], document.reference_size[1], document.snap_px), rect.x, y + 13.0, rect.w, 11.0, editor_theme::colors::TEXT_SECONDARY);
        y += 28.0;
        for (index, lane) in UiAuthoringLane::ALL.into_iter().enumerate() {
            let row = Rect::new(rect.x, y + index as f32 * 26.0, rect.w, 22.0);
            draw_editor_widget_tone(row, lane.label(), self.game_canvas_ui.active_lane == lane, if self.game_canvas_ui.active_lane == lane { WidgetTone::Primary } else { WidgetTone::Quiet });
        }
        y += UiAuthoringLane::ALL.len() as f32 * 26.0 + 12.0;
        if let Some(index) = self.game_canvas_ui.selected_widget {
            if let Some(widget) = document.widgets.get(index) {
                draw_section_header(Rect::new(rect.x, y, rect.w, 26.0), "Selected Control", Some(&widget.id));
                y += 34.0;
                for line in [
                    format!("Kind: {:?}", widget.kind),
                    format!("Rect: {:.0}, {:.0} · {:.0} × {:.0}", widget.rect.x, widget.rect.y, widget.rect.width, widget.rect.height),
                    format!("Data bindings: {}", widget.data_bindings.len()),
                    format!("Behavior bindings: {}", widget.behavior_bindings.len()),
                    format!("Presentation: {}", widget.presentation_resource.as_deref().unwrap_or("none")),
                    format!("Animation: {}", widget.animation_resource.as_deref().unwrap_or("none")),
                    format!("Behavior: {}", widget.behavior_resource.as_deref().unwrap_or("typed bindings")),
                    format!("Sound: {}", widget.sound_event_id.as_deref().unwrap_or("none")),
                ] {
                    draw_scissored_text(&line, rect.x, y + 13.0, rect.w, 11.0, editor_theme::colors::TEXT_SECONDARY);
                    y += 21.0;
                }
                for binding in widget.data_bindings.iter().take(4) {
                    draw_scissored_text(&format!("DATA {} ← {}", binding.property, binding.source), rect.x, y + 13.0, rect.w, 10.5, editor_theme::colors::ACCENT);
                    y += 19.0;
                }
                for binding in widget.behavior_bindings.iter().take(4) {
                    draw_scissored_text(&format!("{} → {}", binding.event, binding.action), rect.x, y + 13.0, rect.w, 10.5, editor_theme::colors::GOOD);
                    y += 19.0;
                }
                if widget.presentation_resource.is_some() {
                    let button = Rect::new(rect.x, y + 6.0, rect.w, 24.0);
                    draw_editor_widget_tone(button, "Edit Visual in Pixel Studio", false, WidgetTone::Primary);
                }
            }
        }
    }

    pub(crate) fn draw_game_canvas_ui_outliner(&self, rect: Rect) {
        let mut y = rect.y;
        draw_section_header(Rect::new(rect.x, y, rect.w, 26.0), "UI Documents", Some("Game Canvas"));
        y += 32.0;
        for (index, entry) in self.game_canvas_ui.catalog.iter().enumerate().take(12) {
            let row = Rect::new(rect.x, y, rect.w, 30.0);
            draw_list_row(row, &entry.display_name, Some(&entry.kind_label), index == self.game_canvas_ui.catalog_index && self.game_canvas_ui.active());
            y += 34.0;
        }
        if let Some(document) = self.game_canvas_ui.document.as_ref() {
            y += 8.0;
            draw_section_header(Rect::new(rect.x, y, rect.w, 26.0), "Controls", Some(&format!("{} total", document.widgets.len())));
            y += 32.0;
            for (index, widget) in document.widgets.iter().enumerate().take(14) {
                let row = Rect::new(rect.x, y, rect.w, 28.0);
                draw_list_row(row, widget.label.as_deref().unwrap_or(&widget.id), Some(&format!("{:?}", widget.kind)), self.game_canvas_ui.selected_widget == Some(index));
                y += 31.0;
            }
        }
    }

    pub(crate) fn handle_game_canvas_ui_outliner_click(&mut self, mx: f32, my: f32, rect: Rect) -> bool {
        let point = vec2(mx, my);
        let mut y = rect.y + 32.0;
        for index in 0..self.game_canvas_ui.catalog.len().min(12) {
            let row = Rect::new(rect.x, y, rect.w, 30.0);
            if row.contains(point) { return self.open_game_canvas_ui_document_index(index); }
            y += 34.0;
        }
        let widget_count = self.game_canvas_ui.document.as_ref().map_or(0, |doc| doc.widgets.len());
        y += 40.0;
        for index in 0..widget_count.min(14) {
            let row = Rect::new(rect.x, y, rect.w, 28.0);
            if row.contains(point) {
                self.game_canvas_ui.selected_widget = Some(index);
                self.status_message = format!("Selected UI control {}", self.game_canvas_ui.document.as_ref().and_then(|doc| doc.widgets.get(index)).map(|widget| widget.id.as_str()).unwrap_or("control"));
                return true;
            }
            y += 31.0;
        }
        true
    }

    pub(crate) fn handle_game_canvas_ui_properties_click(&mut self, mx: f32, my: f32, rect: Rect) -> bool {
        if !self.game_canvas_ui_active() { return false; }
        let point = vec2(mx, my);
        let start_y = rect.y + 34.0 + 24.0 + 28.0;
        for (index, lane) in UiAuthoringLane::ALL.into_iter().enumerate() {
            let row = Rect::new(rect.x, start_y + index as f32 * 26.0, rect.w, 22.0);
            if row.contains(point) {
                self.game_canvas_ui.active_lane = lane;
                self.canvas_layer_context_override = None;
                self.status_message = format!("UI authoring lane: {}", lane.label());
                return true;
            }
        }
        if let Some(button) = self.game_canvas_ui_edit_visual_button_rect(rect) {
            if button.contains(point) {
                self.open_selected_ui_visual_in_pixel_studio();
                return true;
            }
        }
        true
    }

    fn game_canvas_ui_edit_visual_button_rect(&self, rect: Rect) -> Option<Rect> {
        let document = self.game_canvas_ui.document.as_ref()?;
        let index = self.game_canvas_ui.selected_widget?;
        let widget = document.widgets.get(index)?;
        widget.presentation_resource.as_ref()?;
        let mut y = rect.y + 34.0 + 24.0 + 28.0;
        y += UiAuthoringLane::ALL.len() as f32 * 26.0 + 12.0;
        y += 34.0;
        y += 8.0 * 21.0;
        y += widget.data_bindings.len().min(4) as f32 * 19.0;
        y += widget.behavior_bindings.len().min(4) as f32 * 19.0;
        Some(Rect::new(rect.x, y + 6.0, rect.w, 24.0))
    }

    pub(crate) fn open_selected_ui_visual_in_pixel_studio(&mut self) {
        let Some((widget_id, widget_label, resource)) = self.game_canvas_ui.document.as_ref().and_then(|document| {
            let index = self.game_canvas_ui.selected_widget?;
            let widget = document.widgets.get(index)?;
            Some((
                widget.id.clone(),
                widget.label.clone().unwrap_or_else(|| widget.id.clone()),
                widget.presentation_resource.clone()?,
            ))
        }) else {
            self.status_message = "Select a UI control with a presentation resource first".to_string();
            return;
        };
        let configured_path = PathBuf::from(&resource);
        let source_path = if configured_path.is_absolute() {
            configured_path
        } else {
            repo_root_dir().join(configured_path)
        };
        if !source_path.is_file() {
            self.status_message = format!("UI presentation source is missing: {}", source_path.display());
            return;
        }
        let mut document = match PixelDocument::load(&source_path, &widget_label, PixelLicense::default()) {
            Ok(document) => document,
            Err(error) => {
                self.status_message = format!("Unable to open UI presentation in Pixel Studio: {error}");
                return;
            }
        };
        document.metadata.preview_mode = haven_pixel::PixelPreviewMode::Ui;
        self.pixel_studio.open_document_session(document);
        self.pixel_studio.reset_authoring_defaults();
        self.pixel_studio.animation_context = None;
        self.pixel_studio.world_asset_context = None;
        self.pixel_studio.world_region_context = None;
        self.pixel_studio.refresh_texture();
        self.viewport_mode = EditorViewportMode::PixelStudio;
        self.pixel_studio.frame_document(self.pixel_canvas_rect());

        if let Some(context) = self.resource_context.as_mut() {
            context.chain.retain(|node| !matches!(node.kind, ResourceContextKind::Visual | ResourceContextKind::Source));
            context.chain.push(ResourceContextNode::new(ResourceContextKind::Visual, widget_id, widget_label.clone()));
            context.chain.push(ResourceContextNode::new(ResourceContextKind::Source, resource.clone(), resource));
        }
        self.status_message = format!("Editing UI visual {widget_label} in Pixel Studio");
    }
}

fn scan_ui_document_catalog(root: &Path) -> Vec<GameCanvasUiCatalogEntry> {
    let dir = root.join(UI_DOCUMENT_ROOT);
    let Ok(entries) = std::fs::read_dir(dir) else { return Vec::new(); };
    let mut catalog = entries
        .flatten()
        .filter_map(|entry| {
            let path = entry.path();
            if path.extension().and_then(|value| value.to_str()) != Some("json") { return None; }
            let document = UiDocument::load(&path).ok()?;
            Some(GameCanvasUiCatalogEntry {
                path,
                id: document.id,
                display_name: document.display_name,
                kind_label: document.kind.label().to_string(),
            })
        })
        .collect::<Vec<_>>();
    catalog.sort_by(|left, right| left.display_name.cmp(&right.display_name));
    catalog
}

fn ui_reference_canvas_rect(viewport: Rect, reference_size: [u32; 2]) -> Rect {
    let inner = Rect::new(viewport.x + 18.0, viewport.y + 52.0, (viewport.w - 36.0).max(1.0), (viewport.h - 70.0).max(1.0));
    let aspect = reference_size[0].max(1) as f32 / reference_size[1].max(1) as f32;
    let mut width = inner.w;
    let mut height = width / aspect;
    if height > inner.h {
        height = inner.h;
        width = height * aspect;
    }
    Rect::new(inner.x + (inner.w - width) * 0.5, inner.y + (inner.h - height) * 0.5, width, height)
}

fn ui_reference_scale(canvas: Rect, reference_size: [u32; 2]) -> f32 {
    (canvas.w / reference_size[0].max(1) as f32).min(canvas.h / reference_size[1].max(1) as f32)
}

fn ui_widget_screen_rect(canvas: Rect, reference_size: [u32; 2], rect: AuthoringUiRect) -> Rect {
    let scale = ui_reference_scale(canvas, reference_size);
    Rect::new(canvas.x + rect.x * scale, canvas.y + rect.y * scale, rect.width * scale, rect.height * scale)
}
