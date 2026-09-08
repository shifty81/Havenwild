# Havenwild Pass 111 - LPC Mixed-Corner Overdraw Rollback

## What Regressed

Pass 110 tried to fix square sand/grass intersections by drawing the authored
2x2 inner-corner role whenever a cell had one cardinal neighbor and one matching
diagonal neighbor.

In editor testing, that overfired on ordinary stair-stepped borders. Long sand,
wet-sand, and shoreline edges repeated the 2x2 corner bite along the whole run,
creating scalloped chunks and square-looking coast artifacts.

## Corrected Contract

- Pure diagonal contact still uses the authored LPC inner-corner role.
- Mixed edge-plus-diagonal contact stays edge-only for now.
- Mixed contacts require a dedicated 8-neighbor/47-tile role before they can
  draw extra corner art.
- The Pass109 global closed-corner compound-fill shortcut remains rolled back.

## Why This Is Safer

The current LPC transition source has reliable edge roles and pure diagonal
corner roles. It does not yet provide a distinct role for "edge plus diagonal"
contacts. Reusing the pure diagonal role in that topology corrupts broad borders
more severely than the original square-corner limitation.

## Next Required Art/Topology Work

The lasting fix is a visual conformance board and a real 8-neighbor transition
policy per material pair:

- grass over sand;
- grass over dirt;
- sand over wet sand;
- shallow water over sand/wet sand;
- shallow water over deep water.

Each pair needs one-cell, line, L-shape, T-shape, plus-shape, diagonal stair,
island, and inlet cases before the editor should expose it as fully finished.
