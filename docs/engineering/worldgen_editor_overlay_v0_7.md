# Worldgen v0.7 Editor Collision / Interaction Overlay

Worldgen v0.7 turns the v0.6 multi-tile footprint runtime into an editor-facing placement workflow.

## Runtime/editor behavior

- `H` toggles visual footprint outlines.
- `C` toggles collision and blocked-tile overlays.
- `I` toggles interaction and transition overlays.
- Selected object tools now render a placement preview at the cursor.
- Valid placement previews are green; blocked placement previews are red.
- Failed placement attempts write the first placement issue into the status line.

## Overlay meanings

| Overlay | Meaning |
|---|---|
| Blue outline | Visual/sprite bounds |
| Red outline | Object collision footprint |
| Red fill | Final blocked tile after terrain + object collision |
| Yellow outline | Object interaction footprint |
| Cyan outline | Scene transition trigger |
| Green preview | Object placement is valid |
| Red preview | Object placement is blocked |

## Placement diagnostic rules

The editor asks `TavernMap::placement_issues_for_object` before committing an object placement. A placement is rejected when:

1. The anchor is outside the scene.
2. The visual footprint exits the scene.
3. The blocking collision footprint exits the scene.
4. The blocking collision footprint lands on non-walkable terrain.
5. The interaction footprint exits the scene.
6. The object overlaps an existing object footprint.

Generated scene loading still uses `place_custom_object` so already-authored worldgen scenes can be loaded as data. Manual editor placement uses the stricter path.

## Why this matters

This is the first point where multi-tile worldgen objects become practical for authoring. Tables, bars, trees, walls, cave entrances, greenhouse markers, and tavern facade pieces can now be inspected visually before they are committed to a scene.
