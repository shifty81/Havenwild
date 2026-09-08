# Worldgen v0.9 — Editor Footprint Editing Patch

## Purpose

v0.9 turns the v0.8 object outliner into a direct footprint editor. The selected object can now have its visual, collision, and interaction rectangles adjusted from the Objects tab without editing JSON by hand.

## User-facing editor flow

1. Enter dev mode with `F3`.
2. Open the `Objects` tab with `Q` / `E` or by clicking the tab.
3. Select an object from the scene-object list, click `Pick`, or place a new object.
4. Choose a footprint target: `Visual`, `Collision`, or `Interaction`.
5. Use `X-`, `X+`, `Y-`, `Y+`, `W-`, `W+`, `H-`, `H+` to move or resize that rectangle.
6. Toggle `Block`, `Occl`, or `Fade` for movement blocking, player occlusion, and player-behind fade behavior.
7. Use `Reset` to restore only the active target rectangle or `Default` to restore the entire object footprint preset.

## Validation behavior

Every edit creates a candidate object first. The candidate is passed through `TavernMap::placement_issues_for_object_excluding`, with the selected object ignored so the object can validate against the rest of the scene without colliding with itself.

A successful edit:

- pushes an undo snapshot,
- writes the edited `ObjectFootprint` back to the selected placed object,
- updates the inspector,
- updates the status line.

A failed edit:

- does not mutate the scene,
- does not push undo,
- reports the first placement issue in the status line.

## Supported object edits

- Large tavern bars can have a wide visual footprint with narrower collision.
- Tables can expose larger interaction regions than their blocking footprint.
- Trees can keep a tall visual canopy while collision stays on the trunk.
- Tavern/cave entrances can keep a wide visual sprite while only the bottom row blocks movement.
- Decorative objects can have zero-sized collision while still having a visual and interaction footprint.

## Remaining gap

v0.9 edits footprints in memory and preserves them through the existing world save format. It does not yet export the edited object rectangles back into the original worldgen scene JSON. That should be v0.10: scene-object JSON export/save-back.
