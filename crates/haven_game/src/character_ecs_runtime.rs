use super::*;
use haven_sim::{CharacterAnimationIntent, CharacterRuntimeState};

impl Game {
    pub(super) fn player_character_state(&self) -> CharacterRuntimeState {
        *self
            .ecs_world
            .get::<CharacterRuntimeState>(self.player_entity)
            .expect("player ECS character state must exist for the lifetime of Game")
    }

    pub(super) fn set_player_character_state(&mut self, state: CharacterRuntimeState) {
        debug_assert_eq!(state.entity, self.player_entity);
        *self
            .ecs_world
            .get_mut::<CharacterRuntimeState>(self.player_entity)
            .expect("player ECS character state must exist for the lifetime of Game") = state;
    }

    pub(super) fn player_facing_vec(&self) -> Vec2 {
        let state = self.player_character_state();
        vec2(state.facing[0], state.facing[1])
    }

    pub(super) fn player_is_moving(&self) -> bool {
        self.player_character_state().moving
    }
}

pub(crate) const fn compositor_animation_kind(
    intent: CharacterAnimationIntent,
) -> crate::character_runtime_compositor::CharacterAnimationKind {
    use crate::character_runtime_compositor::CharacterAnimationKind as Visual;
    use CharacterAnimationIntent as Intent;
    match intent {
        Intent::Idle => Visual::Idle,
        Intent::Walk => Visual::Walk,
        Intent::Run => Visual::Run,
        Intent::Jump => Visual::Jump,
        Intent::Climb => Visual::Climb,
        Intent::Sit => Visual::Sit,
        Intent::Emote => Visual::Emote,
        Intent::Punch => Visual::Punch,
        Intent::Combat => Visual::Combat,
        Intent::OneHandSlash => Visual::OneHandSlash,
        Intent::OneHandBackslash => Visual::OneHandBackslash,
        Intent::OneHandHalfslash => Visual::OneHandHalfslash,
        Intent::Watering => Visual::Watering,
        Intent::Thrust => Visual::Thrust,
        Intent::Shoot => Visual::Shoot,
        Intent::Hurt => Visual::Hurt,
        Intent::Spellcast => Visual::Spellcast,
        Intent::Slash => Visual::Slash,
    }
}
