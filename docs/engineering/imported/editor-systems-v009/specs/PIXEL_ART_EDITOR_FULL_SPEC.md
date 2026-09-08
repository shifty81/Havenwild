# Pixel Art Editor Full Spec

## Purpose

The pixel art editor is a first-class core tool. It is not a minor asset viewer.

It must create and edit:

```text
terrain tiles
autotile masks
water animation frames
shore/foam overlays
item icons
props
furniture
character layers
animation sheets
UI skins
collision/interaction masks
```

## Canvas modes

```text
Single Image Mode
Tile Atlas Mode
Animation Sheet Mode
Autotile Authoring Mode
Overlay/Mask Mode
Character Layer Mode
UI Skin Mode
```

## Core tools

```text
pencil
eraser
line
rectangle
ellipse
fill bucket
replace color
eyedropper
selection
move selection
copy/paste
rotate 90
flip horizontal/vertical
dither brush
smudge/blend brush
lighten/darken
outline tool
shadow/highlight brush
```

## Pixel-specific features

```text
integer zoom only
pixel-perfect grid
tile grid overlay
sub-grid overlay
alpha checkerboard
palette lock
indexed palette mode
RGBA mode
tile snapping
mirror drawing X/Y
symmetry drawing
onion skin for animation
frame timeline
hotkeys
undo/redo
```

## Tile atlas workflow

The tile atlas workflow must support:

```text
32x32 base tiles
64x96 character frame cells
custom cell sizes
atlas row/column metadata
tile tags
autotile row assignment
collision mask layer
interaction mask layer
anchor/socket layer
preview as 3x3 tile patch
preview as 5x5 tile patch
preview as shoreline/corner-mask patch
preview as animation strip
```

## Autotile authoring

Autotile authoring should support two mask families:

```text
corner mask:
  NW = 1
  NE = 2
  SE = 4
  SW = 8

cardinal mask:
  N = 1
  E = 2
  S = 4
  W = 8
```

Use corner masks for:

```text
shorelines
terrain blends
riverbanks
cave wall/floor
cliff transitions
```

Use cardinal masks for:

```text
roads
paths
fences
docks
tracks
```

## Water animation workflow

Water tiles need animation strips:

```text
deep water frames
mid water frames
shallow water frames
river flow frames
foam/ripple frames
shore splash frames
waterfall frames later
```

The editor should preview animation at different speeds and export metadata.

## Character sheet workflow

Character sheets must support:

```text
64x96 frame cells
8 directions
8 walk frames per direction
bottom-center foot anchor
small foot collision mask
layer compositing
clothing/armor/hair/accessory layers
```

## Metadata sidecar

Every image should save with metadata:

```text
asset id
schema version
cell size
grid dimensions
palette
tags
collision masks
interaction masks
anchor points
animation frame rules
autotile rules
preview rules
source history
license/originality notes
```

## Export formats

```text
PNG
metadata JSON
runtime cache
editor preview cache
packed atlas
individual cells
animation strip
```

## Validation

The pixel editor should detect:

```text
wrong cell size
transparent pixels where forbidden
non-transparent pixels where forbidden
palette drift
missing animation frames
missing metadata
invalid autotile row
invalid collision layer
mismatched frame count
anchor mismatch
```
