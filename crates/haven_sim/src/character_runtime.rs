use haven_core::PersistentEntityId;
use haven_ecs::EntityId;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum CharacterAnimationIntent {
    Idle,
    Walk,
    Run,
    Jump,
    Climb,
    Sit,
    Emote,
    Punch,
    Combat,
    OneHandSlash,
    OneHandBackslash,
    OneHandHalfslash,
    Watering,
    Thrust,
    Shoot,
    Hurt,
    Spellcast,
    Slash,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct CharacterRuntimeState {
    pub entity: EntityId,
    pub facing: [f32; 2],
    pub moving: bool,
    pub locomotion: CharacterAnimationIntent,
    pub locomotion_phase: f32,
    pub action: Option<CharacterAnimationIntent>,
    pub action_phase: f32,
    pub action_duration: f32,
    pub action_remaining: f32,
}

impl CharacterRuntimeState {
    pub const fn player_default(entity: EntityId) -> Self {
        Self {
            entity,
            facing: [0.0, 1.0],
            moving: false,
            locomotion: CharacterAnimationIntent::Idle,
            locomotion_phase: 0.0,
            action: None,
            action_phase: 0.0,
            action_duration: 0.0,
            action_remaining: 0.0,
        }
    }

    pub fn action_locks_movement(self) -> bool {
        self.action_remaining > f32::EPSILON
    }

    pub fn begin_action(&mut self, action: CharacterAnimationIntent, duration: f32) {
        self.action = Some(action);
        self.action_phase = 0.0;
        self.action_duration = duration.max(0.0);
        self.action_remaining = self.action_duration;
    }

    pub fn advance_action(&mut self, dt: f32) {
        if self.action_remaining <= 0.0 {
            self.clear_action();
            return;
        }
        self.action_remaining = (self.action_remaining - dt.max(0.0)).max(0.0);
        self.action_phase += dt.max(0.0);
        if self.action_remaining <= 0.0 {
            self.clear_action();
        }
    }

    pub fn action_progress(self) -> f32 {
        if self.action_duration <= f32::EPSILON {
            return 0.0;
        }
        (self.action_phase / self.action_duration).clamp(0.0, 1.0)
    }

    pub fn clear_action(&mut self) {
        self.action = None;
        self.action_phase = 0.0;
        self.action_duration = 0.0;
        self.action_remaining = 0.0;
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum RuntimeEntityKind {
    Player,
    Npc,
    Interactable,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RuntimeEntityIdentity {
    pub stable_id: PersistentEntityId,
    pub kind: RuntimeEntityKind,
}

impl RuntimeEntityIdentity {
    pub fn player(stable_id: impl Into<String>) -> Self {
        Self {
            stable_id: PersistentEntityId::from_domain_id(stable_id),
            kind: RuntimeEntityKind::Player,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn action_lock_and_timing_match_existing_player_behavior() {
        let mut state = CharacterRuntimeState::player_default(EntityId::from_raw(1));
        state.begin_action(CharacterAnimationIntent::Watering, 0.78);
        assert!(state.action_locks_movement());
        state.advance_action(0.4);
        assert!(state.action.is_some());
        state.advance_action(0.4);
        assert!(state.action.is_none());
        assert!(!state.action_locks_movement());
    }

    #[test]
    fn runtime_identity_uses_persistent_id_not_ecs_handle() {
        let identity = RuntimeEntityIdentity::player("character_123");
        assert_eq!(identity.stable_id.as_str(), "character_123");
        assert!(identity.stable_id.validate().is_ok());
    }
}
