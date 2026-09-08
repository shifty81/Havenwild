use super::render_helpers::*;
use super::*;
use haven_audio::{AudioConnection, AudioNode, AudioNodeKind, InstrumentKind, MidiNote, SoundDocument};

const NODE_W: f32 = 156.0;
const NODE_H: f32 = 62.0;
const NODE_HEADER_H: f32 = 22.0;
const PALETTE_ROW_H: f32 = 30.0;
const INSTRUMENT_ROW_H: f32 = 28.0;

#[derive(Clone, Debug)]
pub(crate) struct SoundStudioState {
    pub document: SoundDocument,
    pub selected_node: Option<usize>,
    pub palette_kind: AudioNodeKind,
    pub link_source: Option<usize>,
    pub drag_offset: Option<[f32; 2]>,
    pub canvas_pan: [f32; 2],
    pub dirty: bool,
}

impl Default for SoundStudioState {
    fn default() -> Self {
        Self {
            document: SoundDocument::default(),
            selected_node: Some(0),
            palette_kind: AudioNodeKind::Oscillator,
            link_source: None,
            drag_offset: None,
            canvas_pan: [0.0, 0.0],
            dirty: false,
        }
    }
}

impl SoundStudioState {
    pub fn new() -> Self {
        Self::default()
    }
}

fn node_rect(canvas: Rect, node: &AudioNode, pan: [f32; 2]) -> Rect {
    Rect::new(
        canvas.x + node.position[0] + pan[0],
        canvas.y + node.position[1] + pan[1],
        NODE_W,
        NODE_H,
    )
}

fn sound_graph_rect(app: &EditorApp) -> Rect {
    let host = app.canvas_content_host_rect();
    Rect::new(host.x + 4.0, host.y + 36.0, (host.w - 8.0).max(1.0), (host.h - 40.0).max(1.0))
}

fn sound_preview_button_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + rect.h - 78.0, rect.w, 32.0)
}

fn sound_add_note_button_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + rect.h - 40.0, rect.w, 32.0)
}

fn palette_kinds() -> [AudioNodeKind; 10] {
    [
        AudioNodeKind::Oscillator,
        AudioNodeKind::Noise,
        AudioNodeKind::Envelope,
        AudioNodeKind::Filter,
        AudioNodeKind::Gain,
        AudioNodeKind::Pan,
        AudioNodeKind::Mixer,
        AudioNodeKind::Delay,
        AudioNodeKind::Lfo,
        AudioNodeKind::Output,
    ]
}

impl EditorApp {
    pub(crate) fn draw_sound_library(&self, rect: Rect) {
        draw_section_header(Rect::new(rect.x, rect.y, rect.w, 24.0), "Sound Assets", Some("Shared CanvasWorkspace"));
        let mut y = rect.y + 34.0;
        draw_list_row(
            Rect::new(rect.x, y, rect.w, 46.0),
            &self.sound_studio.document.display_name,
            Some("Procedural Audio Graph"),
            true,
        );
        y += 56.0;
        draw_editor_text("Instruments", rect.x, y + 15.0, 13.0, editor_theme::colors::TEXT_SECONDARY);
        y += 23.0;
        for instrument in InstrumentKind::ALL {
            let row = Rect::new(rect.x, y, rect.w, INSTRUMENT_ROW_H - 2.0);
            draw_list_row(
                row,
                instrument.label(),
                None,
                self.sound_studio.document.instrument == instrument,
            );
            y += INSTRUMENT_ROW_H;
        }
        y += 10.0;
        draw_editor_text("Node Palette", rect.x, y + 15.0, 13.0, editor_theme::colors::TEXT_SECONDARY);
        y += 23.0;
        for kind in palette_kinds() {
            let row = Rect::new(rect.x, y, rect.w, PALETTE_ROW_H - 2.0);
            draw_list_row(row, kind.label(), Some("Place with Tool Rail > Content"), self.sound_studio.palette_kind == kind);
            y += PALETTE_ROW_H;
            if y > rect.y + rect.h - 20.0 {
                break;
            }
        }
    }

    pub(crate) fn draw_sound_workspace(&self, _rect: Rect) {
        let canvas = sound_graph_rect(self);
        draw_rectangle(canvas.x, canvas.y, canvas.w, canvas.h, Color::new(0.065, 0.065, 0.065, 1.0));
        draw_rectangle_lines(canvas.x, canvas.y, canvas.w, canvas.h, 1.0, editor_theme::colors::BORDER_STRONG);
        let grid = 32.0;
        let mut x = canvas.x + self.sound_studio.canvas_pan[0].rem_euclid(grid);
        while x < canvas.x + canvas.w {
            draw_line(x, canvas.y, x, canvas.y + canvas.h, 1.0, Color::new(0.16, 0.16, 0.16, 0.5));
            x += grid;
        }
        let mut y = canvas.y + self.sound_studio.canvas_pan[1].rem_euclid(grid);
        while y < canvas.y + canvas.h {
            draw_line(canvas.x, y, canvas.x + canvas.w, y, 1.0, Color::new(0.16, 0.16, 0.16, 0.5));
            y += grid;
        }

        for connection in &self.sound_studio.document.connections {
            let Some(from_index) = self.sound_studio.document.nodes.iter().position(|node| node.id == connection.from_node) else { continue; };
            let Some(to_index) = self.sound_studio.document.nodes.iter().position(|node| node.id == connection.to_node) else { continue; };
            let from = node_rect(canvas, &self.sound_studio.document.nodes[from_index], self.sound_studio.canvas_pan);
            let to = node_rect(canvas, &self.sound_studio.document.nodes[to_index], self.sound_studio.canvas_pan);
            draw_line(from.x + from.w, from.y + from.h * 0.5, to.x, to.y + to.h * 0.5, 2.0, editor_theme::colors::ACCENT);
        }

        for (index, node) in self.sound_studio.document.nodes.iter().enumerate() {
            let rect = node_rect(canvas, node, self.sound_studio.canvas_pan);
            let selected = self.sound_studio.selected_node == Some(index);
            draw_rectangle(rect.x, rect.y, rect.w, rect.h, if selected { Color::new(0.14, 0.18, 0.20, 1.0) } else { editor_theme::colors::PANEL_BG });
            draw_rectangle(rect.x, rect.y, rect.w, NODE_HEADER_H, if selected { editor_theme::colors::ACCENT_PRESSED } else { editor_theme::colors::PANEL_HEADER });
            draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, if selected { 2.0 } else { 1.0 }, if selected { editor_theme::colors::SELECTION_OUTLINE } else { editor_theme::colors::BORDER_SUBTLE });
            draw_scissored_text(&node.label, rect.x + 8.0, rect.y + 16.0, rect.w - 16.0, 12.0, editor_theme::colors::TEXT_PRIMARY);
            draw_scissored_text(node.kind.label(), rect.x + 8.0, rect.y + 44.0, rect.w - 16.0, 11.0, editor_theme::colors::TEXT_SECONDARY);
            draw_circle(rect.x, rect.y + rect.h * 0.5, 4.0, editor_theme::colors::TEXT_SECONDARY);
            draw_circle(rect.x + rect.w, rect.y + rect.h * 0.5, 4.0, editor_theme::colors::ACCENT_HOVER);
        }

        if let Some(index) = self.sound_studio.link_source {
            if let Some(node) = self.sound_studio.document.nodes.get(index) {
                let rect = node_rect(canvas, node, self.sound_studio.canvas_pan);
                draw_circle_lines(rect.x + rect.w, rect.y + rect.h * 0.5, 8.0, 2.0, editor_theme::colors::WARN);
            }
        }

        draw_editor_text(
            "Sound Studio | Select / Move / Place / Link use the shared Tool Rail",
            canvas.x + 10.0,
            canvas.y + 20.0,
            12.0,
            editor_theme::colors::TEXT_SECONDARY,
        );
    }

    pub(crate) fn draw_sound_inspector(&self, rect: Rect) {
        draw_section_header(Rect::new(rect.x, rect.y, rect.w, 24.0), "Sound Properties", Some("W62F"));
        let mut y = rect.y + 38.0;
        draw_editor_text(
            &format!("Instrument: {}", self.sound_studio.document.instrument.label()),
            rect.x,
            y,
            14.0,
            editor_theme::colors::TEXT_PRIMARY,
        );
        y += 24.0;
        draw_editor_text(
            &format!("Notes: {} | Nodes: {} | Links: {}", self.sound_studio.document.notes.len(), self.sound_studio.document.nodes.len(), self.sound_studio.document.connections.len()),
            rect.x,
            y,
            12.0,
            editor_theme::colors::TEXT_SECONDARY,
        );
        y += 28.0;
        if let Some(index) = self.sound_studio.selected_node {
            if let Some(node) = self.sound_studio.document.nodes.get(index) {
                draw_editor_text("Selected Node", rect.x, y, 14.0, editor_theme::colors::TEXT_PRIMARY);
                y += 22.0;
                draw_scissored_text(&node.label, rect.x, y, rect.w, 13.0, editor_theme::colors::ACCENT_HOVER);
                y += 21.0;
                draw_editor_text(
                    &format!("Position: {:.0}, {:.0}", node.position[0], node.position[1]),
                    rect.x,
                    y,
                    12.0,
                    editor_theme::colors::TEXT_SECONDARY,
                );
            }
        }
        let issues = self.sound_studio.document.validate();
        if issues.is_empty() {
            draw_editor_text("Graph valid", rect.x, rect.y + rect.h - 104.0, 12.0, editor_theme::colors::GOOD);
        } else {
            draw_scissored_text(&issues.join(" | "), rect.x, rect.y + rect.h - 104.0, rect.w, 11.0, editor_theme::colors::WARN);
        }
        draw_editor_widget_tone(sound_preview_button_rect(rect), "Render Preview WAV", false, WidgetTone::Primary);
        draw_editor_widget_tone(sound_add_note_button_rect(rect), "Add C4 MIDI Note", false, WidgetTone::Quiet);
    }

    pub(crate) fn handle_sound_palette_click_in_rect(&mut self, mx: f32, my: f32, rect: Rect) -> bool {
        let point = vec2(mx, my);
        if !rect.contains(point) { return false; }
        let mut y = rect.y + 34.0 + 56.0 + 23.0;
        for instrument in InstrumentKind::ALL {
            let row = Rect::new(rect.x, y, rect.w, INSTRUMENT_ROW_H - 2.0);
            if row.contains(point) {
                self.sound_studio.document.instrument = instrument;
                self.sound_studio.dirty = true;
                self.status_message = format!("Sound instrument: {}", instrument.label());
                return true;
            }
            y += INSTRUMENT_ROW_H;
        }
        y += 10.0 + 23.0;
        for kind in palette_kinds() {
            let row = Rect::new(rect.x, y, rect.w, PALETTE_ROW_H - 2.0);
            if row.contains(point) {
                self.sound_studio.palette_kind = kind;
                self.canvas_active_tool = tool_registry::UniversalTool::Place;
                self.status_message = format!("Sound node armed: {} | click graph to place", kind.label());
                return true;
            }
            y += PALETTE_ROW_H;
        }
        true
    }

    pub(crate) fn handle_sound_studio_click(&mut self, mx: f32, my: f32) -> bool {
        let point = vec2(mx, my);
        if self.workspace_shell.left_panel_visible {
            let rect = self.contextual_asset_browser_rect();
            if rect.contains(point) {
                return self.handle_sound_palette_click_in_rect(mx, my, rect);
            }
        }

        if self.workspace_shell.right_panel_visible {
            let rect = self.inspector_content_rect();
            if sound_preview_button_rect(rect).contains(point) {
                let root = repo_root_dir();
                let path = root.join("WORKSPACE/audio/previews/sound_studio_preview.wav");
                self.status_message = match self.sound_studio.document.render_preview_wav(&path) {
                    Ok(()) => format!("Rendered real WAV preview: {}", path.strip_prefix(&root).unwrap_or(&path).display()),
                    Err(error) => format!("Sound preview render failed: {error}"),
                };
                return true;
            }
            if sound_add_note_button_rect(rect).contains(point) {
                let start = self.sound_studio.document.notes.last().map(|note| note.start_seconds + note.duration_seconds + 0.05).unwrap_or(0.0);
                self.sound_studio.document.notes.push(MidiNote { note: 60, velocity: 110, start_seconds: start, duration_seconds: 0.3 });
                self.sound_studio.document.duration_seconds = self.sound_studio.document.duration_seconds.max(start + 0.45);
                self.sound_studio.dirty = true;
                self.status_message = "Added C4 MIDI note to Sound Studio timeline data".to_string();
                return true;
            }
        }

        let canvas = sound_graph_rect(self);
        if !canvas.contains(point) {
            return false;
        }
        let hit = self.sound_studio.document.nodes.iter().enumerate().rev().find_map(|(index, node)| {
            node_rect(canvas, node, self.sound_studio.canvas_pan).contains(point).then_some(index)
        });
        match self.canvas_active_tool {
            tool_registry::UniversalTool::Place => {
                let local = [mx - canvas.x - self.sound_studio.canvas_pan[0] - NODE_W * 0.5, my - canvas.y - self.sound_studio.canvas_pan[1] - NODE_H * 0.5];
                let node = AudioNode::new(self.sound_studio.palette_kind, local);
                self.sound_studio.document.nodes.push(node);
                self.sound_studio.selected_node = Some(self.sound_studio.document.nodes.len() - 1);
                self.sound_studio.dirty = true;
                self.status_message = format!("Placed {} node", self.sound_studio.palette_kind.label());
                true
            }
            tool_registry::UniversalTool::Link => {
                if let Some(index) = hit {
                    if let Some(source) = self.sound_studio.link_source.take() {
                        if source != index {
                            let from_node = self.sound_studio.document.nodes[source].id.clone();
                            let to_node = self.sound_studio.document.nodes[index].id.clone();
                            if !self.sound_studio.document.connections.iter().any(|link| link.from_node == from_node && link.to_node == to_node) {
                                self.sound_studio.document.connections.push(AudioConnection { from_node, to_node });
                                self.sound_studio.dirty = true;
                            }
                            self.status_message = "Connected Sound Studio nodes".to_string();
                        }
                    } else {
                        self.sound_studio.link_source = Some(index);
                        self.status_message = "Sound link source selected; choose destination".to_string();
                    }
                }
                true
            }
            tool_registry::UniversalTool::Move => {
                self.sound_studio.selected_node = hit;
                if let Some(index) = hit {
                    let node = &self.sound_studio.document.nodes[index];
                    self.sound_studio.drag_offset = Some([
                        mx - canvas.x - self.sound_studio.canvas_pan[0] - node.position[0],
                        my - canvas.y - self.sound_studio.canvas_pan[1] - node.position[1],
                    ]);
                }
                true
            }
            _ => {
                self.sound_studio.selected_node = hit;
                true
            }
        }
    }

    pub(crate) fn update_sound_studio_input(&mut self) {
        if let Some(index) = self.sound_studio.selected_node {
            if let Some(offset) = self.sound_studio.drag_offset {
                if is_mouse_button_down(MouseButton::Left) && self.canvas_active_tool == tool_registry::UniversalTool::Move {
                    let canvas = sound_graph_rect(self);
                    let (mx, my) = mouse_position();
                    if let Some(node) = self.sound_studio.document.nodes.get_mut(index) {
                        node.position = [
                            (mx - canvas.x - self.sound_studio.canvas_pan[0] - offset[0]).round(),
                            (my - canvas.y - self.sound_studio.canvas_pan[1] - offset[1]).round(),
                        ];
                        self.sound_studio.dirty = true;
                    }
                } else {
                    self.sound_studio.drag_offset = None;
                }
            }
            if !is_key_down(KeyCode::LeftControl) && !is_key_down(KeyCode::RightControl) {
                let mut delta = [0.0_f32, 0.0_f32];
                if is_key_pressed(KeyCode::Left) { delta[0] -= 1.0; }
                if is_key_pressed(KeyCode::Right) { delta[0] += 1.0; }
                if is_key_pressed(KeyCode::Up) { delta[1] -= 1.0; }
                if is_key_pressed(KeyCode::Down) { delta[1] += 1.0; }
                if delta != [0.0, 0.0] {
                    if let Some(node) = self.sound_studio.document.nodes.get_mut(index) {
                        node.position[0] += delta[0];
                        node.position[1] += delta[1];
                        self.sound_studio.dirty = true;
                    }
                }
            }
        }
    }
}
