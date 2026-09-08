use super::*;
use haven_core::SceneSemanticLayer;

impl EditorApp {
    pub(crate) fn active_scene_semantic_layer(&self) -> Option<SceneSemanticLayer> {
        use super::canvas_layers::CanvasLayerKind as L;
        match self.canvas_layer_context_override {
            Some(L::Navigation) => Some(SceneSemanticLayer::NavigationBlock),
            Some(L::Interaction) => Some(SceneSemanticLayer::Interaction),
            Some(L::Shelter) => Some(SceneSemanticLayer::Shelter),
            Some(L::Occlusion) => Some(SceneSemanticLayer::Occlusion),
            Some(L::WaterSwim) => Some(SceneSemanticLayer::WaterSwim),
            Some(L::SpawnPopulation) => Some(SceneSemanticLayer::SpawnPopulation),
            Some(L::BuildabilityFarming) => Some(SceneSemanticLayer::BuildabilityFarming),
            Some(L::LogicBindings) => Some(SceneSemanticLayer::LogicBinding),
            _ => None,
        }
    }

    pub(crate) fn apply_active_scene_semantic_tool(&mut self) -> bool {
        let Some(layer) = self.active_scene_semantic_layer() else { return false; };
        let x = self.scene_cursor_x;
        let y = self.scene_cursor_y;
        let tool = self.scene_edit_tool;
        let Some(scene) = self.model.world.scenes.get_at_mut(self.selected_scene) else { return true; };
        match tool {
            SceneEditTool::Paint | SceneEditTool::Place => {
                let changed = scene.semantic_layers.set(x, y, layer, true);
                if changed { self.status_message = format!("Painted {} at {}, {}", layer.code(), x, y); }
            }
            SceneEditTool::Erase => {
                let changed = scene.semantic_layers.set(x, y, layer, false);
                if changed { self.status_message = format!("Erased {} at {}, {}", layer.code(), x, y); }
            }
            SceneEditTool::Eyedropper | SceneEditTool::Select => {
                let enabled = scene.semantic_layers.has(x, y, layer);
                self.status_message = format!("{} at {}, {} = {}", layer.code(), x, y, if enabled { "on" } else { "off" });
            }
            SceneEditTool::Fill => {
                let target = !scene.semantic_layers.has(x, y, layer);
                for yy in 0..scene.dimensions.height as i32 {
                    for xx in 0..scene.dimensions.width as i32 {
                        scene.semantic_layers.set(xx, yy, layer, target);
                    }
                }
                self.status_message = format!("Filled {} = {} across {}", layer.code(), target, scene.name);
            }
            SceneEditTool::Rectangle => {
                let rect = self.selection.bounds.unwrap_or_else(|| GridRect::single(GridPos { x, y }));
                for cell in rect.cells() {
                    if scene.contains_cell(cell.x, cell.y) {
                        scene.semantic_layers.set(cell.x, cell.y, layer, true);
                    }
                }
                self.status_message = format!("Painted {} rectangle {}x{}", layer.code(), rect.width(), rect.height());
            }
            _ => {}
        }
        true
    }

    pub(crate) fn draw_active_scene_semantic_overlay(&self, scene: &SceneMap) {
        let Some(layer) = self.active_scene_semantic_layer() else { return; };
        use super::canvas_layers::CanvasLayerKind as L;
        let canvas_kind = match layer {
            SceneSemanticLayer::NavigationBlock => L::Navigation,
            SceneSemanticLayer::Interaction => L::Interaction,
            SceneSemanticLayer::Shelter => L::Shelter,
            SceneSemanticLayer::Occlusion => L::Occlusion,
            SceneSemanticLayer::WaterSwim => L::WaterSwim,
            SceneSemanticLayer::SpawnPopulation => L::SpawnPopulation,
            SceneSemanticLayer::BuildabilityFarming => L::BuildabilityFarming,
            SceneSemanticLayer::LogicBinding => L::LogicBindings,
        };
        if !self.canvas_layer_kind_visible(canvas_kind) {
            return;
        }
        let color = match layer {
            SceneSemanticLayer::NavigationBlock => Color::new(0.95, 0.22, 0.22, 0.30),
            SceneSemanticLayer::Interaction => Color::new(0.95, 0.72, 0.20, 0.30),
            SceneSemanticLayer::Shelter => Color::new(0.35, 0.70, 1.0, 0.26),
            SceneSemanticLayer::Occlusion => Color::new(0.62, 0.34, 0.90, 0.28),
            SceneSemanticLayer::WaterSwim => Color::new(0.15, 0.55, 0.95, 0.30),
            SceneSemanticLayer::SpawnPopulation => Color::new(0.30, 0.88, 0.44, 0.28),
            SceneSemanticLayer::BuildabilityFarming => Color::new(0.62, 0.88, 0.28, 0.26),
            SceneSemanticLayer::LogicBinding => Color::new(1.0, 0.38, 0.78, 0.28),
        };
        for y in 0..scene.dimensions.height as i32 {
            for x in 0..scene.dimensions.width as i32 {
                if scene.semantic_layers.has(x, y, layer) {
                    draw_rectangle(x as f32, y as f32, 1.0, 1.0, color);
                    draw_rectangle_lines(x as f32, y as f32, 1.0, 1.0, 0.06 / self.scene_canvas.zoom.max(0.2), color);
                }
            }
        }
    }
}
