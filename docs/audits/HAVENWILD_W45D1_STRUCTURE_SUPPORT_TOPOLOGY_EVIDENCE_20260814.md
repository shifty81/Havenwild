# Havenwild W45D1 — Structure Support Topology + Exact Review Evidence

Date: 2026-08-14  
Pass: `167Z109W45D1`  
Baseline: `167Z109W40` cumulative overwrite lineage

## Purpose

W45D1 closes the *authority definition* for bridge/platform/pillar structural support before exact visual publication. It deliberately does not choose source cells from catalog dimensions alone.

The pinned ElizaWy/LPC Structure inventory contains:

- 5 bridge sheets;
- 2 platform sheets;
- 2 pillar sheets.

All nine remain `SOURCE_CANDIDATE` with `componentRectsReviewed=false` until machine-local source evidence is visually reviewed.

## Locked structural grammar

### Bridges

Bridges are bank-to-bank structural assemblies, not whole-sheet placeables. The future W45D2/W46 representation must distinguish:

- approach/bank A;
- repeatable walkable span;
- approach/bank B;
- optional left/right rail layers;
- end caps and support/post visuals;
- stateful drawbridge leaf where applicable;
- explicit bank sockets and orientation.

Walkable deck/collision authority is separate from decorative rail pixels.

### Platforms

Platforms are structural-surface assemblies with explicit fields, edges, corners and access connectors. They may belong to buildings or world structures but may not become a substitute for terrain elevation authority.

### Pillars

Pillars use base/shaft/capital/full-assembly grammar. Visual height may not alter semantic world level. Collision remains rooted at the occupied footprint.

## Exact review evidence

New root command:

`42. Build exact structure support review evidence bundle`

Direct command:

`tools\build\Build.cmd structure-support-review`

The command ensures the pinned LPC dependency and writes machine-local evidence to:

`WORKSPACE/generated/structure_review/w45d_exact_support/`

and packages:

`WORKSPACE/generated/structure_review/Havenwild_W45D_ExactStructureSupportEvidence.zip`

The evidence contains labelled 2x source boards, exact per-cell source rectangles, RGBA hashes, alpha occupancy/bounds, edge contact, duplicate groups, alpha-connected review groups and a blank semantic selection template.

Automated evidence never assigns semantic topology roles and never changes runtime authority.

## Validation

Targeted validation passes:

- W45A structure source inventory;
- W45B exact structural components;
- W45C1 surfaces/cutaway;
- W45C2 roof topology/wall border;
- W45C3A exact roof evidence authority;
- W45D1 structure support topology/evidence authority;
- architecture;
- project content;
- 18/18 content-integrity checks.

## Local continuation

After applying W45D1:

1. `2. Build development (fast)`
2. `9. Validate current source`
3. command `41` to generate the roof evidence ZIP
4. command `42` to generate the structure-support evidence ZIP
5. upload both evidence bundles

W45C3B/W45D2 can then publish only visually accepted exact regions before W46 BuildingRecipe authority begins.
