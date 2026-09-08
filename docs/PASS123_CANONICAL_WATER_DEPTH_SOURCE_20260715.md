# Pass 123 - Canonical Water Depth Source

Date: 2026-07-15

This pass fixes the same source-family problem that appeared in sand/wet-sand,
but for shallow/deep water.

## Problem

`ShallowWater` was mapped to LPC `Water_Shallows_Sand`, while `DeepWater` was
mapped to `Water_Deep`. The terrain-v7 generated map does not provide a complete
`Water_Shallows_Sand <-> Water_Deep` transition family, so shallow/deep borders
could fall through to older terrain rendering and show legacy-looking square
patches.

## Decision

Gameplay `ShallowWater` and `OceanShallow` now render through canonical
terrain-v7 `Water`.

`Water_Shallows_Sand` remains available, but only as a generated shore/foam/coast
visual material. It is not the gameplay shallow-depth material.

## Locked behavior

- `shallow_water -> Water`
- `ocean_shallow -> Water`
- `deep_water -> Water_Deep`
- `shore_foam -> Water_Shallows_Sand`

The validator now requires full `Water <-> Water_Deep` mapped coverage, which is
present in terrain-v7 with 14 authored two-material shapes.

## Validation

Focused checks passed locally:

- `Build-LpcMappedTerrainV7.py`
- `Validate-LpcMappedTerrainReplacementV122.py`
- `Validate-TerrainMaterialRegistryV126.py`
- `Validate-ShoreWaterNormalizationV127.py`
- `Validate-LpcPaintTopologyStabilityV114.py`
- `Validate-LpcTerrainDetailEditorWindowV123.py`
- `Validate-LpcMappedTerrainRuntimePerformanceV124.py`
- `bash -n tools/build/Build.sh`
