pub mod character_runtime;

pub use character_runtime::{
    CharacterAnimationIntent, CharacterRuntimeState, RuntimeEntityIdentity, RuntimeEntityKind,
};

use haven_core::{SceneId, SceneReference, TILE_SIZE};
use macroquad::prelude::{vec2, Vec2};

pub const ARCHITECTURE_STATUS: &str =
    "Active simulation crate for extracted tavern-time and customer-flow logic; broader tavern, economy, staff, and farming loops will continue moving here.";

pub use haven_world::{GameWorld, SceneMap};

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Customer {
    pub pos: Vec2,
    pub target: Vec2,
    pub patience: f32,
    pub seated: bool,
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct CustomerUpdateResult {
    pub entered: bool,
    pub coin_delta: i32,
    pub reputation_delta: i32,
}

pub fn advance_day_clock(day_clock: &mut f32, dt: f32) {
    *day_clock = (*day_clock + dt * 0.06) % 24.0;
}

pub fn update_tavern_customers(
    customers: &mut Vec<Customer>,
    customer_timer: &mut f32,
    dt: f32,
    tavern_open: bool,
    active_scene: &SceneReference,
) -> CustomerUpdateResult {
    let mut result = CustomerUpdateResult::default();
    if tavern_open && active_scene.legacy_scene_id() == Some(SceneId::TavernInterior) {
        *customer_timer -= dt;
        if *customer_timer <= 0.0 && customers.len() < 8 {
            *customer_timer = 3.5;
            customers.push(Customer {
                pos: vec2(-2.0 * TILE_SIZE, 14.5 * TILE_SIZE),
                target: vec2(20.0 * TILE_SIZE, 12.5 * TILE_SIZE),
                patience: 100.0,
                seated: false,
            });
            result.entered = true;
        }
    }

    for customer in customers.iter_mut() {
        if !customer.seated {
            let delta = customer.target - customer.pos;
            if delta.length() < 6.0 {
                customer.seated = true;
                result.coin_delta += 2;
                result.reputation_delta += 1;
            } else {
                customer.pos += delta.normalize() * 80.0 * dt;
            }
        } else {
            customer.patience -= dt * 6.0;
        }
    }
    customers.retain(|customer| customer.patience > 0.0);
    result
}

pub fn customer_sort_y(customer: &Customer) -> f32 {
    customer.pos.y + 16.0
}

pub fn night_amount(hour: f32) -> f32 {
    let linear = if (7.5..=18.0).contains(&hour) {
        0.0
    } else if hour > 18.0 {
        ((hour - 18.0) / 4.0).clamp(0.0, 1.0)
    } else {
        ((7.5 - hour) / 3.5).clamp(0.0, 1.0)
    };
    linear * linear * (3.0 - 2.0 * linear)
}

pub fn clock_label(hour: f32) -> String {
    let whole = hour.floor() as i32;
    let minute = ((hour - whole as f32) * 60.0).round() as i32;
    format!("{:02}:{:02}", whole, minute)
}

#[cfg(test)]
mod lighting_tests {
    use super::night_amount;

    #[test]
    fn midnight_reaches_full_night() {
        assert_eq!(night_amount(0.0), 1.0);
        assert_eq!(night_amount(23.0), 1.0);
    }

    #[test]
    fn daytime_has_no_night_tint() {
        assert_eq!(night_amount(12.0), 0.0);
        assert_eq!(night_amount(18.0), 0.0);
    }

    #[test]
    fn dusk_and_dawn_transition_smoothly() {
        assert!(night_amount(20.0) > 0.45);
        assert!(night_amount(6.0) > 0.35);
        assert!(night_amount(19.0) < night_amount(21.0));
    }
}
