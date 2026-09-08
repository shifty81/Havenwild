use std::{fs, path::Path};

use serde::{Deserialize, Serialize};

pub(crate) const NATIVE_WORKSPACE_LAYOUT_PATH: &str =
    "WORKSPACE/editor/native_workspace_layout_v0_1.json";

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum WorkspaceResizeDrag {
    LeftPanel,
    RightPanel,
    BottomDock,
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub(crate) enum BottomDockTab {
    #[default]
    Console,
    /// Legacy persisted value from pre-A14 layouts. Normalization migrates this
    /// to Activity; Validation itself has one canonical owner in the right dock.
    Validation,
    Imports,
    Build,
    Tasks,
}

impl BottomDockTab {
    pub(crate) const ALL: [Self; 4] = [
        Self::Console,
        Self::Imports,
        Self::Build,
        Self::Tasks,
    ];

    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Console => "Console",
            Self::Validation => "Activity",
            Self::Imports => "Imports",
            Self::Build => "Build",
            Self::Tasks => "Activity",
        }
    }
}


#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub(crate) enum RightDockTab {
    #[default]
    Properties,
    Assets,
    Outliner,
    Validation,
}

impl RightDockTab {
    pub(crate) const ALL: [Self; 4] = [Self::Properties, Self::Assets, Self::Outliner, Self::Validation];

    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Properties => "Properties",
            Self::Assets => "Assets",
            Self::Outliner => "Outliner",
            Self::Validation => "Validation",
        }
    }
}


#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub(crate) enum AssetBrowserScope {
    #[default]
    AllProject,
    Workspace,
}

impl AssetBrowserScope {
    pub(crate) const ALL: [Self; 2] = [Self::AllProject, Self::Workspace];
    pub(crate) fn label(self) -> &'static str {
        match self { Self::AllProject => "All Project", Self::Workspace => "Workspace" }
    }
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub(crate) enum DocumentSplitMode {
    #[default]
    Single,
    Vertical,
    Horizontal,
}

impl DocumentSplitMode {
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Single => "Single",
            Self::Vertical => "Side ×2",
            Self::Horizontal => "Legacy Split ↕",
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(default)]
pub(crate) struct EditorWorkspaceShellState {
    pub schema: String,
    pub left_panel_visible: bool,
    pub right_panel_visible: bool,
    pub bottom_dock_open: bool,
    pub bottom_dock_tab: BottomDockTab,
    pub right_dock_tab: RightDockTab,
    pub asset_browser_scope: AssetBrowserScope,
    pub shared_palette_visible: bool,
    pub shared_palette_scroll: usize,
    pub document_split_mode: DocumentSplitMode,
    pub document_split_ratio: f32,
    pub link_split_cameras: bool,
    pub left_panel_width: f32,
    pub right_panel_width: f32,
    pub bottom_dock_height: f32,
    pub canvas_tool_rail_collapsed: bool,
    pub canvas_layer_rail_collapsed: bool,
    pub canvas_layer_rail_width: f32,
    pub canvas_tool_scroll: usize,
    pub canvas_layer_scroll: usize,
}

impl Default for EditorWorkspaceShellState {
    fn default() -> Self {
        Self {
            schema: "havenwild.native_editor.workspace_layout.v0_6".to_string(),
            left_panel_visible: false,
            right_panel_visible: true,
            bottom_dock_open: false,
            bottom_dock_tab: BottomDockTab::Console,
            right_dock_tab: RightDockTab::Properties,
            asset_browser_scope: AssetBrowserScope::AllProject,
            shared_palette_visible: true,
            shared_palette_scroll: 0,
            document_split_mode: DocumentSplitMode::Single,
            document_split_ratio: 0.5,
            link_split_cameras: false,
            left_panel_width: 248.0,
            right_panel_width: 360.0,
            bottom_dock_height: 176.0,
            canvas_tool_rail_collapsed: false,
            canvas_layer_rail_collapsed: false,
            canvas_layer_rail_width: 174.0,
            canvas_tool_scroll: 0,
            canvas_layer_scroll: 0,
        }
    }
}

impl EditorWorkspaceShellState {
    pub(crate) fn load_default() -> Self {
        let path = Path::new(NATIVE_WORKSPACE_LAYOUT_PATH);
        let Ok(text) = fs::read_to_string(path) else {
            return Self::default();
        };
        serde_json::from_str::<Self>(&text)
            .map(Self::normalized)
            .unwrap_or_default()
    }

    pub(crate) fn save_default(&self) -> Result<(), String> {
        let path = Path::new(NATIVE_WORKSPACE_LAYOUT_PATH);
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).map_err(|error| {
                format!("could not create native editor workspace directory: {error}")
            })?;
        }
        let normalized = self.clone().normalized();
        let text = serde_json::to_string_pretty(&normalized)
            .map_err(|error| format!("could not serialize native editor workspace: {error}"))?;
        fs::write(path, format!("{text}\n"))
            .map_err(|error| format!("could not save native editor workspace: {error}"))
    }

    pub(crate) fn reset(&mut self) {
        *self = Self::default();
    }

    pub(crate) fn normalize_in_place(&mut self) {
        self.schema = "havenwild.native_editor.workspace_layout.v0_6".to_string();
        // W63: the legacy permanent left project/library panel is retired. Project and
        // asset navigation now live in the canonical right dock so the canvas always
        // reclaims the entire left-side footprint.
        self.left_panel_visible = false;
        // Pixel Studio exposes one deliberate dual-document mode: side-by-side.
        // Older persisted horizontal split layouts migrate to the supported mode.
        if self.document_split_mode == DocumentSplitMode::Horizontal {
            self.document_split_mode = DocumentSplitMode::Vertical;
        }
        self.document_split_ratio = self.document_split_ratio.clamp(0.25, 0.75);
        self.left_panel_width = self.left_panel_width.clamp(220.0, 360.0);
        self.right_panel_width = self.right_panel_width.clamp(300.0, 480.0);
        self.bottom_dock_height = self.bottom_dock_height.clamp(136.0, 320.0);
        self.canvas_layer_rail_width = self.canvas_layer_rail_width.clamp(132.0, 480.0);
        // A14Y: the palette is a real canvas panel whose colors come from the
        // active authored document. Workspace state keeps only visibility/scroll.
        self.shared_palette_scroll = self.shared_palette_scroll.min(128);
        self.canvas_tool_scroll = self.canvas_tool_scroll.min(128);
        self.canvas_layer_scroll = self.canvas_layer_scroll.min(512);
        if self.bottom_dock_tab == BottomDockTab::Validation {
            self.bottom_dock_tab = BottomDockTab::Tasks;
        }
    }

    pub(crate) fn normalized(mut self) -> Self {
        self.normalize_in_place();
        self
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn normalization_keeps_panels_inside_supported_ranges() {
        let state = EditorWorkspaceShellState {
            left_panel_width: 12.0,
            right_panel_width: 900.0,
            bottom_dock_height: 12.0,
            ..EditorWorkspaceShellState::default()
        }
        .normalized();
        assert_eq!(state.left_panel_width, 220.0);
        assert_eq!(state.right_panel_width, 480.0);
        assert_eq!(state.bottom_dock_height, 136.0);
        assert_eq!(state.canvas_layer_rail_width, 174.0);
    }

    #[test]
    fn bottom_dock_tabs_have_stable_labels() {
        assert_eq!(BottomDockTab::ALL.len(), 4);
        assert!(!BottomDockTab::ALL.contains(&BottomDockTab::Validation));
        assert_eq!(BottomDockTab::Tasks.label(), "Activity");
        assert_eq!(RightDockTab::ALL.len(), 4);
        assert_eq!(RightDockTab::Assets.label(), "Assets");
        assert_eq!(DocumentSplitMode::Vertical.label(), "Side ×2");
        assert_eq!(AssetBrowserScope::ALL.len(), 2);
        assert_eq!(AssetBrowserScope::AllProject.label(), "All Project");
    }
}
