# HW-CLIFF-RAMP-CERTIFICATION-06R3

## Purpose

This pass records the current published cliff-ramp runtime contract without
requiring ForgePY to route a Git unified diff. It is packaged as a Forge manifest
`.patch` transport so ForgePY can apply it through the manifest/payload path while
its Git-diff routing rules continue to be normalized.


## ForgePY F60R415 transport binding

This transport is build/source-bound for ForgePY's modern manifest intake. It declares the current Havenwild GREEN source commit as a precondition so the package cannot silently apply to a stale or unrelated working tree.

## Current published ramp contract

| ID | Source | Rect cells | Anchor |
| --- | --- | --- | --- |
| `cliff.ramp.rise_right.grass` | `content/assets/oga_lpc/source/terrain/cliffs_grass_top/LPC_cliffs_grass.png` | `[3, 5, 3, 4]` | `[-1, 0]` |
| `cliff.ramp.rise_left.grass` | `content/assets/oga_lpc/source/terrain/cliffs_grass_top/LPC_cliffs_grass.png` | `[6, 5, 3, 4]` | `[-1, 0]` |

The older `[-1, -1]` hypothesis remains explicitly uncertified. A future visual
certification pass may change the runtime contract, but it must update metadata,
editor preview/assembly, worldgen placement, renderer/depth footprints, tests,
and validation docs together.

## Scope

This pass is Havenwild-only. It does not modify ForgePY, ForgePY routing, or any
Control Center code. It adds an integration test and an architecture note only.
