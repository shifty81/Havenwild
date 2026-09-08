//! W73A/W73B/W73C/W73O — canonical GUI workflow ownership.

#[cfg(test)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct GuiWorkflowAuthority {
    pub id: &'static str,
    pub owner: &'static str,
}

#[cfg(test)]
pub(crate) const GUI_WORKFLOW_AUTHORITIES: &[GuiWorkflowAuthority] = &[
    GuiWorkflowAuthority { id: "tool_selection", owner: "canvas.tool_rail" },
    GuiWorkflowAuthority { id: "layer_management", owner: "canvas.layers" },
    GuiWorkflowAuthority { id: "canvas_zoom", owner: "canvas.view_controls" },
    GuiWorkflowAuthority { id: "palette", owner: "canvas.shared_palette" },
    GuiWorkflowAuthority { id: "properties", owner: "right_dock.properties" },
    GuiWorkflowAuthority { id: "asset_browser", owner: "right_dock.assets" },
    GuiWorkflowAuthority { id: "outliner", owner: "right_dock.outliner" },
    GuiWorkflowAuthority { id: "validation", owner: "right_dock.validation" },
    GuiWorkflowAuthority { id: "scene_navigation", owner: "right_dock.outliner" },
    GuiWorkflowAuthority { id: "world_navigation", owner: "right_dock.outliner" },
    GuiWorkflowAuthority { id: "asset_import", owner: "command.asset.import" },
    GuiWorkflowAuthority { id: "asset_publish", owner: "command.asset.publish" },
    GuiWorkflowAuthority { id: "build_run", owner: "command.build" },
];

#[cfg(test)]
pub(crate) const RETIRED_GUI_AUTHORITIES: &[&str] = &[
    "asset_shelf",
    "asset_library_panel",
    "asset_intake_panel",
    "scene_toolrail",
    "pixel_layer_panel",
    "scene_dock",
    "legacy_canvas_toolbar",
    "legacy_left_workspace_panel",
];

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashSet;

    #[test]
    fn every_workflow_has_one_owner() {
        let mut ids = HashSet::new();
        for authority in GUI_WORKFLOW_AUTHORITIES {
            assert!(ids.insert(authority.id), "duplicate GUI workflow authority: {}", authority.id);
            assert!(!authority.owner.trim().is_empty());
        }
    }

    #[test]
    fn retired_gui_authorities_remain_explicitly_quarantined() {
        let retired: HashSet<_> = RETIRED_GUI_AUTHORITIES.iter().copied().collect();
        for expected in [
            "asset_shelf",
            "asset_library_panel",
            "asset_intake_panel",
            "scene_toolrail",
            "pixel_layer_panel",
            "scene_dock",
            "legacy_canvas_toolbar",
            "legacy_left_workspace_panel",
        ] {
            assert!(retired.contains(expected), "missing retired GUI authority: {expected}");
        }
    }
}
