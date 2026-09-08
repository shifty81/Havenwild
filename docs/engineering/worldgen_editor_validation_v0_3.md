# Worldgen Editor Validation v0.3

This pass turns the generated art/manifest package into editor-loadable worldgen data.

## Core rule

The editor should treat art, collision, interactions, zones, and scene transitions as separate layers. A tree, wall, tavern facade, table, or cave mouth can occupy more visual tiles than collision tiles.

## Required editor panels

1. **Layer Stack** — toggles terrain, autotile preview, zones, objects, collision, interactions, occlusion fade, scene edges, and validation overlays.
2. **Scene Outliner** — lists scene objects, transitions, player spawns, generated border fillers, and unresolved warnings.
3. **Footprint Inspector** — edits visualRect, collisionRect, interactionRects, fadeWhenPlayerBehind, layer, and placement locks.
4. **Scene Edge Resolver** — previews each edge using adjacent world-surface data, never raw void.
5. **Validation Console** — runs the same validator as the script and highlights invalid objects/tiles/transitions in scene view.

## v0.3 generated scene format

Each scene lives under:

```text
content/worldgen/scenes/home_island/*_scene_v0_3.json
```

A scene contains:

```text
sceneSize
layers.terrain
layers.zones
objects[].visualRect
objects[].collisionRect
objects[].interactions[]
transitions[]
spawns[]
edgePolicy.resolvedBorders
```

## Validation gates

The editor should block save when:

- a scene layer does not match scene size
- a tile name does not match runtime TileKind
- object visual/collision rectangles leave the scene bounds
- a scene edge resolves to void
- a required return transition is missing
- a spawn is outside the scene

The editor may warn, not block, when:

- visualRect is much larger than collisionRect
- seating exceeds current tavern occupancy cap
- decorative objects overlap other decorative objects
- a reserved world-surface neighbor has not yet been authored

## Scene-edge policy

Scene edges are not empty space. The renderer should use generated border assets according to:

```text
content/worldgen/world_edge_border_resolution_v0_3.json
content/worldgen/home_island_world_surface_v0_3.json
```

For interiors and caves, the fallback edge is a black/darkness mask. For exteriors, it is a dense forest, city, cliff, field, mountain, or coast border.

## Next implementation step

Wire the editor to load `content/packs/worldgen_home_island_v0_3.json`, list the generated scene files, draw the terrain grid, draw object visual/collision rectangles, and run validator output into the Validation Console.
