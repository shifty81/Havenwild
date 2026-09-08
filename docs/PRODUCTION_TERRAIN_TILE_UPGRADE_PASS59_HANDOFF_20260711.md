# Pass 59 Handoff — Production Terrain Tile Upgrade

The active Havenwild terrain, live-autotile, and animated-water atlases have been replaced in place with original project-owned pixel art. Runtime IDs, editor palette bindings, manifest rectangles, padding, and source dimensions are unchanged.

Run:

```bash
./tools/build/Build.sh tiles
./tools/build/Build.sh all
```

Primary review image:

`docs/assets/previews/havenwild_production_terrain_repeat_preview_pass59.png`

Next recommended art pass: 47-case coastline refinements, grass/dirt/sand transition families, seasonal overlays, and dedicated cliff-height kits.
