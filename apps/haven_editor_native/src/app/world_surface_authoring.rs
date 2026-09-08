use super::*;

use super::world_surface_authoring_geometry::global_grid_line;

impl EditorApp {
    pub(crate) fn world_cell_at_mouse(&self) -> Option<GridPos> {
        // Complete-world mode is a navigation/LOD surface. Once a landmass is
        // selected the editor returns to native tile coordinates for actual
        // semantic/Pixel authoring.
        if self.world_show_entire_world {
            return None;
        }
        let manifest = self.scene_rectangles.as_ref()?;
        let bounds = world_scene_grid_bounds_for_landmass(manifest, self.selected_landmass_id)?;
        let viewport = self.world_canvas_viewport_rect();
        let mouse = vec2(mouse_position().0, mouse_position().1);
        if !viewport.contains(mouse) {
            return None;
        }
        let cell = self
            .world_canvas
            .screen_to_grid_cell(viewport, bounds, mouse, 1.0);
        resolve_world_surface_cell(
            manifest,
            &self.scene_assignments,
            &self.model.world,
            self.selected_landmass_id,
            cell,
        )
        .ok()
        .map(|_| cell)
    }

    pub(crate) fn set_world_edit_tool(&mut self, tool: WorldEditTool) {
        let _ = self.command_bus.commit_gesture();
        self.world_drag = None;
        self.world_last_painted = None;
        self.world_paste_anchor = None;
        self.world_asset_place_anchor = None;
        if self.world_layer_mode == WorldLayerMode::StructuralLevels
            && matches!(
                tool,
                WorldEditTool::Paint | WorldEditTool::Erase | WorldEditTool::Replace
            )
        {
            self.world_edit_tool = WorldEditTool::Rectangle;
            self.world_canvas_pan_tool = false;
            self.status_message =
                "Structural levels use region/platform operations; freeform paint, erase, and global replace are disabled"
                    .to_string();
            return;
        }
        self.world_edit_tool = tool;
        self.world_canvas_pan_tool = tool == WorldEditTool::Pan;
        self.status_message = format!(
            "World {} tool active on {}",
            tool.label(),
            self.world_layer_mode.label()
        );
    }

    pub(crate) fn set_world_layer_mode(&mut self, layer: WorldLayerMode) {
        let _ = self.command_bus.commit_gesture();
        self.world_layer_mode = layer;
        self.canvas_layer_context_override = None;
        self.world_drag = None;
        self.world_last_painted = None;
        self.world_paste_anchor = None;
        self.world_asset_place_anchor = None;
        self.world_edit_tool = WorldEditTool::Select;
        self.world_canvas_pan_tool = false;
        self.canvas_active_tool = super::tool_registry::UniversalTool::Select;
        self.status_message = format!(
            "World layer: {}. Select remains active; choose a modifying tool explicitly.",
            layer.label()
        );
    }

    pub(crate) fn update_world_editor_input(
        &mut self,
        pointer_consumed: bool,
        canvas_pointer_consumed: bool,
    ) {
        let left_pressed = is_mouse_button_pressed(MouseButton::Left);
        let left_down = is_mouse_button_down(MouseButton::Left);
        let left_released = is_mouse_button_released(MouseButton::Left);
        let control_down = is_key_down(KeyCode::LeftControl) || is_key_down(KeyCode::RightControl);
        let shift_down = is_key_down(KeyCode::LeftShift) || is_key_down(KeyCode::RightShift);

        // Complete-world LOD is the real generated archipelago, but destructive
        // editing remains tile-accurate: select a landmass from the overview to
        // enter its native surface coordinate space, then use the same semantic
        // and Pixel workflows as before.
        if self.world_show_entire_world {
            if !pointer_consumed
                && !canvas_pointer_consumed
                && left_pressed
                && matches!(self.world_edit_tool, WorldEditTool::Select)
            {
                let viewport = self.world_canvas_viewport_rect();
                let mouse = vec2(mouse_position().0, mouse_position().1);
                if viewport.contains(mouse) {
                    let hit = self.scene_rectangles.as_ref().and_then(|manifest| {
                        let bake = self.development_world_semantic_bake.as_ref()?;
                        let bounds = world_archipelago_overview_bounds(bake)?;
                        let point = self.world_canvas.screen_to_world(viewport, bounds, mouse);
                        world_overview_landmass_at_point(
                            manifest,
                            &self.development_world_settings,
                            bake,
                            point,
                        )
                    });
                    if let Some((rectangle_index, landmass_id)) = hit {
                        self.selected_rectangle = rectangle_index;
                        self.selected_landmass_id = landmass_id;
                        self.sync_assignment_cycles_to_selected_rectangle();
                        let landmass_name = self
                            .selected_rectangle_spec()
                            .map(|entry| entry.landmass_name.clone())
                            .unwrap_or_else(|| format!("Landmass {landmass_id}"));
                        self.frame_selected_landmass();
                        self.status_message = format!(
                            "Editing {landmass_name} | Open Complete World returns to the archipelago overview"
                        );
                        return;
                    }
                }
            }
            self.handle_world_keyboard_shortcuts(control_down, shift_down);
            return;
        }

        if !pointer_consumed && !canvas_pointer_consumed {
            if let Some(cell) = self.world_cell_at_mouse() {
                if self.world_paste_anchor.is_some() {
                    self.world_paste_anchor = Some(cell);
                    self.world_cursor_x = cell.x;
                    self.world_cursor_y = cell.y;
                    if left_pressed {
                        self.commit_world_paste_preview();
                    }
                } else if self.world_asset_place_anchor.is_some() {
                    self.world_asset_place_anchor = Some(cell);
                    self.world_cursor_x = cell.x;
                    self.world_cursor_y = cell.y;
                    if left_pressed {
                        self.commit_world_asset_place_preview();
                    }
                } else if left_pressed {
                    self.world_cursor_x = cell.x;
                    self.world_cursor_y = cell.y;
                    if self.world_show_entire_world {
                        if let Some(manifest) = self.scene_rectangles.as_ref() {
                            if let Some(landmass_id) = world_landmass_at_global_cell(manifest, cell) {
                                if landmass_id != self.selected_landmass_id {
                                    self.selected_landmass_id = landmass_id;
                                    self.status_message = format!(
                                        "World edit focus switched to landmass {} at {}, {}",
                                        landmass_id, cell.x, cell.y
                                    );
                                }
                            }
                        }
                    }
                    self.begin_world_canvas_action(cell, shift_down);
                } else if left_down {
                    self.world_cursor_x = cell.x;
                    self.world_cursor_y = cell.y;
                    self.update_world_canvas_action(cell);
                }
            }
        }

        if left_released
            && self.world_paste_anchor.is_none()
            && self.world_asset_place_anchor.is_none()
        {
            self.finish_world_canvas_action();
        }
        if is_key_pressed(KeyCode::Escape) {
            if self.world_paste_anchor.take().is_some() {
                self.status_message = "Cancelled pending world paste".to_string();
                self.world_drag = None;
                self.world_last_painted = None;
                return;
            }
            if self.world_asset_place_anchor.take().is_some() {
                self.status_message = "Cancelled pending world asset placement".to_string();
                self.world_drag = None;
                self.world_last_painted = None;
                return;
            }
            if self.command_bus.gesture_is_open() {
                match self.command_bus.cancel_gesture(&mut self.model.world) {
                    Ok(()) => self.status_message = "Cancelled global world edit".to_string(),
                    Err(error) => {
                        self.status_message = format!("Global edit cancel failed: {error}")
                    }
                }
            }
            self.world_drag = None;
            self.world_last_painted = None;
            self.set_world_edit_tool(WorldEditTool::Select);
            self.status_message = "Inspect/Select active; canvas clicks are non-destructive".to_string();
        }

        self.handle_world_keyboard_shortcuts(control_down, shift_down);
    }

    fn begin_world_canvas_action(&mut self, cell: GridPos, additive: bool) {
        let _ = self.select_world_cell(cell);
        match self.world_edit_tool {
            WorldEditTool::Pan => {}
            WorldEditTool::Paint | WorldEditTool::Erase => {
                self.command_bus.begin_gesture();
                self.apply_world_tool_at(cell);
                self.world_last_painted = Some(cell);
            }
            WorldEditTool::Place
            | WorldEditTool::Fill
            | WorldEditTool::Replace
            | WorldEditTool::Eyedropper => self.apply_world_tool_at(cell),
            WorldEditTool::Rectangle => {
                if self.world_layer_mode == WorldLayerMode::Objects {
                    self.status_message =
                        "Rectangle authoring is available for terrain, zones, and structural levels"
                            .to_string();
                } else {
                    self.world_drag = Some(WorldCanvasDrag {
                        kind: WorldCanvasDragKind::Rectangle,
                        start: cell,
                        current: cell,
                    });
                }
            }
            WorldEditTool::Select => {
                if additive {
                    self.world_selection = Some(match self.world_selection {
                        Some(existing) => GridRect::from_points(
                            GridPos {
                                x: existing.min.x.min(cell.x),
                                y: existing.min.y.min(cell.y),
                            },
                            GridPos {
                                x: existing.max.x.max(cell.x),
                                y: existing.max.y.max(cell.y),
                            },
                        ),
                        None => GridRect::single(cell),
                    });
                } else {
                    self.world_drag = Some(WorldCanvasDrag {
                        kind: WorldCanvasDragKind::Marquee,
                        start: cell,
                        current: cell,
                    });
                }
            }
        }
    }

    fn update_world_canvas_action(&mut self, cell: GridPos) {
        if let Some(drag) = self.world_drag.as_mut() {
            drag.current = cell;
            return;
        }
        if matches!(
            self.world_edit_tool,
            WorldEditTool::Paint | WorldEditTool::Erase
        ) && self.world_last_painted != Some(cell)
        {
            let previous = self.world_last_painted.unwrap_or(cell);
            for point in global_grid_line(previous, cell).into_iter().skip(1) {
                self.apply_world_tool_at(point);
            }
            self.world_last_painted = Some(cell);
        }
    }

    fn finish_world_canvas_action(&mut self) {
        if let Some(drag) = self.world_drag.take() {
            match drag.kind {
                WorldCanvasDragKind::Rectangle => self.apply_world_rectangle(drag.rect()),
                WorldCanvasDragKind::Marquee => {
                    self.world_selection = Some(drag.rect());
                    self.status_message = format!(
                        "Selected global rectangle {},{} to {},{} ({}x{})",
                        drag.rect().min.x,
                        drag.rect().min.y,
                        drag.rect().max.x,
                        drag.rect().max.y,
                        drag.rect().width(),
                        drag.rect().height()
                    );
                }
            }
        }
        if let Some(step) = self.command_bus.commit_gesture() {
            self.status_message = format!(
                "Committed {} as one global undo step ({} operations)",
                step.label, step.operation_count
            );
        }
        self.world_last_painted = None;
    }

    fn world_brush_cells(&self, center: GridPos) -> Vec<GridPos> {
        let radius = self.world_brush_radius.max(0);
        GridRect::from_points(
            GridPos {
                x: center.x - radius,
                y: center.y - radius,
            },
            GridPos {
                x: center.x + radius,
                y: center.y + radius,
            },
        )
        .cells()
    }

    fn apply_world_tool_at(&mut self, cell: GridPos) {
        self.world_cursor_x = cell.x;
        self.world_cursor_y = cell.y;
        match self.world_edit_tool {
            WorldEditTool::Select | WorldEditTool::Pan | WorldEditTool::Rectangle => {}
            WorldEditTool::Eyedropper => self.pick_world_brush(cell),
            WorldEditTool::Fill => self.apply_world_fill(cell),
            WorldEditTool::Replace => self.apply_world_replace(cell),
            WorldEditTool::Place => {
                let _ = self.place_world_content(cell);
            }
            WorldEditTool::Paint => self.paint_world_cells(cell, false),
            WorldEditTool::Erase => self.paint_world_cells(cell, true),
        }
    }

    fn paint_world_cells(&mut self, cell: GridPos, erase: bool) {
        let Some(manifest) = self.scene_rectangles.clone() else {
            self.status_message = "No world-surface manifest loaded".to_string();
            return;
        };
        if self.world_layer_mode == WorldLayerMode::StructuralLevels {
            self.status_message =
                "Structural levels are authored as selected or rectangular platform regions, never freeform brush strokes"
                    .to_string();
            return;
        }
        let value = if erase {
            match self.world_layer_mode {
                WorldLayerMode::Terrain => WorldSurfaceValue::Terrain(TileKind::Grass),
                WorldLayerMode::Zones => WorldSurfaceValue::Zone(ZoneKind::None),
                WorldLayerMode::StructuralLevels => {
                    self.status_message =
                        "Use Carve to Level 0 on a selected platform region; structural brush erase is disabled"
                            .to_string();
                    return;
                }
                WorldLayerMode::Objects => {
                    self.erase_world_object(cell);
                    return;
                }
            }
        } else if let Some(value) = self.world_surface_value() {
            value
        } else {
            let _ = self.place_world_content(cell);
            return;
        };
        let brush_cells = self.world_brush_cells(cell);
        let result = paint_world_surface_cells(
            &mut self.model.world,
            &mut self.command_bus,
            &self.model.project.project_id,
            EditorCommandSource::MainEditor,
            &manifest,
            &self.scene_assignments,
            self.selected_landmass_id,
            brush_cells,
            value,
            format!(
                "{} {}",
                if erase { "Erase" } else { "Paint" },
                value.label()
            ),
        );
        self.finish_world_result(result);
    }

    fn apply_world_rectangle(&mut self, rect: GridRect) {
        let Some(manifest) = self.scene_rectangles.clone() else {
            return;
        };
        let Some(value) = self.world_surface_value() else {
            self.status_message =
                "Rectangle authoring is available for terrain, zones, and structural levels"
                    .to_string();
            return;
        };
        let result = paint_world_surface_rectangle(
            &mut self.model.world,
            &mut self.command_bus,
            &self.model.project.project_id,
            EditorCommandSource::MainEditor,
            &manifest,
            &self.scene_assignments,
            self.selected_landmass_id,
            rect,
            value,
        );
        self.finish_world_result(result);
    }

    fn apply_world_fill(&mut self, cell: GridPos) {
        let Some(manifest) = self.scene_rectangles.clone() else {
            return;
        };
        let Some(value) = self.world_surface_value() else {
            self.status_message =
                "Fill is available for terrain, zones, and structural levels".to_string();
            return;
        };
        let result = flood_fill_world_surface(
            &mut self.model.world,
            &mut self.command_bus,
            &self.model.project.project_id,
            EditorCommandSource::MainEditor,
            &manifest,
            &self.scene_assignments,
            self.selected_landmass_id,
            cell,
            value,
        );
        self.finish_world_result(result);
    }

    fn apply_world_replace(&mut self, cell: GridPos) {
        let Some(manifest) = self.scene_rectangles.clone() else {
            return;
        };
        if self.world_layer_mode == WorldLayerMode::StructuralLevels {
            self.status_message =
                "Global structural replace is disabled; select a platform region and use Apply, Raise, Lower, or Carve"
                    .to_string();
            return;
        }
        let Some(value) = self.world_surface_value() else {
            self.status_message = "Replace is available for terrain and zones".to_string();
            return;
        };
        let result = replace_world_surface_value(
            &mut self.model.world,
            &mut self.command_bus,
            &self.model.project.project_id,
            EditorCommandSource::MainEditor,
            &manifest,
            &self.scene_assignments,
            self.selected_landmass_id,
            cell,
            value,
        );
        self.finish_world_result(result);
    }

    fn pick_world_brush(&mut self, cell: GridPos) {
        let Some(manifest) = self.scene_rectangles.as_ref() else {
            return;
        };
        let Ok(address) = resolve_world_surface_cell(
            manifest,
            &self.scene_assignments,
            &self.model.world,
            self.selected_landmass_id,
            cell,
        ) else {
            return;
        };
        let Some(scene) = self.model.world.scene_by_id(&address.scene_id) else {
            return;
        };
        match self.world_layer_mode {
            WorldLayerMode::Terrain => {
                let tile = scene.map.get(address.local.x, address.local.y);
                if let Some(index) = TileKind::ALL
                    .iter()
                    .position(|candidate| *candidate == tile)
                {
                    self.selected_tile = index;
                }
                self.status_message = format!("Picked {} at {}, {}", tile.label(), cell.x, cell.y);
            }
            WorldLayerMode::Zones => {
                let zone = scene.zone_at(address.local.x, address.local.y);
                if let Some(index) = ZONE_BRUSHES.iter().position(|candidate| *candidate == zone) {
                    self.selected_zone = index;
                }
                self.status_message =
                    format!("Picked {} zone at {}, {}", zone.label(), cell.x, cell.y);
            }
            WorldLayerMode::StructuralLevels => {
                self.world_structural_level = scene
                    .map
                    .get_structural_level(address.local.x, address.local.y)
                    .unwrap_or(0);
                self.status_message = format!(
                    "Picked structural Level {} at {}, {}",
                    self.world_structural_level, cell.x, cell.y
                );
            }
            WorldLayerMode::Objects => {
                if let Some(index) = scene.map.object_at(address.local.x, address.local.y) {
                    let kind = scene.map.objects[index].kind;
                    if let Some(brush) = OBJECT_BRUSHES
                        .iter()
                        .position(|candidate| *candidate == kind)
                    {
                        self.selected_object = brush;
                        self.selected_stamp_id = None;
                    }
                    self.status_message = format!("Picked {}", kind.label());
                } else if let Some(index) = scene.map.stamp_at(address.local.x, address.local.y) {
                    self.selected_stamp_id = scene
                        .map
                        .stamps
                        .get(index)
                        .map(|stamp| stamp.stamp_key.clone());
                    self.status_message = "Picked world stamp".to_string();
                }
            }
        }
    }

    fn place_world_content(&mut self, cell: GridPos) -> bool {
        let Some(manifest) = self.scene_rectangles.clone() else {
            self.status_message = "No world-surface manifest loaded".to_string();
            return false;
        };
        let selected_stamp = self
            .selected_stamp_id
            .as_deref()
            .and_then(|id| self.stamp_registry.entry(id))
            .cloned();
        let selected_placeable = self
            .selected_placeable_id
            .as_deref()
            .and_then(|id| self.placeable_registry.entry(id))
            .cloned();
        let object_kind = self.selected_object_kind();
        let footprint = selected_stamp
            .as_ref()
            .map(|definition| definition.footprint)
            .or_else(|| {
                selected_placeable
                    .as_ref()
                    .map(|definition| definition.footprint)
            })
            .unwrap_or_else(|| {
                haven_assets::user_asset_registry::authored_object_footprint(object_kind)
            });
        let address = match validate_world_surface_footprint(
            &manifest,
            &self.scene_assignments,
            &self.model.world,
            self.selected_landmass_id,
            cell,
            footprint,
        ) {
            Ok(address) => address,
            Err(error) => {
                self.status_message = error;
                return false;
            }
        };
        let result = if let Some(definition) = selected_stamp.as_ref() {
            place_scene_stamp(
                &mut self.model.world,
                &mut self.command_bus,
                &self.model.project.project_id,
                EditorCommandSource::MainEditor,
                address.scene_id,
                address.local.x,
                address.local.y,
                definition,
            )
        } else if let Some(definition) = selected_placeable.as_ref() {
            place_scene_pack_asset(
                &mut self.model.world,
                &mut self.command_bus,
                &self.model.project.project_id,
                EditorCommandSource::MainEditor,
                address.scene_id,
                address.local.x,
                address.local.y,
                definition.compatibility_kind(),
                definition.footprint,
                definition.persistent_ref(),
                definition
                    .states
                    .get(self.selected_placeable_preview_state)
                    .or_else(|| definition.states.first())
                    .map(String::as_str),
                &definition.label,
            )
        } else {
            place_scene_object_with_footprint(
                &mut self.model.world,
                &mut self.command_bus,
                &self.model.project.project_id,
                EditorCommandSource::MainEditor,
                address.scene_id,
                address.local.x,
                address.local.y,
                object_kind,
                footprint,
            )
        };
        match result {
            Ok(outcome) => {
                self.status_message = outcome.message;
                true
            }
            Err(error) => {
                self.status_message = error;
                false
            }
        }
    }

    fn erase_world_object(&mut self, cell: GridPos) {
        let Some(manifest) = self.scene_rectangles.as_ref() else {
            return;
        };
        let address = match resolve_world_surface_cell(
            manifest,
            &self.scene_assignments,
            &self.model.world,
            self.selected_landmass_id,
            cell,
        ) {
            Ok(address) => address,
            Err(error) => {
                self.status_message = error;
                return;
            }
        };
        let has_stamp = self
            .model
            .world
            .scene_by_id(&address.scene_id)
            .and_then(|scene| scene.map.stamp_at(address.local.x, address.local.y))
            .is_some();
        let result = if has_stamp {
            erase_scene_stamp(
                &mut self.model.world,
                &mut self.command_bus,
                &self.model.project.project_id,
                EditorCommandSource::MainEditor,
                address.scene_id,
                address.local.x,
                address.local.y,
            )
        } else {
            erase_scene_object(
                &mut self.model.world,
                &mut self.command_bus,
                &self.model.project.project_id,
                EditorCommandSource::MainEditor,
                address.scene_id,
                address.local.x,
                address.local.y,
            )
        };
        self.status_message = result.map_or_else(|error| error, |outcome| outcome.message);
    }

    pub(crate) fn finish_world_result(
        &mut self,
        result: Result<haven_editor::WorldSurfaceEditOutcome, String>,
    ) {
        match result {
            Ok(outcome) => self.status_message = outcome.message,
            Err(error) => self.status_message = error,
        }
    }

    pub(crate) fn copy_world_selection(&mut self) {
        let Some(manifest) = self.scene_rectangles.as_ref() else {
            return;
        };
        let rect = self.world_selection.unwrap_or_else(|| {
            GridRect::single(GridPos {
                x: self.world_cursor_x,
                y: self.world_cursor_y,
            })
        });
        match copy_world_surface_rectangle(
            manifest,
            &self.scene_assignments,
            &self.model.world,
            self.selected_landmass_id,
            rect,
        ) {
            Ok(clipboard) => {
                self.status_message = format!("Copied {}", clipboard.summary());
                self.world_clipboard = Some(clipboard);
            }
            Err(error) => self.status_message = error,
        }
    }

    pub(crate) fn paste_world_selection(&mut self) {
        let Some(clipboard) = self.world_clipboard.as_ref() else {
            self.status_message = "World clipboard is empty".to_string();
            return;
        };
        self.world_asset_place_anchor = None;
        self.world_paste_anchor = Some(GridPos {
            x: self.world_cursor_x,
            y: self.world_cursor_y,
        });
        self.world_drag = None;
        self.world_last_painted = None;
        self.status_message = format!(
            "World paste preview armed: {} | move on the global tile grid, left-click to place, Esc to cancel",
            clipboard.summary()
        );
    }

    pub(crate) fn world_paste_preview_rect(&self) -> Option<GridRect> {
        let anchor = self.world_paste_anchor?;
        let clipboard = self.world_clipboard.as_ref()?;
        Some(GridRect::from_points(
            anchor,
            GridPos {
                x: anchor.x + clipboard.width.saturating_sub(1),
                y: anchor.y + clipboard.height.saturating_sub(1),
            },
        ))
    }

    pub(crate) fn arm_world_asset_place_preview(&mut self, anchor: GridPos) {
        self.world_paste_anchor = None;
        self.world_drag = None;
        self.world_last_painted = None;
        self.world_asset_place_anchor = Some(anchor);
        self.world_cursor_x = anchor.x;
        self.world_cursor_y = anchor.y;
        self.world_layer_mode = WorldLayerMode::Objects;
        self.world_edit_tool = WorldEditTool::Place;
        self.world_canvas_pan_tool = false;
        self.status_message = format!(
            "Asset placement preview at {}, {} | move on tile grid, left-click/Enter place, Esc cancel",
            anchor.x, anchor.y
        );
    }

    pub(crate) fn world_asset_place_preview_rect(&self) -> Option<GridRect> {
        let anchor = self.world_asset_place_anchor?;
        let footprint = self.selected_world_place_footprint();
        let min = GridPos {
            x: anchor.x + footprint.visual_offset_x,
            y: anchor.y + footprint.visual_offset_y,
        };
        let max = GridPos {
            x: min.x + footprint.visual_w.max(1) - 1,
            y: min.y + footprint.visual_h.max(1) - 1,
        };
        Some(GridRect::from_points(min, max))
    }

    fn selected_world_place_footprint(&self) -> haven_core::ObjectFootprint {
        self.selected_stamp_id
            .as_deref()
            .and_then(|id| self.stamp_registry.entry(id))
            .map(|definition| definition.footprint)
            .or_else(|| {
                self.selected_placeable_id
                    .as_deref()
                    .and_then(|id| self.placeable_registry.entry(id))
                    .map(|definition| definition.footprint)
            })
            .unwrap_or_else(|| {
                haven_assets::user_asset_registry::authored_object_footprint(
                    self.selected_object_kind(),
                )
            })
    }

    pub(crate) fn commit_world_asset_place_preview(&mut self) -> bool {
        let Some(anchor) = self.world_asset_place_anchor.take() else {
            return false;
        };
        self.world_cursor_x = anchor.x;
        self.world_cursor_y = anchor.y;
        let footprint = self.selected_world_place_footprint();
        if !self.place_world_content(anchor) {
            self.world_asset_place_anchor = Some(anchor);
            self.status_message = format!(
                "Asset placement preview remains active: {}",
                self.status_message
            );
            return true;
        }
        let min = GridPos {
            x: anchor.x + footprint.visual_offset_x,
            y: anchor.y + footprint.visual_offset_y,
        };
        let max = GridPos {
            x: min.x + footprint.visual_w.max(1) - 1,
            y: min.y + footprint.visual_h.max(1) - 1,
        };
        self.world_selection = Some(GridRect::from_points(min, max));
        self.status_message = format!(
            "{} | placed asset remains selected",
            self.status_message
        );
        true
    }

    pub(crate) fn commit_world_paste_preview(&mut self) -> bool {
        let Some(anchor) = self.world_paste_anchor else {
            return false;
        };
        let Some(manifest) = self.scene_rectangles.clone() else {
            self.world_paste_anchor = None;
            return true;
        };
        let Some(clipboard) = self.world_clipboard.clone() else {
            self.world_paste_anchor = None;
            self.status_message = "World clipboard is empty".to_string();
            return true;
        };
        let result = paste_world_surface_clipboard(
            &mut self.model.world,
            &mut self.command_bus,
            &self.model.project.project_id,
            EditorCommandSource::MainEditor,
            &manifest,
            &self.scene_assignments,
            self.selected_landmass_id,
            anchor,
            &clipboard,
        );
        match result {
            Ok(outcome) => {
                self.world_paste_anchor = None;
                self.world_selection = Some(GridRect::from_points(
                    anchor,
                    GridPos {
                        x: anchor.x + clipboard.width.saturating_sub(1),
                        y: anchor.y + clipboard.height.saturating_sub(1),
                    },
                ));
                self.status_message = format!("{} | pasted region remains selected", outcome.message);
            }
            Err(error) => {
                self.status_message = format!("World paste preview remains active: {error}");
            }
        }
        true
    }

    pub(crate) fn duplicate_world_selection(&mut self) {
        let Some(rect) = self.world_selection else {
            self.status_message = "Nothing selected to duplicate in the World Editor".to_string();
            return;
        };
        self.copy_world_selection();
        if self.world_clipboard.is_none() {
            return;
        }
        self.world_cursor_x = rect.min.x + 1;
        self.world_cursor_y = rect.min.y + 1;
        self.world_asset_place_anchor = None;
        self.world_paste_anchor = Some(GridPos {
            x: self.world_cursor_x,
            y: self.world_cursor_y,
        });
        self.status_message = format!(
            "Duplicate preview at {}, {} | move on tile grid, left-click/Enter place, Esc cancel",
            self.world_cursor_x, self.world_cursor_y
        );
    }

    fn nudge_world_paste_preview(&mut self, delta: GridPos) {
        let Some(anchor) = self.world_paste_anchor else { return; };
        let next = GridPos { x: anchor.x + delta.x, y: anchor.y + delta.y };
        if let Some(manifest) = self.scene_rectangles.as_ref() {
            if resolve_world_surface_cell(
                manifest,
                &self.scene_assignments,
                &self.model.world,
                self.selected_landmass_id,
                next,
            ).is_ok() {
                self.world_paste_anchor = Some(next);
                self.world_cursor_x = next.x;
                self.world_cursor_y = next.y;
                self.status_message = format!(
                    "World paste preview at {}, {} | arrows nudge, left-click/Enter place, Esc cancel",
                    next.x, next.y
                );
            }
        }
    }

    fn nudge_world_asset_place_preview(&mut self, delta: GridPos) {
        let Some(anchor) = self.world_asset_place_anchor else { return; };
        let next = GridPos { x: anchor.x + delta.x, y: anchor.y + delta.y };
        if let Some(manifest) = self.scene_rectangles.as_ref() {
            let footprint = self.selected_world_place_footprint();
            if validate_world_surface_footprint(
                manifest,
                &self.scene_assignments,
                &self.model.world,
                self.selected_landmass_id,
                next,
                footprint,
            ).is_ok() {
                self.world_asset_place_anchor = Some(next);
                self.world_cursor_x = next.x;
                self.world_cursor_y = next.y;
                self.status_message = format!(
                    "Asset placement preview at {}, {} | arrows nudge, left-click/Enter place, Esc cancel",
                    next.x, next.y
                );
            }
        }
    }

    fn handle_world_keyboard_shortcuts(&mut self, control_down: bool, shift_down: bool) {
        if self.world_asset_place_anchor.is_some() {
            if is_key_pressed(KeyCode::Right) { self.nudge_world_asset_place_preview(GridPos { x: 1, y: 0 }); }
            if is_key_pressed(KeyCode::Left) { self.nudge_world_asset_place_preview(GridPos { x: -1, y: 0 }); }
            if is_key_pressed(KeyCode::Down) { self.nudge_world_asset_place_preview(GridPos { x: 0, y: 1 }); }
            if is_key_pressed(KeyCode::Up) { self.nudge_world_asset_place_preview(GridPos { x: 0, y: -1 }); }
            if is_key_pressed(KeyCode::Enter) { self.commit_world_asset_place_preview(); }
            return;
        }
        if self.world_paste_anchor.is_some() {
            if is_key_pressed(KeyCode::Right) { self.nudge_world_paste_preview(GridPos { x: 1, y: 0 }); }
            if is_key_pressed(KeyCode::Left) { self.nudge_world_paste_preview(GridPos { x: -1, y: 0 }); }
            if is_key_pressed(KeyCode::Down) { self.nudge_world_paste_preview(GridPos { x: 0, y: 1 }); }
            if is_key_pressed(KeyCode::Up) { self.nudge_world_paste_preview(GridPos { x: 0, y: -1 }); }
            if is_key_pressed(KeyCode::Enter) { self.commit_world_paste_preview(); }
        }
        if control_down && is_key_pressed(KeyCode::C) {
            self.copy_world_selection();
        }
        if control_down && is_key_pressed(KeyCode::V) {
            self.paste_world_selection();
        }
        if control_down && is_key_pressed(KeyCode::D) {
            self.duplicate_world_selection();
        }
        if control_down
            && (is_key_pressed(KeyCode::Y) || (shift_down && is_key_pressed(KeyCode::Z)))
        {
            self.redo_world_edit();
        } else if control_down && is_key_pressed(KeyCode::Z) {
            self.undo_world_edit();
        }
        if control_down {
            return;
        }

        if is_key_pressed(KeyCode::LeftBracket) {
            self.world_brush_radius = (self.world_brush_radius - 1).max(0);
            self.status_message = format!(
                "World brush {}x{}",
                self.world_brush_radius * 2 + 1,
                self.world_brush_radius * 2 + 1
            );
        }
        if is_key_pressed(KeyCode::RightBracket) {
            self.world_brush_radius = (self.world_brush_radius + 1).min(8);
            self.status_message = format!(
                "World brush {}x{}",
                self.world_brush_radius * 2 + 1,
                self.world_brush_radius * 2 + 1
            );
        }
        if self.world_layer_mode == WorldLayerMode::StructuralLevels {
            if is_key_pressed(KeyCode::Minus) {
                self.world_structural_level = haven_world::step_structural_authoring_level_v1(
                    self.world_structural_level,
                    -1,
                );
                self.status_message =
                    format!("Active structural level: {}", self.world_structural_level);
            }
            if is_key_pressed(KeyCode::Equal) {
                self.world_structural_level = haven_world::step_structural_authoring_level_v1(
                    self.world_structural_level,
                    1,
                );
                self.status_message =
                    format!("Active structural level: {}", self.world_structural_level);
            }
        }
        if is_key_pressed(KeyCode::Delete) || is_key_pressed(KeyCode::Backspace) {
            if self.world_layer_mode == WorldLayerMode::StructuralLevels {
                self.apply_world_structural_level_to_selection(
                    0,
                    "Carve selected platform to Level 0",
                );
            } else {
                let previous = self.world_edit_tool;
                self.world_edit_tool = WorldEditTool::Erase;
                self.apply_world_tool_at(GridPos {
                    x: self.world_cursor_x,
                    y: self.world_cursor_y,
                });
                self.world_edit_tool = previous;
            }
        }
    }
}

#[cfg(test)]
#[path = "world_surface_authoring_tests.rs"]
mod tests;
