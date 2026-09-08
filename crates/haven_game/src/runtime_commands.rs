use super::*;

impl Game {
    pub(super) fn push_undo_snapshot(&mut self) {
        let snapshot = self.world.serialize_lines();
        let command = self.describe_editor_command();
        self.command_bus
            .capture_undo_snapshot(command.clone(), snapshot);
        self.replication_sequence += 1;
        let envelope = replicate_editor_command(self.replication_sequence, &command);
        self.last_replication_status = envelope.status_line();
    }

    pub(super) fn sync_active_terrain_cache_now(&mut self) {
        self.terrain_cache.synchronize(self.world.active());
        self.terrain_cache_next_sync_at = macroquad::prelude::get_time() + 0.35;
    }

    pub(super) fn undo_world(&mut self) {
        let current = self.world.serialize_lines();
        match self.command_bus.undo(&current) {
            Ok(step) => match GameWorld::deserialize_lines(&step.snapshot) {
                Ok(world) => {
                    self.world = world;
                    self.set_player_to_active_spawn();
                    self.sync_active_terrain_cache_now();
                    self.status_message = format!(
                        "Undo applied: {} ({} left)",
                        step.label,
                        self.command_bus.undo_len()
                    );
                    self.log.event(&self.status_message);
                }
                Err(err) => {
                    self.status_message = format!("Undo failed: {err}");
                    self.log.event(&self.status_message);
                }
            },
            Err(message) => {
                self.status_message = message;
            }
        }
    }

    pub(super) fn redo_world(&mut self) {
        let current = self.world.serialize_lines();
        match self.command_bus.redo(&current) {
            Ok(step) => match GameWorld::deserialize_lines(&step.snapshot) {
                Ok(world) => {
                    self.world = world;
                    self.set_player_to_active_spawn();
                    self.sync_active_terrain_cache_now();
                    self.status_message = format!(
                        "Redo applied: {} ({} left)",
                        step.label,
                        self.command_bus.redo_len()
                    );
                    self.log.event(&self.status_message);
                }
                Err(err) => {
                    self.status_message = format!("Redo failed: {err}");
                    self.log.event(&self.status_message);
                }
            },
            Err(message) => {
                self.status_message = message;
            }
        }
    }

    pub(super) fn describe_editor_command(&self) -> EditorCommand {
        let kind = self.current_command_kind();
        let description = if self.status_message.trim().is_empty() {
            kind.label().to_string()
        } else {
            self.status_message.clone()
        };
        EditorCommand::new(
            kind,
            EditorCommandSource::InGameOverlay,
            "havenwild_starter",
            Some(self.world.active().id.code().to_string()),
            None,
            vec![GridPos {
                x: self.selected_cell.0,
                y: self.selected_cell.1,
            }],
            description,
        )
    }

    pub(super) fn current_command_kind(&self) -> EditorCommandKind {
        match self.editor_tab {
            EditorTab::Tiles => EditorCommandKind::PaintTerrain,
            EditorTab::Objects => {
                if self.selected_object_index.is_some() {
                    EditorCommandKind::EditObjectFootprint
                } else {
                    EditorCommandKind::PlaceObject
                }
            }
            EditorTab::Zones => EditorCommandKind::AssignRoom,
            EditorTab::Rules | EditorTab::Map => EditorCommandKind::SetHeight,
            EditorTab::World => match self.palette.tools[self.selected_tool] {
                BuildTool::Transition => EditorCommandKind::CreateTransition,
                _ => EditorCommandKind::SceneMutation,
            },
            EditorTab::Paint => EditorCommandKind::PaintTerrain,
            EditorTab::Transitions => EditorCommandKind::CreateTransition,
            EditorTab::Assets => EditorCommandKind::SceneMutation,
        }
    }

    pub(super) fn brush_min(&self, center: i32) -> i32 {
        (center - self.brush_size / 2).max(0)
    }

    pub(super) fn brush_max(&self, center: i32, limit: i32) -> i32 {
        (center + self.brush_size / 2).min(limit - 1)
    }
}
