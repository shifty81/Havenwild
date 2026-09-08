# World Scene Map

The world is split into traversable scenes connected by transition rectangles. This lets us build a massive world as many editable maps instead of one enormous tile sheet.

## Scene Scale

The active prototype scene size is 48x32 tiles. That is a compact playable slice, not a full island map.

Use scenes like camera-sized chunks of the world:

- `Farmstead` is the local exterior around the first tavern.
- `SouthField` is a separate farming expansion scene.
- `EastWoods` is a separate woods/forage scene.
- `NorthRoad` is a connector toward future town/city content.
- `CaveMouth` is a separate cave entrance/exterior scene.

The starter island or region should be represented by a graph of these scenes. Do not draw the whole island silhouette inside `Farmstead` and then scale the tavern, farm, and cave over it. If the tavern footprint is visually comparable to the island footprint, the preview is using the wrong scale.

## Implemented Scenes

- `Farmstead`: exterior tavern hub, crop plots, greenhouse marker, cave entrance, road edges.
- `TavernInterior`: service floor with bar, kitchen area, tables, cellar stairs, guest-floor stairs.
- `Cellar`: production/storage space for kegs and future aging shelves.
- `GuestFloor`: inn rooms and future rentable bedroom workflow.
- `NorthRoad`: road connector toward future town/city content.
- `SouthField`: larger farm field for crops and greenhouse experiments.
- `EastWoods`: forage/tree/resource connector.
- `CaveMouth`: cave entrance scene with ore nodes.
- `CaveDepths`: deeper cave/resource scene.

## Transition Model

Every door, edge exit, cave mouth, and stairway is represented as:

```text
source scene + rectangle -> target scene + spawn tile
```

This keeps all traversal consistent. In non-dev play, stepping on a transition moves the player. In dev mode, transitions are visible and can be placed/erased/saved.

## Dev Controls

- `F3`: dev mode
- `B`: construction overlay
- `PageUp/PageDown`: cycle active scene
- `[` / `]`: choose transition target
- transition tool: place a one-tile transition to the selected target
- arrow keys: resize hovered transition
- `,` / `.` / `;` / `/`: adjust hovered transition spawn X/Y
- `P`: set current scene spawn at cursor
- `V`: validate world graph
- `G`: toggle world graph panel
- erase tool: deletes tile/object/transition at the cursor
- `F5`: save world to `workspace/saves/world.tworld`
- `F9`: load saved world

## Zone Layers

Dev mode now paints zone overlays separately from tile art:

- Tavern
- Kitchen
- Guest Room
- Cellar
- Greenhouse
- Field
- Cave
- Staff Only

Zones are saved with the world and are intended to drive validation, customer behavior, staff assignments, construction rules, crop rules, and room scoring.

## Next Steps

- Add named transition inspector editing: width, height, target spawn tile, label.
- Add scene creation/deletion from dev overlay.
- Add minimap/world graph view.
- Add path validation for customers and staff.
- Add zone layers for tavern, kitchen, guest room, cellar, greenhouse, field, cave.
- Add persistent scene-specific NPC/resource spawners.
