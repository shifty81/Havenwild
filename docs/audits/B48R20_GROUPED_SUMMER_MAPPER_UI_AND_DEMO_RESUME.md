# Havenwild B48R20 — Grouped Summer mapper UI and honest demo-resume boundary

Baseline: user-reported B48R19 GREEN, committed and pushed experimental lane. This is a cumulative overwrite-style PCC root-drop patch B48R7..B48R20, **not a complete source rollup**. It keeps B48R10's visually rejected assembly out of the authoring baseline.

## Modified existing standalone application

- Added ten genuine Summer library group filters plus ALL: Ground, Water, Cliffs, Plants, Buildings, Structures, Furniture, Characters, Items and FX/UI. Filtering preserves previously activated scene sources and placements. Search works within the selected group.
- Files whose names indicate chairs/tables/furniture are classified as object/furniture before generic path-name classification can misassign them to character. Waterfall sheets remain water/terrain instead of being interpreted as autumn/Fall.
- Replaced nine cramped category tabs at the application top with two rows of left-library group buttons. Removed deceptive inactive "Collision", "Traversal", "Semantics", and "Publish" tabs. Shortened viewport help and reduced inspector duplication/overlap. Sheet rows display containing folder, actual mapped percentage and exact source-address count, not only repeated basenames.
- Reworked source stack scrolling and click hit-testing for the new group header; selecting filters cannot be mistaken for activating a sheet or painting the canvas.
- Renamed current actions accurately: correction draft, learn saved corrections, **stage missing cells**, audit. The GUI explicitly states recipe-driven re-roll is NOT implemented; B48R17 reassemble only adds up to 24 unresolved source cells to a correction tray.
- Added top bar `Save Demo`: saves the user's actual current editable Summer scene to `artifacts/asset-intake/atlas-mapper/projects/elizawy_summer_master.mapper.json`. On startup with no CLI project argument, the mapper loads exactly this file if present. Save/auto-reopen does NOT grant mapping or runtime approval.
- Preserved existing height editing range 0..30, scene source provenance, undo/redo, review PNG/handoff, original read-only source assets and the PCC controls.

## Important missing baseline

No complete editable, visually approved Summer showcase mapper-project document was supplied in B48R19's cumulative package. Its B48R7 watercourse fixture describes topology but has no actual tile placements. The B48R10 assembled watercourse was visually rejected. Therefore an actual Summer demo is **not silently synthesized or marked approved** by this UX patch. You can open a genuine saved project or compose/review a source-exact starter with existing mappings and mark it using `Save Demo`; the editor will resume that project automatically from then on. Building the artist-reference-aligned editable demo from approved tile recipes is a separate outstanding authoring pass.

## Why Chair, Dining E.png is not mapped by scattering row 1

It is furniture/object artwork. A single 32px grid is a pixel-address unit, not the object definition. The source may contain multi-cell views and alternate colors/poses; no unverified row or column is silently called north/south/animation. Future furniture authoring must allow selecting a rectangular or disjoint group of source cells, defining logical object, direction/appearance, pivot, footprint, render sorting, collision and alternative variants. The current single-cell canvas is only for inspection/candidate placement.

## Required next stage before the user-requested generator can be called implemented

A shared Summer demo recipe package must encode exact ElizaWy source cells and roles for land, water, cliff boundaries, entrances/ends/corners, climbing connectors, multi-height steps 0..30, seasonal isolation, and waterfall lip/body/outlet; provide adjacency sockets and collision/nav semantics; then resolve the same seeded scene topology repeatedly while retaining protected manual overrides. Correcting one instance should prompt whether it edits that instance only or a shared recipe. Coverage must report actual source roles, exercised adjacency classes and verified runtime implementations separately; infinite decorative combinations must not be confused with finite topology-equivalence coverage. No green sheet-wide checkbox without every required source-cell mapping plus contextual validation and explicit visual approval.

## Checks run in this environment

- New grouped Summer static guard: PASS (13 checks).
- Previous B48R13, B48R14, B48R15, B48R16 and B48R17 standalone validators: PASS.
- B48R15 full original source registry SHA256 replay: 2,919 originals checked.
- ZIP CRC, per-file SHA-256/size and predecessor-byte preservation: see generated package summary.

**Not run:** Rust compilation, Windows PCC Full Quality Gate, screenshot/manual GUI verification, complete Summer asset-role certification, valid topology reroll, editor/client/worldgen runtime parity. Do not infer approval from these checks.

Windows GUI acceptance: apply only B48R20 on B48R19, run gate, open mapper; switch left filters, confirm `Chair, Dining E.png` under Furniture, save an editable multi-sheet draft with `Save Demo`, reopen and verify identical contents. `Stage missing cells` must not replace any corrected pieces. Submit screenshot/debug bundle if GUI or gate fails.
