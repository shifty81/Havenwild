# B24 — ElizaWy grass / earth / sand source transition diagnostics

**Installation:** This pass is delivered as a canonical PCC root-drop `Havenwild_IncrementalPatch_*.zip` with `PATCH_MANIFEST.json` and per-file SHA-256 and byte lengths. **Do not extract this ZIP manually.** Drop the intact ZIP into the Havenwild repository root, open `HavenwildTools.cmd`, allow PCC intake, then run Full Quality Gate. Only source files listed in the manifest are installed; no generated evidence is put in the repository root.

**Baseline:** B22 and B23 source patches are already extracted/installed by the project owner. This pass adds B24 only; no reapplication, replacement, or assumptions about the user's unprovided live Git worktree. The 2026-09-17 complete source rollup was used for PCC schema and file-layout verification, not assumed to be today's exact source revision.

## Findings against original ElizaWy five-season sheets

- Original grass-on-earth ring `(6,0,3,3)` and sand-on-earth ring `(9,0,3,3)` are complete 3x3 authored source regions. B24 verifies their 384 boundary samples and exact crop pixels for every season. The grass ring has a transparent center; the review fills it with **unchanged original seasonal grass cell `(1,1)`**. The sand ring already contains its original pale sand center `(10,1)` and is not modified.
- The exterior of each earth motif has **two original earth/snow colors**, not a pixel-uniform earth base. A 384/384 equality check against one color would incorrectly reject valid source artwork. This pass records exact source edge-color histograms; it deliberately does not invent a flat earth tile or extrapolate this 3x3 art into an approved arbitrary boundary system.
- The warm/orange sand motif `(9,5,3,3)` is predominantly bounded by pale sand, but **16 original darker edge-highlight samples** remain: north x=40–43 and 52–55, east x=95 at y=40–43 and 52–55, all local 3x3-pixel coordinates. All five season sheets share this signature. The pixels are in the original image, not output corruption. They are preserved; no pixel erasure or fake smoothing. This motif remains unapproved for the strict seamless 3x3 compositing rule.
- B23's corrected pale sand and B22's grass/pond scene are reauthenticated, not altered. Full generalized grass/earth/sand transitions, earth base tiling, arbitrary terrain shape topology and editor/client parity are still **not certified**.

## Review generator

Run from the installed Havenwild repository root, with read-only input ZIPs or extracted evidence directories:

```powershell
python tools/automation/assets/Build-ElizaWyGroundTransitionEvidenceB24.py --evidence "C:\path\to\lpc(5).zip" --b22 "C:\path\to\Havenwild_B22_ElizaWy_Generated_Visual_Evidence.zip" --b23 "C:\path\to\Havenwild_B23_ElizaWy_Sand_Correction_Visual_Evidence.zip" --terrain "C:\path\to\Terrain.zip" --out "WORKSPACE\generated\lpc\b24"
```

The explicit review command requires Python + Pillow; the small stdlib algorithm tests do **not** require Pillow or external source ZIPs. The generator verifies B21/B22 lineage and source hashes, recreates both old B22 images per season, recreates and pixel-compares all B23 corrected sand scenes and full B23 sheet, recreates B23 report metadata, validates original B24 source regions and edge signatures for five seasons, then emits **15 individual previews, one labeled five-season contact sheet, and a JSON evidence report**. It fails closed on altered inputs before writing new outputs. Original source assets stay read-only.

Stdlib unit tests:

```powershell
python -m unittest discover -s tools/automation/tests -p "test_elizawy_ground_transition_b24.py" -v
```

**Not a gameplay patch:** This installs optional evidence tools, a targeted test, and this audit document only. It does not touch PCC implementation, original art, terrain gameplay, editor/runtime shaders, scene materials, other content packs, or source approval flags. Generated images are review artifacts only, not a second root patch or source authority. Actual Windows PCC application, project-wide GREEN gate, and client PIE verification must take place on the local machine.
