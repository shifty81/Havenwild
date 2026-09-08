# Worldgen v0.8 Object Outliner + Footprint Editing

v0.8 is the first editor usability pass on top of the v0.6/v0.7 footprint system.
It keeps object placement and object management in the **Objects** tab so multi-tile props are no longer edited only through cursor inspection.

## Added

- Objects tab scene-object outliner.
- Selected object index and object list offset in the runtime editor state.
- Pick selected object from cursor cell.
- Focus selected object.
- Move selected object with arrow keys or the nudge buttons.
- Move selected object anchor to the cursor cell.
- Delete selected object from the panel, Delete key, or Backspace.
- Selected-object overlay highlight using white visual bounds and gold collision bounds.
- Move validation that ignores the object being moved but still blocks invalid overlaps, blocked terrain, and out-of-scene footprints.

## Controls

| Control | Result |
|---|---|
| Objects tab list row | Select placed object |
| Pick | Select topmost object under cursor tile |
| Focus | Center editor camera target on selected object anchor |
| Up / Down / Left / Right | Nudge selected object one tile |
| Anchor | Move selected object anchor to cursor tile |
| Delete / Backspace | Delete selected object |

## Validation model

Object moves call:

```rust
TavernMap::placement_issues_for_object_excluding(moved, Some(index))
```

That preserves the v0.6/v0.7 multi-tile rules while preventing the selected object from falsely colliding with itself.

## Next patch recommendation

v0.9 should add direct footprint resizing/editing controls:

- visual width/height +/-
- collision width/height +/-
- interaction width/height +/-
- offset nudge controls for each rectangle
- reset-to-kind-default footprint button
- per-object dirty indicator and save confirmation
