# Havenwild B48R23 — Existing standalone mapper, targeted GUI recovery

Baseline: B48R22 user-reported Windows GREEN and pushed; independent GitHub verification of experimental commit 05f6e2ac715ca43d0180328d240220b95d272352.

## Important discovery

The submitted screenshot contains a left navigation rail and a `Save Demo` toolbar. Those are B48R20 markers: the B48R22 source has neither rail nor that toolbar label. A stale/alternate executable is a plausible cause; the screenshot alone does not prove the exact launcher or why the atlas index is empty. B48R23 adds a visible source build marker and resolves the real Havenwild root via HAVENWILD_ROOT, cwd and the executable's ancestors. If no original ElizaWy files are found, the UI shows the attempted directory instead of an empty list without explanation.

## Implemented in the existing apps/haven_atlas_mapper_lite

- Retains grouped lazy original-source indexing, but excludes the 2,553+ character animations from Summer scene browsing. Does NOT load hundreds of textures into the GPU during index refresh. Individual selection activates each sheet without dropping prior scene placements. 336 noncharacter original PNGs exist in this cumulative overlay; this is an asset-presence count, NOT semantic mapping/certification.
- Gives the source atlas most of the left pane vertically by default, with a `More library` / `Larger atlas` toggle. Equal-width left/right panes and optional details overlay remain.
- Makes `Erase selected` visible on the scene toolbar; Delete/Backspace and right-click on a piece share the same undoable removal function. Only selected artwork is deleted; heightmap and water remain intact. First-row default scene origin is below the 74px toolbar so the first tile is click-selectable.
- A visible `B48R23 source-library / erase repair` marker verifies which executable is launched. The source scan reports the actual root and missing original directory if it finds zero files.
- Source-only candidate workflow and protections remain. No automatic visual approval or runtime publication is added.

## Acceptance test on Windows (not performed by package author)

1. Keep prior B48R22 GREEN recovery checkpoint. Apply only this canonically named ZIP via PCC. Approve, verify application receipt, run Full Gate, and commit/push only if GREEN.
2. Launch via PCC `World, terrain & scene tools -> Atlas Mapper`. Confirm *B48R23* marker; if absent, determine which old executable was launched rather than continuing to test stale UI.
3. Check source library counts after startup; toggle ALL/Ground/Cliffs/Water/Furniture; `Larger atlas` should leave much more room for the source pixels. If it still reports zero, copy the displayed root path, check `assets/source/licensed/lpc_revised`, and attach PCC debug bundle; do not manually reclassify assets.
4. Select grass and a cliff or waterfall sheet; verify both remain active and placing tiles does not remove previous sources.
5. Select a scene tile and click `Erase selected`, Undo; select it and press Delete, Undo; right-click it and Undo. Verify layer selection/hit-testing and saved project reopen.
6. Confirm any saved master remains editable and +1 and +30 height/water data survive deletion, save/reopen and review export.

## Explicitly incomplete

- No certified editable Summer demo is currently bundled as a mapper project. A historical PNG or topology fixture cannot be passed off as an editable/certified scene.
- `Draft` operates on one selected atlas; `Stage missing cells` places candidate cells in a correction tray. Neither performs recipe-driven world generation or gameplay-authentic seed rerolls.
- Real Generate Scene requires shared heightmap/worldgen/ElizaWy resolver interfaces, saved scene provenance, source-exact multi-sheet assembly, collision/navigation parity, correction-to-rule promotion and reproducible seed tests. The ForgeGUI migration and Cortex end-to-end integration are separate, unverified host changes; B48R22 established only the read-only Havenwild descriptor.

## Test evidence level

B48R23 new regression, B48R20 grouped test, B48R21 workflow test and inherited mapper static/source tests passed against cumulative overlay. ZIP integrity and hashes are checked at package time. Cargo/Rust not available in authoring environment; Windows compilation, interactive GUI, PCC Full Gate and Forge/Cortex connections require local confirmation.
