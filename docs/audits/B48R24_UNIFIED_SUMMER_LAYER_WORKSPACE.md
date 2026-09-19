# Havenwild B48R24 — unified Summer library and editable scene layers

Date: 2026-09-19. Candidate only. Based on user-reported B48R23 GREEN experimental commit `3dd1fa5ddbaf4f24482a94d62008317dee6f3582`.

## Scope implemented

- Existing `apps/haven_atlas_mapper_lite` only. No competing editor, source-art generation, game physics change, PCC replacement or ForgeGUI migration.
- All indexed non-character Summer/neutral sheets visible on launch. Group filters are non-destructive. Original PNGs are indexed by path and activated lazily, NOT combined into a giant texture or marked mapped by loading.
- Seven semantic authoring buckets in optional Layers [L] panel, mutually exclusive with Details [I]. Active placement bucket, hide/show, lock/unlock, move a selected sprite into another bucket. All operations are metadata-only and undoable. Editing/moving/deleting locked pieces is blocked; hidden pieces are not selectable on the live canvas.
- Legacy integer `AssemblyPiece.layer` and source references are never discarded. Old schema v0_1–v0_6 projects can load into the v0_7 project representation with default visible/unlocked states. The numeric layer maps to a named bucket using floor division by 10, clamped into 0..6; only a user-authorized move sets a new bucket value.
- Layer visibility, locks and selected destination persist in mapper projects and candidate handoffs. The Review PNG exporter still renders every piece (including hidden layers) for exact source replay; hide is solely an editor view operation, not permission to silently omit artwork from evidence.
- Draft/save/handoff stage pills are no longer green: only explicit approved source cells may show an approval check. No new visual approvals granted.

## Deliberately not implemented

`Generate Scene` from actual Havenwild runtime/worldgen is NOT available: existing crosswalk JSON reports pixel-address evidence, not certified topology roles; the current B48R7 watercourse reference is authoring-only; runtime still has legacy height and water rules. Reusing the old 24-cell correction tray as a procedural button would be a false implementation. Collision painting, mask sockets, full-feature grouping, true cave/waterfall recipe authoring, approved Summer demo and Forge/Cortex end-to-end integration remain separate bounded passes.

## Windows acceptance test

1. On clean, certified B48R23 checkout, drop only this cumulative ZIP in the Havenwild root, approve intake and run PCC Full Quality Gate; do not push unless GREEN.
2. Launch mapper via PCC, verify green build label B48R24 and library default ALL. Verify characters excluded, group switch does not disable sources; load two original Summer/neutral sheets.
3. Drag overlapping tiles from two sheets into identical scene grid coordinates, verify topmost draw/pick order and original sprites with alpha. Activate Layers [L], select ground and water layers and move selected tile. Toggle visibility; hidden tiles cannot be picked but survive toggling. Lock a layer and test drag, Delete, right-click, rotate, semantic assignment and relocation are refused. Undo/redo visibility, lock and tile move.
4. Save as mapper project, close/reopen; check source stack, every numeric piece layer, active bucket, visibility, locks, +1 terrain and water values. Export review PNG and source ledger; verify exact pixel replay and hidden layers not lost from evidence. Candidate handoff must include layer metadata and NOT claim approval.
5. Use Ctrl+F/Refresh after group selection. Ensure toolbar and layer overlay do not paint through underlying scene. Send screenshot/debug bundle if any behavior fails.

Static tools: `py -3 apps/haven_atlas_mapper_lite/tests/validate_b48r24_layers.py --repo .`. Previous mapper validators run as inherited regression guards. Rust and native Windows tests are not available in package assembly environment; no gate/GUI/runtime green claimed.
