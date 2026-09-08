use haven_assets::universal_lpc_equipment_catalog::{
    UniversalLpcEquipmentItemSeed, UniversalLpcEquipmentItemSeedCatalog,
};
use haven_sim::CharacterAnimationIntent;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum GameplayEquipmentAction {
    Chop,
    Build,
    Till,
    Mine,
    Fish,
    Dig,
    Water,
    Slash,
    Thrust,
    Shoot,
    Spellcast,
    Block,
    Equip,
}

impl GameplayEquipmentAction {
    pub(crate) fn parse(value: &str) -> Option<Self> {
        Some(match value {
            "chop" => Self::Chop,
            "build" => Self::Build,
            "till" => Self::Till,
            "mine" => Self::Mine,
            "fish" => Self::Fish,
            "dig" => Self::Dig,
            "water" => Self::Water,
            "slash" => Self::Slash,
            "thrust" => Self::Thrust,
            "shoot" => Self::Shoot,
            "spellcast" => Self::Spellcast,
            "block" => Self::Block,
            "equip" => Self::Equip,
            _ => return None,
        })
    }

    pub(crate) fn animation(self) -> CharacterAnimationIntent {
        match self {
            // Upstream ULPC's tool_axe and tool_hammer custom 128px sheets
            // explicitly declare `slash` as their base body animation. Drive the
            // body from that same authored clip so the tool overlay and hands use
            // one frame/time authority instead of visibly separating.
            Self::Chop | Self::Build => CharacterAnimationIntent::Slash,
            Self::Mine | Self::Dig => CharacterAnimationIntent::OneHandHalfslash,
            Self::Till => CharacterAnimationIntent::OneHandSlash,
            Self::Fish | Self::Thrust => CharacterAnimationIntent::Thrust,
            Self::Water => CharacterAnimationIntent::Watering,
            Self::Slash => CharacterAnimationIntent::Slash,
            Self::Shoot => CharacterAnimationIntent::Shoot,
            Self::Spellcast => CharacterAnimationIntent::Spellcast,
            Self::Block | Self::Equip => CharacterAnimationIntent::Combat,
        }
    }

    pub(crate) fn ulpc_animation(self) -> &'static str {
        match self {
            Self::Chop | Self::Build => "slash",
            Self::Mine | Self::Dig => "1h_halfslash",
            Self::Till => "1h_slash",
            Self::Fish | Self::Thrust => "thrust",
            Self::Water => "watering",
            Self::Slash => "slash",
            Self::Shoot => "shoot",
            Self::Spellcast => "spellcast",
            Self::Block | Self::Equip => "combat",
        }
    }

    pub(crate) fn duration_seconds(self) -> f32 {
        match self {
            Self::Chop => 0.58,
            Self::Build => 0.58,
            Self::Till => 0.56,
            Self::Mine => 0.62,
            Self::Fish => 0.72,
            Self::Dig => 0.60,
            Self::Water => 0.78,
            Self::Slash => 0.64,
            Self::Thrust => 0.62,
            Self::Shoot => 0.72,
            Self::Spellcast => 0.82,
            Self::Block | Self::Equip => 0.34,
        }
    }
}

#[derive(Clone, Debug)]
pub(crate) struct RuntimeEquipmentBinding {
    pub item_id: String,
    pub action: GameplayEquipmentAction,
}

impl RuntimeEquipmentBinding {
    fn from_seed(seed: &UniversalLpcEquipmentItemSeed) -> Option<Self> {
        Some(Self {
            item_id: seed.item_id.clone(),
            action: GameplayEquipmentAction::parse(&seed.gameplay_action)?,
        })
    }
}

#[derive(Clone, Debug, Default)]
pub(crate) struct UniversalLpcGameplayEquipmentRuntime {
    pub bindings: Vec<RuntimeEquipmentBinding>,
}

impl UniversalLpcGameplayEquipmentRuntime {
    pub(crate) fn load_default() -> Result<Self, String> {
        let source = UniversalLpcEquipmentItemSeedCatalog::load_default()?;
        let bindings = source
            .items
            .iter()
            .filter_map(RuntimeEquipmentBinding::from_seed)
            .collect();
        Ok(Self { bindings })
    }

    pub(crate) fn find(&self, item_id: &str) -> Option<&RuntimeEquipmentBinding> {
        self.bindings
            .iter()
            .find(|binding| binding.item_id == item_id)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn combat_actions_map_to_real_ulpc_animation_families() {
        assert_eq!(GameplayEquipmentAction::Slash.ulpc_animation(), "slash");
        assert_eq!(GameplayEquipmentAction::Shoot.ulpc_animation(), "shoot");
        assert_eq!(
            GameplayEquipmentAction::Spellcast.ulpc_animation(),
            "spellcast"
        );
    }

    #[test]
    fn custom_tool_actions_use_their_declared_ulpc_base_animation() {
        assert_eq!(GameplayEquipmentAction::Chop.ulpc_animation(), "slash");
        assert_eq!(GameplayEquipmentAction::Build.ulpc_animation(), "slash");
        assert!(matches!(
            GameplayEquipmentAction::Chop.animation(),
            CharacterAnimationIntent::Slash
        ));
        assert!(matches!(
            GameplayEquipmentAction::Build.animation(),
            CharacterAnimationIntent::Slash
        ));
    }
}
