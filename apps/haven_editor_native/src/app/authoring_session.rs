#![allow(dead_code)]
use super::canvas_layers::CanvasLayerKind;
use super::document_authority::{DocumentId, DocumentRegistrySnapshot, DocumentSaveState};
use super::tool_registry::UniversalTool;
use super::EditorViewportMode;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub(crate) enum WorkspaceId { GameCanvas, Assets, Pixel, Animation, Character, Data, Logic, Sound }
impl WorkspaceId {
    pub(crate) fn available(self) -> bool { !matches!(self, Self::Data) }
    pub(crate) fn from_legacy(v: EditorViewportMode) -> Self { match v {
        EditorViewportMode::RegionGraph|EditorViewportMode::SceneRectangles|EditorViewportMode::SceneBank|EditorViewportMode::SceneMap => Self::GameCanvas,
        EditorViewportMode::PixelStudio => Self::Pixel, EditorViewportMode::AnimationStudio => Self::Animation,
        EditorViewportMode::CharacterStudio => Self::Character, EditorViewportMode::LogicStudio => Self::Logic,
        EditorViewportMode::SoundStudio => Self::Sound,
    }}
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub(crate) enum GameCanvasView { World, Scene(Option<DocumentId>), SceneLibrary, Routes, Ui(Option<DocumentId>) }
impl GameCanvasView { pub(crate) fn from_legacy(v: EditorViewportMode) -> Option<Self> { Some(match v {
    EditorViewportMode::SceneRectangles => Self::World, EditorViewportMode::SceneMap => Self::Scene(None),
    EditorViewportMode::SceneBank => Self::SceneLibrary, EditorViewportMode::RegionGraph => Self::Routes, _ => return None,
})}}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum EditScope { World, Region, Chunk, Scene, Source, InstanceOverride }
#[derive(Clone, Debug, PartialEq, Eq)]
pub(crate) enum SelectionEnvelope { None, Spatial, Asset, Content, Graph, Character, Animation }
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum RuntimeState { Stopped, Playing, Paused }
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum PaletteProviderId { Terrain, Structure, Pixel, Character, Animation, Ui, None }

#[derive(Clone, Debug)]
pub(crate) struct AuthoringSession {
    pub workspace: WorkspaceId, pub game_canvas_view: Option<GameCanvasView>, pub active_document: Option<DocumentId>,
    pub open_documents: Vec<DocumentId>, pub selection: SelectionEnvelope, pub active_layer: Option<CanvasLayerKind>,
    pub active_tool: UniversalTool, pub active_palette: PaletteProviderId, pub edit_scope: EditScope,
    pub runtime_state: RuntimeState,
}
#[derive(Clone, Debug)]
pub(crate) struct EditorContextSnapshot { pub session: AuthoringSession, pub dirty_documents: Vec<DocumentId>, pub validation_summary: String }

impl super::EditorApp {
    pub(crate) fn authoring_session_snapshot(&self) -> AuthoringSession {
        let docs: DocumentRegistrySnapshot = self.document_registry_snapshot();
        let workspace = if self.asset_studio_open { WorkspaceId::Assets } else { WorkspaceId::from_legacy(self.viewport_mode) };
        let game_canvas_view = if self.asset_studio_open { None } else { GameCanvasView::from_legacy(self.viewport_mode) };
        let active_document = if self.asset_studio_open { None } else { docs.documents.first().map(|d| d.id.clone()) };
        let open_documents = if self.asset_studio_open { Vec::new() } else { docs.documents.iter().map(|d| d.id.clone()).collect() };
        AuthoringSession { workspace, game_canvas_view, active_document, open_documents,
            selection: SelectionEnvelope::None, active_layer: self.active_canvas_layer_kind(), active_tool: self.canvas_active_tool,
            active_palette: PaletteProviderId::for_context(workspace, self.active_canvas_layer_kind()), edit_scope: if workspace == WorkspaceId::GameCanvas { EditScope::World } else { EditScope::Source }, runtime_state: RuntimeState::Stopped }
    }
    pub(crate) fn editor_context_snapshot(&self) -> EditorContextSnapshot {
        let docs = self.document_registry_snapshot();
        EditorContextSnapshot { session: self.authoring_session_snapshot(), dirty_documents: docs.documents.iter().filter(|d| d.save_state == DocumentSaveState::Dirty).map(|d| d.id.clone()).collect(), validation_summary: String::new() }
    }
}
impl PaletteProviderId { pub(crate) fn for_context(w: WorkspaceId, l: Option<CanvasLayerKind>) -> Self {
    use CanvasLayerKind as L; match w { WorkspaceId::Pixel => Self::Pixel, WorkspaceId::Animation => Self::Animation, WorkspaceId::Character => Self::Character,
        WorkspaceId::GameCanvas => match l { Some(L::StructuralLevels|L::Structures|L::Buildings|L::Furniture|L::Props) => Self::Structure, Some(L::UiLayout|L::UiControls|L::UiData|L::UiBehavior|L::UiPresentation|L::UiOverrides) => Self::Ui, _ => Self::Terrain }, _ => Self::None }
}}
