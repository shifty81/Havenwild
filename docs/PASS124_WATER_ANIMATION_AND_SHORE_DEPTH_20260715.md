# Pass 124 — Water Animation and Shore Depth Guard

Date: 2026-07-15

## Purpose

The terrain-v7 runtime must keep all ordinary water/depth rendering on the
canonical mapped LPC terrain path while avoiding square fallback artifacts at
painted shorelines.

## Locked behavior

- Pure `Water` and pure `Water_Deep` fills may cycle through authored terrain-v7
  fill variants.
- Mixed shoreline and depth-transition tuples stay stable. Coastline shimmer,
  crawl, and foam should be implemented as a separate overlay animation, not by
  swapping the entire mixed edge tile every frame.
- Editor normalization keeps a shallow-water buffer around shore/land in the
  8-neighbor corner-tuple radius. This prevents unsupported `Sand <-> Water_Deep`
  corner tuples from falling back to blocky placeholder-looking tiles.
- Wet sand remains generated from cardinal sand/water contact. Diagonal sand
  contact stays dry sand.

## Deferred follow-up

The player can appear to stand on visual shoreline water where water art overlaps
a neighboring walkable sand/wet-sand cell. Core water tile semantics are already
non-walkable. If this remains visible after the shallow-buffer pass, fix player
movement with a footbox/collision-sample check rather than making water semantics
walkable.
