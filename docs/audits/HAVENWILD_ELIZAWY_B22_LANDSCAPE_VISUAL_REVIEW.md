# B22 — ElizaWy ground composition evidence (non-promoting)

## Scope

B21R1 is retained. This incremental pass adds a *read-only*, explicit-input generator at `tools/automation/assets/Build-ElizaWyGroundLandscapeEvidenceB22.py`. It uses **original** ElizaWy `Terrain.zip` sheets and existing B21 evidence, not the project's old mixed-source runtime terrain. It verifies the B21→B19/B20 digest chain, original ElizaWy season-sheet hashes, 15 plain base previews and ten source-exact authored 3×3 previews. The generator refuses altered or missing inputs.

## Run from repository root (PowerShell)

```powershell
python tools/automation/assets/Build-ElizaWyGroundLandscapeEvidenceB22.py --evidence "C:\path\to\lpc(5).zip" --terrain "C:\path\to\Terrain.zip" --out "WORKSPACE\generated\lpc\b22"
```

Requires Python and Pillow for this **optional reviewer** only; it is **not** installed by the script and is not silently added to the PCC full gate. It never changes source art, content asset authority, renderer, gameplay, generated world assets, or PCC state. Output is an evidence folder and an explicit B22 JSON report. Re-running to a previously used B22 output folder replaces only B22 evidence filenames.

## Review procedure

1. Open `B22_all_seasons_review.png`: grass area on the left uses a B21R1-authenticated flat grass source tile with exact original 3×3 tuft and grass-bank pond assemblies. Right side deliberately demonstrates a **rejected** sand-motif-on-sand composition, not a certified grass→sand junction. In summer all 384 sampled perimeter pixels disagree with the plain sand base, producing a visible square seam. This exact composition must not be promoted.
2. Examine each season at native pixels. Inspect pond boundary, grass tuft alpha underlay, sand boundary and palette continuity. Auto-computed boundary samples are diagnostics, **not** approval or a substitute for looking at source art.
3. Treat the sand sample as **rejected as composed**. Do **not** stitch sand straight onto grass; no exact source-approved cross-material transition layout has been certified yet.
4. Keep all 7×5 / nine-slice / stretched or procedural-width pool and shore experiments inactive. Only original, unmodified 3×3 assemblies are used in B22 scenes.
5. Hold promotion until authored transition grammar (grass↔sand, earth, shoreline and larger ponds), gameplay water behavior, source licensing/credits, and editor–client PIE visual parity have their own passing evidence. Generated preview validation is not production certification.

## Authority and packaging

This patch **adds two files only** under the existing `tools/automation/assets` and `docs/audits` folders; there are no root files, no replacement source assets, no hard-coded new renderer paths, and no implicit runtime cutover. The separately supplied B22 generated-evidence ZIP is for visual review only and should not be put into the patch inbox as source changes. Preserve upstream credit files and ElizaWy provenance when eventual production promotion is approved.
