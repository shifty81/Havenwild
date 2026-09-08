# Havenwild Production Environment Library — Pass 60

## Purpose

Pass 60 expands the project-owned, runtime-ready environment library without promoting any mixed-provenance reference sheet. The uploaded interior, castle, cave, farm, animal, and character sheets were used only to identify missing categories, sheet organization patterns, animation coverage, and multi-tile authoring needs.

No uploaded pixels, tracing, palette lifting, or direct runtime promotion are included in this pass.

## Live runtime/editor tiles

The canonical `TileKind` catalog now exposes all 32 semantic entries in the generated terrain atlas. Every entry is searchable and paintable in the native editor and resolves through the same atlas registry in the client.

Newly promoted semantic tile kinds:

- Watered Soil
- Deep Ocean
- Shallow Ocean
- River Water
- River Mouth Blend
- Shore Foam
- Mud Bank

All 32 semantic tiles provide four deterministic visual variants. Variant selection is stable for a given tile ID and grid coordinate, so repeated terrain gains visual variation without save-file noise or random flicker.

The runtime and native editor both call the same `tile_asset_rect(tile, x, y)` resolver.

## Live placeable objects

The searchable editor object palette now contains 26 placeable object kinds. The expanded project-owned 32×64 atlas includes:

- Tavern furniture and fixtures
- Trees, berry bushes, rocks, ore, mushrooms, and herbs
- Crates and barrels
- Well and scarecrow
- Fence and lamp post
- Bench, tree stump, and fallen log
- Signboard
- Existing doors, stairs, greenhouse marker, and cave entrance workflow

Generated object sprites now use their atlas foot anchors in both the runtime and native editor. This removes dependence on oversized logical visual footprints and fixes the earlier tree-placement/rendering mismatch.

## Authoring stamp libraries

Three additional project-owned libraries are generated:

- `interiors/cozy_interior_stamps_32`
- `town/capital_city_stamps_32`
- `caves/cave_stamps_32`

Each contains 24 original 32×64 authoring stamps. They are cataloged and previewable but remain marked `not_bound_to_generic_stamp_runtime_yet`. This is deliberate: multi-tile stamp placement needs a normalized stamp definition, preview, collision footprint, pivot, undo transaction, and save contract before these libraries can be promoted as generic runtime-placeable stamps.

## Reference-only uploads

The uploaded material currently remains reference-only:

- Interior furniture and wall sheets
- Castle/capital modular architecture
- Cave wall, floor, ledge, and entrance sheets
- Farm terrain/water/cliff examples
- Cat, horse, chicken, llama, and pig animation sheets
- Base character sheet
- Mage-city/environment sheet

Animal art is deferred to a dedicated original Havenwild animal-animation rebuild. It should define species scale, four-direction frame contracts, shadow policy, eating/idle/walk loops, collision, sound hooks, and editor preview before becoming runtime content.

## Generation

```bash
./tools/build/Build.sh tiles
```

This runs both:

1. `Generate-HavenwildProductionTerrainPass59.py`
2. `Generate-HavenwildProductionEnvironmentPass60.py`

The first rebuilds the base terrain, autotile, and animated-water foundations. The second adds four deterministic variants, rebuilds the live object atlas, creates the three authoring stamp libraries, updates manifests, and produces the review preview.

## Validation

Pass 60 adds `Validate-ProductionEnvironmentLibraryV77.py`. It verifies:

- 32 live `TileKind` values
- Four variants for every semantic tile
- Atlas bounds and dimensions
- 26 editor object kinds and runtime bindings
- Runtime/editor shared tile-variant resolver
- Runtime/editor object anchor usage
- Three authoring stamp libraries
- Root manifest registration
- Reference-only policy
- Absence of raw uploaded filenames from the project tree
- Bash generation wiring

## Next art passes

1. Generic multi-tile stamp placement and editor preview.
2. Full building wall/roof/window/door compositor.
3. 47-case shore, river-bank, and cliff transition sets.
4. Biome and seasonal terrain overlays.
5. Original farm-animal animation library.
6. Original capital-city architecture kit.
