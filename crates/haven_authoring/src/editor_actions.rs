use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EditorActionGroup {
    File,
    Edit,
    View,
    World,
    Scene,
    Assets,
    Build,
    Tools,
    Help,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum EditorActionId {
    SaveAll,
    ReloadSaved,
    CloseActiveDocument,
    ReopenClosedDocument,
    CloseAllPixelDocuments,
    NewSceneDocument,
    BrowseProjectScenes,
    CloseSceneDocument,
    ReopenClosedSceneDocument,
    Undo,
    Redo,
    Cut,
    Copy,
    CopyMerged,
    Paste,
    Duplicate,
    MirrorHorizontal,
    MirrorVertical,
    PromoteSelection,
    OpenWorld,
    OpenScene,
    OpenPixel,
    OpenAnimation,
    OpenCharacter,
    OpenLogic,
    OpenSound,
    OpenWorldRoutes,
    OpenSceneBank,
    OpenUiDocuments,
    ToggleRightDock,
    ToggleBottomDock,
    DockProperties,
    DockAssets,
    DockOutliner,
    DockValidation,
    ToggleLayoutAudit,
    ResetLayout,
    ToggleToolRail,
    ToggleLayerRail,
    TogglePalette,
    FrameCanvas,
    RegenerateSeed,
    RerollArchipelago,
    ExportIslandPngs,
    PixelEditSelection,
    Play,
    PlayFromHere,
    Restart,
    Stop,
    PublishComposition,
    OpenAssetBrowser,
    CreatePcgExemplar,
    RefreshAssetCatalog,
    HelpWelcome,
    HelpShortcuts,
    HelpCanvas,
    HelpAssets,
    HelpPixel,
    HelpColor,
}

impl EditorActionId {
    pub const ALL: [Self; 59] = [
        Self::SaveAll,
        Self::ReloadSaved,
        Self::CloseActiveDocument,
        Self::ReopenClosedDocument,
        Self::CloseAllPixelDocuments,
        Self::NewSceneDocument,
        Self::BrowseProjectScenes,
        Self::CloseSceneDocument,
        Self::ReopenClosedSceneDocument,
        Self::Undo,
        Self::Redo,
        Self::Cut,
        Self::Copy,
        Self::CopyMerged,
        Self::Paste,
        Self::Duplicate,
        Self::MirrorHorizontal,
        Self::MirrorVertical,
        Self::PromoteSelection,
        Self::OpenWorld,
        Self::OpenScene,
        Self::OpenPixel,
        Self::OpenAnimation,
        Self::OpenCharacter,
        Self::OpenLogic,
        Self::OpenSound,
        Self::OpenWorldRoutes,
        Self::OpenSceneBank,
        Self::OpenUiDocuments,
        Self::ToggleRightDock,
        Self::ToggleBottomDock,
        Self::DockProperties,
        Self::DockAssets,
        Self::DockOutliner,
        Self::DockValidation,
        Self::ToggleLayoutAudit,
        Self::ResetLayout,
        Self::ToggleToolRail,
        Self::ToggleLayerRail,
        Self::TogglePalette,
        Self::FrameCanvas,
        Self::RegenerateSeed,
        Self::RerollArchipelago,
        Self::ExportIslandPngs,
        Self::PixelEditSelection,
        Self::Play,
        Self::PlayFromHere,
        Self::Restart,
        Self::Stop,
        Self::PublishComposition,
        Self::OpenAssetBrowser,
        Self::CreatePcgExemplar,
        Self::RefreshAssetCatalog,
        Self::HelpWelcome,
        Self::HelpShortcuts,
        Self::HelpCanvas,
        Self::HelpAssets,
        Self::HelpPixel,
        Self::HelpColor,
    ];

    pub const fn stable_key(self) -> &'static str {
        match self {
            Self::SaveAll => "file.save_all",
            Self::ReloadSaved => "file.reload_saved",
            Self::CloseActiveDocument => "file.close_active_document",
            Self::ReopenClosedDocument => "file.reopen_closed_document",
            Self::CloseAllPixelDocuments => "file.close_all_pixel_documents",
            Self::NewSceneDocument => "scene.new_document",
            Self::BrowseProjectScenes => "scene.browse_project_scenes",
            Self::CloseSceneDocument => "scene.close_document",
            Self::ReopenClosedSceneDocument => "scene.reopen_closed_document",
            Self::Undo => "edit.undo",
            Self::Redo => "edit.redo",
            Self::Cut => "edit.cut",
            Self::Copy => "edit.copy",
            Self::CopyMerged => "edit.copy_merged",
            Self::Paste => "edit.paste",
            Self::Duplicate => "edit.duplicate",
            Self::MirrorHorizontal => "edit.mirror_horizontal",
            Self::MirrorVertical => "edit.mirror_vertical",
            Self::PromoteSelection => "asset.promote_selection",
            Self::OpenWorld => "world.open",
            Self::OpenScene => "scene.open_active",
            Self::OpenPixel => "studio.pixel.open",
            Self::OpenAnimation => "studio.animation.open",
            Self::OpenCharacter => "studio.character.open",
            Self::OpenLogic => "studio.logic.open",
            Self::OpenSound => "studio.sound.open",
            Self::OpenWorldRoutes => "world.routes.open",
            Self::OpenSceneBank => "scene.library.open",
            Self::OpenUiDocuments => "scene.ui_documents.open",
            Self::ToggleRightDock => "view.right_dock.toggle",
            Self::ToggleBottomDock => "view.bottom_dock.toggle",
            Self::DockProperties => "view.dock.properties",
            Self::DockAssets => "view.dock.assets",
            Self::DockOutliner => "view.dock.outliner",
            Self::DockValidation => "view.dock.validation",
            Self::ToggleLayoutAudit => "view.layout_audit.toggle",
            Self::ResetLayout => "view.layout.reset",
            Self::ToggleToolRail => "view.tool_rail.toggle",
            Self::ToggleLayerRail => "view.layer_rail.toggle",
            Self::TogglePalette => "view.palette.toggle",
            Self::FrameCanvas => "view.canvas.frame",
            Self::RegenerateSeed => "world.seed.regenerate",
            Self::RerollArchipelago => "world.archipelago.reroll",
            Self::ExportIslandPngs => "world.islands.export_png",
            Self::PixelEditSelection => "scene.selection.pixel_edit",
            Self::Play => "runtime.play",
            Self::PlayFromHere => "runtime.play_from_here",
            Self::Restart => "runtime.restart",
            Self::Stop => "runtime.stop",
            Self::PublishComposition => "asset.publish_composition",
            Self::OpenAssetBrowser => "asset.browser.open",
            Self::CreatePcgExemplar => "asset.pcg_exemplar.create",
            Self::RefreshAssetCatalog => "asset.catalog.refresh",
            Self::HelpWelcome => "help.welcome",
            Self::HelpShortcuts => "help.shortcuts",
            Self::HelpCanvas => "help.canvas",
            Self::HelpAssets => "help.assets",
            Self::HelpPixel => "help.pixel",
            Self::HelpColor => "help.color",
        }
    }

    pub const fn group(self) -> EditorActionGroup {
        match self {
            Self::SaveAll
            | Self::ReloadSaved
            | Self::CloseActiveDocument
            | Self::ReopenClosedDocument
            | Self::CloseAllPixelDocuments => EditorActionGroup::File,
            Self::Undo
            | Self::Redo
            | Self::Cut
            | Self::Copy
            | Self::CopyMerged
            | Self::Paste
            | Self::Duplicate
            | Self::MirrorHorizontal
            | Self::MirrorVertical => EditorActionGroup::Edit,
            Self::ToggleRightDock
            | Self::ToggleBottomDock
            | Self::DockProperties
            | Self::DockAssets
            | Self::DockOutliner
            | Self::DockValidation
            | Self::ToggleLayoutAudit
            | Self::ResetLayout
            | Self::ToggleToolRail
            | Self::ToggleLayerRail
            | Self::TogglePalette
            | Self::FrameCanvas => EditorActionGroup::View,
            Self::OpenWorld
            | Self::OpenWorldRoutes
            | Self::RegenerateSeed
            | Self::RerollArchipelago
            | Self::ExportIslandPngs => EditorActionGroup::World,
            Self::NewSceneDocument
            | Self::BrowseProjectScenes
            | Self::CloseSceneDocument
            | Self::ReopenClosedSceneDocument
            | Self::OpenScene
            | Self::OpenSceneBank
            | Self::OpenUiDocuments
            | Self::PixelEditSelection => EditorActionGroup::Scene,
            Self::PromoteSelection
            | Self::PublishComposition
            | Self::OpenAssetBrowser
            | Self::CreatePcgExemplar
            | Self::RefreshAssetCatalog => EditorActionGroup::Assets,
            Self::Play | Self::PlayFromHere | Self::Restart | Self::Stop => EditorActionGroup::Build,
            Self::OpenPixel
            | Self::OpenAnimation
            | Self::OpenCharacter
            | Self::OpenLogic
            | Self::OpenSound => EditorActionGroup::Tools,
            Self::HelpWelcome
            | Self::HelpShortcuts
            | Self::HelpCanvas
            | Self::HelpAssets
            | Self::HelpPixel
            | Self::HelpColor => EditorActionGroup::Help,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::BTreeSet;

    #[test]
    fn canonical_action_keys_are_unique() {
        let keys: BTreeSet<_> = EditorActionId::ALL
            .iter()
            .map(|action| action.stable_key())
            .collect();
        assert_eq!(keys.len(), EditorActionId::ALL.len());
    }
}
