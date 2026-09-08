use super::*;
use haven_assets::universal_lpc_character_recipe::UniversalLpcCharacterRecipe;
use haven_authoring::{ResourceContextKind, ResourceContextNode};
use haven_save::load_character_profile;

const RESOURCE_CONTEXT_POLL_SECONDS: f64 = 0.25;

impl EditorApp {
    pub(crate) fn poll_resource_context(&mut self) {
        let now = get_time();
        if now < self.resource_context_next_check {
            return;
        }
        self.resource_context_next_check = now + RESOURCE_CONTEXT_POLL_SECONDS;
        let root = repo_root_dir();
        let Ok(Some(context)) = haven_authoring::read_resource_context(&root) else {
            return;
        };
        if self
            .resource_context
            .as_ref()
            .is_some_and(|current| current.revision >= context.revision)
        {
            return;
        }
        if let Ok(descriptor) = development_session::DevelopmentWorldDescriptor::load() {
            if context.world_id.as_deref().is_some_and(|world| world != descriptor.world_id) {
                return;
            }
        }

        let runtime_ui_focus = context
            .ui
            .as_ref()
            .filter(|ui| ui.developer_focus_requested)
            .map(|ui| ui.document_id.clone());
        let should_open_runtime_ui = runtime_ui_focus.is_some()
            && runtime_ui_focus != self.resource_context_runtime_ui_focus;
        self.resource_context_runtime_ui_focus = runtime_ui_focus.clone();

        if let Some(character) = context.character_animation.as_ref() {
            let should_load_profile = self.resource_context_loaded_character.as_deref()
                != Some(character.character_id.as_str());
            if should_load_profile {
                match load_runtime_character_recipe(&root, &character.character_id) {
                    Ok(Some(recipe)) => {
                        match self.character_studio.load_runtime_typed_recipe(
                            &recipe,
                            &character.action_id,
                            &character.direction,
                        ) {
                            Ok(_) => {
                                self.resource_context_loaded_character =
                                    Some(character.character_id.clone());
                            }
                            Err(error) => {
                                self.status_message = format!(
                                    "Runtime Resource Context loaded, but Character Studio recipe failed: {error}"
                                );
                            }
                        }
                    }
                    Ok(None) => {
                        // Older/starter character profiles can still use the legacy
                        // appearance envelope. Preserve the exact runtime identity and
                        // animation state without inventing a typed ULPC recipe.
                        self.resource_context_loaded_character =
                            Some(character.character_id.clone());
                    }
                    Err(error) => {
                        self.status_message = format!(
                            "Runtime Resource Context profile read failed: {error}"
                        );
                    }
                }
            }
            self.character_studio.apply_runtime_animation_context(
                &character.action_id,
                &character.direction,
            );
            if let Some(slot) = character.equipment_slot.as_deref() {
                let _ = self.character_studio.select_runtime_equipment_slot(slot);
            }
        }
        self.resource_context = Some(context);
        if should_open_runtime_ui {
            if let Some(document_id) = runtime_ui_focus.as_deref() {
                let _ = self.open_game_canvas_ui_document_by_id(document_id);
            }
        }
    }

    pub(crate) fn open_runtime_context_animation_in_studio(&mut self) {
        let Some(character) = self
            .resource_context
            .as_ref()
            .and_then(|context| context.character_animation.clone())
        else {
            self.status_message =
                "No runtime character Resource Context is available yet; run the development client and select the character/equipment first"
                    .to_string();
            return;
        };
        let resolved = match self.character_studio.resolve_runtime_animation_source(
            character.equipment_item_id.as_deref(),
            &character.action_id,
        ) {
            Ok(resolved) => resolved,
            Err(error) => {
                self.status_message = format!("Runtime animation source resolution failed: {error}");
                return;
            }
        };
        let label = if let Some(equipment) = character.equipment_label.as_deref() {
            format!("{equipment} · {}", character.action_id)
        } else {
            format!("{} · {}", resolved.display_name, character.action_id)
        };
        if let Err(error) = self.animation_studio.load_direct_source(&resolved.source_path, &label) {
            self.status_message = format!("Runtime animation source open failed: {error}");
            return;
        }
        let sockets = self.animation_studio.apply_runtime_source_context(
            &resolved.source_animation,
            &character.direction,
            character.frame_index,
            resolved.frame_size,
        );
        self.enrich_resource_context_for_animation(&resolved, &character, sockets);
        self.animation_studio.playing = false;
        self.viewport_mode = EditorViewportMode::AnimationStudio;
        self.reopen_workspace_document(EditorViewportMode::AnimationStudio);
        self.focus_right_dock(super::workspace_shell::RightDockTab::Properties);
        self.status_message = format!(
            "Runtime context → {} → {} → {} frame {}",
            resolved.display_name,
            resolved.source_animation,
            character.direction,
            character.frame_index
        );
    }

    fn enrich_resource_context_for_animation(
        &mut self,
        resolved: &super::character_studio::RuntimeCharacterAnimationSource,
        character: &haven_authoring::CharacterAnimationResourceContext,
        sockets: Vec<String>,
    ) {
        let Some(context) = self.resource_context.as_mut() else { return; };
        if let Some(animation) = context.character_animation.as_mut() {
            animation.socket_ids = sockets.clone();
            animation.active_socket_id = sockets.first().cloned();
        }
        context.chain.retain(|node| {
            !matches!(
                node.kind,
                ResourceContextKind::Animation
                    | ResourceContextKind::Frame
                    | ResourceContextKind::Socket
                    | ResourceContextKind::Source
            )
        });
        context.chain.push(ResourceContextNode::new(
            ResourceContextKind::Animation,
            resolved.source_animation.clone(),
            resolved.source_animation.replace('_', " "),
        ));
        context.chain.push(ResourceContextNode::new(
            ResourceContextKind::Frame,
            format!(
                "{}:{}:{}",
                resolved.source_animation, character.frame_index, character.direction
            ),
            format!("Frame {}", character.frame_index),
        ));
        if let Some(socket) = sockets.first() {
            context.chain.push(ResourceContextNode::new(
                ResourceContextKind::Socket,
                socket.clone(),
                socket.replace('_', " "),
            ));
        }
        context.chain.push(ResourceContextNode::new(
            ResourceContextKind::Source,
            resolved.source_path.to_string_lossy().replace('\\', "/"),
            resolved
                .source_path
                .file_name()
                .and_then(|value| value.to_str())
                .unwrap_or("animation source"),
        ));
    }

    pub(crate) fn resource_context_breadcrumb(&self) -> Option<String> {
        let context = self.resource_context.as_ref()?;
        let breadcrumb = context.breadcrumb();
        (!breadcrumb.is_empty()).then_some(breadcrumb)
    }
}

fn load_runtime_character_recipe(
    repo_root: &std::path::Path,
    character_id: &str,
) -> Result<Option<UniversalLpcCharacterRecipe>, String> {
    let path = repo_root
        .join("WORKSPACE/profiles/characters")
        .join(character_id)
        .join("profile.json");
    if !path.is_file() {
        return Ok(None);
    }
    let profile = load_character_profile(&path)?;
    let Some(recipe) = profile.character_recipe else {
        return Ok(None);
    };
    UniversalLpcCharacterRecipe::from_json_value(recipe.0).map(Some)
}
