# Havenwild W53B Runtime Scene/Content Convergence Repair

Date: 2026-08-15
Baseline: Pass167Z109W53A

## Runtime failure observed on Windows

The consolidated W53A build compiled successfully, but live screenshots showed a stale outdoor substrate reused beneath multiple legacy scene identities. `Farmstead`, `Tavern Interior`, and other scene jumps changed labels/objects while preserving old grass/sand/water layouts. The current W53 Estate source contains no ocean/sand water field and does contain 18 trees, 4 boulders, and 10 shrubs/forage/flora entries, proving the live saved SceneMap bank was stale.

## Root cause

Normal startup restores `world.tworld` before packaged authored scene content. The generation-version migration is not a content-baseline version, so old legacy SceneMaps can remain indefinitely after their authored source changes. Current BuildingInstance/published-asset registries still load current content, producing the observed stale-terrain/new-object mixture.

## W53B repair

- Adds a dedicated runtime content-authority revision (`167Z109W53B`).
- Rebases only the six retained authored legacy gameplay scenes onto current source when an old saved legacy scene bank is first opened under W53B.
- Backs up the pre-rebase world and world-paint delta files.
- Filters stale paint deltas only for the rebased/retired legacy scenes; modern/generated-scene paint data is preserved.
- Retires `tavern_interior`, `cellar`, and `guest_floor` as separate SceneMaps. W47/W48 same-world BuildingInstance levels remain the ordinary Tavern interior authority.
- Relocates characters whose stored scene/coordinates point at rebased or retired legacy scenes to a current authored spawn.
- Prevents runtime reset/regenerate commands from manufacturing old starter terrain over current authored Estate/home-island scenes.
- Missing developer scene jumps fail closed instead of panicking.
- Adds `54. Run integrated Estate visual test`, using isolated world/character IDs and bypassing normal gameplay saves.
- Full textual runtime diagnostics are F3/dev-only; the isolated visual test shows only a small identity badge.
- Replaces the oversized 9x7 flat gray Estate cottage roof with the exact 5x5 brown LPC gable authored module.
- Regenerates the W43D placeable acceptance board against current status records and makes W43A's historical 29-item evidence validator forward-compatible with the current migration queue.

## Expected W53B visual-test signature

The clean Estate test must show:

- scene name `Estate` (internal compatibility ID remains `farmstead`);
- current authored grass/mountain/cliff/path substrate, not the old sand/ocean layout;
- 18 trees;
- 4 boulders;
- at least 10 shrubs/forage/flora entries;
- exact cave mouth;
- compact brown-gable starter cottage;
- no old standalone `Tavern Interior`, `Cellar`, or `Guest Floor` scene;
- no full-width terrain/cliff diagnostic text unless F3/dev mode is enabled.

## Validation

Direct W46A-W53B authority validators pass together. JSON/Python/Bash syntax sweeps pass in the packaging environment. Windows Cargo remains the final compile/runtime gate for W53B Rust changes.
