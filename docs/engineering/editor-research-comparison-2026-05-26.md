# Editor Research Comparison - 2026-05-26

This note maps the editor patterns we researched against the current native Rust editor. The goal is not to clone any single tool, but to make our editor carry the same production ideas: explicit layers, command-backed changes, focused inspectors, validation, asset-aware palettes, and scalable world authoring.

## Current Alignment

| Researched system pattern | Local source / model | Current status | Reshape action |
| --- | --- | --- | --- |
| Tiled-style map layers | Terrain, object, zone, transition layers | Started | Native Scene Map now has F1-F4 authoring layers so the canvas can be read as separate terrain, object, zone, and transition surfaces. Terrain, object, zone, transition create/erase, and transition resize edits are command-backed. |
| LDtk-style level/entity separation | Scene rectangles + world graph + scene maps | Started | Region Graph, Scene Rectangles, and Scene Map are separate viewport modes. Scene Map now exposes cursor tile, object, zone, and transition data in the inspector. |
| Shared command model | `haven_editor::scene_edit` and command bus specs | Started | Tile paint, object place, erase, scene rectangle assignment, save, load, and viewport/layer changes are recorded through the native command bus. Undo exists for world edits. |
| Tiled/LDtk validation loops | Validation panel and registry | Partial | Native editor shows validation report and registry status, but messages still need scoped click-through references to scene, layer, and tile/object coordinates. |
| Object layer + property inspector | Tiled object layer / LDtk entities | Partial | Cursor inspector reports selected cell object and transition. Object place/select/move/duplicate/erase are command-backed, and selected objects are outlined in the map. Next step is an object outliner with editable footprint/properties. |
| Rule-based auto-tiling | Tiled Wang sets / LDtk rules | Planned | Terrain layer is ready to host this, but we still need the Rust auto-tile rule asset format, dirty-neighbor invalidation, and preview/apply command path. |
| Pixel editor workflow | Pixelorama / LibreSprite / Aseprite | Planned | Asset registry and animation contract exist. Native app still needs palette, sprite sheet, frame timeline, and generated asset preview workspaces. |
| Docked production UI | External editor specs | Partial | Current Macroquad panels are functional but fixed. Long-term spec still calls for a proper docked Rust editor shell, likely egui/eframe or equivalent. |

## Critical Gaps

1. Layer tools are visible, and terrain/object/zone/transition edits are command-backed. Transition property editing is still needed.
2. Auto-tiling needs to become a first-class terrain-layer system, not a rendering afterthought.
3. Object authoring has place/select/move/duplicate/erase. Property editing, an outliner, and footprint editing are still needed.
4. The island/world generation preview must stay separate from scene map editing: the island landmass defines where scenes live, while scene maps define playable local spaces.
5. Asset packs need searchable palettes and generated/third-party asset provenance in the editor itself.
6. Animation import needs sprite sheet slicing, clip metadata, and character preview playback before it can feed gameplay confidently.
7. Validation should be actionable: each issue should identify workspace, scene, layer, coordinate/object id, and the command that would repair it when possible.

## Next Development Path

1. Finish Scene Map layer editing: transition property edit, object outliner, footprint editing, and command-preview validation before apply.
2. Implement the terrain auto-tile data model: terrain rule config, 4-way/8-way or dual-grid mask calculation, deterministic variation, dirty-neighbor invalidation, and atlas lookup.
3. Add an object/entity outliner and property inspector for scene objects, transitions, spawners, and interactable metadata.
4. Bring the island-generation view back as its own world-shape workspace, using scene rectangles/region nodes as overlays instead of drawing tavern-scale scene content over the island.
5. Add asset browser shelves for imported packs, generated assets, tile palettes, object palettes, and animation clips.
6. Introduce a dockable UI shell once the workflows stabilize, keeping the shared command/editor core reusable by the native app and runtime overlay.

## Asset Generation Still Needed

| Asset family | Needed for |
| --- | --- |
| Terrain auto-tile atlas pieces | Grass, dirt, sand, shore, water, cave, cliff, floor, wall, path, crop, bridge transitions. |
| Zone/transition editor overlays | Non-gameplay editor-only colors/icons for spawn points, exits, blockers, zones, and warnings. |
| Object thumbnails | Tables, chairs, beds, doors, stairs, trees, ore nodes, cave entrances, greenhouse markers, tavern props. |
| Character animation previews | Idle, walk, tool-use, carry, interact, emote, and directional variants from the animation library. |
| UI icons | Layer, brush, erase, fill, eyedropper, rectangle, object, zone, transition, validate, undo, redo, save, reload. |
