# Havenwild W43B — Complete Placeable Visual Sweep

W43B covers all 26 gameplay `ObjectKind`s rather than only the W42 published-scene candidates.

- ordinary `Crate` now uses exact LPC `Crate.png` source rect `[0,32,32,32]` and a 1x1 visual/collision footprint;
- future crate piles/stacks must be explicit assemblies;
- known wrong substitutions fail closed: stairs/ladder, bench/ottoman, sign/standing-screen, well/water-cooler, log/lumber;
- door and fence remain explicit missing-art cases;
- greenhouse marker remains a development placeholder;
- `placeable_visual_sweep_v1.json` records a status/next action for every gameplay ObjectKind.

Validation: `Validate-PlaceableVisualSweepV1.py`.
