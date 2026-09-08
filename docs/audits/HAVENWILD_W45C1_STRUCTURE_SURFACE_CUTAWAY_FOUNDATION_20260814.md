# Havenwild W45C1 — Exact Structure Surface + Multi-Level Cutaway Foundation

## Scope

W45C1 advances the W45 Structure source queue without guessing roof grammar. It publishes exact floor/wall/cutaway/window candidates through the existing `PublishedWorldAssetRegistry` and locks the W46 building visibility model before BuildingRecipe implementation begins.

## Exact published candidate source set

Five additional pinned LPC Structure sheets now have reviewed exact component rectangles:

- `Structure/Floor/Wood Floor B.png`
- `Structure/Walls/Drywall.png`
- `Structure/Walls/Panels A.png`
- `Structure/Walls/CutawayOverlay.png`
- `Structure/Windows/Ornamental Windows B.png`

Combined with W45B, 10/98 Structure source sheets now carry reviewed exact regions.

W45C1 publishes ten candidate assets:

- two 32x32 herringbone wood floor cells;
- one 32x96 plain drywall face strip;
- two 32x64 decorative wall-panel overlays;
- four exact cutaway-cap cells;
- one tall ornamental window with `unlit`, `day`, and `lit` states.

All remain `candidate` until native-editor/client visual acceptance.

## Building visibility / levels lock

`content/buildings/building_level_visibility_contract_v1.json` fixes the W46 default architecture:

- one same-world `BuildingInstance` for ordinary exterior + interior;
- level `0` ground floor, positive upstairs, negative basement/cellar;
- stairs/ladders connect structural levels;
- roof/front-wall cutaway is presentation state computed per client camera;
- visibility changes never mutate shared world simulation;
- different multiplayer clients may simultaneously view/occupy different levels or exterior;
- separate scenes are reserved for genuinely streamed/instanced spaces, not ordinary rooms/floors/cellars.

`PublishedStructureDefinition` now carries optional `visibility_role`, `occlusion_group`, and `camera_local_occlusion` fields for this presentation contract.

## Roof / dedicated wall-border policy

W45C1 intentionally does not publish a guessed roof cell. All seven LPC roof source sheets remain source candidates until their topology is reviewed. `Build-StructureRoofTrimReviewV1.py` creates machine-local coordinate-labelled review boards under `WORKSPACE/generated/structure_review/w45c_roof_trim/` when the pinned LPC dependency is mounted. W45C2 will use that evidence to select exact roof and dedicated Wall Border grammar.

## Diagnostic fixture

`structure_surface_acceptance` contains the ten W45C1 candidates. The old SceneMap object parser still requires an `ObjectKind` carrier, so this diagnostic-only fixture uses compatibility carrier ids while preserving exact `assetId` resolution. W46 must replace this with native building structural layers rather than promoting the diagnostic carrier into production authority.

## Validation

- W45A progression-aware source inventory: PASS (10/98 reviewed)
- W45B exact structure components: PASS
- W45C1 exact structure surfaces/cutaway/building visibility contract: PASS
- deterministic compact-source cache fallback: PASS
- Bash `structure-surfaces` root build command: PASS
- Windows Rust compile: pending local W45C1 gate

## Next

W45C2: exact roof + dedicated Wall Border grammar from local coordinate-labelled source review. Then W45D: bridges, platforms, pillars and miscellaneous structural support. W46 follows with real multi-level `BuildingInstance` / `BuildingRecipe` authority.
