# Havenwild Pass 167Z5A — LPC Terrain Evidence Audit

## Finding corrected

The former `havenwild_client_test_world_v167z.png` and `havenwild_terrain_acceptance_contact_sheet_v167z5.png` files were semantic topology diagrams. They used flat debug colors and could not certify LPC visuals.

## New evidence contract

The corrected pipeline creates three clearly separated outputs:

1. **Semantic topology** — compact diagnostic colors, watermarked as not game art.
2. **LPC mapped-terrain render** — 32×32 pixels copied only from `lpc_mapped_terrain_v7_32.png`, selected through the four-corner tuple manifest.
3. **Comparison** — semantic map and LPC render shown together.

The atlas-backed lane reports missing semantic bindings, missing tuples, owner-fill fallbacks, invalid rectangles, transparent source cells, and source-rectangle usage. It never substitutes flat debug colors.

## Runtime-aligned fixes

The audit exposed two production mismatches:

- `PebbleShore` requested `Gravel_1`, but the generated mapped atlas previously omitted that source material.
- `TallGrass` was treated as a dark terrain fill, producing obvious square patches instead of vegetation layered over grass.

Both are normalized in this pass. Grass decorative fills are also rebased onto the quiet grass tile and selected sparsely.

## Scope limit

The atlas preview certifies the mapped terrain base. It does not claim to render actors, objects, bridge meshes/details, structural overlays, animated water shaders, weather, lighting, or HUD. Those require live-client screenshots and frame telemetry.
