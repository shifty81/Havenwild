# Havenwild Pass 167Z — Character, Worldgen, and Wide-View Performance Audit

## Evidence reviewed

The client captures showed three separate production issues rather than one shared rendering defect:

1. West/east character frames left the visible feet above the logical foot anchor and shadow.
2. Starter clothing layers were generated from one unsuffixed body geometry and reused across both body selections.
3. The default client test scene was still a rectangular QA fixture, while wide views submitted most flat grass cells individually through the mapped terrain atlas.

## Character normalization

- Generated torso, leg, and foot layers are now body-specific (`_male` and `_female`).
- The runtime compositor resolves clothing from the saved body selection.
- West/east frames receive an explicit grounding correction; north/south retain a smaller correction.
- The shadow stays at the logical world foot anchor so collision and navigation remain unchanged.
- The creator preview uses the same body-specific layer authority and preserves the 64×96 display aspect.
- The player atlas generator carries a revision stamp so stale generated character layers are rebuilt automatically.

## Character-creation catalog

The generic starter pool now contains 27 clothing choices across torso, legs, and feet. Headwear remains gameplay-acquired. Facial hair remains Male-only. The expanded options stay generic enough for initial creation while specialized, cultural, professional, armored, rare, and decorative clothing remains reserved for crafting, looting, shops, quests, and NPC outfit systems.

## Client worldgen materialization

The historical rectangular test board is replaced at build time by a deterministic generated slice that preserves existing objects, transitions, and spawn points while rebuilding terrain with:

- an irregular walkable mountain-rock top and blocking cliff perimeter;
- meandering routes;
- a variable east coastline with shallow, normal, and deep water;
- a bridge-protected east transition;
- organic field and pond footprints;
- sparse tall-grass coverage.

The materialized scene remains a development test slice, not the final 1024×1024 world. It makes current world-generation changes visible in the client while the larger chunk-streamed world path is completed.

## Wide-view rendering optimization

At normal and wide zoom, uninterrupted grass interiors are collapsed into row-span submissions. Only sparse interior cells submit LPC atlas detail. Material boundaries, transitions, painted cells, water, cliffs, paths, farms, and other authored terrain continue through their full rendering paths.

The retained-surface expected-coordinate vector is now allocated only when retained execution is requested. Transition-work capacity is reserved only when legacy transition overlays are required.

## Acceptance targets

- West/east feet visually meet the shadow without changing collision position.
- Male/Female clothing layers no longer reuse the wrong body geometry.
- A clean build regenerates the player atlas when its revision is stale.
- The client farmstead test world no longer appears as a rectangular QA board.
- Wide-view flat-grass draw submissions are materially lower while terrain edges remain atlas-authored.
- No performance claim is considered certified until the Windows build and live client telemetry are captured.
