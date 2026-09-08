# Pass 131 - Mapped Tuple Fallback Ownership

This pass prevents stale terrain artifacts from appearing when terrain-v7 does
not yet have an exact authored corner tuple for a complex water/shore shape.

Before this pass, missing mapped tuples could fall through to the older terrain
atlas path. That created square sand, shallow-water, or legacy-water chunks over
the newer terrain-v7 coastline.

The mapped terrain manifest now:

- tries the exact terrain-v7 corner tuple first;
- falls back to a terrain-v7 pure material fill when the tuple is missing;
- marks that fallback as mixed so terrain-v7 still owns the affected cell;
- keeps fallback mixed water/shore tuples stable across water animation frames;
- suppresses legacy transition overlays for these known mapped materials.

This is a safety net, not the final authored art pass. Missing tuples should
still be added to `terrain_v7_full` over time, but they no longer punch through
as stale square artifacts while that coverage grows.

Validated locally:

- `python -m py_compile tools/automation/validation/checks/terrain/Validate-LpcMappedTupleFallbackV131.py tools/automation/validation/validate.py`
- `python tools/automation/validation/checks/characters/Validate-LpcWaterAnimationAndShoreDepthV128.py`
- `python tools/automation/validation/checks/characters/Validate-LpcWaterAnimationOwnershipV129.py`
- `python tools/automation/validation/checks/characters/Validate-LpcSparseWaterAnimationV130.py`
- `python tools/automation/validation/checks/terrain/Validate-LpcMappedTupleFallbackV131.py`
- `bash -n tools/build/Build.sh`

`cargo` is not available in this scratch container, so Rust compile/test should
be verified by the normal Windows build after applying the overlay.
