# Havenwild W56 Visual Truth Preflight

Target: `167Z109W56A`

This pass is intentionally diagnostic-only until the W55R10C source build/test gate is run on Windows.

## Added diagnostic authority

`haven_tools::analyze_world_visual_truth` computes per-scene:

- logical scene dimensions;
- exact spatial terrain signature;
- object signature and semantic object counts;
- natural-object population count;
- transition count;
- exact duplicate-terrain groups across different scene identities;
- exterior scenes with substantial grass but zero natural population.

This directly targets the earlier runtime symptoms where multiple world scenes looked like the same terrain composition with only object substitutions, and where trees/rocks/ground foliage were absent.

## Deliberately not changed yet

W56A does **not** change:

- terrain generation;
- scene composition algorithms;
- tree/rock placement rules;
- cliff rendering;
- cave rendering/navigation;
- building visuals;
- editor/runtime render paths.

Those are visual/runtime-sensitive changes and should begin only after the W55R10C cumulative source compiles/tests locally.

## First home build sequence

1. Root cleanliness audit.
2. Build all.
3. Run tests.
4. If W55 is green, run the W56 visual-truth diagnostic against the development/acceptance world.
5. Use its duplicate terrain groups and population gaps to drive W56B/C repairs instead of guessing from screenshots alone.
