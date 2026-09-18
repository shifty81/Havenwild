# B21 — one authoritative ground layout: pixel-tested composition

## Purpose and scope

This pass consumes, rather than replaces, B19's one canonical 16×26 source layout
and B20's complete 47-region ownership map. It reads only pinned ElizaWy originals
at `assets/source/licensed/lpc_revised/Terrain/terrain_{season}.png` and hashes
those exact bytes against B20. It uses B19's existing pure-stdlib PNG decoder.
No generated assets are written back to the protected source library.

Unlike the earlier visual-only candidate catalog, this pass produces **actual
source-pixel previews** and measures literal opposite-edge pixel equality of
three narrowly selected fully opaque base visual cells in every source season:

| Visual surface | Canonical cell | Rect in original | Verified property |
| --- | --- | --- | --- |
| Grass base appearance | (4,1) | [128,32,32,32] | 0 horizontally and vertically mismatched edge pixels; all 5 seasons |
| Sand base appearance | (4,6) | [128,192,32,32] | same |
| Open water *appearance* | (12,17) | [384,544,32,32] | same; source region is the right-side shoreline components |

This validates **literal self-repeat edges and full opacity only**. It does not
prove a pleasing large-scale texture or that the cell is the author's intended
universal fill. No water depth, swimming, frozen-state policy, animation,
collision, placement rules, or material semantics are approved here. In
particular the B16 decorative-ripple/dark-gradient samples remain unpromoted.
Earth samples are excluded because their opposite edge pixels do not all match.

## Assembly diagnostics, not broken assumptions encoded as rules

The source-native grass tuft `(0,0,3,3)` and grass-banked pool `(0,10,3,3)`
produce side-by-side original 3×3 and provisional 7×5 nine-slice preview PNGs
for **all five seasons**. Original 3×3 internal contacts remain intact. The
preview repeats center and straight-edge cells without scaling artwork. It
measures self-repeat contact differences introduced by this expansion.

The initial full-source summer check recorded 34 repeated contacts per
expanded assembly. Grass yielded 44 horizontal and 14 vertical differing
edge pixels; the pool yielded 56 horizontal and 22 vertical differences.
This demonstrates why the original-looking 7×5 preview is **not** sufficient
to certify seamless arbitrary expansion. Variants, proper water/grass
composition, concave corners, complex shapes and compatible underlays remain
separate work. Do not auto-promote a generic nine-slice terrain rule.

## Deliverables

- Authoritative additive B21 recipe:
  `content/worldgen/elizawy_ground_composition_b21.json`.
- Builder:
  `tools/automation/assets/Build-ElizaWyGroundCompositionB21.py`.
- Outputs, generated locally and not committed:
  `WORKSPACE/generated/lpc/elizawy_ground_composition_b21.json`,
  `elizawy_ground_composition_review_b21.html`, and 35 preview PNGs (five
  per season: three exact 8×5 repeat views plus original and expanded views
  of each of the two assemblies).
- Unit tests:
  `tools/automation/validation/checks/assets/Test-ElizaWyGroundCompositionB21.py`.

From the Havenwild **repository root**:

```powershell
py -3 tools/automation/assets/Build-ElizaWyGroundCompositionB21.py --root .
if ($LASTEXITCODE -ne 0) { throw "B21 composition blocked" }
Start-Process (Resolve-Path 'WORKSPACE/generated/lpc/elizawy_ground_composition_review_b21.html').Path
```

Expected result: `SOURCE_PIXEL_REPEATS_VERIFIED_ASSEMBLY_RESIZE_REVIEW_REQUIRED`.
Inspect the preview visually: literal edge continuity is not a substitute for
variety and natural visual composition.

## Integration boundaries and next step

B21 is an additive authoring **prototype**, not an editor tool or production
renderer change. B19/B20 remain the sole coordinate and region data owners;
B21 references their immutable generated outputs and checks source hashes.
B16–B18 remain audit evidence, not independent asset authorities. No PCC,
branch, saves, worldgen, renderer, editor, runtime or legacy material fallback
is modified. `productionApproval`, `runtimeCutover`, water/gameplay and
resize approvals are explicitly false.

B22 must use these source-native recipes in a single existing shared terrain
adapter, expose them only in the editor's review/experimental mode, and draw
identical previews in the client. It must not bypass the existing world
semantic rules, silently edit worlds, invent source cells, or add another
parallel terrain resolver. Certify natural terrain composition in actual
editor/client screenshots before expanding further. For the two 3×3 shapes,
keep default placement at authored size until repeat seams and more complex
region geometry are properly addressed.
