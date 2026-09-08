use macroquad::prelude::*;

use haven_core::TILE_SIZE;

use crate::client_controls::ControlAction;
use super::Game;

impl Game {
    pub(super) fn update_station_placement_mode(&mut self) -> bool {
        let Some(station_id) = self
            .player_inventory_ui
            .pending_station_placement()
            .map(str::to_string)
        else {
            return false;
        };

        let (tile_x, tile_y) = self.station_placement_candidate();
        let valid = self.station_placement_is_valid(tile_x, tile_y);

        if self.controls.action_pressed(ControlAction::Cancel)
            || self.controls.action_pressed(ControlAction::SecondaryAction)
        {
            self.player_inventory_ui.cancel_pending_station_placement();
            self.status_message = "Station placement cancelled; kit returned".to_string();
            return true;
        }

        if self.controls.action_pressed(ControlAction::Confirm)
            || self.controls.action_pressed(ControlAction::PrimaryAction)
        {
            if valid {
                let world_x = (tile_x as f32 + 0.5) * TILE_SIZE;
                let world_y = (tile_y as f32 + 0.5) * TILE_SIZE;
                let scene_id = self.world.active().id.code().to_string();
                if self.player_inventory_ui.confirm_station_placement(
                    &station_id,
                    world_x,
                    world_y,
                    &scene_id,
                ) {
                    let _ = self.player_inventory_ui.save();
                    self.status_message = format!(
                        "Placed {} at {},{}",
                        station_label(&station_id),
                        tile_x,
                        tile_y
                    );
                }
            } else {
                self.status_message = format!("Cannot place {} here", station_label(&station_id));
            }
        }

        true
    }

    fn station_placement_candidate(&self) -> (i32, i32) {
        let mouse = vec2(mouse_position().0, mouse_position().1);
        let world = self.screen_to_world(mouse);
        let mut tile_x = (world.x / TILE_SIZE).floor() as i32;
        let mut tile_y = (world.y / TILE_SIZE).floor() as i32;
        let dimensions = self.world.active().dimensions;
        if !dimensions.contains(tile_x, tile_y) {
            let facing = self.player_facing_vec();
            tile_x = (self.player.x / TILE_SIZE).floor() as i32 + facing.x.round() as i32;
            tile_y = (self.player.y / TILE_SIZE).floor() as i32 + facing.y.round() as i32;
        }
        (
            tile_x.clamp(0, dimensions.width as i32 - 1),
            tile_y.clamp(0, dimensions.height as i32 - 1),
        )
    }

    fn station_placement_is_valid(&self, tile_x: i32, tile_y: i32) -> bool {
        if !self.world.active().is_cell_walkable(tile_x, tile_y) {
            return false;
        }
        let world_x = (tile_x as f32 + 0.5) * TILE_SIZE;
        let world_y = (tile_y as f32 + 0.5) * TILE_SIZE;
        let scene_id = self.world.active().id.code();
        !self
            .player_inventory_ui
            .placed_stations()
            .iter()
            .any(|station| {
                station.placement_confirmed
                    && station.scene_id == scene_id
                    && (station.world_x - world_x).abs() < TILE_SIZE * 0.75
                    && (station.world_y - world_y).abs() < TILE_SIZE * 0.75
            })
    }

    #[allow(dead_code)]
    pub(super) fn draw_station_placement_preview(&self) {
        let Some(station_id) = self.player_inventory_ui.pending_station_placement() else {
            return;
        };
        let (tile_x, tile_y) = self.station_placement_candidate();
        let valid = self.station_placement_is_valid(tile_x, tile_y);
        let screen =
            self.world_to_screen(vec2(tile_x as f32 * TILE_SIZE, tile_y as f32 * TILE_SIZE));
        let color = if valid {
            Color::from_rgba(105, 230, 132, 155)
        } else {
            Color::from_rgba(245, 92, 92, 170)
        };
        draw_rectangle(
            screen.x + 2.0,
            screen.y + 2.0,
            TILE_SIZE - 4.0,
            TILE_SIZE - 4.0,
            color,
        );
        draw_rectangle_lines(screen.x, screen.y, TILE_SIZE, TILE_SIZE, 3.0, WHITE);
        draw_station_symbol(
            station_id,
            screen + vec2(TILE_SIZE * 0.5, TILE_SIZE * 0.5),
            0.82,
        );
        draw_text(
            &format!(
                "{}/{} place · {}/{} cancel",
                self.controls.prompt_label(ControlAction::PrimaryAction),
                self.controls.prompt_label(ControlAction::Confirm),
                self.controls.prompt_label(ControlAction::SecondaryAction),
                self.controls.prompt_label(ControlAction::Cancel),
            ),
            18.0,
            screen_height() - 24.0,
            18.0,
            Color::from_rgba(255, 244, 207, 255),
        );
    }

    #[allow(dead_code)]
    pub(super) fn draw_placed_crafting_stations(&self) {
        let scene_id = self.world.active().id.code();
        for station in self.player_inventory_ui.placed_stations() {
            if !station.placement_confirmed || station.scene_id != scene_id {
                continue;
            }
            let screen = self.world_to_screen(vec2(station.world_x, station.world_y));
            draw_station_symbol(&station.station_id, screen, 1.0);
        }
    }
}

#[allow(dead_code)]
fn draw_station_symbol(station_id: &str, center: Vec2, scale: f32) {
    match station_id {
        "campfire" => {
            draw_circle(
                center.x,
                center.y + 6.0 * scale,
                12.0 * scale,
                Color::from_rgba(71, 55, 42, 255),
            );
            draw_triangle(
                center + vec2(-8.0, 6.0) * scale,
                center + vec2(0.0, -16.0) * scale,
                center + vec2(8.0, 6.0) * scale,
                Color::from_rgba(255, 146, 45, 255),
            );
        }
        "primitive_forge" => {
            draw_rectangle(
                center.x - 15.0 * scale,
                center.y - 12.0 * scale,
                30.0 * scale,
                24.0 * scale,
                Color::from_rgba(83, 79, 76, 255),
            );
            draw_rectangle(
                center.x - 8.0 * scale,
                center.y - 5.0 * scale,
                16.0 * scale,
                10.0 * scale,
                Color::from_rgba(240, 102, 42, 255),
            );
        }
        "tailor_bench" => {
            draw_rectangle(
                center.x - 17.0 * scale,
                center.y - 10.0 * scale,
                34.0 * scale,
                20.0 * scale,
                Color::from_rgba(104, 70, 91, 255),
            );
            draw_circle(
                center.x,
                center.y - 4.0 * scale,
                6.0 * scale,
                Color::from_rgba(221, 190, 132, 255),
            );
            draw_line(
                center.x - 10.0 * scale,
                center.y + 10.0 * scale,
                center.x - 10.0 * scale,
                center.y + 18.0 * scale,
                4.0 * scale,
                Color::from_rgba(68, 42, 26, 255),
            );
            draw_line(
                center.x + 10.0 * scale,
                center.y + 10.0 * scale,
                center.x + 10.0 * scale,
                center.y + 18.0 * scale,
                4.0 * scale,
                Color::from_rgba(68, 42, 26, 255),
            );
        }
        _ => {
            draw_rectangle(
                center.x - 17.0 * scale,
                center.y - 10.0 * scale,
                34.0 * scale,
                20.0 * scale,
                Color::from_rgba(113, 72, 40, 255),
            );
            draw_line(
                center.x - 12.0 * scale,
                center.y + 10.0 * scale,
                center.x - 12.0 * scale,
                center.y + 18.0 * scale,
                4.0 * scale,
                Color::from_rgba(68, 42, 26, 255),
            );
            draw_line(
                center.x + 12.0 * scale,
                center.y + 10.0 * scale,
                center.x + 12.0 * scale,
                center.y + 18.0 * scale,
                4.0 * scale,
                Color::from_rgba(68, 42, 26, 255),
            );
        }
    }
}

fn station_label(station_id: &str) -> &'static str {
    match station_id {
        "workbench" => "Workbench",
        "campfire" => "Campfire",
        "primitive_forge" => "Primitive Forge",
        "tailor_bench" => "Tailor Bench",
        _ => "Crafting Station",
    }
}
