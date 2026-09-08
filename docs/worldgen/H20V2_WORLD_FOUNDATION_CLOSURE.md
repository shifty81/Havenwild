# Havenwild H20V2 World Foundation Closure

Status: source-complete / Windows compile and runtime acceptance required  
Baseline: `Pass167Z109W81R30R44H7-H20S1S8R3`  
Scope: H20V2 B1-B9 world bake, map truth, ecology, streaming/render performance, structural traversal, waterfalls, roads/harbor, Willowmere layout, and building entrance/exterior normalization.

## Authority chain

A finite Havenwild world now follows one ordered authority chain:

`WorldCreationSettings -> ArchipelagoSkeleton -> SemanticWorldBake -> streamed partition materialization -> hydrology publication -> structural cache -> ecology/objects -> runtime/map presentation`

Storage partitions remain streaming/persistence units. They are not allowed to invent different geography, forest habitat, drainage, or structural semantics merely because the player has reached them.

## B1 — Semantic world pre-bake

Fresh finite worlds persist `worldgen/semantic_world_bake_v1.json` before New Game reports success. The compact bake records the complete low-LOD finite-world raster, the globally planned drainage features, and major landmarks. Detailed chunks still stream on demand; New Game does not eagerly load the whole world into RAM.

## B2 — World-map truth

Development Reveal All first consumes the saved semantic bake and validates its world seed/profile. Older saves retain deterministic sampler fallback. Forest habitat has a distinct map semantic/color so a tester can locate ecological regions before physically streaming their tree sprites.

## B3 — Tree/ecology closure

Streamed PCG keeps region-specific object rolls but forest habitat always uses the full world-geography seed. Runtime population reporting now exposes total trees, forest-habitat grass cells, and trees actually placed inside certified forest habitat. This gives a direct trace for the previously invisible-tree defect.

## B4 — Exploration stutter and far-zoom budget

Hydrology and structural worker completion no longer implies one-frame publication. Completed maps/caches enter bounded queues and are published at no more than two partitions per frame inside a small publication deadline. Structural rebuilding waits for complete hydrology publication.

At extreme zoom-out, continuous-surface rendering stops resolving per-cell mapped LPC tuple/transition overlays that are below useful screen scale, reduces animated-water blend layers, and suppresses tiny forage sprites. Trees, roads, buildings, water, cliffs, and gameplay-important silhouettes remain visible.

## B5 — Cliff/ramp/ladder authority

True cliffs begin at Level 2. Level 1 is reserved for certified 2 -> 1 -> 0 ramp transitions or non-blocking relief semantics; ordinary world generation may not treat a standalone one-high wall as a normal cliff.

Authored 3x4 ramp art no longer claims the whole rectangular stamp as traversal/cliff ownership. Only the six MountainPath corridor cells own the structural passage, allowing neighboring cliff faces to terminate/overlap correctly.

Constructed ladders require a straight south-facing dry Level-2+ host compatible with the current authored ladder source. Angled/corner cliff faces fail closed. Water-facing true cliffs reserve natural vine/climb access; generated shoreline ladders are not substituted.

## B6 — Waterfall ownership

Waterfall presentation now uses the existing deterministic contiguous-run owner. A multi-cell river crossing therefore stamps one LPC waterfall connector rather than one offset giant sprite per neighboring source cell. South and side waterfalls receive the same continuous-surface manifest used to resolve run ownership.

Runtime acceptance still must verify exact crest/body/receiver alignment and adjacent shoreline/cliff tuple presentation against real generated falls.

## B7 — Roads and harbor

Mainland road paths receive deterministic low-amplitude naturalization rather than reading as hard ruler lines. The reserved harbor district now owns an actual stone quay surface with a supported dry road-family apron. The first water traversal is materialized as a wooden bridge/pier run rather than continuing the road material into water.

## B8 — Willowmere layout

The old symmetric cross/rectangle street grid is replaced by deterministic winding primary roads, secondary lanes, short spurs, and staggered plot anchors. Existing stable `pcg.willowmere.*` building IDs are retained so this is a layout correction, not a new persistence identity.

## B9 — Buildings, doors, and interiors

Willowmere residential `house.*` entries use the linked starter-cottage interior authority instead of taller same-world prototypes that presented as houses without a linked scene. The multi-level house exterior gains the missing front gable filler pieces. Generated tavern/prototype exterior doors now start in the closed state.

The shared BuildingInstance door runtime already owns timed LPC swing clips, movement passability/blocked frame thresholds, terminal persistent opening state, and animated draw-frame offsets. This pass preserves that single authority rather than introducing Willowmere-specific door animation code.

## Static certification

`tools/automation/validation/checks/worldgen/Validate-H20V2WorldFoundationClosure.py` guards B1-B9 directly. The project Quick Validation must remain green. Source/full validation may still report inherited historical validator/architecture debt; failures that reproduce unchanged on the baseline are not attributed to H20V2.

## Windows Full Quality Gate

The first Windows build after applying this patch is a compile-risk checkpoint and must run the normal Full Quality Gate. Do not advance to the next milestone if Cargo, tests, content validation, or root-patch intake is red.

## Fresh-world runtime acceptance

Use a newly generated Standard finite world so old generated baselines cannot hide worldgen changes.

1. Open Reveal All immediately. Confirm the complete archipelago is visible before exploration, Willowmere is marked, rivers/highlands are coherent, and forest habitat is visible.
2. Travel to at least two mapped forest regions. Confirm visible trees exist and streaming telemetry/logging reports nonzero forest habitat/tree counts.
3. Cross several unexplored partition boundaries while moving continuously. Record whether movement pauses still occur; watch queued hydrology/structural publication telemetry.
4. Test maximum zoom-out in a dense region and record FPS, then compare with normal/close zoom. Verify trees, buildings, roads, cliffs, and water remain readable.
5. Inspect multiple true Level-2 cliffs and both ramp directions. No standalone one-high cliff wall, diagonal ladder, or whole-ramp rectangular cliff cutoff is accepted.
6. Inspect at least two generated waterfalls. One coherent fall must connect river crest to downstream receiver without duplicated offset strips or broken neighboring cliff/shore tiles.
7. Follow Willowmere roads to the harbor. Roads should meander naturally; the harbor should read as road -> stone quay/apron -> wooden pier -> water without hard rectangular road/shore seams.
8. Walk Willowmere. Houses must be staggered rather than ruler rows. Residential houses must provide their linked interior transition. Civic/tavern/artisan buildings may retain their intentional recipe-specific interior policy.
9. Interact with exterior doors repeatedly. The LPC swing must visibly animate through intermediate frames, collision/passability must change at the authored frame threshold, and the terminal open/closed state must persist.

Only after all nine checks are green should H20V2 be considered runtime accepted and the next milestone begin.
