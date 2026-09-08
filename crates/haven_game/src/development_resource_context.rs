use super::*;
use haven_authoring::{
    CharacterAnimationResourceContext, ResourceContext, ResourceContextKind, ResourceContextNode,
    UiResourceContext,
};

impl Game {
    /// Captures the exact runtime character/equipment/animation frame currently
    /// being presented. The native editor consumes this neutral context instead
    /// of reconstructing an approximate Character Studio state from defaults.
    pub(crate) fn development_resource_context(&self, revision: u64) -> ResourceContext {
        let character = self.player_character_state();
        let locomotion = crate::character_ecs_runtime::compositor_animation_kind(character.locomotion);
        let action = character
            .action
            .map(crate::character_ecs_runtime::compositor_animation_kind);
        let frame = crate::character_runtime_compositor::RuntimeCharacterAppearance::frame(
            self.player_facing_vec(),
            locomotion,
            character.locomotion_phase,
            action,
            character.action_progress(),
        );
        let animation = frame.animation.ulpc_id();
        let direction = match frame.facing {
            crate::character_runtime_compositor::CharacterFacing::North => "north",
            crate::character_runtime_compositor::CharacterFacing::West => "west",
            crate::character_runtime_compositor::CharacterFacing::South => "south",
            crate::character_runtime_compositor::CharacterFacing::East => "east",
        };
        let equipped = self.player_inventory_ui.equipped_items().get("main_hand");

        let mut context = ResourceContext::new(revision);
        context.world_id = Some(self.world_id.0.clone());
        context.scene_id = Some(self.world.active_scene.code().to_string());
        context.chain.push(ResourceContextNode::new(
            ResourceContextKind::Character,
            self.character_id.0.clone(),
            self.character_id.0.clone(),
        ));
        if let Some(stack) = equipped {
            let mut equipment = ResourceContextNode::new(
                ResourceContextKind::Equipment,
                stack.item_id.clone(),
                stack.display_name.clone(),
            );
            equipment.instance_id = Some(format!("{}:main_hand", self.character_id.0));
            context.chain.push(equipment);
        }
        context.chain.push(ResourceContextNode::new(
            ResourceContextKind::Animation,
            animation,
            animation,
        ));
        context.chain.push(ResourceContextNode::new(
            ResourceContextKind::Frame,
            format!("{animation}:{}:{direction}", frame.frame),
            format!("Frame {}", frame.frame),
        ));
        let active_ui_document = if self.pause_menu_open {
            Some(match self.pause_menu_page {
                crate::client_pause_menu::PauseMenuPage::Main => "pause",
                crate::client_pause_menu::PauseMenuPage::Settings
                | crate::client_pause_menu::PauseMenuPage::Controls
                | crate::client_pause_menu::PauseMenuPage::Controller => "settings",
            })
        } else if self.world_map.open {
            Some("map")
        } else if self.player_inventory_ui.open {
            Some(self.player_inventory_ui.authoring_ui_document_id())
        } else {
            None
        };
        if let Some(document_id) = active_ui_document {
            let related_document_ids = if self.player_inventory_ui.open {
                ["inventory", "crafting"]
                    .into_iter()
                    .filter(|candidate| *candidate != document_id)
                    .map(str::to_string)
                    .collect()
            } else {
                Vec::new()
            };
            context.chain.push(ResourceContextNode::new(
                ResourceContextKind::Ui,
                document_id,
                document_id.replace('_', " "),
            ));
            context.ui = Some(UiResourceContext {
                document_id: document_id.to_string(),
                related_document_ids,
                selected_control_id: None,
                developer_focus_requested: self.dev_mode,
            });
        }

        context.character_animation = Some(CharacterAnimationResourceContext {
            character_id: self.character_id.0.clone(),
            equipment_slot: equipped.map(|_| "main_hand".to_string()),
            equipment_item_id: equipped.map(|stack| stack.item_id.clone()),
            equipment_label: equipped.map(|stack| stack.display_name.clone()),
            action_id: animation.to_string(),
            direction: direction.to_string(),
            frame_index: frame.frame,
            // Socket identity is populated by the editor from the authoritative
            // animation document once that frame is opened. Do not fabricate a
            // runtime socket name when no socket metadata is loaded here.
            socket_ids: Vec::new(),
            active_socket_id: None,
        });
        context
    }
}

#[cfg(test)]
mod tests {
    #[test]
    fn direction_labels_match_ulpc_cardinal_rows() {
        let labels = [
            crate::character_runtime_compositor::CharacterFacing::North,
            crate::character_runtime_compositor::CharacterFacing::West,
            crate::character_runtime_compositor::CharacterFacing::South,
            crate::character_runtime_compositor::CharacterFacing::East,
        ]
        .map(|facing| match facing {
            crate::character_runtime_compositor::CharacterFacing::North => "north",
            crate::character_runtime_compositor::CharacterFacing::West => "west",
            crate::character_runtime_compositor::CharacterFacing::South => "south",
            crate::character_runtime_compositor::CharacterFacing::East => "east",
        });
        assert_eq!(labels, ["north", "west", "south", "east"]);
    }
}
