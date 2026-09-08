# Havenwild Pass 95 — LPC Summer Runtime Semantic Promotion

## Goal

Move the next reviewed summer-sheet families from catalog-only metadata into the actual runtime terrain system without remapping the already working grass, coast, and water families.

## Promoted families

- `summer_sand_over_wet_sand`
- `summer_pebble_path_fill`
- `summer_pebble_path_over_dirt`

## Core correction

`WetSand`, `Sand`, and the pebble/stone path family are now distinct semantic terrain families. Previously `WetSand` and `PebbleShore` collapsed into `TerrainFamily::Sand`, which made the reviewed dry-sand/wet-sand and pebble-path transition art unreachable even though it was fully mapped.

Runtime routing now uses:

- `WetSand -> Sand` → `sand_over_wet_sand`
- `PebblePath -> Dirt` → `pebble_path_over_dirt`
- `ShallowWater/Water -> WetSand` → existing `sand_bank_over_shallow`

## Source-authored topology rule

The dry/wet sand family has:

- sixteen normalized outer masks;
- four verified 2x2 authored concave corners.

The pebble-path family has:

- sixteen normalized outer masks;
- no fabricated inner corners because the source sheet does not provide a verified matching 2x2 block.

## Build integration

New command:

```bash
./tools/build/Build.sh lpc-summer-runtime
```

The root `tools/build/dev.sh` menu exposes the same operation as option 18.

`tools/build/Build.sh all` and `tools/build/Build.sh lpc-runtime` now regenerate and validate this active runtime set before Rust compilation.

## Generated outputs

- `assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.png`
- `assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.png`
- `assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.json`
- `docs/assets/previews/havenwild_lpc_summer_runtime_conformance_v107.png`

The transition atlas now contains:

- 9 ordered-pair families;
- 144 outer-mask variants;
- 32 verified inner-corner variants;
- 176 total generated transition records.

## Validation performed

Passed in the packaging environment:

- LPC dependency validation and mount safeguards;
- complete summer map generation and V103;
- shared seasonal topology generation and V106;
- runtime promotion and V107;
- updated legacy validators V93 and V98;
- client/editor stability validator V102;
- Python compilation;
- JSON parsing;
- Bash syntax checks;
- deterministic terrain regeneration.

The complete aggregate validator still stops on a pre-existing missing `content/assets/tile_extraction/tile_extraction_workbench_contract_v0_1.json` from the supplied baseline. Pass 95 does not remove or depend on that contract.

Rust/Cargo is unavailable in the packaging environment. Run the authoritative Windows verification:

```bat
tools/build/Build.cmd lpc-summer-runtime
tools/build/Build.cmd all
```

## Runtime acceptance checks

1. Dry sand surrounded by wet sand renders a complete four-edge/four-corner ring.
2. Adjacent dry-sand cells share no internal wet-sand seams.
3. L-shaped dry-sand regions use the authored concave roles.
4. Wet sand next to water continues to use the established shoreline bank family.
5. Stone path and pebble shore use the reviewed LPC fill cells.
6. Pebble path against dirt uses outer roles only and never displays an unrelated concave corner.
7. Save, reload, undo, and redo preserve the same semantic topology.

## Next asset pass

Continue with the remaining summer overworld families in this order:

1. road and mountain-path visual separation;
2. tilled/watered farm soil transitions;
3. modular rivers and horizontal/vertical bank strips;
4. grass fringe/decor overlays;
5. trees, tufts, rock clusters, and fixed/expandable overworld stamps;
6. seasonal visual binding activation using the shared summer topology IDs.
