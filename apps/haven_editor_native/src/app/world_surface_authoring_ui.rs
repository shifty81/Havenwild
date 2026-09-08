use super::render_helpers::*;
use super::*;

fn selection_action_rect_from(rect: Rect, index: usize, top: f32) -> Rect {
    let gap = 6.0;
    let width = ((rect.w - gap) * 0.5).max(82.0);
    Rect::new(
        rect.x + (index % 2) as f32 * (width + gap),
        rect.y + top + (index / 2) as f32 * 36.0,
        width,
        30.0,
    )
}

fn connector_apply_rect(rect: Rect) -> Rect {
    Rect::new(rect.x, rect.y + 134.0, rect.w, 30.0)
}

impl EditorApp {
    /// W63 canonical World Properties surface. Asset browsing is owned by the
    /// shared right-dock Assets tab, so Properties concentrates on the current
    /// semantic selection or the world build controls.
    pub(crate) fn draw_world_properties(&self, rect: Rect) {
        if self.world_selection.is_some() {
            self.draw_world_selection_inspector(rect);
        } else {
            self.draw_world_surface_build_inspector(rect);
        }
    }

    pub(crate) fn handle_world_properties_click(&mut self, mx: f32, my: f32, rect: Rect) -> bool {
        if self.world_selection.is_some() {
            self.handle_world_selection_inspector_click(mx, my, rect)
        } else {
            self.handle_world_surface_build_inspector_click(mx, my, rect)
        }
    }

    fn draw_world_selection_inspector(&self, rect: Rect) {
        draw_section_header(
            Rect::new(rect.x, rect.y, rect.w, 24.0),
            "Region Tool",
            Some("author, refine, test"),
        );
        let Some(selection) = self.world_selection else {
            draw_editor_text(
                "No world region selected",
                rect.x,
                rect.y + 54.0,
                20.0,
                MUTED,
            );
            draw_wrapped(
                "Choose Select, drag a rectangle on the World Editor, then return here. Region actions stay semantic and cross storage-partition boundaries.",
                rect.x,
                rect.y + 82.0,
                rect.w,
                14.0,
                TEXT,
            );
            return;
        };
        draw_editor_text(
            &format!(
                "{}x{} tiles | {},{} → {},{}",
                selection.width(),
                selection.height(),
                selection.min.x,
                selection.min.y,
                selection.max.x,
                selection.max.y
            ),
            rect.x,
            rect.y + 54.0,
            17.0,
            TEXT,
        );
        draw_wrapped(
            "The selected region remains the authoring target for clipboard, Pixel Studio, PCG exemplar capture, framing, and Play Here.",
            rect.x,
            rect.y + 80.0,
            rect.w,
            14.0,
            MUTED,
        );
        let connector_kind = self.active_world_structural_connector_kind();
        let action_top = if let Some(kind) = connector_kind {
            let preview = self.world_structural_connector_preview();
            let (label, detail, enabled) = match preview {
                Ok(plan) => (
                    format!("Apply {}", kind.label()),
                    format!("Preview: {}", plan.summary()),
                    true,
                ),
                Err(error) => (
                    format!("Apply {}", kind.label()),
                    format!("No valid host: {error}"),
                    false,
                ),
            };
            draw_scissored_text(&detail, rect.x, rect.y + 112.0, rect.w, 12.5, if enabled { GOOD } else { WARN });
            draw_editor_widget(connector_apply_rect(rect), &label, false);
            176.0
        } else {
            134.0
        };
        for (index, label) in [
            "Copy",
            "Duplicate",
            "Pixel Edit",
            "Promote PCG",
            "Play Here",
            "Frame Sel",
            "Open Partition",
            "Clear Selection",
        ]
        .into_iter()
        .enumerate()
        {
            draw_editor_widget(selection_action_rect_from(rect, index, action_top), label, false);
        }
        draw_wrapped(
            if connector_kind.is_some() {
                "Connector placement resolves the nearest certified host intersecting this selection, previews the complete footprint on-canvas, revalidates it at commit, and records one undoable transaction."
            } else {
                "Typical flow: select → duplicate or pixel-edit → save → Play Here. Promote PCG only after the authored region is a good example of the design language you want world generation to reuse."
            },
            rect.x,
            rect.y + if connector_kind.is_some() { 334.0 } else { 292.0 },
            rect.w,
            14.0,
            TEXT,
        );
    }

    fn world_selection_center(&self) -> Option<GridPos> {
        let selection = self.world_selection?;
        Some(GridPos {
            x: selection.min.x + (selection.width().saturating_sub(1) / 2),
            y: selection.min.y + (selection.height().saturating_sub(1) / 2),
        })
    }

    fn frame_world_selection(&mut self) {
        let Some(selection) = self.world_selection else {
            self.status_message = "Select a world region before framing it".to_string();
            return;
        };
        let Some(bounds) = self.world_canvas_bounds() else {
            self.status_message = "World surface bounds are unavailable".to_string();
            return;
        };
        let viewport = self.world_canvas_viewport_rect();
        let target = Rect::new(
            selection.min.x as f32,
            selection.min.y as f32,
            selection.width().max(1) as f32,
            selection.height().max(1) as f32,
        );
        self.world_canvas.frame_rect(viewport, bounds, target);
        self.status_message = format!(
            "Framed selected world region {}x{}",
            selection.width(),
            selection.height()
        );
    }

    fn handle_world_selection_inspector_click(
        &mut self,
        mx: f32,
        my: f32,
        rect: Rect,
    ) -> bool {
        let mouse = vec2(mx, my);
        if !rect.contains(mouse) {
            return false;
        }
        if self.world_selection.is_none() {
            return true;
        }
        let connector_kind = self.active_world_structural_connector_kind();
        if connector_kind.is_some() && connector_apply_rect(rect).contains(mouse) {
            self.apply_world_structural_connector_selection();
            return true;
        }
        let action_top = if connector_kind.is_some() { 176.0 } else { 134.0 };
        for index in 0..8 {
            if !selection_action_rect_from(rect, index, action_top).contains(mouse) {
                continue;
            }
            match index {
                0 => self.copy_world_selection(),
                1 => self.duplicate_world_selection(),
                2 => self.open_world_selection_in_pixel_studio(),
                3 => self.promote_world_selection_to_pcg_exemplar(),
                4 => {
                    if let Some(center) = self.world_selection_center() {
                        self.world_cursor_x = center.x;
                        self.world_cursor_y = center.y;
                    }
                    self.play_development_world(true);
                }
                5 => self.frame_world_selection(),
                6 => {
                    if let Some(center) = self.world_selection_center() {
                        self.world_cursor_x = center.x;
                        self.world_cursor_y = center.y;
                    }
                    self.open_assigned_rectangle_scene();
                }
                7 => {
                    self.world_selection = None;
                    self.status_message = "World region selection cleared".to_string();
                }
                _ => {}
            }
            return true;
        }
        true
    }

    fn draw_world_surface_build_inspector(&self, rect: Rect) {
        let cursor = GridPos { x: self.world_cursor_x, y: self.world_cursor_y };
        let address = self.scene_rectangles.as_ref().and_then(|manifest| {
            resolve_world_surface_cell(
                manifest,
                &self.scene_assignments,
                &self.model.world,
                self.selected_landmass_id,
                cursor,
            ).ok()
        });
        let scene = address.as_ref().and_then(|address| self.model.world.scene_by_id(&address.scene_id));
        let terrain = address.as_ref().zip(scene)
            .map(|(address, scene)| scene.map.get(address.local.x, address.local.y).label())
            .unwrap_or("Unavailable");
        let structural = address.as_ref().zip(scene)
            .and_then(|(address, scene)| scene.map.get_structural_level(address.local.x, address.local.y))
            .map(|level| format!("Level {level}"))
            .unwrap_or_else(|| "Auto / legacy".to_string());
        let zone = address.as_ref().zip(scene)
            .map(|(address, scene)| scene.zone_at(address.local.x, address.local.y).label())
            .unwrap_or("None");
        let partition = address.as_ref().map(|address| address.rectangle_id.as_str()).unwrap_or("outside assigned surface");

        draw_section_header(Rect::new(rect.x, rect.y, rect.w, 24.0), "World Inspector", Some("selection + provenance"));
        draw_editor_text("Havenwild Development World", rect.x, rect.y + 52.0, 19.0, TEXT);
        for (index, line) in [
            format!("Global: {}, {}", cursor.x, cursor.y),
            format!("Partition: {partition}"),
            format!("Terrain: {terrain}"),
            format!("Elevation: {structural}"),
            format!("Zone: {zone}"),
        ].into_iter().enumerate() {
            draw_scissored_text(&line, rect.x, rect.y + 80.0 + index as f32 * 20.0, rect.w, 13.5, if index < 2 { MUTED } else { TEXT });
        }

        draw_section_header(Rect::new(rect.x, rect.y + 194.0, rect.w, 24.0), "Canvas Authoring", Some("single authority"));
        for (index, line) in [
            format!("Layer: {}", self.active_canvas_layer_kind().map(super::brush_authoring::layer_short_label).unwrap_or("Canvas")),
            format!("Tool: {}", self.canvas_active_tool.label()),
            format!("Brush: {}", self.canvas_authoring_context.brush_mode.label()),
            format!("Source: {}", self.canvas_authoring_context.compact_source_label()),
        ].into_iter().enumerate() {
            draw_scissored_text(&line, rect.x, rect.y + 230.0 + index as f32 * 20.0, rect.w, 13.5, TEXT);
        }
        draw_wrapped(
            "World painting is owned by the left Tool Rail, text Layers, and bottom Tool Shelf Palette. The full Project Asset Browser stays in the Assets dock. Select a world region to expose region-level actions here.",
            rect.x, rect.y + 324.0, rect.w, 13.0, MUTED,
        );
    }

    fn handle_world_surface_build_inspector_click(
        &mut self,
        mx: f32,
        my: f32,
        rect: Rect,
    ) -> bool {
        // H21-A9: the Properties dock is inspection-only when no region is
        // selected. Mutating layer/tool/brush controls are owned exclusively
        // by the canvas Tool Rail + text Layers + Tool Shelf Palette.
        rect.contains(vec2(mx, my))
    }

    pub(crate) fn world_active_brush_label(&self) -> String {
        match self.world_layer_mode {
            WorldLayerMode::Terrain => self.selected_tile_kind().label().to_string(),
            WorldLayerMode::Objects => self
                .selected_stamp_id
                .as_deref()
                .and_then(|id| self.stamp_registry.entry(id))
                .map(|entry| entry.label.clone())
                .or_else(|| {
                    self.selected_placeable_id
                        .as_deref()
                        .and_then(|id| self.placeable_registry.entry(id))
                        .map(|entry| entry.label.clone())
                })
                .unwrap_or_else(|| self.selected_object_kind().label().to_string()),
            WorldLayerMode::Zones => self.selected_zone_kind().label().to_string(),
            WorldLayerMode::StructuralLevels => self
                .active_world_structural_connector_kind()
                .map(|kind| kind.label().to_string())
                .unwrap_or_else(|| format!("Level {}", self.world_structural_level)),
        }
    }

    fn cycle_world_brush(&mut self, direction: i32) {
        match self.world_layer_mode {
            WorldLayerMode::Terrain => {
                let palette = TileKind::LPC_MAPPED_EDITOR_TERRAIN;
                let current = palette
                    .iter()
                    .position(|candidate| *candidate == self.selected_tile_kind())
                    .unwrap_or(0);
                let next = wrap_index(current, palette.len(), direction);
                if let Some(index) = TileKind::ALL
                    .iter()
                    .position(|candidate| *candidate == palette[next])
                {
                    self.selected_tile = index;
                }
            }
            WorldLayerMode::Objects => {
                self.selected_stamp_id = None;
                self.selected_placeable_id = None;
                self.selected_object =
                    wrap_index(self.selected_object, OBJECT_BRUSHES.len(), direction);
            }
            WorldLayerMode::Zones => {
                self.selected_zone = wrap_index(self.selected_zone, ZONE_BRUSHES.len(), direction);
            }
            WorldLayerMode::StructuralLevels => {
                self.world_structural_level = haven_world::step_structural_authoring_level_v1(
                    self.world_structural_level,
                    if direction < 0 { -1 } else { 1 },
                );
            }
        }
        self.status_message = format!("World brush: {}", self.world_active_brush_label());
    }

    fn adjust_world_brush_radius(&mut self, direction: i32) {
        self.world_brush_radius = (self.world_brush_radius + direction).clamp(0, 8);
        self.status_message = format!(
            "World brush {}x{}",
            self.world_brush_radius * 2 + 1,
            self.world_brush_radius * 2 + 1
        );
    }
}

fn wrap_index(current: usize, len: usize, direction: i32) -> usize {
    if len == 0 {
        return 0;
    }
    if direction < 0 {
        (current + len - 1) % len
    } else {
        (current + 1) % len
    }
}
