# Havenwild Pass 90C — Expanded Scene Starter Generation + Editor Test Hotfix

## Failure addressed

Pass 90B passed workspace checking and strict Clippy, then failed six `haven_editor` tests.

Two transition-edit tests still looked for the Farmstead tavern transition at its legacy 48×32 coordinate (`23,12`). Pass 88 correctly migrates that transition into the centered 96×64 scene, so the test cursor no longer matched the transition.

The four validation tests exposed a real starter-generation defect: legacy scene generators scanned the expanded 96×64 dimensions before `center_legacy_template` added the legacy offset. Generated trees from the right and bottom portions were shifted beyond the map, producing anchors as large as 118×78 and invalid interaction/collision footprints.

## Corrections

- Legacy starter-template noise, trees, tall grass, roads, creeks, and streams now generate only inside `LEGACY_MAP_W × LEGACY_MAP_H` before centering.
- `TavernMap::new()` now follows the same centered-template contract as `starter_for_seed`.
- Transition erase/resize tests locate the stable `Tavern Door` transition and use its migrated runtime coordinates.
- Resize assertions are relative to the transition's original dimensions instead of hard-coding a legacy result.
- Added validator V95 to protect the legacy-generation boundary and scene-size-independent transition tests.

## Behavior preserved

- Runtime scene size remains 96×64.
- Existing 48×32 saves still center at offset +24,+16.
- Layered outdoor PCG still fills the complete expanded scene.
- Authored legacy structures, objects, zones, spawns, and transitions remain centered.
- No terrain-family or LPC atlas mapping changed.

## Windows verification

Run:

```bat
tools/build/Build.cmd all
```

The expected progression is:

1. `cargo check` passes.
2. strict Clippy passes.
3. all `haven_core` tests pass.
4. all 27 `haven_editor` tests pass.
5. validators V54–V95 pass.
6. release client and editor packages are produced.
