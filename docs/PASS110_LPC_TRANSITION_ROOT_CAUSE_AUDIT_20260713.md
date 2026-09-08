# Havenwild Pass 110 - LPC Transition Root-Cause Audit

Superseded by Pass 111. The Pass 110 mixed edge-plus-diagonal rule overlaid
pure 2x2 inner-corner art on ordinary edge runs, which produced repeated
scalloped bites along sand, wet-sand, and shoreline borders. Keep the Pass109
global compound-fill rollback, but do not keep Pass110 mixed-corner layering.

## Problem Seen In Editor

Sand painted on grass still left square owner-colored cells at tile intersections.
The Pass109 hotfix did not change that case and also introduced wet-sand/shoreline
square artifacts.

## Root Causes

1. Mixed edge-plus-diagonal contacts were intentionally suppressing the authored
   LPC 2x2 corner role. A sand/grass stair step such as `north edge + north-east
   diagonal` rendered only the cardinal edge, so the diagonal corner stayed square.

2. Pass109 tried to fix closed sand/grass corners by forcing any owner cell with
   adjacent edges plus an outer corner to mask `0b1111`. That shortcut was global,
   so wet-sand and water-bank families also picked compound fill cells and produced
   the peach square artifacts visible on the coast.

3. Several rollups omitted the generated transition atlas and LPC family mapping.
   That allows local builds to mix new Rust with stale generated terrain art. This
   remains a packaging/build-contract issue to tighten further, but the runtime
   resolver fix below does not depend on stale generated state.

## Corrected Runtime Contract

- Pure diagonal contact still uses the authored 2x2 inner-corner role.
- Mixed edge-plus-diagonal contact now also requests the authored 2x2 inner-corner
  role, drawn after the cardinal outer edge.
- Adjacent edge plus outer-corner contact no longer mutates the outer mask globally.
- Unsupported compound masks remain the responsibility of the generated atlas bake,
  not a Rust-side forced mask rewrite.

## Validation Added/Updated

- `Validate-LpcMixedCornerTopologyV116.py` now locks mixed edge-plus-diagonal
  corner requests.
- `Validate-LpcClosedSandGrassCornerTopologyV121.py` now locks the rollback of
  the Pass109 global closed-corner shortcut.
- V117/V118 were updated so broad environment policy validation no longer
  re-enforces the stale Pass103/104 "single replacement only" assumption.

## Manual Acceptance Focus

Retest these exact cases:

1. Sand brush on grass: one-cell, line, L-shape, plus-shape, stair-step diagonal.
2. Grass island inside sand: one-cell and 2x2 island.
3. Sand next to wet sand: diagonal coast, narrow strip, and concave inlet.
4. Wet sand next to shallow water: diagonal shore and shallow-water curve.
