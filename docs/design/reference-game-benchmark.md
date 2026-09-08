# Reference Game Benchmark

Date: 2026-05-24

## Benchmark Goal

Capture the closest public-facing implementation patterns for a cozy tavern-management game with construction editing, layered depth, and editable rooms so Havenwild Prototype can mirror the useful behavior without copying protected expression.

## Primary Reference: Travellers Rest

### Publicly Verifiable Workflow Facts

- Construction Mode is the closest visible analog to a player-facing in-game editor.
- Construction is accessed through a dedicated world object rather than a raw debug menu.
- The UI exposes floor switching, material counts, building/decor/zone/access categories, and commit-or-revert behavior.
- Construction edits are previewed before final acceptance.
- Room identity is driven by access placement plus zone/room validation.
- Decoration Mode exposes comfort, footprint, and some rotation behavior.

### What To Copy As System Behavior

- Separate **player-facing construction** from **developer-facing full authoring**.
- Use pending edit sessions with:
  - valid/invalid preview colors
  - material or rules feedback
  - accept/revert actions
- Make room quality derive from rules and metadata, not only from tile art.
- Keep furniture metadata explicit:
  - footprint
  - rotation support
  - comfort contribution
  - placement restrictions

### What Not To Copy

- Exact UI art, specific menu arrangement, proprietary names, room formulas, sprite look, map layouts, or proprietary data tables.

## Secondary Reference: Stardew Valley

### Useful Public Layering Facts

- Standard map stack uses `Back`, `Buildings`, `Paths`, `Front`, and `AlwaysFront`.
- `Front` is the key walk-behind layer.
- Additional suffixed layers can be inserted while preserving the base layer contract.

### Translation For This Project

- Use a fixed semantic layer contract rather than ad hoc draw-order exceptions:
  1. base terrain
  2. terrain details and decals
  3. collision/build surfaces
  4. y-sorted actors and props
  5. front occluders
  6. always-front overlays/VFX/UI markers

## Secondary Reference: Core Keeper / Cozy Top-Down 2.5D Games

### Repeated Genre Patterns

- Orthographic simulation space stays grid-aligned.
- Depth comes from shadows, front faces, raised ledges, tall silhouettes, and y-sort pivots.
- Terrain variety is usually metadata-driven:
  - biome family
  - connection family
  - height band
  - clutter/spawn rules

### Translation For This Project

- Do not rotate the gameplay grid into isometric.
- Use height bands plus front faces and backdrop silhouettes to create the 2.5D illusion.
- Keep authored gameplay positions grid-based for editor simplicity.

## Secondary Reference: Tiled / LDtk / In-Engine Editors

### Shared Authoring Patterns

- Layered maps with explicit semantics outperform a single mixed layer.
- Entities/objects need metadata beyond their sprite.
- Prefabs/stamps accelerate repeated world building.
- Validation surfaces should be visible during authoring, not only at export time.

### Translation For This Project

- Support scene templates, rectangular copy/paste, prefab stamps, and per-object inspectors.
- Keep validation and world graph tools inside the runtime editor.
- Use the web editor for slower data-entry and preview workflows, not as the only editor.

## Benchmark Conclusions

### Exact Product Split

1. **Player Construction Mode**
   - room building
   - furniture/decor placement
   - rule feedback
   - accept/revert transaction
2. **Developer Authoring Overlay**
   - all scene layers
   - transitions
   - spawners/rules
   - map generation
   - validation and world graph
3. **Web Editor**
   - content schemas
   - prefab/template authoring
   - GUI layout preview
   - asset metadata management

### Exact Depth/Layer Recommendation

1. orthographic camera
2. scene height field
3. terrain band resolution
4. y-sorted actor/object pivots
5. front occluders and cliff faces
6. parallax backdrop layers

### Exact Asset/Data Recommendation

Every tile/object family should be authored through metadata rather than one-off hard-coded rendering rules:

- family id
- biome tags
- height band compatibility
- autotile group
- collision flags
- front-occluder flag
- sort pivot
- shadow profile
- decoration scatter rules

## Resulting Design Standard

Havenwild Prototype should feel like:

- Travellers Rest in construction clarity
- Stardew Valley in semantic layer discipline
- modern cozy sandbox games in faux-depth presentation
- LDtk/Tiled-style editors in explicit data ownership
