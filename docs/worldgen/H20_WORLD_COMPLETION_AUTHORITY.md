# H20 World Completion Authority

Status: implementation/certification checkpoint  
Scope: finite production Archipelago worlds, streamed exterior runtime, Willowmere, water presentation, development world-map acceptance

## Purpose

H20 is not complete when isolated geography, streaming, cliff, or map systems merely compile. A production world must be coherent when the player creates a new save, opens the reveal-all map, travels across storage partitions, reaches Willowmere, explores forest and resource regions, crosses elevation, and watches water in motion.

This document locks the remaining H20 world-completion authorities before H21+ gameplay/UI work resumes.

H20S/H20V2 structural supersession: true cliffs begin at Level 2. Standalone one-high cliff walls and generated shoreline ladders are retired from normal worldgen. Level 1 is reserved for certified 2 -> 1 -> 0 ramp transitions or low-relief/grade-break semantics; constructed ladders are reserved for straight, dry Level-2+ hosts, while water-facing true cliffs reserve natural vine/climb access.

## H20A — One finite archipelago authority

`ArchipelagoSkeleton` is the finite Archipelago plan. `sample_geographic_surface()` consumes that same plan directly.

Hard rules:

- `WorldCreationSettings.land.major_landmass_count` requests 3–15 **major** landmasses.
- The default Standard world requests 8 major landmasses.
- Exactly one is the large Havenwild Mainland; the others are distinct major islands.
- Minor islands are additional and do not count toward the major-landmass request.
- The Standard world remains 8192×8192 tiles unless the selected world-size preset says otherwise.
- Finite topology origin/dimensions are part of `GeographicGenerationProfile`; storage chunks may not invent a second geography.
- The full 64-bit world seed is authoritative for the finite live geographic field: mainland initial materialization, runtime streaming, reveal-map sampling, ecology, hydrology, and structural generation.
- Historical non-active rectangle/island compatibility lanes may retain derived preview seeds until they are retired, but they may not define or override the finite streamed geography.
- Major islands are placed into separated ocean basins with an outer deep-ocean guard.
- The mainland is deliberately much larger than an ordinary major island so it can hold Willowmere, several regions/biomes, farms, rivers, highlands, caves, roads, and long traversal routes.
- Coastline lobes/noise may roughen planned landmasses but may not create an unrelated probabilistic continent authority.
- Chunk boundaries are storage boundaries only.

Acceptance:

- Reveal All shows every requested major landmass.
- Every planned major-landmass center samples as land.
- No major landmass crosses the finite-world ocean guard.
- A default 8-major world cannot collapse into a single connected circular island because of planner overlap.
- Larger size presets scale the plan in world coordinates rather than simply adding empty ocean.

## H20B — Streamed ecology/resource completion

Every newly streamed land partition runs the same deterministic natural-object population authority used during initial PCG materialization.

Order:

1. semantic geographic terrain
2. hydrology
3. structural levels/connectors
4. protected settlement/road/zone masks
5. deterministic natural objects/resources
6. runtime publication

Population includes the existing authored object families:

- trees
- bushes
- herbs/flowers
- mushrooms
- boulders
- ore nodes

Hard rules:

- ecology is based on global coordinates + the full world seed;
- forest habitat crosses chunk boundaries continuously;
- city, harbor, agricultural, and other reserved zones reject natural-object population;
- objects never replace semantic terrain;
- population is deterministic on regeneration;
- stale generated baselines from the pre-ecology/pre-archipelago authority are version-invalidated while player delta files remain authoritative.

## H20C — Willowmere is a visible city, not reservation metadata

The existing mainland feature pass remains authority for:

- harbor landfall
- town center
- road connection
- street network
- civic plaza
- plot reservations
- civic props
- cave approach

The selected global town center is now passed into world creation and materialized through the existing save-backed `BuildingInstance` system.

Initial Willowmere block:

- civic hall / large house
- tavern/inn
- residential cottages/houses
- market-side building
- artisan-side building
- additional civic/residential buildings

Hard rules:

- buildings use `BuildingPlacementSpace::ContinuousSurface`;
- `surface_region_id` is `havenwild_mainland`;
- global anchors sit inside the eight existing city plot reservations;
- building IDs are stable `pcg.willowmere.*` IDs;
- instances are written to the normal save-backed BuildingInstance world-state file;
- runtime building rendering, doors, linked interiors, persistence, and future player edits use the shared building authority;
- no Willowmere-only renderer or fake map icon substitutes for a physical city.

This first block is intentionally a production-visible capital foundation, not the final content-complete city. Later passes can add more recipe variety, NPCs, services, decoration, districts, and progression without replacing this authority.

## H20D — Animated pixel-art water

The LPC/V7 water tile remains the semantic/base visual authority. Animation is a presentation layer.

The existing renderer-neutral `WaterSurfaceSample` owns:

- depth
- reflection strength
- refraction strength
- caustic strength
- wave phase
- foam phase

Runtime presentation consumes those values for restrained world-space motion:

- ocean/pond/shallow water: horizontal wavelet highlights;
- shallow water: stronger subtle caustic contribution;
- deep water: darker/slower reflection-dominant motion;
- rivers/river mouths: directional flow streaks;
- shoreline topology remains authored V7/LPC terrain, never synthesized by the animation overlay;
- adaptive frame pressure reduces decorative layers/cadence without changing water semantics.

The compatibility shader also receives animation time so a non-LPC fallback does not regress to static water. If shader creation fails, the emergency lane draws the semantic water owner fill first and then the same bounded CPU animation overlay; a flat fallback may never overpaint animated water or leave water blank.

## H20E — Full-world development map

During development acceptance, Reveal All is the default map mode. `V` toggles normal exploration fog.

The reveal map:

- samples the same `GeographicGenerationProfile` and `sample_geographic_surface()` used by runtime generation;
- uses the same `ArchipelagoSkeleton` plan;
- covers the entire finite topology, not merely loaded/explored chunks;
- remains bounded to a coarse longest axis for performance;
- marks all major landmass centers;
- marks Willowmere when the save-backed city exists;
- retains the player marker;
- remains a diagnostic view and does not materialize every world chunk.

This is the acceptance surface for landmass count/scale, coastline shape, elevation distribution, hydrology, settlement placement, and traversal planning.

## H20F — World-generation certification

The Windows Full Quality Gate must fail closed when the source loses any of these contracts.

Static/structural certification checks:

- finite profile carries topology dimensions + requested major count;
- live finite sampler calls the planned archipelago authority;
- `ArchipelagoSkeleton::for_geographic_profile()` is present;
- streamed partition functions call deterministic natural-object population;
- generated baseline cache version is advanced for this authority change;
- Willowmere world creation writes `pcg.willowmere.*` ContinuousSurface BuildingInstances;
- animated water consumes `resolve_water_surface_sample()` and time;
- development reveal map consumes the persisted semantic world bake, with deterministic sampler/skeleton fallback for legacy saves;
- the H20 world-completion specification remains part of source.

Rust tests additionally cover:

- exact requested major count;
- production maximum 15-major placement;
- planned major centers resolve as land;
- outer finite boundary remains ocean;
- streamed ecology is deterministic and non-empty on representative mainland terrain;
- Willowmere building IDs/anchors are stable and unique;
- water animation changes with time and river motion is directional;
- existing H20 spawn, two-tier cliff/ramp, shoreline, hydrology, and streaming tests remain green.

## Runtime acceptance checklist

A fresh Standard world is accepted only after visual inspection confirms:

1. Reveal All visibly contains the requested major islands plus minor islands.
2. The mainland is substantially larger than the surrounding major islands.
3. Willowmere is physically visible as a road/plaza/building settlement.
4. Traversed forest habitat contains trees and supporting natural objects across streamed chunk boundaries.
5. Water visibly animates without shimmering the coastline geometry or changing semantic collision.
6. Rivers visibly flow and waterfalls remain structurally aligned.
7. Inland cliffs follow the two-tier grammar; large directional ramps appear only on carved 2→1→0 gateways.
8. True cliffs begin at Level 2. Standalone one-level walls are excluded from normal worldgen; Level 1 is reserved for certified ramp transition/low-relief semantics. Constructed ladders are reserved for straight, dry Level-2+ faces, while water-facing true cliffs reserve natural vine/climb access.
9. No straight chunk seam changes coastline, biome, objects, or structural generation.
10. Traversal into unexplored partitions does not synchronously stall player movement.

H21+ work may resume only after this world-completion checkpoint is green in the Windows gate and visually accepted in a fresh generated world.
