# In-Game Overlay Editor Spec

## Purpose

The in-game overlay is the runtime-safe mirror of the main editor. It should be usable for both development and player-facing build mode.

## Opening behavior

```text
dev hotkey opens full overlay
player build button opens restricted build mode
overlay can pause, slow, or continue simulation depending mode
```

## Overlay layout

```text
Top Bar:
  Select | Build | Terrain | Parcel | Inspect | Validate | Exit

Left Panel:
  tool categories, brush/object list

Right Panel:
  selected tile/object/parcel inspector

Bottom Panel:
  cost, warnings, confirm/cancel, validation log

World Overlay:
  grid, ownership, collision, ghost preview, path preview, scene bounds
```

## Allowed in-game tools

```text
select
inspect
place object
move object
rotate object
delete object
terrain edit on owned land
water placement on owned land
parcel preview
room assignment
construction queue preview
collision preview
staff/customer path preview
```

## Restricted tools

The overlay should not allow unsafe global edits unless dev mode is enabled:

```text
macro worldgen regeneration
landmass editing
scene rectangle resizing
global asset metadata editing
database editing
raw file operations
schema migrations
```

## Overlay command rule

Every overlay action creates an EditorCommand.

```text
Preview command
Validate command
Confirm command
Apply command
Record undo state
Mark scene dirty
```

## Runtime bridge

The overlay should talk to the runtime through a safe bridge:

```text
read current scene data
submit command
receive validation result
apply command to runtime ECS/object state
request V005 terrain recomposition for dirty cells
request V006 collision/object rebuild
save runtime edit state
```

## Visual feedback

```text
green = valid
yellow = warning
red = invalid
blue = owned land
purple = scene seam/boundary
cyan = water/fishing region
orange = construction area
```
