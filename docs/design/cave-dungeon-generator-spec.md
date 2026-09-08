# Cave And Dungeon Generator Specification

Date: 2026-05-24

## Goal

Create a random cave/dungeon pipeline that produces editable, coherent scenes for mining, exploration, and special encounter spaces while fitting the same tile/layer/editor model as the overworld.

## Design Targets

- support replayable cave scenes from seeds
- preserve authored entrances, exits, and landmark anchors
- generate layouts that remain editable in the in-game editor
- output valid terrain, height, occluder, object, and rule layers

## Generator Types

### 1. Surface Cave Mouth

Purpose:

- transition from overworld to underground
- partial daylight look
- visible cliff and entrance framing

Generation:

- mostly handcrafted template
- seeded detail clutter only

### 2. Cave Interior

Purpose:

- mining/resource exploration
- looping rooms and corridors

Generation:

- room-and-corridor hybrid
- optional cellular automata smoothing for natural walls

### 3. Special Dungeon

Purpose:

- curated challenge or story spaces
- stronger landmark identity

Generation:

- prefab-room graph with seeded connectors
- much higher authored content ratio

## Exact Generation Pipeline

1. choose biome preset and depth tier
2. stamp required anchors:
   - entrance
   - exit
   - boss/event room if applicable
   - safe utility nodes
3. build room graph
4. carve corridors
5. run wall smoothing pass
6. stamp water pits/chasms if allowed by preset
7. assign height bands and cliff/front-face markers
8. resolve autotiles
9. place props/resources/spawners
10. validate reachability

## Room Graph Standard

### Required Room Roles

- entry room
- at least one hub room
- resource rooms
- connector corridors
- optional hidden or reward room

### Graph Rules

- entry must connect to the critical path
- every required room must be reachable
- dead ends are allowed only for optional rewards/resources
- special rooms must not replace the main traversal path unless explicitly configured

## Tile And Layer Output

The generator must write:

1. terrain tiles
2. terrain autotile masks
3. object placements
4. zone tags
5. transition markers
6. rule/spawner markers
7. saved per-tile height values
8. front-occluder markers where cave arches or tall fronts exist

## Height / 2.5D Rules

- caves still use the same height model as the overworld
- most cave floors stay in one or two low bands
- ledges, pits, and raised shelves create depth breaks
- cliff/front-face assets provide the vertical illusion
- tall cave fronts may occlude the player when walking north behind them

## Resource Placement Rules

### Ore And Harvestables

- ore nodes spawn on wall-adjacent valid cells
- mushroom/herb nodes spawn on damp floor tags
- rare nodes prefer optional branches or deeper tiers

### Prop Placement

- debris avoids blocking the critical path
- support beams prefer large open rooms and chokepoints
- water pools/chasms require edge-safe collision output

## Seed Model

Use a stable composed seed:

```text
world_seed + scene_id + depth_tier + generator_version
```

This allows regeneration while preserving deterministic output for a saved world version.

## Editing Contract

Generated caves are not locked.

The player/dev workflow must support:

- repainting tiles
- moving/removing props
- editing transitions
- editing spawners/rules
- stamping handcrafted rooms into generated scenes

## Validation Rules

The generator must fail validation if:

- entrance or exit is unreachable
- mandatory room count is not met
- transition spawn lands on blocked terrain
- ore/resource nodes overlap collision-critical tiles
- autotile resolution leaves invalid seams at key paths

## Phase Plan

### Phase 1

- cave mouth template
- one cave interior preset
- room/corridor generator
- ore/resource placement

### Phase 2

- multiple cave biome presets
- underground water/chasm variants
- prefab special rooms
- hidden branches and rewards

### Phase 3

- dungeon-style encounter graphs
- event scripting hooks
- authored-plus-random hybrid story spaces
