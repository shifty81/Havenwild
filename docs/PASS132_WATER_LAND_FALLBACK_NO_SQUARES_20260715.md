# Pass 132 - Water/Land Fallback No-Squares

This pass tightens the terrain-v7 missing-tuple fallback added in Pass 131.

Pass 131 stopped stale legacy atlas tiles from leaking through, but missing
water/land tuples could still choose a majority land material as the fallback.
That produced square grass, sand, or dirt chunks when painting near water.

The fallback now treats any missing tuple that mixes water with land as a shore
case:

- sand + water falls back to `WaterShallowsSand`;
- dirt/path/stone + water falls back to `WaterShallowsDirt`;
- grass + water falls back to generic `Water`;
- explicit authored shallow-water materials still win when present;
- mixed fallback entries remain stable across animation frames.

This does not replace the final authored tuple work. It prevents hard square
land blocks while the exact `terrain_v7_full` transition coverage continues to
grow.

Validated locally:

- `python -m py_compile tools/automation/validation/checks/terrain/Validate-LpcMappedTupleFallbackV131.py tools/automation/validation/validate.py`
- `python tools/automation/validation/checks/characters/Validate-LpcWaterAnimationAndShoreDepthV128.py`
- `python tools/automation/validation/checks/characters/Validate-LpcWaterAnimationOwnershipV129.py`
- `python tools/automation/validation/checks/characters/Validate-LpcSparseWaterAnimationV130.py`
- `python tools/automation/validation/checks/terrain/Validate-LpcMappedTupleFallbackV131.py`
- `bash -n tools/build/Build.sh`

`cargo` is not available in this scratch container, so Rust compile/test should
be verified by the normal Windows build after applying the overlay.
