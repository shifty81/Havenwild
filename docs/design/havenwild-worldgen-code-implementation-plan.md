# Havenwild — Worldgen Code Implementation Plan

## Goal

Move from hand-authored scene rectangles toward deterministic layered generation while preserving the current scene-based editor and save format.

## Scale rule

Treat `MAP_W=48` and `MAP_H=32` as the current compact playable scene size, not as the dimensions of a whole island. A scene preview should show one local area at tile scale. A region/island preview should show a world graph or coarse island map where scenes are nodes/areas and buildings are icons, not full-size tile rectangles.

Farmstead-specific scale targets for the current 48x32 prototype:

- tavern footprint: roughly 10-18 tiles wide and 7-12 tiles deep
- starter field: roughly 8-16 tiles wide and 5-10 tiles deep
- road/path: 1-3 tiles wide except plazas/porches
- cave entrance: local object/transition feature, not a mountain covering the scene
- coastline/island silhouette: only present if the scene is explicitly coastal; otherwise use transitions to adjacent shore/harbor scenes

Any debug image that makes the tavern and island appear near the same size is invalid and should be labeled as an imported concept placeholder or regenerated.

## Existing code anchors

Current code already has strong anchors:

- `TileKind::ALL` for stable tile identity
- `SceneId` and `SceneMap` for scene-based worlds
- `SceneBiome` for biome routing
- `ZoneKind` for gameplay zones
- `TavernMap.heights` for per-cell height
- `starter_for_seed(scene, seed)` for deterministic scene generation entry
- `validate_world(world)` for structural validation

Do not throw these out. Extend them.

## Phase 1 — Add generator module without changing behavior

Add:

```text
crates/haven_core/src/worldgen_layered.rs
```

Then add to `lib.rs`:

```rust
pub mod worldgen_layered;
```

This gives us shared helper code without risking current maps.

## Phase 2 — Add visual metadata helpers

Add metadata methods without expanding the enum too much:

```rust
TileKind::is_natural()
TileKind::is_liquid()
TileKind::is_fishable()
TileKind::supports_decor()
TileKind::base_spawn_weight()
```

This lets render/editor/game logic ask tile questions cleanly.

## Phase 3 — Add generated-cell side data

Current `TavernMap` has `tiles`, `heights`, and `objects`. Add optional layer arrays later:

```rust
pub struct TileStateLayers {
    pub moisture: Vec<u8>,
    pub fertility: Vec<u8>,
    pub water_flow: Vec<FlowDir>,
    pub decor: Vec<DecorKind>,
    pub generated_flags: Vec<u16>,
}
```

This avoids turning every condition into a new tile enum.

## Phase 4 — Replace one scene at a time

Do not rewrite every starter scene at once. Recommended order:

1. `EastWoods` — easiest natural generation test.
2. `SouthField` — tests soil/fertility/farm rules.
3. `Farmstead` — tests tavern/farm/cave/river together.
4. `CaveMouth` — tests cave generator.
5. `CaveDepths` — tests deeper ore/resource generation.
6. Interiors last — they need room planner/construction integration.

## Phase 5 — Editor debug overlays

Expose generated layers in the dev/editor overlay:

- height
- moisture
- fertility
- water flow
- decor density
- protected/reserved zones
- fishable water
- generated vs player-edited cells

Debug preview outputs should include their source:

- `active_scene_render`: actual current `SceneMap`
- `generated_layers`: output of `worldgen_layered` before player edits
- `region_graph`: abstract island/region composition
- `imported_placeholder`: non-authoritative art from asset packs

## Phase 6 — Save deltas

Eventually save:

```text
world_seed
scene_profile_id
player_modified_cells
placed_objects
crop_state
soil_state
resource_state
construction_state
```

This keeps saves small while still allowing deterministic generated worlds.

## Code-specific improvements to make now

### Add `TileMeta`

A small metadata table avoids huge match statements across gameplay/render/editor code.

Suggested fields:

```rust
pub struct TileMeta {
    pub walkable: bool,
    pub buildable: bool,
    pub natural: bool,
    pub liquid: bool,
    pub fishable: bool,
    pub fertile: bool,
    pub decor_allowed: bool,
    pub default_zone: ZoneKind,
}
```

### Add `FlowDir`

```rust
pub enum FlowDir { None, North, East, South, West }
```

Use it for animated rivers, fishing region, boat drift, and water sound direction.

### Add `DecorKind`

```rust
pub enum DecorKind {
    None,
    FlowerPatch,
    Reeds,
    Shells,
    Driftwood,
    Pebbles,
    SmallRock,
    Mushroom,
    CaveCrystal,
    Foam,
    WaterRipple,
}
```

This makes appearance richer without changing collision.

### Add path/room reservation masks

Generated scenes need protected areas:

- tavern footprint
- roads
- bridges
- cave entrances
- transition rectangles
- farm plots
- future city/town entries

These should be reserved before object/decor scatter.

### Add validation for worldgen

Add warnings for:

- no fishable natural water in exterior scenes
- cave scenes with no ore nodes
- farm scenes with no fertile/tilled soil
- transitions landing in water/walls
- roads disconnected from transitions
- scene has zero walkable cells
- missing return transition

## Patch included

The included `patches/0001-add-worldgen-layered-module.patch` only exposes the module. It intentionally avoids changing active generation so it is low-risk.
