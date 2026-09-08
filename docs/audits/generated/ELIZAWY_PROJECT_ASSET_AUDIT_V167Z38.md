# ElizaWy/LPC Project Asset Audit — Pass 167Z38

- Source: `https://github.com/ElizaWy/LPC`
- Pinned commit: `f07f7f5892e67c932c68f70bb04472f2c64e46bc`
- Files indexed: **64,365**
- Coverage complete: **True**
- Unrouted files: **0**
- Duplicate stable IDs: **0**
- Source revision provenance verified: **True**
- Images without source-local/root credit context: **0**

## Domain routing

| Domain | Files | Project owners |
|---|---:|---|
| `characters` | 63,986 | character_creator, npc_generation, equipment, animation_runtime, portrait_pipeline |
| `fx` | 5 | runtime_fx, animation_editor, world_editor |
| `legal_and_documentation` | 36 | release_credits, asset_audit |
| `nature` | 16 | biome_worldgen, runtime_objects, world_editor, foraging, forestry, mining |
| `objects` | 188 | placeables, interiors, inventory, crafting, shops, taverns, editor |
| `palette` | 13 | pixel_studio, character_creator, asset_validation |
| `reference_scenes` | 6 | asset_audit, editor_reference |
| `repository_support` | 3 | asset_audit, editor_reference |
| `structure` | 99 | building_system, city_authoring, interiors, world_editor, runtime_structures |
| `terrain` | 13 | worldgen, runtime_terrain, world_editor, pixel_studio |

## Source handling

The mounted ElizaWy/LPC repository remains intact. Havenwild routes assets through derived catalogs and generated atlases so local Credits files, original paths, and source context are never lost.

## Tree-first world construction

Temperate biome generation reserves authored infrastructure first, then places natural-scale tree canopies and one-tile trunk collisions, then derives understory, flowers, mushrooms, herbs, reeds, and rocks from tree/water proximity. Generic circle tree fallbacks are prohibited.

## Generated outputs

- Full compressed audit: `WORKSPACE/generated/lpc/elizawy_repository_audit_v167z38.json.gz`
- Summary: `WORKSPACE/generated/lpc/elizawy_repository_audit_v167z38_summary.json`
- Domain catalogs: `WORKSPACE/generated/lpc/catalogs`
