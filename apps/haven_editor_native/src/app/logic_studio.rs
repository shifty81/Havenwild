use super::render_helpers::*;
use super::*;
use haven_logic::{LogicGraph, LogicLink, LogicNode, LogicNodeKind};

const NODE_W: f32 = 170.0;
const NODE_H: f32 = 62.0;
const PALETTE_ROW_H: f32 = 34.0;

#[derive(Clone, Debug)]
pub(crate) struct LogicStudioState {
    pub graph: LogicGraph,
    pub selected_node: Option<usize>,
    pub palette_kind: LogicNodeKind,
    pub link_source: Option<usize>,
    pub drag_offset: Option<[f32; 2]>,
    pub canvas_pan: [f32; 2],
    pub dirty: bool,
}

impl Default for LogicStudioState {
    fn default() -> Self {
        Self {
            graph: LogicGraph::default(),
            selected_node: Some(0),
            palette_kind: LogicNodeKind::ActionPlaySound,
            link_source: None,
            drag_offset: None,
            canvas_pan: [0.0, 0.0],
            dirty: false,
        }
    }
}

impl LogicStudioState {
    pub fn new() -> Self { Self::default() }
}

fn logic_palette() -> [LogicNodeKind; 10] {
    [
        LogicNodeKind::EventInteract,
        LogicNodeKind::EventEnter,
        LogicNodeKind::ConditionFlag,
        LogicNodeKind::ConditionHasItem,
        LogicNodeKind::ActionSetFlag,
        LogicNodeKind::ActionGiveItem,
        LogicNodeKind::ActionPlaySound,
        LogicNodeKind::ActionPlayAnimation,
        LogicNodeKind::Branch,
        LogicNodeKind::Sequence,
    ]
}

fn logic_graph_rect(app: &EditorApp) -> Rect {
    let host = app.canvas_content_host_rect();
    Rect::new(host.x + 4.0, host.y + 36.0, (host.w - 8.0).max(1.0), (host.h - 40.0).max(1.0))
}

fn logic_node_rect(canvas: Rect, node: &LogicNode, pan: [f32; 2]) -> Rect {
    Rect::new(canvas.x + node.position[0] + pan[0], canvas.y + node.position[1] + pan[1], NODE_W, NODE_H)
}

fn compile_button_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + rect.h - 40.0, rect.w, 32.0)
}

impl EditorApp {
    pub(crate) fn draw_logic_library(&self, rect: Rect) {
        draw_section_header(Rect::new(rect.x, rect.y, rect.w, 24.0), "Behavior Palette", Some("Deterministic"));
        let mut y = rect.y + 36.0;
        draw_list_row(Rect::new(rect.x, y, rect.w, 46.0), &self.logic_studio.graph.display_name, Some("Behavior Graph"), true);
        y += 58.0;
        for kind in logic_palette() {
            let row = Rect::new(rect.x, y, rect.w, PALETTE_ROW_H - 2.0);
            let category = match kind {
                LogicNodeKind::EventInteract | LogicNodeKind::EventEnter => "Event",
                LogicNodeKind::ConditionFlag | LogicNodeKind::ConditionHasItem => "Condition",
                LogicNodeKind::ActionSetFlag | LogicNodeKind::ActionGiveItem | LogicNodeKind::ActionPlaySound | LogicNodeKind::ActionPlayAnimation => "Action",
                LogicNodeKind::Branch | LogicNodeKind::Sequence => "Logic",
            };
            draw_list_row(row, kind.label(), Some(category), self.logic_studio.palette_kind == kind);
            y += PALETTE_ROW_H;
            if y > rect.y + rect.h - 20.0 { break; }
        }
    }

    pub(crate) fn draw_logic_workspace(&self, _rect: Rect) {
        let canvas = logic_graph_rect(self);
        draw_rectangle(canvas.x, canvas.y, canvas.w, canvas.h, Color::new(0.055, 0.055, 0.058, 1.0));
        draw_rectangle_lines(canvas.x, canvas.y, canvas.w, canvas.h, 1.0, editor_theme::colors::BORDER_STRONG);
        let grid = 32.0;
        let mut x = canvas.x + self.logic_studio.canvas_pan[0].rem_euclid(grid);
        while x < canvas.x + canvas.w {
            draw_line(x, canvas.y, x, canvas.y + canvas.h, 1.0, Color::new(0.15, 0.15, 0.15, 0.55));
            x += grid;
        }
        let mut y = canvas.y + self.logic_studio.canvas_pan[1].rem_euclid(grid);
        while y < canvas.y + canvas.h {
            draw_line(canvas.x, y, canvas.x + canvas.w, y, 1.0, Color::new(0.15, 0.15, 0.15, 0.55));
            y += grid;
        }
        for link in &self.logic_studio.graph.links {
            let Some(from_index) = self.logic_studio.graph.nodes.iter().position(|node| node.id == link.from_node) else { continue; };
            let Some(to_index) = self.logic_studio.graph.nodes.iter().position(|node| node.id == link.to_node) else { continue; };
            let from = logic_node_rect(canvas, &self.logic_studio.graph.nodes[from_index], self.logic_studio.canvas_pan);
            let to = logic_node_rect(canvas, &self.logic_studio.graph.nodes[to_index], self.logic_studio.canvas_pan);
            draw_line(from.x + from.w, from.y + from.h * 0.5, to.x, to.y + to.h * 0.5, 2.0, editor_theme::colors::ACCENT);
        }
        for (index, node) in self.logic_studio.graph.nodes.iter().enumerate() {
            let rect = logic_node_rect(canvas, node, self.logic_studio.canvas_pan);
            let selected = self.logic_studio.selected_node == Some(index);
            draw_rectangle(rect.x, rect.y, rect.w, rect.h, if selected { Color::new(0.14, 0.17, 0.20, 1.0) } else { editor_theme::colors::PANEL_BG });
            draw_rectangle(rect.x, rect.y, rect.w, 22.0, if selected { editor_theme::colors::ACCENT_PRESSED } else { editor_theme::colors::PANEL_HEADER });
            draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, if selected { 2.0 } else { 1.0 }, if selected { editor_theme::colors::SELECTION_OUTLINE } else { editor_theme::colors::BORDER_SUBTLE });
            draw_scissored_text(&node.label, rect.x + 8.0, rect.y + 16.0, rect.w - 16.0, 12.0, editor_theme::colors::TEXT_PRIMARY);
            draw_scissored_text(&format!("{:?}", node.kind), rect.x + 8.0, rect.y + 44.0, rect.w - 16.0, 10.5, editor_theme::colors::TEXT_SECONDARY);
            draw_circle(rect.x, rect.y + rect.h * 0.5, 4.0, editor_theme::colors::TEXT_SECONDARY);
            draw_circle(rect.x + rect.w, rect.y + rect.h * 0.5, 4.0, editor_theme::colors::ACCENT_HOVER);
        }
        if let Some(index) = self.logic_studio.link_source {
            if let Some(node) = self.logic_studio.graph.nodes.get(index) {
                let rect = logic_node_rect(canvas, node, self.logic_studio.canvas_pan);
                draw_circle_lines(rect.x + rect.w, rect.y + rect.h * 0.5, 8.0, 2.0, editor_theme::colors::WARN);
            }
        }
        draw_editor_text("Logic Studio | graph authoring compiles to deterministic Havenwild instructions", canvas.x + 10.0, canvas.y + 20.0, 12.0, editor_theme::colors::TEXT_SECONDARY);
    }

    pub(crate) fn draw_logic_inspector(&self, rect: Rect) {
        draw_section_header(Rect::new(rect.x, rect.y, rect.w, 24.0), "Logic Properties", Some("W62G"));
        let issues = self.logic_studio.graph.validate();
        let compiled_count = self.logic_studio.graph.compile().ok().map(|compiled| compiled.instructions.len()).unwrap_or(0);
        let mut y = rect.y + 40.0;
        draw_editor_text(&format!("Nodes: {} | Links: {}", self.logic_studio.graph.nodes.len(), self.logic_studio.graph.links.len()), rect.x, y, 13.0, editor_theme::colors::TEXT_PRIMARY);
        y += 24.0;
        draw_editor_text(&format!("Compiled instructions: {compiled_count}"), rect.x, y, 12.0, editor_theme::colors::TEXT_SECONDARY);
        y += 30.0;
        if let Some(index) = self.logic_studio.selected_node {
            if let Some(node) = self.logic_studio.graph.nodes.get(index) {
                draw_editor_text("Selected Node", rect.x, y, 14.0, editor_theme::colors::TEXT_PRIMARY);
                y += 22.0;
                draw_scissored_text(&node.label, rect.x, y, rect.w, 13.0, editor_theme::colors::ACCENT_HOVER);
                y += 22.0;
                draw_editor_text(&format!("Position: {:.0}, {:.0}", node.position[0], node.position[1]), rect.x, y, 12.0, editor_theme::colors::TEXT_SECONDARY);
            }
        }
        if issues.is_empty() {
            draw_editor_text("Graph valid", rect.x, rect.y + rect.h - 70.0, 12.0, editor_theme::colors::GOOD);
        } else {
            draw_scissored_text(&issues.join(" | "), rect.x, rect.y + rect.h - 70.0, rect.w, 11.0, editor_theme::colors::WARN);
        }
        draw_editor_widget_tone(compile_button_rect(rect), "Compile / Validate", false, WidgetTone::Primary);
    }

    pub(crate) fn handle_logic_palette_click_in_rect(&mut self, mx: f32, my: f32, rect: Rect) -> bool {
        let point = vec2(mx, my);
        if !rect.contains(point) { return false; }
        let mut y = rect.y + 36.0 + 58.0;
        for kind in logic_palette() {
            let row = Rect::new(rect.x, y, rect.w, PALETTE_ROW_H - 2.0);
            if row.contains(point) {
                self.logic_studio.palette_kind = kind;
                self.canvas_active_tool = tool_registry::UniversalTool::Place;
                self.status_message = format!("Logic node armed: {} | click graph to place", kind.label());
                return true;
            }
            y += PALETTE_ROW_H;
        }
        true
    }

    pub(crate) fn handle_logic_studio_click(&mut self, mx: f32, my: f32) -> bool {
        let point = vec2(mx, my);
        if self.workspace_shell.left_panel_visible {
            let rect = self.contextual_asset_browser_rect();
            if rect.contains(point) {
                return self.handle_logic_palette_click_in_rect(mx, my, rect);
            }
        }
        if self.workspace_shell.right_panel_visible {
            let rect = self.inspector_content_rect();
            if compile_button_rect(rect).contains(point) {
                self.status_message = match self.logic_studio.graph.compile() {
                    Ok(compiled) => format!("Logic graph compiled: {} deterministic instructions", compiled.instructions.len()),
                    Err(issues) => format!("Logic graph validation failed: {}", issues.join(" | ")),
                };
                return true;
            }
        }
        let canvas = logic_graph_rect(self);
        if !canvas.contains(point) { return false; }
        let hit = self.logic_studio.graph.nodes.iter().enumerate().rev().find_map(|(index, node)| {
            logic_node_rect(canvas, node, self.logic_studio.canvas_pan).contains(point).then_some(index)
        });
        match self.canvas_active_tool {
            tool_registry::UniversalTool::Place => {
                let local = [mx - canvas.x - self.logic_studio.canvas_pan[0] - NODE_W * 0.5, my - canvas.y - self.logic_studio.canvas_pan[1] - NODE_H * 0.5];
                self.logic_studio.graph.nodes.push(LogicNode::new(self.logic_studio.palette_kind, local));
                self.logic_studio.selected_node = Some(self.logic_studio.graph.nodes.len() - 1);
                self.logic_studio.dirty = true;
                self.status_message = format!("Placed {} node", self.logic_studio.palette_kind.label());
                true
            }
            tool_registry::UniversalTool::Link => {
                if let Some(index) = hit {
                    if let Some(source) = self.logic_studio.link_source.take() {
                        if source != index {
                            let from_node = self.logic_studio.graph.nodes[source].id.clone();
                            let to_node = self.logic_studio.graph.nodes[index].id.clone();
                            if !self.logic_studio.graph.links.iter().any(|link| link.from_node == from_node && link.to_node == to_node) {
                                self.logic_studio.graph.links.push(LogicLink { from_node, to_node });
                                self.logic_studio.dirty = true;
                            }
                            self.status_message = "Connected Logic Studio nodes".to_string();
                        }
                    } else {
                        self.logic_studio.link_source = Some(index);
                        self.status_message = "Logic link source selected; choose destination".to_string();
                    }
                }
                true
            }
            tool_registry::UniversalTool::Move => {
                self.logic_studio.selected_node = hit;
                if let Some(index) = hit {
                    let node = &self.logic_studio.graph.nodes[index];
                    self.logic_studio.drag_offset = Some([
                        mx - canvas.x - self.logic_studio.canvas_pan[0] - node.position[0],
                        my - canvas.y - self.logic_studio.canvas_pan[1] - node.position[1],
                    ]);
                }
                true
            }
            _ => {
                self.logic_studio.selected_node = hit;
                true
            }
        }
    }

    pub(crate) fn update_logic_studio_input(&mut self) {
        if let (Some(index), Some(offset)) = (self.logic_studio.selected_node, self.logic_studio.drag_offset) {
            if is_mouse_button_down(MouseButton::Left) && self.canvas_active_tool == tool_registry::UniversalTool::Move {
                let canvas = logic_graph_rect(self);
                let (mx, my) = mouse_position();
                if let Some(node) = self.logic_studio.graph.nodes.get_mut(index) {
                    node.position = [
                        (mx - canvas.x - self.logic_studio.canvas_pan[0] - offset[0]).round(),
                        (my - canvas.y - self.logic_studio.canvas_pan[1] - offset[1]).round(),
                    ];
                    self.logic_studio.dirty = true;
                }
            } else {
                self.logic_studio.drag_offset = None;
            }
        }
    }
}
