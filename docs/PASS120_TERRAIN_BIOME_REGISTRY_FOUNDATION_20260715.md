# Pass 120 — Terrain/Biome Registry Foundation

Date: 2026-07-15

## Purpose

This pass locks the planning contract needed to finish terrain without adding more patch debt.

It does not change renderer/editor behavior yet. It defines the source of truth that the next passes must follow.

## Added

- `content/assets/terrain_material_registry_v0_1.json`
- `content/worldgen/biome_registry_v0_1.json`
- `content/assets/havenwild_asset_library_v0_1.json`
- `docs/TERRAIN_COMPLETION_MATRIX.md`
- `tools/automation/validation/checks/terrain/Validate-TerrainMaterialRegistryV126.py`

## Contract decisions

- Wet sand is generated shore terrain, not a normal inland paint material.
- Shore foam, river mouth blend, ocean shallow, and ocean deep are generated terrain.
- Greenhouse zone is deferred and represents greenhouse interior scene transition logic, not overworld paint terrain.
- Cliff and mountain rock are structural rock terrain, not ground-corner terrain.
- Stone path and pebble shore must remain separate semantic categories.
- One in-game day target is locked at 3600 real seconds in the biome defaults.
- Terrain detail variation and rare detail sliders are represented as registry defaults for the future editor terrain browser.

## Next passes

1. Pass121 — shore/water normalization.
2. Pass122 — path/ground pair coverage.
3. Pass123 — structural cliff/mountain-rock topology.
4. Pass124 — editor terrain browser with thumbnails, badges, search, biome/season selectors, and detail sliders.
5. Pass125 — seasonal terrain atlas reuse from compatible LPC sheets.
