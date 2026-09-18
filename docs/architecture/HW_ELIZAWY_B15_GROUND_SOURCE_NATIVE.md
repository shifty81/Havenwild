# B15 — ElizaWy ground source-native inspection and legacy rule reset

## Verified intent and real scope

B13 full-source integrity is complete and B14 source-only provider catalogs are GREEN. This pass establishes ElizaWy ground source addresses and a review board, and removes the **incorrect V7-supplement language** from the LPC Revised ground authority. It does NOT claim any tile is semantically correct, walkable, transition-compatible, commercially approved, or renderer-certified. The current V7 editor/client renderer and previously authored saves remain unchanged until the coordinated cutover. Preserve the old configurations as legacy runtime inputs; do not delete V7 validators while the active V7 runtime still uses them.

## Added implementation

- `elizawy_ground_cell_contract_b15.json`: single pinned ElizaWy-only candidate contract; no V7 or non-ElizaWy fallback; ties existing index, B13, B14, and generated terrain domain catalog together.
- `Build-ElizaWyGroundCellReviewB15.py`: byte-verify seven genuine source sheets against historical SHA-256 and size, verify PNG headers/dimensions, source catalog stable IDs, generate unique, pixel-exact cell rectangles for all five 512×832 seasonal sheets (5×416 addresses), the 256×256 farm sheet (64 addresses) and 192×192 ice-shallows sheet (36 addresses). Expected total: **2,180 source addresses**. Outputs are local generated workspace files only; raw source art remains read-only.
- A local HTML board showing the unmodified source artwork at 1:1 pixels, optional grid overlay, and hover coordinates. Open `WORKSPACE/generated/lpc/elizawy_ground_review_b15.html` with a browser. Do not copy/paint a single addressed cell until its actual source visual role and connected neighbors are identified.
- `elizawy_ground_review_decisions_b15.json` is deliberately empty. It is the controlled, project-owned destination for future reviewed mappings. The validator refuses arbitrary IDs, duplicate entries, publication, or treating source cells as certified assemblies.
- Source-native authority no longer describes seasonal ElizaWy art as supplemental to terrain-map-v7, and its unsupported-contact rule no longer directs new authoring to V7 tuples or synthetic semantic fill. The retained `terrainTupleAuthority` object is explicitly historical for existing V7 saves, **not** a new production source.

## Why review is necessary

The actual source `terrain_summer.png` has authored multi-cell elements: surface patches, shoreline pools, cut-ins, islands, and river/water patches. Its 32×32 grid is an addressing grid, not a promise of 416 independent walkable terrain assets. Coordinate-equivalent seasons also do not prove matching terrain roles or alpha geometry. No role, adjacency, game collision, coast, waterfall, cliff connector, or ramp is inferred solely from coordinates or filenames.

## User-side verification (Experimental)

Apply the root-drop ZIP unextracted through the existing PCC. After a GREEN gate, from the **Havenwild root**:

```powershell
py -3 tools/automation/validation/checks/assets/Test-ElizaWyGroundCellReviewB15.py
py -3 tools/automation/assets/Build-ElizaWyGroundCellReviewB15.py --root .
start WORKSPACE/generated/lpc/elizawy_ground_review_b15.html
```

Expected status: `SOURCE_CELL_INVENTORY_READY_FOR_REVIEW`; seven source sheets; 2,180 source addresses; zero blockers; `runtimeCutover:false`, `productionApproved:false`, `tileCertification:NOT_PERFORMED`. If blocked, send `WORKSPACE/generated/lpc/elizawy_ground_certification_b15.json`; never force activation. The source index is loaded but the 64,365-file repository is **not rescanned**. This audits only the seven ground/soil/ice PNG files.

Inspect the board as exact original art, compare spring/summer/autumn/winter/winter-ice, and note composed fills/borders/ponds and any connected regions. The goal is a reproducible mapping review, not approving 2,180 coordinates as individual tiles.

## Next development and cutover sequencing

B15 follow-up: map semantic fill/edge/inner-and-outer-corner/shoreline/connected transition *assemblies* from the board into review decisions and independently evidence per-season compatibility; only valid combinations may enter published bindings. B16: original cliff sheets, authored height assemblies, actual climbable faces/ladders/vines and verified gameplay traversal. B17: water, shoreline animations, waterfall host and frames. Then objects/structures/characters/FX, shared editor/client resolver, legacy-save migration adapter, and image + traversal + perf certification. Retire obsolete V7 validators **at the same time** as its runtime path, never sooner and never by weakening the Full Quality Gate.
