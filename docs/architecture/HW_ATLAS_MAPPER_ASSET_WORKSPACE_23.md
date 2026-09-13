# HW-ATLAS-MAPPER-ASSET-WORKSPACE-23

This pass corrects the Atlas Mapper direction after the first Auto Map test.

The old behavior scattered source cells into a sampler layout. That is not enough.
The mapper now treats Auto Map as **Auto Scene**: a reviewable correction scene generated from the loaded sheet's known category and lightweight cell profiling.

## What changed

- Source cells are profiled by alpha coverage and average color into rough authoring roles: grass/top surface, water, cliff/earth face, sand/path, wood/structure, stone/neutral, detail/decor, and empty.
- Auto Scene now uses category templates instead of random scatter:
  - Cliff: top surface, cliff face, pool/water, shoulder/debris correction pieces.
  - Terrain: ground scene with water/channel sample.
  - Structure/House: small buildable module scenes.
  - Object/Equipment/UI: review galleries.
  - Character/FX: strip-style frame/layer layouts.
- Generated scenes are still **authoring evidence**, not runtime-published assets.
- The generated scene is meant to be corrected by the user, saved/exported, regenerated, and repeated until the sheet family is fully mapped.

## Where this goes next

The mapper becomes the seed of the Havenwild Asset Mapping Workspace:

```text
Source Library -> Tile Sheet -> Auto Scene -> Correction -> Pixel Collision -> Handoff -> Publish Candidate
```

Each panel must eventually be dockable/floating/lockable and embeddable into Emberwright's infinite-canvas editor.

## Green check policy

A green mapped check means mapper metadata exists for the source sheet path/hash. It does not mean runtime publication.

Runtime publication still requires sockets, footprint, collision, traversal, layer role, occlusion, provenance, and validation.
