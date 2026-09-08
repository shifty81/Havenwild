# Havenwild W53C — Estate Structural / Runtime Visual Repair

**Pass:** Pass167Z109W53C  
**Date:** 2026-08-15  
**Input:** user runtime screenshots from the isolated W53B Estate visual test.

## Runtime defects confirmed

1. The Estate authored JSON had no persisted `structuralLevels` layer, so the current 0/1/2 cliff system could not receive the intended Estate topology from authored source.
2. The Estate generator painted a raw one-cell `Cliff` border. This duplicated/undermined derived structural cliff presentation and visually read as one-high brown strips.
3. The ordinary cave source was being treated ambiguously as “1x3 mouth”. The exact source is a 1x3 envelope, but the usable cave aperture is **1 tile wide x 2 tiles tall**; the third row is the threshold/receiver row.
4. The cave PublishedWorldAsset could render separately from the structural cliff connector on authored exterior scenes, allowing the cave source to be double-submitted/misaligned.
5. Building interior navigation limited movement to room `walkableRects`. Door cells may lie on the footprint boundary, so after `inside=true` a player could be unable to cross back through the same valid open doorway.
6. The W53B 5x5 starter cottage still did not visually read as a correct house. It used a partial exact gable module while N/E/W wall-facing art remained unresolved. Runtime review therefore rejects that exterior composition.

## W53C corrections

- `worldgen_loader` accepts an optional authored `layers.structuralLevels` grid using only discrete Level 0/1/2 values (or null/auto for compatibility).
- The structural parser is split into `worldgen_loader_structural.rs` so the main loader remains below the 750-line architecture ceiling.
- The Estate generator now writes explicit Level-2 perimeter highlands and Level-0 interior/gate terrain.
- Raw `Cliff` terrain is no longer generated for the Estate border; visible cliff faces are derived from structural-level edges.
- The cave buttress/host is Level 2 and the walkable approach threshold immediately south is Level 0, producing a true two-level south-facing cliff drop.
- Cave aperture contract is **1x2**. The exact ElizaWy source remains the original **1x3** envelope because its third row is the threshold/receiver row.
- Cave interaction and scene transition occur on the Level-0 threshold tile `[78,9]`; the cave host remains `[78,8]`.
- The structural cliff renderer owns the cave visual whenever a cave object occupies a valid structural south-face host; ordinary PublishedWorldAsset object drawing does not double-render it.
- BuildingInstance Door/Archway cells are explicit navigation thresholds; door-state collision is still resolved separately, so closed doors remain blocking while open doors can be crossed from either side.
- The rejected Estate starter cottage instance is `deprecated` in the active BuildingInstance catalog. Its recipe/source remains preserved for future exact-exterior certification, but the isolated Estate runtime no longer displays the incorrect shell.
- The previous unused `RuntimeBuildingDrawPiece.instance_id` field is removed, clearing the warning observed in the successful W53A Windows build.

## Acceptance target

Run:

```text
2. Build all
53. Regenerate + validate Home Estate
54. Run integrated Estate visual test
```

The W53C visual test must show:

- no raw one-cell brown `Cliff` border;
- visibly multi-row Level-2 south-facing cliff drops where the Estate highland meets Level 0;
- ordinary cave opening exactly one tile wide with a two-tile-tall aperture;
- no duplicate cave-mouth sprite over the structural cliff;
- cave entry from the lower threshold tile;
- no rejected partial starter-cottage shell in the Estate;
- BuildingInstance acceptance buildings can be exited through their open doorway.
