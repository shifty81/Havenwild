# Havenwild Pass 99 — LPC Editor Paint Topology Stabilization

Pass 99 fixes the failures visible when painting small test squares in the
client World Editor.

## Fixed behavior

- Opposite-edge, T, and enclosed terrain masks use the verified repeatable LPC
  neighbor fill. They no longer leave transparent cells that expose square
  patches of grass inside dirt, sand, or water.
- The client runtime now loads and draws the existing complete 16-mask
  same-family atlas. Roads, paths, walls, cliffs, cave walls, and supported
  floors respond to adjacency in the game, not only in the native editor.
- `tools/build/Build.cmd all` rebuilds that atlas after LPC base promotion, preventing an
  older project-art atlas from surviving underneath the new runtime binding.
- Pebble-path topology recognizes grass, dirt, sand, and wet-sand neighbors.
- Painting deep water automatically maintains a shallow-water boundary.
  Boundary deep cells become shallow and enclosed shallow cells return to deep
  as the water body grows.

The runtime cache is still synchronized after every editor stroke, so the
painted cell and its neighboring topology resolve immediately.

## Build

Extract this complete source rollup over the repository and run:

```bat
tools/build/Build.cmd all
```

V114 locks the compound-mask, same-family runtime binding, pebble-path, and
deep-water boundary fixes.
