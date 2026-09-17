# B06 — Source-first visual reset, stage 1 (2026-09-17)

## Scope and truth

B06 is **not** a claim that the cliff, water, world canvas, ramp, ladder, or PIE work is finished. The previous B05C fix restored the correct source-derived W3 cliff wall overlay but the current editor screenshots still show rocky upper terrain, missing/back-face and connector problems, heavy water redraws and partition seams.

This first repair closes a concrete dependency hole and establishes a source-only water baseline. Do not remove authored semantic/structural levels, original LPC/OGA source folders, existing recipes, scenes, or the PCC. Generated runtime caches may be removed/rebuilt only when an exact provenance-backed builder and original source are available. No synthesized replacement image should be used to make a status indicator GREEN.

### Verified defects addressed by B06

1. `content/asset_packs/havenwild_objects/pack.json` registers `havenwild_structure_components_w45b.png`, `havenwild_structure_surfaces_w45c.png`, and `havenwild_structure_roof_trim_w45c2.png` as live sources. They are absent from both supplied September 17 rollups, and the editor's console confirms they are absent on the user's Windows machine.
2. The ordinary `dev/all` build creates LPC object and cliff caches but did not run the *existing* three W45 source-specific builders. The builders were exposed by separate specialized build commands instead. B06 runs a new preflight before Cargo that verifies existing W45 outputs or invokes those pinned-source builders on a missing/invalid cache. It refuses missing, hash-mismatched original source and never generates fake artwork. An incomplete source may now deliberately FAIL the Full Gate with a precise dependency message. That is an intentional truthful failure, not a Rust defect.
3. The native editor reloaded the same PNG for each published definition and repeated the same file-not-found warning. B06 decodes each source path once and reports each missing original/derived image once. This does not silently make a missing image available.
4. `lpc_mapped_terrain_owner_fill_entry_for_map_with_water_frame` selected per-cell water variations from V7, producing conspicuous pattern changes in broad water. B06 selects the exact quiet V7 source cell for pure water while preserving the separate exact mixed-tuple/shoreline overlay. Water animation/detail is temporarily suspended at the pure owner-fill level; water render calls have not yet been cached or batched. This is a **visual baseline**, not a water FPS fix.

### Missing separate source

The native editor also loads `content/assets/oga_lpc/source/terrain/cliffs_grass_top/LPC_cliffs_grass.png` for directional ramps, but that original is missing from the supplied archives and the Windows console. Its pack is explicitly quarantined (`production_enabled=false`). Restore the **exact file with its catalogued checksum, credits and license** through governed source intake; do not synthesize directional ramps or repurpose arbitrary ElizaWy cells. Until it exists, ramp artwork remains unavailable. Existing traversal semantics remain independent of artwork.

## Next source-first passes (strict order)

- **B07 — Source provenance and quarantine:** enumerate each *active* visual binding, certified source rect/whole assembly, original source SHA, license, and renderer consumer. Classify exact source, lossless packing, pixel-modified projection, compatibility/debug, and missing/quarantined. W45B door normalization/sign composition and W3 palette-stripping projection must be explicitly reviewed. Do not label either "identical original image." Keep unsupported bindings out of production until mapped and visually certified.
- **B08 — Cliff assembly correctness:** use the actual original cliff sheets and certified source-spans to author the north/back, south/front, edge/corner, top/receiver, and full directional ramp/ladder recipes. Never fabricate a missing orientation by scaling/rotating/cropping unrelated art. Top-surface choice belongs to the authored V7 material/terrain, not a hard-coded "all plateaus are rock" rule. The V7 library *does* contain source-authored rock material; the screenshot proves its current assignment is inappropriate, **not** that those pixels were invented.
- **B09 — Shared world-space sampling:** resolve tile/tuple and structural neighbors globally across partition boundaries using the existing tile sampler. A missing neighboring partition is "unknown," not water/rock/level zero. Preserve all existing world data and one authored Base World.
- **B10 — Retained renderer:** retain/upload source-backed static terrain and shoreline meshes or render targets by visible partition, only redraw dirty spans after authoring. Use the same render plan and source assets for editor and client. Measure per-frame tile draws, water time, partition generation and texture residency before/after. Do not promise FPS improvement from B06's visual change alone.
- **B11 — Proof:** one permanent side-by-side editor/client test map demonstrating original LPC grass/dirt/rock plateau options, corners, rear faces, ramps, ladders, multi-tier traversal, seam crossings, coastal water and varied zoom, with timing evidence.
- **PIE:** extract and embed a re-entrant game runtime session after B07–B11, not an external window disguised as PIE.

## Acceptance for this patch

Run PCC Option 1. If it stops on W45 original source, record the **specific missing path**: the cache recovery correctly refused fake art. If it passes, editor startup should no longer emit repeated identical W45 warnings. In the same water test location, pure water should use one V7 quiet source tile, while original transition overlays remain; note that water lag, cliff back faces and missing ramps are still open.

The complete/full rollups exclude original licensed source directories, so local source availability cannot be certified from those ZIPs. Windows compilation and real editor/client FPS have not been performed for this patch.
