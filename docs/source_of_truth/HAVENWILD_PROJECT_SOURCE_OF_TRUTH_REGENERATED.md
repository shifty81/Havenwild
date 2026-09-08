# Havenwild — Project Source of Truth

**Regenerated:** 2026-08-09  
**Authoritative continuation:** Pass167Z109W8.1
**Normalization milestone:** Pass167Z106N5 — Repository, Content, Documentation & Victorian Asset Normalization.  
**Locked cumulative baseline:** Pass167Z59  

This document describes current Havenwild direction and architecture. Historical pass records are evidence only and live under `docs/archive/pass_history/`.

## 1. Product identity

Havenwild is a 2D pixel-art, top-down 2.5D open-world life simulator and sandbox with optional adventure gameplay. It combines persistent life simulation, relationships/family, professions/classes, player-owned property and businesses, farming/crafting, city life, exploration, caves, fishing, mining, and co-op in one generated world. Players choose how deeply to participate in adventure or production systems.

The game world is not a collection of small outdoor scenes. Outdoor town/roads/farms/woods/coast/mountains form one continuous chunked overworld. Interiors, caves, dungeons, cellars, upper floors, and other enclosed/special spaces can use transitions.

## 2. Permanent world anchors

- Main landmass/player-facing mainland name: **Alderreach**.
- Permanent capital: **Willowmere**.
- Willowmere is generated first from a stable authored capital framework in every world, then its surroundings/outskirts and supporting generated population may vary by seed.
- Willowmere/main capital occupies the western/left mainland coast and owns the major harbor/outer-island expedition gateway.
- A second primary city is guaranteed in/adjacent to the major mountainous resource/cave province.
- A third primary city is guaranteed in the southern sandy/dry province.
- The three primary cities require scheduled trade connectivity and NPC/passenger/freight movement between them.
- Storage partitions are implementation/runtime streaming units only; their boundaries must remain invisible to mainland geography, PCG, authoring and player-facing maps.
- World generation remains seed-driven and should vary landmass/coastlines/rivers/lakes/mountains/roads/resources/caves/biomes/settlement surroundings while guaranteeing required playability anchors.



## Current generated cliff grammar authority — W8

Fresh procedurally generated structural landforms are normalized before `CliffShape15` bake. The stable generated cliff vocabulary is masks `1,2,3,4,5,6,8,9,10,12`; one-cell three/four-edge caps/posts (`7,11,13,14,15`) are removed from fresh PCG rather than receiving invented pixels. North/east/west straight edges and north convex corners use exact authored ElizaWy cells, while the east+west narrow ridge uses the exact natural-scale three-cell companion LPC ridge row. Explicit editor/player-authored thin structures remain structurally legal but require a feature-specific authored recipe rather than a generic visual fallback. Ordinary generated cave mouths use the exact one-tile-wide authored narrow cave recipe regardless of cliff height; the wide 3x3 portal is explicit road/cart/major-tunnel only.

## Current vertical cliff modularity authority — W5

ElizaWy cliffs are modular vertically as well as horizontally. `StructuralCellV2.face_segments` already represents the discrete structural-tier delta. Runtime presentation therefore assembles height as fixed authored top/rim or shoulder, one complete authored 32x32 middle module per structural tier, then the fixed authored foot/base. Additional structural tiers insert one additional middle module each; there is no second `* 2` resolver-unit multiplier and no texture stretching. Straight south faces repeat c10r10, southwest/southeast rounded faces repeat c1r3/c3r3, the natural-scale three-column terminal repeats the complete c1-c3 row3 body row, and ladder A/B repeat c11r10/c13r10. Collision projection grows by the same one row per inserted module. Ramps remain one-tier; cave mouths and waterfalls are fixed authored features whose taller variants must use certified continuation above/through the feature rather than stretching it.

## Current cliff vocabulary authority — W4

The ElizaWy cliff sheet is treated as an authored tile/stamp vocabulary, not as raw pixels to reconstruct. The runtime vocabulary is centralized in `haven_assets::elizawy_cliff_provider`. Ordinary square rims use their exact square-plateau cells, and the ordinary south face uses the dedicated c10 r9-r11 authored top/body/foot column. The previous rounded-plateau body/foot borrowing is retired. Natural-scale authored windows remain the only legal basis for multi-cell cliff features. Missing roles remain unresolved until mapped; they are never synthesized.

## Current terrain/cliff provider authority — W3

Terrain and cliff sheets are treated as authored visual grammars. Semantic topology does not manufacture pixels. V7 surface terrain resolves exact four-corner tuple cells from its authored atlas. ElizaWy structural cliffs resolve whole 32x32 source cells and connected multi-cell assemblies at natural source/world-grid offsets. Half-tile composites, crop-as-new-shape, stretching, and directional mirroring/rotation in place of existing authored art are forbidden.

W3 explicitly supersedes W2's 16px southwest + 16px southeast synthesized terminal. The current rounded terminal path uses complete authored source cells at 32px offsets and extends collision over the same visual stamp footprint. The derived ElizaWy runtime overlay may remove semantic grass/ground pixels so the V7 surface provider remains visible; it does not alter cliff rock geometry or establish topology. Structural Level 0/1/2 and `CliffShape15` remain world/collision authority.

## 3. Tile/world presentation contract

- Canonical world cell: 32x32 pixels.
- The world is top-down 2.5D: artwork supplies visual height/depth; Havenwild does not use freeform continuous elevation painting.
- Structural elevation is discrete (Level 0, Level 1, Level 2 at current scope).
- Visible cliffs, lips, corners, ramps, stairs, ladders, bridges, cave mouths and waterfalls come from authored multi-cell art/recipes.
- A 32x32 LPC source grid is an addressing grid. It must never be assumed to equal a 1x1 placeable/world footprint.
- Collision/navigation may only follow visible certified structures and explicit traversal connectors.
- Geological/hydrology height remains separate raw simulation data and round-trips independently from structural levels.

## 4. Current Rust workspace

The Rust workspace contains:

```text
apps/haven_editor_native
crates/haven_core
crates/haven_world
crates/haven_assets
crates/haven_render
crates/haven_ecs
crates/haven_sim
crates/haven_net
crates/haven_pixel
crates/haven_save
crates/haven_authoring
crates/haven_editor
crates/haven_game
crates/haven_tools
```

The focused Rust module ceiling is 750 lines. Pass167Z109Q restored the architecture gate by extracting the four coordinators that had regressed above their limits. Pass167Z109R added the small `SurfaceTerrainRecipeV1` compatibility bridge so map/minimap, retained base-terrain presentation and structural traversal consume shared terrain authority without changing current visuals. Pass167Z109S normalized the native canvas transform/visible-region path, Pass167Z109T routed current PCG through `SurfaceWorldPlanV1`, Pass167Z109U added the small `haven_ecs` runtime plus one canonical ECS-backed player character motion/action state, and Pass167Z109V separated durable gameplay IDs from runtime ECS handles while typing persistence versions/deltas and retained-cache ownership without changing current save JSON shapes. Pass167Z109V1 then corrected the character animation binding: sprint now selects the authored LPC run family, Hand emits Punch rather than Emote, and tool-action semantic names bind to the pinned LPC backslash/halfslash/slash/thrust source families without silent walk/idle substitution. Pass167Z109W1 returned the active lane to terrain: south cliff corner presentation follows contour orientation across masks 6/7 and 12/13, mixed-mask diagonal chains share compact ownership, and projected collision follows the same corner decision. Pass167Z109W3 then corrects visual-provider ownership project-wide: V7 resolves exact authored surface tuples, ElizaWy cliffs use whole source cells/natural-scale stamps, and W2's half-width synthesized terminal is retired; collision follows the same authored footprint. Pass167Z109W5 certifies vertical modularity: one complete authored middle module is inserted per structural tier for straight, rounded, terminal and ladder families, and collision grows by the same row count. Pass167Z109W7 promotes the exact natural-scale left/right 3x4 directional ramp assemblies from the companion LPC cliff family and aligns fresh PCG to their six-cell traversal corridors. Pass167Z109W8 freezes the remaining fresh-PCG contour grammar to source-authored stable masks, removes thin generated cap/post shapes before bake, and locks ordinary cave mouths to the authored one-tile-wide recipe. Pass167Z109W8.1 is the compile-only follow-up required by the local Windows Cargo gate: it exposes the shared cliff source-cell draw helper to sibling modules and replaces const-unstable trait calls in modular-height helpers without changing terrain behavior. Future systems must extend focused units instead of increasing the limit.

## 5. Authoring architecture

`haven_authoring` is the canonical headless authoring kernel.

```text
                         haven_authoring
                      shared authoring kernel
                              |
             +----------------+----------------+
             |                |                |
 Native Developer       Player World       PCG / tools /
     Editor                Builder           automation
             |                |                |
             +----------------+----------------+
                              |
                        world/domain data
```

### Native Developer Editor

The native editor is Havenwild's complete offline developer authoring environment. It may expose source asset metadata, collision/recipe authoring, PCG internals, validation, Pixel/Animation Studio, world editing, building recipes, debug overlays, and other developer-only capabilities.

### Player World Builder

World Builder is an intentional player-facing game feature. Players/hosts can author worlds to play in using safe capabilities from `haven_authoring`. It is not the native editor embedded in the game. Source/license metadata, raw asset editing, developer collision recipes, and other unsafe developer-only operations are excluded from the player capability profile.

### F3 Developer Overlay

F3 is for diagnostics, inspection, teleport/debug spawning, profiling, and development live-reload support. It is distinct from Player World Builder.

### Future feature rule

A new feature should normally add:

```text
domain schema/data
+ runtime implementation
+ shared authoring operations
+ capability registration
+ save/migration ownership
+ validation
+ frontend presentation where permitted
```

Do not implement separate domain rules independently in the game, native editor, World Builder, PCG and validators.

## 6. World/content ownership

Current canonical roots:

```text
content/animations/        animation contracts/catalogs
content/worldgen/packs/    world-generation pack definitions
content/asset_packs/       asset provider manifests
content/assets/            asset/source metadata and curated licensed sources
content/editor/            editor/authoring contracts
content/gameplay/          gameplay data/contracts
assets/generated/          packageable reviewed runtime/editor generated outputs
WORKSPACE/generated/       reproducible machine-local audits/indexes/caches
```

`WORKSPACE/generated`, test outputs, saves and recovery are not source-rollup authority and are excluded from future complete-source/ChatGPT rollups. `assets/generated` remains packageable because it contains runtime/editor outputs required for exact visual reconstruction.

## 7. Asset and license policy

Every major asset family must carry source/license/provenance and technical metadata. Raw third-party source is read-only. Runtime promotion requires appropriate license status plus semantic role, complete visual region, actual world footprint, collision/interaction behavior where applicable, and editor/runtime validation.

The pinned ElizaWy LPC repository and Universal LPC character repository are major production foundations. Individual sources retain their own license/credit requirements.

### Victorian building source family

Pass167Z106N5 adds four supplied `LPC Victorian Buildings` sheets and the supplied credit file under:

```text
content/assets/lpc/source/victorian-buildings/
```

Havenwild selects the supplied **CC-BY-SA 3.0** route for this family. Attribution and share-alike obligations are preserved. The combined pack URL was not present in the supplied credit file; the underlying source URLs listed there are recorded in the machine-readable source-family contract.

These sheets are source-only until component regions are certified. The intended first use is modular Willowmere/city architecture: walls, foundations, roofs, gables, dormers, towers, windows, doors, bays, columns, porches, balconies, railings and trim.

## 8. Structural cliff state

The old procedural OGA grass-top cliff renderer remains quarantined because it treated connected specialist artwork as repeatable fragments. N5S also corrects the same category of mistake in the newer ElizaWy lane: the rounded 5x4 example plateau is connected sample art, not a source of generic repeatable west/east wall cells.

Current runtime authority:

- ElizaWy seasonal cliff sheets remain the primary structural family.
- all fifteen non-zero N/E/S/W exposure masks remain resolved by the structural topology authority.
- north/east/west boundaries use narrow square-plateau rim crops rather than full example cells.
- south boundaries use one upper lip plus the perspective-visible rock face; multi-level drops repeat rock body only and emit one lower grass foot.
- rounded/diagonal example cells are reference-only until a dedicated diagonal/curved structural authoring mode explicitly requests them.
- the walkable plateau surface remains the authored terrain material and is not overwritten by sample grass tiles.
- N5R water-facing cliffs, ramps/stairs/ladders, cave mouths, bridges, south/west/east waterfalls and visible structural collision remain active.
- missing visual authority still fails collision open so invisible walls cannot return.
- global structural-neighbor sampling continues across storage partition seams.

## 9. Native editor current direction

The native editor is the primary developer authoring environment. Its target/current shell is a persistent workspace with:

- application menu and document tabs;
- Project/Asset Browser;
- continuous world canvas;
- Inspector;
- fixed/overlay diagnostics panels;
- fixed status bar;
- unified selection/command/undo model;
- World, Scene, Pixel/Animation, Character and future PCG/building workspaces.

The World Editor treats Alderreach as one continuous authoring surface. Storage partition boundaries are diagnostics only, not authoring scene boundaries.

Pixel/Animation Studio uses read-only source sheets plus Havenwild-owned working documents. Multi-cell source selection, world footprint, collision, sockets and publish certification are separate concepts.

The legacy browser editor is archived and is not part of normal builds or future editor authority.

## 10. Characters and progression

- Character sex selection: Male or Female.
- Age groups: Child, Teen, Adult, Elder.
- Modular LPC character rendering is the production character path; pixel textures use nearest-neighbor filtering.
- Classes and professions are separate progression systems.
- Classes cap at level 10; a focused class should take roughly one in-game year to master.
- Characters begin with one active class slot and can unlock a second after mastery for hybrid builds; maximum two active classes.
- Professions are separately learnable and can eventually all be learned by one character.
- Each class/profession owns XP, levels, skill tree and permanent point allocation.

## 11. Property, cities and life simulation

Major cities include civic/property services where players can acquire deeds to land, houses, apartments, commercial buildings, farms, workshops and other properties. Deeds define ownership, zoning, boundaries, taxes, build permissions, utility access and restrictions.

Players can live, work, build relationships, marry NPCs or players, have children, run businesses, farm, craft, explore, fish, cave-dive and travel between cities. Adventure participation is optional rather than mandatory progression pressure.

## 12. Multiplayer/world ownership direction

The editor itself remains offline-capable and does not require networking. Multiplayer belongs to the game runtime. Player World Builder operates inside the client/runtime with host/world permissions and will use capability-based authoring controls. Future multiplayer authoring must preserve authoritative ownership/permission rules rather than importing native-editor trust assumptions into the networked game.

## 13. Validation and packaging

- normal Build development (fast) runs machine-local/dependency/cache sentinels, `cargo check --workspace --all-targets`, and debug game/editor builds; formatting, strict Clippy, tests, source validation, certification, and release builds remain explicit checkpoint/release commands unless the build scripts intentionally change.
- current-source validation runs the registered source authority profile.
- historical pass validators exist for evidence but are not automatically current authority unless registered.
- older validator/output registry generations are archived.
- cumulative patches are built from the locked Pass167Z59 baseline.
- when normalization requires path removal/move, the cumulative package includes a guarded removal manifest consumed by `HavenwildTools.cmd`; package-only apply helpers are forbidden at repository root.

## 14. Immediate roadmap after Pass167Z109W8.1

1. Keep terrain as the active lane. W3 makes the authored source sheets the visual authority and retires W2 half-tile synthesis; do not resume character/NPC/animal expansion yet.
2. W8 freezes the fresh-PCG cliff grammar after W7 ramps: stable generated masks use exact authored recipes, thin one-cell caps/posts are normalized out, and ordinary caves remain one tile wide. Complete the local visual cliff acceptance gate rather than inventing remaining pathological cap art.
3. Complete shoreline/coastal-toe + animated water through authored providers: semantic sand/pebble/rock/mud/direct-water receivers, shallows/deep water, surf, foam, ripples and flow presentation.
4. Complete mandatory waterfall/mountain hydrology semantics, then cave entrances and graph-first persistent cave PCG.
5. Run multi-seed terrain certification before resuming shared ECS character/NPC/animal capability expansion.


## Pass167Z106N5R integrated cliff connectors and collision

N5R retains the N5Q all-fifteen-mask ElizaWy cliff shape grammar and activates the remaining structural lanes against the same derived level field. Water-facing edges and waterfall edges are stored per cardinal edge instead of as cell-wide booleans. One-level MountainPath pairs are ramp connectors; Stairs objects provide stairs/ladder connectors; Bridge tiles open structural crossings; CaveEntrance objects replace eligible south cliff faces and use transitions for entry; and `Terrain/Waterfall.png` animates certified south/west/east multi-cell waterfall envelopes. Visible structural edges are authoritative movement collision while the pinned ElizaWy cliff source is available. Missing visual authority fails open. Cave mouths and waterfalls remain blocking faces rather than free-walk connectors.


## Pass167Z106N5S square-plateau cliff projection correction

The N5R live screenshot showed that the previous dry-cliff renderer still repeated full cells from the rounded 5x4 sample plateau as generic side-wall segments. Because those sample cells contain diagonal grass/rock transitions, long west/east boundaries produced alternating green/brown diagonal bands. N5S retires that runtime interpretation. The square 3x4 plateau now supplies narrow N/E/S/W rim crops, only south exposures own a full rock face, and the authored walkable top material remains visible. N5R water/connectors/caves/bridges/waterfalls/collision are retained unchanged.


## Pass167Z106N5X cliff corner, foot border, and ramp refinement

N5X keeps N5S straight-run square-plateau strips but promotes the reviewed rounded reference only for one-shot outer-corner joins. SW/SE outer masks use their connected three-cell rounded face columns once, while NW/NE use one-shot rounded lip crops. Rounded sample cells remain forbidden as repeatable generic sidewall material. Dry south cliff feet extend only the existing final grass fringe into a half-tile receiving apron over non-water, non-route projected lower terrain. Fresh-world ramp selection is now component-aware: each connected raised exact-level component with a supported south boundary gets at least one paired MountainPath gateway before optional spatially separated extras, with deterministic preference toward existing route/civic proximity outside the protected cliff buffer. N5R collision/connectors, caves, bridges, stairs/ladders, waterfalls, and missing-source fail-open behavior remain authoritative.

## Pass167Z109D — contextual ElizaWy cliff projection

**Historical Pass167Z109D checkpoint.**

Structural cliffs continue to use `TavernMap.structural_levels` and the canonical fifteen `CliffShape15` masks. Visual selection now adds read-only 8-neighbor context solely to distinguish a genuine diagonal chain from an isolated orthogonal South+West/South+East corner. V7 remains plateau-fill authority. Ordinary cardinal boundaries use narrow ElizaWy rim crops; ordinary perspective-visible south walls use c10 r9-r11; diagonal c1/c3 r6-r8 art is drawn from a generated transparent projection that removes foreign flat plateau grass while preserving rock and immediate grass fringe. Collision/traversal remains structural and connector-driven, independent of artwork.

### Pass167Z109W7 terrain continuation

Directional cliff ramps are exact authored 3x4 stamps from `content/assets/oga_lpc/source/terrain/cliffs_grass_top/LPC_cliffs_grass.png`: c3-c5/r5-r8 and c6-c8/r5-r8. Fresh generation paints the corresponding six-cell MountainPath corridor, while the center one-tier structural edge remains collision/navigation authority. No crop, mirror, rotation, stretch or fabricated ramp composition is permitted. Normal cave mouths are predominantly one tile wide; large openings are reserved for explicit road/landmark tunnels.

### Pass167Z109W8 terrain continuation

Fresh-PCG structural contours are frozen to masks `1,2,3,4,5,6,8,9,10,12`; generated masks `7,11,13,14,15` are contour-noise caps/posts and are normalized out before bake rather than receiving generic invented pixels. Exact ElizaWy north/east/west and north-corner source roles plus the exact companion-LPC E+W ridge row own the remaining non-south presentation. Ordinary generated cave mouths use c6/r9-r11 at one tile wide independent of cliff height; the 3x3 portal is reserved for explicit road/cart/major mountain tunnels. After local cliff visual acceptance, move directly to shoreline/water.


### W10 edge-delta cliff alignment
W10 preserves discrete Level-2 modular cliff height while sizing each visible south face from its exact structural edge delta (`1→0`/`2→1` = one module, `2→0` = two). Connected rounded diagonals use the complete authored lip/shoulder/body/foot stack rather than the historical compact projection, keeping straight and angled feet aligned.

### W11 exact receiver-facing cliff height
W11 separates **structural height** from authored endpoint decoration. The exact tier delta is now the total number of receiver-facing rows: height 1 uses the authored end/foot cell; height 2 uses top/shoulder + foot; height N inserts only `N-2` repeatable body rows between those endpoints. Host-row diagonal/terminal lips remain authored plateau-boundary caps and do not add height. Collision follows the identical row count.
