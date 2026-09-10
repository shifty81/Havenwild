# Havenwild Editor Workflow Gap Audit 02

Pass: `HW-EDITOR-GAP-AUDIT-02`  
Baseline: `HW-EDITOR-AUDIT-01` / `4fe34ca82a40547b475c29d22540c7a385434037`  
Behavior change: **none**

## Purpose

HW-EDITOR-AUDIT-01 classified the existing editor/F3 modules. This follow-up audits the **workflow model** against proven 2D editor patterns and resolves several terms before the command-spine refactor begins.

The important correction is that spawn placement does not need a new Spawn editor or Spawn tool. It belongs to the ordinary contextual placement workflow.

## Reference systems reviewed

### GameMaker Room/TileSet workflow

Useful patterns adopted conceptually:

- one Room Canvas where instances, tiles and assets are authored;
- layer-specific tools and Inspector properties;
- direct Asset Browser drag/drop into the room;
- Tile Editing window showing the source tileset;
- single/multi-tile selection and custom temporary selections;
- persistent multi-tile Brush Builder;
- rotate/mirror/flip operations on compatible tile selections;
- specialized asset editors reached from the same project/asset environment.

### LDtk workflow

Useful patterns adopted conceptually:

- Definitions vs Instances;
- active layer drives the lower contextual palette;
- separate Tile, Entity and semantic IntGrid layer concepts;
- semantic IntGrid values can drive generated auto-layer visuals;
- generated visual layer can be hidden to inspect source semantics;
- Entity Definitions can have typed custom fields and placement constraints, including a unique PlayerStart;
- world/level hierarchy with direct level navigation.

### Tiled workflow

Useful patterns adopted conceptually:

- tile layers plus richer object layers;
- point/object placement for gameplay metadata such as spawn points;
- object Templates with inherited defaults and per-instance overrides;
- typed custom properties/classes;
- reusable stamp brush with transform shortcuts;
- terrain/Wang metadata for edge/corner painting;
- Automapping rule maps for patterns terrains alone cannot express, including RPG-style cliff sides;
- generated rules may target multiple output layers;
- chunked large-map authoring and world organization.

### Godot TileSet/TileMap workflow

Useful patterns adopted conceptually:

- atlas tiles retain stable source/atlas/alternative identities;
- TileSet metadata owns collision, navigation, occlusion and custom data rather than scattering those rules through the map editor;
- terrain painting supports Connect, Path and tile-specific/manual overrides;
- terrain metadata is assigned to ordinary tiles, so a tile can still be placed manually;
- alternative tiles support visual/property variants;
- scene-backed tiles demonstrate a useful distinction between cheap visual tiles and richer instanced content;
- tile proxy/migration mappings provide a useful precedent for stable-ID remapping when catalogs change.

### RPG Maker map/event workflow

Useful pattern adopted conceptually:

- gameplay events/markers are placed in the same map context rather than requiring coordinates to be hardcoded elsewhere;
- map, event and region authoring are contextual modes over one map-oriented workflow.

Havenwild should not copy any proprietary UI or protected assets. These are workflow references only.

## Highest-value findings

### P0-01 — Creator-facing taxonomy is too large

`Stamp`, `ObjectKind`, placeable asset, building instance, structural pattern, PCG exemplar, source reference and multiple brush concepts overlap. V2 freezes the normal creator nouns to Source Sheet, TileSet, Material, Asset, Entity Definition, Instance, Prefab, Brush and Rule. Legacy nouns may remain as internal adapters during migration.

### P0-02 — Spawn is a workflow gap, not a missing studio

Current F3 has a special hotkey path for setting scene spawn. Native command vocabulary already contains `PlayFromHere`, but persisted Player Start placement is not normalized as ordinary typed entity placement. V2 uses Entities -> Player Start -> Place and a canvas command `Set Player Start Here`. `Play From Here` remains ephemeral.

### P0-03 — Current tool applicability is still adapter-driven

`UniversalTool` exists, but current applicability contains many explicit exceptions because real adapters are still split by viewport/layer. V2 makes the Authoring Context authoritative: active layer + selected definition/material determines valid tools.

### P0-04 — Asset definition/source-sheet boundary remains incomplete

The Assets Studio can list source sheets and assembly candidates, while other browsers still expose donor/source-oriented data. Normal creation palettes must present semantic/runtime-ready subassets. Source sheets move to Sources/Atlas Inspector.

### P0-05 — Terrain has accumulated material-specific policy

Terrain should be driven by Material capabilities and rule sets. Water, ponds, sand, shore, grass and future terrain families must not require separate creator workflows or name-based renderer/editor branches merely to participate in autotiling.

### P0-06 — Semantic source and generated visual output need explicit separation

The editor needs an LDtk-like ability to inspect semantic authored data without the generated visual layer, then restore generated presentation. This is essential when diagnosing cliffs, shorelines, roads and water.

### P0-07 — Terrain requires Connect, Path and Exact modes

A single neighbor-joining mode is insufficient. Connect is appropriate for contiguous regions, Path preserves stroke intent for roads/rivers/walls, and Exact allows direct tile/variant control. Godot's current terrain workflow demonstrates the practical value of all three concepts.

### P0-08 — Complex structural generation needs rule outputs, not more hard-coded branches

Tiled Automapping's RPG-cliff example is directly relevant: semantic cliff tops can be painted while rule outputs place side faces on another layer. Havenwild should support data-driven input-pattern -> output-pattern rules for structural visuals, with manually authored examples feeding those rules.

### P0-09 — Brushes and Prefabs need separate meanings

A Brush is an editor convenience that paints a repeatable arrangement. A Prefab is reusable semantic game content with identity/fields/overrides. A house is a Prefab; a frequently used 3x4 cliff arrangement can be a Brush or a rule output. This distinction removes much current ambiguity.

### P0-10 — Per-tile metadata needs one authority

Collision, navigation, occlusion, interaction/surface tags, terrain membership, transform permissions and variant weight should be metadata on TileSet tiles/alternatives where appropriate. Instance-specific overrides belong to the placed Instance, not the source tile.

### P0-11 — Definitions and Instances need inheritance/override semantics

Changing a definition should update instances unless a field is explicitly overridden. The Inspector must visibly distinguish inherited/default fields from local overrides and support resetting a field to its definition default.

### P0-12 — Editor/runtime render authority must converge

The Native Editor may use editor overlays, but world content cannot rely on separate proxy artwork or a different tile/structural resolver from the client. Editor and client need the same stable IDs and resolver outputs.

### P0-13 — F3 still activates the heavy editor path

Current F3 immediately enables `dev_mode`, `build_mode` and expands the editor. That contradicts the intended lightweight developer overlay. Runtime Edit must be entered explicitly.

### P0-14 — F3 per-frame work still needs a formal budget

The current runtime editor has already received culling fixes, but expensive paths remain possible: Assets/reference code loads catalog data on demand from UI paths, and collision overlay construction can rebuild a continuous-surface manifest during drawing. V2 forbids source/catalog discovery and complete-world index reconstruction in per-frame draw code.

### P0-15 — Native/F3/automation mutation parity needs executable tests

The same operation from each frontend must produce identical command semantics and saved world deltas. A visual screenshot alone is insufficient for parity certification.

## Additional gaps locked for later waves

- **P1 Context menu:** canvas right-click offers Play From Here, Set Player Start Here, Paste, Inspect, Open Atlas/Definition and compatible creation actions.
- **P1 Placement ghost:** show the exact pending tile/entity/prefab plus footprint and validation before commit.
- **P1 Multi-edit Inspector:** compatible selected instances can edit common fields in one operation.
- **P1 Transform policy:** transform availability comes from asset metadata; no silent rotation of directional art/collision when unsupported.
- **P1 Stable ID migration:** catalog changes can provide alias/proxy mappings rather than breaking placed content.
- **P1 Search/navigation:** search assets, definitions, instances, scenes/chunks and go-to coordinate/bookmark.
- **P1 Layer folders:** groups are collapsible, visibility/lock/opacity are consistent, and generated/manual state is obvious.
- **P1 Rule debugging:** visualize which rule matched, source neighborhood, produced outputs, rule priority/probability and unsupported cases.
- **P1 Rule locality:** auto-resolution invalidates/recomputes only the affected neighborhood, not an entire scene/world.
- **P1 Variation weights:** variants support deterministic weighted selection and a manual alternative picker.
- **P1 Brush Library:** saved brushes are searchable, categorized and previewable; temporary copied selections can act as transient brushes.
- **P1 Prefab creation:** `Create Prefab From Selection` captures selected semantic content with a declared root/pivot and dependency list.
- **P1 Prefab instances:** retain link to definition and expose explicit per-instance overrides/unpack operation where allowed.
- **P1 Logic binding:** selected entities/prefabs can open their Behavior/Dialogue graph directly from Inspector/context menu.
- **P1 World navigation:** complete finite-world overview, neighbor navigation, scene/chunk browser, minimap and bookmarks.
- **P1 Chunk/scene streaming in editor:** only needed detailed content is hydrated while the full world descriptor remains navigable.
- **P1 Recovery:** editor autosave/session recovery is independent from Git/PCC certification and never silently rewrites authoritative source.
- **P1 Hot reload:** changed TileSet/Asset/Prefab/Logic resources update the open Game Canvas and PIE through stable resource identities.
- **P1 Generated/manual diff:** regeneration can preview what generated cells/instances would change before overwriting derived output.
- **P1 Manual-override protection:** PCG/autotile regeneration cannot silently erase explicit manual overrides.
- **P1 Validation navigation:** diagnostics can focus/select the offending tile/entity/definition/rule directly.
- **P1 Provenance:** asset Inspector exposes source/license/attribution lineage without cluttering normal placement.
- **P2 Room/scene inheritance:** evaluate template/base-scene inheritance for recurring interiors/shops after Prefab semantics stabilize.
- **P2 Scene-backed tile optimization:** richer scene/entity-backed placements should be used only when behavior warrants the runtime cost; simple visuals stay atlas-backed.
- **P2 Advanced rule groups:** optional/biome-specific rule groups, deterministic probability and rule priority become data-driven PCG/terrain features.

## Canonical creation examples

### Terrain

`Surface -> Terrain -> Grass Meadow -> Paint -> drag canvas`

No Grass-specific editor path. Selecting another compatible Material follows the identical workflow.

### Exact tile correction

`Surface -> Terrain -> Grass Meadow -> Open Atlas -> select exact tile -> Exact -> click canvas`

This creates an explicit manual visual override while preserving semantic terrain authority.

### Cliff authoring

`Structure -> Cliffs -> Rock Cliff -> Paint/Rectangle`

Generated side/corner output comes from structural rules. If an output is wrong, select exact atlas tiles on the override lane, then optionally `Create Brush` or `Create PCG Exemplar` from the corrected selection.

### Player start

`Entities -> Player Start -> Place`

No spawn window. The unique-definition constraint moves/replaces the existing Player Start if necessary.

### Runtime test

Canvas context menu -> `Play From Here`.

This does not change the saved Player Start.

### House

Place individual structure/content pieces or existing Prefabs -> select assembled content -> `Create Prefab From Selection` -> name it -> place future instances with the normal Place tool.

## Pass 2 entry criteria

The next code pass may begin when:

1. the creator-facing noun set above is accepted;
2. Spawn is treated as entity placement, not a separate tool/studio;
3. Material/TileSet/Entity/Prefab responsibilities are explicit;
4. Game Canvas is the primary world-authoring surface;
5. current GREEN runtime remains the comparison oracle;
6. Authoring Context/Command/Transaction can be introduced without changing terrain visuals first.

The next implementation pass should therefore be `HW-AUTHORING-SPINE-02`: canonical Authoring Context + command/transaction adapters, including typed definition/instance identity and persisted Player Start vs ephemeral Play From Here semantics.
