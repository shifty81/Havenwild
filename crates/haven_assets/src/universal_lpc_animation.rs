use serde::{Deserialize, Serialize};

pub const ULPC_SOURCE_FRAME_SIZE: [u32; 2] = [64, 64];
pub const HAVENWILD_CHARACTER_FRAME_SIZE: [u32; 2] = [64, 96];
pub const ULPC_DIRECTION_ORDER: [&str; 4] = ["north", "west", "south", "east"];

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum UniversalLpcBodyType {
    Male,
    Female,
    Teen,
    Child,
    Muscular,
    Pregnant,
}

impl UniversalLpcBodyType {
    pub const ALL: [Self; 6] = [
        Self::Male,
        Self::Female,
        Self::Teen,
        Self::Child,
        Self::Muscular,
        Self::Pregnant,
    ];

    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Male => "male",
            Self::Female => "female",
            Self::Teen => "teen",
            Self::Child => "child",
            Self::Muscular => "muscular",
            Self::Pregnant => "pregnant",
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct UniversalLpcAnimationSpec {
    pub id: &'static str,
    pub source_row: usize,
    pub direction_rows: usize,
    pub cycle: &'static [usize],
    pub exported: bool,
    pub gameplay_contact_cycle_index: Option<usize>,
}

const SPELLCAST: &[usize] = &[0, 1, 2, 3, 4, 5, 6];
const THRUST: &[usize] = &[0, 1, 2, 3, 4, 5, 6, 7];
const WALK: &[usize] = &[1, 2, 3, 4, 5, 6, 7, 8];
const SLASH: &[usize] = &[0, 1, 2, 3, 4, 5];
const SHOOT: &[usize] = &[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
const HURT: &[usize] = &[0, 1, 2, 3, 4, 5];
const CLIMB: &[usize] = &[0, 1, 2, 3, 4, 5];
const IDLE: &[usize] = &[0, 0, 1];
const JUMP: &[usize] = &[0, 1, 2, 3, 4, 1];
const SIT: &[usize] = &[0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2];
const EMOTE: &[usize] = SIT;
const RUN: &[usize] = &[0, 1, 2, 3, 4, 5, 6, 7];
const WATERING: &[usize] = &[0, 1, 4, 4, 4, 4, 5];
const COMBAT: &[usize] = &[0, 0, 1];
const ONE_HAND_SLASH: &[usize] = &[0, 1, 2, 3, 4, 5, 6];
const ONE_HAND_BACKSLASH: &[usize] = &[0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12];
const ONE_HAND_HALFSLASH: &[usize] = &[0, 1, 2, 3, 4, 5];

pub const ULPC_ANIMATIONS: [UniversalLpcAnimationSpec; 17] = [
    UniversalLpcAnimationSpec { id: "spellcast", source_row: 0, direction_rows: 4, cycle: SPELLCAST, exported: true, gameplay_contact_cycle_index: Some(4) },
    UniversalLpcAnimationSpec { id: "thrust", source_row: 4, direction_rows: 4, cycle: THRUST, exported: true, gameplay_contact_cycle_index: Some(5) },
    UniversalLpcAnimationSpec { id: "walk", source_row: 8, direction_rows: 4, cycle: WALK, exported: true, gameplay_contact_cycle_index: None },
    UniversalLpcAnimationSpec { id: "slash", source_row: 12, direction_rows: 4, cycle: SLASH, exported: true, gameplay_contact_cycle_index: Some(3) },
    UniversalLpcAnimationSpec { id: "shoot", source_row: 16, direction_rows: 4, cycle: SHOOT, exported: true, gameplay_contact_cycle_index: Some(7) },
    UniversalLpcAnimationSpec { id: "hurt", source_row: 20, direction_rows: 1, cycle: HURT, exported: true, gameplay_contact_cycle_index: None },
    UniversalLpcAnimationSpec { id: "climb", source_row: 21, direction_rows: 1, cycle: CLIMB, exported: true, gameplay_contact_cycle_index: None },
    UniversalLpcAnimationSpec { id: "idle", source_row: 22, direction_rows: 4, cycle: IDLE, exported: true, gameplay_contact_cycle_index: None },
    UniversalLpcAnimationSpec { id: "jump", source_row: 26, direction_rows: 4, cycle: JUMP, exported: true, gameplay_contact_cycle_index: None },
    UniversalLpcAnimationSpec { id: "sit", source_row: 30, direction_rows: 4, cycle: SIT, exported: true, gameplay_contact_cycle_index: None },
    UniversalLpcAnimationSpec { id: "emote", source_row: 34, direction_rows: 4, cycle: EMOTE, exported: true, gameplay_contact_cycle_index: None },
    UniversalLpcAnimationSpec { id: "run", source_row: 38, direction_rows: 4, cycle: RUN, exported: true, gameplay_contact_cycle_index: None },
    UniversalLpcAnimationSpec { id: "watering", source_row: 4, direction_rows: 4, cycle: WATERING, exported: false, gameplay_contact_cycle_index: Some(3) },
    UniversalLpcAnimationSpec { id: "combat", source_row: 42, direction_rows: 4, cycle: COMBAT, exported: true, gameplay_contact_cycle_index: None },
    UniversalLpcAnimationSpec { id: "1h_slash", source_row: 46, direction_rows: 4, cycle: ONE_HAND_SLASH, exported: false, gameplay_contact_cycle_index: Some(4) },
    UniversalLpcAnimationSpec { id: "1h_backslash", source_row: 46, direction_rows: 4, cycle: ONE_HAND_BACKSLASH, exported: true, gameplay_contact_cycle_index: Some(5) },
    UniversalLpcAnimationSpec { id: "1h_halfslash", source_row: 50, direction_rows: 4, cycle: ONE_HAND_HALFSLASH, exported: true, gameplay_contact_cycle_index: Some(3) },
];

pub fn animation_spec(id: &str) -> Option<&'static UniversalLpcAnimationSpec> {
    ULPC_ANIMATIONS.iter().find(|spec| spec.id == id)
}

pub fn frame_for_progress(animation: &str, progress: f32) -> usize {
    let Some(spec) = animation_spec(animation) else { return 0; };
    if spec.cycle.is_empty() { return 0; }
    let clamped = progress.clamp(0.0, 0.999_999);
    let index = (clamped * spec.cycle.len() as f32).floor() as usize;
    spec.cycle[index.min(spec.cycle.len() - 1)]
}

pub fn contact_progress(animation: &str) -> Option<f32> {
    let spec = animation_spec(animation)?;
    let index = spec.gameplay_contact_cycle_index?;
    if spec.cycle.is_empty() { return None; }
    Some((index as f32 + 0.5) / spec.cycle.len() as f32)
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct UniversalLpcCustomAnimationSpec {
    pub id: &'static str,
    pub frame_size: u32,
    pub source_single_animation: bool,
}

pub const ULPC_CUSTOM_ANIMATIONS: [UniversalLpcCustomAnimationSpec; 13] = [
    UniversalLpcCustomAnimationSpec { id: "wheelchair", frame_size: 64, source_single_animation: false },
    UniversalLpcCustomAnimationSpec { id: "tool_rod", frame_size: 128, source_single_animation: false },
    UniversalLpcCustomAnimationSpec { id: "slash_128", frame_size: 128, source_single_animation: false },
    UniversalLpcCustomAnimationSpec { id: "backslash_128", frame_size: 128, source_single_animation: false },
    UniversalLpcCustomAnimationSpec { id: "halfslash_128", frame_size: 128, source_single_animation: false },
    UniversalLpcCustomAnimationSpec { id: "walk_128", frame_size: 128, source_single_animation: false },
    UniversalLpcCustomAnimationSpec { id: "thrust_128", frame_size: 128, source_single_animation: false },
    UniversalLpcCustomAnimationSpec { id: "thrust_oversize", frame_size: 192, source_single_animation: false },
    UniversalLpcCustomAnimationSpec { id: "slash_oversize", frame_size: 192, source_single_animation: false },
    UniversalLpcCustomAnimationSpec { id: "slash_reverse_oversize", frame_size: 192, source_single_animation: false },
    UniversalLpcCustomAnimationSpec { id: "tool_whip", frame_size: 192, source_single_animation: false },
    UniversalLpcCustomAnimationSpec { id: "tool_axe", frame_size: 128, source_single_animation: true },
    UniversalLpcCustomAnimationSpec { id: "tool_hammer", frame_size: 128, source_single_animation: true },
];

pub fn custom_animation_spec(id: &str) -> Option<&'static UniversalLpcCustomAnimationSpec> {
    ULPC_CUSTOM_ANIMATIONS.iter().find(|spec| spec.id == id)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ulpc_contract_is_four_direction_and_preserves_exact_walk_cycle() {
        assert_eq!(ULPC_DIRECTION_ORDER.len(), 4);
        assert_eq!(animation_spec("walk").unwrap().cycle, &[1, 2, 3, 4, 5, 6, 7, 8]);
    }

    #[test]
    fn action_progress_uses_declared_cycle_instead_of_twelve_frame_guess() {
        assert_eq!(frame_for_progress("slash", 0.99), 5);
        assert_eq!(frame_for_progress("watering", 0.50), 4);
    }
}
