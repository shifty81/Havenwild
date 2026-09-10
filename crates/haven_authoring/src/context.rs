use crate::{AuthoringFrontendKind, GridPos};
use haven_core::ProjectSceneId;
use serde::{Deserialize, Serialize};

/// Canonical creator-facing workspace identity shared by every authoring frontend.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AuthoringWorkspaceKind {
    GameCanvas,
    Assets,
    Pixel,
    Animation,
    Character,
    Logic,
    Sound,
}

/// Contextual view hosted by the Game Canvas. These are not independent studios.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum GameCanvasContextKind {
    World,
    Scene,
    SceneLibrary,
    Routes,
    Ui,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AuthoringEditScope {
    World,
    Region,
    Chunk,
    Scene,
    Source,
    InstanceOverride,
}


#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AuthoringResourceKind {
    SourceSheet,
    TileSet,
    Material,
    Asset,
    EntityDefinition,
    Prefab,
    Brush,
    Rule,
    Scene,
    UiDocument,
    Animation,
    Character,
    Sound,
    Logic,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AuthoringRuntimeState {
    Stopped,
    Playing,
    Paused,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AuthoringSelectionKind {
    None,
    Spatial,
    Asset,
    Entity,
    Prefab,
    Graph,
    Character,
    Animation,
}

/// Cursor/placement authority. A world editor may know both global and local coordinates;
/// scene editing normally needs only the local cell.
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AuthoringCursor {
    #[serde(default)]
    pub scene_id: Option<ProjectSceneId>,
    #[serde(default)]
    pub local_cell: Option<GridPos>,
    #[serde(default)]
    pub world_cell: Option<GridPos>,
}

/// Shared authoring context. UI widgets are projections of this state; they must not own
/// separate world-mutation semantics.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AuthoringContext {
    pub schema: String,
    pub frontend: AuthoringFrontendKind,
    pub workspace: AuthoringWorkspaceKind,
    #[serde(default)]
    pub game_canvas_context: Option<GameCanvasContextKind>,
    pub edit_scope: AuthoringEditScope,
    #[serde(default)]
    pub active_scene: Option<ProjectSceneId>,
    #[serde(default)]
    pub active_layer_id: Option<String>,
    #[serde(default)]
    pub active_tool_id: Option<String>,
    #[serde(default)]
    pub selected_resource_id: Option<String>,
    #[serde(default)]
    pub selected_resource_kind: Option<AuthoringResourceKind>,
    pub selection_kind: AuthoringSelectionKind,
    pub cursor: AuthoringCursor,
    pub runtime_state: AuthoringRuntimeState,
}

impl AuthoringContext {
    pub const SCHEMA_V1: &'static str = "havenwild.authoring_context.v1";

    pub fn native_game_canvas(context: GameCanvasContextKind) -> Self {
        Self {
            schema: Self::SCHEMA_V1.to_string(),
            frontend: AuthoringFrontendKind::NativeDeveloperEditor,
            workspace: AuthoringWorkspaceKind::GameCanvas,
            game_canvas_context: Some(context),
            edit_scope: match context {
                GameCanvasContextKind::World | GameCanvasContextKind::Routes => {
                    AuthoringEditScope::World
                }
                GameCanvasContextKind::Scene | GameCanvasContextKind::Ui => {
                    AuthoringEditScope::Scene
                }
                GameCanvasContextKind::SceneLibrary => AuthoringEditScope::Source,
            },
            active_scene: None,
            active_layer_id: None,
            active_tool_id: None,
            selected_resource_id: None,
            selected_resource_kind: None,
            selection_kind: AuthoringSelectionKind::None,
            cursor: AuthoringCursor::default(),
            runtime_state: AuthoringRuntimeState::Stopped,
        }
    }

    pub fn developer_overlay() -> Self {
        Self {
            schema: Self::SCHEMA_V1.to_string(),
            frontend: AuthoringFrontendKind::DeveloperOverlay,
            workspace: AuthoringWorkspaceKind::GameCanvas,
            game_canvas_context: Some(GameCanvasContextKind::Scene),
            edit_scope: AuthoringEditScope::Scene,
            active_scene: None,
            active_layer_id: None,
            active_tool_id: Some("inspect".to_string()),
            selected_resource_id: None,
            selected_resource_kind: None,
            selection_kind: AuthoringSelectionKind::None,
            cursor: AuthoringCursor::default(),
            runtime_state: AuthoringRuntimeState::Playing,
        }
    }

    pub fn runtime_developer_editor() -> Self {
        let mut context = Self::developer_overlay();
        context.frontend = AuthoringFrontendKind::RuntimeDeveloperEditor;
        context.active_tool_id = Some("select".to_string());
        context
    }

    pub fn is_game_canvas(&self) -> bool {
        self.workspace == AuthoringWorkspaceKind::GameCanvas
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn world_and_scene_are_contexts_inside_one_game_canvas() {
        let world = AuthoringContext::native_game_canvas(GameCanvasContextKind::World);
        let scene = AuthoringContext::native_game_canvas(GameCanvasContextKind::Scene);
        assert!(world.is_game_canvas());
        assert!(scene.is_game_canvas());
        assert_eq!(world.edit_scope, AuthoringEditScope::World);
        assert_eq!(scene.edit_scope, AuthoringEditScope::Scene);
    }

    #[test]
    fn developer_overlay_defaults_to_non_destructive_inspection_context() {
        let context = AuthoringContext::developer_overlay();
        assert_eq!(context.active_tool_id.as_deref(), Some("inspect"));
        assert_eq!(context.runtime_state, AuthoringRuntimeState::Playing);

        let runtime_editor = AuthoringContext::runtime_developer_editor();
        assert_eq!(runtime_editor.frontend, AuthoringFrontendKind::RuntimeDeveloperEditor);
        assert_eq!(runtime_editor.active_tool_id.as_deref(), Some("select"));
    }
}
