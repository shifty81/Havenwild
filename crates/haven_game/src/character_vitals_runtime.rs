use super::*;
use serde_json::{Map, Number, Value};

const DEFAULT_MAX_STAMINA: f32 = 100.0;
const SPRINT_DRAIN_PER_SECOND: f32 = 13.0;
const MOVING_RECOVERY_PER_SECOND: f32 = 1.25;
const STANDING_RECOVERY_PER_SECOND: f32 = 8.0;
const RESTED_RECOVERY_PER_SECOND: f32 = 12.0;
const LOW_STAMINA_THRESHOLD: f32 = 0.25;
const FATIGUE_LOSS_PER_SECOND: f32 = 0.08;
const MINIMUM_CAPACITY_RATIO: f32 = 0.70;

impl Game {
    /// Advances the persistent character-vitals state without duplicating its
    /// save-schema ownership in the client. Pass 166 used floating-point
    /// profile fields; the alias-aware document adapter keeps older profile
    /// spellings readable while the save crate remains authoritative.
    pub(super) fn update_character_vitals_runtime(&mut self, dt: f32) {
        if dt <= 0.0 || self.pause_menu_open {
            return;
        }
        let Ok(mut document) = serde_json::to_value(&self.character_vitals) else {
            return;
        };
        let Some(object) = document.as_object_mut() else {
            return;
        };

        let base_max = read_number(
            object,
            &["base_max_stamina", "stamina_base_max", "max_stamina"],
            DEFAULT_MAX_STAMINA,
        )
        .max(1.0);
        let mut fatigue_max = read_number(
            object,
            &[
                "fatigue_reduced_max_stamina",
                "fatigue_max_stamina",
                "stamina_fatigue_max",
            ],
            base_max,
        )
        .clamp(base_max * MINIMUM_CAPACITY_RATIO, base_max);
        let comfort_bonus = read_number(
            object,
            &["comfort_bonus_stamina", "stamina_comfort_bonus"],
            0.0,
        )
        .max(0.0);
        let effective_max = (fatigue_max + comfort_bonus).max(1.0);
        let mut stamina = read_number(
            object,
            &["current_stamina", "stamina", "stamina_current"],
            effective_max,
        )
        .clamp(0.0, effective_max);
        let mut rested_seconds = read_number(
            object,
            &[
                "rested_buff_seconds",
                "rested_seconds_remaining",
                "rested_duration_seconds",
            ],
            0.0,
        )
        .max(0.0);

        let sprinting = self.player_is_moving()
            && self.controls.action_down(ControlAction::Sprint)
            && stamina > 0.5;
        if sprinting {
            stamina = (stamina - SPRINT_DRAIN_PER_SECOND * dt).max(0.0);
            if stamina <= effective_max * LOW_STAMINA_THRESHOLD {
                fatigue_max = (fatigue_max - FATIGUE_LOSS_PER_SECOND * dt)
                    .max(base_max * MINIMUM_CAPACITY_RATIO);
            }
        } else {
            let recovery = if !self.player_is_moving() {
                if rested_seconds > 0.0 {
                    RESTED_RECOVERY_PER_SECOND
                } else if self.world.active().kind == SceneKind::Interior {
                    STANDING_RECOVERY_PER_SECOND + 2.0
                } else {
                    STANDING_RECOVERY_PER_SECOND
                }
            } else {
                MOVING_RECOVERY_PER_SECOND
            };
            stamina = (stamina + recovery * dt).min(fatigue_max + comfort_bonus);
        }

        if rested_seconds > 0.0 {
            rested_seconds = (rested_seconds - dt).max(0.0);
            fatigue_max = (fatigue_max + 0.22 * dt).min(base_max);
        }

        write_number(
            object,
            &["current_stamina", "stamina", "stamina_current"],
            stamina,
        );
        write_number(
            object,
            &[
                "fatigue_reduced_max_stamina",
                "fatigue_max_stamina",
                "stamina_fatigue_max",
            ],
            fatigue_max,
        );
        write_number(
            object,
            &[
                "rested_buff_seconds",
                "rested_seconds_remaining",
                "rested_duration_seconds",
            ],
            rested_seconds,
        );

        if let Ok(next) = serde_json::from_value(document) {
            self.character_vitals = next;
        }
    }

    pub(super) fn try_begin_character_rest(&mut self) {
        if self.player_is_moving() {
            self.status_message = "Stand still before resting".to_string();
            return;
        }
        if self.world.active().kind != SceneKind::Interior {
            self.status_message = "Rest requires a sheltered interior".to_string();
            return;
        }
        let Ok(mut document) = serde_json::to_value(&self.character_vitals) else {
            return;
        };
        let Some(object) = document.as_object_mut() else {
            return;
        };
        let comfort = read_number(
            object,
            &["shelter_comfort", "comfort", "rest_comfort"],
            0.35,
        )
        .clamp(0.0, 1.0);
        let duration = (300.0 + comfort * 600.0).min(900.0);
        write_number(
            object,
            &[
                "rested_buff_seconds",
                "rested_seconds_remaining",
                "rested_duration_seconds",
            ],
            duration,
        );
        if let Ok(next) = serde_json::from_value(document) {
            self.character_vitals = next;
            self.status_message = format!(
                "Rested buff {:.0} minutes (comfort {:.0}%)",
                duration / 60.0,
                comfort * 100.0
            );
            self.log.event(&self.status_message);
        }
    }

    pub(super) fn character_is_sprinting(&self) -> bool {
        self.controls.action_down(ControlAction::Sprint)
            && self.character_stamina_current() > 0.5
    }

    pub(super) fn character_stamina_current(&self) -> f32 {
        serde_json::to_value(&self.character_vitals)
            .ok()
            .and_then(|document| {
                document.as_object().map(|object| {
                    read_number(
                        object,
                        &["current_stamina", "stamina", "stamina_current"],
                        DEFAULT_MAX_STAMINA,
                    )
                })
            })
            .unwrap_or(DEFAULT_MAX_STAMINA)
    }

    pub(super) fn try_spend_character_stamina(&mut self, cost: f32) -> bool {
        let Ok(mut document) = serde_json::to_value(&self.character_vitals) else {
            return true;
        };
        let Some(object) = document.as_object_mut() else {
            return true;
        };
        let current = read_number(
            object,
            &["current_stamina", "stamina", "stamina_current"],
            DEFAULT_MAX_STAMINA,
        );
        if current + f32::EPSILON < cost {
            return false;
        }
        let next_stamina = (current - cost).max(0.0);
        write_number(
            object,
            &["current_stamina", "stamina", "stamina_current"],
            next_stamina,
        );
        let base_max = read_number(
            object,
            &["base_max_stamina", "stamina_base_max", "max_stamina"],
            DEFAULT_MAX_STAMINA,
        )
        .max(1.0);
        if cost > 0.0 && next_stamina <= base_max * LOW_STAMINA_THRESHOLD {
            let fatigue_max = read_number(
                object,
                &[
                    "fatigue_reduced_max_stamina",
                    "fatigue_max_stamina",
                    "stamina_fatigue_max",
                ],
                base_max,
            );
            write_number(
                object,
                &[
                    "fatigue_reduced_max_stamina",
                    "fatigue_max_stamina",
                    "stamina_fatigue_max",
                ],
                (fatigue_max - cost * 0.015).max(base_max * MINIMUM_CAPACITY_RATIO),
            );
        }
        if let Ok(next) = serde_json::from_value(document) {
            self.character_vitals = next;
        }
        true
    }
}

fn read_number(object: &Map<String, Value>, aliases: &[&str], fallback: f32) -> f32 {
    aliases
        .iter()
        .find_map(|key| object.get(*key).and_then(Value::as_f64))
        .map(|value| value as f32)
        .unwrap_or(fallback)
}

fn write_number(object: &mut Map<String, Value>, aliases: &[&str], value: f32) {
    let key = aliases
        .iter()
        .find(|key| object.contains_key(**key))
        .copied()
        .unwrap_or(aliases[0]);
    if let Some(number) = Number::from_f64(value as f64) {
        object.insert(key.to_string(), Value::Number(number));
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn alias_adapter_updates_existing_stamina_field() {
        let mut object = Map::new();
        object.insert("stamina".to_string(), Value::from(50.0));
        write_number(
            &mut object,
            &["current_stamina", "stamina", "stamina_current"],
            42.0,
        );
        assert_eq!(object.get("stamina").and_then(Value::as_f64), Some(42.0));
        assert!(!object.contains_key("current_stamina"));
    }
}
