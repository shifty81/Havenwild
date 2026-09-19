# B48R8 — ElizaWy summer waterfall-transition missing-source recovery

## Direct findings

- B48R7 checked the reference split `Terrain/Mountain, Waterfall Transitions (Summer).png` against `Terrain/cliff_summer.png` and found 10/42 exact tile matches.
- B48R8 checked **all 29 original Terrain.zip PNGs**: the 32 waterfall-transition nonmatching cells have **zero exact 32×32 matches anywhere in the original combined archive**. Two of the overall 40 B48R7 unmatched records are available elsewhere in that archive; 38 remain unmatched across the 29 PNGs.
- The complete **192×224 RGBA original source file**, SHA256 `8deafc172a31e96409d31ef0e7c23eee1b25d3c903ff24f6ab602f56985c1ae4`, is included unchanged in the root-drop patch under `assets/source/licensed/lpc_revised/Terrain/Mountain, Waterfall Transitions (Summer).png`. This recovers all 42 waterfall-transition source cells without altering existing atlases or inventing artwork. The 32 missing cells were not an empty/transparent bug or a renderer misconfiguration: they were missing exact source pixels from the old combined atlas collection.
- License and provenance follow the reference archive's `Terrain/Credits.txt` (Mountain includes Eliza Wyatt / Lanea Zimmerman, OGA-BY 3.0); a byte-identical copy accompanies the image.

## Source role versus game readiness

The recovered sheet visibly includes cliff-top/water interface pieces, but their topology, ordering and placement against the original ElizaWy demo are NOT established by a per-cell hash. The board shows direct source pixels and their omission state, **not** an assembled Havenwild game scene. Previous B43 winter approvals remain unchanged. North row 0 remains a candidate, not a complete north-running waterfall. Existing 7 fps runtime animation is unchanged. No separate north or frozen family is silently enabled.

B48R8 is a **real missing-source recovery and usable deterministic authoring input**. The project can now resolve the sheet through `assets/source/licensed/lpc_revised/Terrain/Mountain, Waterfall Transitions (Summer).png`, and the new validator checks source/cell coordinates, its source hash, its existence in the project, and its B48R7 agreement. The editor/client renderer and physical collision have NOT yet consumed the new recipe; a screenshot alone cannot prove collision.

## PCC lineage

B48R8 is an incremental root-drop PCC patch intended for the user's GREEN B48R7 project. It adds only new paths; it does not overwrite previous B22–B48R7 changes and is **not a complete cumulative source rollup**. The complete Sept 17 rollup plus B48R7 patch were available for isolated staging, but the actual user's current post-GREEN directory was not available for Windows compile or source-diff checks. Do not mark full gate GREEN for B48R8 based on B48R7's separate GREEN checkpoint.

## Clean-clone preservation and hydration

Havenwild intentionally Git-ignores all of `/assets/` and `*.png`. A source PNG installed **only** under `assets/source/licensed/` would disappear from a clean Git checkout even if the PCC gate was GREEN locally. B48R8 therefore also preserves identical original PNG bytes as the non-PNG, Git-trackable `content/assets/lpc/source_blobs/elizawy_mountain_waterfall_transitions_summer.png.source`, and keeps its original credits under `content/assets/lpc/credits/elizawy_reference_terrain_credits_b48r8.txt`. This is not recompressed or altered artwork: the blob is byte-identical to the PNG.

Run `python tools/automation/validation/checks/assets/Hydrate-ElizaWyWaterfallTransitionB48R8.py` after a clean clone to restore the ignored local asset mount. This operation refuses overwriting a different existing file. Run `python tools/automation/validation/checks/assets/Validate-ElizaWyWaterfallTransitionB48R8.py` to check source bytes and every cell without requiring Pillow. The optional `--reference-zip` also matches the uploaded original pack byte-for-byte. The supplied regression test checks corrupted PNG, cell hashes, duplicates, attempted runtime promotion, and clean-clone hydration.

No automatic PCC command registration or build-gate enrollment has been performed; these commands are explicit until reviewed against the actual current GREEN repository. This patch does not promise editor/client runtime sourcing of these new cells.
