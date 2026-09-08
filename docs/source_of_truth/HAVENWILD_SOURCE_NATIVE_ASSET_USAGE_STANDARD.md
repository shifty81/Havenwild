# Havenwild Source-Native Asset Usage Standard

**Authority:** project-wide production asset consumption and PCG/editor/runtime placement  
**Pass:** H21A14AC3R4A  
**Status:** source-of-truth

## Core rule

Havenwild conforms authored gameplay and generation to the legal grammar of the source asset. The engine must not manufacture a new visual grammar from a source sheet merely because pixels or cells can be addressed.

A source cell, frame, module, or atlas coordinate is an address. It becomes a production-placeable asset only after its authored role, native footprint, allowed orientation, connectivity, layering, and runtime semantics are known.

## Production requirements

1. **Preserve native authored assemblies.** Multi-cell ramps, cliff bodies, roofs, walls, doors, furniture, character layers, animation frames, and similar authored groups are consumed at their declared footprint and alignment.
2. **No implicit transform synthesis.** Rotation, mirroring, stretching, arbitrary cropping, recoloring, or recomposition is forbidden unless the source contract for that asset family explicitly permits it.
3. **No diagnostic content in production worldgen.** Diagnostic, reference-only, rejected, compatibility-only, and preview assets remain available to tools/acceptance fixtures but cannot be selected by ordinary PCG/runtime placement.
4. **Semantic generation follows visual capability.** PCG may request only terrain shapes, cliff transitions, building footprints, connectors, and object roles that have a certified source-backed presentation. Missing orientations or transitions fail closed or use another certified connector type; they are not fabricated.
5. **Exact identity remains traceable.** Runtime/editor/PCG resolution must preserve the source family and promoted semantic identity so validation can prove what authored asset is being rendered.
6. **Native footprints and sockets are authoritative.** Collision roots, building anchors, architectural sockets, object footprints, and animation alignment derive from the promoted asset contract rather than a generic guessed rectangle.
7. **Variants are explicit.** Visual variety comes from real promoted source variants, legal palette/tint contracts, or authored modular composition. Repeating one asset is preferable to inventing a fake unsupported variant.
8. **Generated caches are disposable; player deltas are not.** When source-native generation rules change, generated baseline cache versions advance. Player-authored deltas remain authoritative and load before generated baselines.
9. **Editor and runtime consume the same contract.** An asset may not have one placement grammar in the editor and another in game/worldgen.
10. **Regression tests enforce the grammar.** High-risk source-backed systems require executable tests for allowed orientations, footprints, semantic roles, diagnostic exclusions, and generation invariants.

## LPC cliff and ramp application

- ElizaWy/LPC cliff source cells are consumed through certified connected cliff recipes, not as arbitrary standalone world tiles.
- The current certified directional ramp family is the native **3x4** RiseLeft/RiseRight source pair.
- The ramp pair is never mirrored, rotated, stretched, or cropped to create unsupported directions.
- Generated platform levels are **0 / 2 / 4**. Odd structural tiers are connector-local only: **1** inside a 2->1->0 ramp and **3** inside a 4->3->2 ramp.
- Generic one-high coastal cliff bands are not generated because no matching production cliff/ramp grammar is certified for that role.
- Constructed ladders use only their certified dry straight-face host. Water-facing connectors fail closed until an authored water-appropriate connector family is promoted.
- The ramp chooser owns the exact six-cell structural corridor. Downstream consumers copy that result; they do not reinterpret or reconstruct it.

## Building application

- BuildingRecipe footprint, sockets, roof mode, opening placement, and module orientation are authoritative.
- `classification.diagnosticOnly == true` recipes are never selected by normal settlement worldgen.
- Settlement variety is produced from promoted production recipes and authored layout variation. PCG must not rotate/stretch a cottage or diagnostic prototype merely to create another building silhouette.
- Coastal-city harbors are city districts and share the same settlement plan/road network; remote outposts and villages remain separate settlement classes.

## Terrain and ecology application

- Terrain tuples use exact promoted source combinations; unsupported material contacts remain explicit diagnostics or receive source-backed topology repair rather than proxy art.
- Natural population uses promoted object families at audited footprints/anchors.
- Streamed PCG partitions receive the same deterministic ecology contract as initially materialized regions so exploration does not cross into barren generated chunks.

## Promotion rule

When Havenwild needs a visual or structural capability that the current production library cannot express, the next step is to **promote an appropriate real source asset/module and certify it**, not to weaken this standard.
