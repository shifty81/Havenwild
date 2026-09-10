# Havenwild Game Canvas Workflow V2

Pass: `HW-EDITOR-GAP-AUDIT-02`  
Behavioral scope: specification only

## Primary creator loop

Havenwild authoring is centered on one Game Canvas. The creator should not need to know which legacy subsystem owns an edit.

`Select layer -> choose definition/material/asset -> choose applicable tool -> author on canvas -> inspect/edit properties -> save -> PIE`

Changing the active layer changes the contextual palette and applicable tools. It must not require opening a second editor for ordinary world construction.

## Creator-facing nouns

The V2 UI deliberately reduces terminology.

- **Source Sheet** — immutable imported atlas/spritesheet/source image. It is a container, not normally a placeable asset.
- **TileSet** — source-sheet slicing plus stable tile IDs, transformations and per-tile metadata.
- **Material** — semantic paint value such as grass, sand, water, road or a structural surface. A material resolves to visual tiles.
- **Asset** — reusable project resource such as a sprite, animation, sound, item visual or tile family.
- **Entity Definition** — reusable gameplay definition with typed fields/constraints: Player Start, NPC, animal, spawner, trigger, transition marker, light, sound emitter, etc.
- **Instance** — a placed reference to an Asset, Entity Definition or Prefab with per-instance overrides.
- **Prefab** — reusable multi-part authored content with semantic identity, such as a house, cave entrance, dock, shop or configured object assembly.
- **Brush** — editor-only reusable paint/stamp selection. Brushes accelerate placement but are not gameplay identities.
- **Rule** — data-driven automatic resolution/generation logic for terrain, structures or PCG.

Legacy internal terms such as Stamp, Pattern, ObjectKind-specific placement paths and specialized editor tabs may remain temporarily as adapters, but they should not create additional creator-facing concepts when one of the nouns above already covers the use case.

## Game Canvas layer model

The normal creator view uses seven collapsible groups. Internal storage may remain more granular.

1. **Surface** — Terrain, Water, Roads/Paths.
2. **Structure** — Elevation, Cliffs, Ramps/Stairs/Ladders, Bridges, Buildings.
3. **Content** — Vegetation, Resources, Props, Furniture.
4. **Entities** — Player Start, NPCs, Animals, Spawners and authored runtime entities.
5. **Gameplay** — Zones, Triggers, Transitions/Links, Interaction, Collision, Navigation.
6. **Presentation** — Lighting, Weather, Atmosphere, Effects, Sound Emitters.
7. **Overrides** — Raw Tiles, authored visual overrides, debug/reference guides.

Visibility, lock, opacity and generated/derived/manual status are visible in the layer tree. Advanced child layers may be hidden by default.

## Contextual palette and Place workflow

There is no separate Spawn tool or Spawn window.

The standard **Place** operation places the active compatible definition:

- Entities + Player Start + Place
- Entities + NPC + Place
- Entities + Animal Spawner + Place
- Gameplay + Transition Destination + Place
- Structure + Cottage Prefab + Place
- Content + Oak Tree + Place

`Player Start` is a unique Entity Definition. Placing it when one already exists moves/replaces the existing instance according to the definition constraint.

`Play From Here` is not a persisted entity. It is an editor/runtime launch command available from the Play dropdown and canvas context menu. `Set Player Start Here` is a separate persisted authoring command.

## Tile and atlas authoring

Selecting a TileSet or Material exposes **Open Atlas**. The Atlas Inspector can be docked or floated and supports nearest-neighbor zoom/pan, grid visibility, tile metadata inspection and:

- single-tile selection;
- rectangular region selection;
- non-contiguous selection where supported;
- semantic slices/subassets;
- animation/alternative variants;
- legal rotate/mirror/flip operations;
- drag/drop or paint directly onto the Game Canvas.

Raw atlas placement writes to an explicit manual override lane. It never silently changes the semantic source layer.

## Terrain modes

Any compliant Material can use the same terrain authoring operations. Water, sand, ponds, grass, dirt and roads do not gain bespoke UI or renderer branches merely because of their names.

The primary terrain modes are:

- **Connect** — continuously resolve to compatible neighboring semantic materials.
- **Path** — resolve within the current stroke, useful for roads/rivers/walls that may touch without merging.
- **Exact/Manual** — place the chosen tile/variant without automatic neighbor mutation.
- **Fill/Rectangle/Replace/Pick** — normal scope-aware operations using the same material definition.

Automatic visuals are derived from semantic authoring data. The creator can toggle generated presentation to inspect the semantic layer underneath.

## Brushes, Prefabs and PCG

A canvas selection can become:

- **Create Brush** — editor convenience for repeated tile/material placement.
- **Create Prefab** — reusable semantic multi-part content with fields, collision/interaction and instance overrides.
- **Create PCG Exemplar** — advanced operation that captures an approved authored arrangement as rule/generation training/reference data.

World generation must consume the same Materials, Entity Definitions, Prefabs, structural recipes and rule outputs that the Game Canvas uses. PCG must not own a second visual vocabulary.

## Inspector

One contextual Inspector edits the selected layer, definition, asset, tile, prefab or instance. It supports multi-selection when fields are compatible, shows inherited/default values separately from instance overrides and provides navigation to the owning definition/source.

Tile metadata may include collision, navigation, occlusion, interaction/surface flags, audio surface, animation, terrain membership, transform permissions, variation weight, provenance and license data.

Entity fields are typed and constrained. Behavior/dialogue/quest/shop bindings link to the shared Logic/Behavior system instead of embedding a second event language in the map editor.

## World/scene navigation

The full finite Havenwild archipelago remains the world authority. Game Canvas provides world overview, direct chunk/scene navigation, bookmarks, search/go-to-coordinate and neighboring-scene navigation. Detailed chunks/scenes materialize lazily.

World, Scene, Scene Library, Routes and UI are views/documents inside Game Canvas, not separate global authoring philosophies.

## PIE and runtime parity

The toolbar provides Play, Play From Here, Pause/Resume, Restart and Stop. Native Editor, Runtime Edit and automation must resolve equivalent authoring actions to the same stable IDs, coordinates, layer semantics, transactions, validation and persistence.

The editor may use diagnostic overlays, but normal world pixels must resolve through the same asset/material/structure authority used by the client. Proxy visuals may not silently stand in for runtime-ready content.

## F3 developer experience

F3 toggles a lightweight in-game developer overlay only. It does not automatically enter Build/Edit mode.

Default F3 provides inspect, selected-target details, performance summary, current scene/chunk/cell, quick teleport/debug-spawn and optional diagnostic overlays. Runtime Edit is entered explicitly and then exposes a compact version of the same layer -> palette -> tool -> inspector workflow.

F3 drawing is cache/visibility driven. No catalog JSON/SQLite scanning, source discovery, complete-world manifest reconstruction or broad off-screen iteration is allowed in the per-frame UI draw path unless explicitly profiled and bounded.
