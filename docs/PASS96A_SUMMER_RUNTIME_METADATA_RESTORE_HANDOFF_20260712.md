# Havenwild Pass 96A — Summer Runtime Metadata Restore

## Failure addressed

`tools/build/Build.cmd all` stopped while building the V107 conformance board with:

```text
KeyError: 'sand_over_wet_sand'
```

The preceding terrain bake emitted 140 records instead of the Pass 95 target
of 176. The source-only Pass 95 export had excluded `content/assets` broadly
enough to omit two runtime-family mapping entries and the pebble fill promotion
metadata.

## Repair

`Sync-LpcSummerRuntimeMetadataV108.py` runs before terrain promotion and derives
the missing data from:

```text
content/assets/intake/lpc_terrain_summer_complete_map_v0_1.json
```

That contract already passed V103 and contains the pinned, reviewed source
coordinates. The repair therefore does not guess or hard-code new LPC cells.

Restored runtime entries:

- `sand_over_wet_sand`, including its verified 2×2 inner-corner block;
- `pebble_path_over_dirt`, remaining outer-role-only;
- `pebble_shore` and `stone_path` base-fill cells from
  `summer_pebble_path_fill`.

V108 now also requires exactly nine terrain groups, 144 outer variants, and 32
verified inner corners before accepting the seam-conformant atlas.

## Build

Extract the complete Pass 96A source rollup over the existing repository,
delete the `target` directory, then run:

```bat
tools/build/Build.cmd all
```

Expected terrain-bake summary:

```text
Baked 176 ordered-pair LPC transition variants
```

The V107 conformance board should then find both restored groups, and V108
should validate the mask-authoritative edge signatures.
