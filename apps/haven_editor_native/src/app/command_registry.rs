//! W73D/W73E — canonical native-editor command vocabulary.

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub(crate) enum EditorCommandId {
    SaveAll, ReloadSaved, CloseActiveDocument, ReopenClosedDocument, CloseAllPixelDocuments,
    NewSceneDocument, BrowseProjectScenes, CloseSceneDocument, ReopenClosedSceneDocument,
    Undo, Redo, Cut, Copy, CopyMerged, Paste, Duplicate, MirrorHorizontal, MirrorVertical,
    PromoteSelection, OpenWorld, OpenScene, OpenPixel, OpenAnimation, OpenCharacter, OpenLogic,
    OpenSound, OpenWorldRoutes, OpenSceneBank, OpenUiDocuments, ToggleRightDock, ToggleBottomDock, DockProperties,
    DockAssets, DockOutliner, DockValidation, ToggleLayoutAudit, ResetLayout, ToggleToolRail,
    ToggleLayerRail, TogglePalette, FrameCanvas, RegenerateSeed, RerollArchipelago,
    ExportIslandPngs, PixelEditSelection, Play, PlayFromHere, Restart, Stop, PublishComposition,
    OpenAssetBrowser, CreatePcgExemplar, RefreshAssetCatalog, HelpWelcome, HelpShortcuts,
    HelpCanvas, HelpAssets, HelpPixel, HelpColor,
}

#[derive(Clone, Copy, Debug)]
pub(crate) struct MenuCommand { pub label: &'static str, pub id: EditorCommandId }
impl MenuCommand { pub(crate) const fn new(label: &'static str, id: EditorCommandId) -> Self { Self { label, id } } }

pub(crate) const FILE_COMMANDS: &[MenuCommand] = &[
    MenuCommand::new("Save All", EditorCommandId::SaveAll),
    MenuCommand::new("Reload Saved", EditorCommandId::ReloadSaved),
    MenuCommand::new("Close Active Document", EditorCommandId::CloseActiveDocument),
    MenuCommand::new("Reopen Closed Document", EditorCommandId::ReopenClosedDocument),
    MenuCommand::new("Close All Pixel Documents", EditorCommandId::CloseAllPixelDocuments),
];
pub(crate) const EDIT_COMMANDS: &[MenuCommand] = &[
    MenuCommand::new("Undo", EditorCommandId::Undo), MenuCommand::new("Redo", EditorCommandId::Redo),
    MenuCommand::new("Cut Selection", EditorCommandId::Cut), MenuCommand::new("Copy Selection", EditorCommandId::Copy),
    MenuCommand::new("Copy Merged Selection", EditorCommandId::CopyMerged), MenuCommand::new("Paste", EditorCommandId::Paste),
    MenuCommand::new("Duplicate Selection", EditorCommandId::Duplicate),
    MenuCommand::new("Mirror Selection Horizontal", EditorCommandId::MirrorHorizontal),
    MenuCommand::new("Mirror Selection Vertical", EditorCommandId::MirrorVertical),
];
pub(crate) const VIEW_COMMANDS: &[MenuCommand] = &[
    MenuCommand::new("Dock: Properties", EditorCommandId::DockProperties), MenuCommand::new("Dock: Assets", EditorCommandId::DockAssets),
    MenuCommand::new("Dock: Outliner", EditorCommandId::DockOutliner), MenuCommand::new("Dock: Validation", EditorCommandId::DockValidation),
    MenuCommand::new("Toggle Right Dock", EditorCommandId::ToggleRightDock), MenuCommand::new("Toggle Bottom Panels", EditorCommandId::ToggleBottomDock),
    MenuCommand::new("Toggle Tool Rail", EditorCommandId::ToggleToolRail), MenuCommand::new("Toggle Layers", EditorCommandId::ToggleLayerRail),
    MenuCommand::new("Toggle Palette", EditorCommandId::TogglePalette), MenuCommand::new("Frame Canvas", EditorCommandId::FrameCanvas),
    MenuCommand::new("Toggle Layout Audit", EditorCommandId::ToggleLayoutAudit), MenuCommand::new("Reset Workspace Layout", EditorCommandId::ResetLayout),
];
pub(crate) const WORLD_COMMANDS: &[MenuCommand] = &[
    MenuCommand::new("Game Canvas: Complete World", EditorCommandId::OpenWorld), MenuCommand::new("Game Canvas: Routes", EditorCommandId::OpenWorldRoutes),
    MenuCommand::new("Regenerate Current Seed", EditorCommandId::RegenerateSeed), MenuCommand::new("Reroll Archipelago Seed", EditorCommandId::RerollArchipelago),
    MenuCommand::new("Export Island PNGs", EditorCommandId::ExportIslandPngs), MenuCommand::new("Frame Complete World", EditorCommandId::FrameCanvas),
];
pub(crate) const SCENE_COMMANDS: &[MenuCommand] = &[
    MenuCommand::new("Game Canvas: Active Scene", EditorCommandId::OpenScene),
    MenuCommand::new("New Scene...", EditorCommandId::NewSceneDocument),
    MenuCommand::new("Browse Project Scenes...", EditorCommandId::BrowseProjectScenes),
    MenuCommand::new("Close Scene Tab", EditorCommandId::CloseSceneDocument),
    MenuCommand::new("Reopen Closed Scene", EditorCommandId::ReopenClosedSceneDocument),
    MenuCommand::new("Scene Library", EditorCommandId::OpenSceneBank),
    MenuCommand::new("Game Canvas: UI Documents", EditorCommandId::OpenUiDocuments),
    MenuCommand::new("Pixel Edit Selection", EditorCommandId::PixelEditSelection),
    MenuCommand::new("Play From Here", EditorCommandId::PlayFromHere),
    MenuCommand::new("Frame Scene", EditorCommandId::FrameCanvas),
];
pub(crate) const ASSET_COMMANDS: &[MenuCommand] = &[
    MenuCommand::new("Open Asset Browser", EditorCommandId::OpenAssetBrowser), MenuCommand::new("Refresh Asset Catalog", EditorCommandId::RefreshAssetCatalog),
    MenuCommand::new("Publish Authored Composition...", EditorCommandId::PublishComposition), MenuCommand::new("Promote Selection to Asset...", EditorCommandId::PromoteSelection),
    MenuCommand::new("Create PCG Exemplar From Selection", EditorCommandId::CreatePcgExemplar),
];
pub(crate) const BUILD_COMMANDS: &[MenuCommand] = &[
    MenuCommand::new("Play", EditorCommandId::Play), MenuCommand::new("Play From Here", EditorCommandId::PlayFromHere),
    MenuCommand::new("Restart", EditorCommandId::Restart), MenuCommand::new("Stop", EditorCommandId::Stop),
];
pub(crate) const TOOLS_COMMANDS: &[MenuCommand] = &[
    MenuCommand::new("Pixel Studio", EditorCommandId::OpenPixel), MenuCommand::new("Animation Studio", EditorCommandId::OpenAnimation),
    MenuCommand::new("Character Studio", EditorCommandId::OpenCharacter), MenuCommand::new("Logic Studio", EditorCommandId::OpenLogic),
    MenuCommand::new("Sound Studio", EditorCommandId::OpenSound),
];
pub(crate) const HELP_COMMANDS: &[MenuCommand] = &[
    MenuCommand::new("Help Center", EditorCommandId::HelpWelcome), MenuCommand::new("Keyboard Shortcuts", EditorCommandId::HelpShortcuts),
    MenuCommand::new("Canvas & Layers", EditorCommandId::HelpCanvas), MenuCommand::new("Asset Browsers", EditorCommandId::HelpAssets),
    MenuCommand::new("Pixel / Junction Authoring", EditorCommandId::HelpPixel), MenuCommand::new("Color & Palette", EditorCommandId::HelpColor),
];

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn nine_menu_groups_are_registered() {
        let menus = [FILE_COMMANDS, EDIT_COMMANDS, VIEW_COMMANDS, WORLD_COMMANDS, SCENE_COMMANDS, ASSET_COMMANDS, BUILD_COMMANDS, TOOLS_COMMANDS, HELP_COMMANDS];
        assert_eq!(menus.len(), 9);
        assert!(menus.iter().all(|menu| !menu.is_empty()));
    }
}
