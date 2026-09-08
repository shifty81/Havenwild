# Havenwild Generative World Lock

Generated: 2026-06-05

## Locked Direction

Havenwild is no longer a tiny-scene tavern prototype. The forward world model is:

```text
Factorio-esque seeded world generation
+ one continuous chunked outdoor overworld
+ transitions only for interiors, caves, dungeons, cellars, upper floors, and special enclosed spaces
+ persistent living-town schedules
+ effectively infinite procedural caves/mines
+ texture/material-atlas rendering for overworld and caves
```

## Overworld Rule

Outdoor areas should feel like one continuous open world:

- town
- tavern exterior
- roads
- farms
- woods
- rivers
- harbor
- mountain paths
- outdoor NPC travel routes
- owned land / purchasable land

These should not use tiny outdoor scene transitions. They should be represented as a chunked overworld surface generated from seed and settings.

## Factorio-Style Worldgen Rule

No two new generated worlds/playthroughs should need to be identical. The generator should vary:

- landmass shape
- coastline
- rivers and lakes
- mountain placement
- forest density
- road network
- town layout
- tavern starting plot placement
- cave entrances
- resource patches
- forage zones
- soil/fertility/moisture zones
- NPC home/work placement
- regional cuisine/resource distribution
- discovery order

The generator must still guarantee a valid cozy tavern-life start:

- reachable starter tavern plot
- reachable town
- reachable City Hall or equivalent land/permit service
- reachable harbor/ferry path when needed
- valid cave entrance
- sufficient early trees/resources/forage
- valid roads/path graph
- valid NPC homes/jobs/routes

## Worldgen Implementation Model

Use deterministic generation from:

```text
world seed
+ generator version
+ world preset/settings
+ biome/material profiles
+ authored gameplay anchors/stamps
```

Recommended stages:

```text
1. World seed and settings
2. Landmass / island mask
3. Heightmap
4. Moisture / temperature / fertility fields
5. Biome assignment
6. Water, rivers, lakes, shore bands
7. Mountain/highland/cave-region placement
8. Tavern/town/harbor/City Hall anchor placement
9. Road/path graph solve
10. NPC home/work/public marker placement
11. Resource/forage/crop/fish distribution
12. Cave entrance and cave seed assignment
13. Texture/material/autotile bake
14. Validation pass
15. Chunk delta save initialization
```

## Persistent Town Life

Citizens should live by persistent schedules across the open world.

Use simulation tiers:

```text
Full simulation       = visible/nearby NPCs
Light simulation      = loaded nearby chunks
Virtual simulation    = far/offscreen citizens
Resolved simulation   = calculated when player enters area/interior
```

Schedules should target named world places rather than raw coordinates whenever possible:

```text
npc_home.bed
shop.counter
town_square.bench
harbor.fishing_spot
road_marker.crossing
haven_tavern.public_table_pool
```

Weather, season, festivals, tavern open/closed state, quests, and route unlocks should be able to override schedules.

## Cave Rule

Caves/mines should be procedural and effectively infinite by chunks/depth layers.

Players can continue deeper/farther if they bring enough:

- pickaxes
- dynamite
- rope ladders
- food/supplies
- lantern fuel/light sources
- inventory space
- protective gear

Caves should support:

- destructible/minable tiles
- depth-based ore/resource tiers
- cave biomes
- underground water
- weak spots
- hidden shafts
- rope ladder descent
- rare chambers
- save deltas for mined/blown/placed changes

## Weak Spot + Rope Ladder Rule

PCG cave chunks can spawn weak spots:

- cracked walls
- weak floors
- collapsed passages
- suspicious rubble
- hidden shafts
- ore-pocket blockers

Dynamite or stronger explosives can open these. Some reveal lower shafts. A shaft is only usable if the player has/deploys a rope ladder or later ladder/winch upgrade.

Rope ladders become persistent placed traversal objects and must be saved as deltas.

## Texture/Material Rendering Rule

Use real texture/material atlases for both overworld and caves. PCG should output material IDs and metadata, not just color blocks.

Generation produces:

- material ids
- biome ids
- height/depth values
- moisture/fertility values
- edge relationships
- overlays/clutter
- objects/resources

Renderer resolves those into:

- base texture tiles
- variations
- autotile edges/corners
- detail overlays
- water/shore animation
- cave wall/floor materials
- lighting/weather/shader polish

Shaders are polish, not a replacement for source textures.

## Save Rule

Large generated worlds should save:

```text
seed
world settings
worldgen version
authored anchors
changed chunk deltas
placed/removed objects
mined cave cells
exploded weak spots
deployed ladders
NPC state
relationship/tavern/inventory/quest state
```

Do not save every generated tile unless modified.

## Editor Requirement

The Havenwild Editor needs tools for:

- seed preview/reroll
- world preset editing
- landmass/heightmap preview
- biome/material preview
- town/tavern/harbor anchor preview
- route graph preview
- NPC schedule marker validation
- cave generator preview
- weak spot/shaft preview
- texture/material atlas validation
- regenerate selected chunk/region
- lock authored regions/stamps
- validate entire generated world
