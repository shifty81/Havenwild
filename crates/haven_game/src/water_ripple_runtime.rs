use std::collections::VecDeque;

use haven_core::{TileKind, TILE_SIZE};
use haven_world::water_surface::WaterRippleEvent;
use macroquad::prelude::Vec2;

const MAX_RIPPLES: usize = 32;
const STEP_RIPPLE_INTERVAL: f64 = 0.18;

#[derive(Default)]
pub(crate) struct WaterRippleRuntime {
    events: VecDeque<WaterRippleEvent>,
    next_player_ripple_at: f64,
}

impl WaterRippleRuntime {
    pub(crate) fn update_player(&mut self, player: Vec2, moving: bool, tile: TileKind, now: f64) {
        self.events.retain(|event| event.is_alive(now as f32));
        if !moving || !tile.is_water() || now < self.next_player_ripple_at {
            return;
        }
        self.push(WaterRippleEvent {
            world_x: player.x,
            world_y: player.y,
            radius: TILE_SIZE * 0.72,
            strength: 0.72,
            started_at: now as f32,
        });
        self.next_player_ripple_at = now + STEP_RIPPLE_INTERVAL;
    }

    pub(crate) fn push(&mut self, event: WaterRippleEvent) {
        while self.events.len() >= MAX_RIPPLES {
            self.events.pop_front();
        }
        self.events.push_back(event);
    }

    #[allow(dead_code)]
    pub(crate) fn active_count(&self) -> usize {
        self.events.len()
    }
}
