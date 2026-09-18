# B19 — Canonical ElizaWy ground-sheet geometry and corrected classifications

**Scope:** Consolidates B15–B18's fragmented *provisional* source interpretation into ONE canonical 16×26 coordinate layout, with five seasonal source substitutions. This is a real implemented mapping of every address and every seasonal source reference, **not** a claim that every cell has an approved semantic role or an active runtime binding.

## Evidence and results

- The original `Terrain/terrain_summer.png` is the canonical 512×832 (32px × 16 columns × 26 rows) layout; spring, autumn, winter and winter-ice are the corresponding source PNGs. All five are verified against the B15 source-inventory SHA-256 before mapping.
- Creates a unique stable identity for every one of 416 canonical coordinates: `elizawy.ground.master.cXX.rYY`, plus *exact original* per-season B15 cell IDs, source hashes and pixel rectangles: 2,080 source substitutions, no repacking or pixel edits.
- Checks original image transparency at the pixel level using a built-in, dependency-free RGBA PNG reader (no extra Pillow install). The normal spring/summer/autumn/winter occupied-pixel layouts match. Winter differs in one numerical alpha value only; winter-ice differs in exactly two fully occupied source cells at `[6,21]` and `[11,21]` (2,048 occupied-pixel changes and one other alpha-value change). These exact exceptions must stay declared; unexpected differences block generation.
- Checks 10 B16 candidates against original B15 IDs, B17 proposals and B18 intact-assembly evidence. Outputs 42 original-sheet source placements, covering 193 address placements and 35 of 416 *unique summer locations*. Remaining 381 summer coordinates are **explicitly UNMAPPED**, not guessed or silently promoted. Counts of the 100 supplemental sheet addresses are preserved. B16–B18 remain historical evidence, not active terrain grammar.
- Corrects two misleading provisional labels: `ground.water.surface.visual` is a water-detail/pattern **candidate**, and `ground.water.dark.visual` a dark-gradient **candidate**, not repeatable water fills or proof of gameplay depth. Do not publish those B17 assumptions.
- Rectangular nine-slice arrangements for grass, grass-bordered pool, tilled-soil and ice-shallows remain *candidates*. B19 measures center/top-edge/left-edge opposite-border RGBA differences in every available seasonal placement. It does not claim that matching border pixels alone proves aesthetic seam quality, extensibility, curved/concave topology, collision, or an approved brush.
- Outputs a browsable five-season whole-sheet HTML review grid, showing provisional candidate membership and winter-ice differences by coordinate. It links to the original external source PNGs and does not embed or distribute those PNGs.

## Run from the Havenwild repository root

```powershell
py -3 tools/automation/assets/Build-ElizaWyMasterGroundB19.py --root .
start WORKSPACE/generated/lpc/elizawy_master_ground_review_b19.html
py -3 tools/automation/validation/checks/assets/Test-ElizaWyMasterGroundB19.py
```

Expected status: `CANONICAL_COORDINATES_AND_SEASON_LAYOUT_VERIFIED_SEMANTIC_REVIEW_REQUIRED` with 416 canonical cells, 2,080 seasonal bindings, 381 unmapped master coordinates and zero blockers. The validator checks only the seven B15 sheets, not the full 64,365-file source again. Generated outputs reside under `WORKSPACE/generated/lpc/`.

## Critical acceptance boundary

`productionApproval=false`, `runtimeCutover=false`, and all semantic mappings, transition/topology rules, collisions, water depths, resizing modes and editor/client runtime bindings remain unapproved. Existing-world compatibility and V7 runtime must not be destroyed merely to clear this stage. Current provider policy remains ElizaWy-only *candidate* for new art; no cross-family fallback or missing-art proxy is allowed for eventual cutover.

B20 should complete source-region semantic coverage of remaining 381 master addresses in a single review pass, preferably using original source examples / license-backed compatible Tiled metadata only as evidence. Then certify periodic surfaces and size-variable assemblies (including concave corners where actually available), direction/neighbor contact combinations, and explicit season/ice gameplay exceptions. Do not build another per-season mapping or another competing validator stack. Only then publish shared editor/client bindings with visual and gameplay tests.
