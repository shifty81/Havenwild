# B23 — ElizaWy sand composition correction (non-promoting)

## Root cause verified

The B21R1 sand cell `(10, 6)` is **pixel-uniform**, but its summer color is the warm/orange **interior** of the authored 3×3 sand motif, not the pale surrounding sand. B22 incorrectly repeated that warm cell as the scene exterior and pasted the full sand motif `(9, 5, 3, 3)` onto it. In **all five seasons** its 384 perimeter samples disagreed with the chosen exterior, producing the obvious square.

The original source provides a uniform pale exterior at `(10, 1)`. The authored grass-on-sand ring `(6, 5, 3, 3)` has **384/384 matching outer-edge samples** against that pale cell in every season. Its center tile is fully transparent and is filled from the existing authentic grass base `(1, 1)` before compositing the original patch. This produces grass islands on continuous sand without editing source pixels, painting a seam, stretching, or generating substitute art. The grass-and-pond B22 scene is reproduced and shown **unchanged** next to sand.

The original orange sand motif is **NOT approved**: its perimeter disagreement falls from 384 pixels on the B21 warm base to 16 on the corrected pale base, but it still fails the zero-disagreement requirement for these strictly sealed example scenes. B23 intentionally omits it from the corrected preview rather than cosmetically covering its source pixels. The B21 source-coordinate evidence and B22 rejection remain immutable history. B23 proposes semantic roles; it does not silently rewrite B21's `ground.sand.base` binding or promote an asset.

## Run (repository root, after B22 patch is installed)

```powershell
python tools/automation/assets/Build-ElizaWySandCorrectionEvidenceB23.py --evidence "C:\path\to\lpc(5).zip" --b22 "C:\path\to\Havenwild_B22_ElizaWy_Generated_Visual_Evidence.zip" --terrain "C:\path\to\Terrain.zip" --out "WORKSPACE\generated\lpc\b23"
```

B23 reuses the existing B22 Python generator as a validation module and requires Python + Pillow *only* for this explicit optional review action. Inputs may be ZIP files or matching extracted directories. It verifies B21's B19/B20 lineage, the B22 report/B21 link, the exact original five source-sheet hashes, 15 original B21 base previews, ten original B21 3×3 assemblies, and reconstructs/compares all B22 grass and rejected sand previews before generating any new evidence. Output: five corrected sand scenes, one combined five-season review sheet, and an auditable JSON report. It does not alter PCC, runtime, renderer, game materials, source library, authoring metadata, or previous evidence.

## Review checklist / remaining gates

- Inspect `B23_all_seasons_sand_correction_review.png` at native pixels for five seasons. B22's grass and pond scenes on the left are intact; sand on the right uses the authentic pale exterior and authored grass-on-sand patch, with authentic grass centers.
- Check `elizawy_sand_correction_b23.json` for five matching seasonal hashes, 384/384 matched grass–sand patch perimeter samples, all opaque source pixels preserved, and intact grass center cells.
- Keep warm/orange motif `(9, 5, 3, 3)` unapproved until its 16 exceptional boundary pixels can be explained using original source topology. Do not crop the perimeter or silently remove its detail.
- Generalized grass↔sand↔earth transitions, arbitrary shore/pool sizing, actual gameplay material approval, editor/client PIE parity, source credits, and full project gate still require separate review. **These visual previews are not production or runtime certification.**

## Scope / handoff

Incremental patch adds this document and `tools/automation/assets/Build-ElizaWySandCorrectionEvidenceB23.py` only. No new root files or game/asset changes. It requires the separately delivered B22 incremental patch already installed. The separate B23 evidence ZIP is a review artifact, not a PCC root-drop patch.
