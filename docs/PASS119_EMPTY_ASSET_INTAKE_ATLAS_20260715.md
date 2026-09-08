# Pass 119 — Empty Asset Intake Atlas

Date: 2026-07-15

## Build failure addressed

After Pass118 correctly ran asset-intake baking before full validation, the build failed with:

> Asset intake bake failed: catalog has no approved recipes

## Root cause

The asset-intake bake script treated zero approved import recipes as a fatal error. That is too strict for the current project state. A catalog may contain no approved project imports while the base game still builds from bundled/generated Havenwild and LPC assets.

## Fix

- `Bake-AssetIntakeAtlasV66.py` now emits a deterministic empty user-import atlas when no recipes are approved.
- Empty output is a 1x1 transparent PNG plus a manifest with `entries: []`.
- License acceptance and promotion license checks now apply only to recipes with `promotionState: "approved"`.
- `Validate-AssetIntakeAtlasAuthoringV66.py` no longer requires the cave-entrance proof binding when there are zero approved recipes.

## Expected result

With no approved intake recipes, `tools/build/Build.sh all` should continue past:

```text
START bake asset intake atlas
Asset intake baked: <recipe count> recipes, 0 approved
OK bake asset intake atlas
```

If a recipe is later approved, the bake/validation gates still enforce unique targets, valid sources, accepted licenses, and deterministic generated atlas output.
