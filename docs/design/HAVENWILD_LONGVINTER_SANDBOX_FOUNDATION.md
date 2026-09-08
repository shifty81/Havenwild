# Havenwild Sandbox Foundation — Longvinter Reference Contract

Status: Project direction / implementation reference  
Scope: Gameplay foundation, world density, economy, travel, building, PvE expansion  
Reference policy: Longvinter is a **workflow/feel reference only**. Havenwild must use original code, assets, world fiction, content, balance, UI, names, quests, characters, items, and encounter design.

## 1. Target Experience

Havenwild should preserve the immediacy of a compact top-down sandbox while supporting a substantially deeper persistent PvE world.

The player should be able to leave a safe/home location with no quest selected and still encounter useful decisions every few minutes: gather, fish, forage, hunt, mine, discover, fight, trade, build, farm, explore, help an NPC, investigate a cave, recover salvage, or redirect toward another island/settlement.

The world is large, but local play must remain dense. Large-scale PCG is not permission for empty traversal space.

## 2. Primary Sandbox Loop

Explore -> Discover opportunity -> Gather/Fight/Interact -> Carry/value decision -> Craft/Cook/Process/Sell/Use -> Upgrade player/property/tools/equipment -> Reach new territory/opportunities -> Repeat.

Every major profession should plug into this loop without requiring combat, while PvE should remain a first-class parallel route rather than an optional afterthought.

## 3. Reference Pillars

### Longvinter-inspired foundation

Use as reference for:
- readable top-down sandbox movement and world scale;
- frequent gatherable/interactable opportunities;
- fishing, farming, crafting, cooking and trading participating in one economy;
- camps/property/building embedded directly in the playable world;
- island travel and destination-based exploration;
- low-friction interactions and compact UI feedback;
- persistent multiplayer/co-op sandbox flow.

Do not inherit a PvP-first foundation. Havenwild is solo/co-op PvE first.

### Stardew-inspired depth

Use as reference for:
- profession identity and long-form skill progression;
- farming/crops/animals/processing;
- town life, vendors and services;
- relationships, routines and personal NPC arcs;
- readable interaction language.

### Zelda-inspired world/traversal

Use as reference for:
- discrete readable topology;
- explicit traversal connectors and environmental gating;
- secrets and layered exploration;
- caves/dungeons and authored-feeling encounter spaces;
- readable combat arenas and route choices.

## 4. Havenwild Differentiators

Havenwild must go substantially beyond the sandbox reference with:
- rich hostile wildlife, monsters and hostile factions;
- caves, mines, ruins, dungeons and elite/boss encounters;
- NPC villages, towns and major cities with persistent simulation;
- quests, contracts, discoveries and dynamic events;
- class and profession progression;
- equipment, tools, upgrades, injuries and treatment;
- hunting, carcass harvesting and skinning;
- deeper farming, fishing, cooking, brewing and crafting chains;
- sailing/island travel and later broader transportation systems;
- persistent Home Estate and property ownership;
- authored anchors blended with deterministic PCG geography;
- server-authoritative persistent multiplayer/co-op state;
- economy driven by both NPC and player production/consumption.

## 5. World Density Contract

Every generated region/chunk cluster should be evaluated by gameplay opportunity, not biome appearance alone.

A populated surface region should normally provide several of:
- forage/resource nodes;
- fishing/water opportunity;
- harvestable vegetation or timber;
- wildlife;
- hostile encounter possibility;
- landmark/POI;
- cave/ruin/dungeon hook;
- road/trail/shoreline route;
- buildable/campable space;
- settlement/vendor/service connection;
- profession-specific resource;
- environmental storytelling or secret.

World generation should expose a density diagnostic so designers can identify visually large but gameplay-empty regions.

## 6. Region Opportunity Graph

PCG should eventually produce an opportunity graph in addition to terrain.

Example coastal region:
Harbor -> fishing grounds -> forage route -> cliff connector -> cave -> hostile camp -> farmable clearing -> road to settlement.

Example upland region:
Road junction -> forest resource pocket -> Level-2 plateau -> mine -> waterfall -> herbs -> ruins -> monster territory -> farmstead.

This graph is semantic. Renderer/editor/map consume it; they do not independently invent POIs.

## 7. PvE Foundation

PvE is a permanent core system, not post-launch decoration.

Surface PvE should include:
- territorial wildlife;
- roaming predators/monsters;
- bandits/hostile humanoids where fiction allows;
- guarded resource sites;
- random encounters/events;
- elite variants;
- faction-controlled locations.

Enclosed PvE should include:
- caves;
- mines;
- ruins;
- dungeons;
- lairs;
- hostile settlements/outposts;
- event instances.

Combat rewards should feed crafting, professions, economy, equipment and exploration rather than exist as an isolated XP loop.

## 8. Economy Contract

Resources should have multiple possible destinations:
- consume/use directly;
- process into higher-value goods;
- use for crafting/building;
- satisfy quests/contracts;
- sell to appropriate vendors/markets;
- reserve for profession progression;
- trade with players in multiplayer.

Fishing, farming, hunting, mining, forestry, cooking and crafting must all be viable economic identities.

## 9. Building and Property

Building should remain part of the normal world interaction loop.

Layers:
1. Temporary field camp / deployables.
2. Persistent Home Estate expansion.
3. Purchased land/property/buildings in settlements where allowed.
4. Specialized production buildings/workshops.
5. Multiplayer/shared or organizational structures where supported later.

Building must use world collision, zoning, ownership and persistence authority rather than a detached minigame scene.

## 10. Travel

Travel should create destination decisions rather than dead time.

Near-term:
- walking/running;
- swimming where allowed;
- ladders/ramps/stairs/vines under structural connector authority;
- boats/ferries between islands and coastal destinations.

Travel routes should expose resources, POIs, encounters and services along the way.

## 11. Map Contract

The map is a semantic LOD of the real persistent world, not a separate decorative image.

It should eventually expose according to exploration/knowledge:
- coastlines and landmasses;
- structural elevation/cliff contours;
- rivers/lakes;
- roads/trails;
- settlements;
- discovered buildings/services;
- caves/ruins/POIs;
- travel connections;
- profession/resource knowledge where appropriate.

Debug Reveal All may show final deterministic world truth, but release play respects exploration/fog/knowledge rules.

## 12. Editor/PCG Requirements

The native editor should support:
- world-density heatmap;
- opportunity graph overlay;
- resource/forage/fishing overlays;
- PvE spawn/territory overlay;
- settlement/service overlay;
- travel-route overlay;
- structural topology/connector overlay;
- map semantic preview;
- deterministic seed regeneration and comparison.

Authoring anchors and PCG output use the same semantic contracts.

## 13. Initial Implementation Sequence

### HW-SBX1 — Opportunity/Density Semantics
Add shared semantic types for opportunity categories, region density accounting and diagnostics without changing gameplay balance.

### HW-SBX2 — Gathering/Fishing/Farming Loop Audit
Normalize existing gathering, fishing, farming, inventory, tool belt, crafting and economy connections into one player loop.

### HW-SBX3 — Surface PvE Population
Introduce deterministic hostile/wildlife encounter placement tied to geography and region opportunity budgets.

### HW-SBX4 — POI/Cave/Ruin Hooks
Make generated regions reserve and publish semantic POI anchors that editor, map and runtime share.

### HW-SBX5 — Settlement/Trade Integration
Connect city/town/vendor services to regional resource flows, contracts and player selling/processing.

### HW-SBX6 — Camp/Property Integration
Normalize temporary camps, Home Estate and purchased-property progression under common ownership/build authority.

### HW-SBX7 — Island Travel
Make harbors/boats/ferries real world-route nodes and integrate travel destinations with the semantic world map.

### HW-SBX8 — Sandbox Acceptance World
Create a permanent acceptance seed/area where a short play session can demonstrate exploration, gathering, fishing, farming, crafting, trade, building, PvE, cave/POI discovery and island travel without debug commands.

## 14. Acceptance Principle

A Havenwild region is not complete merely because terrain renders correctly.

It is complete when:
- geography is readable;
- traversal makes sense;
- there are useful things to do;
- activities connect to progression/economy;
- PvE and non-combat play coexist;
- map/editor/runtime agree on world semantics;
- multiplayer persistence can represent the resulting state.
