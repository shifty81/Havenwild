# Havenwild Production Terrain Tile Upgrade — Pass 59

## Scope

This pass replaces the active generated placeholder terrain art without changing tile IDs, atlas rectangles, runtime bindings, or editor palette contracts.

Upgraded active sheets:

- `terrain/common_base_terrain_32.png`
- `terrain/live_autotile_16_32.png`
- `water/water_families_animated_32.png`

All art is original and project-owned. No quarantined/reference pixels are copied, traced, palette-lifted, or shipped.

## Production rules applied

- 32×32 fixed orthographic world tiles.
- Nearest-neighbor pixel clusters with no smoothing.
- Quiet center tiles to reduce visible repetition.
- Material-specific authored clusters instead of random single-pixel noise.
- Warm highlights and cooler/darker shadow ramps.
- Clear value separation between grass, soil, stone, wood, water, coast, cave, and mountain materials.
- Existing IDs and source rectangles preserved for immediate editor/runtime compatibility.
- One-pixel edge extrusion retained inside the padded atlas cells.

## Current usable families

- Grass and tall grass
- Sand, wet sand, pebble shore, mud bank
- Dirt, roads, stone paths, mountain paths
- Tilled, watered, and crop soil
- Fresh, shallow, deep, ocean, and river water
- Shore foam and river-mouth blend
- Cliff, mountain rock, cave floor, cave wall
- Wood, plank, stone, and brick floors
- Bridge, wall, crop seedling, and greenhouse zone
- Seven 16-mask live-autotile groups
- Five four-frame animated water families

## Regeneration

```bash
./tools/build/Build.sh tiles
```

Then validate:

```bash
./tools/build/Build.sh validate editor
```

## Review workflow

1. Open `docs/assets/previews/havenwild_production_terrain_repeat_preview_pass59.png`.
2. Inspect each family as a 3×3 repeat.
3. Launch the native editor and open the Asset Palette.
4. Paint terrain in a disposable scene.
5. Test all 16 adjacency cases for roads, floors, water, walls, cliffs, and cave walls.
6. Test animated water in the client.
7. Promote further refinements only when repeat seams and value separation remain clean.

## Deferred

This pass does not yet add seasonal variants, 47-case diagonal shoreline refinement, biome-specific grass families, river current overlays, snow depth, fertilization overlays, crop-stage sheets, cliff-height stacks, or full interior wall kits. Those should follow as separate production families after this baseline is approved.
