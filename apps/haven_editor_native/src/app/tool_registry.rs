use super::canvas_layers::CanvasLayerKind;
use super::EditorViewportMode;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum UniversalTool {
    Inspect,
    Select,
    Pan,
    Paint,
    Erase,
    Fill,
    Replace,
    Pick,
    MagicSelect,
    Rectangle,
    Ellipse,
    Line,
    Gradient,
    Blur,
    Smudge,
    Lighten,
    Darken,
    Place,
    Move,
    Link,
    Collision,
    PixelEdit,
    Anchor,
    Socket,
    Event,
}

impl UniversalTool {
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Inspect => "Inspect",
            Self::Select => "Select",
            Self::Pan => "Pan",
            Self::Paint => "Brush / Pencil",
            Self::Erase => "Eraser",
            Self::Fill => "Fill",
            Self::Replace => "Replace",
            Self::Pick => "Eyedropper",
            Self::MagicSelect => "Magic Select",
            Self::Rectangle => "Rectangle",
            Self::Ellipse => "Ellipse",
            Self::Line => "Line",
            Self::Gradient => "Gradient",
            Self::Blur => "Blur",
            Self::Smudge => "Smudge",
            Self::Lighten => "Lighten",
            Self::Darken => "Darken",
            Self::Place => "Stamp / Place",
            Self::Move => "Move",
            Self::Link => "Link",
            Self::Collision => "Collision",
            Self::PixelEdit => "Pixel Edit",
            Self::Anchor => "Anchor / Pivot",
            Self::Socket => "Socket",
            Self::Event => "Event",
        }
    }

    #[allow(dead_code)]
    pub(crate) fn mutates_document(self) -> bool {
        !matches!(self, Self::Inspect | Self::Select | Self::Pan | Self::Pick | Self::PixelEdit)
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum ToolGroup {
    Selection,
    Paint,
    Shapes,
    Transform,
    Content,
    Gameplay,
    Animation,
}

impl ToolGroup {
    pub(crate) const ALL: [Self; 7] = [
        Self::Selection,
        Self::Paint,
        Self::Shapes,
        Self::Transform,
        Self::Content,
        Self::Gameplay,
        Self::Animation,
    ];

    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Selection => "Selection",
            Self::Paint => "Paint",
            Self::Shapes => "Shapes",
            Self::Transform => "Transform",
            Self::Content => "Content",
            Self::Gameplay => "Gameplay",
            Self::Animation => "Animation",
        }
    }

    pub(crate) fn tools(self) -> &'static [UniversalTool] {
        match self {
            Self::Selection => &[UniversalTool::Inspect, UniversalTool::Select, UniversalTool::MagicSelect, UniversalTool::Pan],
            Self::Paint => &[UniversalTool::Paint, UniversalTool::Erase, UniversalTool::Fill, UniversalTool::Replace, UniversalTool::Pick, UniversalTool::Gradient, UniversalTool::Blur, UniversalTool::Smudge, UniversalTool::Lighten, UniversalTool::Darken],
            Self::Shapes => &[UniversalTool::Rectangle, UniversalTool::Ellipse, UniversalTool::Line],
            Self::Transform => &[UniversalTool::Move],
            Self::Content => &[UniversalTool::Place, UniversalTool::PixelEdit],
            Self::Gameplay => &[UniversalTool::Link, UniversalTool::Collision],
            Self::Animation => &[UniversalTool::Anchor, UniversalTool::Socket, UniversalTool::Event],
        }
    }

}

#[derive(Clone, Copy, Debug)]
pub(crate) struct ToolDescriptor {
    pub shortcut: &'static str,
    pub help: &'static str,
}

pub(crate) fn descriptor(tool: UniversalTool) -> ToolDescriptor {
    match tool {
        UniversalTool::Inspect => ToolDescriptor { shortcut: "Esc", help: "Inspect without modifying the document" },
        UniversalTool::Select => ToolDescriptor { shortcut: "1 / S", help: "Select; Pixel Studio uses a marquee selection" },
        UniversalTool::Pan => ToolDescriptor { shortcut: "9 / Space-drag", help: "Pan the current canvas" },
        UniversalTool::Paint => ToolDescriptor { shortcut: "2 / P", help: "Paint; Pixel Studio always starts with a 1px pencil" },
        UniversalTool::Erase => ToolDescriptor { shortcut: "8 / E", help: "Erase from a compatible editable layer" },
        UniversalTool::Fill => ToolDescriptor { shortcut: "4 / F", help: "Fill a compatible semantic or pixel region" },
        UniversalTool::Replace => ToolDescriptor { shortcut: "Q", help: "Replace the sampled semantic value across the compatible scope" },
        UniversalTool::Pick => ToolDescriptor { shortcut: "6 / I", help: "Sample without modifying" },
        UniversalTool::MagicSelect => ToolDescriptor { shortcut: "W (Pixel)", help: "Select the contiguous same-color region under the pointer" },
        UniversalTool::Rectangle => ToolDescriptor { shortcut: "3 / R", help: "Create a rectangular selection or authored region" },
        UniversalTool::Ellipse => ToolDescriptor { shortcut: "O (Pixel)", help: "Draw a pixel-snapped ellipse on the active editable Pixel layer" },
        UniversalTool::Line => ToolDescriptor { shortcut: "L (Pixel)", help: "Draw a one-pixel-aware line on the active editable Pixel layer" },
        UniversalTool::Gradient => ToolDescriptor { shortcut: "G (Pixel)", help: "Fill the current Pixel selection with an FG-to-BG linear gradient" },
        UniversalTool::Blur => ToolDescriptor { shortcut: "B (Pixel effects)", help: "Blur the current selection or clicked pixel neighborhood through document history" },
        UniversalTool::Smudge => ToolDescriptor { shortcut: "U (Pixel)", help: "Blend neighboring pixels while dragging on the active editable layer" },
        UniversalTool::Lighten => ToolDescriptor { shortcut: "J (Pixel)", help: "Lighten the current selection through transactional Pixel history" },
        UniversalTool::Darken => ToolDescriptor { shortcut: "D (Pixel)", help: "Darken the current selection through transactional Pixel history" },
        UniversalTool::Place => ToolDescriptor { shortcut: "7", help: "Place the currently selected compatible asset" },
        UniversalTool::Move => ToolDescriptor { shortcut: "M", help: "Move compatible selected authored content" },
        UniversalTool::Link => ToolDescriptor { shortcut: "L", help: "Create scene, route, doorway, or socket links" },
        UniversalTool::Collision => ToolDescriptor { shortcut: "C", help: "Author collision without changing visual pixels" },
        UniversalTool::PixelEdit => ToolDescriptor { shortcut: "Ctrl+E", help: "Open the selected scope in Pixel Studio" },
        UniversalTool::Anchor => ToolDescriptor { shortcut: "A", help: "Place or edit an animation pivot/anchor" },
        UniversalTool::Socket => ToolDescriptor { shortcut: "K", help: "Author attachment or animation sockets" },
        UniversalTool::Event => ToolDescriptor { shortcut: "V", help: "Author animation or timeline events" },
    }
}

#[allow(dead_code)]
pub(crate) fn tools_for_viewport(viewport: EditorViewportMode) -> Vec<ToolDescriptor> {
    let layer = None;
    ToolGroup::ALL
        .into_iter()
        .flat_map(|group| group.tools().iter().copied())
        .filter(|tool| tool_is_applicable(viewport, layer, *tool))
        .map(descriptor)
        .collect()
}


/// A14Y: every tool that is valid for the active studio/layer is a first-class
/// Tool Rail entry. The rail scrolls vertically; no applicable tool is hidden
/// behind a generic overflow/menu affordance.
pub(crate) fn group_has_applicable_tool(viewport: EditorViewportMode, layer: Option<CanvasLayerKind>, group: ToolGroup) -> bool {
    group.tools().iter().copied().any(|tool| tool_is_applicable(viewport, layer, tool))
}

pub(crate) fn tool_is_applicable(viewport: EditorViewportMode, layer: Option<CanvasLayerKind>, tool: UniversalTool) -> bool {
    use CanvasLayerKind as L;
    use EditorViewportMode as V;
    use UniversalTool as T;

    // W60E3: the centralized rack only enables operations that are genuinely
    // wired for the current CanvasWorkspace. Unsupported future tools remain
    // visible in their group but greyed instead of silently falling back to Select.
    // W60E7: enabled means a real adapter exists for this exact canvas.
    // Inspect is retained in the shared vocabulary but remains disabled until
    // it has behavior distinct from Select. Select itself is only enabled on
    // canvases whose shared adapter actually owns selection state.
    if tool == T::Inspect {
        return false;
    }
    if tool == T::Select {
        return matches!(viewport, V::SceneMap | V::SceneRectangles | V::PixelStudio | V::AnimationStudio | V::RegionGraph | V::SceneBank | V::LogicStudio | V::SoundStudio);
    }
    if tool == T::Pan {
        return matches!(viewport, V::SceneMap | V::SceneRectangles | V::PixelStudio | V::RegionGraph);
    }

    match viewport {
        V::RegionGraph => match layer {
            Some(L::Links) => matches!(tool, T::Link),
            Some(L::Buildings) | Some(L::Terrain) => matches!(tool, T::Select),
            _ => false,
        },
        V::SceneBank => match layer {
            Some(L::Buildings) => matches!(tool, T::Select),
            _ => false,
        },
        V::CharacterStudio => false,
        V::LogicStudio => match layer {
            Some(L::LogicNodes) => matches!(tool, T::Select | T::Place | T::Move),
            Some(L::LogicConnections) => matches!(tool, T::Select | T::Link),
            Some(L::LogicBindings) => matches!(tool, T::Select | T::Link),
            _ => matches!(tool, T::Select),
        },
        V::SoundStudio => match layer {
            Some(L::SoundNodes) => matches!(tool, T::Select | T::Place | T::Move),
            Some(L::SoundConnections) => matches!(tool, T::Select | T::Link),
            Some(L::SoundTimeline) => matches!(tool, T::Select),
            _ => matches!(tool, T::Select),
        },
        V::AnimationStudio => match layer {
            Some(L::AnimationFrames) => matches!(tool, T::PixelEdit),
            Some(L::AnimationAnchors) | Some(L::AnimationFootAnchor) | Some(L::AnimationShadowAnchor) => matches!(tool, T::Anchor),
            Some(L::AnimationSockets) => matches!(tool, T::Socket),
            Some(L::AnimationEvents) => matches!(tool, T::Event),
            Some(L::AnimationHitboxes) | Some(L::AnimationHurtboxes) => matches!(tool, T::Rectangle | T::Erase),
            _ => false,
        },
        V::PixelStudio => match layer {
            Some(L::Collision) => matches!(tool, T::Paint | T::Erase | T::Fill | T::Pick | T::Rectangle | T::Ellipse | T::Line | T::Collision),
            Some(L::SourceReference)
            | Some(L::Terrain)
            | Some(L::TerrainTransitions)
            | Some(L::StructuralLevels)
            | Some(L::Buildings)
            | Some(L::Objects) => matches!(tool, T::Pick),
            _ => matches!(tool, T::Select | T::MagicSelect | T::Paint | T::Erase | T::Fill | T::Pick | T::Rectangle | T::Ellipse | T::Line | T::Gradient | T::Blur | T::Smudge | T::Lighten | T::Darken),
        },
        V::SceneMap => match layer {
            Some(L::Terrain) | Some(L::Water) | Some(L::RoadsPaths) => matches!(tool, T::Paint | T::Erase | T::Fill | T::Replace | T::Pick | T::Rectangle | T::PixelEdit),
            // Transition pixels are resolved/generated presentation. The current
            // eyedropper samples base terrain, not a transition recipe, so only
            // Pixel Edit is advertised until a real transition picker exists.
            Some(L::TerrainTransitions) => matches!(tool, T::PixelEdit),
            Some(L::StructuralLevels) => matches!(tool, T::PixelEdit),
            // Building transform/place/pick adapters are still separate legacy
            // commands. Do not advertise them in the shared rack yet.
            Some(L::Buildings) | Some(L::Structures) | Some(L::Furniture) | Some(L::Props)
            | Some(L::Lighting) | Some(L::Effects) => matches!(tool, T::Select | T::Place | T::Move | T::Pick | T::Erase | T::PixelEdit),
            Some(L::Objects) | Some(L::Vegetation) | Some(L::Resources) => matches!(tool, T::Select | T::Place | T::Move | T::Pick | T::Erase | T::PixelEdit),
            Some(L::AuthoredPixels) => matches!(tool, T::Paint | T::Erase | T::Pick | T::PixelEdit),
            // Direct scene collision drawing is authored through the Pixel
            // collision Add/Subtract layers today. The overlay toggle is not a
            // mutation tool, so Collision remains disabled here.
            Some(L::Collision) => matches!(tool, T::PixelEdit),
            Some(L::Zones) | Some(L::Triggers) => matches!(tool, T::Paint | T::Erase | T::Fill | T::Replace | T::Rectangle),
            // Scene transitions already have real place/erase/pick semantics.
            Some(L::Links) => matches!(tool, T::Place | T::Erase | T::Pick),
            Some(L::Navigation) | Some(L::Interaction) | Some(L::Shelter) | Some(L::Occlusion)
            | Some(L::WaterSwim) | Some(L::SpawnPopulation) | Some(L::BuildabilityFarming)
            | Some(L::LogicBindings) => matches!(tool, T::Paint | T::Erase | T::Fill | T::Pick | T::Rectangle),
            _ => false,
        },
        V::SceneRectangles => match layer {
            Some(L::Terrain) | Some(L::Water) | Some(L::RoadsPaths) => matches!(tool, T::Paint | T::Erase | T::Fill | T::Replace | T::Pick | T::Rectangle | T::PixelEdit),
            Some(L::TerrainTransitions) => matches!(tool, T::PixelEdit),
            Some(L::Objects) | Some(L::Vegetation) | Some(L::Resources) | Some(L::Structures)
            | Some(L::Furniture) | Some(L::Props) | Some(L::Lighting) | Some(L::Effects) => matches!(tool, T::Place | T::Pick | T::PixelEdit),
            Some(L::Buildings) => matches!(tool, T::PixelEdit),
            Some(L::AuthoredPixels) => matches!(tool, T::Paint | T::Erase | T::Pick | T::PixelEdit),
            Some(L::Collision) => matches!(tool, T::PixelEdit),
            Some(L::Zones) | Some(L::Triggers) => matches!(tool, T::Paint | T::Erase | T::Fill | T::Replace | T::Rectangle),
            // Structural levels are discrete region/platform authoring. Freeform
            // Paint/Erase is intentionally not a valid adapter.
            Some(L::StructuralLevels) => matches!(tool, T::Fill | T::Pick | T::Rectangle),
            _ => false,
        },
    }
}

#[cfg(test)]
mod w80_tests {
    use super::*;

    #[test]
    fn pixel_effect_tools_are_direct_rail_entries() {
        assert!(tool_is_applicable(EditorViewportMode::PixelStudio, None, UniversalTool::Blur));
        assert!(tool_is_applicable(EditorViewportMode::PixelStudio, None, UniversalTool::MagicSelect));
        assert!(tool_is_applicable(EditorViewportMode::PixelStudio, None, UniversalTool::Gradient));
    }

    #[test]
    fn world_pixel_edit_is_direct_when_applicable() {
        let layer = Some(CanvasLayerKind::Terrain);
        assert!(tool_is_applicable(EditorViewportMode::SceneRectangles, layer, UniversalTool::PixelEdit));
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub(crate) struct ToolAvailability { pub enabled: bool, pub reason: Option<&'static str> }
pub(crate) fn tool_availability(viewport: EditorViewportMode, layer: Option<CanvasLayerKind>, tool: UniversalTool) -> ToolAvailability {
    let enabled = tool_is_applicable(viewport, layer, tool);
    ToolAvailability { enabled, reason: if enabled { None } else { Some("Tool is not supported by the active document/layer authority") } }
}
