# Worldgen Tileset Zip Audit - 2026-05-25

## Summary

Four new project-owned worldgen tileset archives were added at the repository root and audited:

1. `havenwild_worldgen_full_terrain_tileset_v001.zip`
2. `havenwild_worldgen_compact_plusmask_tileset_v002.zip`
3. `havenwild_worldgen_corner_mask_tileset_v003.zip`
4. `havenwild_worldgen_depth_shore_tileset_v004.zip`

There was also a duplicate archive:

- `havenwild_worldgen_corner_mask_tileset_v003 (1).zip`

## Audit result

These are **project-owned raw source/authoring packs**, not direct runtime overlays for the current Rust game/editor build.

They were staged under:

```text
assets/raw/worldgen-tilesets/
```

and indexed by:

```text
content/packs/worldgen_source_tilesets.json
```

## Pack roles

| Pack | Role | Recommendation |
|---|---|---|
| v001 full terrain | very broad 4096-slot terrain atlas | keep as source/reference baseline, not canonical runtime atlas |
| v002 compact plus-mask | compact cardinal-mask terrain/autotile experiment | useful for centerline connectors like roads/paths; shoreline logic is superseded |
| v003 corner-mask | shoreline/corner-mask fix | strong candidate reference for terrain edge logic |
| v004 depth shore | depth bands + shore profile follow-up | strongest current reference for richer shore/water profile authoring |

## Key conclusions

- v001 is broad but heavy and likely too expensive to maintain as the final runtime atlas.
- v002 is a meaningful simplification, but the README explicitly shows its shoreline approach was flawed.
- v003 is the better terrain-edge model for coasts, riverbanks, cliffs, cave transitions, and similar contour-based boundaries.
- v004 is the most advanced pack and should be treated as the leading raw-source candidate for future runtime/editor terrain pipeline work.

## Current implementation status

- The packs are available as raw source archives plus extracted review copies.
- They are **not** wired into the runtime/editor atlas pipeline yet.
- Current runtime/editor worldgen still uses the staged/generated worldgen v0.1 asset contract plus the imported v0.7-v0.10 editor/runtime data flow.

## Critical gaps moving forward

- A canonical terrain-tileset decision is still needed: keep evolving generated v0.1 placeholders, promote one of these raw source packs, or derive a baked runtime atlas from them.
- The runtime/editor autotile resolver still needs a deliberate upgrade path if v003/v004 corner-mask/depth-shore logic is to become authoritative.
- The repo still needs a normalized import workflow for project-owned raw source packs, similar to the one already used for third-party reference packs.
