use super::render_helpers::*;
use super::*;

fn enclosed_action_rect(rect: Rect, index: usize) -> Rect {
    let gap = 6.0;
    let width = ((rect.w - gap) * 0.5).max(92.0);
    Rect::new(
        rect.x + (index % 2) as f32 * (width + gap),
        rect.y + 126.0 + (index / 2) as f32 * 38.0,
        width,
        31.0,
    )
}

impl EditorApp {
    pub(crate) fn draw_enclosed_scene_inspector(&self, rect: Rect, scene: &SceneMap) {
        let skin = haven_core::EnclosedWallSkin::default_for_scene(scene.kind);
        draw_editor_text("Enclosed Scene Authoring", rect.x, rect.y + 22.0, 24.0, TEXT);
        draw_scissored_text(
            &format!("{} | {}", scene.name, skin.code()),
            rect.x,
            rect.y + 50.0,
            rect.w,
            16.0,
            GOOD,
        );
        let render_bounds = scene
            .renderable_bounds()
            .map(|(x0, y0, x1, y1)| format!("Renderable: {x0},{y0} → {x1},{y1}"))
            .unwrap_or_else(|| "Renderable: empty".to_string());
        draw_scissored_text(&render_bounds, rect.x, rect.y + 74.0, rect.w, 14.0, MUTED);
        draw_scissored_text(
            "Unused Wall/CaveWall backing remains void and is not part of the visible scene.",
            rect.x,
            rect.y + 96.0,
            rect.w,
            13.0,
            MUTED,
        );
        for (index, label) in [
            "Paint Floor",
            "Paint Wall",
            "Place Door",
            "Collision",
            "Pixel Edit",
            "Play Here",
        ]
        .into_iter()
        .enumerate()
        {
            draw_editor_widget(enclosed_action_rect(rect, index), label, false);
        }
        draw_wrapped(
            "Interior and cave authoring share the same semantic wall topology. Walls define collision/navigation; the active skin controls presentation. Door placement cuts a walkable threshold and places the published animated structural door.",
            rect.x,
            rect.y + 258.0,
            rect.w,
            14.0,
            TEXT,
        );
    }

    pub(crate) fn handle_enclosed_scene_inspector_click(
        &mut self,
        mx: f32,
        my: f32,
        rect: Rect,
    ) -> bool {
        let mouse = vec2(mx, my);
        if !rect.contains(mouse) {
            return false;
        }
        let Some(kind) = self
            .model
            .world
            .scenes
            .get(self.selected_scene)
            .map(|scene| scene.kind)
        else {
            return true;
        };
        if kind == SceneKind::Exterior {
            return false;
        }
        for index in 0..6 {
            if !enclosed_action_rect(rect, index).contains(mouse) {
                continue;
            }
            match index {
                0 => self.activate_enclosed_scene_tile_brush(false),
                1 => self.activate_enclosed_scene_tile_brush(true),
                2 => self.activate_enclosed_scene_door_brush(),
                3 => {
                    let visible = !self.canvas_layer_kind_visible(super::canvas_layers::CanvasLayerKind::Collision);
                    self.set_game_canvas_layer_visibility(super::canvas_layers::CanvasLayerKind::Collision, visible);
                    self.status_message = format!(
                        "Collision overlay {}",
                        if visible { "enabled" } else { "disabled" }
                    );
                }
                4 => self.open_scene_tile_source_in_pixel_studio(),
                5 => self.play_development_world(true),
                _ => {}
            }
            return true;
        }
        true
    }

    fn activate_enclosed_scene_tile_brush(&mut self, wall: bool) {
        let Some(scene) = self.model.world.scenes.get(self.selected_scene) else {
            return;
        };
        let tile = match (scene.kind, wall) {
            (SceneKind::Interior, true) => TileKind::Wall,
            (SceneKind::Interior, false) => TileKind::WoodFloor,
            (SceneKind::Cave, true) => TileKind::CaveWall,
            (SceneKind::Cave, false) => TileKind::CaveFloor,
            (SceneKind::Exterior, _) => return,
        };
        let Some(index) = TileKind::ALL.iter().position(|candidate| *candidate == tile) else {
            self.status_message = format!("{} is unavailable in the scene tile catalog", tile.label());
            return;
        };
        self.selected_tile = index;
        self.selected_placeable_id = None;
        self.selected_stamp_id = None;
        self.scene_layer_mode = SceneLayerMode::Terrain;
        self.terrain_paint_mode = TerrainPaintMode::Exact;
        self.set_scene_edit_tool(SceneEditTool::Paint);
        self.status_message = format!(
            "{} semantic brush active. Click or drag on the snapped grid; {} outside the authored shell remains void.",
            tile.label(),
            if wall { "wall backing" } else { "unused backing" }
        );
    }

    fn activate_enclosed_scene_door_brush(&mut self) {
        let Some(definition) = self.placeable_registry.resolve_alias("door_basic") else {
            self.status_message = "Published door_basic asset is unavailable".to_string();
            return;
        };
        self.selected_placeable_id = Some(definition.stable_id.clone());
        self.selected_placeable_preview_state = definition
            .states
            .iter()
            .position(|state| state == "closed")
            .unwrap_or(0);
        self.selected_stamp_id = None;
        self.scene_layer_mode = SceneLayerMode::Objects;
        self.set_scene_edit_tool(SceneEditTool::Place);
        self.status_message = "Animated structural door brush active. Place on an Interior/Cave wall cell; the editor cuts the walkable threshold and places the canonical door in one authoring action.".to_string();
    }

    pub(crate) fn prepare_enclosed_scene_doorway_for_place(
        &mut self,
        scene_id: &ProjectSceneId,
        x: i32,
        y: i32,
    ) -> Result<(), String> {
        let Some(scene) = self.model.world.scene_by_id(scene_id) else {
            return Err(format!("Scene {} is unavailable", scene_id.label()));
        };
        let floor = match scene.kind {
            SceneKind::Interior if scene.map.get(x, y) == TileKind::Wall => Some(TileKind::WoodFloor),
            SceneKind::Cave if scene.map.get(x, y) == TileKind::CaveWall => Some(TileKind::CaveFloor),
            _ => None,
        };
        let Some(floor) = floor else {
            return Ok(());
        };
        haven_editor::paint_scene_tile(
            &mut self.model.world,
            &mut self.command_bus,
            &self.model.project.project_id,
            EditorCommandSource::MainEditor,
            scene_id.clone(),
            x,
            y,
            floor,
        )?;
        Ok(())
    }
}
