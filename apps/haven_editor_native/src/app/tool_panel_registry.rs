#![allow(dead_code)]

/// Emberwright-facing registry for editor tools that should live as docked,
/// floating, or canvas-overlay panels instead of replacing the central canvas.
///
/// This is intentionally data-only in the first pass. Existing Havenwild panels
/// can be migrated one at a time without changing their rendering/input code in
/// the same patch that introduces the registry.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub(crate) enum ToolPanelId {
    ResourceTree,
    AssetBrowser,
    SourceLibrary,
    AssetAuthority,
    CatalogHealth,
    FamilyCompleteness,
    UsageWhereUsed,
    LicenseAttribution,
    Quarantine,
    AtlasAssembly,
    Inspector,
    Properties,
    ToolProperties,
    ToolRailOverlay,
    LayerRailOverlay,
    TilePaletteOverlay,
    PieControlStripOverlay,
    SpriteTools,
    RasterLayers,
    AnimationTimeline,
    CharacterRig,
    CharacterPaperDoll,
    LogicGraph,
    NodePalette,
    SoundTimeline,
    Output,
    Problems,
    Build,
    Git,
    Activity,
    CortexChat,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub(crate) enum ToolPanelCategory {
    Resource,
    AssetLane,
    CanvasOverlay,
    Inspector,
    Sprite,
    Character,
    Logic,
    Sound,
    Diagnostics,
    Cortex,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub(crate) enum ToolPanelDockTarget {
    Left,
    Right,
    Bottom,
    Overlay,
    Floating,
    Hidden,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct ToolPanelDescriptor {
    pub id: ToolPanelId,
    pub stable_key: &'static str,
    pub label: &'static str,
    pub category: ToolPanelCategory,
    pub default_target: ToolPanelDockTarget,
    pub default_visible: bool,
    pub hides_during_pie: bool,
    pub legacy_workspace: Option<&'static str>,
}

impl ToolPanelDescriptor {
    pub const fn is_overlay(self) -> bool {
        matches!(self.default_target, ToolPanelDockTarget::Overlay)
    }

    pub const fn replaces_legacy_workspace(self) -> bool {
        self.legacy_workspace.is_some()
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct ToolPanelLayoutEntry {
    pub id: ToolPanelId,
    pub target: ToolPanelDockTarget,
    pub visible: bool,
}

pub(crate) const EMBERWRIGHT_TOOL_PANELS: &[ToolPanelDescriptor] = &[
    ToolPanelDescriptor { id: ToolPanelId::ResourceTree, stable_key: "resource.tree", label: "Resource Tree", category: ToolPanelCategory::Resource, default_target: ToolPanelDockTarget::Left, default_visible: true, hides_during_pie: true, legacy_workspace: None },
    ToolPanelDescriptor { id: ToolPanelId::AssetBrowser, stable_key: "asset.browser", label: "Asset Browser", category: ToolPanelCategory::AssetLane, default_target: ToolPanelDockTarget::Left, default_visible: true, hides_during_pie: true, legacy_workspace: Some("Assets") },
    ToolPanelDescriptor { id: ToolPanelId::SourceLibrary, stable_key: "asset.source_library", label: "Source Library", category: ToolPanelCategory::AssetLane, default_target: ToolPanelDockTarget::Right, default_visible: false, hides_during_pie: true, legacy_workspace: Some("Assets") },
    ToolPanelDescriptor { id: ToolPanelId::AssetAuthority, stable_key: "asset.authority", label: "Asset Authority", category: ToolPanelCategory::AssetLane, default_target: ToolPanelDockTarget::Right, default_visible: false, hides_during_pie: true, legacy_workspace: Some("Assets") },
    ToolPanelDescriptor { id: ToolPanelId::CatalogHealth, stable_key: "asset.catalog_health", label: "Catalog Health", category: ToolPanelCategory::AssetLane, default_target: ToolPanelDockTarget::Bottom, default_visible: false, hides_during_pie: true, legacy_workspace: Some("Assets") },
    ToolPanelDescriptor { id: ToolPanelId::FamilyCompleteness, stable_key: "asset.family_completeness", label: "Family Completeness", category: ToolPanelCategory::AssetLane, default_target: ToolPanelDockTarget::Right, default_visible: false, hides_during_pie: true, legacy_workspace: Some("Assets") },
    ToolPanelDescriptor { id: ToolPanelId::UsageWhereUsed, stable_key: "asset.where_used", label: "Where Used", category: ToolPanelCategory::AssetLane, default_target: ToolPanelDockTarget::Bottom, default_visible: false, hides_during_pie: true, legacy_workspace: Some("Assets") },
    ToolPanelDescriptor { id: ToolPanelId::LicenseAttribution, stable_key: "asset.license_attribution", label: "License / Attribution", category: ToolPanelCategory::AssetLane, default_target: ToolPanelDockTarget::Right, default_visible: false, hides_during_pie: true, legacy_workspace: Some("Assets") },
    ToolPanelDescriptor { id: ToolPanelId::Quarantine, stable_key: "asset.quarantine", label: "Quarantine", category: ToolPanelCategory::AssetLane, default_target: ToolPanelDockTarget::Bottom, default_visible: false, hides_during_pie: true, legacy_workspace: Some("Assets") },
    ToolPanelDescriptor { id: ToolPanelId::AtlasAssembly, stable_key: "asset.atlas_assembly", label: "Atlas Assembly", category: ToolPanelCategory::AssetLane, default_target: ToolPanelDockTarget::Floating, default_visible: false, hides_during_pie: true, legacy_workspace: Some("Assets") },
    ToolPanelDescriptor { id: ToolPanelId::Inspector, stable_key: "inspector", label: "Inspector", category: ToolPanelCategory::Inspector, default_target: ToolPanelDockTarget::Right, default_visible: true, hides_during_pie: true, legacy_workspace: None },
    ToolPanelDescriptor { id: ToolPanelId::Properties, stable_key: "properties", label: "Properties", category: ToolPanelCategory::Inspector, default_target: ToolPanelDockTarget::Right, default_visible: true, hides_during_pie: true, legacy_workspace: None },
    ToolPanelDescriptor { id: ToolPanelId::ToolProperties, stable_key: "tool.properties", label: "Tool Properties", category: ToolPanelCategory::Inspector, default_target: ToolPanelDockTarget::Right, default_visible: true, hides_during_pie: true, legacy_workspace: None },
    ToolPanelDescriptor { id: ToolPanelId::ToolRailOverlay, stable_key: "overlay.tool_rail", label: "Tool Rail", category: ToolPanelCategory::CanvasOverlay, default_target: ToolPanelDockTarget::Overlay, default_visible: true, hides_during_pie: true, legacy_workspace: None },
    ToolPanelDescriptor { id: ToolPanelId::LayerRailOverlay, stable_key: "overlay.layer_rail", label: "Layer Rail", category: ToolPanelCategory::CanvasOverlay, default_target: ToolPanelDockTarget::Overlay, default_visible: true, hides_during_pie: true, legacy_workspace: None },
    ToolPanelDescriptor { id: ToolPanelId::TilePaletteOverlay, stable_key: "overlay.tile_palette", label: "Tile Palette", category: ToolPanelCategory::CanvasOverlay, default_target: ToolPanelDockTarget::Overlay, default_visible: false, hides_during_pie: true, legacy_workspace: None },
    ToolPanelDescriptor { id: ToolPanelId::PieControlStripOverlay, stable_key: "overlay.pie_control_strip", label: "PIE Control Strip", category: ToolPanelCategory::CanvasOverlay, default_target: ToolPanelDockTarget::Overlay, default_visible: false, hides_during_pie: false, legacy_workspace: None },
    ToolPanelDescriptor { id: ToolPanelId::SpriteTools, stable_key: "sprite.tools", label: "Sprite Tools", category: ToolPanelCategory::Sprite, default_target: ToolPanelDockTarget::Left, default_visible: false, hides_during_pie: true, legacy_workspace: Some("Pixel") },
    ToolPanelDescriptor { id: ToolPanelId::RasterLayers, stable_key: "sprite.raster_layers", label: "Raster Layers", category: ToolPanelCategory::Sprite, default_target: ToolPanelDockTarget::Right, default_visible: false, hides_during_pie: true, legacy_workspace: Some("Pixel") },
    ToolPanelDescriptor { id: ToolPanelId::AnimationTimeline, stable_key: "animation.timeline", label: "Animation Timeline", category: ToolPanelCategory::Sprite, default_target: ToolPanelDockTarget::Bottom, default_visible: false, hides_during_pie: true, legacy_workspace: Some("Animation") },
    ToolPanelDescriptor { id: ToolPanelId::CharacterRig, stable_key: "character.rig", label: "Character Rig", category: ToolPanelCategory::Character, default_target: ToolPanelDockTarget::Right, default_visible: false, hides_during_pie: true, legacy_workspace: Some("Character") },
    ToolPanelDescriptor { id: ToolPanelId::CharacterPaperDoll, stable_key: "character.paper_doll", label: "Paper Doll", category: ToolPanelCategory::Character, default_target: ToolPanelDockTarget::Floating, default_visible: false, hides_during_pie: true, legacy_workspace: Some("Character") },
    ToolPanelDescriptor { id: ToolPanelId::LogicGraph, stable_key: "logic.graph", label: "Logic Graph", category: ToolPanelCategory::Logic, default_target: ToolPanelDockTarget::Floating, default_visible: false, hides_during_pie: true, legacy_workspace: Some("Logic") },
    ToolPanelDescriptor { id: ToolPanelId::NodePalette, stable_key: "logic.node_palette", label: "Node Palette", category: ToolPanelCategory::Logic, default_target: ToolPanelDockTarget::Left, default_visible: false, hides_during_pie: true, legacy_workspace: Some("Logic") },
    ToolPanelDescriptor { id: ToolPanelId::SoundTimeline, stable_key: "sound.timeline", label: "Sound Timeline", category: ToolPanelCategory::Sound, default_target: ToolPanelDockTarget::Bottom, default_visible: false, hides_during_pie: true, legacy_workspace: Some("Sound") },
    ToolPanelDescriptor { id: ToolPanelId::Output, stable_key: "diagnostics.output", label: "Output", category: ToolPanelCategory::Diagnostics, default_target: ToolPanelDockTarget::Bottom, default_visible: true, hides_during_pie: true, legacy_workspace: None },
    ToolPanelDescriptor { id: ToolPanelId::Problems, stable_key: "diagnostics.problems", label: "Problems", category: ToolPanelCategory::Diagnostics, default_target: ToolPanelDockTarget::Bottom, default_visible: false, hides_during_pie: true, legacy_workspace: None },
    ToolPanelDescriptor { id: ToolPanelId::Build, stable_key: "diagnostics.build", label: "Build", category: ToolPanelCategory::Diagnostics, default_target: ToolPanelDockTarget::Bottom, default_visible: false, hides_during_pie: true, legacy_workspace: None },
    ToolPanelDescriptor { id: ToolPanelId::Git, stable_key: "diagnostics.git", label: "Git", category: ToolPanelCategory::Diagnostics, default_target: ToolPanelDockTarget::Bottom, default_visible: false, hides_during_pie: true, legacy_workspace: None },
    ToolPanelDescriptor { id: ToolPanelId::Activity, stable_key: "diagnostics.activity", label: "Activity", category: ToolPanelCategory::Diagnostics, default_target: ToolPanelDockTarget::Bottom, default_visible: false, hides_during_pie: true, legacy_workspace: None },
    ToolPanelDescriptor { id: ToolPanelId::CortexChat, stable_key: "cortex.chat", label: "Cortex Chat", category: ToolPanelCategory::Cortex, default_target: ToolPanelDockTarget::Bottom, default_visible: false, hides_during_pie: true, legacy_workspace: None },
];

pub(crate) fn tool_panel_descriptors() -> &'static [ToolPanelDescriptor] {
    EMBERWRIGHT_TOOL_PANELS
}

pub(crate) fn find_tool_panel(stable_key: &str) -> Option<&'static ToolPanelDescriptor> {
    EMBERWRIGHT_TOOL_PANELS
        .iter()
        .find(|panel| panel.stable_key == stable_key)
}

pub(crate) fn default_tool_panel_layout() -> Vec<ToolPanelLayoutEntry> {
    EMBERWRIGHT_TOOL_PANELS
        .iter()
        .map(|panel| ToolPanelLayoutEntry {
            id: panel.id,
            target: panel.default_target,
            visible: panel.default_visible,
        })
        .collect()
}

pub(crate) fn panels_for_category(category: ToolPanelCategory) -> impl Iterator<Item = &'static ToolPanelDescriptor> {
    EMBERWRIGHT_TOOL_PANELS
        .iter()
        .filter(move |panel| panel.category == category)
}

pub(crate) fn panels_hidden_during_pie() -> impl Iterator<Item = &'static ToolPanelDescriptor> {
    EMBERWRIGHT_TOOL_PANELS
        .iter()
        .filter(|panel| panel.hides_during_pie)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashSet;

    #[test]
    fn panel_keys_are_stable_and_unique() {
        let mut keys = HashSet::new();
        for panel in tool_panel_descriptors() {
            assert!(!panel.stable_key.trim().is_empty());
            assert!(keys.insert(panel.stable_key), "duplicate panel key: {}", panel.stable_key);
        }
    }

    #[test]
    fn canvas_is_not_a_dockable_tool_panel() {
        assert!(find_tool_panel("canvas").is_none());
        assert!(find_tool_panel("room_canvas").is_none());
        assert!(find_tool_panel("game_canvas").is_none());
    }

    #[test]
    fn asset_workspace_is_split_into_asset_lane_panels() {
        let asset_panels: Vec<_> = panels_for_category(ToolPanelCategory::AssetLane).collect();
        assert!(asset_panels.iter().any(|panel| panel.id == ToolPanelId::AssetBrowser));
        assert!(asset_panels.iter().any(|panel| panel.id == ToolPanelId::SourceLibrary));
        assert!(asset_panels.iter().any(|panel| panel.id == ToolPanelId::AssetAuthority));
        assert!(asset_panels.iter().any(|panel| panel.id == ToolPanelId::AtlasAssembly));
        assert!(asset_panels.iter().all(|panel| panel.legacy_workspace == Some("Assets")));
    }

    #[test]
    fn normal_canvas_overlays_hide_during_pie_but_control_strip_stays() {
        let hidden: HashSet<_> = panels_hidden_during_pie().map(|panel| panel.id).collect();
        assert!(hidden.contains(&ToolPanelId::ToolRailOverlay));
        assert!(hidden.contains(&ToolPanelId::LayerRailOverlay));
        assert!(hidden.contains(&ToolPanelId::TilePaletteOverlay));
        assert!(!hidden.contains(&ToolPanelId::PieControlStripOverlay));
    }

    #[test]
    fn default_layout_keeps_primary_editor_frame_visible() {
        let layout = default_tool_panel_layout();
        assert!(layout.iter().any(|entry| entry.id == ToolPanelId::ResourceTree && entry.visible && entry.target == ToolPanelDockTarget::Left));
        assert!(layout.iter().any(|entry| entry.id == ToolPanelId::Inspector && entry.visible && entry.target == ToolPanelDockTarget::Right));
        assert!(layout.iter().any(|entry| entry.id == ToolPanelId::Output && entry.visible && entry.target == ToolPanelDockTarget::Bottom));
    }
}
