use super::editor_text::draw_editor_text;
use super::pixel_layer_rail::pixel_layer_actual_index;
use super::render_helpers::{draw_editor_widget_tone, WidgetTone};
use super::*;

pub(crate) const CANVAS_TOOL_RACK_WIDTH: f32 = 54.0;
pub(crate) const CANVAS_TOOL_RACK_COMPACT_WIDTH: f32 = 36.0;
pub(crate) const CANVAS_LAYER_RAIL_COMPACT_WIDTH: f32 = 28.0;
const RAIL_GAP: f32 = super::editor_theme::metrics::PANEL_GAP;
const HEADER_H: f32 = 28.0;
const ROW_H: f32 = 27.0;
const GROUP_HEADER_H: f32 = 18.0;
const EYE_ZONE_W: f32 = 28.0;
const THUMB_ZONE_W: f32 = 25.0;
const LOCK_ZONE_W: f32 = 28.0;
const LAYER_SCROLL_BUTTON_W: f32 = 20.0;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub(crate) enum CanvasLayerKind {
    Terrain,
    TerrainTransitions,
    Water,
    RoadsPaths,
    Vegetation,
    Resources,
    Structures,
    Furniture,
    Props,
    Characters,
    Triggers,
    Lighting,
    Atmosphere,
    Weather,
    SoundEmitters,
    Effects,
    Buildings,
    Objects,
    AuthoredPixels,
    Collision,
    Navigation,
    Zones,
    Links,
    Shelter,
    WaterSwim,
    SpawnPopulation,
    BuildabilityFarming,
    LogicBindings,
    StructuralLevels,
    SourceReference,
    AnimationFrames,
    AnimationAnchors,
    AnimationFootAnchor,
    AnimationShadowAnchor,
    AnimationSockets,
    AnimationHitboxes,
    AnimationHurtboxes,
    AnimationEvents,
    CharacterParts,
    PixelLayer,
    Interaction,
    Occlusion,
    LogicNodes,
    LogicConnections,
    SoundNodes,
    SoundConnections,
    SoundTimeline,
    UiLayout,
    UiControls,
    UiData,
    UiBehavior,
    UiPresentation,
    UiOverrides,
    Guides,
}

/// A14AA: the layer rail reflects resolved visual families, not storage
/// containers. Water and path tiles may live in the terrain map, but they
/// remain independently visible/editable layer families.
pub(crate) fn canvas_layer_kind_for_surface_tile(tile: TileKind) -> CanvasLayerKind {
    if tile.is_water() || matches!(tile, TileKind::ShoreFoam) {
        CanvasLayerKind::Water
    } else if matches!(tile, TileKind::Road | TileKind::StonePath | TileKind::MountainPath) {
        CanvasLayerKind::RoadsPaths
    } else if matches!(tile, TileKind::Cliff) {
        CanvasLayerKind::StructuralLevels
    } else if matches!(
        tile,
        TileKind::WoodFloor
            | TileKind::PlankFloor
            | TileKind::StoneFloor
            | TileKind::BrickFloor
            | TileKind::Wall
            | TileKind::Bridge
            | TileKind::CaveWall
    ) {
        CanvasLayerKind::Structures
    } else {
        CanvasLayerKind::Terrain
    }
}

/// World object presentation families are likewise semantic. Natural flora,
/// harvest resources, structural placeables, and ordinary props are not one
/// monolithic "objects" visibility switch.
pub(crate) fn canvas_layer_kind_for_stamp(stamp_key: &str, category: Option<&str>) -> CanvasLayerKind {
    let mut semantic = stamp_key.to_ascii_lowercase();
    if let Some(category) = category {
        semantic.push(' ');
        semantic.push_str(&category.to_ascii_lowercase());
    }
    if semantic.contains("water") || semantic.contains("pond") || semantic.contains("hydrolog") {
        CanvasLayerKind::Water
    } else if semantic.contains("road") || semantic.contains("path") {
        CanvasLayerKind::RoadsPaths
    } else if semantic.contains("cliff") || semantic.contains("elevation") {
        CanvasLayerKind::StructuralLevels
    } else if semantic.contains("building")
        || semantic.contains("structure")
        || semantic.contains("house")
        || semantic.contains("cottage")
        || semantic.contains("estate")
        || semantic.contains("roof")
        || semantic.contains("wall")
        || semantic.contains("floor")
        || semantic.contains("bridge")
        || semantic.contains("dock")
        || semantic.contains("door")
        || semantic.contains("stair")
        || semantic.contains("fence")
    {
        CanvasLayerKind::Structures
    } else {
        CanvasLayerKind::Objects
    }
}

pub(crate) fn canvas_layer_kind_for_world_object(kind: ObjectKind) -> CanvasLayerKind {
    match kind {
        ObjectKind::Tree
        | ObjectKind::Bush
        | ObjectKind::Mushroom
        | ObjectKind::Herb
        | ObjectKind::Stump
        | ObjectKind::Log => CanvasLayerKind::Vegetation,
        ObjectKind::Boulder | ObjectKind::OreNode => CanvasLayerKind::Resources,
        ObjectKind::Fence
        | ObjectKind::Door
        | ObjectKind::Stairs
        | ObjectKind::CaveEntrance
        | ObjectKind::Well
        | ObjectKind::GreenhouseMarker => CanvasLayerKind::Structures,
        _ => CanvasLayerKind::Objects,
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum CanvasLayerGroup {
    Surface,
    Content,
    Simulation,
    Overrides,
    Visual,
    Gameplay,
    Animation,
    Guides,
}

impl CanvasLayerGroup {
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Surface => "SURFACE",
            Self::Content => "CONTENT",
            Self::Simulation => "SIMULATION",
            Self::Overrides => "OVERRIDES",
            Self::Visual => "VISUAL",
            Self::Gameplay => "GAMEPLAY",
            Self::Animation => "ANIMATION",
            Self::Guides => "GUIDES",
        }
    }
}

#[derive(Clone, Debug)]
pub(crate) struct CanvasLayerDescriptor {
    pub label: String,
    pub kind: CanvasLayerKind,
    pub group: CanvasLayerGroup,
    pub visible: bool,
    pub locked: bool,
    pub active: bool,
    pub dirty: bool,
}

impl EditorApp {
    fn game_canvas_uses_semantic_layer_authority(&self) -> bool {
        !self.game_canvas_ui_active()
            && matches!(self.viewport_mode, EditorViewportMode::SceneMap | EditorViewportMode::SceneRectangles)
    }

    pub(crate) fn canvas_layer_kind_visible(&self, kind: CanvasLayerKind) -> bool {
        if self.game_canvas_uses_semantic_layer_authority() {
            !self.canvas_hidden_layer_kinds.contains(&kind)
        } else {
            true
        }
    }

    pub(crate) fn canvas_layer_kind_selected(&self, kind: CanvasLayerKind) -> bool {
        self.game_canvas_uses_semantic_layer_authority()
            && self.canvas_selected_layer_kinds.contains(&kind)
    }

    pub(crate) fn set_game_canvas_layer_visibility(
        &mut self,
        kind: CanvasLayerKind,
        visible: bool,
    ) {
        if visible {
            self.canvas_hidden_layer_kinds.remove(&kind);
        } else {
            self.canvas_hidden_layer_kinds.insert(kind);
        }
        if kind == CanvasLayerKind::Collision {
            self.show_collision_overlay = visible;
        }
    }

    pub(crate) fn toggle_game_canvas_layer_visibility(&mut self, kind: CanvasLayerKind) -> bool {
        let visible = !self.canvas_layer_kind_visible(kind);
        self.set_game_canvas_layer_visibility(kind, visible);
        visible
    }

    fn toggle_game_canvas_layer_selection(&mut self, kind: CanvasLayerKind) -> bool {
        let selected = if self.canvas_selected_layer_kinds.remove(&kind) {
            false
        } else {
            self.canvas_selected_layer_kinds.insert(kind);
            true
        };
        if selected {
            self.canvas_layer_context_override = Some(kind);
        } else if self.canvas_layer_context_override == Some(kind) {
            // Fall back to descriptor order through active_canvas_layer_kind();
            // HashSet iteration must never choose the next primary context.
            self.canvas_layer_context_override = None;
        }
        selected
    }

    pub(crate) fn selected_game_canvas_layer_count(&self) -> usize {
        if self.game_canvas_uses_semantic_layer_authority() {
            self.canvas_selected_layer_kinds.len()
        } else {
            0
        }
    }

    pub(crate) fn active_canvas_layer_descriptors(&self) -> Vec<CanvasLayerDescriptor> {
        if self.game_canvas_ui_active() {
            use haven_authoring::UiAuthoringLane as L;
            let active = self.game_canvas_ui.active_lane;
            return vec![
                CanvasLayerDescriptor { label: "Layout".into(), kind: CanvasLayerKind::UiLayout, group: CanvasLayerGroup::Visual, visible: true, locked: false, active: active == L::Layout, dirty: self.game_canvas_ui.dirty },
                CanvasLayerDescriptor { label: "Controls".into(), kind: CanvasLayerKind::UiControls, group: CanvasLayerGroup::Visual, visible: true, locked: false, active: active == L::Controls, dirty: self.game_canvas_ui.dirty },
                CanvasLayerDescriptor { label: "Data".into(), kind: CanvasLayerKind::UiData, group: CanvasLayerGroup::Gameplay, visible: true, locked: false, active: active == L::Data, dirty: self.game_canvas_ui.dirty },
                CanvasLayerDescriptor { label: "Behavior".into(), kind: CanvasLayerKind::UiBehavior, group: CanvasLayerGroup::Gameplay, visible: true, locked: false, active: active == L::Behavior, dirty: self.game_canvas_ui.dirty },
                CanvasLayerDescriptor { label: "Presentation".into(), kind: CanvasLayerKind::UiPresentation, group: CanvasLayerGroup::Visual, visible: true, locked: false, active: active == L::Presentation, dirty: self.game_canvas_ui.dirty },
                CanvasLayerDescriptor { label: "Overrides".into(), kind: CanvasLayerKind::UiOverrides, group: CanvasLayerGroup::Overrides, visible: true, locked: false, active: active == L::Overrides, dirty: self.game_canvas_ui.dirty },
            ];
        }
        let mut rows = match self.viewport_mode {
            EditorViewportMode::SceneMap => vec![
                self.scene_layer_grouped("Terrain", CanvasLayerKind::Terrain, SceneLayerMode::Terrain, CanvasLayerGroup::Surface),
                CanvasLayerDescriptor { label: "Elevation / Cliffs".into(), kind: CanvasLayerKind::StructuralLevels, group: CanvasLayerGroup::Surface, visible: true, locked: true, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Water / Hydrology".into(), kind: CanvasLayerKind::Water, group: CanvasLayerGroup::Surface, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Roads & Paths".into(), kind: CanvasLayerKind::RoadsPaths, group: CanvasLayerGroup::Surface, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Structures & Buildings".into(), kind: CanvasLayerKind::Structures, group: CanvasLayerGroup::Content, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Objects & Props".into(), kind: CanvasLayerKind::Objects, group: CanvasLayerGroup::Content, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "NPCs & Creatures".into(), kind: CanvasLayerKind::Characters, group: CanvasLayerGroup::Content, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Lighting".into(), kind: CanvasLayerKind::Lighting, group: CanvasLayerGroup::Simulation, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Atmosphere".into(), kind: CanvasLayerKind::Atmosphere, group: CanvasLayerGroup::Simulation, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Weather".into(), kind: CanvasLayerKind::Weather, group: CanvasLayerGroup::Simulation, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Collision".into(), kind: CanvasLayerKind::Collision, group: CanvasLayerGroup::Simulation, visible: self.show_collision_overlay, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Navigation".into(), kind: CanvasLayerKind::Navigation, group: CanvasLayerGroup::Simulation, visible: true, locked: false, active: false, dirty: false },
                self.scene_layer_grouped("Gameplay", CanvasLayerKind::Zones, SceneLayerMode::Zones, CanvasLayerGroup::Simulation),
                CanvasLayerDescriptor { label: "Visual Overrides".into(), kind: CanvasLayerKind::AuthoredPixels, group: CanvasLayerGroup::Overrides, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Generated / Derived".into(), kind: CanvasLayerKind::SourceReference, group: CanvasLayerGroup::Overrides, visible: true, locked: true, active: false, dirty: false },
            ],
            EditorViewportMode::SceneRectangles => vec![
                self.world_layer_grouped("Terrain", CanvasLayerKind::Terrain, WorldLayerMode::Terrain, self.world_layer_mode == WorldLayerMode::Terrain && self.canvas_layer_context_override.is_none(), CanvasLayerGroup::Surface),
                self.world_layer_grouped("Elevation", CanvasLayerKind::StructuralLevels, WorldLayerMode::StructuralLevels, self.world_layer_mode == WorldLayerMode::StructuralLevels, CanvasLayerGroup::Surface),
                CanvasLayerDescriptor { label: "Hydrology".into(), kind: CanvasLayerKind::Water, group: CanvasLayerGroup::Surface, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Roads & Paths".into(), kind: CanvasLayerKind::RoadsPaths, group: CanvasLayerGroup::Surface, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Vegetation".into(), kind: CanvasLayerKind::Vegetation, group: CanvasLayerGroup::Content, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Resources".into(), kind: CanvasLayerKind::Resources, group: CanvasLayerGroup::Content, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Structures & Buildings".into(), kind: CanvasLayerKind::Structures, group: CanvasLayerGroup::Content, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Objects & Props".into(), kind: CanvasLayerKind::Objects, group: CanvasLayerGroup::Content, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "NPCs & Creatures".into(), kind: CanvasLayerKind::SpawnPopulation, group: CanvasLayerGroup::Content, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Lighting".into(), kind: CanvasLayerKind::Lighting, group: CanvasLayerGroup::Simulation, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Atmosphere".into(), kind: CanvasLayerKind::Atmosphere, group: CanvasLayerGroup::Simulation, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Weather".into(), kind: CanvasLayerKind::Weather, group: CanvasLayerGroup::Simulation, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Collision".into(), kind: CanvasLayerKind::Collision, group: CanvasLayerGroup::Simulation, visible: self.show_collision_overlay, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Navigation".into(), kind: CanvasLayerKind::Navigation, group: CanvasLayerGroup::Simulation, visible: true, locked: false, active: false, dirty: false },
                self.world_layer_grouped("Gameplay", CanvasLayerKind::Zones, WorldLayerMode::Zones, self.world_layer_mode == WorldLayerMode::Zones, CanvasLayerGroup::Simulation),
                CanvasLayerDescriptor { label: "Visual Overrides".into(), kind: CanvasLayerKind::AuthoredPixels, group: CanvasLayerGroup::Overrides, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Generated / Derived".into(), kind: CanvasLayerKind::SourceReference, group: CanvasLayerGroup::Overrides, visible: true, locked: true, active: false, dirty: false },
            ],
            EditorViewportMode::PixelStudio => {
                let mut rows = Vec::new();
                if let Some(document) = self.pixel_studio.document.as_ref() {
                    for (index, layer) in document.layers().iter().enumerate().rev() {
                        let kind = if layer.metadata.name.contains("Collision") {
                            CanvasLayerKind::Collision
                        } else if layer.metadata.locked && layer.metadata.name == "Generated Terrain" {
                            CanvasLayerKind::Terrain
                        } else if layer.metadata.locked && layer.metadata.name == "Terrain Transitions" {
                            CanvasLayerKind::TerrainTransitions
                        } else if layer.metadata.locked && layer.metadata.name == "Structural Terrain / Cliffs" {
                            CanvasLayerKind::StructuralLevels
                        } else if layer.metadata.locked && layer.metadata.name == "Buildings" {
                            CanvasLayerKind::Buildings
                        } else if layer.metadata.locked && layer.metadata.name == "Objects & Stamps" {
                            CanvasLayerKind::Objects
                        } else if layer.metadata.locked || layer.metadata.name.contains("Reference") || layer.metadata.name.contains("Generated") {
                            CanvasLayerKind::SourceReference
                        } else {
                            CanvasLayerKind::PixelLayer
                        };
                        let group = if matches!(kind, CanvasLayerKind::Collision | CanvasLayerKind::Navigation | CanvasLayerKind::Shelter) {
                            CanvasLayerGroup::Gameplay
                        } else if matches!(kind, CanvasLayerKind::SourceReference) {
                            CanvasLayerGroup::Guides
                        } else {
                            CanvasLayerGroup::Visual
                        };
                        rows.push(CanvasLayerDescriptor {
                            label: layer.metadata.name.clone(),
                            kind,
                            group,
                            visible: layer.metadata.visible,
                            locked: layer.metadata.locked,
                            active: index == document.active_layer_index(),
                            dirty: document.dirty,
                        });
                    }
                }
                rows
            }
            EditorViewportMode::AnimationStudio => vec![
                CanvasLayerDescriptor { label: "Frame Artwork".into(), kind: CanvasLayerKind::AnimationFrames, group: CanvasLayerGroup::Visual, visible: true, locked: false, active: true, dirty: self.animation_studio.document.as_ref().is_some_and(|d| d.dirty) },
                CanvasLayerDescriptor { label: "Pivot / Origin".into(), kind: CanvasLayerKind::AnimationAnchors, group: CanvasLayerGroup::Animation, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Foot / Ground Anchor".into(), kind: CanvasLayerKind::AnimationFootAnchor, group: CanvasLayerGroup::Animation, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Shadow Anchor".into(), kind: CanvasLayerKind::AnimationShadowAnchor, group: CanvasLayerGroup::Animation, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Sockets".into(), kind: CanvasLayerKind::AnimationSockets, group: CanvasLayerGroup::Animation, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Frame Events".into(), kind: CanvasLayerKind::AnimationEvents, group: CanvasLayerGroup::Animation, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Hitboxes".into(), kind: CanvasLayerKind::AnimationHitboxes, group: CanvasLayerGroup::Gameplay, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Hurtboxes".into(), kind: CanvasLayerKind::AnimationHurtboxes, group: CanvasLayerGroup::Gameplay, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Source Reference".into(), kind: CanvasLayerKind::SourceReference, group: CanvasLayerGroup::Guides, visible: true, locked: true, active: false, dirty: false },
            ],
            EditorViewportMode::CharacterStudio => {
                let semantic_rows = self.character_studio.semantic_layer_rows();
                let selected = self.character_studio.selected_semantic_layer_index();
                let mut rows = semantic_rows.into_iter().enumerate().map(|(index, layer)| {
                    let coverage = if layer.empty_slot {
                        "○"
                    } else if layer.presentation_note.is_some() {
                        "⊘"
                    } else if layer.current_action_available {
                        "✓"
                    } else {
                        "⚠"
                    };
                    let detail = layer
                        .presentation_note
                        .as_deref()
                        .map(|_| " · occluded/conflict")
                        .unwrap_or("");
                    CanvasLayerDescriptor {
                        label: format!("{} {} · {}{}", coverage, layer.group, layer.label, detail),
                        kind: CanvasLayerKind::CharacterParts,
                        group: CanvasLayerGroup::Visual,
                        visible: layer.preview_visible,
                        locked: layer.locked_order,
                        active: index == selected,
                        dirty: false,
                    }
                }).collect::<Vec<_>>();
                if rows.is_empty() {
                    rows.push(CanvasLayerDescriptor { label: "Character Recipe (empty)".into(), kind: CanvasLayerKind::CharacterParts, group: CanvasLayerGroup::Visual, visible: true, locked: true, active: true, dirty: false });
                }
                rows.push(CanvasLayerDescriptor { label: "Attachment / Sockets".into(), kind: CanvasLayerKind::AnimationSockets, group: CanvasLayerGroup::Animation, visible: true, locked: false, active: false, dirty: false });
                rows.push(CanvasLayerDescriptor { label: "Source / zPos Diagnostics".into(), kind: CanvasLayerKind::SourceReference, group: CanvasLayerGroup::Guides, visible: true, locked: true, active: false, dirty: false });
                rows
            },
            EditorViewportMode::LogicStudio => vec![
                CanvasLayerDescriptor { label: "Behavior Nodes".into(), kind: CanvasLayerKind::LogicNodes, group: CanvasLayerGroup::Gameplay, visible: true, locked: false, active: true, dirty: self.logic_studio.dirty },
                CanvasLayerDescriptor { label: "Connections".into(), kind: CanvasLayerKind::LogicConnections, group: CanvasLayerGroup::Gameplay, visible: true, locked: false, active: false, dirty: self.logic_studio.dirty },
                CanvasLayerDescriptor { label: "Object / Scene Bindings".into(), kind: CanvasLayerKind::LogicBindings, group: CanvasLayerGroup::Gameplay, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Runtime Debug".into(), kind: CanvasLayerKind::Guides, group: CanvasLayerGroup::Guides, visible: true, locked: true, active: false, dirty: false },
            ],
            EditorViewportMode::SoundStudio => vec![
                CanvasLayerDescriptor { label: "Audio Nodes".into(), kind: CanvasLayerKind::SoundNodes, group: CanvasLayerGroup::Visual, visible: true, locked: false, active: true, dirty: self.sound_studio.dirty },
                CanvasLayerDescriptor { label: "Audio Connections".into(), kind: CanvasLayerKind::SoundConnections, group: CanvasLayerGroup::Visual, visible: true, locked: false, active: false, dirty: self.sound_studio.dirty },
                CanvasLayerDescriptor { label: "MIDI / Timeline".into(), kind: CanvasLayerKind::SoundTimeline, group: CanvasLayerGroup::Animation, visible: true, locked: false, active: false, dirty: self.sound_studio.dirty },
                CanvasLayerDescriptor { label: "Meters / References".into(), kind: CanvasLayerKind::Guides, group: CanvasLayerGroup::Guides, visible: true, locked: true, active: false, dirty: false },
            ],
            EditorViewportMode::RegionGraph => vec![
                CanvasLayerDescriptor { label: "Overworld Map".into(), kind: CanvasLayerKind::Terrain, group: CanvasLayerGroup::Visual, visible: true, locked: true, active: true, dirty: false },
                CanvasLayerDescriptor { label: "Scene Cards".into(), kind: CanvasLayerKind::Buildings, group: CanvasLayerGroup::Visual, visible: true, locked: false, active: false, dirty: false },
                CanvasLayerDescriptor { label: "Route Links".into(), kind: CanvasLayerKind::Links, group: CanvasLayerGroup::Gameplay, visible: true, locked: false, active: false, dirty: false },
            ],
            EditorViewportMode::SceneBank => vec![
                CanvasLayerDescriptor { label: "Scene Cards".into(), kind: CanvasLayerKind::Buildings, group: CanvasLayerGroup::Visual, visible: true, locked: false, active: true, dirty: false },
                CanvasLayerDescriptor { label: "Links".into(), kind: CanvasLayerKind::Links, group: CanvasLayerGroup::Gameplay, visible: true, locked: false, active: false, dirty: false },
            ],
        };
        if self.game_canvas_uses_semantic_layer_authority() {
            let has_multi_selection = !self.canvas_selected_layer_kinds.is_empty();
            for row in &mut rows {
                row.visible = !self.canvas_hidden_layer_kinds.contains(&row.kind);
                if has_multi_selection {
                    row.active = self.canvas_layer_kind_selected(row.kind);
                }
            }
        } else if let Some(active_kind) = self.canvas_layer_context_override {
            if rows.iter().any(|row| row.kind == active_kind) {
                for row in &mut rows {
                    row.active = row.kind == active_kind;
                }
            }
        }
        rows
    }

    fn scene_layer(&self, label: &str, kind: CanvasLayerKind, mode: SceneLayerMode) -> CanvasLayerDescriptor {
        let state = self.scene_layers[scene_layer_index(mode)];
        CanvasLayerDescriptor { label: label.into(), kind, group: if matches!(kind, CanvasLayerKind::Zones | CanvasLayerKind::Links | CanvasLayerKind::Collision | CanvasLayerKind::Navigation | CanvasLayerKind::Shelter) { CanvasLayerGroup::Gameplay } else { CanvasLayerGroup::Visual }, visible: state.visible, locked: state.locked, active: self.scene_layer_mode == mode, dirty: false }
    }

    fn scene_layer_grouped(&self, label: &str, kind: CanvasLayerKind, mode: SceneLayerMode, group: CanvasLayerGroup) -> CanvasLayerDescriptor {
        let mut row = self.scene_layer(label, kind, mode);
        row.group = group;
        row
    }

    fn world_layer(&self, label: &str, kind: CanvasLayerKind, _mode: WorldLayerMode, active: bool) -> CanvasLayerDescriptor {
        CanvasLayerDescriptor { label: label.into(), kind, group: if matches!(kind, CanvasLayerKind::Zones | CanvasLayerKind::Links | CanvasLayerKind::Collision | CanvasLayerKind::Navigation | CanvasLayerKind::Shelter | CanvasLayerKind::StructuralLevels) { CanvasLayerGroup::Gameplay } else { CanvasLayerGroup::Visual }, visible: true, locked: false, active, dirty: false }
    }

    fn world_layer_grouped(&self, label: &str, kind: CanvasLayerKind, mode: WorldLayerMode, active: bool, group: CanvasLayerGroup) -> CanvasLayerDescriptor {
        let mut row = self.world_layer(label, kind, mode, active);
        row.group = group;
        row
    }

    pub(crate) fn canvas_authoring_ruler_gutter(&self) -> f32 {
        // W72D: rulers belong to the canvas itself. The dedicated Tool Rail and
        // Layers panel live to the left of the canvas and therefore never add
        // another ruler/layout gutter between Layers and the authored surface.
        0.0
    }

    /// W72D locked GUI geometry: Tool Rail is a dedicated left column outside
    /// the canvas. Its width is real shell geometry, not an overlay width.
    pub(crate) fn canvas_tool_rack_width(&self) -> f32 {
        if self.workspace_shell.canvas_tool_rail_collapsed {
            CANVAS_TOOL_RACK_COMPACT_WIDTH
        } else {
            CANVAS_TOOL_RACK_WIDTH
        }
    }

    pub(crate) fn canvas_layer_rail_expanded_width(&self) -> f32 {
        self.workspace_shell.canvas_layer_rail_width.clamp(132.0, 480.0)
    }

    /// W72D locked GUI geometry: Layers is the dedicated panel immediately to
    /// the right of Tool Rail and also participates in shell geometry.
    pub(crate) fn canvas_layer_rail_width(&self) -> f32 {
        if self.workspace_shell.canvas_layer_rail_collapsed {
            CANVAS_LAYER_RAIL_COMPACT_WIDTH
        } else {
            self.canvas_layer_rail_expanded_width()
        }
    }

    pub(crate) fn canvas_authoring_left_inset(&self) -> f32 {
        // A14X restores the already-locked W72D geometry: Tool Rail and Layers are
        // real sibling panels outside the authored canvas. Neither is allowed to
        // cover document tabs, rulers, canvas titles, terrain, or pointer input.
        self.canvas_tool_rack_width()
            + RAIL_GAP
            + self.canvas_layer_rail_width()
            + RAIL_GAP
            + self.canvas_authoring_ruler_gutter()
    }

    /// Tool Rail and Layers use the complete workspace-content height so their
    /// top/bottom borders align exactly with the adjacent canvas.
    pub(crate) fn canvas_overlay_surface_rect(&self) -> Rect {
        // Exact shell bounds: Tool Rail, Layers, Canvas, and Right Dock share
        // the same body top/bottom baseline with no one-off vertical inset.
        self.main_viewport_rect()
    }

    pub(crate) fn canvas_content_host_rect(&self) -> Rect {
        self.canvas_workspace_layout().workspace_body
    }

    pub(crate) fn canvas_layer_rail_rect(&self) -> Rect {
        let host = self.canvas_overlay_surface_rect();
        let tool_w = self.canvas_tool_rack_width();
        let x = host.x + tool_w + RAIL_GAP + self.canvas_authoring_ruler_gutter();
        // A14X: Layers owns a complete, independent panel surface aligned with
        // Tool Rail and CanvasWorkspace. Vertical offsets are forbidden because
        // they recreate an overlay that collides with top-of-canvas chrome.
        Rect::new(x, host.y, self.canvas_layer_rail_width(), host.h)
    }

    pub(crate) fn active_canvas_layer_kind(&self) -> Option<CanvasLayerKind> {
        if self.game_canvas_uses_semantic_layer_authority() {
            if let Some(primary) = self.canvas_layer_context_override {
                if self.canvas_selected_layer_kinds.contains(&primary) {
                    return Some(primary);
                }
            }
        }
        self.active_canvas_layer_descriptors()
            .into_iter()
            .find(|row| row.active)
            .map(|row| row.kind)
    }

    pub(crate) fn active_canvas_layer_locked(&self) -> bool {
        self.active_canvas_layer_descriptors()
            .into_iter()
            .find(|row| row.active)
            .is_some_and(|row| row.locked)
    }

    /// R35: layer context, tools, assets, inspector, and help all pivot from the
    /// same semantic selection. This routine only changes browser context; it
    /// never arms a mutating tool.
    fn sync_asset_browser_for_canvas_layer(&mut self, kind: CanvasLayerKind) {
        use haven_assets::asset_palette::AssetPaletteCategory as C;
        let category = match kind {
            CanvasLayerKind::Terrain => Some(C::Terrain),
            CanvasLayerKind::TerrainTransitions => Some(C::Terrain),
            CanvasLayerKind::Water | CanvasLayerKind::WaterSwim => Some(C::Water),
            CanvasLayerKind::RoadsPaths => Some(C::Paths),
            CanvasLayerKind::StructuralLevels => Some(C::Elevation),
            CanvasLayerKind::Vegetation => Some(C::Nature),
            CanvasLayerKind::Resources => Some(C::Resources),
            CanvasLayerKind::Structures | CanvasLayerKind::Buildings => Some(C::Props),
            CanvasLayerKind::Furniture => Some(C::Furniture),
            CanvasLayerKind::Props | CanvasLayerKind::Objects => Some(C::Objects),
            CanvasLayerKind::Lighting => Some(C::Lighting),
            CanvasLayerKind::Atmosphere | CanvasLayerKind::Weather | CanvasLayerKind::Effects => Some(C::Effects),
            CanvasLayerKind::BuildabilityFarming => Some(C::Farm),
            _ => None,
        };
        if let Some(category) = category {
            self.asset_category = category;
            self.asset_list_offset = 0;
        }
    }

    pub(crate) fn draw_canvas_layer_rail(&self) {
        let rows = self.active_canvas_layer_descriptors();
        if rows.is_empty() {
            return;
        }
        let rect = self.canvas_layer_rail_rect();
        // A14X: Layers is a dedicated panel, not text painted over the world.
        draw_rectangle(rect.x, rect.y, rect.w, rect.h, editor_theme::colors::PANEL_BG);
        draw_rectangle_lines(
            rect.x,
            rect.y,
            rect.w,
            rect.h,
            1.0,
            editor_theme::colors::BORDER_STRONG,
        );
        draw_rectangle(
            rect.x + 1.0,
            rect.y + 1.0,
            (rect.w - 2.0).max(1.0),
            (HEADER_H - 1.0).max(1.0),
            editor_theme::colors::PANEL_HEADER,
        );

        let compact = self.workspace_shell.canvas_layer_rail_collapsed;
        let toggle = Rect::new(rect.x + 3.0, rect.y + 3.0, (rect.w - 6.0).min(24.0), HEADER_H - 6.0);
        draw_editor_widget_tone(toggle, "", false, WidgetTone::Quiet);
        draw_layer_chevron_icon(toggle, compact, editor_theme::colors::TEXT_SECONDARY);
        if compact {
            draw_editor_text("L", rect.x + 9.0, rect.y + 48.0, 11.0, editor_theme::colors::TEXT_SECONDARY);
            return;
        }

        draw_editor_text("LAYERS", rect.x + 34.0, rect.y + 18.0, 9.5, editor_theme::colors::TEXT_DISABLED);
        let max_scroll = rows.len().saturating_sub(1);
        let scroll_up = canvas_layer_scroll_up_rect(rect);
        let scroll_down = canvas_layer_scroll_down_rect(rect);
        let can_up = self.workspace_shell.canvas_layer_scroll > 0;
        let can_down = self.workspace_shell.canvas_layer_scroll < max_scroll;
        draw_editor_widget_tone(scroll_up, "", false, if can_up { WidgetTone::Quiet } else { WidgetTone::Disabled });
        draw_layer_scroll_icon(scroll_up, true, if can_up { editor_theme::colors::TEXT_SECONDARY } else { editor_theme::colors::TEXT_DISABLED });
        draw_editor_widget_tone(scroll_down, "", false, if can_down { WidgetTone::Quiet } else { WidgetTone::Disabled });
        draw_layer_scroll_icon(scroll_down, false, if can_down { editor_theme::colors::TEXT_SECONDARY } else { editor_theme::colors::TEXT_DISABLED });

        let mouse = vec2(mouse_position().0, mouse_position().1);
        let layout = canvas_layer_row_layout(
            &rows,
            rect,
            self.pixel_layer_footer_reserved(),
            self.workspace_shell.canvas_layer_scroll,
        );
        let mut last_group = None;
        for (index, row_rect) in &layout {
            let row = &rows[*index];
            if last_group != Some(row.group) {
                let header_y = row_rect.y - GROUP_HEADER_H;
                draw_editor_text(row.group.label(), rect.x + 9.0, header_y + 13.0, 9.5, editor_theme::colors::TEXT_DISABLED);
                last_group = Some(row.group);
            }
            let hovered = row_rect.contains(mouse);
            if row.active {
                draw_rectangle(row_rect.x, row_rect.y, row_rect.w, row_rect.h, Color::new(0.12, 0.27, 0.42, 0.82));
            } else if hovered {
                draw_rectangle(row_rect.x, row_rect.y, row_rect.w, row_rect.h, Color::new(0.10, 0.10, 0.10, 0.72));
            }

            let eye_rect = Rect::new(row_rect.x, row_rect.y, EYE_ZONE_W, row_rect.h);
            let lock_rect = Rect::new(row_rect.x + row_rect.w - LOCK_ZONE_W, row_rect.y, LOCK_ZONE_W, row_rect.h);
            // A14AA: visibility is a static, fixed control. It must not appear
            // only on hover/selection because visibility and edit selection are
            // intentionally independent authorities.
            let eye_center = vec2(eye_rect.x + eye_rect.w * 0.5, eye_rect.y + eye_rect.h * 0.5);
            draw_circle_lines(
                eye_center.x,
                eye_center.y,
                6.0,
                1.5,
                if row.visible { editor_theme::colors::TEXT_PRIMARY } else { editor_theme::colors::TEXT_SECONDARY },
            );
            if row.visible {
                draw_circle(eye_center.x, eye_center.y, 3.0, editor_theme::colors::TEXT_PRIMARY);
            }
            if hovered || row.active || row.locked {
                draw_lock_icon(lock_rect, row.locked);
            }

            let thumb_rect = Rect::new(eye_rect.x + eye_rect.w + 2.0, row_rect.y + 3.0, THUMB_ZONE_W - 5.0, row_rect.h - 6.0);
            draw_layer_kind_badge(row.kind, thumb_rect, row.active);
            let label_x = thumb_rect.x + thumb_rect.w + 4.0;
            let label_w = (lock_rect.x - label_x - 4.0).max(1.0);
            let display_label = if row.dirty { format!("{} *", row.label) } else { row.label.clone() };
            draw_scissored_text(
                &display_label,
                label_x,
                row_rect.y + 18.0,
                label_w,
                11.5,
                if row.locked && !row.active { editor_theme::colors::TEXT_SECONDARY } else { editor_theme::colors::TEXT_PRIMARY },
            );
        }
        if let Some(drag) = self.pixel_layer_drag {
            if self.viewport_mode == EditorViewportMode::PixelStudio {
                if let Some((_, target_rect)) = layout.iter().find(|(index, _)| *index == drag.target_display_index) {
                    let y = if drag.target_display_index > drag.source_display_index { target_rect.y + target_rect.h } else { target_rect.y };
                    draw_line(target_rect.x + 2.0, y, target_rect.x + target_rect.w - 2.0, y, 2.0, editor_theme::colors::ACCENT_HOVER);
                }
            }
        }
        self.draw_pixel_layer_footer(rect);
    }

    pub(crate) fn canvas_layer_tooltip_request(&self) -> Option<(Rect, String)> {
        let rect = self.canvas_layer_rail_rect();
        let mouse = vec2(mouse_position().0, mouse_position().1);
        if !rect.contains(mouse) { return None; }
        let toggle = Rect::new(rect.x + 3.0, rect.y + 3.0, (rect.w - 6.0).min(24.0), HEADER_H - 6.0);
        if toggle.contains(mouse) { return Some((toggle, if self.workspace_shell.canvas_layer_rail_collapsed { "Expand Layer Rail" } else { "Collapse Layer Rail" }.to_string())); }
        if self.workspace_shell.canvas_layer_rail_collapsed { return None; }
        if canvas_layer_scroll_up_rect(rect).contains(mouse) { return Some((canvas_layer_scroll_up_rect(rect), "Scroll layers up".to_string())); }
        if canvas_layer_scroll_down_rect(rect).contains(mouse) { return Some((canvas_layer_scroll_down_rect(rect), "Scroll layers down".to_string())); }
        let rows = self.active_canvas_layer_descriptors();
        for (index, row_rect) in canvas_layer_row_layout(&rows, rect, self.pixel_layer_footer_reserved(), self.workspace_shell.canvas_layer_scroll) {
            if row_rect.contains(mouse) {
                if let Some(row) = rows.get(index) {
                    return Some((row_rect, format!("{} layer • click name to toggle edit selection (multi-select) • left circle toggles visibility • lock toggles editing", row.label)));
                }
            }
        }
        None
    }

    pub(crate) fn handle_canvas_layer_rail_click(&mut self, mx: f32, my: f32) -> bool {
        let rect = self.canvas_layer_rail_rect();
        let p = vec2(mx, my);
        if self.pixel_layer_menu_anchor.is_some() && self.handle_pixel_layer_footer_click(p, rect) {
            return true;
        }
        if !rect.contains(p) { return false; }
        let toggle = Rect::new(rect.x + 3.0, rect.y + 3.0, (rect.w - 6.0).min(24.0), HEADER_H - 6.0);
        if toggle.contains(p) {
            self.workspace_shell.canvas_layer_rail_collapsed = !self.workspace_shell.canvas_layer_rail_collapsed;
            let _ = self.workspace_shell.save_default();
            self.status_message = if self.workspace_shell.canvas_layer_rail_collapsed { "Layer rail collapsed".to_string() } else { "Layer rail expanded".to_string() };
            return true;
        }
        if self.workspace_shell.canvas_layer_rail_collapsed { return true; }
        if canvas_layer_scroll_up_rect(rect).contains(p) {
            self.workspace_shell.canvas_layer_scroll = self.workspace_shell.canvas_layer_scroll.saturating_sub(1);
            let _ = self.workspace_shell.save_default();
            return true;
        }
        if canvas_layer_scroll_down_rect(rect).contains(p) {
            let max_scroll = self.active_canvas_layer_descriptors().len().saturating_sub(1);
            self.workspace_shell.canvas_layer_scroll = (self.workspace_shell.canvas_layer_scroll + 1).min(max_scroll);
            let _ = self.workspace_shell.save_default();
            return true;
        }
        if my < rect.y + HEADER_H { return true; }
        if self.handle_pixel_layer_footer_click(p, rect) { return true; }
        let rows = self.active_canvas_layer_descriptors();
        let Some((index, _row_rect)) = canvas_layer_row_layout(
            &rows,
            rect,
            self.pixel_layer_footer_reserved(),
            self.workspace_shell.canvas_layer_scroll,
        )
            .into_iter()
            .find(|(_, row_rect)| row_rect.contains(p)) else { return true; };
        let Some(row) = rows.get(index) else { return true; };
        let eye_zone = mx <= rect.x + 3.0 + EYE_ZONE_W;
        let lock_zone = mx >= rect.x + rect.w - 3.0 - LOCK_ZONE_W;
        if self.game_canvas_uses_semantic_layer_authority() && eye_zone {
            let visible = self.toggle_game_canvas_layer_visibility(row.kind);
            self.status_message = format!(
                "{} visibility {} | editing selection unchanged",
                row.label,
                if visible { "shown" } else { "hidden" },
            );
            return true;
        }
        if self.game_canvas_uses_semantic_layer_authority() && !lock_zone {
            let selected = self.toggle_game_canvas_layer_selection(row.kind);
            if !selected {
                self.sync_canvas_authoring_context();
                self.status_message = format!(
                    "Layer deselected for editing: {} | {} layer(s) selected",
                    row.label,
                    self.selected_game_canvas_layer_count(),
                );
                return true;
            }
        }
        if !eye_zone && !lock_zone {
            self.sync_asset_browser_for_canvas_layer(row.kind);
        }
        if self.game_canvas_ui_active() {
            self.game_canvas_ui.active_lane = match row.kind {
                CanvasLayerKind::UiLayout => haven_authoring::UiAuthoringLane::Layout,
                CanvasLayerKind::UiControls => haven_authoring::UiAuthoringLane::Controls,
                CanvasLayerKind::UiData => haven_authoring::UiAuthoringLane::Data,
                CanvasLayerKind::UiBehavior => haven_authoring::UiAuthoringLane::Behavior,
                CanvasLayerKind::UiPresentation => haven_authoring::UiAuthoringLane::Presentation,
                CanvasLayerKind::UiOverrides => haven_authoring::UiAuthoringLane::Overrides,
                _ => self.game_canvas_ui.active_lane,
            };
            self.status_message = format!("UI authoring lane: {}", self.game_canvas_ui.active_lane.label());
            return true;
        }
        match self.viewport_mode {
            EditorViewportMode::SceneMap => {
                let scene_mode = match row.kind {
                    CanvasLayerKind::Terrain | CanvasLayerKind::Water | CanvasLayerKind::RoadsPaths => Some(SceneLayerMode::Terrain),
                    CanvasLayerKind::Objects | CanvasLayerKind::Buildings | CanvasLayerKind::Structures
                    | CanvasLayerKind::Furniture | CanvasLayerKind::Props | CanvasLayerKind::Lighting
                    | CanvasLayerKind::Atmosphere | CanvasLayerKind::Weather | CanvasLayerKind::Effects => Some(SceneLayerMode::Objects),
                    CanvasLayerKind::Zones | CanvasLayerKind::Triggers => Some(SceneLayerMode::Zones),
                    CanvasLayerKind::Links => Some(SceneLayerMode::Transitions),
                    _ => None,
                };
                if let Some(mode) = scene_mode {
                    if eye_zone {
                        self.toggle_layer_visibility(mode);
                        return true;
                    }
                    if lock_zone {
                        self.toggle_layer_lock(mode);
                        return true;
                    }
                    self.set_scene_layer_mode(mode);
                    if !matches!(row.kind, CanvasLayerKind::Terrain | CanvasLayerKind::Objects | CanvasLayerKind::Zones | CanvasLayerKind::Links) {
                        self.canvas_layer_context_override = Some(row.kind);
                    }
                    self.set_scene_edit_tool(SceneEditTool::Select);
                } else {
                    if !eye_zone && !lock_zone {
                        self.canvas_layer_context_override = Some(row.kind);
                    }
                    match row.kind {
                        CanvasLayerKind::TerrainTransitions if eye_zone => {
                            self.autotile_preview_enabled = !self.autotile_preview_enabled;
                        }
                        CanvasLayerKind::Collision if eye_zone => {
                            self.toggle_game_canvas_layer_visibility(CanvasLayerKind::Collision);
                        }
                        CanvasLayerKind::Collision if !lock_zone => {
                            self.canvas_layer_context_override = Some(row.kind);
                        }
                        CanvasLayerKind::Collision => {}
                        _ => {}
                    }
                    self.set_scene_edit_tool(SceneEditTool::Select);
                }
            }
            EditorViewportMode::SceneRectangles => match row.kind {
                CanvasLayerKind::Terrain => self.set_world_layer_mode(WorldLayerMode::Terrain),
                CanvasLayerKind::Water | CanvasLayerKind::RoadsPaths => {
                    self.set_world_layer_mode(WorldLayerMode::Terrain);
                    self.canvas_layer_context_override = Some(row.kind);
                }
                CanvasLayerKind::Objects | CanvasLayerKind::Buildings | CanvasLayerKind::Vegetation
                | CanvasLayerKind::Resources | CanvasLayerKind::Structures | CanvasLayerKind::Furniture
                | CanvasLayerKind::Props | CanvasLayerKind::Lighting | CanvasLayerKind::Atmosphere
                | CanvasLayerKind::Weather | CanvasLayerKind::Effects => {
                    self.set_world_layer_mode(WorldLayerMode::Objects);
                    self.canvas_layer_context_override = Some(row.kind);
                }
                CanvasLayerKind::Zones | CanvasLayerKind::Triggers => self.set_world_layer_mode(WorldLayerMode::Zones),
                CanvasLayerKind::StructuralLevels => self.set_world_layer_mode(WorldLayerMode::StructuralLevels),
                CanvasLayerKind::Collision => {
                    if eye_zone {
                        self.toggle_game_canvas_layer_visibility(CanvasLayerKind::Collision);
                    } else if !lock_zone {
                        self.canvas_layer_context_override = Some(row.kind);
                    }
                    self.set_world_edit_tool(WorldEditTool::Select);
                }
                _ => {
                    if !eye_zone && !lock_zone {
                        self.canvas_layer_context_override = Some(row.kind);
                    }
                    self.set_world_edit_tool(WorldEditTool::Select);
                }
            },
            EditorViewportMode::PixelStudio => {
                self.canvas_layer_context_override = None;
                let mut selected = false;
                let mut begin_drag = false;
                if let Some(document) = self.pixel_studio.document.as_mut() {
                    // Rail rows are displayed top-most first while PixelDocument stores bottom-most first.
                    let actual = pixel_layer_actual_index(document.layer_count(), index).unwrap_or(0);
                    if document.select_layer(actual) {
                        selected = true;
                        if eye_zone {
                            document.toggle_active_layer_visibility();
                        } else if lock_zone {
                            document.toggle_active_layer_lock();
                        } else if !row.locked {
                            begin_drag = true;
                        }
                    }
                }
                if selected {
                    self.pixel_studio.tool = haven_pixel::PixelTool::Selection;
                    self.pixel_studio.inspector_tab = super::pixel_studio::PixelInspectorTab::Asset;
                }
                if begin_drag {
                    self.begin_pixel_layer_drag(index);
                }
            }
            EditorViewportMode::AnimationStudio => {
                if !eye_zone && !lock_zone {
                    self.canvas_layer_context_override = Some(row.kind);
                    self.animation_studio.placement_mode = match row.kind {
                        CanvasLayerKind::AnimationAnchors => super::animation_studio::AnimationPlacementMode::Pivot,
                        CanvasLayerKind::AnimationFootAnchor => super::animation_studio::AnimationPlacementMode::Foot,
                        CanvasLayerKind::AnimationShadowAnchor => super::animation_studio::AnimationPlacementMode::Shadow,
                        CanvasLayerKind::AnimationSockets => super::animation_studio::AnimationPlacementMode::Socket,
                        CanvasLayerKind::AnimationHitboxes => super::animation_studio::AnimationPlacementMode::Hitbox,
                        CanvasLayerKind::AnimationHurtboxes => super::animation_studio::AnimationPlacementMode::Hurtbox,
                        _ => super::animation_studio::AnimationPlacementMode::None,
                    };
                }
            }
            EditorViewportMode::CharacterStudio => {
                if row.kind == CanvasLayerKind::CharacterParts {
                    let recipe_count = self.character_studio.semantic_layer_count();
                    if index < recipe_count {
                        self.canvas_layer_context_override = None;
                        if eye_zone {
                            self.status_message = self.character_studio.toggle_semantic_layer_preview(index);
                        } else if !lock_zone {
                            self.status_message = self.character_studio.select_semantic_layer(index);
                        }
                        return true;
                    }
                }
                if !eye_zone && !lock_zone {
                    self.canvas_layer_context_override = Some(row.kind);
                }
            }
            EditorViewportMode::LogicStudio | EditorViewportMode::SoundStudio | EditorViewportMode::RegionGraph | EditorViewportMode::SceneBank => {
                if !eye_zone && !lock_zone {
                    self.canvas_layer_context_override = Some(row.kind);
                }
            }
        }
        self.sync_canvas_authoring_context();
        self.status_message = if eye_zone {
            format!("Layer visibility toggled: {} | editing selection unchanged", row.label)
        } else if lock_zone {
            format!("Layer lock toggled: {} | editing selection unchanged", row.label)
        } else if self.game_canvas_uses_semantic_layer_authority() {
            format!(
                "Layer selected for editing: {} | {} layer(s) selected",
                row.label,
                self.selected_game_canvas_layer_count(),
            )
        } else {
            format!("Layer context selected: {} | tool remains non-destructive", row.label)
        };
        true
    }

    pub(crate) fn update_canvas_layer_resize_input(&mut self) -> bool {
        // A14X: Layers is a dedicated fixed-width sibling panel. The historical
        // drag-resize grip remains retired; width is governed by workspace settings.
        self.canvas_layer_resize_active = false;
        false
    }

    pub(crate) fn update_canvas_layer_scroll_input(&mut self) -> bool {
        if self.workspace_shell.canvas_layer_rail_collapsed {
            return false;
        }
        let mouse = vec2(mouse_position().0, mouse_position().1);
        if !self.canvas_layer_rail_rect().contains(mouse) {
            return false;
        }
        let wheel = mouse_wheel().1;
        if wheel.abs() < f32::EPSILON {
            return false;
        }
        let max_scroll = self.active_canvas_layer_descriptors().len().saturating_sub(1);
        if wheel > 0.0 {
            self.workspace_shell.canvas_layer_scroll = self.workspace_shell.canvas_layer_scroll.saturating_sub(1);
        } else {
            self.workspace_shell.canvas_layer_scroll = (self.workspace_shell.canvas_layer_scroll + 1).min(max_scroll);
        }
        let _ = self.workspace_shell.save_default();
        true
    }

    pub(crate) fn select_canvas_layer_by_shortcut(&mut self, display_index: usize) -> bool {
        let rows = self.active_canvas_layer_descriptors();
        let Some(row) = rows.get(display_index).cloned() else { return false; };
        if self.game_canvas_uses_semantic_layer_authority()
            && !self.toggle_game_canvas_layer_selection(row.kind)
        {
            self.sync_canvas_authoring_context();
            self.status_message = format!(
                "Layer {} deselected: {} | {} layer(s) selected",
                display_index + 1,
                row.label,
                self.selected_game_canvas_layer_count(),
            );
            return true;
        }
        self.canvas_active_tool = super::tool_registry::UniversalTool::Select;
        match self.viewport_mode {
            EditorViewportMode::SceneMap => {
                match row.kind {
                    CanvasLayerKind::Terrain => self.set_scene_layer_mode(SceneLayerMode::Terrain),
                    CanvasLayerKind::Objects => self.set_scene_layer_mode(SceneLayerMode::Objects),
                    CanvasLayerKind::Zones => self.set_scene_layer_mode(SceneLayerMode::Zones),
                    CanvasLayerKind::Links => self.set_scene_layer_mode(SceneLayerMode::Transitions),
                    CanvasLayerKind::Collision => self.canvas_layer_context_override = Some(row.kind),
                    _ => self.canvas_layer_context_override = Some(row.kind),
                }
                self.set_scene_edit_tool(SceneEditTool::Select);
            }
            EditorViewportMode::SceneRectangles => {
                match row.kind {
                    CanvasLayerKind::Terrain => self.set_world_layer_mode(WorldLayerMode::Terrain),
                    CanvasLayerKind::Objects | CanvasLayerKind::Buildings => self.set_world_layer_mode(WorldLayerMode::Objects),
                    CanvasLayerKind::Zones => self.set_world_layer_mode(WorldLayerMode::Zones),
                    CanvasLayerKind::StructuralLevels => self.set_world_layer_mode(WorldLayerMode::StructuralLevels),
                    CanvasLayerKind::Collision => self.canvas_layer_context_override = Some(row.kind),
                    _ => self.canvas_layer_context_override = Some(row.kind),
                }
                self.set_world_edit_tool(WorldEditTool::Select);
            }
            EditorViewportMode::PixelStudio => {
                self.canvas_layer_context_override = None;
                if let Some(document) = self.pixel_studio.document.as_mut() {
                    let actual = pixel_layer_actual_index(document.layer_count(), display_index).unwrap_or(0);
                    if !document.select_layer(actual) { return false; }
                    self.pixel_studio.tool = haven_pixel::PixelTool::Selection;
                } else { return false; }
            }
            EditorViewportMode::AnimationStudio => {
                self.canvas_layer_context_override = Some(row.kind);
                self.animation_studio.placement_mode = match row.kind {
                    CanvasLayerKind::AnimationAnchors => super::animation_studio::AnimationPlacementMode::Pivot,
                    CanvasLayerKind::AnimationFootAnchor => super::animation_studio::AnimationPlacementMode::Foot,
                    CanvasLayerKind::AnimationShadowAnchor => super::animation_studio::AnimationPlacementMode::Shadow,
                    CanvasLayerKind::AnimationSockets => super::animation_studio::AnimationPlacementMode::Socket,
                    CanvasLayerKind::AnimationHitboxes => super::animation_studio::AnimationPlacementMode::Hitbox,
                    CanvasLayerKind::AnimationHurtboxes => super::animation_studio::AnimationPlacementMode::Hurtbox,
                    _ => super::animation_studio::AnimationPlacementMode::None,
                };
            }
            _ => self.canvas_layer_context_override = Some(row.kind),
        }
        self.sync_canvas_authoring_context();
        self.status_message = format!("Layer {}: {} | Alt+{}", display_index + 1, row.label, display_index + 1);
        true
    }

}


pub(crate) fn canvas_layer_row_layout(
    rows: &[CanvasLayerDescriptor],
    rect: Rect,
    bottom_reserved: f32,
    scroll: usize,
) -> Vec<(usize, Rect)> {
    let mut out = Vec::new();
    let mut y = rect.y + HEADER_H;
    let mut group = None;
    let start = scroll.min(rows.len().saturating_sub(1));
    for (index, row) in rows.iter().enumerate().skip(start) {
        if group != Some(row.group) {
            y += GROUP_HEADER_H;
            group = Some(row.group);
        }
        let row_rect = Rect::new(rect.x + 3.0, y, rect.w - 6.0, ROW_H - 2.0);
        if row_rect.y + row_rect.h > rect.y + rect.h - bottom_reserved - 2.0 {
            break;
        }
        out.push((index, row_rect));
        y += ROW_H;
    }
    out
}

fn canvas_layer_scroll_up_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + rect.w - LAYER_SCROLL_BUTTON_W * 2.0 - 12.0, rect.y + 4.0, LAYER_SCROLL_BUTTON_W, HEADER_H - 8.0)
}

fn canvas_layer_scroll_down_rect(rect: Rect) -> Rect {
    Rect::new(rect.x + rect.w - LAYER_SCROLL_BUTTON_W - 10.0, rect.y + 4.0, LAYER_SCROLL_BUTTON_W, HEADER_H - 8.0)
}

fn draw_layer_chevron_icon(rect: Rect, points_right: bool, color: Color) {
    let cx = rect.x + rect.w * 0.5;
    let cy = rect.y + rect.h * 0.5;
    let d = 4.0;
    if points_right {
        draw_line(cx - d, cy - d, cx + d, cy, 1.7, color);
        draw_line(cx + d, cy, cx - d, cy + d, 1.7, color);
    } else {
        draw_line(cx + d, cy - d, cx - d, cy, 1.7, color);
        draw_line(cx - d, cy, cx + d, cy + d, 1.7, color);
    }
}

fn draw_layer_scroll_icon(rect: Rect, up: bool, color: Color) {
    let cx = rect.x + rect.w * 0.5;
    let cy = rect.y + rect.h * 0.5;
    if up {
        draw_line(cx - 4.0, cy + 2.0, cx, cy - 2.0, 1.6, color);
        draw_line(cx, cy - 2.0, cx + 4.0, cy + 2.0, 1.6, color);
    } else {
        draw_line(cx - 4.0, cy - 2.0, cx, cy + 2.0, 1.6, color);
        draw_line(cx, cy + 2.0, cx + 4.0, cy - 2.0, 1.6, color);
    }
}

fn draw_layer_kind_badge(kind: CanvasLayerKind, rect: Rect, active: bool) {
    let bg = if active { Color::new(0.18, 0.31, 0.45, 1.0) } else { editor_theme::colors::CONTROL_BG };
    draw_rectangle(rect.x, rect.y, rect.w, rect.h, bg);
    draw_rectangle_lines(rect.x, rect.y, rect.w, rect.h, 1.0, editor_theme::colors::BORDER_SUBTLE);
    let label = match kind {
        CanvasLayerKind::Terrain => "T",
        CanvasLayerKind::TerrainTransitions => "Tr",
        CanvasLayerKind::Buildings => "B",
        CanvasLayerKind::Objects => "O",
        CanvasLayerKind::AuthoredPixels | CanvasLayerKind::PixelLayer => "P",
        CanvasLayerKind::Collision => "C",
        CanvasLayerKind::StructuralLevels => "Lv",
        CanvasLayerKind::SourceReference | CanvasLayerKind::Guides => "R",
        CanvasLayerKind::AnimationFrames => "F",
        CanvasLayerKind::AnimationSockets => "S",
        CanvasLayerKind::AnimationHitboxes | CanvasLayerKind::AnimationHurtboxes => "H",
        CanvasLayerKind::AnimationEvents => "E",
        CanvasLayerKind::LogicNodes | CanvasLayerKind::SoundNodes => "N",
        CanvasLayerKind::LogicConnections | CanvasLayerKind::SoundConnections | CanvasLayerKind::Links => "L",
        _ => "·",
    };
    draw_editor_text(label, rect.x + 4.0, rect.y + rect.h - 5.0, if label.len() > 1 { 8.0 } else { 9.0 }, editor_theme::colors::TEXT_SECONDARY);
}

fn draw_lock_icon(rect: Rect, locked: bool) {
    let color = if locked { editor_theme::colors::WARN } else { editor_theme::colors::TEXT_SECONDARY };
    let cx = rect.x + rect.w * 0.5;
    let body = Rect::new(cx - 5.5, rect.y + 11.0, 11.0, 8.0);
    draw_rectangle_lines(body.x, body.y, body.w, body.h, 1.4, color);
    // Vector padlock avoids relying on a font glyph and stays crisp at every DPI.
    let left = cx - 4.0;
    let right = cx + 4.0;
    let top = rect.y + 7.0;
    if locked {
        draw_line(left, body.y, left, top + 2.0, 1.4, color);
        draw_line(left, top + 2.0, cx - 2.0, top, 1.4, color);
        draw_line(cx - 2.0, top, cx + 2.0, top, 1.4, color);
        draw_line(cx + 2.0, top, right, top + 2.0, 1.4, color);
        draw_line(right, top + 2.0, right, body.y, 1.4, color);
    } else {
        draw_line(left + 3.0, body.y, left + 3.0, top + 2.0, 1.4, color);
        draw_line(left + 3.0, top + 2.0, cx + 1.0, top, 1.4, color);
        draw_line(cx + 1.0, top, right + 1.0, top + 2.0, 1.4, color);
    }
}

fn scene_layer_index(mode: SceneLayerMode) -> usize {
    match mode {
        SceneLayerMode::Terrain => 0,
        SceneLayerMode::Objects => 1,
        SceneLayerMode::Zones => 2,
        SceneLayerMode::Transitions => 3,
    }
}

#[cfg(test)]
mod a14aa_semantic_layer_tests {
    use super::*;

    #[test]
    fn water_and_paths_do_not_collapse_into_terrain_layer() {
        assert_eq!(
            canvas_layer_kind_for_surface_tile(TileKind::Grass),
            CanvasLayerKind::Terrain
        );
        assert_eq!(
            canvas_layer_kind_for_surface_tile(TileKind::ShallowWater),
            CanvasLayerKind::Water
        );
        assert_eq!(
            canvas_layer_kind_for_surface_tile(TileKind::RiverWater),
            CanvasLayerKind::Water
        );
        assert_eq!(
            canvas_layer_kind_for_surface_tile(TileKind::Road),
            CanvasLayerKind::RoadsPaths
        );
        assert_eq!(
            canvas_layer_kind_for_surface_tile(TileKind::Cliff),
            CanvasLayerKind::StructuralLevels
        );
        assert_eq!(
            canvas_layer_kind_for_surface_tile(TileKind::MudBank),
            CanvasLayerKind::Terrain
        );
    }

    #[test]
    fn structure_tiles_and_world_objects_have_independent_families() {
        assert_eq!(
            canvas_layer_kind_for_surface_tile(TileKind::Bridge),
            CanvasLayerKind::Structures
        );
        assert_eq!(
            canvas_layer_kind_for_surface_tile(TileKind::Wall),
            CanvasLayerKind::Structures
        );
        assert_eq!(
            canvas_layer_kind_for_world_object(ObjectKind::Tree),
            CanvasLayerKind::Vegetation
        );
        assert_eq!(
            canvas_layer_kind_for_world_object(ObjectKind::Boulder),
            CanvasLayerKind::Resources
        );
        assert_eq!(
            canvas_layer_kind_for_world_object(ObjectKind::Door),
            CanvasLayerKind::Structures
        );
        assert_eq!(
            canvas_layer_kind_for_world_object(ObjectKind::Crate),
            CanvasLayerKind::Objects
        );
    }
    #[test]
    fn stamps_follow_semantic_visibility_families() {
        assert_eq!(
            canvas_layer_kind_for_stamp("lpc_pond_grass_bank_a", Some("terrain/ponds")),
            CanvasLayerKind::Water
        );
        assert_eq!(
            canvas_layer_kind_for_stamp("estate_cottage_roof", Some("roof")),
            CanvasLayerKind::Structures
        );
        assert_eq!(
            canvas_layer_kind_for_stamp("market_crate_stack", Some("props")),
            CanvasLayerKind::Objects
        );
    }

}
