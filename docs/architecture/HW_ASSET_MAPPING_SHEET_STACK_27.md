# HW-ASSET-MAPPING-SHEET-STACK-27

## Purpose

Pass 27 keeps Havenwild standalone and upgrades the Atlas Mapper toward a real Asset Mapping Workspace. The left side now refreshes from catalog-declared sheets, project source libraries, generated terrain atlases, OGA/LPC sources, and configured external asset roots. This makes the mapper the proof surface for the future Ember ingest path without making Ember the authority yet.

## Runtime behavior

The mapper preloads sheet **cards**, not every image texture. Selecting a sheet lazy-loads that source atlas into the preview. This preserves the desired workflow of having the Havenwild atlas universe visible on the left while avoiding a heavy startup texture load.

## Indexed sources

- `content/assets/terrain_atlas_catalog_v2.json`
- `assets/source/licensed/lpc_revised/Terrain`
- `assets/source/licensed/lpc_revised/Objects`
- `assets/source/licensed/lpc_revised/Structure`
- `assets/source/licensed/lpc_revised/Characters`
- `assets/source/licensed/lpc_revised/Equipment`
- `assets/source/licensed/lpc_revised/FX`
- `assets/source/licensed/lpc_revised/UI`
- `content/assets/oga_lpc/source`
- `content/assets/lpc/source`
- `assets/generated/worldgen_v0_1/terrain`
- external roots from `content/assets/intake/external_asset_roots_v0_1.json`
- optional local roots from `.local/havenwild_external_asset_roots.json`

## Mapped sheet records

Mapped-sheet records now include per-tile mapping evidence:

```text
mapped_tile_count
mapped_tiles[]
coverage_percent
```

Each mapped tile records exact source cell identity and the current role/layer evidence:

```text
source_tile_x
source_tile_y
source_rect
semantic_role
layer
status
```

A green tile/sheet check still means **mapper metadata exists**, not runtime publication. Runtime publication still requires Terrain Lane authority, layer rules, collision, sockets/adjacency, provenance, validation, and a green gate.

## Next passes

The next implementation should add family filters, virtualized browsing, group boxing, Learn From Scene correction memory, Generate Next Unmapped Group, and the real Havenwild world preview canvas.
