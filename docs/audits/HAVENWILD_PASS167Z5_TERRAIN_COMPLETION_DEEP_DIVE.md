> **Superseded evidence note:** Pass 167Z5A corrects the preview/certification claims in this document. The former flat-color images are semantic topology diagrams, not LPC or runtime renders. Use the Z5A atlas-backed evidence instead.

# Havenwild Pass 167Z5 — Terrain Completion Deep Dive

## Scope

This pass closes the highest-risk terrain defects visible in the client:

- repeated per-frame terrain classification and water-span construction;
- production terrain mixed with emergency solid-color grass spans;
- generated water without an enforced depth/shore ordering;
- cliff faces without a guaranteed walkable rock top;
- test fixtures that omitted ponds, bridges, multi-material junctions, and the complete semantic palette;
- stale diagnostics that described the old traversal path.

It does not claim final live-FPS certification. Runtime frame timing still has to be measured on the Windows client after the patch is compiled.

## Runtime render normalization

`VisibleTerrainPlanCache` now retains the complete visible terrain plan until one of four authoritative inputs changes:

1. camera tile bounds;
2. active scene;
3. terrain/autotile revision;
4. world-paint revision.

Sub-tile camera movement no longer rebuilds terrain classification. The retained plan contains:

- sorted row-major visible cells;
- base/mixed-boundary submission indices;
- project-paint submission indices;
- legacy transition indices;
- greenhouse overlay indices;
- precomputed pure-water spans.

Pure-water cells are no longer sent through the base terrain draw function before the water material pass. Water spans are created only when the plan is rebuilt and may cross 16-tile chunk boundaries.

The normal client no longer scans every visible terrain cell for developer overlays. That scan now runs only while developer mode is active.

## Terrain ownership

The runtime ownership order is now explicit:

```text
semantic terrain
  -> cached mapped LPC tuple for base/mixed boundary
  -> pure-water material spans
  -> project paint
  -> compatibility transitions only when mapped atlas is unavailable
  -> gameplay/debug overlays
```

Solid-color grass spans remain an emergency no-atlas fallback only.

## Generated terrain topology

The client-loaded farmstead fixture now runs deterministic cleanup passes for:

- deep/water/shallow shoreline depth ordering;
- freshwater pond bank and shallow-water buffers;
- route-to-bridge conversion at water contacts;
- cliff-to-walkable-rock adjacency;
- tall-grass removal near routes, shorelines, water, and cultivated soil;
- protected route accessibility.

Generated `ShoreFoam` and `RiverMouthBlend` cells are prohibited. Those are compatibility/presentation roles rather than persistent terrain authority.

## Certification fixtures

The acceptance suite now includes nine scenes:

1. coastline;
2. river;
3. pond and bridge;
4. farm soil;
5. mountain/cliff/ramp;
6. three/four-material junctions;
7. cold-biome bands;
8. wrapped-world seam;
9. complete TileKind gallery.

The gallery includes compatibility-only roles for inspection, but production-generated scenes may not use those roles as semantic terrain.

## Build workflow

`tools/build/Build.sh all` now regenerates the client test terrain, regenerates all terrain acceptance scenes, and runs the topology validator before Rust compilation.

A focused command is also available:

```bash
./tools/build/Build.sh terrain-cert
```

## Remaining live certification

After compilation, verify:

- no large flat green rectangles at 85%, 100%, 135%, or 220% zoom;
- stable plan-hit growth while the camera remains inside the same tile bounds;
- plan rebuilds only when crossing a tile boundary or changing terrain/paint/scene;
- water submissions remain span-based;
- no continuous base-cache rebuilds while idle;
- frame time with F3 disabled is lower than Pass 167Z4;
- coast, pond, cliff, farm, and route boundaries remain visually correct.
