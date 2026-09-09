# PCC Universal Asset System V1

## Purpose

This is the first production-oriented slice of the project-agnostic Python asset
spine. Havenwild is the first adapter, not the owner of the core model.

The system intentionally separates:

1. source evidence,
2. structural detection,
3. semantic certification,
4. prefab composition,
5. runtime/editor consumption.

Pixel analysis may propose structure. It may not invent semantic roles or
runtime certification.

## Current capabilities

- Standard-library PNG decoding/encoding.
- Declared or inferred grid analysis.
- Havenwild 32x32 default adapter.
- Per-cell alpha occupancy, bounds and hashes.
- Exact-RGBA and alpha-mask duplicate detection.
- Cross-cell seam continuity analysis.
- Multi-cell assembly candidates from opaque seam connectivity.
- Conservative horizontal animation candidates.
- TSX Wang/Terrain metadata parsing.
- TSX tile properties, animation and collision parsing.
- TMX map/tileset/layer metadata parsing.
- Canonical asset catalog generation for a folder.
- Source-native prefab candidate extraction from detected assemblies.
- Semantic house-prefab recipe generation.
- Catalog validation.
- Deterministic self-test.

## Safety rules

- No pixel-derived candidate is runtime-certified automatically.
- Multi-cell detection does not imply semantic meaning.
- A cell that belongs to a larger candidate assembly remains a member; it is not
  silently promoted to an independent tile.
- Tiled collision is metadata evidence unless a project adapter explicitly
  promotes it.
- Generated house prefabs place semantic roles. Missing certified assets remain
  unresolved; the generator never draws substitute artwork.

## CLI

From repository root:

```bat
tools\automation\assets\Run-PccAssetTool.cmd self-test

tools\automation\assets\Run-PccAssetTool.cmd analyze-sheet ^
  assets\source\licensed\lpc_revised\Terrain\cliff_summer.png ^
  --output artifacts\asset-intake\cliff_summer.analysis.json

tools\automation\assets\Run-PccAssetTool.cmd scan ^
  assets\source\licensed\lpc_revised ^
  --output artifacts\asset-intake\lpc_revised.catalog.json

tools\automation\assets\Run-PccAssetTool.cmd inspect-tiled some.tsx

tools\automation\assets\Run-PccAssetTool.cmd extract-prefabs ^
  artifacts\asset-intake\lpc_revised.catalog.json ^
  --output artifacts\asset-intake\lpc_revised.prefabs.json

tools\automation\assets\Run-PccAssetTool.cmd generate-house ^
  --width 7 --height 9 ^
  --role-map content\assets\building_role_map.json ^
  --output artifacts\asset-intake\house-7x9.prefab.json
```

## Next normalization lane

The existing Havenwild asset scripts are compatibility authorities until their
outputs are compared against this package. Migration should happen capability by
capability:

- acquisition/source intake,
- catalog/index,
- provenance/license,
- exact-source validation,
- LPC/ElizaWy analysis,
- atlas derivation,
- promotion,
- structural certification,
- character/building/terrain/UI/audio tooling.

Old entry points become thin wrappers only after parity is demonstrated.


## Existing-tool normalization inventory

The subsystem can inventory the current automation tree without deleting or
rewriting anything:

```bat
tools\automation\assets\Run-PccAssetTool.cmd inventory-tools . ^
  --output artifacts\asset-intake\legacy-tool-inventory.json
```

This is the migration ledger for folding older asset acquisition, catalog,
provenance, validation, atlas, promotion and certification tools into the shared
Python spine.
