# Havenwild V7 Tile Lane Contamination Audit — Pass 167Z60

## Result

Cross-contamination was confirmed in the Pass 167Z59 baseline. The original `lpc-terrains-v7` source package itself is intact and does not contain ElizaWy files, but the generated atlas and runtime family combined V7 and ElizaWy pixels.

## Confirmed contamination

1. `Build-LpcMappedTerrainV7.py` replaced the first authored V7 grass fill with the `grass` cell from `common_base_terrain_32.png`.
2. `common_base_terrain_32.json` identifies that atlas as an Eliza Wyatt / Lanea Zimmerman LPC promotion, so the generated V7 atlas contained an ElizaWy-derived grass tile.
3. `terrain_visual_family_authority_v0_1.json` declared the active family as `lpc_authored_terrain_map_v7_plus_summer_wet_sand_v1` and explicitly allowed `terrain_summer.png` inside the same family.
4. `terrain_v7_highland_v1` pointed to ElizaWy `cliff_summer.png`, so a V7-labeled family was sourcing ElizaWy art.
5. Runtime water-depth contours and several direct transition groups are drawn from ElizaWy `terrain_summer.png` while V7 mapped cells provide underlying terrain.
6. The terrain certification renderer deliberately loaded both V7 and ElizaWy summer sheets.

## Clean areas

- `content/assets/lpc/source/lpc-terrains-v7/terrain-map-v7.png`
- `content/assets/lpc/source/lpc-terrains-v7/terrain-map-v7.tsx`
- `content/assets/lpc/source/lpc-terrains-v7/terrain-v7.png`
- `content/assets/lpc/source/lpc-terrains-v7/terrain-v7.tsx`
- `content/assets/lpc/source/lpc-terrains-v7/CREDITS-terrain.txt`
- V7 editor bindings that point directly to `content/assets/lpc/source/lpc-terrains-v7/terrain-v7.png`

The V7 source credits list the original LPC terrain contributors and do not list Eliza Wyatt as a source contributor for this package.

## Corrections applied

- Removed the `common_base_terrain_32` grass replacement from the V7 atlas builder.
- Regenerated `lpc_mapped_terrain_v7_32.png` using only `terrain-map-v7.png` and `terrain-v7.png`.
- Updated the generated manifest to version `0.4.0` with explicit `stylePackLane` and `sourcePurity` metadata.
- Quarantined the current mixed mainland runtime as `legacy_mixed_mainland_v1`; it is no longer represented as the V7 lane.
- Added the pure `lpc_terrain_v7_island_v1` family with cross-family fallback disabled.
- Renamed the ElizaWy-backed highland family to `elizawy_highland_v1`.
- Added a machine-readable isolation contract and build validator.

## Remaining migration work

The live mainland renderer is still a legacy mixed integration. It must not be used to certify the pure V7 island lane. A later terrain-style-pack pass must give both ElizaWy and V7 their own complete fill, edge, corner, shoreline, and depth mappings while sharing only topology identifiers and neighbor-mask policy.

The pure V7 lane also intentionally omits `WetSand`; its coast policy is `Sand -> Water_Shallows_Sand` until a V7-authored wet-sand material is added.
