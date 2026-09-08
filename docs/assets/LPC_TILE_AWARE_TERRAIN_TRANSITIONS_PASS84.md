# LPC Tile-Aware Terrain Transitions - Pass 84

Pass 84 fixes the first visible autotiling artifact from the LPC transition reset:
grass/sand and shallow/deep-water intersections were still leaving square base
tiles visible at corners.

## What Changed

- `resolve_terrain_transitions` now starts from exact `TileKind` values instead
  of immediately collapsing everything into broad `TerrainFamily` values.
- Wet sand and pebble shore painted into grass now resolve as sand-family edge
  cases instead of anonymous `Sand`.
- Shallow water beside deep water now emits a depth-edge transition even though
  both are still part of the broad water family.
- One-row shallow-water shore strips are valid; they no longer require a second
  adjacent shallow row just to resolve a land/deep-water edge.
- Atlas-backed transition cells now draw as full replacement tiles in both the
  native editor and game renderer.

## Why The Square Happened

The transition atlas cells are complete opaque 32x32 tiles. The renderer was
drawing them at partial opacity over the raw base cell. At grass/sand corners,
that let the underlying grass or sand square remain visible through the authored
corner tile.

## Remaining Environment Autotile Work

This pass does not finish every environment tile. It fixes the transition
resolver and replacement draw model so the current LPC grass/sand/water families
behave correctly.

The next promotion pass should expand the LPC autotile atlas rows so these
families have real per-family art instead of old shared placeholders:

- road
- stone path
- mountain path
- dirt
- wet sand
- pebble shore
- shallow water
- deep water
- plank floor
- stone floor
- brick floor
- wall
- cave floor
- cave wall
- cliff
- bridge
- modular building exterior walls/roofs where tileable

Vegetation, furniture, signs, lamps, fences, and town clutter should stay as
objects or stamps unless the asset is truly tileable.

## Town Planning Reference

The attached Stardew Valley town screenshot is useful as a density/layout
reference only. Havenwild should use the same broad town design lessons without
copying its art, layout, names, or IP:

- multiple path materials woven together
- cliffs and river edges as major navigation structure
- bridges and stairs as authored transition points
- dense props and foliage around paths
- fenced gardens, plazas, shops, public-service buildings, and waterfront areas
- small irregular natural edges rather than large square terrain patches

For Havenwild, those ideas should become LPC-backed town stamps, modular building
exteriors, bridge kits, cliff/river transition rules, and object palettes inside
the World Editor.

## Validation

New validator:

```text
tools/automation/validation/checks/terrain/Validate-LpcTileAwareTerrainTransitionsV84.py
```

It verifies:

- exact `TileKind` identity reaches terrain transition resolution
- shallow/deep water depth edges are represented
- wet-sand-in-grass regression tests exist
- editor transition replacements render at full opacity
- runtime transition replacements render at full opacity
