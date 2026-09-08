# Terrain Live Certification Checklist

Use this after `tools/build/Build.cmd all` succeeds.

## World Builder

- Paint Grass, Sand, Dirt, Dark Grass, Dead Grass, Soil, Rock, Snow/Ice, and Water.
- Confirm exact tuple artwork updates around all four corners.
- Confirm unresolved tuples appear in the diagnostic overlay.
- Confirm the inspector reports the same semantic gameplay profile as runtime.
- Confirm ordinary objects cannot be placed on water or cliffs.
- Confirm foundation and bridge support queries accept water and reject cliffs.

## Runtime parity

- Open the same map in the game client.
- Compare coastlines, rivers, farm boundaries, mountain paths, and snow edges.
- Confirm no legacy transition overlay is drawn over exact tuple artwork.
- Confirm shallow water blocks normal movement.
- Confirm traversal capability tests do not bypass object or stamp collision.

## Wrapped world seam

- Paint connected terrain across the left and right map boundaries.
- Confirm the tuple selected on each edge matches the wrapped neighbor.
- Confirm collision and movement costs remain semantic across the seam.

## Evidence

Capture:
- one editor screenshot;
- one matching runtime screenshot;
- the generated terrain pipeline certification report;
- the complete `tools/build/Build.cmd all` log.
