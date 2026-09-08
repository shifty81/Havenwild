use super::*;

impl EditorApp {
    pub(crate) fn world_surface_value(&self) -> Option<WorldSurfaceValue> {
        match self.world_layer_mode {
            WorldLayerMode::Terrain => Some(WorldSurfaceValue::Terrain(self.selected_tile_kind())),
            WorldLayerMode::Zones => Some(WorldSurfaceValue::Zone(self.selected_zone_kind())),
            WorldLayerMode::StructuralLevels => Some(WorldSurfaceValue::StructuralLevel(
                haven_world::normalize_structural_authoring_level_v1(self.world_structural_level),
            )),
            WorldLayerMode::Objects => None,
        }
    }

    fn world_selected_or_cursor_cells(&self) -> Vec<GridPos> {
        self.world_selection
            .unwrap_or_else(|| {
                GridRect::single(GridPos {
                    x: self.world_cursor_x,
                    y: self.world_cursor_y,
                })
            })
            .cells()
    }

    pub(crate) fn apply_world_structural_level_to_selection(&mut self, level: u8, label: &str) {
        if self.world_layer_mode != WorldLayerMode::StructuralLevels {
            self.status_message =
                "Switch to Levels & Cliffs before applying a platform level".to_string();
            return;
        }
        let Some(manifest) = self.scene_rectangles.clone() else {
            return;
        };
        let cells = self.world_selected_or_cursor_cells();
        let result = paint_world_surface_cells(
            &mut self.model.world,
            &mut self.command_bus,
            &self.model.project.project_id,
            EditorCommandSource::MainEditor,
            &manifest,
            &self.scene_assignments,
            self.selected_landmass_id,
            cells,
            WorldSurfaceValue::StructuralLevel(
                haven_world::normalize_structural_authoring_level_v1(level),
            ),
            label.to_string(),
        );
        self.finish_world_result(result);
    }

    pub(crate) fn adjust_world_structural_selection(&mut self, delta: i8) {
        if self.world_layer_mode != WorldLayerMode::StructuralLevels {
            self.status_message =
                "Switch to Levels & Cliffs before raising or lowering a platform".to_string();
            return;
        }
        let Some(manifest) = self.scene_rectangles.clone() else {
            return;
        };
        let label = if delta > 0 {
            "Raise selected platform one level"
        } else {
            "Lower selected platform one level"
        };
        let cells = self.world_selected_or_cursor_cells();
        let result = adjust_world_structural_levels(
            &mut self.model.world,
            &mut self.command_bus,
            &self.model.project.project_id,
            EditorCommandSource::MainEditor,
            &manifest,
            &self.scene_assignments,
            self.selected_landmass_id,
            cells,
            delta,
            label,
        );
        self.finish_world_result(result);
    }
    pub(crate) fn active_world_structural_connector_kind(&self) -> Option<WorldStructuralConnectorKind> {
        if self.world_layer_mode != WorldLayerMode::StructuralLevels {
            return None;
        }
        match self.canvas_authoring_context.source_id.as_deref() {
            Some("connector.ramp") => Some(WorldStructuralConnectorKind::Ramp),
            Some("connector.ladder") => Some(WorldStructuralConnectorKind::Ladder),
            _ => None,
        }
    }

    pub(crate) fn world_structural_connector_preview(&self) -> Result<WorldStructuralConnectorPlan, String> {
        let kind = self.active_world_structural_connector_kind()
            .ok_or_else(|| "Choose Ramp or Ladder from the Elevation palette first".to_string())?;
        let selection = self.world_selection
            .ok_or_else(|| "Select a cliff section to resolve a structural connector host".to_string())?;
        let manifest = self.scene_rectangles.as_ref()
            .ok_or_else(|| "World surface manifest is unavailable".to_string())?;
        resolve_world_structural_connector_plan(
            &self.model.world,
            manifest,
            &self.scene_assignments,
            self.selected_landmass_id,
            selection,
            kind,
        )
    }

    pub(crate) fn apply_world_structural_connector_selection(&mut self) {
        let plan = match self.world_structural_connector_preview() {
            Ok(plan) => plan,
            Err(error) => {
                self.status_message = error;
                return;
            }
        };
        let Some(manifest) = self.scene_rectangles.clone() else {
            self.status_message = "World surface manifest is unavailable".to_string();
            return;
        };
        let result = place_world_structural_connector(
            &mut self.model.world,
            &mut self.command_bus,
            &self.model.project.project_id,
            EditorCommandSource::MainEditor,
            &manifest,
            &self.scene_assignments,
            self.selected_landmass_id,
            &plan,
        );
        self.finish_world_result(result);
    }

}
