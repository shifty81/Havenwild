# Havenwild Generic Multi-Tile Stamp System — Pass 61

## Purpose

Pass 61 promotes Havenwild's project-owned structures, trees, clutter, interiors, capital/town pieces, and cave pieces from atlas-only authoring material into one shared multi-tile stamp system used by the native editor, headless authoring services, save format, and client runtime.

A stamp is a named atlas region with a stable asset key and three grid-space footprints:

- **Visual footprint** — the pixels drawn on the scene.
- **Collision footprint** — the cells that block movement.
- **Interaction footprint** — the cells available to later gameplay interaction binding.

The authored anchor remains stable while the visual art may extend above, left, or right of it. This is required for buildings, large trees, cave entrances, furniture groups, scaffolds, walls, roofs, and other assets that cannot be represented honestly as one 32×32 tile.

## Production coverage

The shared registry currently loads six project-owned manifests:

1. Home-island structures
2. Home-island trees
3. Home-island clutter
4. Cozy interior stamps
5. Capital/town stamps
6. Cave and dungeon stamps

Current validated coverage:

- **136 registered stamp definitions**
- **109 multi-tile definitions**
- **Six atlas sheets**
- Stable, unique asset IDs across the combined registry

The uploaded third-party/reference sheets remain reference-only. Pass 61 uses project-owned generated Havenwild artwork and does not promote, trace, copy, or ship reference pixels.

## Native editor workflow

1. Open **Scene Editor**.
2. Select the **Objects** layer.
3. Open the **Assets** dock and choose **Stamps**.
4. Search or filter the interior, town, cave, nature, clutter, or structure entries.
5. Select a stamp. The editor switches to the Place tool.
6. Move the cursor over the permanent scene canvas.
7. Review the translucent placement ghost and footprint outline:
   - Green means the placement currently validates.
   - Warning color means the visual/collision footprint is outside the scene or overlaps blocked content.
8. Click to place the complete asset as one authored instance.
9. Switch to **Select** to move, duplicate, copy, cut, paste, frame, or delete the instance.
10. Use the inspector and outliner to locate the stable stamp instance and inspect its asset key, anchor, atlas, category, and footprints.
11. Use `Ctrl+Z` and `Ctrl+Y` for typed undo/redo.
12. Use **File > Save All**, `Ctrl+S`, or `F5` to persist the scene.

## Editor behaviors

The native editor now provides:

- Searchable **Objects & Multi-Tile Stamps** outliner
- Project-owned atlas thumbnails
- Placement ghosts using the real atlas crop
- Visual and collision footprint overlays
- Stable `StampInstanceId` selection rather than vector-index selection
- Grid-snapped placement and movement
- Collision-safe movement and placement diagnostics
- Marquee selection support
- Copy, cut, paste, duplicate, delete, and frame-selection support
- One typed undo transaction per placement/move/delete/bulk action
- Scene Bank object and stamp counts
- Cursor, brush, and scene stamp status in the inspector

## Persistence format

`TavernMap` now owns both ordinary objects and multi-tile stamps:

```text
objects: Vec<PlacedObject>
stamps: Vec<PlacedStamp>
```

Each saved stamp record contains:

- Stable instance ID
- Stable stamp asset key
- Anchor X/Y
- Visual footprint offset and dimensions
- Collision footprint offset and dimensions
- Interaction footprint offset and dimensions
- Movement blocking flag
- Player occlusion flag
- Fade-behind flag

Older scene documents remain readable because stamp records are additive. A scene with no stamp records loads with an empty stamp collection.

## Runtime behavior

The client loads the same registry and atlas sheets as the editor. Runtime rendering:

- Draws the authored atlas crop at the visual footprint
- Sorts stamps using the lower collision edge so the player and world objects layer correctly
- Uses a visible fallback rectangle when a definition or texture is missing
- Includes blocking stamp cells in normal player walkability checks

This means a building, large tree, cave prop, or furniture composition placed in the editor is no longer merely a preview. It saves, reloads, renders in the client, and participates in collision.

## Headless authoring and transactions

The reusable authoring crates now expose:

- `place_scene_stamp`
- `move_scene_stamp`
- `erase_scene_stamp`
- `InsertStamp`
- `RemoveStamp`
- `MoveStamp`
- `ClipboardStamp`

Undo/redo operates on logical stamp instances and stable IDs. The implementation does not serialize the entire world for each edit.

## Regeneration and validation

Regenerate the stamp-library preview and validate the registry:

```bash
./tools/build/Build.sh stamps
```

Regenerate the complete environment set, including stamp sheets:

```bash
./tools/build/Build.sh tiles
```

Run the definitive Windows Rust build:

```bash
./tools/build/Build.sh all
```

The dedicated validator is:

```bash
python tools/automation/validation/checks/misc/Validate-GenericMultitileStampSystemV78.py
```

## Deliberately deferred

Pass 61 does not yet attempt to make every structure into a modular construction kit. The following remain later passes:

- Stretchable wall, fence, cliff, and roof runs
- Corner/end-cap/door/window-aware building recipes
- Rotation and mirror variants with authored collision remapping
- Gameplay function binding for doors, beds, storage, crafting stations, wells, lamps, and cave entrances
- Seasonal and damage-state stamp variants
- Animation tracks for smoke, fire, water features, machinery, and lighting
- Stamp definition editing directly in a dedicated asset-definition inspector
- Prefab composition from multiple nested stamp instances

The strongest next step is a **modular building and boundary kit pass** built on this stamp foundation, followed by gameplay-function binding for interactable placed assets.
