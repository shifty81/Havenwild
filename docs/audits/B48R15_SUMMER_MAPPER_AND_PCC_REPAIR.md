# Havenwild B48R15 — cumulative Summer mapper and PCC intake repair

## Baseline and installation

User's attached 2026-09-19 03:04 failure bundle identifies B48R9 as the installed local baseline. The reported failed Full Quality Gate stopped at **root cleanliness**, before Rust build or tests: the download `Havenwild_CUMULATIVE_PCC_Patch_B48R7_to_B48R14_ElizaWyMapperAuthoring_20260919 (1).zip` was not recognized by the old patch discovery and remained an illegal ZIP in the repository root. Do not misdiagnose this as a mapper compile failure. The four existing deletions of `ForgePY*.cmd` in Git status are independent and deliberately not modified by this patch.

Do **not** apply B48R10, B48R11, B48R12 or B48R14 separately. Preserve/move the old `(1).zip` out of Havenwild root (e.g. Downloads), then place only the B48R15 ZIP in the root, without a browser `(1)` suffix. Launch the existing PCC and use its normal patch approval/Full Gate workflow. Do not extract manually. Once installed, patched PCC discovery recognizes both `Havenwild_IncrementalPatch_*.zip` and `Havenwild_CUMULATIVE_PCC_Patch_*.zip`; browser-suffixed cumulative duplicates with a valid manifest are moved, intact, to `artifacts/updates/held-duplicate-downloads/` and never executed. Unrecognized/malformed ZIPs remain blocking for review. The root cleanliness audit remains strict.

## In-place mapper development

Uses the original `apps/haven_atlas_mapper_lite` rather than inventing another generator:

- LEFT: catalog of available Summer and season-neutral original ElizaWy sheets, including original terrain, split-source strips, terrain objects, structures, objects, FX, and a provided character subset. Textures are loaded only when a source is activated. Original source files are not modified.
- Source list supports `Ctrl+F` / Find search, Reset, virtualized large-list drawing and per-sheet ON/OFF. Selecting another sheet retains earlier scene pieces. Removing a source used by pieces is blocked.
- RIGHT: editable scene canvas, inspector, real candidate per-cell heights 0..30 (including +1), water mark, placement layers, project save/load, original-pixel review PNG and ledger.
- Source addresses pull from B48R7 and the **641 Summer entries** from B48R9. They are pixel-match coordinates, not semantic cliff/water approval; mapped-sheet metadata is separate.
- All active sheets' per-source mapped records are exported separately. Exact SHA256 for packaged original source files is pinned in scene/review source metadata from the registry; external/unregistered files stay observed-only. Existing verifier rejects pinned-byte changes and pixel replay discrepancies.
- The string `Waterfall` is NOT mistaken for the autumn `Fall` season. Multi-season `Spring & Summer` and `Non-Winter` originals remain selectable; spring-only, autumn-only and winter/frozen art remain inactive.
- Both conflicting ORIGINAL `Terrain/Waterfall.png` versions are retained separately: primary original in `Terrain`, distinct four-season variant under `seasonal_split/Terrain`, with source hash/provenance. Both Terrain credits texts are preserved separately.

## Source scope

This PCC package contains 2,919 exact original Summer or season-neutral source/credit files extracted from the supplied Terrain, Structure, Objects, FX and four-season archives (including the provided 2,553-file character subset where seasonal names allow). Registered SHA256 values are evidence of supplied bytes, not semantic approval. **The full `Characters.zip` (~64,000 files) is NOT embedded** in this transport; a complete full-character intake and all individual tile role/assembly mapping are still work to do. Only sources present in or declared to the user's local project can appear in the left panel.

## Remaining work and tests

This iteration does NOT implement approved cliff-water recipes, seam topology certification, full collision, nav, animation, source-to-worldgen Asset Authority publication, runtime/editor elevation migration, native GUI tests or the +30 engine migration. The rejected B48R10 candidate image is historical evidence, never a certified result. B48R14 project and test groundwork is preserved, as are earlier source mappings. Source-only crosswalk evidence must not be interpreted as all Summer art already mapped.

Offline static, registry SHA, archived original pixel replay and ZIP integrity are tested separately. Run the **Windows Full Quality Gate**; if GREEN launch `tools\launch\HavenwildAtlasMapperLite.cmd`. Verify left index Summer, `Ctrl+F` for `Waterfall`, ON both distinct originals one at a time, select Summer cliffs and original FX, place mixed sources on right, paint +1 and +30, save/reopen and export review PNG. Compare review with original artist references. Any GUI/build failure must be repaired from its debug bundle before certification.
