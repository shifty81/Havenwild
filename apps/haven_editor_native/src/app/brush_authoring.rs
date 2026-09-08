use super::canvas_layers::CanvasLayerKind;
use super::tool_registry::UniversalTool;
use super::{EditorApp, EditorViewportMode};

/// UGC-A1: canonical authoring intent shared by Tool Rail, text layers,
/// palette/tool shelf, F3 live authoring and the eventual Game Canvas cards.
/// It intentionally stores semantic intent rather than renderer/runtime details.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum BrushMode {
    None,
    Pixel,
    ExactTile,
    Stamp,
    SemanticTerrain,
    Autotile,
    TerrainElevation,
    Elevation,
    Hydrology,
    Collision,
    Navigation,
    Object,
    Scatter,
    GameplayRegion,
    Lighting,
    Atmosphere,
    Weather,
    VisualOverride,
}

impl BrushMode {
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::None => "None",
            Self::Pixel => "Pixel",
            Self::ExactTile => "Exact Tile",
            Self::Stamp => "Stamp",
            Self::SemanticTerrain => "Semantic",
            Self::Autotile => "Autotile",
            Self::TerrainElevation => "Terrain + Elevation",
            Self::Elevation => "Elevation",
            Self::Hydrology => "Hydrology",
            Self::Collision => "Collision",
            Self::Navigation => "Navigation",
            Self::Object => "Object",
            Self::Scatter => "Scatter",
            Self::GameplayRegion => "Gameplay Region",
            Self::Lighting => "Lighting",
            Self::Atmosphere => "Atmosphere",
            Self::Weather => "Weather",
            Self::VisualOverride => "Visual Override",
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum BrushSourceKind {
    None,
    PixelColor,
    TerrainMaterial,
    AtlasCell,
    Stamp,
    StructuralRecipe,
    Object,
    CollisionSemantic,
    NavigationSemantic,
    GameplaySemantic,
    Light,
    AtmosphereProfile,
    WeatherProfile,
}

impl BrushSourceKind {
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::None => "No source",
            Self::PixelColor => "Color",
            Self::TerrainMaterial => "Terrain",
            Self::AtlasCell => "Atlas",
            Self::Stamp => "Stamp",
            Self::StructuralRecipe => "Structure",
            Self::Object => "Object",
            Self::CollisionSemantic => "Collision",
            Self::NavigationSemantic => "Navigation",
            Self::GameplaySemantic => "Gameplay",
            Self::Light => "Light",
            Self::AtmosphereProfile => "Atmosphere",
            Self::WeatherProfile => "Weather",
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum ElevationBrushPolicy {
    Preserve,
    SetLevel,
    RaiseBy,
    LowerBy,
    MatchSample,
}

impl ElevationBrushPolicy {
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Preserve => "Preserve",
            Self::SetLevel => "Set Level",
            Self::RaiseBy => "Raise By",
            Self::LowerBy => "Lower By",
            Self::MatchSample => "Match Sample",
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum StructuralBakePolicy {
    Preserve,
    Automatic,
    Suggest,
    ExplicitOnly,
}

impl StructuralBakePolicy {
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Preserve => "Preserve",
            Self::Automatic => "Automatic",
            Self::Suggest => "Suggest",
            Self::ExplicitOnly => "Explicit Only",
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub(crate) struct CanvasAuthoringContext {
    pub layer: Option<CanvasLayerKind>,
    pub tool: UniversalTool,
    pub brush_mode: BrushMode,
    pub source_kind: BrushSourceKind,
    /// Stable semantic resource id when the palette has a concrete source.
    pub source_id: Option<String>,
    pub elevation_policy: ElevationBrushPolicy,
    pub elevation_level: u8,
    pub cliff_policy: StructuralBakePolicy,
    pub ramp_policy: StructuralBakePolicy,
    pub brush_radius: u8,
}

impl Default for CanvasAuthoringContext {
    fn default() -> Self {
        Self {
            layer: None,
            tool: UniversalTool::Select,
            brush_mode: BrushMode::None,
            source_kind: BrushSourceKind::None,
            source_id: None,
            elevation_policy: ElevationBrushPolicy::Preserve,
            elevation_level: 0,
            cliff_policy: StructuralBakePolicy::Automatic,
            ramp_policy: StructuralBakePolicy::ExplicitOnly,
            brush_radius: 1,
        }
    }
}

impl CanvasAuthoringContext {
    pub(crate) fn compact_source_label(&self) -> String {
        self.source_id
            .as_deref()
            .map(compact_resource_label)
            .unwrap_or_else(|| self.source_kind.label().to_string())
    }

    pub(crate) fn sync(&mut self, viewport: EditorViewportMode, layer: Option<CanvasLayerKind>, tool: UniversalTool) {
        self.layer = layer;
        self.tool = tool;
        let previous_source_kind = self.source_kind;
        let preferred = default_brush_mode(viewport, layer, tool);
        if !brush_mode_compatible(viewport, layer, tool, self.brush_mode) {
            self.brush_mode = preferred;
        }
        self.source_kind = source_kind_for(self.brush_mode);
        // H21-A14: never carry a stale source across incompatible brush kinds.
        // Terrain -> Collision, for example, must not leave Grass displayed as
        // the active collision source. Compatible modes keep their selection.
        if self.source_kind != previous_source_kind {
            self.source_id = None;
        }
        if self.brush_mode == BrushMode::TerrainElevation && self.elevation_policy == ElevationBrushPolicy::Preserve {
            self.cliff_policy = StructuralBakePolicy::Automatic;
        }
    }
}

pub(crate) fn compatible_brush_modes(
    viewport: EditorViewportMode,
    layer: Option<CanvasLayerKind>,
    tool: UniversalTool,
) -> &'static [BrushMode] {
    use BrushMode as B;
    use CanvasLayerKind as L;
    use UniversalTool as T;

    if viewport == EditorViewportMode::PixelStudio {
        return match tool {
            T::Paint | T::Erase | T::Fill | T::Rectangle | T::Ellipse | T::Line | T::Gradient
            | T::Blur | T::Smudge | T::Lighten | T::Darken => &[B::Pixel],
            _ => &[B::None],
        };
    }
    match (layer, tool) {
        (Some(L::Terrain), T::Paint | T::Fill | T::Rectangle) => &[B::SemanticTerrain, B::Autotile, B::TerrainElevation, B::ExactTile],
        (Some(L::TerrainTransitions), T::Paint | T::Place) => &[B::Autotile, B::ExactTile, B::VisualOverride],
        // Structural connector authoring is selection-first: Select keeps the
        // Elevation semantic active so Ramp/Ladder can resolve a complete cliff
        // host from a marquee before the user explicitly commits it.
        (Some(L::StructuralLevels), T::Select) => &[B::Elevation],
        (Some(L::StructuralLevels), T::Paint | T::Rectangle | T::Place) => &[B::Elevation, B::TerrainElevation, B::Stamp],
        (Some(L::Water), T::Paint | T::Rectangle | T::Place) => &[B::Hydrology, B::Stamp],
        (Some(L::Collision), T::Paint | T::Collision | T::Rectangle | T::Fill) => &[B::Collision],
        (Some(L::Navigation), T::Paint | T::Rectangle | T::Fill) => &[B::Navigation],
        (Some(L::Vegetation | L::Resources | L::Objects | L::Props | L::Furniture | L::Buildings | L::Structures), T::Paint | T::Place | T::Rectangle) => &[B::Object, B::Stamp, B::Scatter],
        (Some(L::Triggers | L::Zones | L::Interaction | L::SpawnPopulation | L::BuildabilityFarming), T::Paint | T::Place | T::Rectangle) => &[B::GameplayRegion],
        (Some(L::Lighting), T::Paint | T::Place | T::Rectangle) => &[B::Lighting],
        (Some(L::Atmosphere), T::Paint | T::Place | T::Rectangle) => &[B::Atmosphere],
        (Some(L::Weather), T::Paint | T::Place | T::Rectangle) => &[B::Weather],
        (Some(L::AuthoredPixels), T::Paint | T::Erase | T::Fill | T::Pick) => &[B::Pixel, B::VisualOverride],
        (_, T::Place) => &[B::Stamp],
        _ => &[B::None],
    }
}

pub(crate) fn default_brush_mode(
    viewport: EditorViewportMode,
    layer: Option<CanvasLayerKind>,
    tool: UniversalTool,
) -> BrushMode {
    compatible_brush_modes(viewport, layer, tool)
        .iter()
        .copied()
        .find(|mode| *mode != BrushMode::None)
        .unwrap_or(BrushMode::None)
}

pub(crate) fn brush_mode_compatible(
    viewport: EditorViewportMode,
    layer: Option<CanvasLayerKind>,
    tool: UniversalTool,
    mode: BrushMode,
) -> bool {
    compatible_brush_modes(viewport, layer, tool).contains(&mode)
}

pub(crate) fn source_kind_for(mode: BrushMode) -> BrushSourceKind {
    match mode {
        BrushMode::None => BrushSourceKind::None,
        BrushMode::Pixel => BrushSourceKind::PixelColor,
        BrushMode::ExactTile | BrushMode::VisualOverride => BrushSourceKind::AtlasCell,
        BrushMode::Stamp => BrushSourceKind::Stamp,
        BrushMode::SemanticTerrain | BrushMode::Autotile | BrushMode::TerrainElevation => BrushSourceKind::TerrainMaterial,
        BrushMode::Elevation => BrushSourceKind::StructuralRecipe,
        BrushMode::Hydrology => BrushSourceKind::TerrainMaterial,
        BrushMode::Collision => BrushSourceKind::CollisionSemantic,
        BrushMode::Navigation => BrushSourceKind::NavigationSemantic,
        BrushMode::Object | BrushMode::Scatter => BrushSourceKind::Object,
        BrushMode::GameplayRegion => BrushSourceKind::GameplaySemantic,
        BrushMode::Lighting => BrushSourceKind::Light,
        BrushMode::Atmosphere => BrushSourceKind::AtmosphereProfile,
        BrushMode::Weather => BrushSourceKind::WeatherProfile,
    }
}

fn compact_resource_label(value: &str) -> String {
    let leaf = value.rsplit(|c| c == '/' || c == '.').find(|segment| !segment.is_empty()).unwrap_or(value);
    let mut out: String = leaf.chars().take(13).collect();
    if leaf.chars().count() > 13 { out.push('…'); }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn terrain_paint_exposes_semantic_autotile_elevation_and_exact_modes() {
        let modes = compatible_brush_modes(EditorViewportMode::SceneRectangles, Some(CanvasLayerKind::Terrain), UniversalTool::Paint);
        assert!(modes.contains(&BrushMode::SemanticTerrain));
        assert!(modes.contains(&BrushMode::Autotile));
        assert!(modes.contains(&BrushMode::TerrainElevation));
        assert!(modes.contains(&BrushMode::ExactTile));
    }

    #[test]
    fn lighting_weather_and_atmosphere_are_not_generic_pixel_brushes() {
        assert_eq!(default_brush_mode(EditorViewportMode::SceneRectangles, Some(CanvasLayerKind::Lighting), UniversalTool::Place), BrushMode::Lighting);
        assert_eq!(default_brush_mode(EditorViewportMode::SceneRectangles, Some(CanvasLayerKind::Atmosphere), UniversalTool::Paint), BrushMode::Atmosphere);
        assert_eq!(default_brush_mode(EditorViewportMode::SceneRectangles, Some(CanvasLayerKind::Weather), UniversalTool::Paint), BrushMode::Weather);
    }

    #[test]
    fn pixel_studio_keeps_pixel_authority() {
        assert_eq!(default_brush_mode(EditorViewportMode::PixelStudio, Some(CanvasLayerKind::PixelLayer), UniversalTool::Paint), BrushMode::Pixel);
    }

    #[test]
    fn incompatible_brush_kind_clears_stale_palette_source() {
        let mut context = CanvasAuthoringContext::default();
        context.brush_mode = BrushMode::Autotile;
        context.source_kind = BrushSourceKind::TerrainMaterial;
        context.source_id = Some("tile/grass".to_string());
        context.sync(EditorViewportMode::SceneRectangles, Some(CanvasLayerKind::Collision), UniversalTool::Paint);
        assert_eq!(context.brush_mode, BrushMode::Collision);
        assert_eq!(context.source_kind, BrushSourceKind::CollisionSemantic);
        assert!(context.source_id.is_none());
    }
}


impl EditorApp {
    pub(crate) fn sync_canvas_authoring_context(&mut self) {
        let layer = self.active_canvas_layer_kind();
        self.canvas_authoring_context
            .sync(self.viewport_mode, layer, self.canvas_active_tool);
        self.canvas_authoring_context.brush_radius = self.world_brush_radius.clamp(1, 255) as u8;
        self.canvas_authoring_context.elevation_level = self.world_structural_level;
    }

    pub(crate) fn select_canvas_brush_mode(&mut self, mode: BrushMode) -> bool {
        let layer = self.active_canvas_layer_kind();
        if !brush_mode_compatible(self.viewport_mode, layer, self.canvas_active_tool, mode) {
            return false;
        }
        let previous_source_kind = self.canvas_authoring_context.source_kind;
        self.canvas_authoring_context.brush_mode = mode;
        self.canvas_authoring_context.source_kind = source_kind_for(mode);
        if self.canvas_authoring_context.source_kind != previous_source_kind {
            self.canvas_authoring_context.source_id = None;
        }
        self.brush_palette_offset = 0;
        self.workspace_shell.shared_palette_visible = true;
        self.status_message = format!("Brush mode: {}", mode.label());
        true
    }


    pub(crate) fn canvas_palette_context_title(&self) -> String {
        let layer = self.active_canvas_layer_kind()
            .map(layer_short_label)
            .unwrap_or("Canvas");
        format!("{} • {}", layer, self.canvas_authoring_context.brush_mode.label())
    }
}

pub(crate) fn layer_short_label(layer: CanvasLayerKind) -> &'static str {
    use CanvasLayerKind as L;
    match layer {
        L::Terrain => "Terrain",
        L::TerrainTransitions => "Transitions",
        L::StructuralLevels => "Elevation",
        L::Water | L::WaterSwim => "Water",
        L::RoadsPaths => "Roads",
        L::Vegetation => "Vegetation",
        L::Resources => "Resources",
        L::Structures | L::Buildings => "Structures",
        L::Furniture => "Furniture",
        L::Props | L::Objects => "Objects",
        L::Collision => "Collision",
        L::Navigation => "Navigation",
        L::Lighting => "Lighting",
        L::Atmosphere => "Atmosphere",
        L::Weather => "Weather",
        L::Triggers | L::Zones | L::Interaction | L::SpawnPopulation | L::BuildabilityFarming => "Gameplay",
        L::AuthoredPixels | L::PixelLayer => "Pixels",
        _ => "Canvas",
    }
}
