# HW-CLIFF-RAMP-CERTIFICATION-06R1

## Purpose

This is a patch-friendly follow-up to `HW-CLIFF-RAMP-CERTIFICATION-06`.
It keeps the Havenwild-side cliff/ramp work independent from ForgePY while the
ForgePY transport rules are still being normalized.

The pass avoids editing `published_world_topology.rs` directly. Instead, it adds
an integration-test authority file and a short library note. That makes the
patch safer to apply even if an earlier local attempt partially inserted
source-module tests.

## Current published ramp contract

The active published topology contract remains:

| ID | Source | Rect cells | Anchor |
| --- | --- | --- | --- |
| `cliff.ramp.rise_right.grass` | `content/assets/oga_lpc/source/terrain/cliffs_grass_top/LPC_cliffs_grass.png` | `[3, 5, 3, 4]` | `[-1, 0]` |
| `cliff.ramp.rise_left.grass` | `content/assets/oga_lpc/source/terrain/cliffs_grass_top/LPC_cliffs_grass.png` | `[6, 5, 3, 4]` | `[-1, 0]` |

This pass does not visually certify a new ramp placement. It protects the
current runtime-certified contract so later Assemble/preview work cannot drift
silently between `[-1, 0]` and the older `[-1, -1]` hypothesis.

## Certification boundary

A future anchor migration must be a deliberate visual certification pass. It must
update all affected project-side contracts in one change:

- published topology metadata;
- editor Assemble/stamp preview;
- structural access/worldgen placement;
- runtime draw and depth footprint;
- tests and validation docs.

Until that happens, `[-1, 0]` is the active published contract.
