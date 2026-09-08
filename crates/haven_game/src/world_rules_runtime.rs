use super::*;

impl Game {
    pub(super) fn handle_rules_tab_click(&mut self, mx: f32, my: f32, panel_x: f32) -> bool {
        for (i, tile) in TileKind::ALL.iter().enumerate() {
            let x = panel_x + 18.0 + (i % 2) as f32 * 168.0;
            let y = 108.0 + (i / 2) as f32 * 24.0;
            if mx >= x && mx <= x + 154.0 && my >= y - 16.0 && my <= y + 4.0 {
                self.selected_rule_tile = i;
                self.status_message = format!("Selected tile rule: {}", tile.label());
                return true;
            }
        }
        for (label, x, y) in [
            ("Prev", panel_x + 18.0, 478.0),
            ("Next", panel_x + 98.0, 478.0),
            ("Default", panel_x + 178.0, 478.0),
            ("Test", panel_x + 258.0, 478.0),
        ] {
            if mx >= x && mx <= x + 72.0 && my >= y && my <= y + 26.0 {
                match label {
                    "Prev" => self.cycle_selected_tile_rule(-1),
                    "Next" => self.cycle_selected_tile_rule(1),
                    "Default" => self.reset_selected_tile_rule(),
                    "Test" => self.interact_with_selected_cell(),
                    _ => {}
                }
                self.log.event(&self.status_message);
                return true;
            }
        }
        true
    }

    pub(super) fn handle_world_tab_click(&mut self, mx: f32, my: f32, panel_x: f32) -> bool {
        let panel_y = self.panel_rect(UiPanelId::Editor).y;
        for (i, scene_id) in SceneId::ALL.iter().enumerate() {
            let y = panel_y + 112.0 + i as f32 * 20.0;
            if mx >= panel_x + 18.0 && mx <= panel_x + 382.0 && my >= y - 15.0 && my <= y + 5.0 {
                self.jump_to_scene(*scene_id);
                return true;
            }
        }
        let transition_len = self.world.active().transitions.len();
        for i in 0..transition_len.min(6) {
            let y = panel_y + 112.0 + i as f32 * 20.0;
            if mx >= panel_x + 398.0 && mx <= panel_x + 628.0 && my >= y - 15.0 && my <= y + 5.0 {
                self.selected_transition_index = i;
                self.status_message = format!("Selected transition {}", i + 1);
                return true;
            }
        }

        for (label, x, y) in [
            ("Save", panel_x + 18.0, panel_y + 314.0),
            ("Load", panel_x + 98.0, panel_y + 314.0),
            ("Validate", panel_x + 178.0, panel_y + 314.0),
            ("Graph", panel_x + 278.0, panel_y + 314.0),
            ("Export", panel_x + 278.0, panel_y + 350.0),
            ("Regen", panel_x + 18.0, panel_y + 350.0),
            ("Reset", panel_x + 98.0, panel_y + 350.0),
            ("Spawn", panel_x + 178.0, panel_y + 350.0),
            ("Target", panel_x + 18.0, panel_y + 438.0),
            ("Size+", panel_x + 98.0, panel_y + 438.0),
            ("Size-", panel_x + 178.0, panel_y + 438.0),
            ("Dest", panel_x + 258.0, panel_y + 438.0),
            ("Delete", panel_x + 18.0, panel_y + 478.0),
            ("Clone", panel_x + 98.0, panel_y + 478.0),
        ] {
            if mx >= x && mx <= x + 72.0 && my >= y && my <= y + 26.0 {
                match label {
                    "Save" => self.save_map(),
                    "Load" => {
                        self.push_undo_snapshot();
                        self.load_map();
                    }
                    "Validate" => {
                        self.validation_messages = validate_world(&self.world);
                        self.status_message = if self.validation_messages.is_empty() {
                            "World validation passed".to_string()
                        } else {
                            format!(
                                "World validation: {} warning(s)",
                                self.validation_messages.len()
                            )
                        };
                    }
                    "Graph" => {
                        self.show_world_graph = !self.show_world_graph;
                        self.status_message = if self.show_world_graph {
                            "World graph enabled".to_string()
                        } else {
                            "World graph hidden".to_string()
                        };
                    }
                    "Export" => self.export_worldgen_json(),
                    "Regen" => {
                        self.push_undo_snapshot();
                        self.regenerate_active_scene();
                    }
                    "Reset" => {
                        self.push_undo_snapshot();
                        self.reset_active_scene();
                    }
                    "Spawn" => {
                        self.push_undo_snapshot();
                        let scene = self.world.active_mut();
                        scene.spawn_x = self.selected_cell.0;
                        scene.spawn_y = self.selected_cell.1;
                        self.status_message = format!(
                            "Set {} spawn to {}, {}",
                            scene.name, scene.spawn_x, scene.spawn_y
                        );
                    }
                    "Target" => self.edit_selected_transition(TransitionEdit::CycleTarget),
                    "Size+" => self.edit_selected_transition(TransitionEdit::Grow),
                    "Size-" => self.edit_selected_transition(TransitionEdit::Shrink),
                    "Dest" => self.edit_selected_transition(TransitionEdit::SetDestination),
                    "Delete" => self.edit_selected_transition(TransitionEdit::Delete),
                    "Clone" => {
                        self.push_undo_snapshot();
                        self.clone_active_scene_to_target();
                    }
                    _ => {}
                }
                self.log.event(&self.status_message);
                return true;
            }
        }
        true
    }

    pub(super) fn cycle_selected_tile_rule(&mut self, direction: i32) {
        let tile = TileKind::ALL[self.selected_rule_tile.min(TileKind::ALL.len() - 1)];
        let current = self.world.tile_rule(tile);
        let index = TileInteraction::ALL
            .iter()
            .position(|rule| *rule == current)
            .unwrap_or(0);
        let next =
            (index as i32 + direction).rem_euclid(TileInteraction::ALL.len() as i32) as usize;
        self.push_undo_snapshot();
        self.world.set_tile_rule(tile, TileInteraction::ALL[next]);
        self.status_message = format!(
            "{} interaction: {}",
            tile.label(),
            TileInteraction::ALL[next].label()
        );
    }

    pub(super) fn reset_selected_tile_rule(&mut self) {
        let tile = TileKind::ALL[self.selected_rule_tile.min(TileKind::ALL.len() - 1)];
        let default = default_interaction_for_tile(tile);
        self.push_undo_snapshot();
        self.world.set_tile_rule(tile, default);
        self.status_message = format!("{} interaction reset to {}", tile.label(), default.label());
    }

    pub(super) fn draw_rules_editor_tab(&self, panel_x: f32) {
        draw_text(
            "Tile Interaction Rules",
            panel_x + 18.0,
            104.0,
            17.0,
            Color::from_rgba(162, 228, 255, 255),
        );
        for (i, tile) in TileKind::ALL.iter().enumerate() {
            let x = panel_x + 18.0 + (i % 2) as f32 * 168.0;
            let y = 132.0 + (i / 2) as f32 * 24.0;
            let active = i == self.selected_rule_tile;
            if active {
                draw_rectangle(
                    x - 4.0,
                    y - 16.0,
                    154.0,
                    19.0,
                    Color::from_rgba(76, 101, 78, 190),
                );
            }
            draw_text(
                &format!("{}: {}", tile.label(), self.world.tile_rule(*tile).label()),
                x,
                y,
                13.0,
                if active {
                    Color::from_rgba(255, 232, 144, 255)
                } else {
                    Color::from_rgba(220, 231, 236, 255)
                },
            );
        }
        let tile = TileKind::ALL[self.selected_rule_tile.min(TileKind::ALL.len() - 1)];
        draw_text(
            &format!(
                "Selected {} -> {}",
                tile.label(),
                self.world.tile_rule(tile).label()
            ),
            panel_x + 18.0,
            458.0,
            15.0,
            Color::from_rgba(244, 238, 201, 255),
        );
        for (label, x, y) in [
            ("Prev", panel_x + 18.0, 478.0),
            ("Next", panel_x + 98.0, 478.0),
            ("Default", panel_x + 178.0, 478.0),
            ("Test", panel_x + 258.0, 478.0),
        ] {
            draw_editor_button(label, x, y, 72.0, 26.0);
        }
        draw_text(
            "F interacts with player tile | Test uses cursor cell",
            panel_x + 18.0,
            532.0,
            14.0,
            Color::from_rgba(208, 224, 232, 255),
        );
    }

    pub(super) fn draw_world_editor_tab(&self, panel_x: f32) {
        let panel_y = self.panel_rect(UiPanelId::Editor).y;
        draw_text(
            "Scenes",
            panel_x + 18.0,
            panel_y + 88.0,
            17.0,
            Color::from_rgba(162, 228, 255, 255),
        );
        for (i, scene_id) in SceneId::ALL.iter().enumerate() {
            let y = panel_y + 112.0 + i as f32 * 20.0;
            let Some(scene) = self.world.scene(*scene_id) else {
                continue;
            };
            let active = self.world.active_scene.legacy_scene_id() == Some(*scene_id);
            if active {
                draw_rectangle(
                    panel_x + 16.0,
                    y - 15.0,
                    366.0,
                    20.0,
                    Color::from_rgba(76, 101, 78, 190),
                );
            }
            draw_text(
                &format!(
                    "{}  {} link(s)  spawn {},{}",
                    scene.name,
                    scene.transitions.len(),
                    scene.spawn_x,
                    scene.spawn_y
                ),
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
            "Links",
            panel_x + 398.0,
            panel_y + 88.0,
            17.0,
            Color::from_rgba(162, 228, 255, 255),
        );
        for (i, transition) in self.world.active().transitions.iter().take(6).enumerate() {
            let y = panel_y + 112.0 + i as f32 * 20.0;
            let active = i
                == self
                    .selected_transition_index
                    .min(self.world.active().transitions.len().saturating_sub(1));
            if active {
                draw_rectangle(
                    panel_x + 396.0,
                    y - 15.0,
                    232.0,
                    20.0,
                    Color::from_rgba(76, 101, 78, 190),
                );
            }
            draw_text(
                &format!(
                    "{} {}x{}",
                    transition.target.label(),
                    transition.w,
                    transition.h
                ),
                panel_x + 402.0,
                y,
                16.0,
                if active {
                    Color::from_rgba(255, 232, 144, 255)
                } else {
                    Color::from_rgba(220, 231, 236, 255)
                },
            );
        }

        let active = self.world.active();
        draw_text(
            &format!(
                "Active: {} | {} transition(s)",
                active.name,
                active.transitions.len()
            ),
            panel_x + 18.0,
            panel_y + 298.0,
            15.0,
            Color::from_rgba(244, 238, 201, 255),
        );
        for (label, x, y) in [
            ("Save", panel_x + 18.0, panel_y + 314.0),
            ("Load", panel_x + 98.0, panel_y + 314.0),
            ("Validate", panel_x + 178.0, panel_y + 314.0),
            ("Graph", panel_x + 278.0, panel_y + 314.0),
            ("Export", panel_x + 278.0, panel_y + 350.0),
            ("Regen", panel_x + 18.0, panel_y + 350.0),
            ("Reset", panel_x + 98.0, panel_y + 350.0),
            ("Spawn", panel_x + 178.0, panel_y + 350.0),
        ] {
            draw_editor_button(label, x, y, 72.0, 26.0);
        }
        let selected = self
            .world
            .active()
            .transitions
            .get(self.selected_transition_index);
        let selected_text = selected.map_or("No transition selected".to_string(), |transition| {
            format!(
                "Selected link: {},{} {}x{} -> {} dest {},{}",
                transition.x,
                transition.y,
                transition.w,
                transition.h,
                transition.target.label(),
                transition.spawn_x,
                transition.spawn_y
            )
        });
        draw_text(
            &selected_text,
            panel_x + 18.0,
            panel_y + 418.0,
            16.0,
            Color::from_rgba(244, 238, 201, 255),
        );
        for (label, x, y) in [
            ("Target", panel_x + 18.0, panel_y + 438.0),
            ("Size+", panel_x + 98.0, panel_y + 438.0),
            ("Size-", panel_x + 178.0, panel_y + 438.0),
            ("Dest", panel_x + 258.0, panel_y + 438.0),
            ("Delete", panel_x + 18.0, panel_y + 478.0),
            ("Clone", panel_x + 98.0, panel_y + 478.0),
        ] {
            draw_editor_button(label, x, y, 72.0, 26.0);
        }
        draw_text(
            "Dest/Spawn use cursor cell | Clone copies active scene into [] target",
            panel_x + 18.0,
            panel_y + 526.0,
            14.0,
            Color::from_rgba(208, 224, 232, 255),
        );
    }
}
