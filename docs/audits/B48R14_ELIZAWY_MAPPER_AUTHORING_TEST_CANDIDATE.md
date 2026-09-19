# B48R14 — ElizaWy mapper cumulative authoring test candidate

This checkpoint rolls B48R7–B48R13 forward and keeps the existing `apps/haven_atlas_mapper_lite`
application as the single mapping/certification workbench. It is intended to be **testable on the
user's Windows Havenwild checkout**, but no Windows GREEN build is claimed here.

## Added in B48R14

- Direct canvas height-paint mode with genuine elevation `0..30`; +1 is first-class and is not
  promoted/collapsed.
- Direct water-cell paint/toggle mode tied to the same candidate heightmap.
- Visible height/water overlay on the scene canvas so the structural map and source artwork can be
  reviewed together.
- Explicit Select / Height / Water tool controls and keyboard shortcuts.
- Static authoring gate checking multi-source scenes, height/water authoring, source review,
  candidate-only handoff and ElizaWy cliff connector role vocabulary.

## Existing behavior retained

- Multiple original ElizaWy sheets may be loaded into one scene without clearing earlier pieces.
- Each placement remembers its exact source sheet and crop.
- Project save/load stores the source stack, placements and heightmap.
- Review PNG uses source crops only and writes a placement/height ledger.
- Handoff remains candidate-only; export is not certification or runtime publication.
- Cliff connector candidates include climbable vines, cliff handholds/indentations, ladders and
  walkable cliff terminations.

## Production blockers after the mapper GUI itself is smoke-tested

The mapper is not the game runtime. Shared recipe compilation / Asset Authority publication,
complete cliff-water topology approval, collision/navigation recipes, animation timing, +30 runtime
migration, editor/client parity and worldgen consumption remain separate downstream gates.

The immediate Windows acceptance gate is: PCC full quality gate, launch mapper, load two original
ElizaWy sheets, place from both, paint +1/+30 and water, save/reopen, export review PNG, verify it with
the independent replay tool, and export a candidate handoff without changing certification state.
