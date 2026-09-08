# Pass 118 — Asset Intake Build Order

Date: 2026-07-15

## Build failure addressed

The Windows bash build reached `tools/automation/validation/checks/editor/Validate-AssetIntakeAtlasAuthoringV66.py` and failed with:

> generated user atlas entry count does not match approved recipes

That means the approved recipe catalog and generated user-import atlas were out of sync.

## Root cause

`tools/build/Build.sh all` regenerated the LPC terrain assets before validation, but it did not run `tools/automation/assets/Bake-AssetIntakeAtlasV66.py` before `tools/automation/validation/validate.py all`.

The generated atlas could therefore be stale even though the source catalog was current.

## Fix

- Added a shared `build_asset_intake` step in `tools/build/Build.sh`.
- `tools/build/Build.sh all` now runs asset-intake baking before pre-cargo validation, Rust checks, and full validation.
- `tools/build/Build.ps1 all` now runs the LPC runtime generation path and the asset-intake bake before full validation.
- Tightened `Validate-AssetIntakeAtlasAuthoringV66.py` so future build-order regressions are reported directly.

## Expected next build behavior

`./tools/build/Build.sh all` should now show:

1. LPC runtime asset generation
2. `START bake asset intake atlas`
3. terrain/source validators
4. Cargo checks/tests/build
5. `Havenwild validation: all`

If V66 fails after this change, it should indicate a real bad recipe, missing source image, duplicate target, or blocked license rather than a stale generated atlas.
