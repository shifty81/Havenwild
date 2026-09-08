# World Paint Layer Composition Pass 40

This pass upgrades the paint preview from a single atlas tile per world cell into ordered layer composition for a canonical 32x32 cell.

## Why

The paint system already stores material-family and layer state. A single rendered tile per cell is not enough for the target world workflow because a cell may need a base ground tile, a shoreline/fringe tile, a water overlay, future foam/debris overlays, collision preview, and dev overlay information.

## Runtime rule

Authoritative state remains:

- world paint delta records
- world paint material-state records

Derived client/editor state remains disposable:

- transition tile resolution
- render cache document
- runtime render binding cache

## Composition order

The draw order is centralized in `world_paint_layer_render_order`:

1. ground_base
2. ground_variation
3. ground_transition_fringe
4. water_base
5. water_surface_fx
6. cave_base
7. cave_wall_face
8. town_surface
9. indoor_floor
10. debris_overlay
11. collision_footprint
12. occlusion_fade_mask
13. dev_overlay

## Game-side binding

`WorldPaintRenderBindingCache` now maps one `(x, y)` cell to a vector of resolved tile bindings. The draw path calls `draw_world_paint_atlas_layers_if_bound`, which draws all available layers in deterministic order. If no atlas-bound layer exists, the runtime falls back to the legacy `TileKind` color/atlas path.

## Anti-monolith note

Layer ordering and cache validation live in `haven_world`. Macroquad drawing stays in `haven_game`. No world-paint logic was moved into `main.rs`.
