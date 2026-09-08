# In-Game Editor Spec

Havenwild Prototype should be editable from inside the running game. The overlay is a dockable/minimizable tool surface, not a separate debug screen. The player should be able to build scenes, author rules, validate links, regenerate terrain, and save the result as game content.

## Overlay Goals

- Toggle with `F3`; construction mode with `B`.
- Overlay panels must block accidental world painting beneath them.
- Every destructive edit should support undo/redo.
- Hotkeys are optional accelerators; primary workflows should be clickable.
- Saved edits must become the actual game world on next launch.

## Current Prototype Capabilities

The current standalone prototype already supports:

- scene-based world editing rather than a single global map
- tile, object, zone, and transition editing
- save/load to `workspace/saves/world.tworld`
- undo/redo snapshots
- scene switching and per-scene spawn editing
- transition validation and a simple world graph panel
- per-tile interaction rules
- persisted per-tile heights saved with each scene map
- seeded heightmap generation with biome, water, and cliff controls
- live map-tab height painting with raise/lower/smooth brushes
- bridge placement over generated water and shallow water
- neighbor-aware autotile rendering for connected roads, water, walls, and floors
- y-sorted prop/NPC/player depth layering so actors can walk behind tall objects
- expanded terrain palette for sand, wet sand, pebble shore, mountain path, cliff, mountain rock, shallow water, and deep water
- anchor-aware GUI panel layout with live drag editing, 16px grid snapping, and saved panel positions
- minimized editor overlay mode

This means the editor is already beyond the mockup stage. The next work should focus on stronger world-authoring workflows and tile-system data, not on replacing the current architecture.

## Tabs

- Tiles: terrain, floor, walls, water, cave tiles, hoe, greenhouse.
- Objects: tavern furniture, beds, storage, doors, stairs, natural resources.
- Zones: tavern, kitchen, guest room, cellar, greenhouse, field, cave, staff-only.
- Rules: per-tile interaction behavior.
- Map: heightmap/noise generation, biome presets, water, cliffs, rivers, lakes, shores, mountains, bridges, and height brushes.
- World: scenes, transitions, spawn points, validation, save/load.

## Map Editor V1

- Generate active scene from a seed and biome preset.
- Save per-cell height values alongside tile/object data.
- Use noise plus biome bias to determine coastlines, uplands, and mountain ridges.
- Water level controls deep/shallow water and shoreline bands.
- Cliff level controls cliffs, mountain rock, and highland path bands.
- Raise/Lower/Smooth brushes edit the saved height field directly in the running scene.
- Repaint resolves the terrain families from the current saved height field without regenerating noise.
- Transition exits carve road openings so generated scenes remain traversable.
- Bridge tool converts cursor area to walkable bridge spans over water.

## GUI Layout Editor V1

- Toggle layout edit with `L` while dev mode is active.
- Panel movement happens by dragging panel title bars.
- Layout positions snap to a **16px grid**.
- Panels store:
  - anchor
  - snapped grid X/Y offset
  - panel width/height
- Saved layout data lives beside the world save so panel placement persists between sessions.
- Current layout-editable panels are:
  - main HUD panel
  - editor overlay
  - inspector
  - validation panel
  - world graph

### Layout Rules

- Anchors must be resolution-relative, not hard-coded absolute screen corners.
- Offsets should be stored in snapped grid units so scaling remains stable.
- Width/height can remain explicit in V1, but future layout templates should support tokenized sizes and panel presets.
- The in-game overlay is the authoritative live layout editor; the web editor should eventually preview the same saved layout format.

## World Tile Expansion V2

Best implementation approach:

1. Keep the existing scene grid as the top-level world structure.
2. Add richer tile metadata instead of multiplying hard-coded tile enums too early.
3. Resolve art variants through autotiling and biome presets.
4. Keep terrain, zones, objects, transitions, and rules as separate editable layers.

### Authoring Layers

The editor should treat a scene as:

- base terrain
- terrain variant/autotile mask
- zone overlay
- object layer
- transition layer
- rule/spawner layer

### Features To Add Next

Highest priority:

- rectangle select/copy/paste
- flood fill and replace-by-tile tools
- autotile rules for roads, water, cave walls, cliffs, and floors
- scene create/delete/duplicate tools
- transition inspector with label, size, target, and destination spawn editing
- minimap with zone and transition overlays
- tile palette categories by biome and layer
- reusable scene stamps and prefabs

Second wave:

- decoration scatter tools for grass clutter, rocks, weeds, and cave debris
- biome presets for farm, woods, road, cave, tavern exterior, and town
- pathing validation for customers, staff, and traversal
- persistent resource/node/NPC spawner editing
- script/event hook editor for rule tiles and placed objects

## Tile Rules V1

Each tile kind has a saved interaction behavior:

- None
- Forage
- Hoe
- Water
- Harvest
- Rest
- Blocked
- Enter

These are placeholders for later scripting. The next step is to let object and tile rules call named scripts/events such as `on_interact`, `on_day_start`, `on_step`, and `on_tool_used`.

## Asset Workflow

- Keep original/free/imported raw assets under `assets/raw`.
- Keep generated placeholder assets under `assets/generated`.
- Every generated pack should have a manifest describing tile size, source script, license, and intended replacement path.
- Prototype assets should be replaceable without touching gameplay logic.

## Near-Term Next Steps

- Add minimizable/dockable overlay state.
- Add rectangle select/copy/paste.
- Add object property editor.
- Add script/event editor for tile and object interactions.
- Add autotile rules for water, cliffs, roads, and floors.
- Add scene templates and biome presets.
