# Havenwild Pass 91D — Transition Rule Owner-Side Test Hotfix

Date: 2026-07-12

## Build failure resolved

The Pass 91C build reached the final `haven_world` test group and failed only in:

`autotile::transition_rule_draft::tests::pair_specific_atlas_group_is_not_auto_fixed_to_material_default`

The test constructed the ordered pair backwards:

- center: `sand`
- neighbor: `grass`
- atlas group: `grass_over_sand`

The Pass 91 owner-side contract defines `grass_over_sand` as:

- center/owner: `grass`
- neighbor: `sand`

The live transition manifest already uses that ordering. Because the test used the reverse pair, the draft auto-fix correctly considered `grass_over_sand` inconsistent and reported one fix candidate.

## Change

The test now constructs `center = grass` and `neighbor = sand` while retaining `material = grass_fringe`. This continues to verify the intended behavior: an ordered-pair-specific atlas group overrides the material-only default and is not auto-fixed.

## Runtime impact

None. This pass changes test data only. It does not change terrain resolution, shoreline generation, atlas baking, rendering, camera behavior, input, saves, or LPC dependency acquisition.

## Verification

Run:

```bat
tools/build/Build.cmd all
```

Expected progression:

- pinned LPC dependency validation: pass
- cargo fmt/check/clippy: pass
- workspace tests: continue beyond the previously failing `haven_world` test
- remaining validators and release builds: run normally
