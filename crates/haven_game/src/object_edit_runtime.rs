use super::*;

impl Game {
    pub(super) fn handle_objects_tab_click(&mut self, mx: f32, my: f32, panel_x: f32) -> bool {
        let visible_tools = self.visible_tool_indices();
        let start = self.tool_page * 10;
        let end = (start + 6).min(visible_tools.len());
        for (slot, visible_index) in (start..end).enumerate() {
            let tool_index = visible_tools[visible_index];
            let y = 122.0 + slot as f32 * 24.0;
            if mx >= panel_x + 18.0 && mx <= panel_x + 158.0 && my >= y - 16.0 && my <= y + 4.0 {
                self.selected_tool = tool_index;
                self.status_message = format!(
                    "Object placement tool: {}",
                    self.palette.tools[tool_index].label()
                );
                return true;
            }
        }

        let object_count = self.world.active().map.objects.len();
        let list_start = self.object_list_offset.min(object_count.saturating_sub(1));
        for list_slot in 0..8 {
            let index = list_start + list_slot;
            if index >= object_count {
                break;
            }
            let y = 126.0 + list_slot as f32 * 25.0;
            if mx >= panel_x + 174.0 && mx <= panel_x + 352.0 && my >= y - 16.0 && my <= y + 6.0 {
                self.select_object_index(index);
                return true;
            }
        }

        for (label, x, y, w) in [
            ("Pick", panel_x + 18.0, 286.0, 62.0),
            ("Focus", panel_x + 88.0, 286.0, 66.0),
            ("Prev", panel_x + 174.0, 286.0, 62.0),
            ("Next", panel_x + 244.0, 286.0, 62.0),
            ("Up", panel_x + 88.0, 318.0, 48.0),
            ("Left", panel_x + 34.0, 350.0, 48.0),
            ("Right", panel_x + 142.0, 350.0, 54.0),
            ("Down", panel_x + 88.0, 382.0, 58.0),
            ("Anchor", panel_x + 18.0, 430.0, 72.0),
            ("Delete", panel_x + 98.0, 430.0, 72.0),
        ] {
            if mx >= x && mx <= x + w && my >= y && my <= y + 26.0 {
                match label {
                    "Pick" => self.select_object_at_cursor(),
                    "Focus" => self.focus_selected_object(),
                    "Prev" => self.cycle_selected_object(-1),
                    "Next" => self.cycle_selected_object(1),
                    "Up" => self.move_selected_object(0, -1),
                    "Left" => self.move_selected_object(-1, 0),
                    "Right" => self.move_selected_object(1, 0),
                    "Down" => self.move_selected_object(0, 1),
                    "Anchor" => self.move_selected_object_to_cursor(),
                    "Delete" => self.delete_selected_object(),
                    _ => {}
                }
                self.log.event(&self.status_message);
                return true;
            }
        }

        for (target, x) in [
            (FootprintEditTarget::Visual, panel_x + 18.0),
            (FootprintEditTarget::Collision, panel_x + 104.0),
            (FootprintEditTarget::Interaction, panel_x + 202.0),
        ] {
            let w = if target == FootprintEditTarget::Interaction {
                108.0
            } else {
                82.0
            };
            if mx >= x && mx <= x + w && (506.0..=532.0).contains(&my) {
                self.footprint_edit_target = target;
                self.status_message = format!("Footprint edit target: {}", target.label());
                return true;
            }
        }

        for (label, x, y, w) in [
            ("X-", panel_x + 18.0, 546.0, 42.0),
            ("X+", panel_x + 66.0, 546.0, 42.0),
            ("Y-", panel_x + 116.0, 546.0, 42.0),
            ("Y+", panel_x + 164.0, 546.0, 42.0),
            ("W-", panel_x + 218.0, 546.0, 42.0),
            ("W+", panel_x + 266.0, 546.0, 42.0),
            ("H-", panel_x + 18.0, 580.0, 42.0),
            ("H+", panel_x + 66.0, 580.0, 42.0),
            ("Block", panel_x + 116.0, 580.0, 60.0),
            ("Occl", panel_x + 184.0, 580.0, 54.0),
            ("Fade", panel_x + 246.0, 580.0, 54.0),
            ("Reset", panel_x + 18.0, 624.0, 66.0),
            ("Default", panel_x + 92.0, 624.0, 76.0),
        ] {
            if mx >= x && mx <= x + w && my >= y && my <= y + 26.0 {
                match label {
                    "X-" => self.adjust_selected_object_footprint(-1, 0, 0, 0),
                    "X+" => self.adjust_selected_object_footprint(1, 0, 0, 0),
                    "Y-" => self.adjust_selected_object_footprint(0, -1, 0, 0),
                    "Y+" => self.adjust_selected_object_footprint(0, 1, 0, 0),
                    "W-" => self.adjust_selected_object_footprint(0, 0, -1, 0),
                    "W+" => self.adjust_selected_object_footprint(0, 0, 1, 0),
                    "H-" => self.adjust_selected_object_footprint(0, 0, 0, -1),
                    "H+" => self.adjust_selected_object_footprint(0, 0, 0, 1),
                    "Block" => self.toggle_selected_object_blocking(),
                    "Occl" => self.toggle_selected_object_occlusion(),
                    "Fade" => self.toggle_selected_object_fade(),
                    "Reset" => self.reset_selected_object_footprint_rect(),
                    "Default" => self.reset_selected_object_to_default_footprint(),
                    _ => {}
                }
                self.log.event(&self.status_message);
                return true;
            }
        }
        true
    }

    pub(super) fn clamp_selected_object(&mut self) -> Option<usize> {
        let len = self.world.active().map.objects.len();
        if len == 0 {
            self.selected_object_index = None;
            self.object_list_offset = 0;
            return None;
        }
        let index = self.selected_object_index.unwrap_or(0).min(len - 1);
        self.selected_object_index = Some(index);
        if index < self.object_list_offset {
            self.object_list_offset = index;
        }
        if index >= self.object_list_offset + 8 {
            self.object_list_offset = index.saturating_sub(7);
        }
        self.object_list_offset = self.object_list_offset.min(len.saturating_sub(1));
        Some(index)
    }

    pub(super) fn select_object_index(&mut self, index: usize) {
        let len = self.world.active().map.objects.len();
        if index >= len {
            self.selected_object_index = None;
            self.status_message = "No object at selected index".to_string();
            return;
        }
        self.selected_object_index = Some(index);
        self.clamp_selected_object();
        let object = self.world.active().map.objects[index];
        self.selected_cell = (object.x, object.y);
        self.inspector = inspect_scene_cell(self.world.active(), object.x, object.y);
        self.status_message = format!(
            "Selected object {}: {}",
            index + 1,
            object.placement_label()
        );
    }

    pub(super) fn select_object_at_cursor(&mut self) {
        let (x, y) = self.selected_cell;
        if let Some(index) = self.world.active().map.object_at(x, y) {
            self.select_object_index(index);
        } else {
            self.status_message = format!("No object under cursor {},{}", x, y);
        }
    }

    pub(super) fn cycle_selected_object(&mut self, direction: i32) {
        let len = self.world.active().map.objects.len();
        if len == 0 {
            self.selected_object_index = None;
            self.status_message = "Active scene has no objects".to_string();
            return;
        }
        let current = self.selected_object_index.unwrap_or(0).min(len - 1);
        let next = (current as i32 + direction).rem_euclid(len as i32) as usize;
        self.select_object_index(next);
    }

    pub(super) fn focus_selected_object(&mut self) {
        let Some(index) = self.clamp_selected_object() else {
            self.status_message = "No object selected".to_string();
            return;
        };
        let object = self.world.active().map.objects[index];
        self.selected_cell = (object.x, object.y);
        self.camera_target = vec2(
            object.x as f32 * TILE_SIZE + TILE_SIZE * 0.5,
            object.y as f32 * TILE_SIZE + TILE_SIZE * 0.5,
        );
        self.status_message = format!(
            "Focused {} at {},{}",
            object.kind.label(),
            object.x,
            object.y
        );
    }

    pub(super) fn handle_selected_object_hotkeys(&mut self) {
        if is_key_pressed(KeyCode::Delete) || is_key_pressed(KeyCode::Backspace) {
            self.delete_selected_object();
            return;
        }
        if is_key_pressed(KeyCode::Up) {
            self.move_selected_object(0, -1);
        }
        if is_key_pressed(KeyCode::Down) {
            self.move_selected_object(0, 1);
        }
        if is_key_pressed(KeyCode::Left) {
            self.move_selected_object(-1, 0);
        }
        if is_key_pressed(KeyCode::Right) {
            self.move_selected_object(1, 0);
        }
    }

    pub(super) fn move_selected_object_to_cursor(&mut self) {
        let (x, y) = self.selected_cell;
        self.move_selected_object_to(x, y);
    }

    pub(super) fn move_selected_object(&mut self, dx: i32, dy: i32) {
        let Some(index) = self.clamp_selected_object() else {
            self.status_message = "No object selected".to_string();
            return;
        };
        let object = self.world.active().map.objects[index];
        self.move_selected_object_to(object.x + dx, object.y + dy);
    }

    pub(super) fn move_selected_object_to(&mut self, x: i32, y: i32) {
        let Some(index) = self.clamp_selected_object() else {
            self.status_message = "No object selected".to_string();
            return;
        };
        let object = self.world.active().map.objects[index];
        let mut moved = object;
        let dimensions = self.world.active().dimensions;
        moved.x = x.clamp(0, dimensions.width as i32 - 1);
        moved.y = y.clamp(0, dimensions.height as i32 - 1);
        let issues = self
            .world
            .active()
            .map
            .placement_issues_for_object_excluding(moved, Some(index));
        if issues.is_empty() {
            self.push_undo_snapshot();
            let _ = self
                .world
                .active_mut()
                .map
                .move_object_to(index, moved.x, moved.y);
            self.selected_cell = (moved.x, moved.y);
            self.inspector = inspect_scene_cell(self.world.active(), moved.x, moved.y);
            self.status_message =
                format!("Moved {} to {},{}", moved.kind.label(), moved.x, moved.y);
        } else {
            let first_issue = issues
                .first()
                .map(|issue| issue.label())
                .unwrap_or_else(|| "unknown placement issue".to_string());
            self.status_message = format!("Cannot move {}: {}", object.kind.label(), first_issue);
        }
    }

    pub(super) fn adjust_selected_object_footprint(&mut self, dx: i32, dy: i32, dw: i32, dh: i32) {
        let Some(index) = self.clamp_selected_object() else {
            self.status_message = "No object selected".to_string();
            return;
        };
        let mut object = self.world.active().map.objects[index];
        match self.footprint_edit_target {
            FootprintEditTarget::Visual => {
                object.footprint.visual_offset_x += dx;
                object.footprint.visual_offset_y += dy;
                object.footprint.visual_w = (object.footprint.visual_w + dw).max(1);
                object.footprint.visual_h = (object.footprint.visual_h + dh).max(1);
            }
            FootprintEditTarget::Collision => {
                object.footprint.collision_offset_x += dx;
                object.footprint.collision_offset_y += dy;
                object.footprint.collision_w = (object.footprint.collision_w + dw).max(0);
                object.footprint.collision_h = (object.footprint.collision_h + dh).max(0);
            }
            FootprintEditTarget::Interaction => {
                object.footprint.interaction_offset_x += dx;
                object.footprint.interaction_offset_y += dy;
                object.footprint.interaction_w = (object.footprint.interaction_w + dw).max(0);
                object.footprint.interaction_h = (object.footprint.interaction_h + dh).max(0);
            }
        }
        self.apply_selected_object_candidate(index, object, "Edited footprint");
    }

    pub(super) fn toggle_selected_object_blocking(&mut self) {
        let Some(index) = self.clamp_selected_object() else {
            self.status_message = "No object selected".to_string();
            return;
        };
        let mut object = self.world.active().map.objects[index];
        object.footprint.blocks_movement = !object.footprint.blocks_movement;
        self.apply_selected_object_candidate(index, object, "Toggled collision blocking");
    }

    pub(super) fn toggle_selected_object_occlusion(&mut self) {
        let Some(index) = self.clamp_selected_object() else {
            self.status_message = "No object selected".to_string();
            return;
        };
        let mut object = self.world.active().map.objects[index];
        object.footprint.occludes_player = !object.footprint.occludes_player;
        if !object.footprint.occludes_player {
            object.footprint.fade_when_player_behind = false;
        }
        self.apply_selected_object_candidate(index, object, "Toggled player occlusion");
    }

    pub(super) fn toggle_selected_object_fade(&mut self) {
        let Some(index) = self.clamp_selected_object() else {
            self.status_message = "No object selected".to_string();
            return;
        };
        let mut object = self.world.active().map.objects[index];
        object.footprint.fade_when_player_behind = !object.footprint.fade_when_player_behind;
        if object.footprint.fade_when_player_behind {
            object.footprint.occludes_player = true;
        }
        self.apply_selected_object_candidate(index, object, "Toggled player-behind fade");
    }

    pub(super) fn reset_selected_object_footprint_rect(&mut self) {
        let Some(index) = self.clamp_selected_object() else {
            self.status_message = "No object selected".to_string();
            return;
        };
        let mut object = self.world.active().map.objects[index];
        let default = audited_object_footprint_for_cell(object.kind, object.x, object.y);
        match self.footprint_edit_target {
            FootprintEditTarget::Visual => {
                object.footprint.visual_offset_x = default.visual_offset_x;
                object.footprint.visual_offset_y = default.visual_offset_y;
                object.footprint.visual_w = default.visual_w;
                object.footprint.visual_h = default.visual_h;
            }
            FootprintEditTarget::Collision => {
                object.footprint.collision_offset_x = default.collision_offset_x;
                object.footprint.collision_offset_y = default.collision_offset_y;
                object.footprint.collision_w = default.collision_w;
                object.footprint.collision_h = default.collision_h;
                object.footprint.blocks_movement = default.blocks_movement;
            }
            FootprintEditTarget::Interaction => {
                object.footprint.interaction_offset_x = default.interaction_offset_x;
                object.footprint.interaction_offset_y = default.interaction_offset_y;
                object.footprint.interaction_w = default.interaction_w;
                object.footprint.interaction_h = default.interaction_h;
            }
        }
        self.apply_selected_object_candidate(index, object, "Reset footprint rect to default");
    }

    pub(super) fn reset_selected_object_to_default_footprint(&mut self) {
        let Some(index) = self.clamp_selected_object() else {
            self.status_message = "No object selected".to_string();
            return;
        };
        let mut object = self.world.active().map.objects[index];
        object.footprint = audited_object_footprint_for_cell(object.kind, object.x, object.y);
        self.apply_selected_object_candidate(index, object, "Reset full footprint to default");
    }

    pub(super) fn apply_selected_object_candidate(
        &mut self,
        index: usize,
        object: PlacedObject,
        action: &str,
    ) {
        let issues = self
            .world
            .active()
            .map
            .placement_issues_for_object_excluding(object, Some(index));
        if issues.is_empty() {
            self.push_undo_snapshot();
            if let Some(slot) = self.world.active_mut().map.objects.get_mut(index) {
                *slot = object;
            }
            self.selected_cell = (object.x, object.y);
            self.inspector = inspect_scene_cell(self.world.active(), object.x, object.y);
            self.status_message = format!(
                "{}: {} {}",
                action,
                self.footprint_edit_target.label(),
                object.footprint_label()
            );
        } else {
            let first_issue = issues
                .first()
                .map(|issue| issue.label())
                .unwrap_or_else(|| "unknown footprint issue".to_string());
            self.status_message = format!("Cannot edit footprint: {}", first_issue);
        }
    }

    pub(super) fn delete_selected_object(&mut self) {
        let Some(index) = self.clamp_selected_object() else {
            self.status_message = "No object selected".to_string();
            return;
        };
        self.push_undo_snapshot();
        let removed = self.world.active_mut().map.remove_object_index(index);
        self.selected_object_index = None;
        self.clamp_selected_object();
        self.status_message = removed.map_or_else(
            || "No object deleted".to_string(),
            |object| {
                format!(
                    "Deleted {} at {},{}",
                    object.kind.label(),
                    object.x,
                    object.y
                )
            },
        );
    }

    pub(super) fn draw_object_footprint_preview(&self, object: PlacedObject, valid: bool) {
        let base = if valid {
            Color::from_rgba(117, 236, 137, 205)
        } else {
            Color::from_rgba(255, 92, 92, 220)
        };
        self.draw_tile_rect_fill(
            object.visual_rect(),
            Color::new(base.r, base.g, base.b, 0.10),
        );
        self.draw_tile_rect_lines(
            object.visual_rect(),
            Color::from_rgba(120, 178, 255, 230),
            2.0,
        );
        self.draw_tile_rect_lines(object.collision_rect(), base, 3.0);
        self.draw_tile_rect_lines(
            object.interaction_rect(),
            Color::from_rgba(255, 225, 104, 230),
            2.0,
        );
    }

    pub(super) fn draw_tile_rect_fill(&self, rect: (i32, i32, i32, i32), color: Color) {
        let (x, y, w, h) = rect;
        if w <= 0 || h <= 0 {
            return;
        }
        let screen = self.world_to_screen(vec2(x as f32 * TILE_SIZE, y as f32 * TILE_SIZE));
        draw_rectangle(
            screen.x,
            screen.y,
            w as f32 * TILE_SIZE,
            h as f32 * TILE_SIZE,
            color,
        );
    }

    pub(super) fn draw_tile_rect_lines(
        &self,
        rect: (i32, i32, i32, i32),
        color: Color,
        thickness: f32,
    ) {
        let (x, y, w, h) = rect;
        if w <= 0 || h <= 0 {
            return;
        }
        let screen = self.world_to_screen(vec2(x as f32 * TILE_SIZE, y as f32 * TILE_SIZE));
        draw_rectangle_lines(
            screen.x + 1.0,
            screen.y + 1.0,
            w as f32 * TILE_SIZE - 2.0,
            h as f32 * TILE_SIZE - 2.0,
            thickness,
            color,
        );
    }

    pub(super) fn draw_objects_editor_tab(&self, panel_x: f32) {
        draw_text(
            "Object Tools",
            panel_x + 18.0,
            104.0,
            17.0,
            Color::from_rgba(162, 228, 255, 255),
        );
        let visible_tools = self.visible_tool_indices();
        let start = self.tool_page * 10;
        let end = (start + 6).min(visible_tools.len());
        for (slot, visible_index) in (start..end).enumerate() {
            let tool_index = visible_tools[visible_index];
            let tool = self.palette.tools[tool_index];
            let y = 122.0 + slot as f32 * 24.0;
            let active = tool_index == self.selected_tool;
            if active {
                draw_rectangle(
                    panel_x + 16.0,
                    y - 16.0,
                    142.0,
                    20.0,
                    Color::from_rgba(76, 101, 78, 190),
                );
            }
            draw_text(
                &format!("{} {}", (slot + 1) % 10, tool.label()),
                panel_x + 22.0,
                y,
                16.0,
                if active {
                    Color::from_rgba(255, 232, 144, 255)
                } else {
                    Color::from_rgba(220, 231, 236, 255)
                },
            );
        }

        draw_text(
            "Scene Objects",
            panel_x + 174.0,
            104.0,
            17.0,
            Color::from_rgba(162, 228, 255, 255),
        );
        let objects = &self.world.active().map.objects;
        let list_start = self.object_list_offset.min(objects.len().saturating_sub(1));
        for list_slot in 0..8 {
            let index = list_start + list_slot;
            if index >= objects.len() {
                break;
            }
            let object = objects[index];
            let y = 126.0 + list_slot as f32 * 25.0;
            let active = Some(index) == self.selected_object_index;
            if active {
                draw_rectangle(
                    panel_x + 172.0,
                    y - 16.0,
                    180.0,
                    22.0,
                    Color::from_rgba(76, 101, 78, 190),
                );
            }
            draw_text(
                &format!(
                    "{:02} {} {},{}",
                    index + 1,
                    object.kind.label(),
                    object.x,
                    object.y
                ),
                panel_x + 178.0,
                y,
                15.0,
                if active {
                    Color::from_rgba(255, 232, 144, 255)
                } else {
                    Color::from_rgba(220, 231, 236, 255)
                },
            );
        }

        draw_editor_button("Pick", panel_x + 18.0, 286.0, 62.0, 26.0);
        draw_editor_button("Focus", panel_x + 88.0, 286.0, 66.0, 26.0);
        draw_editor_button("Prev", panel_x + 174.0, 286.0, 62.0, 26.0);
        draw_editor_button("Next", panel_x + 244.0, 286.0, 62.0, 26.0);
        draw_text(
            &format!(
                "Page {}/{} | {} object(s)",
                self.tool_page + 1,
                self.max_tool_page() + 1,
                objects.len()
            ),
            panel_x + 18.0,
            278.0,
            16.0,
            Color::from_rgba(162, 228, 255, 255),
        );
        draw_editor_button("Up", panel_x + 88.0, 318.0, 48.0, 26.0);
        draw_editor_button("Left", panel_x + 34.0, 350.0, 48.0, 26.0);
        draw_editor_button("Right", panel_x + 142.0, 350.0, 54.0, 26.0);
        draw_editor_button("Down", panel_x + 88.0, 382.0, 58.0, 26.0);
        draw_editor_button("Anchor", panel_x + 18.0, 430.0, 72.0, 26.0);
        draw_editor_button("Delete", panel_x + 98.0, 430.0, 72.0, 26.0);

        let selected_text = self
            .selected_object_index
            .and_then(|index| objects.get(index))
            .map_or_else(
                || "Selected: none".to_string(),
                |object| format!("Selected: {}", object.placement_label()),
            );
        draw_text(
            &selected_text,
            panel_x + 18.0,
            474.0,
            15.0,
            Color::from_rgba(244, 238, 201, 255),
        );

        draw_text(
            &format!("Footprint Edit: {}", self.footprint_edit_target.label()),
            panel_x + 18.0,
            500.0,
            15.0,
            Color::from_rgba(162, 228, 255, 255),
        );
        for (target, x, w) in [
            (FootprintEditTarget::Visual, panel_x + 18.0, 82.0),
            (FootprintEditTarget::Collision, panel_x + 104.0, 82.0),
            (FootprintEditTarget::Interaction, panel_x + 202.0, 108.0),
        ] {
            if target == self.footprint_edit_target {
                draw_rectangle(
                    x - 2.0,
                    504.0,
                    w + 4.0,
                    30.0,
                    Color::from_rgba(76, 101, 78, 190),
                );
            }
            draw_editor_button(target.label(), x, 506.0, w, 26.0);
        }

        for (label, x, y, w) in [
            ("X-", panel_x + 18.0, 546.0, 42.0),
            ("X+", panel_x + 66.0, 546.0, 42.0),
            ("Y-", panel_x + 116.0, 546.0, 42.0),
            ("Y+", panel_x + 164.0, 546.0, 42.0),
            ("W-", panel_x + 218.0, 546.0, 42.0),
            ("W+", panel_x + 266.0, 546.0, 42.0),
            ("H-", panel_x + 18.0, 580.0, 42.0),
            ("H+", panel_x + 66.0, 580.0, 42.0),
            ("Block", panel_x + 116.0, 580.0, 60.0),
            ("Occl", panel_x + 184.0, 580.0, 54.0),
            ("Fade", panel_x + 246.0, 580.0, 54.0),
            ("Reset", panel_x + 18.0, 624.0, 66.0),
            ("Default", panel_x + 92.0, 624.0, 76.0),
        ] {
            draw_editor_button(label, x, y, w, 26.0);
        }

        draw_text(
            "Blue visual + collision and yellow interaction bounds follow the selected authored variant.",
            panel_x + 18.0,
            666.0,
            14.0,
            Color::from_rgba(208, 224, 232, 255),
        );
        draw_text(
            "Reset restores the manifest-backed footprint; X/Y/W/H remain explicit custom overrides.",
            panel_x + 18.0,
            686.0,
            14.0,
            Color::from_rgba(208, 224, 232, 255),
        );
    }
}
