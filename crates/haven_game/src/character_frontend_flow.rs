#![allow(dead_code)]

use haven_save::{CharacterId, WorldSaveId};

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum CharacterFrontendIntent { NewGame, LoadGame }

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum CharacterFrontendStage {
    MainMenu,
    ChooseCharacter { intent: CharacterFrontendIntent },
    CreateCharacter { intent: CharacterFrontendIntent },
    ChooseWorld { intent: CharacterFrontendIntent, character_id: CharacterId },
    CreateWorld { character_id: CharacterId },
    Ready { character_id: CharacterId, world_id: WorldSaveId },
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CharacterFrontendFlow { pub stage: CharacterFrontendStage }

impl Default for CharacterFrontendFlow { fn default() -> Self { Self { stage: CharacterFrontendStage::MainMenu } } }

impl CharacterFrontendFlow {
    pub fn begin(&mut self, intent: CharacterFrontendIntent) { self.stage = CharacterFrontendStage::ChooseCharacter { intent }; }
    pub fn choose_character(&mut self, intent: CharacterFrontendIntent, character_id: CharacterId) { self.stage = CharacterFrontendStage::ChooseWorld { intent, character_id }; }
    pub fn choose_world(&mut self, character_id: CharacterId, world_id: WorldSaveId) { self.stage = CharacterFrontendStage::Ready { character_id, world_id }; }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn new_and_load_both_choose_character_before_world() {
        for intent in [CharacterFrontendIntent::NewGame, CharacterFrontendIntent::LoadGame] {
            let mut flow = CharacterFrontendFlow::default(); flow.begin(intent.clone());
            assert_eq!(flow.stage, CharacterFrontendStage::ChooseCharacter { intent });
        }
    }
}
