# Havenwild Pass 104 - LPC Single Replacement Role Hotfix

Pass 104 corrects the Pass 103 mixed-corner regression.

## Why

Pass 103 allowed a terrain cell to request both:

- a complete outer-edge replacement tile, and
- a complete inner-corner replacement tile.

LPC transition roles are complete replacement cells, not transparent overlays.
Layering an inner-corner replacement over an edge replacement produced repeated
shore/corner stamps and visibly broke tile placement.

## Changed

- Restored inner-corner requests to pure diagonal contacts only.
- Mixed edge-plus-diagonal contacts now keep one complete outer replacement
  role.
- V116 now guards against layering complete inner-corner roles over outer edge
  roles.
- Removed the unshipped broader V117 topology edits from this hotfix package.

## Remaining Work

The general goal is still correct: roads, caves, floors, walls, buildings, and
all environment families should eventually share a richer neighbor-aware
autotile model. That requires authored mixed-role LPC/Wang/47-tile families,
not compositing two complete replacement cells.
