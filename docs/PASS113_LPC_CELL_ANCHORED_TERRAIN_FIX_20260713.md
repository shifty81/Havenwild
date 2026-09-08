# Pass 113 LPC Cell-Anchored Terrain Fix

Pass 112 proved that `terrain-map-v7` is useful, but it used the Tiled corner
terrain data too literally. Tiled terrain metadata describes the four corners
of a tile. Havenwild world editing paints whole map cells. Treating the map cell
as the upper-left corner of a Tiled terrain quad made one click visually affect
neighboring tiles and made mixed terrain appear offset toward the upper-left of
the world grid.

Pass 113 restores the Havenwild cell contract:

- A painted map cell owns the rendered tile at that same `(x, y)` cell.
- The mapped `terrain-map-v7` atlas is used only for mixed land transitions.
- Pure mapped fills fall back to the detailed Havenwild/LPC base tile path.
- Wet sand is deferred until a true wet-sand source mapping is promoted.
- Shallow water, deep water, ocean, and river tiles fall back to the existing
  water/autotile renderer instead of using mapped land corner tuples.

This fixes the upper-left placement behavior and prevents one-cell water paints
from producing a 2x2-looking grass/detail patch. If faint grid lines are still
visible while testing terrain art, confirm the editor overlays are off; the HUD
shows overlay toggles as `H`, `C`, `I`, and `T`.
