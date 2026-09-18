# B16 — Exact ElizaWy artwork inspection and first ground assembly candidates

## Evidence actually inspected

The original uploaded `Terrain.zip` was visually inspected against the uploaded original `DemoGame - 2 - Summer.png` scene and the B15-generated source inventory from `catalogs.zip`. Every one of the seven ground-source PNG byte hashes equals its B15 inventory hash, including all five seasonal ground sheets and the two supplemental sheets. The full source repository remains externally mounted and immutable. `Terrain/Credits.txt` attributes original terrain contributions to Lanea Zimmerman and Eliza Wyatt; preserve exact upstream credit data, not inferred authorship from a filename.

- All five `terrain_<season>.png` sheets are 512×832, on a 16×26 source address grid. Their apparent horizontal and vertical motifs occupy multiple cells. Matching coordinates alone **do not prove** interchangeable semantics or animation. In particular, winter changes the apparent grass surface into snow and the adjacent earth surface into an icy stone-like texture; identical coordinates must not automatically produce identical biome/material semantics.
- `tilled_soil.png` is 256×256, containing connected 3×3 soil patches and variants; `ice-shallows.png` is 192×192 and includes an authored surface and edge assembly. Both need underlying-material and adjacency review.
- Source screenshot and summer sheet visibly show grass, earth, sand, pools, shoreline strips, and water variants arranged into designed connected pieces; blindly treating all 2,180 source addresses as standalone paintable tiles would break these authored pieces.
- The summer cliff sheet also contains cliff profiles, cave openings, vines/vegetation, ladders, and water-contact details, while Waterfall.png and FX images are separate source assemblies. Those require their own cliff/traversal/waterfall passes; they are *not* validated by B16 ground candidates.

## Implementation

`content/worldgen/elizawy_ground_visual_candidates_b16.json` lists ten inspected candidate groups with exact **source-cell rectangle** coordinates and grounded visual descriptions. The eight seasonal groups expand to five original sheets each; the two supplemental groups each refer to one sheet. In total, 42 source placements are individually backed by B15 source-file SHA-256 and exact B15 cell IDs. IDs are proposals for review and are **not** registered as runtime tile IDs. Unreviewed parts of the original sheets remain fully accessible through the B15 source browser.

`Build-ElizaWyGroundVisualCandidatesB16.py` validates B15 and pinned source evidence and produces a read-only HTML board displaying exact original PNG rectangles at 2× nearest-neighbor zoom across seasons. Generated outputs live only under `WORKSPACE/generated/lpc/`; no PNGs, licenses, or generated files are committed or embedded in the patch. Original demo scene and credits must be present for evidence continuity.

The B16 report must say `SOURCE_RECT_CANDIDATES_READY_FOR_VISUAL_REVIEW`, `approvedMappings:0`, `approvedAssemblies:0`, `productionApproval:false`, and `runtimeCutover:false`. The candidate's visual description **does not certify** surface walkability, autotile masks, water depth, transitions, seasonal equivalence, legal shipping clearance, editor/game image parity, or traversal. These require separate decisions and an end-to-end rendered showcase. Do not enable V7/Universal LPC fallback or remove validators while the V7 renderer is still running.

## Windows checkout verification

From Havenwild root after PCC apply and Full Gate:

```powershell
py -3 tools/automation/validation/checks/assets/Test-ElizaWyGroundVisualCandidatesB16.py
py -3 tools/automation/assets/Build-ElizaWyGroundVisualCandidatesB16.py --root .
start WORKSPACE/generated/lpc/elizawy_ground_visual_review_b16.html
```

Compare the 42 exact snippets and original DemoGame test scene against local source. To advance, record source-specific approval and actual connected terrain grammar in a later review decision file; then test the same binding in editor and runtime. Do not certify every raw cell just because B15 inventory and B16 previews succeeded. No full 64k-file rescan is needed.
