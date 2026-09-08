# H21 A9-A14 — Canvas Ownership + Palette Normalization

This pass closes the first visible overlap/duplication problems found during H21 acceptance.

## Locked ownership

- **Tool Rail**: permanent left vertical action surface.
- **Tool Shelf**: bottom of Tool Rail; current source, brush mode, Palette toggle.
- **Palette Panel**: reserved bottom-of-Canvas contextual source/color panel for the active Layer + Tool + Brush. It is not the Project Asset Browser and never overlays authored content.
- **Project Asset Browser**: remains in the right Workspace Dock and answers “what exists in the project?”.
- **Layers**: dedicated opaque sibling panel between Tool Rail and Canvas; it owns real layout width and never paints over authored content.
- **Properties**: inspection/provenance and selected-region actions only; no duplicate layer/tool/brush controls.

## Layer groups

World/scene authoring uses four primary groups:

1. Surface — Terrain, Elevation, Hydrology, Roads & Paths.
2. Content — Vegetation, Resources, Structures/Buildings, Objects/Props, NPCs/Creatures.
3. Simulation — Lighting, Atmosphere, Weather, Collision, Navigation, Gameplay.
4. Overrides — Visual Overrides and Generated/Derived reference state.

## Palette behavior

Pixel mode continues to use the shared Pixel Studio color palette. Non-pixel modes use a brush-aware palette:

- Terrain/Autotile/Terrain+Elevation: compatible runtime-ready terrain resources only.
- Exact Tile/Visual Override: runtime-ready exact tile resources.
- Stamp: reusable stamps only.
- Object/Scatter: compatible placeables/stamps only.
- Lighting: lighting-capable placeables only.
- Collision, Navigation, Gameplay, Elevation, Atmosphere and Weather: semantic choices, not generic asset-browser cards.

Changing to an incompatible brush source kind clears the stale source so Grass can never remain displayed as the source for Collision, Weather, etc.

## Reuse-first LPC direction

The new `lpc_semantic_bridge_v0_1.json` records the engine-independent semantic/provenance contract distilled from the wider LPC ecosystem audit. Existing Havenwild/ULPC/LPC assets stay in place; stable semantic IDs, certification, provenance and brush compatibility are layered over them. Havenwild structural gameplay grammar remains authoritative above visual LPC recipes.

## Acceptance targets

- No canvas-side duplicate Asset Browser.
- Palette button lives in Tool Rail and shows/hides the reserved contextual Palette panel.
- Properties dock contains no duplicate mutating world authoring controls.
- World title/header, Layers panel, rulers, and Palette panel have non-overlapping reserved geometry.
- World/scene layer lists are reduced and grouped by authoring intent.
- Pixel Studio palette behavior remains intact.
- Switching brush source kinds clears incompatible stale palette selections.
