# Worldgen Pipeline Zip Audit - 2026-05-25

## Summary

Two new project-owned worldgen pipeline archives were added at the repository root and audited:

1. `havenwild_worldgen_compositor_v005.zip`
2. `havenwild_macro_worldgen_v007.zip`

## Audit result

These are **project-owned source/design pipeline packs**, not direct runtime overlays for the current Rust game/editor build.

They were staged under:

```text
assets/raw/worldgen-pipeline/
```

and indexed by:

```text
content/packs/worldgen_source_pipeline.json
```

## Pack roles

| Pack | Role | Recommendation |
|---|---|---|
| v005 compositor | semantic terrain compositor inputs and rules | keep as the leading source/design baseline for future runtime compositor work |
| v007 macro worldgen | continent/island layout, climate, hydrology, biome, and shore-profile semantic maps | keep as upstream world-layout reference for future macro-world generation/editor preview work |

## Key conclusions

- v005 is meaningful source material for terrain composition, but it is not wired into the live renderer/editor/runtime.
- v007 adds large-scale semantic world planning that sits above the current home-island runtime pack flow.
- Both packs are useful for future generator/compositor development, but neither should replace the current live worldgen pack chain directly.

## Current implementation status

- Both packs are available as staged source archives plus extracted review copies.
- Their schemas, previews, pseudocode, and specs are preserved for future implementation work.
- They are **not** runtime-bound in the current Rust workspace.

## Critical gaps moving forward

- The repo still lacks a real semantic terrain compositor that can consume v005-style mask/profile layers.
- The repo still lacks a macro-world pipeline that can turn v007 landmass/climate/hydrology maps into live pack generation or editor previews.
- A future integration pass should define how v007 feeds v005 and how both eventually bake into canonical runtime/export packs.
