# Havenwild V7 Ground Material Closeout Audit — Pass167Z81

## Result

The remaining ordinary V7 ground lane is structurally closed around Gravel, Rock Ground, and Mud. Watered Tilled Soil is now explicitly a farming-state result rather than a normal terrain brush.

## Findings and actions

| Area | Finding | Pass167Z81 action |
|---|---|---|
| Pebble Shore | Visual role is general gravel rather than an intrinsic shoreline | User-facing label changed to Gravel; retained stable `PebbleShore` save identity |
| Rock Ground | Was still inconsistently treated as wall-like in a loose compatibility source | Canonical and mirrored catalogs now classify it as walkable terrain/floor authority |
| Mud | Used dirt artwork in some fallback paths and retained shoreline-overlay assumptions | Bound to V7 `Mud_Brown`; promoted as ordinary walkable ground and direct brush |
| Watered Soil | Exposed beside ordinary terrain even though it represents moisture on tilled soil | Removed from direct palettes; retained as `Watered Tilled Soil` created by watering action |
| Missing direct tuples | V7 has no exact pair for several Gravel/Rock/Mud contacts | Added exact-first reviewed connector overlays using complete existing V7 tuple cells |
| Style isolation | Connector work could have reintroduced cross-style or generated pixels | Atlas PNG/JSON hashes are unchanged; connector candidates resolve only from the certified V7 manifest |
| Complex junctions | Proxy substitution across three or more materials could invent ambiguous topology | Bridge resolver is restricted to exactly two distinct materials; complex junctions remain diagnostic |
| Checkpoint | User identified the current Z80 build as a checkpoint | Added explicit Pass167Z80 checkpoint contract and made Z81 depend on it |

## Reviewed source materials

Owner fills:

- Gravel: `Gravel_1`
- Rock Ground: `Rock_Dark`
- Mud: `Mud_Brown`
- Watered Tilled Soil state: `Mud_Brown`

Reviewed connectors use only exact pair-shape coverage already present in `lpc_mapped_terrain_v7_32.json`, including:

- `Stone_Tan / Grass`
- `Stone_Tan / Sand`
- `Dirt_Tan / Soil`
- `Dirt_Brown / Water`
- `Dirt_Brown / Water_Deep`
- `Dirt_Brown / Water_Shallows_Dirt`
- `Sand / Water_Shallows_Sand`
- `Dirt_Roots / Grass`
- `Dirt_Roots / Mudstone_Brown`
- `Dirt_Brown / Sand`

Every reviewed pair was checked for all fourteen non-uniform 2×2 corner arrangements.

## Pixel-integrity evidence

The normalized V7 outputs were not modified:

- Manifest SHA-256: `6b38c1ad88d02ec4be9ce6a83990e7acc08e1a40abd963ce89c6c68819480703`
- Atlas PNG SHA-256: `edac6c174572ace834e6014c624042fdf2eab859a03d082550e3db8815dafed1`

## Acceptance targets for Windows

1. Paint isolated and connected Gravel patches against Grass, Sand, Dirt, paths, soil, rock, mud, and water.
2. Confirm Gravel remains Gravel after save/reload and does not trigger shoreline lifecycle behavior in Exact mode.
3. Paint Rock Ground against Grass, Sand, water, Gravel, Mud, and paths; verify it remains walkable.
4. Paint Mud against Grass, Sand, soil, and water; verify quiet owner fills and complete edges.
5. Confirm Watered Tilled Soil is absent from direct Ground palettes but still appears after watering Tilled Soil.
6. Verify F3 diagnostics distinguish `exact`, `authored bridge`, and `unsupported` contacts.
7. Verify the same results at and across PCG storage-partition boundaries.

## Next

Proceed to derived elevation cliffs only after the three ground materials pass live visual acceptance.
