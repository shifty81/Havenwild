# Havenwild Open World + PCG v1 Implementation Notes

Generated: 2026-07-05

## Purpose

This pass turns the recent design decisions into repo-level contracts so the next code pass can replace the tiny outdoor scene model with a Factorio-esque generated overworld.

## Added Source Contracts

- `crates/haven_world/src/open_world.rs`
  - `WorldSurfaceConfig`
  - `WorldSizePreset`
  - `WorldTileCoord`
  - `ChunkCoord`
  - required open-world anchor types
  - cave-depth and cave weak-spot contracts
  - rope-ladder/lower-shaft traversal requirements
  - open-world validation report helpers
- `content/worldgen/havenwild_open_world_preset_v1.json`
  - canonical v1 seed-generation preset
  - 1024x1024 tile default overworld
  - 64x64 tile chunking
  - no outdoor transitions
  - required gameplay anchors
  - procedural caves, weak spots, lower shafts, and rope-ladder rule
  - texture/material atlas rendering rule
- `content/schemas/havenwild_open_world_preset.schema.v1.json`
  - lightweight schema definition for the preset
- `tools/automation/validation/checks/misc/Validate-HavenwildOpenWorldPreset.py`
  - dependency-free validator for the v1 preset

## Locked Runtime Direction

Outdoor areas should become one continuous generated chunked surface:

```text
Havenwild main surface
  1024x1024 tiles initially
  64x64 tile chunks
  deterministic seed generation
  modified chunks saved as deltas
```

Interior/cave/dungeon spaces remain transition-based:

```text
tavern interior
cellar
guest floor
shops
homes
caves
dungeons
special event maps
```

## Next Implementation Target

The next actual code step should be `Havenwild_OpenWorldSurfaceRuntimePass_V1`:

1. Add a runtime `WorldSurface` storage type that owns/generated chunks.
2. Add coordinate conversion between world tiles, chunk coordinates, and local chunk tiles.
3. Add a first deterministic overworld chunk generator that outputs material/tile IDs.
4. Add a temporary viewport mode that renders a window over the generated surface.
5. Keep the old scene runtime for interiors and caves until outdoor traversal is migrated.
6. Add a save-delta format for edited/generated chunks.

## Validation Command

```bash
python3 tools/automation/validation/checks/misc/Validate-HavenwildOpenWorldPreset.py
```

Expected result:

```text
PASS Havenwild open-world preset: 1024x1024 tiles, 16x16 chunks, 9 required anchors
```
