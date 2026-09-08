# H21 Unified Game Canvas Brush + Environment Foundation

This pass begins the reuse-first conversion of the existing Havenwild native editor into the unified Game Canvas authoring model.

## Locked architecture

- The existing `UniversalTool` registry remains the tool authority.
- `CanvasLayerKind` remains the layer identity authority; Layers use a dedicated sibling panel so layer controls never overlap the authored canvas.
- The existing asset catalog feeds the reserved Canvas Palette panel for contextual resource choices. Pixel Studio feeds that same panel from the active document palette.
- `CanvasAuthoringContext` is the shared state joining active layer, tool, brush mode, source resource, brush radius, elevation policy, cliff policy, and ramp policy.
- Existing assets retain stable ids and paths. `AssetPaletteEntry` now derives brush-resource class and compatible brush capabilities rather than creating duplicate assets.
- Terrain/elevation authoring distinguishes semantic terrain, autotile, exact tile, stamp, elevation, and combined terrain+elevation intent. Cliff visuals remain derived from structural elevation truth.
- Lighting, Atmosphere/Fog, and Weather are distinct first-class canvas layers. Exploration/map fog remains unrelated to atmospheric fog.
- Environment data begins with deterministic, serializable time-of-day, light, atmosphere, weather, environment-profile, and environment-volume contracts.

## Tool Shelf / Palette behavior

The permanent vertical Tool Rail exposes every applicable tool directly and scrolls vertically when needed. Compatible brush modes are explicit buttons rather than a blind cycle action. Palette toggles a reserved bottom-of-Canvas panel; opening it reduces only the authored viewport and never covers it.

For World/Scene authoring the panel reuses the canonical asset catalog. For Pixel Studio it uses the active document palette, including left-click FG, right-click BG, and transactional add-color workflows. Asset selection writes the stable resource id into `CanvasAuthoringContext` and re-synchronizes compatible authoring state.

## First combined brush contract

The `TerrainElevation` mode represents the intended workflow for presets such as **Grassy Level-2 Plateau**:

1. semantic terrain source (`terrain.grass`),
2. structural elevation policy (`set_level = 2`),
3. connected cliff bake (`automatic`),
4. ramp policy (`explicit_only` by default),
5. derived collision/navigation updates performed by existing authorities in later execution wiring.

This pass establishes the context/capability contract and does not replace the existing terrain, structural cliff, collision, navigation, Pixel Studio, or asset authorities.

## Environment foundation

`haven_world::environment_system` introduces versioned data contracts for:

- outdoor/interior/cave/underground environment profiles,
- time-of-day stages,
- placed light profiles,
- atmospheric fog/mist/haze profiles,
- weather profiles,
- environment volumes with blend boundaries.

The initial content catalog includes standard day/night stages, clear/morning/cave/storm atmosphere, clear/rain/thunderstorm weather, and warm lantern/fireplace lights. Renderer and simulation execution remain subsequent passes; this pass intentionally establishes a stable data/editor contract first.

## Acceptance target

After building on Windows, verify that the Palette is a reserved bottom Canvas panel, Layers remain a dedicated sibling panel, all applicable tools are directly reachable on the scrollable Tool Rail, changing layers re-contextualizes brush mode, Pixel Studio Palette uses the active document palette, and World/Scene Palette uses existing assets. Lighting, Atmosphere/Fog, and Weather should appear as distinct authoring layers even before their full runtime rendering passes land.
