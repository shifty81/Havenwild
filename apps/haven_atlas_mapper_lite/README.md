# Havenwild ElizaWy Mapping Workspace — cumulative test candidate (B48R14)

This is the **existing** `haven_atlas_mapper_lite` application, extended in place. It is
not a second atlas tool. Source PNGs are immutable. The recovered waterfall-transition
mapping and B48R7–B48R12 audits are preserved as input/evidence rather than gameplay approval.

## What's implemented in this checkpoint

- v0_6 project / v0_7 *candidate* handoff schema. v0_1–v0_5 projects deserialize and their old
  single-atlas pieces acquire that source's ID; new pieces remember the active source. The
  load/switch sheet operations no longer clear the scene, and the canvas draws each piece from
  the source atlas named by its ID. Save/load stores all loaded sheet references and placements.
- The canvas now has explicit **Select**, **Height** and **Water** authoring tools. Height paint writes real local elevation cells `0..30` directly on the canvas (`1/2/3` switch tools; `-`/`+` choose the active height). `PageUp`/`PageDown` and `Ctrl+W` remain available on selected pieces. `+1` is accepted rather than promoted.
  **This edits the mapper's candidate scene data only.** The old core/runtime 0..4 / level-1
  normalization has not been migrated and cannot currently consume the new range.
- Saved scenes can produce a source-crop PNG and its placement/height ledger through **Review
  PNG** in the top bar or `Ctrl+Shift+P`. Missing image sources, invalid crop bounds and heights
  outside 0..30 fail closed. The PNG is **UNREVIEWED**, not a playable scene.
- The independent, mapper-owned `tools/verify_review.py` uses referenced source bytes + observed SHA-256 and
  replays the tile placement into the PNG with Pillow, writing a source-proof receipt. Sources
  lacking a pinned expected hash are marked as observed-only, not proven immutable originals. No
  source-integrity, visual, topology, collision or runtime approval is inferred by export.
- Project opening preflights missing source references, invalid height cells and unsaved edits
  before destroying an existing editing session.
- Source mapped-sheet output filenames use deterministic path disambiguation rather than only
  basenames. Mapping a second sheet no longer writes its tiles into the active first sheet's
  metadata. Export no longer marks a sheet "validated" without validation.

## Windows manual smoke test (required before calling the mapper GREEN)

1. Run the PCC full gate first, **after verifying that the mapper source at this checkpoint
   is compatible with any local uncommitted changes**. No Windows build is claimed here.
2. Run `tools\launch\HavenwildAtlasMapperLite.cmd` from the Havenwild repo.
3. Load an original ElizaWy PNG using Load PNG, drag a source tile into the canvas.
   Load a **different original ElizaWy PNG** and drag a tile beside it. Both must stay visible.
4. Switch to **Height** (`2`), set `+1`, and paint several cells directly on the scene. Paint a `+30` cell and confirm the value clamps at 30. Switch to **Water** (`3`) and toggle water over both +1 and +30 cells. Switch back to **Select** (`1`). Save Project (`Ctrl+S`), reopen (`Ctrl+Shift+O`), and verify source tiles, elevation, water and layers remain identical.
5. Choose Review PNG. Run:

   ```powershell
   py -3 apps\haven_atlas_mapper_lite\tools\verify_review.py --ledger "YOUR.review.json" --png "YOUR.png" --repo "."
   ```

   Pillow is required for this independent verification utility (`py -3 -m pip install Pillow`),
   but is **not** required by the native Rust image exporter. Do not install packages without
   reviewing your PC environment first.
6. Export candidate handoff; confirm its `certification_stage` is
   `candidate_export_not_validated`, and the sheet did not become runtime certified.
7. Check mapping for a same-named sheet in a second root creates a distinct mapped-sheet file.

Static source/convergence guard (not a native Rust compile):

```powershell
py -3 apps\haven_atlas_mapper_lite\tests\validate_convergence.py --repo "."
```

The offline Python smoke fixture:

```powershell
py -3 apps\haven_atlas_mapper_lite\tests\smoke_review.py --terrain-zip "PATH_TO_Terrain.zip" --reference-zip "PATH_TO_4-season_terrain.zip" --out "TEMP_TEST_DIRECTORY"
```

## Explicit incomplete work — do not claim completion

- The real Rust binary has **not been built or launched** in this Linux tool environment:
  `cargo`/`rustc` are unavailable. The Rust unit tests in `src/review.rs` are written but unrun.
- Per-cell height/water painting is implemented in this candidate. Undo/redo, brush rectangles/fill, source checksum persistence in native projects, multi-tile recipe modules, and the complete collision/animation/connector inspector remain to be implemented before production certification.
- B48R11's ten cliff-water contact roles remain unapproved; no recovered art is silently
  placed as a gameplay recipe. The generated smoke PNG is a source-pixel checkerboard, **not**
  the approved summer pond scene.
- Shared recipe compilation, Asset Authority intake, worldgen, editor/client parity, +30
  structural runtime migration and PCC Windows gate all remain blocking for production.

The sequence is M1/M2 foundation -> M3 geometry/recipe authoring -> M4 visual certification
-> M5 game/editor parity -> M6 full ElizaWy coverage. Carry this candidate cumulative patch
forward; do not start parallel generators and never reintroduce the old minimum-2 cliff rule.


Additional B48R14 static authoring guard:

```powershell
py -3 apps\haven_atlas_mapper_lite\tests\validate_authoring.py --repo "."
```

## B48R15 Summer source library and PCC repair (cumulative with B48R14)

The left library now indexes available original Summer/neutral source files, supports explicit
ON/OFF activation and `Ctrl+F` search, and virtualizes large lists. The right canvas and
inspector are the editing workspace; source placements and candidate heights are retained
while switching sheets. Previous B48R7 and B48R9 *pixel-address* evidence is displayed as
source-coordinate matches, not automatically approved terrain roles. The original supplied
source bytes are in a SHA256 registry. Both different waterfall-sheet versions are retained
with distinct paths; nonseasonal Waterfall is not filtered as the season Fall.

Included source assets are terrain, split terrain, terrain objects, structures, objects, FX and
the four-season archive's character subset. The FULL separate 63,991-file Characters.zip is
not included, nor are all original asset roles exhaustively mapped. Certification and live
worldgen/editor/client use remain separate. See `docs/audits/B48R15_SUMMER_MAPPER_AND_PCC_REPAIR.md`.

Run `py -3 apps\haven_atlas_mapper_lite\tests\validate_summer_lane.py --repo .` as an offline
source/transport guard. This is NOT a Rust compile or Windows PCC GREEN claim.

## B48R16 — standalone editing repair (cumulative B48R7 onward)

**This is the existing standalone application, not the final complete/approved mapper.**

- Repaired the actual PCC restart source `tools/control/PccRestartTicket.ps1`:
  reserved PowerShell `$Host` is no longer assigned. This fix is included in the
  cumulative source transport; no separate emergency repair script is required
  *after this package is safely applied*. A checkout stuck in a failed PCC
  replacement restart may still need the previously supplied one-time repair
  script before it can intake this ZIP. First inspect patch/archive state to
  avoid reapplying an already installed transport.
- Added 64-step scene undo/redo (`Ctrl+Z`, `Ctrl+Y`, `Ctrl+Shift+Z`, toolbar).
  Captures pieces, transforms, labels, IDs and height/water cells. One continuous
  height-paint gesture makes one checkpoint. Undo is conservatively marked dirty;
  save again before exporting evidence. Unloading a sheet clears history so
  undo cannot resurrect references to a deactivated source. Clear scene keeps
  source sheets available to support Undo.
- Fixed pointer interaction zones: canvas top controls/bottom help overlay
  cannot accidentally paint/move tiles, dragging from the source chooser does
  not paint the heightmap, and scene header/toolbar now render over the tiles.
- Added non-destructive load preflight: source identity uniqueness, image
  decodability, piece IDs/source references/crop bounds and duplicate height
  cells are checked before the current scene is cleared. Genuine levels 0..30,
  including +1 coastal cliffs and one-tile pond recesses, are preserved.
- Added **Audit** (`Ctrl+Shift+A`, save project first): writes a
  `.scene-audit.json` next to the saved project, listing structurally invalid
  records and elevation/water boundaries needing source-exact recipe review.
  The audit explicitly **does not approve** cliff geometry, waterfront seams,
  traversal, collision, gameplay or runtime asset publication.

Run `py -3 apps\haven_atlas_mapper_lite\tests\validate_standalone_b48r16.py --repo .`
for offline guard assertions. In PCC use Full Quality Gate, then launch
`tools\launch\HavenwildAtlasMapperLite.cmd`, edit two activated originals,
undo/redo placements and a +1/+30 brush stroke, save/reopen, press Audit,
export PNG and run the independent `verify_review.py`. The Rust compiler and
Windows GUI were unavailable in the packaging environment: do not label this
binary/GUI certified until these operations pass on Windows.

## B48R17 — iterative ElizaWy Summer mapping (candidate)

`Ctrl+M` / **Reassemble saved scene + missing** keeps the previously corrected and
saved scene intact and stages up to 24 missing *nontransparent* source cells per
pass in a separate right-hand correction tray. No guessed waterfall/cliff pixels
are auto-placed into the playable terrain. Resolve the tray by positioning and
assigning accurate roles, save, run Audit, export Review PNG and Handoff. Candidate
handoff contains an `iteration_coverage` report and `generation_passes` count.
Draft cells have amber `?`, learned candidates blue `L`, and only separately
approved exact cell mappings may have a green check. Full-sheet green requires
all nontransparent cells approved and an appropriately validated lifecycle.

For a single uploadable mapping iteration ZIP (source originals are referenced,
not copied into the ZIP):

```powershell
py -3 apps\haven_atlas_mapper_lite\tools\package_iteration.py --project "YOUR_MAPPER_PROJECT.json" --png "YOUR_SOURCE_REVIEW.png" --handoff "YOUR_handoff.json" --audit "YOUR.scene-audit.json" --out "YOUR_iteration.zip"
```

The source-exact independent pixel replay still uses `tools/verify_review.py`;
the ZIP packager verifies matched snapshots and evidence hashes, not approval.
B48R17 fixes future PCC archived-ZIP timestamp evidence in
`tools/control/PccPatchLedger.ps1`, but an already FAILED historical ledger must
be reconciled separately by the fail-closed, archive/SHA-verified recovery helper
before Full Quality Gate can proceed. See `docs/audits/B48R17_ELIZAWY_SUMMER_ITERATION_AND_LEDGER_REPAIR.md`.

**Not yet complete:** genuine source-exact topology assembly, full summer
semantic certification, in-GUI one-click ZIP packaging, native compilation,
Windows GUI/PCC tests, and editor/client/worldgen parity. Do not mark GREEN.
