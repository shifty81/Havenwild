# GUI Layout Grid Spec

## Goal

All movable GUI should be editable on a snapped layout grid instead of hard-coded per-resolution pixel coordinates.

This keeps the in-game debug overlay usable across resolutions and creates a shared layout language that the web editor can preview later.

## Layout Model

Each panel/widget layout entry should store:

- `id`
- `anchor`
- `grid_x`
- `grid_y`
- `width`
- `height`
- optional `min_width`
- optional `min_height`
- optional `visible_in_modes`

## Anchor Model

Supported anchors:

- `top_left`
- `top_right`
- `bottom_left`
- `bottom_right`
- later: `center`, `top_center`, `bottom_center`

Anchors define the stable reference edge for resolution changes. Offsets are measured from the anchor in snapped grid units.

## Snap Rules

- V1 grid size: **16 px**
- drag operations snap on release and during move preview
- stored offsets are snapped units, not arbitrary floats
- panel title bars are the default drag handles

## Persistence

Saved layout should live outside code in a dedicated layout file.

Current runtime path:

```text
workspace/saves/editor_layout.tlayout
```

Future shared path:

- promote the format into `haven_core`
- let the web editor load and preview the same file

## Current Runtime Scope

The current layout-editable panels are:

- HUD panel
- Editor Overlay
- Inspector
- Validation panel
- World Graph

## Editing Workflow

1. Enter dev mode.
2. Press `L` to toggle layout editing.
3. Drag panel headers.
4. The panel snaps to the 16 px grid.
5. Press `L` again or save the world to persist layout changes.

## Scaling Rules

- anchors keep panels attached to stable edges
- snapped offsets preserve relative spacing
- explicit panel width/height are acceptable in V1
- later iterations should support:
  - tokenized widths (`sidebar`, `panel-wide`, `panel-compact`)
  - breakpoint rules
  - text-scale-aware minimum sizes

## Future Extensions

- per-widget editing inside panels, not only panel containers
- resize handles
- alignment/distribution tools
- panel docking
- layout presets by editor mode
- export/import between runtime and web editor
- safe-area handling for ultrawide and small window sizes

## Reference Implementation Advice

The best practical approach for this project is:

1. keep **panels anchor-relative**
2. keep **movement grid-snapped**
3. keep **saved layout data external**
4. let the in-game overlay be the fastest live editor
5. use the web editor as a higher-level authoring/preview surface for the same schema
