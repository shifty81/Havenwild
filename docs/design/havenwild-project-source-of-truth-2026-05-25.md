# Havenwild / Havenwild — Project Source of Truth

**Generated:** 2026-05-25  
**Purpose:** Consolidated single-document project reference covering the current design, architecture, gameplay systems, editor systems, source-code state, asset rules, implementation roadmap, and remaining gaps.  
**Working project identity:** Havenwild / Havenwild prototype.  
**Current source prototype name:** Havenwild Prototype / tavern workspace.  
**Important naming note:** `Havenwild Prototype` appears in the current source zip because the prototype started as a cozy tavern-life inspired Rust sandbox/tool workspace. The forward project identity should become **Havenwild** or another original final title. Keep all production names legally distinct from Travellers Rest and other existing games.

---

## 0. Executive Summary

Havenwild is a cozy 2.5D orthographic tavern-life, farming, crafting, relationship, exploration, and island-progression game. The player owns one primary tavern near the main city on a mountainous island. The tavern is the home base and main hands-on loop. Over time the player expands the tavern, builds production rooms, grows crops and herbs, hires staff, learns regional cuisines, explores caves and islands, fishes, mines, smiths tools/armor, and eventually unlocks additional island plots and late-game managed tavern branches.

The current technical direction is a **Rust-first custom game/editor stack** with a playable Rust prototype already present in the uploaded clean source. The current source uses a workspace with:

```text
crates/haven_core      shared gameplay data model
crates/haven_game      playable Macroquad runtime and in-game editor overlay
crates/haven_editor    editor/tooling model and validators
```

The current prototype already includes scenes, transitions, heightmaps, tile editing, tile rules, world graph tools, save/load, zones, object placement, construction tools, and a live in-game editor overlay. The forward path is to refactor this into a proper Havenwild architecture with a cleaner runtime/editor split, multiplayer/listen-server foundation, metadata-backed assets, and stronger worldgen/editor tooling.

The central project requirement is no longer just a game. It is a **game plus authoring environment**: a main Rust editor, an in-game overlay editor, and optional web/editor utilities that together allow full front-to-back authoring of maps, tiles, assets, objects, NPCs, quests, staff, dialogue, recipes, worldgen, and gameplay content.

---

## 1. Non-Negotiable Project Rules

### 1.1 Originality and Legal Boundary

- The project is inspired by the broad cozy tavern/farming/life-sim genre, but it must remain legally distinct.
- Do not clone or directly reproduce Travellers Rest, Stardew Valley, Paper Mario, OpenGameArt/LPC packs, or any other existing game/assets.
- Uploaded third-party/reference asset packs are **reference-only**.
- Do not directly import, trace, pixel-copy, palette-lift, or ship reference assets unless their license has been audited and the project intentionally accepts the obligations.
- Production art must be original Havenwild art, recreated/redrawn to project specs.
- Any source assets with uncertain licensing should remain in a quarantined/reference folder and never enter runtime bundles by default.

### 1.2 Camera and View Direction

- The game is a **fixed 2.5D orthographic depth-view game**.
- It is **not isometric**.
- It is **not full top-down**.
- Most generated gameplay references, editor previews, asset specs, and worldgen previews must use the player-facing 2.5D orthographic view.
- Wide scenic/zoomed-out maps are valid only as world-map, planning, or cinematic references, not normal gameplay camera references.
- Cinematic pans may be used for important story/event moments, but the normal player view remains fixed 2.5D orthographic.

### 1.3 Tile Scale and Character Scale

- Base world tile size: **32×32 pixels**.
- Current Rust prototype uses `TILE_SIZE = 32.0`.
- First locked player animation sheet:
  - File: `player_base_walk_8dir.png`
  - Frame cell: `64×96`
  - Directions: 8
  - Walk frames per direction: 8
  - Sheet size: `512×768`
  - Anchor: bottom-center foot anchor
  - Collision: small foot collision mask
- Player sprites are roughly 2 tiles tall visually.
- Tavern/building walls are **1 tile thick** structurally.
- Wall visual readability should be around 3 tiles tall minimum.

### 1.4 Editor-First Production Rule

- The editor must be a real production tool, not a fake overlay.
- Every major runtime system should be authorable, inspectable, validated, and saveable through tools.
- The in-game editor overlay should support live gameplay testing and fast iteration.
- The main Rust editor should support deeper authoring workflows.
- Optional web editors can be used for lightweight workflows, previews, and data editing.

### 1.5 Metadata-Backed Asset Rule

Every major asset must have schema-versioned metadata. Do not treat assets as raw PNG/JSON only.

Metadata should define:

- editor behavior
- runtime behavior
- validation rules
- preview behavior
- hot reload behavior
- optional runtime cache outputs
- save/export behavior
- anchors and pivots
- collision/interaction masks
- sorting/Y-sort origin
- footprints
- tags/categories
- license/source/audit status

This applies to:

- character animations
- terrain/autotiles
- wall autotiles
- objects/furniture
- trees/foliage
- rooms
- scenes
- worldgen packs
- water/fishing regions
- doors/transitions
- GUI skins
- items
- recipes
- NPC/staff definitions
- build/expansion rules
- dialogue portraits
- cutscene/camera markers

---

## 2. Current Uploaded Source Snapshot

### 2.1 Uploaded Zips Audited

Current accessible project source zips:

```text
/mnt/data/havenwild-thin-source-20260524-214551.zip
/mnt/data/havenwild-clean-source-current-20260524-222502.zip
```

The clean source zip is the larger current source and contains:

```text
Cargo.toml
Cargo.lock
tools/build/Build.ps1
README.md
assets/
content/
crates/haven_core/
crates/haven_game/
crates/haven_editor/
docs/
MODS/
SDK_FACTORY/
SOFTWARE/
legacy/havenwild_platformer/
```

### 2.2 Current Rust Workspace

Root `Cargo.toml` defines a Rust workspace:

```toml
[workspace]
resolver = "2"
members = [
  "crates/haven_core",
  "crates/haven_game",
  "crates/haven_editor"
]

[workspace.package]
version = "0.1.0"
edition = "2021"
authors = ["Shifty"]

[workspace.dependencies]
macroquad = "0.4"
```

### 2.3 Current Runtime Prototype Controls

The current prototype README documents these working/editor controls:

- `WASD`: move
- `O`: open/close tavern
- `F3`: toggle dev mode
- `B`: toggle construction mode while dev mode is active
- `M` or Min button: minimize/restore editor overlay
- `PageUp` / `PageDown`: cycle scenes in dev mode
- `Tab` or `1`-`0`: construction tool selection
- `Q` / `E`: switch editor tabs
- World tab: click scenes to jump
- World tab: Save / Load / Validate / Graph / Regen / Reset / Spawn
- Rules tab: assign per-tile interaction behavior
- Map tab: generate active-scene heightmaps with noise, rivers/lakes, mountain borders, bridge placement
- `F`: interact with current tile rule
- `Z` / `X`: previous/next construction tool page
- `Ctrl+Z` / `Ctrl+Y`: undo/redo
- `-` / `+`: brush size
- `[` / `]`: select transition destination
- Arrow keys over a transition: resize transition
- `,` / `.` / `;` / `/`: adjust transition spawn X/Y
- `P`: set current scene spawn
- `R`: reset current scene
- `N`: regenerate current scene
- `V`: validate world graph
- `G`: toggle graph panel
- `F5`: save world
- `F9`: load world

Current save path:

```text
workspace/saves/world.tworld
```

### 2.4 Current Prototype Map Constants

The current core source defines:

```rust
pub const TILE_SIZE: f32 = 32.0;
pub const MAP_W: usize = 48;
pub const MAP_H: usize = 32;
```

This means current scenes are 48×32 tiles in the prototype. This is useful for early testing, but the final editor should support variable scene sizes, multi-rectangle scene surfaces, and generated scene borders.

### 2.5 Current Core Data Types

The current `haven_core` source includes these major types:

```text
SceneId
SceneKind
SceneBiome
ZoneKind
TileCategory
TileAutoGroup
TileKind
TileInteraction
ObjectKind
PlacedObject
BuildTool
Transition
TavernMap
SceneMap
GameWorld
AssetRecord
```

Current scenes:

```text
Farmstead
TavernInterior
Cellar
GuestFloor
NorthRoad
SouthField
EastWoods
CaveMouth
CaveDepths
```

Current scene kinds:

```text
Exterior
Interior
Cave
```

Current biomes:

```text
Temperate
Coastal
Highlands
Cave
```

Current zones:

```text
None
Tavern
Kitchen
GuestRoom
Cellar
Greenhouse
Field
Cave
StaffOnly
```

Current tile categories:

```text
Terrain
Floor
Wall
Farm
Water
Special
```

Current autotile groups:

```text
Road
WoodFloor
StoneFloor
Water
Wall
Cliff
CaveWall
```

Current tiles:

```text
Grass
TallGrass
Sand
WetSand
PebbleShore
Road
StonePath
MountainPath
WoodFloor
PlankFloor
StoneFloor
BrickFloor
Wall
Cliff
MountainRock
Dirt
Bridge
CaveFloor
CaveWall
TilledSoil
Crop
GreenhouseZone
Water
ShallowWater
DeepWater
```

Current tile interactions:

```text
None
Forage
Hoe
Water
Harvest
Rest
Blocked
Enter
```

Current object kinds:

```text
Table
Chair
Bar
Keg
Bed
Fireplace
GreenhouseMarker
Tree
OreNode
Door
Stairs
CaveEntrance
```

Current build tools:

```text
Inspect
Floor(TileKind)
Object(ObjectKind)
Erase
Hoe
GreenhouseZone
Zone(ZoneKind)
Transition
```

### 2.6 Current Editor Model

The current `haven_editor` crate includes:

- editor palette tools
- cell inspection
- scene inspection
- world validation
- required zone/object validation
- transition walkability validation
- asset record validation

This is a strong starter foundation for a more formal editor architecture.

### 2.7 Current `haven_game` Runtime

The current `haven_game` source includes:

- Macroquad runtime window
- player movement
- camera logic
- scene drawing
- customer simulation placeholder
- tavern open/closed state
- time/clock rendering
- editor overlay tabs
- tool palettes
- rules tab
- map tab
- world tab
- inspector
- world graph
- validation panel
- undo/redo snapshots
- heightmap generation
- map brush operations
- bridge placement
- tile/object/zone/transition editing
- save/load to `.tworld`
- tile color/detail rendering
- simple autotile bevel/inner corner visuals
- lighting overlay
- object drawing and Y-sort helpers

### 2.8 Current Docs in Source Zip

Important docs already in the zip:

```text
docs/BUILD_AND_INSTALL.md
docs/WORKSPACE_LAYOUT.md
docs/design/cozy-aesthetic-roadmap.md
docs/design/in-game-editor-spec.md
docs/design/world-scene-map.md
docs/engineering/editor-asset-pipeline.md
docs/engineering/workspace-architecture.md
docs/sdk/ASSET_EDITOR_ROADMAP.md
docs/sdk/AUDIT_GAP_MATRIX.md
docs/sdk/CONTENT_CLONING_BLUEPRINTS.md
docs/sdk/DISCOVERY_WORKFLOW.md
docs/sdk/FEATURE_GUIDES.md
docs/sdk/SNIPPET_COOKBOOK.md
docs/sdk/TARGET_REGISTRY.md
SDK_FACTORY/
MODS/
SOFTWARE/tools/asset-kit/
```

### 2.9 Source Status Conclusion

The source zip is not a final Havenwild codebase yet, but it is a valuable prototype base because it already proves:

- Rust workspace structure
- Macroquad playable runtime
- in-game editor overlay
- scenes and transitions
- heightmap-backed scene generation
- world validation
- tile rules
- tile/object/zone editing
- save/load
- early asset/content-pack thinking
- tooling/modding docs that can be mined for editor patterns

Forward action: keep the prototype as the seed, but refactor naming, architecture, data schemas, and editor separation around the full Havenwild vision.

---

## 3. Product Identity and Pitch

### 3.1 Working Title

Primary working title:

```text
Havenwild
```

Fallback internal labels:

```text
Havenwild
Cozy Tavern Life Game
Tavern Workspace Prototype
```

### 3.2 Core Pitch

Run and expand a warm mountainside tavern in a coastal island world. Grow ingredients, cook regional cuisine, brew drinks, host travelers, hire and manage staff, build relationships with villagers and patrons, explore caves and islands, learn recipes, expand your property, and gradually turn your tavern into a beloved destination while uncovering the deeper history of the mountain, harbor, and surrounding islands.

### 3.3 Core Player Fantasy

- Owning a cozy tavern that feels alive.
- Expanding rooms and production areas over time.
- Serving meals and drinks made from personally grown, bought, fished, foraged, or mined resources.
- Meeting memorable patrons and villagers with portraits, schedules, relationships, and stories.
- Becoming part of a broader island trade/cuisine network.
- Exploring caves and coastal lands for resources and rare unlocks.
- Building a persistent character who can travel between saves/worlds.
- Playing solo or co-op from day one.

### 3.4 Tone

- Cozy but deep.
- Warm wood, brass, parchment, stone, hearthlight, mountain mist, harbor air.
- Relaxed sandbox pacing with optional challenge and optimization.
- Relationship-driven town life.
- Functional but readable systems.
- Progression without forcing sleep or daily resets.

---

## 4. Gameplay Pillars

### 4.1 Pillar 1 — Tavern Operation

The player runs a main tavern that can be opened whenever desired.

Key rules:

- Tavern operation is player-controlled, not locked to a fixed daily schedule.
- The tavern can operate 24 hours if staffed and supplied.
- Sleep is optional and mainly advances time faster.
- Background simulation continues to tally time, consume stock, process sales, and run staff tasks.
- Staff and managers can maintain operations while the player farms, explores, mines, fishes, shops, or visits other islands.

Tavern systems:

- tables and seating
- bar service
- kitchen/cooking
- brewing/drinks
- cellar/aging
- guest rooms/inn
- customer flow
- complaints
- cleanliness/dirt/trash
- reputation
- regional cuisine demand
- events/story moments
- staffing schedules
- inventory/storage/crafting access

### 4.2 Pillar 2 — Building and Expansion

The player expands the tavern and owned land over time.

Core expansion rule:

- Building expansion happens in **2×2 tile increments** for wall-push/open-space functions.
- Mid/late game unlocks additional expansion blocks to push rooms farther out.
- Tavern/building walls are 1 tile thick structurally.
- Wall visuals should read around 3 tiles tall.

Expansion targets:

- main tavern hall
- kitchen
- brewery
- cellar
- guest floor / inn rooms
- staff rooms
- office
- greenhouse
- off-kitchen herb garden
- outdoor bar/dining area
- storage rooms
- production rooms
- smithing/mining placeables, if placed at home

### 4.3 Pillar 3 — Farming, Herbs, Greenhouse, Soil

Farming is part of the tavern supply chain.

Rules:

- Soil quality matters.
- Tilling and fertilizing improves crop outcomes.
- Crops grow on short cycles: **2–7 in-game days maximum**.
- Crops may be one-time harvest or regrow for multiple harvests.
- Crops can grow year-round if conditions are correct.
- Greenhouse helps maintain year-round conditions.
- Greenhouse starts small, roughly 5×5, and can expand.
- Planters can be placed in greenhouse rooms.
- Trees can be planted in greenhouses/plots if space allows.
- Off-kitchen herb garden can eventually support all 20 herbs at home.

### 4.4 Pillar 4 — Seasons, Weather, Day/Night

Seasons are a core gameplay pillar.

Rules:

- In-game day target: about **1 real-world hour**.
- Sleep is optional.
- Seasons affect crops, visuals, fish, forage, weather, cuisine demand, travel, events, and NPC schedules.
- Rivers should visibly flow.
- Natural water should be fishable.
- Weather should affect ambience, customer patterns, crop watering, travel, and hazards.

### 4.5 Pillar 5 — World Exploration

The world contains one main continent/mainland and 9 surrounding islands.

Exploration includes:

- main city
- far villages
- roads
- harbors
- mountain pass tunnels
- caves
- fishing waters
- purchasable land plots
- regional cuisine discovery
- forage regions
- mines/caves
- NPC travel paths
- special item currency sources
- island-specific items/trees/crops

### 4.6 Pillar 6 — Relationships, Patrons, Villagers

The player builds Stardew-style relationships with patrons and villagers.

Relationship content includes:

- portraits
- dialogue states
- emotion portraits
- relationship stages
- quests
- gifts/favorites
- event scenes
- schedule-based appearances
- tavern patron behavior
- city/village routines
- romance/friendship optionality, if desired later

### 4.7 Pillar 7 — Regional Cuisine and Island Progression

Each island/city has its own cuisine identity.

Unlock channels:

- quests
- special item currency
- cave diving
- fishing
- relationship progression
- island travel
- purchasing local recipe books
- seasonal festivals

Cuisine affects:

- menus
- customer satisfaction
- island reputation
- staff skill relevance
- ingredient supply chains
- travel incentives
- late-game tavern branches

### 4.8 Pillar 8 — Staff and Management

Employees are central to automation.

Hireable roles:

- cook
- brewer
- farmer
- cleaner/server, likely needed
- manager
- later regional specialists

Existing confirmed roles:

- cook
- brewer
- farmer
- manager

Farmer can:

- tend crops
- feed/care for animals

Manager can:

- deal with customer complaints
- keep employees on task
- maintain schedules
- improve automation reliability
- improve customer satisfaction
- improve business performance while player is away

Staff traits affect:

- automation
- profit
- food quality
- service speed
- reputation
- morale
- shipping reliability
- cleanliness
- regional cuisine performance

Staff systems:

- tavern level determines employee capacity
- tavern level determines occupancy/customer limit
- staff skills/perks may exceed occupancy cap
- staff rooms boost morale
- work hours and priorities configurable through office desk GUI

### 4.9 Pillar 9 — Mining, Smithing, Protective Gear

Blacksmithing and armor/protective gear are part of cozy-adventure progression.

Gear use cases:

- mining efficiency
- cave hazards
- tool upgrades
- heat/cold/rain protection
- later combat if implemented
- deeper cave progression

Placeables/unlocks:

- ore storage
- furnace/smelter
- forge
- anvil
- quenching trough
- grindstone/sharpening wheel
- bellows
- casting molds
- ingot racks
- fuel storage
- workbench
- upgrade stations

Armor/protective gear should render through the same modular character compositor pipeline as clothing.

### 4.10 Pillar 10 — Multiplayer and Persistent Characters

Multiplayer is required from the foundation.

Rules:

- Multiplayer is not optional future scope.
- Hosting model is peer-to-peer/listen-server from the start.
- Single-player uses the same local hosted server path.
- Co-op uses a player client acting as authoritative host/server.
- Dedicated server can remain later optional mode.
- Characters are fully persistent profiles that can travel across saves/worlds.

Persistent characters carry:

- core level-ups
- appearance
- equipment/tools where allowed
- recipes/knowledge where allowed
- unlocked additions where allowed
- personal relationship/history flags as appropriate
- player identity/profile data

Guest-player land options still need final design:

1. Persistent guest plot remains in host save and host can maintain/control while guest is away.
2. Online-only guest plot appears/loads only when guest is online.
3. Hybrid leased/instanced guest plot model.

Anti-exploit rule:

- Guest plots must not become a simple way to permanently cheese free land expansion.
- Ownership, permissions, offline simulation, transfer rules, and save migration must be explicit.

### 4.11 Pillar 11 — Roguelike-Inspired Long-Term Progression

The project should fold roguelike-inspired systems into long-term progression, especially New Game+ and a portable character-wide skill tree.

Use roguelike elements without turning the cozy game into a punishing roguelike.

Possible systems:

- procedural cave expeditions
- run modifiers
- seasonal/world modifiers
- challenge contracts
- randomized rewards
- legacy unlocks
- meta-progression
- New Game+ world variants
- character-wide portable skill tree
- multiplayer-compatible expedition rewards

---

## 5. World and Setting

### 5.1 Macro World Layout

Current locked direction:

- one main continent/mainland
- 9 surrounding islands smaller than the main land
- multiple coastal cities
- multiple island cuisines
- each island has unique resources, vegetation, trees, NPCs, structures, and regional identity

### 5.2 Main Home Island

The player-owned tavern is just outside the main city on an island.

Home island features:

- center dominated by a mountain
- mountain has cave entrance
- tavern built into/against mountain base
- main city nearby
- harbor nearby
- east-west road across island between city and far villages
- north-south path/intersection near tavern
- approximately 20-tile path from main road up to tavern
- outdoor bar and indoor bar possible
- outside staircase or entrance to upstairs inn if NPC only needs a place to sleep
- mountain pass tunnels that can eventually be cleared/opened
- NPC travel spawn rates increase once tunnel travel is shortened

### 5.3 Player Property and Land Expansion

Starting/home region:

- mountainside tavern scene
- player-owned land around tavern
- can expand through parcel purchases from City Hall
- purchases can be whole plots or selected tiles
- owned scene can expand south/east/west
- scene/map borders can be pushed outward as land is purchased
- coastline/land can extend where needed
- southern path starts unowned/untraveled until purchased

Owned land supports:

- building
- gardens
- greenhouse
- placed objects
- terrain editing
- water placement
- fishable water installation
- shore/riverbank autotile generation

### 5.4 City Hall and Land Purchasing

City Hall should support:

- buying adjacent land parcels
- buying selected tiles
- seeing ownership overlays
- plot deed information
- expansion rules
- tax/permit hooks if desired later
- island property purchases

### 5.5 Other Island Properties

Players can buy land on other islands.

These plots are for:

- homes
- gardens
- greenhouses
- placed objects
- local farming/resources
- regional supply chain support

Earlier direction said only one main tavern, but later direction also allows late-game managed tavern branches. Reconciled rule:

- **First tavern is the primary hands-on home base.**
- Additional taverns/franchise branches are late-game systems only.
- Late-game branches are run by hired managers and exist to unlock additional island rewards/systems, not replace the main tavern loop.

### 5.6 Shipping/Parcel Service

The harbor should include a fictional parcel/shipping service inspired by FedEx/UPS/USPS-style delivery services, but parody-safe and original.

Needed:

- original name
- logo/colors
- shipping reliability stat
- package/parcel UI
- NPC employees
- region-to-region delivery rules
- staff/manager traits that affect shipping reliability

---

## 6. Camera, Screen Composition, and Rendering

### 6.1 Gameplay Camera

Target camera:

- fixed orthographic 2.5D depth view
- no isometric rotation
- no free camera in normal play
- player-facing zoom must show local gameplay, not entire scenes

Current prototype scene size:

```text
48×32 tiles at 32×32
```

Recommended gameplay view target:

```text
~36–40 tiles wide
~20–23 tiles tall
```

For a 1280×720 reference:

```text
1280 / 32 = 40 tiles wide
720 / 32 = 22.5 tiles tall
```

Use this as the default gameplay reference scale unless the editor/viewport has a zoom slider.

### 6.2 Cinematic Camera

Story-critical events may pan the camera cinematically.

Examples:

- new tunnel opens
- important NPC arrival
- festival event starts
- tavern expansion completes
- cave boss/major discovery
- ship arrives at harbor

Cinematic camera can temporarily show more scene context, but should return to fixed gameplay view.

### 6.3 Depth Simulation

The game should simulate depth through:

- sprite height
- wall visual height
- Y-sort draw order
- bottom-center anchors
- object footprints
- collision masks
- overhead/fringe layers
- wall fade masks when player walks behind structures
- heightmap-driven terrain bands
- shoreline/water edge layering
- shadows/ambient occlusion

### 6.4 Wall Fade Behind Player

When the player walks behind walls/trees/large objects:

- obstructing visuals should fade in a radius around the player
- collision remains intact
- fade mask should be object/layer metadata-driven
- editor should preview fade radius
- validation should mark assets that can occlude player but lack fade masks

### 6.5 Y-Sort and Anchors

Required standard:

- Objects use bottom-center or explicit sort anchor.
- Characters use bottom-center foot anchor.
- Foot collision is separate from visual sprite bounds.
- Large objects define:
  - visual bounds
  - footprint bounds
  - collision mask
  - interaction points
  - occlusion/fade region
  - Y-sort anchor

---

## 7. Worldgen and Scene Architecture

### 7.1 Scene-Based World

Maps are scene-based. Each scene uses layered tile rendering.

Scene types:

- exterior
- interior
- cave/dungeon
- city
- tavern rooms
- farm/owned land
- road scenes
- island plots
- harbor
- special event scenes

Scene records need:

- id
- name
- scene kind
- biome
- tile dimensions
- layers
- zones
- objects
- transitions
- spawns
- ownership data
- weather/season rules
- world-map coordinates/rectangles
- generated border rules
- save delta

### 7.2 Multi-Rectangle Scene Surfaces

Some scenes like cities and player-owned areas can be multiple world-map rectangles.

Needed system:

- scene can own multiple rectangles on world map
- each rectangle has local-to-world mapping
- transitions can connect to specific rectangle edges
- editor displays scene bounds over world map
- generated surfaces can extend scene borders when new parcels are bought

### 7.3 Adjacent Scene Border Treatment

Screen edges should never show void.

Use border simulation:

- forest edge if adjacent to woods
- cliff/mountain edge if adjacent to mountain
- water horizon/shoreline if adjacent to sea/lake
- road continuation if adjacent to road scene
- city silhouettes/fences if adjacent to city
- fields/hedges if adjacent to farmland

Adjacent scenes must share border treatment so the world feels continuous.

### 7.4 Ghost-Border Chunk Baking

For scene edges:

- bake ghost border tiles from adjacent scene metadata
- do not make them fully interactable unless loaded/owned
- use them for visual continuity
- avoid void edges
- support parallax/backdrop for deep forest/mountain/water edges

### 7.5 Heightmaps

Heightmaps should be used to produce more realistic world generation.

Heightmaps drive:

- shallow/deep water
- coastlines
- shore bands
- river banks
- cliffs
- highlands
- mountain borders
- roads/bridges
- cave entrances
- terrain moisture
- path slope hints

Current prototype already supports per-cell heights and map generation. Expand this into a formal height layer.

### 7.6 Layer Model

Adopt V005/V006-style split and layered map model:

```text
Terrain layer
Fringe layer
Overhead layer
Objects layer
Zones layer
Collision layer
Interaction layer
Water/fishing region layer
Height layer
Ownership/buildability layer
Lighting/ambience layer
Metadata markers layer
```

Minimum render layers:

```text
Ground/Terrain
Floor/Fringe
Objects under actor
Actors
Objects over actor
Overhead/Occluders
Lighting/Weather
UI/Editor overlays
```

### 7.7 Delta Save System

Use semantic/entity-ID-based delta saves.

Rules:

- generated scenes keep seed + generator version
- player/editor changes save as deltas
- object edits use stable entity IDs
- tile edits save exact layer changes
- generated base can be regenerated if generator version allows
- migration system updates old saves
- multiplayer changes are logged as authoritative operations

### 7.8 Worldgen Asset Coverage

Worldgen needs assets for:

- grass variants
- tall grass
- soil
- tilled soil dry/wet/fertilized
- crop states
- roads
- stone paths
- mountain paths
- sand
- wet sand
- pebble shore
- shallow water
- deep water
- animated shore foam
- river banks
- river flow frames
- bridges
- cliffs
- cave floors/walls
- mountain rock
- retaining walls
- forest borders
- weeds/flowers/clutter
- trees by growth stage and season
- fruit/nut trees
- logs/stumps/fallen trees
- rocks/ore nodes
- building walls/doors/windows
- city props
- tavern props
- dungeon/cave props

### 7.9 Ten-Island Style Direction

Worldgen should support 10 landmass styles: main continent/mainland plus 9 smaller islands.

Each island should define:

- biome/style identity
- city/town architecture
- cuisine
- vegetation
- tree set
- fruit/nut tree set
- crops/herbs
- forage items
- fish/water profile
- cave/resource profile
- NPC cultural flavor
- color/lighting palette
- terrain material set
- weather bias
- festival/quest themes

Each island needs at least:

- 2 wood tree types
- 2 fruiting/nut tree types
- unique items/resources
- unique NPC/building style direction

---

## 8. Terrain, Autotiles, Walls, and Water

### 8.1 Autotile Requirement

All wall-like and terrain-edge systems should support autotiling.

Autotile systems:

- terrain transitions
- shoreline/water edges
- river banks
- roads
- cliffs
- tavern/building walls
- dungeon walls
- cave walls
- city/interior walls
- cellar walls
- greenhouse walls
- retaining/mountain walls
- any other structural boundary

Autotile should handle:

- corners
- inner corners
- caps
- junctions
- doors/openings
- height/depth visuals
- collision
- fade masks
- attachment sockets
- transitions
- animation variants

### 8.2 Water Placement and Owned Land

Build mode can install water tiles on owned land.

Rules:

- water placement behaves like terrain/autotile brush
- banks/edges update automatically
- installed water can become fishable if valid size/depth/region rules are met
- water should support shallow/deep bands
- water should support animation
- water should support river flow direction where applicable
- editor should validate enclosed ponds, river connections, and shoreline continuity

### 8.3 Shorelines

Shorelines need:

- smooth natural-looking banks
- animated water
- splash/foam animation at shore
- wet sand transition
- pebble shore variants
- riverbank variants
- beach/wave variants
- editor 3×3 and larger preview
- validation for missing corners/edge cases

### 8.4 PCG Safeguards for Natural Shorelines

Safeguards:

- heightmap smoothing
- erosion pass
- edge noise pass
- minimum land/water blob size
- forbidden single-tile noise cleanup
- contour-to-autotile resolver
- beach band generator
- shore foam animation resolver
- bridge/path pass after water pass
- gameplay traversability check after water pass

### 8.5 Walls

Wall rules:

- structural thickness: 1 tile
- visual height: around 3 tiles minimum
- collision: foot/base collision, not full visual height
- player can pass behind some walls only where designed
- fade mask when player is behind
- doors/transitions define openings
- autotiling across all wall families
- wall caps/faces/corners/junctions required

Wall families:

- tavern wall
- city building wall
- house wall
- cellar wall
- greenhouse wall
- dungeon wall
- cave wall
- mountain retaining wall
- fence/low wall

### 8.6 Tile Rules

Current prototype includes tile interaction rules:

```text
None
Forage
Hoe
Water
Harvest
Rest
Blocked
Enter
```

Expand tile rules into metadata-driven behaviors:

- walkable
- blocks movement
- blocks build
- hoeable
- waterable
- harvestable
- fishable
- forageable
- rest point
- enter/transition
- hazard
- seasonal transform
- requires tool
- requires permission/ownership
- allowed zones

---

## 9. Objects, Footprints, Furniture, Trees, and Placement

### 9.1 Object Metadata Contract

Every object/placeable needs:

```text
id
name
category
visual asset references
footprint size
visual bounds
collision mask
interaction points
seat/attachment points if any
storage/crafting hooks if any
Y-sort anchor
placement rules
rotation/reflection support
occlusion/fade settings
seasonal variants if any
required zone/floor/room
validation rules
```

### 9.2 Footprint System

Apply footprint logic to:

- tables
- chairs/stools/benches
- bars
- counters
- stoves/ovens
- kegs/barrels
- beds
- fireplaces
- chests/storage
- crafting stations
- trees
- bushes
- foliage clumps
- ground clutter if it blocks or interacts
- rocks/ore nodes
- cave props
- city props
- doors/stairs/transitions
- outdoor dining areas

### 9.3 Table and Seating Rules

Corrected table seating spec:

- Do **not** model seats as left/right benches or fixed left/right seat slots.
- Tables expose generic adjacent-tile seat attachment points around their sides/perimeter.
- NPCs use generic seat attachments.

Seating capacity:

```text
Individual table = 1 seat
Small table      = 2 seats
Medium table     = 4 seats
Large table      = 6 seats
```

Build mode rules:

- Players may place more seating than current occupancy cap.
- Tavern level caps active customers, not physical seats.
- Extra seating is allowed and should show info/warning, not error.
- Chairs attached to tables must be manually removed by dragging/removing the chair asset.
- Seating attachments must validate reachability.

### 9.4 Furniture Footprint Examples

Examples:

- small table may occupy 2×2
- chairs/stools attached can expand used footprint to around 2×4
- stove/oven setup may be 2×3 each
- large table could visually seat 6 with perimeter seat attachments
- bar stools attach to bar interaction points

### 9.5 Trees and Foliage

Tree rules:

- Trees have growth stages:
  - sapling
  - young
  - mature
  - stump
  - chopped/fallen variant
- Normal mature trees should be up to about 5 tiles tall and 3×3 visually.
- Special trees can be 5×5 with a 2×2 base.
- Tree trunk collision may be 1 tile center base for most trees.
- Some trees use larger collision/footprint depending on trunk mass.
- Seasonal variants: spring/summer/autumn/winter.
- Preview should show all growth states.
- Trees can occlude player; use fade masks.
- Fully grown greenhouse trees need planter/room validation.

Foliage/ground clutter:

- purely decorative clutter can be non-blocking
- harvestable/forage clutter needs interaction metadata
- dense foliage may have soft collision/slow movement if desired
- foliage should be included in worldgen density rules

### 9.6 Placement Validation

Placement validation should check:

- footprint fits in scene
- collision does not block required paths
- object allowed in current zone
- object allowed on current tile/floor
- rotation supported
- attachments valid
- interaction points reachable
- required wall/floor/socket exists
- owned land requirement
- multiplayer permission
- not overlapping incompatible objects
- tavern service path remains valid
- staff path remains valid
- customers can reach seats/bar/rooms

---

## 10. Tavern Systems

### 10.1 Main Tavern Structure

The main tavern is the core home base.

Major spaces:

- tavern hall
- bar
- kitchen
- brewery
- cellar
- guest floor/inn
- office
- storage
- staff rooms
- greenhouse/herb garden
- outdoor bar/dining
- production expansions

### 10.2 Tavern Opening Rules

- Player can open/close tavern whenever desired.
- Tavern can operate 24 hours if staff and supplies allow.
- Sleep is optional.
- Staff schedules determine background operation quality.

### 10.3 Tavern Level and Occupancy

Tavern level controls:

- employee capacity
- active customer occupancy cap
- unlocks
- reputation bracket
- advanced rooms/expansions
- maybe menu size/order volume

Occupancy cap formula should include:

```text
tavern level base cap
+ staff skill bonuses
+ manager bonuses
+ event modifiers
+ furniture/comfort upgrades
+ reputation modifiers
+ other occupancy upgrades
```

Physical seats can exceed occupancy cap.

### 10.4 Office Desk GUI

Office desk unlocks staff and business management.

GUI functions:

- employee list
- roles
- priorities
- schedules/work hours
- pay/wages
- morale
- skills/perks/traits
- complaints log
- tavern open/closed automation rules
- menu assignments
- production queues
- manager delegation settings
- reports/profit/reputation

### 10.5 Staff Rooms

On-site employee rooms:

- can be built/unlocked
- boost staff morale
- may improve retention/performance
- may unlock overnight/24-hour shifts
- require beds/storage/comfort objects

### 10.6 Customer Complaints

Complaint categories:

- slow service
- unavailable item
- poor food quality
- dirty tavern
- no seats
- noise/crowding
- wrong cuisine expectations
- room quality if staying overnight
- staff mistake

Manager skill affects complaint handling.

### 10.7 Menu and Stock

Menu should connect to:

- available recipes
- pantry/storage
- staff cooking skill
- kitchen equipment
- regional cuisine demand
- customer preferences
- ingredient quality
- seasonality

### 10.8 Production

Production systems:

- brewing
- cooking
- aging cellar
- preserves/pickles maybe later
- smithing/tool upgrades
- herb drying/mixing maybe later

Production needs:

- recipe input/output
- timers
- station assignment
- quality tiers
- staff automation
- storage access
- validation in editor

---

## 11. Crafting, Storage, Inventory, and Recipes

### 11.1 Inventory Model

Needed inventories:

- player backpack
- hotbar/action bar
- tavern storage
- kitchen storage
- cellar storage
- greenhouse/farm storage
- staff-held temporary inventory
- merchant/shop inventory
- shipping depot inventory
- multiplayer personal stash
- guest/player profile inventory

### 11.2 Connected Storage

Storage should support connected crafting/storage networks where appropriate.

Examples:

- kitchen scans food ingredients
- brewery scans brewing ingredients
- cellar scans aging products
- smithy scans ore/ingots/fuel
- staff can pull from assigned storage

### 11.3 Filtered Station Inventory

Crafting/interactable stations should show filtered inventories relevant to that station.

Examples:

- cooking stations show only cooking-relevant materials
- brewing stations show brewing ingredients
- smithing stations show ore, ingots, fuel, molds, tools
- seed station shows seeds, fertilizer, soil amendments

### 11.4 Recipes

Recipe records need:

```text
id
name
category
regional cuisine tag
ingredients
allowed substitutes
station requirements
skill requirements
unlock requirements
cook/brew/craft time
quality rules
output item(s)
seasonal availability
staff automation tags
UI icon
```

### 11.5 Special Item Currency

Special item currency can unlock:

- regional recipes
- rare seeds
- island permits
- cave unlocks
- decorative items
- staff contracts
- upgrades
- New Game+ modifiers

Sources:

- quests
- cave diving
- fishing
- festivals
- relationship milestones
- island achievements

---

## 12. NPCs, Dialogue, Portraits, Relationships, and Events

### 12.1 NPC Identity

NPC records need:

```text
id
name
role
home island/city
schedule
portrait set
sprite set
relationship data
dialogue profile
quests
shop/service data
preferences
regional cuisine tags
traits
story flags
```

### 12.2 Dialogue UI

When the player talks to characters:

- a conversation UI appears
- character portrait shown
- each individual character has its own portrait set
- portrait changes by emotion, relationship state, quest state, and context

Dialogue portraits must be metadata-backed and connected to:

- NPC definitions
- schedules
- relationships
- quests
- cutscenes
- editor preview tools
- validation tools

### 12.3 Portrait Set Contract

Portrait metadata:

```text
npc_id
portrait_sheet
cell_size
anchor/padding
emotions
relationship variants
quest variants
seasonal outfits if any
fallback portrait
license/source status
```

Common emotions:

- neutral
- happy
- annoyed
- sad
- surprised
- thoughtful
- embarrassed
- angry
- worried
- proud

### 12.4 Relationship System

Relationship variables:

- friendship level
- trust
- patron loyalty
- gift history
- quest history
- tavern satisfaction
- known preferences
- regional reputation
- personal flags

Relationships unlock:

- recipes
- discounts
- quests
- personal events
- staff recruits
- island information
- special currency
- property opportunities

### 12.5 Event System

Events need:

- trigger conditions
- location/scene
- camera pan markers
- participants
- dialogue/cutscene script
- rewards
- relationship changes
- one-shot/repeat rules
- multiplayer synchronization rules

---

## 13. Character Creator and Animation

### 13.1 Character Creator

Support male and female base characters with modular editor-driven layers:

- base body
- hair styles
- hair colors
- beard/facial hair for male characters
- clothing
- eyes
- nose
- mouth
- shoes
- gloves
- accessories
- armor/protective gear
- tools/equipment overlays

Base bodies should remain:

- bald
- no-face
- no-hair
- featureless source assets

Visible identity comes from composited layers.

### 13.2 Animation Base Contract

First locked asset:

```text
player_base_walk_8dir.png
64×96 frame cell
8 directions
8 walk frames per direction
512×768 sheet
bottom-center foot anchor
small foot collision mask
```

### 13.3 Required Animation Set

Needed character animation specs:

- idle 8-dir
- walk 8-dir
- run 8-dir
- sit
- sleep
- carry
- serve mug/plate
- use tool
- fish
- mine
- chop
- hoe
- water
- cook
- wash dishes
- interact
- emote
- cutscene poses
- NPC-only variants
- staff work animations

### 13.4 Modular Animation Consistency

To guarantee uniformity:

- all layers use same frame grid
- all layers share same anchor metadata
- all layers share direction/frame order
- all tools/equipment use socket metadata
- compositor validates missing frames
- editor previews all layers together
- export step bakes runtime atlases if desired
- source layer files remain editable

---

## 14. UI / HUD / GUI Direction

### 14.1 Art Direction

Target visual direction:

- cozy polished pixel-art / painted-pixel hybrid
- warm wood
- brass accents
- parchment panels
- carved tavern/mug/leaf motifs
- readable pixel/serif fantasy fonts
- soft warm lighting
- tactile buttons
- rounded but still pixel-readable panel edges

### 14.2 Core HUD

HUD should include:

- hotbar
- time
- season
- weather
- date/day
- quest tracker
- money/reputation maybe compact
- tavern open/closed status
- staff alert markers

### 14.3 Inventory GUI

Inventory should include:

- player inventory grid
- hotbar
- clothing/armor paper-doll slots
- tool slots
- currency display
- item details
- filters/sorting
- storage transfer

### 14.4 Build Mode GUI

Build mode should show:

- grid
- brush preview
- 2×2 expansion preview
- wall push-out preview
- terrain/water autotile preview
- object footprints
- collision overlays
- interaction points
- warnings/errors
- owned land boundaries
- cost/material preview

### 14.5 Staff Scheduling GUI

Office staff GUI should show:

- schedule grid
- staff roles
- task priorities
- morale
- traits
- skill levels
- pay
- automation status
- alerts/complaints

### 14.6 Storage / Chest / Cargo Manifest UI

Storage UI should support:

- searchable alphabetical list
- item grid/list toggle
- click-to-take
- drag-and-drop
- filters
- station-relevant filtered view
- connected storage indicator

Cargo/ledger style:

- parchment/ledger background
- player inventory
- crafting grid
- crafting output
- connected storage on right

### 14.7 Workstation GUIs

Needed workstation GUI groups:

- bar
- kitchen
- brewery
- cellar
- merchant
- storage/chest
- greenhouse/planters
- smithing
- smelter
- forge
- anvil
- quenching
- grindstone
- tool/armor upgrade

### 14.8 UI Widgets Needed

Standard UI widget set:

- buttons
- icon buttons
- radio buttons
- checkboxes
- sliders
- dropdowns
- text fields
- number fields
- tabs
- accordions
- tooltips
- modal dialogs
- confirm/warning dialogs
- inventory grids
- searchable lists
- scroll panels
- draggable item slots
- color/palette pickers
- timeline/frame scrubber
- property inspector rows
- validation badges
- progress bars
- schedule grid
- graph nodes/links

---

## 15. Main Editor System

### 15.1 Editor Philosophy

The editor should be straightforward, user-friendly, and logically grouped while still tying systems together cohesively.

Main editor goals:

- one cohesive editor shell
- properly grouped systems
- project browser
- asset browser
- scene/world editor
- pixel editor
- inspector
- validation panel
- console/log panel
- play/test controls
- tooltips and help menus
- tutorials
- undo/redo across authoring actions
- autosave/recovery
- metadata-backed editing

### 15.2 Main Editor Workspaces

Recommended top-level editor workspaces:

1. World & Scene Editor
2. Tile/Autotile/Water Editor
3. Object & Furniture Editor
4. Pixel/Animation Editor
5. Character/NPC Editor
6. Dialogue/Quest/Event Editor
7. Recipe/Item/Crafting Editor
8. Tavern/Staff/Business Editor
9. Worldgen/Biome Editor
10. Validation/Build/Packaging

Keep targeted editors under 10 major areas where possible.

### 15.3 Editor Responsibilities

The editor must support:

- create/open projects
- scene authoring
- map painting
- worldgen preview/regeneration
- heightmap editing
- tile atlas editing
- autotile rules
- water/shoreline preview
- object placement
- footprint/collision editing
- interaction map editing
- transition editing
- NPC placement/schedules
- dialogue portraits and lines
- quests/events
- recipes/items
- staff schedules
- UI skin preview
- multiplayer permissions/world settings
- validation and error repair
- asset import/export
- hot reload
- runtime test/play mode

### 15.4 In-Game Overlay Editor

The in-game editor overlay is for live iteration.

Current prototype already has:

- minimized toolbar
- tabs for tiles/objects/zones/world/rules/map
- save/load/validate/graph/regenerate/reset/spawn
- brush sizing
- undo/redo
- tile rules
- heightmap generation
- world graph panel

Forward overlay should include:

- quick paint/edit tools
- inspect tile/object/NPC
- toggle collision/interaction overlays
- place/resize transitions
- edit object footprints at runtime only in dev mode
- test NPC/customer paths
- spawn test customers/staff
- simulate tavern open/closed
- run scene validation
- quick save/load
- send selected issue to main editor

### 15.5 Web Editor Systems

Web editors can help with lightweight workflows.

Possible web editors:

- content pack editor
- item/recipe editor
- NPC/dialogue editor
- asset metadata editor
- documentation/wiki/editor help
- validation dashboards
- maybe pixel preview but not primary pixel editing

Web editor architecture can mimic existing open-source patterns but should not dictate game architecture.

### 15.6 Editor Tooltips and Tutorials

Needed user-help systems:

- contextual tooltips
- beginner tutorials
- per-tool help panel
- validation explanation links
- examples/templates
- warning severity system
- onboarding checklist
- “why invalid?” placement explanation
- searchable help index

---

## 16. Pixel Editor System

### 16.1 Role

The pixel editor is a first-class core tool, not secondary.

It supports:

- tiles
- sprites
- animations
- brushes
- smudge/blend tools
- palettes
- in-game asset authoring
- atlas previews
- metadata editing

### 16.2 Minimum Pixel Editor Features

Needed:

- palette swatch manager
- brush tools
- pencil/eraser/fill
- line/rectangle/circle tools
- selection/copy/paste
- rotate/mirror selection
- transparency support
- layers if possible
- animation timeline
- onion skin for animations
- sprite slicing grid
- 3×3 tile preview
- autotile preview
- water/shoreline animated preview
- character layer preview
- paper-doll compositor preview
- export/import to PNG + metadata

### 16.3 Atlas Grid Realignment Mode

Explicit locked requirement:

The pixel editor must include **Atlas Grid Realignment Mode** for generated/offset atlas correction.

It should allow moving the whole logical atlas grid over the image to fix cell alignment discrepancies without moving pixels.

Safeguards:

- deliberate mode toggle
- warning/confirm flow
- preview
- undo/redo
- non-destructive metadata-backed offset changes
- cannot be activated accidentally
- clear “grid moved, pixels unchanged” messaging

### 16.4 Generation Safeguards

AI-generated or procedurally generated sheets may struggle with:

- perfect 32×32 alignment
- seamless tiling
- autotile edge/corner completeness
- transparent background
- consistent animation frames
- consistent object scale
- avoiding labels/text
- keeping groups separate

Editor safeguards:

- atlas slicing validation
- grid realignment
- cell bounds overlay
- transparent-background checker
- tile seamless preview
- 3×3/5×5 repeat preview
- autotile completeness checker
- duplicate/missing corner detection
- animation frame consistency validator
- scale ruler/anchor checks
- object footprint preview
- batch crop/trim with anchor preservation
- metadata repair suggestions

### 16.5 External Tool Support

Support import/export flows for:

- Pixelorama
- LibreSprite
- Aseprite, if user owns it
- Tiled
- LDtk

Do not build a full Aseprite replacement first. Build project-specific tools first.

---

## 17. Asset Pipeline

### 17.1 Asset Families Needed

Environment:

- terrain
- water
- shorelines
- roads
- walls
- cliffs
- caves
- foliage
- trees
- flowers
- clutter
- weather effects

Tavern objects:

- tables
- chairs
- stools
- benches
- bar
- counters
- shelves
- mugs/plates
- kegs/barrels
- beds
- fireplaces
- décor
- lights

Farming/greenhouse:

- crops
- crop stages
- herbs
- seeds
- planters
- irrigation objects
- compost/fertilizer
- greenhouse walls/windows

Characters:

- base bodies
- hair
- facial hair
- clothing
- shoes/gloves
- armor/protective gear
- tools
- NPC sprites
- portrait sets

Effects:

- water splash
- smoke
- fire
- cooking steam
- dust
- leaf fall
- snow/rain
- tool swing
- mining spark

UI:

- HUD
- hotbar
- inventory
- build mode
- schedule GUI
- storage/merchant windows
- dialogue windows
- crafting workstations
- smithing panels

### 17.2 Asset Manifest Example

```json
{
  "schema": "hh.asset.v1",
  "id": "wood_floor_basic",
  "source": "assets/source/tiles/tavern_tiles.pxo",
  "output": "assets/processed/sprites/tavern_tiles.png",
  "license": "Original / Shifty",
  "author": "Shifty",
  "tags": ["floor", "wood", "tavern"],
  "tileSize": [32, 32],
  "animations": []
}
```

### 17.3 Runtime Asset Records

Current prototype `AssetRecord` contains:

```text
id
kind
source
output
license
author
tags
```

Expand into formal schemas per asset class.

### 17.4 Reference Assets

Uploaded `25D assets examples.zip` should be treated as reference library only.

Use it to study:

- coverage
- sheet structure
- animation organization
- terrain/prop categories
- assembly patterns
- style references

Do not use for:

- direct runtime import
- tracing
- pixel copying
- palette lifting
- shipping

### 17.5 AI-Generated Drafts

Generated images can be used as original production-direction drafts/reference sheets, but must still be:

- audited
- cleaned/cropped
- metadata-backed
- validated in editor
- tested in scenes
- possibly redrawn/standardized

Do not attempt one giant asset pack.

Recommended vertical slices:

1. terrain/foliage
2. tavern props
3. item icons
4. animals
5. smithy props
6. UI widgets
7. character layers
8. NPC portraits

---

## 18. Runtime Architecture

### 18.1 Current Architecture

Current working crates:

```text
crates/haven_core
crates/haven_game
crates/haven_editor
```

Current role:

- `haven_core`: data model and generation helpers
- `haven_game`: playable Macroquad runtime and editor overlay
- `haven_editor`: validators and editor helper model

### 18.2 Recommended Forward Crate Architecture

Potential future crate split:

```text
crates/haven_core          pure data types, ids, schemas, math, time
crates/haven_world         scenes, maps, worldgen, heightmaps, transitions
crates/haven_assets        asset metadata, manifests, import/export
crates/haven_render        2.5D rendering, layers, camera, lighting
crates/haven_sim           tavern, customers, staff, farming, economy
crates/haven_net           listen-server networking, replication, authority
crates/haven_save          save/load, deltas, migrations
crates/haven_editor        editor core, commands, validation, undo/redo
crates/haven_game          playable client/runtime
crates/haven_tools         CLI tools, validators, asset processors
```

This can be introduced gradually. Do not over-split before the prototype stabilizes.

### 18.3 Runtime Client/Server Model

Multiplayer foundation:

```text
single-player = local hosted server + local client
co-op         = host client runs authoritative listen server + guest clients
future        = optional dedicated server
```

Authoritative server owns:

- world state
- time/calendar
- tavern simulation
- inventory/storage
- crafting/production
- NPC/customer simulation
- player permissions
- build actions
- economy
- scene deltas

Clients own:

- input
- rendering
- UI
- prediction where safe
- editor requests if authorized

### 18.4 Save Architecture

Save layers:

- world seed/generator config
- base generated scene definitions
- semantic deltas
- entities and stable IDs
- player profiles
- NPC relationship states
- tavern business state
- inventories/storage
- production queues
- staff schedules
- quest flags
- multiplayer permissions
- migration version

### 18.5 Deterministic Systems

Determinism is important for:

- worldgen
- multiplayer replication
- save migration
- validation
- tests
- background simulation

Use seed-driven generation and operation logs for authoritative changes.

### 18.6 Scripting

Implement a straightforward natural-language scripting layer for game functions and logic.

Important rule:

- Natural language descriptions should compile/translate into deterministic project logic, events, commands, or visual graphs.
- Do not rely on vague runtime interpretation.

Candidate scripting support:

- Rhai for Rust-native embedded scripts
- command graph / visual node graph
- event DSL for quests/dialogue/cutscenes
- validated editor-generated scripts

---

## 19. Multiplayer Architecture

### 19.1 Required From Foundation

Multiplayer must be built into the architecture early.

Core features:

- player-hosted listen server
- join/invite system later
- shared world state
- synchronized tavern operation
- synchronized build mode
- synchronized storage/inventory
- permissions
- scene/chunk persistence
- synchronized NPCs/customers/staff
- conflict resolution
- save migration

### 19.2 Authority Rules

Server authoritative for:

- item creation/destruction
- money/reputation
- land ownership
- build placement
- NPC state
- production/crafting completion
- farming growth
- relationship state in host world
- cave/dungeon reward rolls

Client may predict:

- local movement
- UI feedback
- placement preview
- visual effects

### 19.3 Permissions

Needed permissions:

- build/edit land
- access storage
- spend money
- open/close tavern
- manage staff
- edit schedules
- buy land
- start events/quests
- use office desk
- invite/kick players

### 19.4 Persistent Character Travel

Players can bring characters between saves.

Need import policy:

- what equipment transfers
- what recipes transfer
- what currency transfers
- what relationship state transfers
- what level/skills transfer
- how host world rules restrict imported items
- exploit prevention

### 19.5 Guest Plot Models

Option A: Persistent guest plot

- guest plot remains in host world
- host can maintain while guest away
- highest persistence
- highest exploit risk

Option B: Online-only guest plot

- plot appears/loads only while guest online
- lower exploit risk
- less cozy persistence

Option C: Hybrid leased/instanced plot

- guest has a tied plot record
- host controls access rules
- plot may visually persist but production/offline gains are limited
- likely best compromise

Need final spec.

---

## 20. Progression

### 20.1 Tavern Progression

Progression sources:

- reputation
- level
- expansion permits
- recipes
- staff quality
- room quality
- cuisine mastery
- customer satisfaction
- island reputation

Unlocks:

- more customers
- more staff slots
- more room types
- higher-tier equipment
- greenhouse expansion
- larger cellar
- upstairs inn
- outdoor dining
- advanced production
- office tools
- manager automation

### 20.2 Character Progression

Character progression:

- portable character profile
- skills
- recipes/knowledge
- tool proficiency
- crafting/smithing skill
- cooking/brewing skill
- farming/gathering/fishing/mining skill
- social/business skills
- New Game+ meta tree

### 20.3 Skill Tree

Skill tree should be character-wide and portable where safe.

Possible branches:

- Tavernkeeper
- Cook
- Brewer
- Farmer
- Angler
- Miner
- Smith
- Explorer
- Social/Negotiation
- Manager/Leadership
- Island Cuisine Specialist

### 20.4 New Game+

New Game+ should preserve cozy progression and replayability.

Possible unlocks:

- legacy skill points
- alternate world seeds
- island modifier packs
- seasonal challenge modifiers
- cave expedition rules
- rare recipe variants
- starting perks
- cosmetic legacy items
- inherited business plaques/trophies

---

## 21. Editor Data and Validation

### 21.1 Validation Philosophy

The editor should prevent broken content without blocking creative placement unnecessarily.

Validation severities:

- Info: allowed but may be inefficient
- Warning: likely issue but valid
- Error: invalid or broken
- Blocker: cannot save/build/run

Example:

- Extra seats above occupancy cap = Info/Warning, not Error.
- Unreachable required transition = Error.
- Missing asset license metadata = Error or Blocker depending release mode.

### 21.2 Validation Areas

Validate:

- scene bounds
- tile layers
- autotile completeness
- water/shoreline continuity
- collisions
- object footprints
- interactions
- transitions
- pathfinding
- room requirements
- tavern service flow
- staff workflow
- NPC schedules
- dialogue references
- portrait references
- item/recipe references
- animation frame completeness
- atlas grid alignment
- multiplayer permissions
- save schema version
- asset license/source metadata

### 21.3 Editor Commands

All editor edits should be command-based for undo/redo.

Command examples:

- paint tile
- erase tile
- place object
- move object
- rotate object
- remove object
- edit footprint
- set collision
- set interaction
- create transition
- resize transition
- edit spawn
- assign zone
- generate scene
- apply height brush
- place water
- add parcel
- edit NPC schedule
- edit recipe
- edit dialogue node

### 21.4 Logs

Logging should capture:

- validation reports
- editor command history
- save/load errors
- asset import errors
- runtime exceptions
- multiplayer desync warnings
- generation seeds and versions
- build/package outputs

---

## 22. World/Scene Save Format Direction

### 22.1 Current Prototype

Current prototype serializes to `.tworld` lines and loads from:

```text
workspace/saves/world.tworld
```

### 22.2 Forward Save Schema

Move toward structured schema format:

```text
world.hhworld
scenes/*.hhscene
assets/*.hhasset.json
profiles/*.hhprofile
```

Or use a single packed save with internal files:

```text
save_name.hhsave
  manifest.json
  world.json
  scenes/*.json
  entities/*.json
  players/*.json
  deltas/*.json
```

### 22.3 Scene Schema Sketch

```json
{
  "schema": "hh.scene.v1",
  "id": "home_farmstead",
  "name": "Home Farmstead",
  "kind": "exterior",
  "biome": "temperate_coastal",
  "size": [96, 64],
  "worldRects": [],
  "layers": {
    "height": "height_u8.bin",
    "terrain": "terrain_layer.bin",
    "fringe": "fringe_layer.bin",
    "overhead": "overhead_layer.bin",
    "collision": "collision_layer.bin",
    "interaction": "interaction_layer.bin"
  },
  "objects": [],
  "zones": [],
  "transitions": [],
  "spawns": [],
  "ownership": [],
  "generator": {
    "seed": 12345,
    "version": "worldgen.v1"
  }
}
```

---

## 23. Rust Systems and Crates to Consider

### 23.1 Current Dependency

Current prototype uses:

```text
macroquad = 0.4
```

### 23.2 Helpful Rust Systems

Likely useful long-term categories:

- ECS: Bevy ECS, hecs, specs, shipyard, or custom lightweight ECS
- serialization: serde, ron, bincode, postcard
- scripting: rhai
- pathfinding: pathfinding crate or custom grid/A* implementation
- noise/worldgen: noise, rand, rand_chacha
- networking: renet, bevy_replicon patterns, quinn, tokio, laminar alternatives
- UI/editor: egui, iced, floem, Tauri/web, custom Macroquad/editor UI, or retained immediate hybrid
- asset processing: image, asefile, ldtk_rust, tiled parser
- hot reload/file watch: notify
- validation: schemars/jsonschema
- command CLI: clap, xshell, xtask
- logging: tracing, tracing-subscriber
- diagnostics: thiserror, anyhow, miette

### 23.3 xtask

`xtask` would benefit the project.

Use it for:

- build
- run
- validate assets
- generate schemas
- pack content
- run tests
- bake atlases
- check licenses
- migrate saves
- run editor
- generate docs

Recommended root command shape:

```text
cargo xtask run
cargo xtask editor
cargo xtask validate
cargo xtask bake-assets
cargo xtask package
cargo xtask migrate-saves
cargo xtask docs
```

---

## 24. Current Source Legacy/SDK Material

### 24.1 Modding SDK Material

The source zip contains substantial Travellers Rest modding SDK work:

- BepInEx plugin docs
- target registry
- feature guides
- content cloning blueprints
- asset editor roadmap
- mod folders for KegsPlus, NPCPlus, EmployeesPlus, GreenhouseExpansion, HavenwildPrototype
- SDK factory templates
- logging/capture standards

For Havenwild, treat these as:

- workflow references
- validation/checklist references
- content-pack architecture references
- logging/capture references
- not final game runtime architecture

### 24.2 Useful Ideas from SDK Material

Adapt:

- target registry concept → project feature registry
- discovery workflow → asset/content discovery/import audit
- validation checklists → release gates
- content pack schema → mod/content pack system
- asset editor roadmap → internal Havenwild asset editor
- logging/capture standard → editor/runtime QA capture tools

Do not carry over:

- direct Unity/BepInEx dependencies
- Travellers Rest-specific target names
- external game assets
- direct mod cloning assumptions

### 24.3 Legacy Platformer

`legacy/havenwild_platformer` exists and should remain archived. It is not the active direction.

---

## 25. Content Packs and Modding

### 25.1 Content Pack Direction

Content packs should define:

- items
- recipes
- sprites
- prefabs/placeables
- NPCs
- dialogue
- shops
- regions/biomes
- quests
- UI skins maybe later

### 25.2 Content Pack Schema Example

```json
{
  "schema": "hh.content_pack.v1",
  "id": "shifty.example.drinks",
  "name": "Example Drinks",
  "version": "0.1.0",
  "items": [
    {
      "id": "blueberry_ale",
      "displayName": "Blueberry Ale",
      "description": "A fruity tavern ale.",
      "icon": "sprites/blueberry_ale.png",
      "stackSize": 99,
      "price": 120
    }
  ]
}
```

### 25.3 Modding Safety

- Validate content packs before load.
- Keep content removable.
- Avoid save corruption if content removed.
- Use stable IDs.
- Warn on missing dependencies.
- Use release-mode license checks.

---

## 26. Build and Tooling

### 26.1 Current Build

Current source supports:

```powershell
.\tools/build/Build.ps1
cargo run -p haven_game
```

### 26.2 Recommended Build Workflow

Forward:

```text
cargo check --workspace
cargo test --workspace
cargo run -p haven_game
cargo run -p haven_editor_native
cargo xtask validate-assets
cargo xtask package-dev
```

### 26.3 Packaging

Needed packaging outputs:

- dev build
- editor build
- runtime game build
- content pack bundles
- validation reports
- asset catalog
- source-of-truth docs

---

## 27. Testing and QA

### 27.1 Automated Tests

Test categories:

- tile/autotile resolver tests
- wall/corner/junction tests
- water/shoreline tests
- pathfinding tests
- object placement tests
- table seating attachment tests
- transition graph tests
- save/load roundtrip tests
- migration tests
- worldgen deterministic tests
- multiplayer authority tests
- inventory/crafting tests
- staff schedule simulation tests
- crop growth tests
- recipe validation tests
- asset metadata validation tests

### 27.2 Manual Validation

Manual validation scenes:

- basic tavern operation
- tavern expansion
- kitchen workflow
- table seating and NPC use
- greenhouse planting
- water placement/fishing
- cave entrance/transition
- city transition
- road border scene
- tree occlusion/fade
- large furniture placement
- multiplayer co-op build action
- persistent character import

### 27.3 Editor Validation UX

Validation panel should show:

- issue title
- severity
- scene/object/asset link
- explanation
- suggested fix
- auto-fix button where safe
- documentation/help link

---

## 28. Critical Gaps Remaining

### 28.1 Project Identity Refactor

Needed:

- rename prototype from Havenwild Prototype to Havenwild or chosen title
- rename crates
- rename docs/folders
- separate reference/SDK leftovers
- define final root layout

### 28.2 Runtime Architecture Refactor

Needed:

- split runtime/editor/core cleanly
- prepare listen-server model
- define authoritative state model
- define save schemas
- migrate `.tworld` prototype toward structured formats

### 28.3 Scene/Layer Model Finalization

Needed:

- final layer stack
- scene schema
- multi-rectangle scene support
- world map coordinates
- border/ghost-bake spec
- delta-save spec

### 28.4 Autotile and Asset Contracts

Needed:

- terrain autotile schema
- wall autotile schema
- water/shoreline animation schema
- object footprint schema
- collision/interaction schema
- generated atlas validation rules

### 28.5 Pixel Editor Implementation Spec

Needed:

- tool list
- UI layout
- atlas grid realignment mode
- animation timeline
- 3×3/5×5 preview
- export/import formats
- metadata linking

### 28.6 Multiplayer Foundation Spec

Needed:

- host server lifecycle
- connection flow
- player profile import
- world authority
- permissions
- conflict resolution
- guest plot model decision
- save migration

### 28.7 NPC/Dialogue/Portrait System

Needed:

- NPC schema
- portrait schema
- dialogue node schema
- schedule schema
- relationship schema
- quest/event schema
- cutscene/camera marker schema

### 28.8 Staff and Business Simulation

Needed:

- staff schema
- traits/perks
- schedule simulation
- manager AI
- complaints
- task assignment
- tavern level/occupancy formula
- morale/staff rooms

### 28.9 Farming and Seasons

Needed:

- crop schema
- soil quality model
- fertilizer model
- water/rain rules
- season compatibility
- greenhouse conditions
- farm staff automation

### 28.10 Regional Cuisine and Islands

Needed:

- 10-island biome/cuisine matrix
- recipe unlock matrix
- local item lists
- tree/crop/forage/fish lists
- city/town architecture notes
- NPC roster per island

### 28.11 Art/Asset Vertical Slice

Needed first slice:

- common base terrain/water/autotile sheets
- home island biome set
- tavern wall/floor/object set
- player base walk sheet
- first NPC portrait/sprite pair
- UI kit MVP

### 28.12 Editor Usability

Needed:

- main editor shell
- clear panels
- tooltips/help
- tutorials
- validation panel
- undo/redo command bus
- asset browser
- inspector
- console/logs

---

## 29. Recommended Immediate Roadmap

### Phase 0 — Preserve and Rename

- archive current zips
- create project root decision
- rename visible project identity to Havenwild
- keep legacy/modding materials in reference/archive folders
- document source provenance

### Phase 1 — Stabilize Current Rust Prototype

- ensure `cargo check --workspace` passes
- ensure `cargo run -p haven_game` runs
- verify save/load works
- verify in-game editor overlay works
- add validation output export
- add logs

### Phase 2 — Formalize Core Schemas

- scene schema
- tile schema
- autotile schema
- object footprint schema
- asset metadata schema
- NPC schema
- item/recipe schema
- save schema draft

### Phase 3 — Editor Foundation

- command bus
- undo/redo model
- inspector data binding
- validation panel
- scene/object/tile editing with metadata
- asset browser
- pixel editor MVP shell

### Phase 4 — Worldgen and Asset Pipeline

- heightmap worldgen pass
- water/shoreline resolver
- road/bridge pass
- border ghost-bake
- home island biome set
- atlas validation
- generated asset cleanup workflow

### Phase 5 — Tavern Core Loop

- open/close tavern
- customers enter/seat/order/pay/leave
- tables/seating attachments
- bar/kitchen service
- storage/menu linkage
- basic reputation/money
- staff stub

### Phase 6 — Farming/Greenhouse/Recipes

- crop schema
- crop growth
- soil/water/fertilizer
- greenhouse conditions
- ingredient-to-recipe loop
- cooking stations

### Phase 7 — Staff/Manager Simulation

- staff roles
- schedules
- priorities
- manager behavior
- complaints
- morale
- staff rooms
- occupancy bonuses

### Phase 8 — NPC/Dialogue/Portraits

- NPC definitions
- portrait set support
- dialogue UI
- relationship flags
- quest/event hooks
- first city/tavern NPC set

### Phase 9 — Multiplayer Foundation

- local hosted server path
- listen server
- client join
- player profile persistence
- build/action authority
- save migration
- permissions

### Phase 10 — Expansion and Island Progression

- City Hall purchases
- multi-rectangle scenes
- other island plots
- regional cuisines
- cave progression
- New Game+ hooks

---

## 30. One-Document Implementation Checklist

### Foundation

- [ ] Rename project identity
- [ ] Clean root layout
- [ ] Keep reference assets quarantined
- [ ] Establish original asset policy
- [ ] Add `xtask`
- [ ] Add logging/tracing
- [ ] Add schema generation

### Runtime

- [ ] Core data model
- [ ] Scene system
- [ ] Layer stack
- [ ] Renderer layers
- [ ] Camera
- [ ] Input/actions
- [ ] Save/load
- [ ] Delta saves
- [ ] Local server path
- [ ] Multiplayer permissions

### Worldgen

- [ ] Heightmap generator
- [ ] Water bands
- [ ] Shoreline resolver
- [ ] Road/path pass
- [ ] Bridge pass
- [ ] Border baking
- [ ] Biome packs
- [ ] Scene adjacency
- [ ] Multi-rectangle scenes

### Editor

- [ ] Main editor shell
- [ ] In-game overlay cleanup
- [ ] Command bus
- [ ] Inspector
- [ ] Asset browser
- [ ] Validation panel
- [ ] Pixel editor MVP
- [ ] Autotile editor
- [ ] Object footprint editor
- [ ] NPC/dialogue editor
- [ ] Recipe/item editor
- [ ] Staff/tavern editor

### Gameplay

- [ ] Tavern open/close
- [ ] Customers
- [ ] Seating attachments
- [ ] Orders/service
- [ ] Kitchen
- [ ] Brewing
- [ ] Cellar
- [ ] Staff
- [ ] Manager
- [ ] Farming
- [ ] Greenhouse
- [ ] Recipes
- [ ] Fishing
- [ ] Mining
- [ ] Smithing
- [ ] Relationships
- [ ] Quests
- [ ] Island travel
- [ ] New Game+

### Assets

- [ ] Terrain base sheet
- [ ] Water/shoreline sheet
- [ ] Wall sheet
- [ ] Tavern prop sheet
- [ ] Character base walk sheet
- [ ] Character creator layers
- [ ] NPC portraits
- [ ] UI skin kit
- [ ] Item icons
- [ ] Tree/foliage sets
- [ ] Cave assets
- [ ] City assets

---

## 31. Recommended Source Layout Target

```text
HearthAndHollow/
  Cargo.toml
  xtask/
  crates/
    haven_core/
    haven_world/
    haven_assets/
    haven_render/
    haven_sim/
    haven_net/
    haven_save/
    haven_editor/
    haven_game/
    haven_tools/
  assets/
    source/
    reference_quarantine/
    processed/
    generated_drafts/
  content/
    packs/
    schemas/
    worlds/
    scenes/
    npcs/
    items/
    recipes/
  editor/
    layouts/
    themes/
    help/
  docs/
    source_of_truth/
    architecture/
    gameplay/
    editor/
    assets/
    validation/
    archive/
  saves/
    dev/
  logs/
  tools/
  legacy/
```

---

## 32. Final Consolidated Direction

Havenwild should move forward as a Rust-native cozy tavern life-sim with a robust editor-first workflow. The existing prototype already proves the most important starting pieces: scenes, tiles, heightmaps, transitions, construction tools, tile rules, save/load, validation, and a live in-game editor overlay. The next major step is not to add random gameplay features. The next step is to solidify the architecture and editor foundations so every gameplay system can be authored, validated, and saved cleanly.

Priority should be:

1. preserve current prototype
2. rename/refactor project identity
3. formalize schemas
4. stabilize editor command/validation architecture
5. build asset metadata and pixel/autotile tools
6. complete worldgen scene/layer model
7. then implement tavern/farming/staff/NPC gameplay loops on top

The strongest path is to treat the current source as a prototype seed, not as a disposable experiment. Keep what works, archive what is legacy/reference, and convert the working Rust systems into a clean Havenwild foundation.
