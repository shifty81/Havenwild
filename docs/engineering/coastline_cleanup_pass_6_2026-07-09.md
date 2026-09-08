# Havenwild Coastline Cleanup Pass 6 — 2026-07-09

## Purpose

Pass 6 upgrades the generated terrain underneath the Pass 4 transition overlays. The renderer can now draw water/land/grass/sand/dirt transitions, but the generated base terrain still needed a cleanup stage so the coast itself is less square before art overlays are drawn.

## Added

- `CoastlineCleanupReport` in `crates/haven_world/src/autotile/shoreline_resolver.rs`
- tiny water speckle removal
- one-tile land spike erosion
- shallow-water band rebuild
- primary shoreline band rebuild
- secondary shoreline band rebuild
- explicit preservation of authored/structural tiles
- startup cleanup for generated starter/worldgen-pack worlds
- reset/regenerate cleanup for generated scenes
- Farmstead biome changed to Coastal because the home tavern is on the starting island/coast
- `Validate-CoastlineCleanupV12.py`
- `content/worldgen/havenwild_open_world_preset_v1.json` coastline cleanup metadata

## Safety rule

Saved worlds are not auto-mutated during startup. Cleanup is applied only to generated starter/worldgen-pack worlds and to reset/regenerate outputs. Future editor buttons can explicitly rebuild a selected saved scene's coast after confirmation.

## Runtime impact

Expected visible improvements:

- fewer isolated single-cell water holes
- fewer jagged one-tile land teeth
- clearer shallow-water ring around coastlines
- wider and more coherent beach/shore band
- better input to the terrain transition debug overlay

## Next pass

Add atlas-backed shoreline material variants so `WetSand`, `Foam`, `ShallowWaterEdge`, `SandBlend`, and related transition materials can resolve to actual sprite cells instead of only procedural overlay drawing.
