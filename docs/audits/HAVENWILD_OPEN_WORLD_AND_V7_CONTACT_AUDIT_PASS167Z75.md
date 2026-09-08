# Havenwild Open World and V7 Contact Audit — Pass 167Z75

## Findings

1. `SurfaceRuntimeState::starter` used only the legacy Farmstead/NorthRoad/SouthField/EastWoods binding table.
2. Generated PCG scene IDs were not parsed as surface coordinates and silently defaulted to chunk `0,0`.
3. `scene_id_for_chunk` could therefore select unrelated `surface_x_*_y_*` generated chunks while an authored PCG mainland was active.
4. V7 contains direct Grass/Water tuples but no Grass/Water_Deep tuple.
5. The correct source-authored path for exact land in deep water is `land -> Water presentation rim -> Water_Deep`, with semantic tiles unchanged.
6. Water animation variants beneath mixed edge tuples created visible cell-sized blocks on long coastlines.

## Action matrix

| Area | Action | Result |
|---|---|---|
| Exact Grass in ocean | Derive one-cell medium-water presentation rim | Authored V7 edge; no semantic mutation |
| Sea coastline | Use quiet water owner fills beside transitions | Removes independent square shimmer blocks |
| PCG surface identity | Parse region and trailing grid coordinates | Loaded PCG rectangles become one surface namespace |
| Other islands | Filter bindings to active region | Reused local coordinates do not collide |
| Outdoor transitions | Keep exterior-to-exterior triggers compatibility-only | Coordinate streaming remains authoritative |
| Seamless viewport | Defer to next runtime stage | Requires neighboring partition composition |
