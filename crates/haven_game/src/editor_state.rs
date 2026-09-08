use haven_core::{BuildTool, UiPanelId};
use macroquad::prelude::Vec2;

#[derive(Clone, Copy, PartialEq, Eq)]
pub(crate) enum EditorTab {
    Tiles,
    Objects,
    Zones,
    Rules,
    Map,
    Paint,
    World,
    Transitions,
    Assets,
}

#[derive(Clone, Copy)]
pub(crate) enum TransitionEdit {
    CycleTarget,
    Grow,
    Shrink,
    SetDestination,
    Delete,
}

#[derive(Clone, Copy, PartialEq, Eq)]
pub(crate) enum MapBrushMode {
    Raise,
    Lower,
    Smooth,
}

impl MapBrushMode {
    pub(crate) fn label(self) -> &'static str {
        match self {
            MapBrushMode::Raise => "Raise",
            MapBrushMode::Lower => "Lower",
            MapBrushMode::Smooth => "Smooth",
        }
    }
}

#[derive(Clone, Copy, PartialEq, Eq)]
pub(crate) enum FootprintEditTarget {
    Visual,
    Collision,
    Interaction,
}

impl FootprintEditTarget {
    pub(crate) fn label(self) -> &'static str {
        match self {
            FootprintEditTarget::Visual => "Visual",
            FootprintEditTarget::Collision => "Collision",
            FootprintEditTarget::Interaction => "Interaction",
        }
    }
}

#[derive(Clone, Copy)]
pub(crate) struct LayoutDrag {
    pub(crate) panel: UiPanelId,
    pub(crate) grab_offset: Vec2,
}

#[derive(Clone, Copy)]
pub(crate) struct TileContextMenu {
    pub(crate) cell: (i32, i32),
    pub(crate) screen: Vec2,
}

impl EditorTab {
    pub(crate) const ALL: [EditorTab; 8] = [
        EditorTab::World,
        EditorTab::Tiles,
        EditorTab::Objects,
        EditorTab::Zones,
        EditorTab::Map,
        EditorTab::Transitions,
        EditorTab::Rules,
        EditorTab::Assets,
    ];

    pub(crate) fn label(self) -> &'static str {
        match self {
            EditorTab::Tiles => "Ground",
            EditorTab::Objects => "Props",
            EditorTab::Zones => "Zones",
            EditorTab::Rules => "Rules",
            EditorTab::Map => "Elevation",
            EditorTab::Paint => "Blend",
            EditorTab::World => "World",
            EditorTab::Transitions => "Topology",
            EditorTab::Assets => "Sources",
        }
    }

    pub(crate) fn workflow_help(self) -> &'static str {
        match self {
            EditorTab::Tiles => "Choose Exact, Coast, or Hydrology before painting. Exact changes only selected semantic cells and is the default. Coast and Hydrology are explicit neighboring-repair operations. The current certified ground palette is V7-only; ElizaWy remains a separate style lane.",
            EditorTab::Objects => "Choose a prop to place. Blue visual, collision, and yellow interaction bounds resolve from the same deterministic authored atlas variant; manual overrides remain available for custom props.",
            EditorTab::Zones => "Choose a gameplay zone, then paint its owned cells directly on the map.",
            EditorTab::Rules => "Inspect and change the interaction behavior assigned to each tile material.",
            EditorTab::Map => "Raise, lower, or smooth the saved height field, then rebuild style-aware cliff faces, ramps, cave hosts, and water-facing edges.",
            EditorTab::Paint => "Blend semantic materials and refresh their adjacency-driven transition bindings.",
            EditorTab::World => "Switch scenes, save or validate the world, and manage scene connections.",
            EditorTab::Transitions => "Inspect shared topology without mixing style pixels. V7 shoreline and water use exact authored tuples; Gravel, Rock Ground and Mud may use reviewed V7-only connector tuples. Unsupported combinations remain diagnostic; no ElizaWy or generated transition overlay is layered onto this lane.",
            EditorTab::Assets => "Browse audited style-pack sources, provenance, grid metadata, cliff providers, and runtime promotion status.",
        }
    }

    pub(crate) fn contains(self, tool: BuildTool) -> bool {
        match self {
            EditorTab::Tiles => matches!(
                tool,
                BuildTool::Floor(_) | BuildTool::Hoe | BuildTool::GreenhouseZone
            ),
            EditorTab::Objects => matches!(tool, BuildTool::Object(_)),
            EditorTab::Zones => matches!(tool, BuildTool::Zone(_)),
            EditorTab::Rules => matches!(tool, BuildTool::Inspect),
            EditorTab::Map => matches!(tool, BuildTool::Inspect),
            EditorTab::Paint => matches!(tool, BuildTool::Inspect),
            EditorTab::World => matches!(
                tool,
                BuildTool::Inspect | BuildTool::Transition | BuildTool::Erase
            ),
            EditorTab::Transitions => matches!(tool, BuildTool::Inspect),
            EditorTab::Assets => matches!(tool, BuildTool::Inspect),
        }
    }
}
