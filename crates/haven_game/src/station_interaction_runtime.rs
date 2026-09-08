use macroquad::prelude::*;

use haven_core::TILE_SIZE;

use crate::client_controls::ControlAction;
use super::Game;

const STATION_INTERACTION_DISTANCE: f32 = TILE_SIZE * 1.75;

impl Game {
    pub(super) fn update_station_interaction(&mut self) -> bool {
        if !self.controls.action_pressed(ControlAction::Interact) {
            return false;
        }

        let scene_id = self.world.active().id.code();
        let Some((station_id, instance_id)) =
            self.nearest_station(scene_id, STATION_INTERACTION_DISTANCE)
        else {
            // No nearby station owns this Interact press; let normal world/tile
            // interaction consume the same semantic action later in the frame.
            return false;
        };

        if self
            .player_inventory_ui
            .open_station_instance(&station_id, &instance_id)
        {
            self.status_message = format!("Opened {}", station_label(&station_id));
        }
        true
    }

    #[allow(dead_code)]
    pub(super) fn draw_station_interaction_prompt(&self) {
        if self.player_inventory_ui.open
            || self
                .player_inventory_ui
                .pending_station_placement()
                .is_some()
        {
            return;
        }
        let scene_id = self.world.active().id.code();
        let Some((station_id, _instance_id)) =
            self.nearest_station(scene_id, STATION_INTERACTION_DISTANCE)
        else {
            return;
        };

        let label = format!(
            "{}  Use {}",
            self.controls.prompt_label(ControlAction::Interact),
            station_label(&station_id)
        );
        let metrics = measure_text(&label, None, 20, 1.0);
        let width = metrics.width + 34.0;
        let x = (screen_width() - width) * 0.5;
        let y = screen_height() - 92.0;
        draw_rectangle(x, y, width, 38.0, Color::from_rgba(26, 23, 18, 232));
        draw_rectangle_lines(x, y, width, 38.0, 2.0, Color::from_rgba(208, 169, 91, 255));
        draw_text(
            &label,
            x + 17.0,
            y + 26.0,
            20.0,
            Color::from_rgba(247, 230, 183, 255),
        );
    }

    fn nearest_station(&self, scene_id: &str, maximum_distance: f32) -> Option<(String, String)> {
        let maximum_distance_squared = maximum_distance * maximum_distance;
        self.player_inventory_ui
            .placed_stations()
            .iter()
            .filter(|station| station.placement_confirmed && station.scene_id == scene_id)
            .filter_map(|station| {
                let dx = station.world_x - self.player.x;
                let dy = station.world_y - self.player.y;
                let distance_squared = dx * dx + dy * dy;
                (distance_squared <= maximum_distance_squared).then_some((
                    distance_squared,
                    station.station_id.clone(),
                    station.instance_id.clone(),
                ))
            })
            .min_by(|left, right| left.0.total_cmp(&right.0))
            .map(|(_, station_id, instance_id)| (station_id, instance_id))
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
