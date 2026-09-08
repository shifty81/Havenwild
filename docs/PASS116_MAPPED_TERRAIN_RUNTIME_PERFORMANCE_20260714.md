# Pass 116 Mapped Terrain Runtime Performance

Date: 2026-07-14

## Symptom

The runtime could drop to roughly 1 FPS when a large mapped terrain field filled the screen.

## Likely cause

Pass114 introduced a complete mapped LPC terrain atlas with 5,760 entries. The runtime lookup path was still shaped like a small-table lookup:

- every visible tile called `lpc_mapped_terrain_entry_for_map`;
- each call scanned the full manifest entry list to count matches;
- it then scanned again to select the chosen variant;
- the transition pass could call the same lookup around the current cell again.

On a wide 2K viewport this can become tens of millions of material string comparisons per frame.

## Pass116 fix

`crates/haven_assets/src/lpc_mapped_terrain.rs` now builds an indexed lookup when the manifest loads:

- material names are converted into a typed `LpcMappedTerrainMaterial` enum;
- each corner tuple becomes `[LpcMappedTerrainMaterial; 4]`;
- a `HashMap<[LpcMappedTerrainMaterial; 4], Vec<usize>>` maps the tuple directly to its variant rows;
- runtime selection is now direct lookup plus deterministic variant selection.

This removes the per-tile full-manifest scan and avoids per-tile string comparisons.

## Guard

`tools/automation/validation/checks/terrain/Validate-LpcMappedTerrainRuntimePerformanceV124.py` prevents this from regressing by checking that:

- the mapped terrain manifest uses a typed-material `HashMap`;
- the runtime no longer uses `self.entries.iter().filter`, `matches().count()`, or `matches().nth()` in the lookup path.

The V124 guard is wired into both:

- `tools/build/Build.sh` pre-cargo validation;
- `tools/automation/validation/validate.py`.

## Long-term engine optimization path

This pass fixes the immediate hot path. The longer-term renderer should still move toward:

1. dirty-region terrain resolution caches per scene;
2. chunk-level terrain render buffers/meshes instead of thousands of tile draw submissions;
3. atlas/material bucketing per chunk;
4. optional offscreen cached chunk textures for static terrain;
5. separate editor overlay rendering so debug/editor UI never invalidates terrain chunk caches.

Do those after terrain correctness is stable. The indexed lookup is safe to put in now because it preserves output behavior while removing the largest accidental CPU cost.
